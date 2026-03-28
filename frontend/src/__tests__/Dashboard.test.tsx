import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import Dashboard from '../pages/Dashboard'
import { statsApi } from '../services'

vi.mock('../services', () => ({
  statsApi: {
    get: vi.fn(),
  },
}))

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render dashboard title', () => {
    vi.mocked(statsApi.get).mockResolvedValue({ data: {} } as any)
    render(<Dashboard />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('should display statistics cards with default values', async () => {
    vi.mocked(statsApi.get).mockResolvedValue({ data: {} } as any)
    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Total Sessions')).toBeInTheDocument()
      expect(screen.getByText('Raw Sessions')).toBeInTheDocument()
      expect(screen.getByText('Approved')).toBeInTheDocument()
      expect(screen.getByText('Rejected')).toBeInTheDocument()
    })
  })

  it('should display correct statistics from API response', async () => {
    const mockStats = {
      total_sessions: 100,
      raw_sessions: 30,
      approved_sessions: 60,
      rejected_sessions: 10,
      avg_auto_score: 8.5,
      curated_sessions: 70,
    }
    vi.mocked(statsApi.get).mockResolvedValue({ data: mockStats } as any)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('30')).toBeInTheDocument()
      expect(screen.getByText('60')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument()
    })

    expect(screen.getByText('Average Auto Score')).toBeInTheDocument()
    expect(screen.getByText('Curated Sessions')).toBeInTheDocument()
  })

  it('should handle API error gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.mocked(statsApi.get).mockRejectedValue(new Error('API Error'))

    render(<Dashboard />)

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load stats:', expect.any(Error))
    })

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('should display average auto score card', async () => {
    vi.mocked(statsApi.get).mockResolvedValue({
      data: { avg_auto_score: 7.8 },
    } as any)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Average Auto Score')).toBeInTheDocument()
    })
  })

  it('should display curated sessions card', async () => {
    vi.mocked(statsApi.get).mockResolvedValue({
      data: { curated_sessions: 50 },
    } as any)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Curated Sessions')).toBeInTheDocument()
    })
  })
})
