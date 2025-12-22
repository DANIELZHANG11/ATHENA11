"""
存储服务

MinIO S3 对象存储操作封装。
"""

import uuid
from datetime import timedelta
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class StorageService:
    """MinIO 存储服务"""

    def __init__(self):
        self.client = Minio(
            endpoint=settings.minio.minio_endpoint,
            access_key=settings.minio.minio_access_key,
            secret_key=settings.minio.minio_secret_key,
            secure=settings.minio.minio_secure,
        )
        self._ensure_buckets()

    def _ensure_buckets(self) -> None:
        """确保所需的存储桶存在"""
        buckets = [
            settings.minio.minio_bucket_books,
            settings.minio.minio_bucket_covers,
            settings.minio.minio_bucket_ocr,
        ]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def generate_presigned_upload_url(
        self,
        filename: str,
        content_type: str,  # noqa: ARG002
        user_id: str,
        expires: timedelta = timedelta(hours=1),
    ) -> tuple[str, str]:
        """
        生成预签名上传 URL

        Args:
            filename: 原始文件名
            content_type: MIME 类型
            user_id: 用户 ID
            expires: 过期时间

        Returns:
            (upload_url, object_key)
        """
        # 生成唯一的对象键
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        object_key = f"{user_id}/{uuid.uuid4()}.{ext}" if ext else f"{user_id}/{uuid.uuid4()}"

        # 生成预签名 URL
        url = self.client.presigned_put_object(
            bucket_name=settings.minio.minio_bucket_books,
            object_name=object_key,
            expires=expires,
        )

        return url, object_key

    def generate_presigned_download_url(
        self,
        object_key: str,
        bucket: str | None = None,
        expires: timedelta = timedelta(hours=1),
        filename: str | None = None,
    ) -> str:
        """
        生成预签名下载 URL

        Args:
            object_key: 对象键
            bucket: 存储桶名称
            expires: 过期时间
            filename: 下载时的文件名

        Returns:
            download_url
        """
        bucket = bucket or settings.minio.minio_bucket_books

        # 可选的响应头
        response_headers = {}
        if filename:
            response_headers["response-content-disposition"] = f'attachment; filename="{filename}"'

        return self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_key,
            expires=expires,
        )

    def get_object_info(
        self,
        object_key: str,
        bucket: str | None = None,
    ) -> dict | None:
        """
        获取对象元信息

        Returns:
            {"size": int, "content_type": str, "etag": str} 或 None
        """
        bucket = bucket or settings.minio.minio_bucket_books
        try:
            stat = self.client.stat_object(bucket, object_key)
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "etag": stat.etag,
            }
        except S3Error:
            return None

    def delete_object(
        self,
        object_key: str,
        bucket: str | None = None,
    ) -> bool:
        """删除对象"""
        bucket = bucket or settings.minio.minio_bucket_books
        try:
            self.client.remove_object(bucket, object_key)
            return True
        except S3Error:
            return False

    def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str | None = None,
        dest_bucket: str | None = None,
    ) -> bool:
        """复制对象"""
        from minio.commonconfig import CopySource

        source_bucket = source_bucket or settings.minio.minio_bucket_books
        dest_bucket = dest_bucket or settings.minio.minio_bucket_books

        try:
            self.client.copy_object(
                dest_bucket,
                dest_key,
                CopySource(source_bucket, source_key),
            )
            return True
        except S3Error:
            return False

    def upload_file(
        self,
        file: BinaryIO,
        object_key: str,
        content_type: str,
        bucket: str | None = None,
    ) -> bool:
        """直接上传文件"""
        bucket = bucket or settings.minio.minio_bucket_books
        try:
            file.seek(0, 2)  # 移动到末尾
            size = file.tell()
            file.seek(0)  # 回到开头

            self.client.put_object(
                bucket_name=bucket,
                object_name=object_key,
                data=file,
                length=size,
                content_type=content_type,
            )
            return True
        except S3Error:
            return False


# 单例
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """获取存储服务单例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
