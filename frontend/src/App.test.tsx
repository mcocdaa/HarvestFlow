import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

vi.mock('./pages/Dashboard', () => ({
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}))

vi.mock('./pages/Sessions', () => ({
  default: () => <div data-testid="sessions-page">Sessions Page</div>,
}))

vi.mock('./pages/Review', () => ({
  default: () => <div data-testid="review-page">Review Page</div>,
}))

vi.mock('./pages/Export', () => ({
  default: () => <div data-testid="export-page">Export Page</div>,
}))

vi.mock('./pages/Plugins', () => ({
  default: () => <div data-testid="plugins-page">Plugins Page</div>,
}))

vi.mock('@ant-design/icons', () => ({
  DashboardOutlined: () => <span data-testid="dashboard-icon" />,
  FolderOutlined: () => <span data-testid="folder-icon" />,
  CheckSquareOutlined: () => <span data-testid="check-icon" />,
  ExportOutlined: () => <span data-testid="export-icon" />,
  ApiOutlined: () => <span data-testid="plugin-icon" />,
}))

describe('App Component', () => {
  it('should render app header with title', () => {
    render(<App />)
    expect(screen.getByText('HarvestFlow')).toBeInTheDocument()
  })

  it('should render navigation menu with all items', () => {
    render(<App />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Sessions')).toBeInTheDocument()
    expect(screen.getByText('Review')).toBeInTheDocument()
    expect(screen.getByText('Export')).toBeInTheDocument()
    expect(screen.getByText('Plugins')).toBeInTheDocument()
  })

  it('should have correct navigation links', () => {
    render(<App />)

    const dashboardLink = screen.getByText('Dashboard').closest('a')
    const sessionsLink = screen.getByText('Sessions').closest('a')
    const reviewLink = screen.getByText('Review').closest('a')
    const exportLink = screen.getByText('Export').closest('a')
    const pluginsLink = screen.getByText('Plugins').closest('a')

    expect(dashboardLink).toHaveAttribute('href', '/')
    expect(sessionsLink).toHaveAttribute('href', '/sessions')
    expect(reviewLink).toHaveAttribute('href', '/review')
    expect(exportLink).toHaveAttribute('href', '/export')
    expect(pluginsLink).toHaveAttribute('href', '/plugins')
  })
})
