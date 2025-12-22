"""
AI 服务

处理 AI 对话、向量检索等功能。
"""

import json
from collections.abc import AsyncGenerator
from uuid import UUID

import httpx
import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AthenaException, ErrorCode
from app.models import AIMessage, AISession

logger = structlog.get_logger()


class AIService:
    """AI 对话和检索服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_url = settings.ai.ai_proxy_url
        self.api_key = settings.ai.ai_api_key
        self.default_model = settings.ai.ai_default_model

    # ========================================================================
    # 会话管理
    # ========================================================================

    async def create_session(
        self,
        user_id: str,
        book_id: str | None = None,
        title: str | None = None,
        model: str | None = None,
    ) -> AISession:
        """创建 AI 会话"""
        session = AISession(
            user_id=UUID(user_id),
            book_id=UUID(book_id) if book_id else None,
            title=title or "新对话",
            model=model or self.default_model,
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info("AI session created", session_id=str(session.id))
        return session

    async def get_session(self, session_id: str, user_id: str) -> AISession:
        """获取会话"""
        result = await self.db.execute(
            select(AISession).where(
                AISession.id == UUID(session_id),
                AISession.user_id == UUID(user_id),
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise AthenaException(
                code=ErrorCode.NOT_FOUND,
                message="Session not found",
            )

        return session

    async def list_sessions(
        self,
        user_id: str,
        book_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AISession], int]:
        """列出会话"""
        query = select(AISession).where(AISession.user_id == UUID(user_id))

        if book_id:
            query = query.where(AISession.book_id == UUID(book_id))

        # 计数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # 分页
        query = query.order_by(AISession.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        # 获取消息数量
        for session in sessions:
            count_result = await self.db.execute(
                select(func.count()).where(AIMessage.session_id == session.id)
            )
            session.message_count = count_result.scalar() or 0

        return sessions, total

    async def delete_session(self, session_id: str, user_id: str) -> None:
        """删除会话"""
        session = await self.get_session(session_id, user_id)
        await self.db.delete(session)
        await self.db.commit()

    # ========================================================================
    # 消息管理
    # ========================================================================

    async def get_session_messages(
        self,
        session_id: str,
        user_id: str,
    ) -> list[AIMessage]:
        """获取会话的所有消息"""
        await self.get_session(session_id, user_id)  # 验证权限

        result = await self.db.execute(
            select(AIMessage)
            .where(AIMessage.session_id == UUID(session_id))
            .order_by(AIMessage.created_at)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: int | None = None,
    ) -> AIMessage:
        """添加消息"""
        message = AIMessage(
            session_id=UUID(session_id),
            role=role,
            content=content,
            tokens_used=tokens_used,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # 更新会话时间
        await self.db.execute(
            text("""
                UPDATE ai_sessions
                SET updated_at = NOW()
                WHERE id = :session_id::uuid
            """),
            {"session_id": session_id},
        )
        await self.db.commit()

        return message

    # ========================================================================
    # AI 对话
    # ========================================================================

    async def chat(
        self,
        user_id: str,
        message: str,
        session_id: str | None = None,
        book_id: str | None = None,
        stream: bool = False,  # noqa: ARG002
    ) -> dict:
        """
        发送聊天消息

        如果未提供 session_id，会自动创建新会话。
        如果关联了书籍，会自动进行 RAG 检索。
        """
        # 获取或创建会话
        if session_id:
            session = await self.get_session(session_id, user_id)
        else:
            session = await self.create_session(
                user_id=user_id,
                book_id=book_id,
            )

        # 保存用户消息
        await self.add_message(
            session_id=str(session.id),
            role="user",
            content=message,
        )

        # 获取历史消息
        history = await self.get_session_messages(str(session.id), user_id)
        messages = self._build_messages(history, session.book_id)

        # 如果关联书籍，进行 RAG 检索
        if session.book_id:
            context = await self._retrieve_context(message, [str(session.book_id)])
            if context:
                # 在最后一条用户消息前插入上下文
                messages[-1]["content"] = self._format_rag_prompt(message, context)

        # 调用 AI API
        response = await self._call_ai_api(messages, session.model)

        # 保存助手回复
        assistant_message = await self.add_message(
            session_id=str(session.id),
            role="assistant",
            content=response["content"],
            tokens_used=response["tokens_used"],
        )

        return {
            "session_id": str(session.id),
            "message": assistant_message,
            "tokens_used": response["tokens_used"],
        }

    async def chat_stream(
        self,
        user_id: str,
        message: str,
        session_id: str | None = None,
        book_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天

        返回 SSE 格式的数据流。
        """
        # 获取或创建会话
        if session_id:
            session = await self.get_session(session_id, user_id)
        else:
            session = await self.create_session(
                user_id=user_id,
                book_id=book_id,
            )

        # 保存用户消息
        await self.add_message(
            session_id=str(session.id),
            role="user",
            content=message,
        )

        # 获取历史消息
        history = await self.get_session_messages(str(session.id), user_id)
        messages = self._build_messages(history, session.book_id)

        # RAG 检索
        if session.book_id:
            context = await self._retrieve_context(message, [str(session.book_id)])
            if context:
                messages[-1]["content"] = self._format_rag_prompt(message, context)

        # 流式调用
        full_content = ""
        async for chunk in self._call_ai_api_stream(messages, session.model):
            full_content += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"

        # 保存完整回复
        await self.add_message(
            session_id=str(session.id),
            role="assistant",
            content=full_content,
        )

        yield f"data: {json.dumps({'done': True, 'session_id': str(session.id)})}\n\n"

    def _build_messages(
        self,
        history: list[AIMessage],
        book_id: UUID | None = None,
    ) -> list[dict[str, str]]:
        """构建消息列表"""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(book_id),
            }
        ]

        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        return messages

    def _get_system_prompt(self, book_id: UUID | None = None) -> str:
        """获取系统提示词"""
        if book_id:
            return """你是雅典娜阅读助手，一个专业的图书阅读和理解助手。
你正在帮助用户理解他们正在阅读的书籍内容。

规则：
1. 基于提供的书籍内容回答问题
2. 如果内容不足以回答，请诚实说明
3. 使用中文回答
4. 保持回答简洁准确
5. 可以引用原文并注明位置"""
        else:
            return """你是雅典娜阅读助手，一个智能的阅读和学习伙伴。
你可以帮助用户：
- 讨论书籍和阅读体验
- 解释概念和术语
- 提供阅读建议
- 总结和分析内容

请用中文回答，保持友好和专业。"""

    def _format_rag_prompt(self, query: str, context: list[dict]) -> str:
        """格式化 RAG 提示"""
        context_text = "\n\n".join([
            f"[来源: 第{c['chunk_index']}段]\n{c['content']}"
            for c in context
        ])

        return f"""基于以下书籍内容回答问题：

---相关内容---
{context_text}
---

用户问题: {query}"""

    # ========================================================================
    # 向量检索
    # ========================================================================

    async def vector_search(
        self,
        user_id: str,
        query: str,
        book_ids: list[str] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        向量相似度检索

        使用 pgvector 进行相似度搜索。
        """
        # 获取查询向量
        query_embedding = await self._get_embedding(query)

        if not query_embedding:
            return []

        # 构建查询
        sql = """
            SELECT
                dv.book_id,
                b.title as book_title,
                dv.chunk_index,
                dv.content,
                dv.metadata,
                1 - (dv.embedding <=> :embedding::vector) as score
            FROM document_vectors dv
            JOIN books b ON b.id = dv.book_id
            WHERE b.user_id = :user_id::uuid
        """

        if book_ids:
            sql += " AND dv.book_id = ANY(:book_ids::uuid[])"

        sql += """
            ORDER BY dv.embedding <=> :embedding::vector
            LIMIT :top_k
        """

        params = {
            "user_id": user_id,
            "embedding": str(query_embedding),
            "top_k": top_k,
        }

        if book_ids:
            params["book_ids"] = book_ids

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        return [
            {
                "book_id": str(row.book_id),
                "book_title": row.book_title,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "score": float(row.score),
                "metadata": row.metadata,
            }
            for row in rows
        ]

    async def _retrieve_context(
        self,
        query: str,
        book_ids: list[str],
        top_k: int = 3,
    ) -> list[dict]:
        """检索相关上下文"""
        try:
            return await self.vector_search(
                user_id="system",  # 内部调用
                query=query,
                book_ids=book_ids,
                top_k=top_k,
            )
        except Exception as e:
            logger.warning("Context retrieval failed", error=str(e))
            return []

    # ========================================================================
    # API 调用
    # ========================================================================

    async def _call_ai_api(
        self,
        messages: list[dict[str, str]],
        model: str,
    ) -> dict:
        """调用 AI API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": settings.ai.ai_max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "content": data["choices"][0]["message"]["content"],
                    "tokens_used": data["usage"]["total_tokens"],
                }

            except httpx.HTTPStatusError as e:
                logger.error("AI API error", status=e.response.status_code)
                raise AthenaException(
                    code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    message="AI service error",
                ) from e
            except Exception as e:
                logger.exception("AI API call failed")
                raise AthenaException(
                    code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    message="AI service unavailable",
                ) from e

    async def _call_ai_api_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
    ) -> AsyncGenerator[str, None]:
        """流式调用 AI API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.api_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": settings.ai.ai_max_tokens,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0]["delta"].get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue

            except Exception:
                logger.exception("AI API stream failed")
                raise

    async def _get_embedding(self, text: str) -> list[float] | None:
        """获取文本向量"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.ai.embedding_model,
                        "input": text,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]

            except Exception as e:
                logger.warning("Embedding API failed", error=str(e))
                return None
