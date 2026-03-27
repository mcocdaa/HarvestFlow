import { describe, it, expect, vi, beforeEach } from 'vitest'
import api, {
  sessionApi,
  collectorApi,
  curatorApi,
  reviewerApi,
  exporterApi,
  pluginApi,
  statsApi,
} from '../services/api'

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
  const mockResponse = { data: { success: true } }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('sessionApi', () => {
    it('should call getSessions with correct parameters', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await sessionApi.getSessions({ status: 'raw', page: 1, page_size: 10 })

      expect(mockGet).toHaveBeenCalledWith('/sessions', {
        params: { status: 'raw', page: 1, page_size: 10 },
      })
    })

    it('should call getSession with sessionId', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await sessionApi.getSession('session-123')

      expect(mockGet).toHaveBeenCalledWith('/sessions/session-123')
    })

    it('should call createSession with session data', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost
      const sessionData = { title: 'Test Session' }

      await sessionApi.createSession(sessionData)

      expect(mockPost).toHaveBeenCalledWith('/sessions', sessionData)
    })

    it('should call updateSession with sessionId and updates', async () => {
      const mockPut = vi.fn().mockResolvedValue(mockResponse)
      api.put = mockPut
      const updates = { title: 'Updated Title' }

      await sessionApi.updateSession('session-123', updates)

      expect(mockPut).toHaveBeenCalledWith('/sessions/session-123', updates)
    })

    it('should call deleteSession with sessionId', async () => {
      const mockDelete = vi.fn().mockResolvedValue(mockResponse)
      api.delete = mockDelete

      await sessionApi.deleteSession('session-123')

      expect(mockDelete).toHaveBeenCalledWith('/sessions/session-123')
    })
  })

  describe('collectorApi', () => {
    it('should call scanFolder with folder path', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await collectorApi.scanFolder('/path/to/folder')

      expect(mockPost).toHaveBeenCalledWith('/collector/scan', null, {
        params: { folder_path: '/path/to/folder' },
      })
    })

    it('should call importSession with file path', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await collectorApi.importSession('/path/to/file.json')

      expect(mockPost).toHaveBeenCalledWith('/collector/import', null, {
        params: { file_path: '/path/to/file.json' },
      })
    })

    it('should call getConfig', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await collectorApi.getConfig()

      expect(mockGet).toHaveBeenCalledWith('/collector/config')
    })
  })

  describe('curatorApi', () => {
    it('should call evaluateSession with sessionId', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await curatorApi.evaluateSession('session-123')

      expect(mockPost).toHaveBeenCalledWith('/curator/evaluate/session-123')
    })

    it('should call evaluateAll', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await curatorApi.evaluateAll()

      expect(mockPost).toHaveBeenCalledWith('/curator/evaluate/all')
    })

    it('should call updateConfig with config data', async () => {
      const mockPut = vi.fn().mockResolvedValue(mockResponse)
      api.put = mockPut
      const config = { threshold: 0.8 }

      await curatorApi.updateConfig(config)

      expect(mockPut).toHaveBeenCalledWith('/curator/config', config)
    })
  })

  describe('reviewerApi', () => {
    it('should call approveSession with sessionId and notes', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await reviewerApi.approveSession('session-123', 'Approved by reviewer')

      expect(mockPost).toHaveBeenCalledWith('/reviewer/approve/session-123', null, {
        params: { notes: 'Approved by reviewer' },
      })
    })

    it('should call rejectSession with sessionId and notes', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await reviewerApi.rejectSession('session-123', 'Rejected by reviewer')

      expect(mockPost).toHaveBeenCalledWith('/reviewer/reject/session-123', null, {
        params: { notes: 'Rejected by reviewer' },
      })
    })

    it('should call batchApprove with sessionIds', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost
      const sessionIds = ['session-1', 'session-2']

      await reviewerApi.batchApprove(sessionIds)

      expect(mockPost).toHaveBeenCalledWith('/reviewer/batch-approve', {
        session_ids: sessionIds,
      })
    })

    it('should call getPending with pagination', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await reviewerApi.getPending(1, 20)

      expect(mockGet).toHaveBeenCalledWith('/reviewer/pending', {
        params: { page: 1, page_size: 20 },
      })
    })
  })

  describe('exporterApi', () => {
    it('should call exportSessions with export data', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost
      const exportData = { session_ids: ['session-1'], format: 'json' }

      await exporterApi.exportSessions(exportData)

      expect(mockPost).toHaveBeenCalledWith('/export', exportData)
    })

    it('should call getHistory with limit', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await exporterApi.getHistory(10)

      expect(mockGet).toHaveBeenCalledWith('/export/history', {
        params: { limit: 10 },
      })
    })

    it('should call getFormats', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await exporterApi.getFormats()

      expect(mockGet).toHaveBeenCalledWith('/export/formats')
    })
  })

  describe('pluginApi', () => {
    it('should call getAll', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await pluginApi.getAll()

      expect(mockGet).toHaveBeenCalledWith('/plugins')
    })

    it('should call getByType with plugin type', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await pluginApi.getByType('collector')

      expect(mockGet).toHaveBeenCalledWith('/plugins/collector')
    })

    it('should call getDetails with plugin type and name', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await pluginApi.getDetails('collector', 'json-collector')

      expect(mockGet).toHaveBeenCalledWith('/plugins/collector/json-collector')
    })

    it('should call enable with plugin name', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await pluginApi.enable('json-collector')

      expect(mockPost).toHaveBeenCalledWith('/plugins/json-collector/enable')
    })

    it('should call disable with plugin name', async () => {
      const mockPost = vi.fn().mockResolvedValue(mockResponse)
      api.post = mockPost

      await pluginApi.disable('json-collector')

      expect(mockPost).toHaveBeenCalledWith('/plugins/json-collector/disable')
    })
  })

  describe('statsApi', () => {
    it('should call get', async () => {
      const mockGet = vi.fn().mockResolvedValue(mockResponse)
      api.get = mockGet

      await statsApi.get()

      expect(mockGet).toHaveBeenCalledWith('/stats')
    })
  })
})
