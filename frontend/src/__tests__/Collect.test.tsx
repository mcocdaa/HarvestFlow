import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import Collect from '../pages/Collect';

vi.mock('../services', () => ({
  collectorApi: {
    getWatchFolders: vi.fn(),
    addWatchFolder: vi.fn(),
    removeWatchFolder: vi.fn(),
    scan: vi.fn(),
    importFile: vi.fn(),
    importAll: vi.fn(),
    getWatchState: vi.fn(),
    watchStart: vi.fn(),
    watchStop: vi.fn(),
    watchRun: vi.fn(),
  },
}));

import { collectorApi } from '../services';

const mockResponse = (data: unknown) => ({ data }) as never;

describe('Collect Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(collectorApi.getWatchFolders).mockResolvedValue(
      mockResponse({ watch_folders: ['/data/sessions'] })
    );
    vi.mocked(collectorApi.getWatchState).mockResolvedValue(
      mockResponse({ enabled: false, running: false, interval: 30, folders: ['/data/sessions'], last_runs: {} })
    );
  });

  it('should render watch folders', async () => {
    render(<Collect />);

    await waitFor(() => {
      expect(screen.getByText('/data/sessions')).toBeInTheDocument();
    });
  });

  it('should add watch folder', async () => {
    vi.mocked(collectorApi.addWatchFolder).mockResolvedValue(mockResponse({ success: true }));

    render(<Collect />);

    await waitFor(() => {
      expect(screen.getByText('/data/sessions')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('如 /data/openclaw/sessions');
    fireEvent.change(input, { target: { value: '/data/new' } });
    fireEvent.click(screen.getByRole('button', { name: /添加/ }));

    await waitFor(() => {
      expect(collectorApi.addWatchFolder).toHaveBeenCalledWith('/data/new');
    });
  });

  it('should render watch state and toggle watching', async () => {
    vi.mocked(collectorApi.getWatchState).mockResolvedValue(
      mockResponse({
        enabled: false,
        running: false,
        interval: 15,
        folders: ['/data/sessions'],
        last_runs: {
          '/data/sessions': { total: 2, imported: 1, skipped: 1, failed: 0, at: '2026-01-01T00:00:00Z' },
        },
      })
    );
    vi.mocked(collectorApi.watchStart).mockResolvedValue(mockResponse({ enabled: true, running: true }));

    render(<Collect />);

    await waitFor(() => {
      expect(screen.getByText(/每 15 秒/)).toBeInTheDocument();
    });
    expect(screen.getByText('未运行')).toBeInTheDocument();
    expect(screen.getByText(/导入 1 \/ 跳过 1 \/ 失败 0/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('switch'));
    await waitFor(() => {
      expect(collectorApi.watchStart).toHaveBeenCalledTimes(1);
    });
  });

  it('should run watch scan once', async () => {
    vi.mocked(collectorApi.getWatchState).mockResolvedValue(
      mockResponse({ enabled: true, running: true, interval: 30, folders: [], last_runs: {} })
    );
    vi.mocked(collectorApi.watchRun).mockResolvedValue(
      mockResponse({ results: { '/a': { total: 1, imported: 1, skipped: 0, failed: 0 } } })
    );

    render(<Collect />);

    fireEvent.click(await screen.findByRole('button', { name: /立即运行一次/ }));
    await waitFor(() => {
      expect(collectorApi.watchRun).toHaveBeenCalledTimes(1);
    });
  });

  it('should scan folder and import a single file', async () => {
    vi.mocked(collectorApi.scan).mockResolvedValue(
      mockResponse({ folder_path: '/data/sessions', files_found: 1, files: ['/data/sessions/a.json'] })
    );
    vi.mocked(collectorApi.importFile).mockResolvedValue(mockResponse({ session_id: 's1' }));

    render(<Collect />);

    await waitFor(() => {
      expect(screen.getByText('/data/sessions')).toBeInTheDocument();
    });

    const scanInput = screen.getByPlaceholderText('待扫描目录，留空则使用第一个监听目录');
    await waitFor(() => {
      expect((scanInput as HTMLInputElement).value).toBe('/data/sessions');
    });

    fireEvent.click(screen.getByRole('button', { name: /扫描/ }));

    await waitFor(() => {
      expect(collectorApi.scan).toHaveBeenCalledWith('/data/sessions');
      expect(screen.getByText('/data/sessions/a.json')).toBeInTheDocument();
    });

    fireEvent.click(within(screen.getByRole('table')).getByRole('button', { name: /导入/ }));

    await waitFor(() => {
      expect(collectorApi.importFile).toHaveBeenCalledWith('/data/sessions/a.json');
    });
  });

  it(
    'should import all files',
    async () => {
    vi.mocked(collectorApi.scan).mockResolvedValue(
      mockResponse({ folder_path: '/data/sessions', files_found: 2, files: ['/a.json', '/b.json'] })
    );
    vi.mocked(collectorApi.importAll).mockResolvedValue(
      mockResponse({
        total: 2,
        imported: 1,
        skipped: 1,
        failed: 0,
        session_ids: ['s1'],
        skipped_ids: ['s2'],
        failed_files: [],
      })
    );

    render(<Collect />);

    await waitFor(() => {
      expect(screen.getByText('/data/sessions')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /扫描/ }));
    await waitFor(() => {
      expect(screen.getByText('/a.json')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /全部导入/ }));

    await waitFor(() => {
      expect(collectorApi.importAll).toHaveBeenCalledWith('/data/sessions');
      expect(screen.getByText(/成功 1，跳过 1，失败 0/)).toBeInTheDocument();
    });
  },
    15000
  );
});
