import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import SessionTable from '../components/sessions/SessionTable'
import type { Session } from '../types'

// Mock antd icons
vi.mock('@ant-design/icons', () => {
  const stub = () => function IconStub() {
    return null
  }
  return {
    EyeOutlined: stub(),
    CopyOutlined: stub(),
    RiseOutlined: stub(),
    MinusOutlined: stub(),
  }
})

describe('SessionTable Component', () => {
  const mockSessions: Session[] = [
    {
      session_id: 'abc123def456ghi789',
      status: 'approved',
      quality_auto_score: 8,
      quality_manual_score: 9,
      agent_role: 'coder',
      task_type: 'code_generation',
      created_at: '2024-01-15T10:30:00Z',
    },
    {
      session_id: 'xyz789uvw456rst123',
      status: 'raw',
      agent_role: 'reviewer',
      task_type: 'code_review',
      created_at: '2024-01-16T14:00:00Z',
    },
  ]

  const defaultProps = {
    sessions: mockSessions,
    loading: false,
    total: 42,
    page: 2,
    pageSize: 20,
    onPageChange: vi.fn(),
    onViewSession: vi.fn(),
  }

  it('should render session summaries using task_type directly (not O(n²) find)', () => {
    render(<SessionTable {...defaultProps} />)

    // The summary column should display the task_type from the record directly
    expect(screen.getByText('code_generation')).toBeInTheDocument()
    expect(screen.getByText('code_review')).toBeInTheDocument()
  })

  it('should display "无摘要信息" when task_type is missing', () => {
    const sessionsWithoutTaskType: Session[] = [
      {
        session_id: 'nosummary001',
        status: 'raw',
        created_at: '2024-01-01T00:00:00Z',
      },
    ]

    render(<SessionTable {...defaultProps} sessions={sessionsWithoutTaskType} />)

    expect(screen.getByText('无摘要信息')).toBeInTheDocument()
  })

  it('should display pagination info with total count', () => {
    render(<SessionTable {...defaultProps} />)

    // Ant Design pagination showTotal format: "共 42 条"
    expect(screen.getByText(/共 42 条/)).toBeInTheDocument()
  })

  it('should render status correctly', () => {
    render(<SessionTable {...defaultProps} />)

    expect(screen.getByText('approved')).toBeInTheDocument()
    expect(screen.getByText('raw')).toBeInTheDocument()
  })

  it('should render auto score as Tag when present', () => {
    render(<SessionTable {...defaultProps} />)

    // Session 1 has score 8, should render as Tag
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('should render "-" for missing auto score', () => {
    render(<SessionTable {...defaultProps} />)

    // Session 2 has no auto score, should show "-"
    // Both "-" for auto score and "-" for manual score may exist
    const dashes = screen.getAllByText('-')
    expect(dashes.length).toBeGreaterThan(0)
  })

  it('should call onViewSession when view button is clicked', () => {
    const onViewSession = vi.fn()
    render(<SessionTable {...defaultProps} onViewSession={onViewSession} />)

    const viewButtons = screen.getAllByText('查看')
    viewButtons[0].click()

    expect(onViewSession).toHaveBeenCalledWith(mockSessions[0])
  })
})
