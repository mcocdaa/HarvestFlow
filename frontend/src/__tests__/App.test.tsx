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

vi.mock('../pages/Collect', () => ({
  default: () => <div data-testid="collect-page">Collect Page</div>,
}))

vi.mock('../pages/Export', () => ({
  default: () => <div data-testid="export-page">Export Page</div>,
}))

vi.mock('../pages/Plugins', () => ({
  default: () => <div data-testid="plugins-page">Plugins Page</div>,
}))

vi.mock('../pages/NotFound', () => ({
  default: () => <div data-testid="notfound-page">404 Not Found</div>,
}))

vi.mock('../services', () => ({
  statsApi: {
    get: vi.fn().mockResolvedValue({ data: { curated_sessions: 3 } }),
  },
}))

describe('App Component', () => {
  it('should render app title', () => {
    render(<App />)
    expect(screen.getByText('HarvestFlow')).toBeInTheDocument()
  })

  it('should render navigation menu with all items', async () => {
    render(<App />)

    expect(await screen.findByText('概览')).toBeInTheDocument()
    expect(screen.getByText('会话')).toBeInTheDocument()
    expect(screen.getByText('审核')).toBeInTheDocument()
    expect(screen.getByText('采集')).toBeInTheDocument()
    expect(screen.getByText('导出')).toBeInTheDocument()
    expect(screen.getByText('插件')).toBeInTheDocument()
  })

  it('should navigate to pages when menu items are clicked', async () => {
    render(<App />)

    fireEvent.click(await screen.findByText('会话'))
    expect(await screen.findByTestId('sessions-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('审核'))
    expect(await screen.findByTestId('review-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('采集'))
    expect(await screen.findByTestId('collect-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('导出'))
    expect(await screen.findByTestId('export-page')).toBeInTheDocument()

    fireEvent.click(screen.getByText('插件'))
    expect(await screen.findByTestId('plugins-page')).toBeInTheDocument()
  })

  it('should render 404 page for unknown routes', async () => {
    window.history.pushState({}, '', '/unknown-route')

    render(<App />)

    expect(await screen.findByTestId('notfound-page')).toBeInTheDocument()
  })
})
