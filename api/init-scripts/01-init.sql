-- PostgreSQL 初始化脚本
-- 在容器首次启动时执行

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 创建发布（用于 PowerSync 复制）
CREATE PUBLICATION athena_publication FOR ALL TABLES;

-- 设置 RLS (Row Level Security) 相关函数
-- 用于获取当前请求的用户 ID

-- 设置当前用户 ID 的函数
CREATE OR REPLACE FUNCTION set_current_user_id(user_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 获取当前用户 ID 的函数
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- 通用的 updated_at 触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 版本号自增触发器函数
CREATE OR REPLACE FUNCTION increment_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version = COALESCE(OLD.version, 0) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 冲突检测触发器函数（用于笔记等）
CREATE OR REPLACE FUNCTION detect_conflict()
RETURNS TRIGGER AS $$
DECLARE
    existing_record RECORD;
BEGIN
    -- 检查是否存在相同位置的记录
    IF TG_TABLE_NAME = 'notes' THEN
        SELECT * INTO existing_record
        FROM notes
        WHERE book_id = NEW.book_id
          AND position_json = NEW.position_json
          AND user_id = NEW.user_id
          AND id != NEW.id
          AND deleted_at IS NULL
        LIMIT 1;
        
        IF FOUND THEN
            -- 标记为冲突副本
            NEW.conflict_of = existing_record.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- LWW (Last Write Wins) 触发器函数
-- 用于阅读进度等需要时间戳比较的场景
CREATE OR REPLACE FUNCTION lww_update()
RETURNS TRIGGER AS $$
BEGIN
    -- 如果新记录的 updated_at 比旧记录更早，拒绝更新
    IF OLD.updated_at > NEW.updated_at THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 打印初始化完成信息
DO $$
BEGIN
    RAISE NOTICE 'Athena database initialization completed successfully!';
END $$;
