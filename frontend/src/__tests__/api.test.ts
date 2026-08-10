import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  sessionApi,
  reviewerApi,
  exporterApi,
  pluginApi,
  statsApi,
} from '../services'

// Capture interceptor handlers registered on the mock axios instance
const { requestInterceptorHandlers, responseInterceptorHandlers, mockMessageError } = vi.hoisted(() => ({
  requestInterceptorHandlers: [] as Array<(config: unknown) => unknown>,
  responseInterceptorHandlers: [] as Array<(error: unknown) => unknown>,
  mockMessageError: vi.fn(),
}))

vi.mock('antd', () => ({
  message: {
    error: (...args: unknown[]) => mockMessageError(...args),
    success: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: {
          use: (fn: (config: unknown) => unknown) => {
            requestInterceptorHandlers.push(fn)
            return 0
          },
        },
        response: {
          use: (
            _onFulfilled: unknown,
            onRejected: (error: unknown) => unknown
          ) => {
            responseInterceptorHandlers.push(onRejected)
            return 0
          },
        },
      },
    })),
  },
}))

const mockGet = vi.fn()
const mockPost = vi.fn()

beforeEach(() => {
  vi.clearAllMocks()
})

describe('API Service', () => {
  describe('sessionApi', () => {
    it('should call getSessions with correct parameters', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await sessionApi.getSessions({ status: 'raw', page: 1, page_size: 10 })
      expect(mockGet).toHaveBeenCalledWith('/sessions', {
        params: { status: 'raw', page: 1, page_size: 10 },
      })
    })

    it('should call getSessionContent with sessionId', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await sessionApi.getSessionContent('session-123')
      expect(mockGet).toHaveBeenCalledWith('/sessions/session-123/content')
    })
  })

  describe('reviewerApi', () => {
    it('should call approveSession with sessionId and notes', async () => {
      const { api } = await import('../services')
      api.post = mockPost
      await reviewerApi.approveSession('session-123', 'Approved by reviewer')
      expect(mockPost).toHaveBeenCalledWith('/reviewer/approve/session-123', null, {
        params: { notes: 'Approved by reviewer', score: undefined },
      })
    })

    it('should call rejectSession with sessionId and notes', async () => {
      const { api } = await import('../services')
      api.post = mockPost
      await reviewerApi.rejectSession('session-123', 'Rejected by reviewer')
      expect(mockPost).toHaveBeenCalledWith('/reviewer/reject/session-123', null, {
        params: { notes: 'Rejected by reviewer', score: undefined },
      })
    })

    it('should call getPending with pagination', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await reviewerApi.getPending(1, 20)
      expect(mockGet).toHaveBeenCalledWith('/reviewer/pending', {
        params: { page: 1, page_size: 20 },
      })
    })
  })

  describe('exporterApi', () => {
    it('should call exportSessions with export data', async () => {
      const { api } = await import('../services')
      api.post = mockPost
      const exportData = { format: 'sharegpt', min_score: 4 }
      await exporterApi.exportSessions(exportData)
      expect(mockPost).toHaveBeenCalledWith('/exporter/export', exportData)
    })

    it('should call getHistory with limit', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await exporterApi.getHistory(10)
      expect(mockGet).toHaveBeenCalledWith('/exporter/history', {
        params: { limit: 10 },
      })
    })

    it('should call getFormats', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await exporterApi.getFormats()
      expect(mockGet).toHaveBeenCalledWith('/exporter/formats')
    })
  })

  describe('pluginApi', () => {
    it('should call getAll', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await pluginApi.getAll()
      expect(mockGet).toHaveBeenCalledWith('/plugins')
    })

    it('should call enable with plugin key', async () => {
      const { api } = await import('../services')
      api.post = mockPost
      await pluginApi.enable('collectors/openclaw')
      expect(mockPost).toHaveBeenCalledWith('/plugins/enable', null, {
        params: { key: 'collectors/openclaw' },
      })
    })

    it('should call disable with plugin key', async () => {
      const { api } = await import('../services')
      api.post = mockPost
      await pluginApi.disable('collectors/openclaw')
      expect(mockPost).toHaveBeenCalledWith('/plugins/disable', null, {
        params: { key: 'collectors/openclaw' },
      })
    })
  })

  describe('statsApi', () => {
    it('should call get', async () => {
      const { api } = await import('../services')
      api.get = mockGet
      await statsApi.get()
      expect(mockGet).toHaveBeenCalledWith('/stats')
    })
  })

  describe('request interceptor', () => {
    it('should attach Bearer header when VITE_API_KEY is set', async () => {
      // client.ts reads import.meta.env at module load; re-import via fresh query
      vi.stubEnv('VITE_API_KEY', 'test-secret')
      // Force fresh module evaluation
      const fresh = await import(`../services/client?key=${Date.now()}`)
      expect(requestInterceptorHandlers.length).toBeGreaterThan(0)
      const onRequest = requestInterceptorHandlers[requestInterceptorHandlers.length - 1]
      const config = { headers: {} as Record<string, string> }
      const result = onRequest(config)
      expect(result).toBe(config)
      expect(config.headers.Authorization).toBe('Bearer test-secret')
      vi.unstubAllEnvs()
      void fresh
    })

    it('should not attach Authorization header when VITE_API_KEY is empty', async () => {
      vi.stubEnv('VITE_API_KEY', '')
      await import(`../services/client?empty=${Date.now()}`)
      const onRequest = requestInterceptorHandlers[requestInterceptorHandlers.length - 1]
      const config = { headers: {} as Record<string, string> }
      onRequest(config)
      expect(config.headers.Authorization).toBeUndefined()
      vi.unstubAllEnvs()
    })
  })

  describe('response error interceptor', () => {
    it('should show string detail message on error', async () => {
      // Re-import client to trigger interceptor registration (cached module)
      await import('../services/client')
      expect(responseInterceptorHandlers.length).toBeGreaterThan(0)
      const onRejected = responseInterceptorHandlers[0]

      const error = { response: { status: 400, data: { detail: 'Bad request' } } }
      await expect(onRejected(error)).rejects.toBe(error)
      expect(mockMessageError).toHaveBeenCalledWith('Bad request')
    })

    it('should join array detail (pydantic validation) messages', async () => {
      await import('../services/client')
      const onRejected = responseInterceptorHandlers[0]

      const error = {
        response: {
          status: 422,
          data: {
            detail: [
              { msg: 'field required', loc: ['body', 'tags'] },
              { msg: 'too long', loc: ['body', 'notes'] },
            ],
          },
        },
      }
      await expect(onRejected(error)).rejects.toBe(error)
      expect(mockMessageError).toHaveBeenCalledWith('field required; too long')
    })

    it('should fall back to status-based text when detail is missing', async () => {
      await import('../services/client')
      const onRejected = responseInterceptorHandlers[0]

      const error = { response: { status: 401, data: {} } }
      await expect(onRejected(error)).rejects.toBe(error)
      expect(mockMessageError).toHaveBeenCalledWith('认证失败')
    })
  })
})
