import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import Dashboard from '../pages/Dashboard'
import { curatorApi, sessionApi, statsApi } from '../services'
import type { Stats } from '../types'

vi.mock('../services', () => ({
  statsApi: {
    get: vi.fn(),
  },
  sessionApi: {
    getSessions: vi.fn(),
  },
  curatorApi: {
    getStatus: vi.fn(),
    evaluateAll: vi.fn(),
  },
}))

vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }))

// Mock axios response shape (status/headers/config are not needed by components)
const mockResponse = (data: unknown) => ({ data }) as never

const mockSession = {
  session_id: 's1',
  status: 'approved' as const,
  quality_auto_score: 4,
  task_type: 'coding',
  created_at: '2026-01-01T00:00:00Z',
}

const setupMocks = (stats: Partial<Stats> = {}) => {
  vi.mocked(statsApi.get).mockResolvedValue(mockResponse(stats))
  vi.mocked(sessionApi.getSessions).mockResolvedValue(mockResponse({ sessions: [mockSession], total: 1 }))
  vi.mocked(curatorApi.getStatus).mockResolvedValue(
    mockResponse({ enabled: true, auto_approve_threshold: 4 })
  )
}

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render dashboard title', async () => {
    setupMocks()
    render(<Dashboard />)
    expect(screen.getByText('概览')).toBeInTheDocument()
  })

  it('should display statistic cards with default values', async () => {
    setupMocks()
    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('会话总数')).toBeInTheDocument()
      expect(screen.getByText('待清洗')).toBeInTheDocument()
      expect(screen.getByText('待审核')).toBeInTheDocument()
      expect(screen.getAllByText('已通过').length).toBeGreaterThan(0)
      expect(screen.getAllByText('已拒绝').length).toBeGreaterThan(0)
    })
  })

  it('should display correct statistics from API response', async () => {
    setupMocks({
      total_sessions: 100,
      raw_sessions: 30,
      approved_sessions: 60,
      rejected_sessions: 10,
      avg_auto_score: 4.5,
      curated_sessions: 70,
      reviewed_sessions: 70,
    })

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('30')).toBeInTheDocument()
      expect(screen.getByText('60')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument()
    })

    expect(screen.getByText('质量与审核')).toBeInTheDocument()
    expect(screen.getByText('清洗器')).toBeInTheDocument()
    expect(screen.getByText('已启用')).toBeInTheDocument()
  })

  it('should render recent sessions', async () => {
    setupMocks()

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('最近会话')).toBeInTheDocument()
      expect(screen.getByText('coding')).toBeInTheDocument()
    })
  })

  it('should handle API error gracefully', async () => {
    vi.mocked(statsApi.get).mockRejectedValue(new Error('API Error'))
    vi.mocked(sessionApi.getSessions).mockRejectedValue(new Error('API Error'))
    vi.mocked(curatorApi.getStatus).mockRejectedValue(new Error('API Error'))

    render(<Dashboard />)

    await waitFor(() => {
      expect(document.querySelector('.ant-card-loading')).toBeFalsy()
    })

    expect(screen.getByText('概览')).toBeInTheDocument()
    expect(screen.getByText('会话总数')).toBeInTheDocument()
  })

  it('should show loading state while fetching stats', async () => {
    let resolveGet: (value: unknown) => void
    vi.mocked(statsApi.get).mockReturnValue(
      new Promise((resolve) => {
        resolveGet = resolve
      }) as never
    )
    vi.mocked(sessionApi.getSessions).mockResolvedValue(mockResponse({ sessions: [], total: 0 }))
    vi.mocked(curatorApi.getStatus).mockResolvedValue(
      mockResponse({ enabled: true, auto_approve_threshold: 4 })
    )

    render(<Dashboard />)

    expect(document.querySelector('.ant-card-loading')).toBeTruthy()

    await act(async () => {
      resolveGet({ data: {} })
    })

    await waitFor(() => {
      expect(document.querySelector('.ant-card-loading')).toBeFalsy()
    })
  })

  it('should warn when curator is disabled', async () => {
    setupMocks()
    vi.mocked(curatorApi.getStatus).mockResolvedValue(
      mockResponse({ enabled: false, auto_approve_threshold: 4 })
    )

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('已禁用')).toBeInTheDocument()
      expect(screen.getByText(/清洗器当前禁用/)).toBeInTheDocument()
    })
  })
})
