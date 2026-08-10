import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Plugins from '../pages/Plugins';

vi.mock('../services', () => ({
  pluginApi: {
    getByType: vi.fn(),
    enable: vi.fn(),
    disable: vi.fn(),
  },
}));

import { pluginApi } from '../services';

const mockPlugins = {
  collectors: [
    {
      key: 'collectors/openclaw',
      name: 'OpenClaw',
      version: '1.0.0',
      description: 'A test collector',
      author: 'Test Author',
      plugin_type: 'collectors',
      enabled: true,
    },
    {
      key: 'collectors/disabled-plugin',
      name: 'Disabled Collector',
      version: '0.5.0',
      description: 'A disabled collector',
      author: 'Test Author',
      plugin_type: 'collectors',
      enabled: false,
    },
  ],
};

describe('Plugins Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render Switch as checked when plugin is enabled', async () => {
    (pluginApi.getByType as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { plugins: [mockPlugins.collectors[0]] },
    });

    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('OpenClaw')).toBeInTheDocument();
    });

    const switches = screen.getAllByRole('switch');
    expect(switches.length).toBe(1);
    expect(switches[0]).toBeChecked();
  });

  it('should render Switch as unchecked when plugin is disabled', async () => {
    (pluginApi.getByType as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { plugins: [mockPlugins.collectors[1]] },
    });

    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('Disabled Collector')).toBeInTheDocument();
    });

    const switches = screen.getAllByRole('switch');
    expect(switches.length).toBe(1);
    expect(switches[0]).not.toBeChecked();
  });

  it('should call getByType with collector type on initial load', async () => {
    (pluginApi.getByType as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { plugins: [] },
    });

    render(<Plugins />);

    await waitFor(() => {
      expect(pluginApi.getByType).toHaveBeenCalledWith('collectors');
    });
  });

  it('should render only collectors and curators tabs', async () => {
    (pluginApi.getByType as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { plugins: [] },
    });

    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('Collectors')).toBeInTheDocument();
    });

    expect(screen.getByText('Curators')).toBeInTheDocument();
    // reviewers tab was removed since backend has no reviewer plugins
    expect(screen.queryByText('Reviewers')).not.toBeInTheDocument();
  });
});
