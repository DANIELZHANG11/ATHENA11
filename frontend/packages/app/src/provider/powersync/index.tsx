/**
 * Athena App - PowerSync Provider
 * 
 * 跨平台 PowerSync 初始化和 Context 提供
 * - Web: 使用 @powersync/web + wa-sqlite WASM
 * - Native: 使用 @powersync/react-native + @op-engineering/op-sqlite
 * 
 * @see 雅典娜开发技术文档汇总/00 - AI 编码宪法与规范AI_Coding_Constitution_and_Rules.md
 * @see 雅典娜开发技术文档汇总/03 - 系统架构与ADR System_Architecture_and_Decisions.md ADR-007
 */

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react'

// PowerSync 配置
const POWERSYNC_URL = process.env.NEXT_PUBLIC_POWERSYNC_URL || 'http://localhost:8090'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:48000'

// ============================================================================
// Types
// ============================================================================

type AnyRecord = Record<string, unknown>

export interface PowerSyncDatabase {
  /** 执行 SQL 查询 */
  execute: (sql: string, params?: unknown[]) => Promise<{ rowsAffected: number }>
  /** 执行 SQL 并返回结果 */
  getAll: <T extends AnyRecord = AnyRecord>(sql: string, params?: unknown[]) => Promise<T[]>
  /** 监听查询变化 (返回取消订阅函数) */
  watch: <T extends AnyRecord = AnyRecord>(
    sql: string,
    params: unknown[],
    callback: (results: T[]) => void
  ) => () => void
  /** 连接状态 */
  connected: boolean
}

interface PowerSyncContextValue {
  db: PowerSyncDatabase | null
  isConnected: boolean
  isLoading: boolean
  error: Error | null
}

// ============================================================================
// Context
// ============================================================================

const defaultContext: PowerSyncContextValue = {
  db: null,
  isConnected: false,
  isLoading: true,
  error: null,
}

const PowerSyncContext = createContext<PowerSyncContextValue>(defaultContext)

// ============================================================================
// Mock Implementation (用于开发和测试)
// ============================================================================

function createMockDatabase(): PowerSyncDatabase {
  const listeners = new Map<string, Set<(results: unknown[]) => void>>()
  
  return {
    execute: async (sql, params) => {
      console.log('[PowerSync Mock] Execute:', sql, params)
      return { rowsAffected: 0 }
    },
    getAll: async function getAllImpl<T extends AnyRecord = AnyRecord>(
      sql: string, 
      params?: unknown[]
    ): Promise<T[]> {
      console.log('[PowerSync Mock] GetAll:', sql, params)
      return [] as T[]
    },
    watch: function watchImpl<T extends AnyRecord = AnyRecord>(
      sql: string, 
      params: unknown[], 
      callback: (results: T[]) => void
    ): () => void {
      const key = `${sql}:${JSON.stringify(params)}`
      
      if (!listeners.has(key)) {
        listeners.set(key, new Set())
      }
      listeners.get(key)?.add(callback as (results: unknown[]) => void)
      
      // 立即返回空数组
      callback([] as T[])
      
      // 返回取消订阅函数
      return () => {
        listeners.get(key)?.delete(callback as (results: unknown[]) => void)
      }
    },
    connected: false,
  }
}

// ============================================================================
// Web Implementation
// ============================================================================

async function initWebPowerSync(): Promise<PowerSyncDatabase> {
  // TODO: 正式实现 PowerSync Web 初始化
  console.log('[PowerSync] Web initialization - using mock for development')
  return createMockDatabase()
}

// ============================================================================
// Native Implementation
// ============================================================================

async function initNativePowerSync(): Promise<PowerSyncDatabase> {
  // TODO: 正式实现 PowerSync Native 初始化
  console.log('[PowerSync] Native initialization - using mock for development')
  return createMockDatabase()
}

// ============================================================================
// Platform Detection
// ============================================================================

const isWeb = typeof window !== 'undefined' && typeof document !== 'undefined'

// ============================================================================
// Provider Component
// ============================================================================

interface PowerSyncProviderProps {
  children: ReactNode
  /** 使用 Mock 数据库（用于测试） */
  useMock?: boolean
}

export function PowerSyncProvider({ children, useMock = false }: PowerSyncProviderProps): React.JSX.Element {
  const [db, setDb] = useState<PowerSyncDatabase | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let mounted = true

    async function init(): Promise<void> {
      try {
        let database: PowerSyncDatabase

        if (useMock) {
          database = createMockDatabase()
        } else {
          database = isWeb
            ? await initWebPowerSync()
            : await initNativePowerSync()
        }

        if (mounted) {
          setDb(database)
          setIsConnected(database.connected)
          setIsLoading(false)
        }
      } catch (err) {
        console.error('[PowerSync] Initialization failed:', err)
        if (mounted) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    init()

    return () => {
      mounted = false
    }
  }, [useMock])

  const value: PowerSyncContextValue = {
    db,
    isConnected,
    isLoading,
    error,
  }

  return (
    <PowerSyncContext.Provider value={value}>
      {children}
    </PowerSyncContext.Provider>
  )
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * 获取 PowerSync Context
 */
export function usePowerSync(): PowerSyncContextValue {
  const context = useContext(PowerSyncContext)
  if (context === undefined) {
    throw new Error('usePowerSync must be used within a PowerSyncProvider')
  }
  return context
}

/**
 * 获取 PowerSync 数据库实例
 * @throws 如果数据库未初始化则抛出错误
 */
export function usePowerSyncDatabase(): PowerSyncDatabase {
  const { db, isLoading, error } = usePowerSync()
  
  if (error) {
    throw error
  }
  
  if (isLoading) {
    throw new Error('PowerSync database is still loading')
  }
  
  if (!db) {
    throw new Error('PowerSync database is not initialized')
  }
  
  return db
}

/**
 * 实时查询返回类型
 */
interface LiveQueryResult<T> {
  data: T[]
  isLoading: boolean
  error: Error | null
}

/**
 * 实时查询 Hook
 * 
 * @example
 * ```tsx
 * const { data: books } = useLiveQuery(
 *   'SELECT * FROM books WHERE is_deleted = 0 ORDER BY updated_at DESC'
 * )
 * ```
 */
export function useLiveQuery<T extends AnyRecord = AnyRecord>(
  sql: string,
  params: unknown[] = []
): LiveQueryResult<T> {
  const { db, isLoading: dbLoading, error: dbError } = usePowerSync()
  const [data, setData] = useState<T[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // 序列化 params 用于依赖比较
  const paramsKey = JSON.stringify(params)

  useEffect(() => {
    if (!db || dbLoading) return

    // 创建局部引用以满足 TypeScript 的 null 检查
    const database = db

    let unsubscribe: (() => void) | undefined

    async function fetchAndWatch(): Promise<void> {
      try {
        // 初始查询
        const results = await database.getAll<T>(sql, params)
        setData(results)
        setIsLoading(false)

        // 监听变化
        unsubscribe = database.watch<T>(sql, params, (newResults) => {
          setData(newResults)
        })
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)))
        setIsLoading(false)
      }
    }

    fetchAndWatch()

    return () => {
      unsubscribe?.()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [db, dbLoading, sql, paramsKey])

  return { 
    data, 
    isLoading: dbLoading || isLoading, 
    error: dbError || error 
  }
}

/**
 * 数据库写入返回类型
 */
interface MutationResult {
  execute: (sql: string, params?: unknown[]) => Promise<{ rowsAffected: number }>
  isExecuting: boolean
  error: Error | null
  isReady: boolean
}

/**
 * 数据库写入 Hook
 * 
 * @example
 * ```tsx
 * const { execute, isExecuting } = useMutation()
 * 
 * const updateBookTitle = async (bookId: string, newTitle: string) => {
 *   await execute(
 *     'UPDATE books SET title = ?, updated_at = ? WHERE id = ?',
 *     [newTitle, new Date().toISOString(), bookId]
 *   )
 * }
 * ```
 */
export function useMutation(): MutationResult {
  const { db, isLoading: dbLoading } = usePowerSync()
  const [isExecuting, setIsExecuting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const execute = useCallback(async (sql: string, params: unknown[] = []): Promise<{ rowsAffected: number }> => {
    if (!db) {
      throw new Error('Database not initialized')
    }
    
    setIsExecuting(true)
    setError(null)
    
    try {
      const result = await db.execute(sql, params)
      return result
    } catch (err) {
      const mutationError = err instanceof Error ? err : new Error(String(err))
      setError(mutationError)
      throw mutationError
    } finally {
      setIsExecuting(false)
    }
  }, [db])

  return { 
    execute, 
    isExecuting, 
    error,
    isReady: !dbLoading && db !== null,
  }
}

// 导出未使用的常量以避免警告
export const _config = { POWERSYNC_URL, API_URL }
