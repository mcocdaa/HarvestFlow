import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from '../App'

vi.mock('../pages/Dashboard', () => ({
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}))

vi.mock('../pages/Sessions', () => ({
  default: () => <div data-testid="sessions-page">Sessions Page</div>,
}))

vi.mock('../pages/Review', () => ({
  default: () => <div data-testid="review-page">Review Page</div>,
}))

vi.mock('../pages/Export', () => ({
  default: () => <div data-testid="export-page">Export Page</div>,
}))

vi.mock('../pages/Plugins', () => ({
  default: () => <div data-testid="plugins-page">Plugins Page</div>,
}))

vi.mock('@ant-design/icons', () => {
  const stub = () => function IconStub() {
    return null
  }
  return {
    DashboardOutlined: stub(),
    FolderOutlined: stub(),
    CheckSquareOutlined: stub(),
    ExportOutlined: stub(),
    ApiOutlined: stub(),
    SearchOutlined: stub(),
    UserOutlined: stub(),
    CopyOutlined: stub(),
    EyeOutlined: stub(),
    RiseOutlined: stub(),
    MinusOutlined: stub(),
  }
})

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

  it('should navigate to pages when menu items are clicked', async () => {
    render(<App />)

    fireEvent.click(screen.getByText('Sessions'))
    expect(await screen.findByTestId('sessions-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Review'))
    expect(await screen.findByTestId('review-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Export'))
    expect(await screen.findByTestId('export-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Plugins'))
    expect(await screen.findByTestId('plugins-page')).toBeInTheDocument()
  })
})
