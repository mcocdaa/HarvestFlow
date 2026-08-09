import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  sessionApi,
  reviewerApi,
  exporterApi,
  pluginApi,
  statsApi,
} from '../services'

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    })),
  },
}))

describe('API Service', () => {
  const mockGet = vi.fn()
  const mockPost = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

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
})
