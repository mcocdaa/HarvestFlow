import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Plugins from '../pages/Plugins';

vi.mock('../services', () => ({
  pluginApi: {
    getAll: vi.fn(),
    enable: vi.fn(),
    disable: vi.fn(),
  },
}));

import { pluginApi } from '../services';

const plugins = [
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
    key: 'services/infisical',
    name: 'Infisical',
    version: '0.5.0',
    description: 'A secret service',
    author: 'Test Author',
    plugin_type: 'services',
    enabled: false,
  },
];

describe('Plugins Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(pluginApi.getAll).mockResolvedValue({ data: { plugins } } as never);
  });

  it('should load all plugins via getAll', async () => {
    render(<Plugins />);

    await waitFor(() => {
      expect(pluginApi.getAll).toHaveBeenCalledTimes(1);
      expect(screen.getByText('OpenClaw')).toBeInTheDocument();
      expect(screen.getByText('Infisical')).toBeInTheDocument();
    });
  });

  it('should render switches reflecting enabled state', async () => {
    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('OpenClaw')).toBeInTheDocument();
    });

    const switches = screen.getAllByRole('switch');
    expect(switches[0]).toBeChecked();
    expect(switches[1]).not.toBeChecked();
  });

  it('should render all type tabs with counts', async () => {
    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('全部（2）')).toBeInTheDocument();
      expect(screen.getByText('采集器（1）')).toBeInTheDocument();
      expect(screen.getByText('清洗器（0）')).toBeInTheDocument();
      expect(screen.getByText('审核器（0）')).toBeInTheDocument();
      expect(screen.getByText('服务（1）')).toBeInTheDocument();
    });
  });

  it('should enable plugin directly on switch toggle', async () => {
    vi.mocked(pluginApi.enable).mockResolvedValue({ data: { success: true } } as never);

    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('Infisical')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole('switch')[1]);

    await waitFor(() => {
      expect(pluginApi.enable).toHaveBeenCalledWith('services/infisical');
    });
  });

  it('should require confirmation before disabling plugin', async () => {
    vi.mocked(pluginApi.disable).mockResolvedValue({ data: { success: true } } as never);

    render(<Plugins />);

    await waitFor(() => {
      expect(screen.getByText('OpenClaw')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole('switch')[0]);

    // 弹窗确认后才调用 disable（antd 会在两个汉字的按钮文本中插入空格）
    expect(pluginApi.disable).not.toHaveBeenCalled();
    fireEvent.click(await screen.findByRole('button', { name: /停\s*用/ }));

    await waitFor(() => {
      expect(pluginApi.disable).toHaveBeenCalledWith('collectors/openclaw');
    });
  });
});
