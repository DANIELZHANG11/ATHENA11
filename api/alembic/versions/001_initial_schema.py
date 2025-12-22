"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

创建所有初始表结构。
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ==========================================================================
    # 启用扩展
    # ==========================================================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # ==========================================================================
    # users 表
    # ==========================================================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('nickname', sa.String(100), nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('locale', sa.String(10), server_default='zh-CN'),
        sa.Column('timezone', sa.String(50), server_default='Asia/Shanghai'),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('email_verified', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('oauth_providers', postgresql.JSONB, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # ==========================================================================
    # user_sessions 表
    # ==========================================================================
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_info', postgresql.JSONB, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'])

    # ==========================================================================
    # 辅助函数
    # ==========================================================================
    op.execute('''
        CREATE OR REPLACE FUNCTION current_user_id()
        RETURNS UUID AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
        END;
        $$ language 'plpgsql';
    ''')

    op.execute('''
        CREATE OR REPLACE FUNCTION set_current_user_id(user_id UUID)
        RETURNS VOID AS $$
        BEGIN
            PERFORM set_config('app.current_user_id', user_id::TEXT, FALSE);
        END;
        $$ language 'plpgsql';
    ''')

    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    ''')

    op.execute('''
        CREATE OR REPLACE FUNCTION increment_version()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.version = OLD.version + 1;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    ''')

    op.execute('''
        CREATE OR REPLACE FUNCTION lww_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.updated_at < OLD.updated_at THEN
                RETURN NULL;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    ''')

    op.execute('''
        CREATE OR REPLACE FUNCTION detect_conflict()
        RETURNS TRIGGER AS $$
        BEGIN
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    ''')

    # ==========================================================================
    # books 表
    # ==========================================================================
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('original_format', sa.String(20), nullable=False),
        sa.Column('size', sa.BigInteger, nullable=False),
        sa.Column('minio_key', sa.Text, nullable=False),
        sa.Column('cover_key', sa.Text, nullable=True),
        sa.Column('ocr_pdf_key', sa.Text, nullable=True),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('storage_ref_count', sa.Integer, server_default='1'),
        sa.Column('processing_status', sa.String(20), server_default="'pending'"),
        sa.Column('processing_error', sa.Text, nullable=True),
        sa.Column('reader_type', sa.String(20), server_default="'pdf'"),
        sa.Column('is_readable', sa.Boolean, server_default='false'),
        sa.Column('is_interactive', sa.Boolean, server_default='false'),
        sa.Column('has_text_layer', sa.Boolean, server_default='false'),
        sa.Column('is_image_based', sa.Boolean, server_default='false'),
        sa.Column('ocr_status', sa.String(20), nullable=True),
        sa.Column('metadata_confirmed', sa.Boolean, server_default='false'),
        sa.Column('meta', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer, server_default='1'),
    )
    op.create_index('ix_books_user_id', 'books', ['user_id'])
    op.create_index('ix_books_sha256', 'books', ['sha256'])
    op.create_index('ix_books_deleted_at', 'books', ['deleted_at'])
    op.create_index('ix_books_title_trgm', 'books', ['title'], postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'})

    # ==========================================================================
    # book_position 表
    # ==========================================================================
    op.create_table(
        'book_position',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter_or_page', sa.Integer, server_default='0'),
        sa.Column('scroll_position_json', postgresql.JSONB, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_book_position_user_book', 'book_position', ['user_id', 'book_id'], unique=True)

    # ==========================================================================
    # reading_time_log 表
    # ==========================================================================
    op.create_table(
        'reading_time_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_sec', sa.Integer, nullable=False),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_reading_time_log_user_id', 'reading_time_log', ['user_id'])
    op.create_index('ix_reading_time_log_book_id', 'reading_time_log', ['book_id'])
    op.create_index('ix_reading_time_log_started_at', 'reading_time_log', ['started_at'])

    # ==========================================================================
    # notes 表
    # ==========================================================================
    op.create_table(
        'notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position_json', postgresql.JSONB, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('conflict_of', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_notes_user_id', 'notes', ['user_id'])
    op.create_index('ix_notes_book_id', 'notes', ['book_id'])
    op.create_index('ix_notes_deleted_at', 'notes', ['deleted_at'])

    # ==========================================================================
    # highlights 表
    # ==========================================================================
    op.create_table(
        'highlights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position_json', postgresql.JSONB, nullable=False),
        sa.Column('color', sa.String(20), server_default="'yellow'"),
        sa.Column('text_preview', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_highlights_user_id', 'highlights', ['user_id'])
    op.create_index('ix_highlights_book_id', 'highlights', ['book_id'])

    # ==========================================================================
    # bookmarks 表
    # ==========================================================================
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position_json', postgresql.JSONB, nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_bookmarks_user_id', 'bookmarks', ['user_id'])
    op.create_index('ix_bookmarks_book_id', 'bookmarks', ['book_id'])

    # ==========================================================================
    # shelves 表
    # ==========================================================================
    op.create_table(
        'shelves',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_shelves_user_id', 'shelves', ['user_id'])

    # ==========================================================================
    # shelf_books 表
    # ==========================================================================
    op.create_table(
        'shelf_books',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('shelf_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shelves.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_shelf_books_shelf_id', 'shelf_books', ['shelf_id'])
    op.create_index('ix_shelf_books_book_id', 'shelf_books', ['book_id'])
    op.create_unique_constraint('uq_shelf_books', 'shelf_books', ['shelf_id', 'book_id'])

    # ==========================================================================
    # user_settings 表
    # ==========================================================================
    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('settings_json', postgresql.JSONB, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # ai_sessions 表
    # ==========================================================================
    op.create_table(
        'ai_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('books.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('model', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_ai_sessions_user_id', 'ai_sessions', ['user_id'])

    # ==========================================================================
    # ai_messages 表
    # ==========================================================================
    op.create_table(
        'ai_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_ai_messages_session_id', 'ai_messages', ['session_id'])

    # ==========================================================================
    # billing_* 表
    # ==========================================================================
    op.create_table(
        'billing_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_provider', sa.String(50), nullable=True),
        sa.Column('external_subscription_id', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_billing_subscriptions_user_id', 'billing_subscriptions', ['user_id'])

    op.create_table(
        'billing_quotas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quota_type', sa.String(50), nullable=False),
        sa.Column('total', sa.Integer, nullable=False),
        sa.Column('used', sa.Integer, server_default='0'),
        sa.Column('resets_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_billing_quotas_user_id', 'billing_quotas', ['user_id'])
    op.create_unique_constraint('uq_billing_quotas_user_type', 'billing_quotas', ['user_id', 'quota_type'])

    # ==========================================================================
    # document_vectors 表
    # ==========================================================================
    op.execute('''
        CREATE TABLE document_vectors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    ''')
    op.create_index('ix_document_vectors_book_id', 'document_vectors', ['book_id'])
    # 向量索引
    op.execute('''
        CREATE INDEX ix_document_vectors_embedding
        ON document_vectors
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')

    # ==========================================================================
    # system_* 表
    # ==========================================================================
    op.create_table(
        'system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', postgresql.JSONB, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'system_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_system_audit_log_user_id', 'system_audit_log', ['user_id'])
    op.create_index('ix_system_audit_log_action', 'system_audit_log', ['action'])
    op.create_index('ix_system_audit_log_created_at', 'system_audit_log', ['created_at'])

    # ==========================================================================
    # 创建 RLS 策略
    # ==========================================================================
    # 启用 RLS
    tables_with_rls = ['books', 'book_position', 'reading_time_log', 'notes',
                       'highlights', 'bookmarks', 'shelves', 'shelf_books', 'user_settings']

    for table in tables_with_rls:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')

        if table == 'shelf_books':
            # shelf_books 通过 shelf 关联到用户
            op.execute(f'''
                CREATE POLICY {table}_policy ON {table}
                FOR ALL
                USING (
                    EXISTS (
                        SELECT 1 FROM shelves
                        WHERE shelves.id = {table}.shelf_id
                        AND shelves.user_id = current_user_id()
                    )
                )
            ''')
        else:
            op.execute(f'''
                CREATE POLICY {table}_policy ON {table}
                FOR ALL
                USING (user_id = current_user_id())
            ''')

    # ==========================================================================
    # 创建触发器
    # ==========================================================================
    # updated_at 触发器
    tables_with_updated_at = ['users', 'books', 'notes', 'highlights', 'shelves',
                              'user_settings', 'ai_sessions', 'billing_subscriptions',
                              'billing_quotas', 'system_config']

    for table in tables_with_updated_at:
        op.execute(f'''
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        ''')

    # 版本号触发器
    op.execute('''
        CREATE TRIGGER increment_books_version
        BEFORE UPDATE ON books
        FOR EACH ROW
        EXECUTE FUNCTION increment_version()
    ''')

    # LWW 触发器
    op.execute('''
        CREATE TRIGGER book_position_lww
        BEFORE UPDATE ON book_position
        FOR EACH ROW
        EXECUTE FUNCTION lww_update()
    ''')

    # 冲突检测触发器
    op.execute('''
        CREATE TRIGGER notes_conflict_detection
        BEFORE INSERT OR UPDATE ON notes
        FOR EACH ROW
        EXECUTE FUNCTION detect_conflict()
    ''')

    # ==========================================================================
    # 创建 PowerSync 发布
    # ==========================================================================
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'athena_publication') THEN
                CREATE PUBLICATION athena_publication FOR ALL TABLES;
            END IF;
        END $$
    ''')


def downgrade() -> None:
    # 删除发布
    op.execute('DROP PUBLICATION IF EXISTS athena_publication')

    # 删除所有表（按依赖顺序）
    tables = [
        'system_audit_log', 'system_config',
        'document_vectors',
        'billing_quotas', 'billing_subscriptions',
        'ai_messages', 'ai_sessions',
        'user_settings',
        'shelf_books', 'shelves',
        'bookmarks', 'highlights', 'notes',
        'reading_time_log', 'book_position', 'books',
        'user_sessions', 'users',
    ]

    for table in tables:
        op.drop_table(table)

    # 删除函数
    op.execute('DROP FUNCTION IF EXISTS current_user_id()')
    op.execute('DROP FUNCTION IF EXISTS set_current_user_id(UUID)')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    op.execute('DROP FUNCTION IF EXISTS increment_version()')
    op.execute('DROP FUNCTION IF EXISTS lww_update()')
    op.execute('DROP FUNCTION IF EXISTS detect_conflict()')
