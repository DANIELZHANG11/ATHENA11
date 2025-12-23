/**
 * Athena App - PowerSync Schema
 * 
 * SQLite 本地数据库 Schema 定义
 * 与后端 PostgreSQL 表结构保持同步
 * 
 * @see 雅典娜开发技术文档汇总/04 - 数据库全景与迁移Database_Schema_and_Migration_Log.md
 */

import { column, Schema, Table } from '@powersync/web'

// ============================================================================
// 同步表 (Synced Tables) - 9 个
// ============================================================================

/**
 * 书籍表
 */
const books = new Table({
  id: column.text,                    // UUID
  user_id: column.text,               // 所属用户
  title: column.text,                 // 书名
  author: column.text,                // 作者
  cover_url: column.text,             // 封面 S3 Key
  file_type: column.text,             // 原始格式 (pdf/epub)
  file_size: column.integer,          // 文件大小 (bytes)
  content_sha256: column.text,        // 文件哈希
  storage_key: column.text,           // MinIO 存储 Key
  metadata_confirmed: column.integer, // 元数据已确认 (0/1)
  is_image_based: column.integer,     // 是否图片型 (0/1)
  ocr_status: column.text,            // OCR 状态
  conversion_status: column.text,     // 格式转换状态
  converted_epub_key: column.text,    // 转换后 EPUB Key
  page_count: column.integer,         // 书籍页数
  is_deleted: column.integer,         // 软删除标记 (0/1)
  created_at: column.text,            // ISO8601 时间戳
  updated_at: column.text,            // ISO8601 时间戳
})

/**
 * 阅读位置表
 */
const book_position = new Table({
  user_id: column.text,
  book_id: column.text,
  progress: column.real,              // 进度 0-1
  last_cfi: column.text,              // EPUB CFI 位置
  last_page: column.integer,          // PDF 当前页
  total_pages: column.integer,        // PDF 总页数
  finished_at: column.text,           // 读完时间
  updated_at: column.text,
})

/**
 * 阅读时长记录表
 */
const reading_time_log = new Table({
  id: column.text,
  user_id: column.text,
  book_id: column.text,
  device_id: column.text,
  is_active: column.integer,          // 会话是否活跃 (0/1)
  duration_ms: column.integer,        // 阅读时长 (毫秒)
  created_at: column.text,
  updated_at: column.text,
})

/**
 * 笔记表
 */
const notes = new Table({
  id: column.text,
  user_id: column.text,
  book_id: column.text,
  content: column.text,               // 笔记内容
  cfi: column.text,                   // 位置 CFI
  page_number: column.integer,        // PDF 页码
  is_deleted: column.integer,
  created_at: column.text,
  updated_at: column.text,
})

/**
 * 高亮表
 */
const highlights = new Table({
  id: column.text,
  user_id: column.text,
  book_id: column.text,
  text: column.text,                  // 高亮文本
  cfi_range: column.text,             // CFI 范围
  color: column.text,                 // 高亮颜色
  page_number: column.integer,
  is_deleted: column.integer,
  created_at: column.text,
  updated_at: column.text,
})

/**
 * 书签表
 */
const bookmarks = new Table({
  id: column.text,
  user_id: column.text,
  book_id: column.text,
  cfi: column.text,
  page_number: column.integer,
  title: column.text,                 // 书签标题
  is_deleted: column.integer,
  created_at: column.text,
  updated_at: column.text,
})

/**
 * 书架表
 */
const shelves = new Table({
  id: column.text,
  user_id: column.text,
  name: column.text,
  description: column.text,
  cover_book_id: column.text,         // 封面书籍 ID
  sort_order: column.integer,
  is_deleted: column.integer,
  created_at: column.text,
  updated_at: column.text,
})

/**
 * 书架-书籍关联表
 */
const shelf_books = new Table({
  id: column.text,
  shelf_id: column.text,
  book_id: column.text,
  user_id: column.text,
  sort_order: column.integer,
  added_at: column.text,
})

/**
 * 用户设置表
 */
const user_settings = new Table({
  id: column.text,
  user_id: column.text,
  key: column.text,
  value: column.text,                 // JSON 字符串
  updated_at: column.text,
})

// ============================================================================
// 本地专用表 (Local-only Tables) - 不同步
// ============================================================================

/**
 * 本地书籍文件缓存
 */
const local_book_files = new Table(
  {
    id: column.text,
    book_id: column.text,
    file_type: column.text,           // original / converted / ocr
    local_path: column.text,          // 本地文件路径
    s3_key: column.text,              // S3 Key
    file_size: column.integer,
    downloaded_at: column.text,
    expires_at: column.text,
  },
  { localOnly: true }
)

/**
 * 本地封面缓存
 */
const local_cover_cache = new Table(
  {
    id: column.text,
    book_id: column.text,
    local_path: column.text,
    s3_key: column.text,
    downloaded_at: column.text,
  },
  { localOnly: true }
)

/**
 * 本地 TTS 设置
 */
const local_tts_settings = new Table(
  {
    id: column.text,
    voice_id: column.text,
    speed: column.real,
    pitch: column.real,
    volume: column.real,
    updated_at: column.text,
  },
  { localOnly: true }
)

// ============================================================================
// Schema 导出
// ============================================================================

export const AppSchema = new Schema({
  // 同步表
  books,
  book_position,
  reading_time_log,
  notes,
  highlights,
  bookmarks,
  shelves,
  shelf_books,
  user_settings,
  // 本地表
  local_book_files,
  local_cover_cache,
  local_tts_settings,
})

export type Database = (typeof AppSchema)['types']
