import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Review from '../pages/Review'

vi.mock('../services', () => ({
  reviewerApi: {
    getPending: vi.fn(),
    approveSession: vi.fn(),
    rejectSession: vi.fn(),
    batchApprove: vi.fn(),
    batchReject: vi.fn(),
    getAuditLogs: vi.fn(),
  },
  sessionApi: {
    getSessionContent: vi.fn(),
  },
}))

import { reviewerApi, sessionApi } from '../services'

// Mock axios response shape (status/headers/config are not needed by components)
const mockResponse = <T,>(data: T) => ({ data }) as never

// Simulate clipboard API
Object.defineProperty(navigator, 'clipboard', {
  writable: true,
  value: { writeText: vi.fn().mockResolvedValue(undefined) },
})

function mockSession(id: string, status = 'curated') {
  return {
    session_id: id,
    status,
    quality_auto_score: 4,
    agent_role: 'assistant',
    task_type: 'qa',
    created_at: '2026-01-01T00:00:00Z',
  }
}

const mockContent = {
  messages: [
    { role: 'user', content: 'Hello' },
    { role: 'assistant', content: 'Hi there' },
  ],
  metadata: { tokens: 100 },
}

describe('Review Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(reviewerApi.getAuditLogs).mockResolvedValue(mockResponse({ logs: [] }))
  })

  it('should render review page with queue and approve button', async () => {
    vi.mocked(reviewerApi.getPending).mockResolvedValue(
      mockResponse({ sessions: [mockSession('s1'), mockSession('s2'), mockSession('s3')] })
    )
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue(mockResponse({ content: mockContent }))

    render(<Review />)

    await waitFor(() => {
      expect(screen.getByText('通过评审')).toBeInTheDocument()
      expect(screen.getByText(/第 1 \/ 3 条/)).toBeInTheDocument()
    })
    expect(reviewerApi.getPending).toHaveBeenCalledTimes(1)
    await waitFor(() => {
      expect(sessionApi.getSessionContent).toHaveBeenCalledWith('s1')
    })
  })

  it('should approve current session and advance queue locally', async () => {
    vi.mocked(reviewerApi.getPending).mockResolvedValue(
      mockResponse({ sessions: [mockSession('s1'), mockSession('s2'), mockSession('s3')] })
    )
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue(mockResponse({ content: mockContent }))
    vi.mocked(reviewerApi.approveSession).mockResolvedValue(mockResponse({ success: true }))

    render(<Review />)

    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 3 条/)).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(sessionApi.getSessionContent).toHaveBeenCalledWith('s1')
    })

    fireEvent.click(screen.getByText('通过评审'))

    await waitFor(() => {
      expect(reviewerApi.approveSession).toHaveBeenCalledTimes(1)
      expect(reviewerApi.approveSession).toHaveBeenCalledWith('s1', '', 3)
    })

    // 本地移除后自动前进到 s2，队列总数减少
    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 2 条/)).toBeInTheDocument()
      expect(sessionApi.getSessionContent).toHaveBeenCalledWith('s2')
    })
  })

  it('should reload when queue becomes empty', async () => {
    let getPendingCall = 0
    vi.mocked(reviewerApi.getPending).mockImplementation(() => {
      getPendingCall += 1
      if (getPendingCall === 1) {
        return Promise.resolve(mockResponse({ sessions: [mockSession('s1')] }))
      }
      return Promise.resolve(mockResponse({ sessions: [] }))
    })
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue(mockResponse({ content: mockContent }))
    vi.mocked(reviewerApi.approveSession).mockResolvedValue(mockResponse({ success: true }))

    render(<Review />)

    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 1 条/)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('通过评审'))

    await waitFor(() => {
      expect(reviewerApi.getPending).toHaveBeenCalledTimes(2)
      expect(screen.getByText('审核队列已清空，去会话页看看新数据吧')).toBeInTheDocument()
    })
  })

  it(
    'should batch approve selected sessions in batch mode',
    async () => {
      vi.mocked(reviewerApi.getPending).mockResolvedValue(
        mockResponse({ sessions: [mockSession('s1'), mockSession('s2')] })
      )
      vi.mocked(sessionApi.getSessionContent).mockResolvedValue(mockResponse({ content: mockContent }))
      vi.mocked(reviewerApi.batchApprove).mockResolvedValue(
        mockResponse({ total: 1, success: 1, failed: 0, results: [{ session_id: 's1', success: true }] })
      )

      render(<Review />)

      const batchTab = await screen.findByText('批量处理')
      fireEvent.click(batchTab)

      // 等待批量面板加载出行数据后勾选第一行
      await screen.findAllByText('qa')
      const checkboxes = screen.getAllByRole('checkbox')
      fireEvent.click(checkboxes[1])

      fireEvent.click(screen.getByRole('button', { name: /批量通过/ }))
      await screen.findByRole('tooltip')
      fireEvent.click(screen.getByText(/确\s*认\s*通\s*过/))

      await waitFor(() => {
        expect(reviewerApi.batchApprove).toHaveBeenCalledWith(['s1'])
      })
    },
    15000
  )

  it('should open audit log drawer', async () => {
    vi.mocked(reviewerApi.getPending).mockResolvedValue(mockResponse({ sessions: [] }))
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue(mockResponse({ content: mockContent }))
    vi.mocked(reviewerApi.getAuditLogs).mockResolvedValue(
      mockResponse({
        logs: [
          {
            id: 1,
            session_id: 's1',
            action: 'approve',
            operator: 'user',
            details: 'ok',
            created_at: '2026-01-01T00:00:00Z',
          },
        ],
      })
    )

    render(<Review />)

    fireEvent.click(await screen.findByRole('button', { name: /审计日志/ }))

    await waitFor(() => {
      expect(screen.getByText('通过')).toBeInTheDocument()
      expect(screen.getByText('人工')).toBeInTheDocument()
    })
  })
})
