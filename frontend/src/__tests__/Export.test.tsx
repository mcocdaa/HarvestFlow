import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Export from '../pages/Export';

vi.mock('../services', () => ({
  exporterApi: {
    getHistory: vi.fn(),
    getFormats: vi.fn(),
    exportSessions: vi.fn(),
    downloadExport: vi.fn(),
    downloadZip: vi.fn(),
  },
  sessionApi: {
    getSessions: vi.fn(),
  },
}));

import { exporterApi, sessionApi } from '../services';

const mockResponse = (data: unknown) => ({ data }) as never;

const mockHistory = [
  {
    id: 1,
    export_format: 'sharegpt',
    version: 'v1',
    record_count: 12,
    file_path: '/data/export/sharegpt_v1_abc.jsonl',
    filters: null,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    export_format: 'alpaca',
    version: 'v2',
    record_count: 3,
    file_path: '/data/export/alpaca_v2_def.jsonl',
    filters: null,
    created_at: '2026-01-02T00:00:00Z',
  },
];

describe('Export Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    URL.createObjectURL = vi.fn(() => 'blob:mock');
    URL.revokeObjectURL = vi.fn();

    vi.mocked(exporterApi.getHistory).mockResolvedValue(mockResponse({ exports: [] }))
    vi.mocked(exporterApi.getFormats).mockResolvedValue(mockResponse({ formats: ['sharegpt', 'alpaca'] }))
    vi.mocked(sessionApi.getSessions).mockResolvedValue(
      mockResponse({
        sessions: [
          {
            session_id: 's1',
            status: 'approved',
            agent_role: 'backend_dev',
            task_type: 'coding',
            tags: ['math'],
            created_at: '2026-01-01T00:00:00Z',
          },
        ],
        total: 1,
      })
    )
  });

  it('should render version as a text input, not a number input', async () => {
    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('导出配置')).toBeInTheDocument();
    });

    const versionInput = document.getElementById('version') as HTMLInputElement;
    expect(versionInput).toBeTruthy();
    expect(versionInput.getAttribute('role')).not.toBe('spinbutton');
  });

  it('should render task type and tags fields', async () => {
    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('任务类型')).toBeInTheDocument();
      expect(screen.getByText('标签')).toBeInTheDocument();
      expect(screen.getByText('最低人工评分')).toBeInTheDocument();
    });
  });

  it('should submit payload with default version v1 and first format', async () => {
    vi.mocked(exporterApi.exportSessions).mockResolvedValue(
      mockResponse({
        success: true,
        record_count: 5,
        filename: 'sharegpt_v1_x.jsonl',
        file_path: '/tmp/sharegpt_v1_x.jsonl',
      })
    );

    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('导出配置')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /导出会话/ }));

    await waitFor(() => {
      expect(exporterApi.exportSessions).toHaveBeenCalledTimes(1);
    });
    const payload = vi.mocked(exporterApi.exportSessions).mock.calls[0][0] as unknown as Record<string, unknown>;
    expect(payload.version).toBe('v1');
    expect(payload.format).toBe('sharegpt');
  });

  it('should render parsed history filters as chips', async () => {
    vi.mocked(exporterApi.getHistory).mockResolvedValue(
      mockResponse({
        exports: [
          {
            id: 1,
            export_format: 'sharegpt',
            version: 'v1',
            record_count: 12,
            file_path: '/data/export/sharegpt_v1_abc.jsonl',
            filters: '{"min_score":4,"tags":["math"]}',
            created_at: '2026-01-01T00:00:00Z',
          },
        ],
      })
    );

    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('min_score: 4')).toBeInTheDocument();
      expect(screen.getByText('tags: math')).toBeInTheDocument();
    });
  });

  it('should download a single export file', async () => {
    vi.mocked(exporterApi.getHistory).mockResolvedValue(mockResponse({ exports: [mockHistory[0]] }));
    vi.mocked(exporterApi.downloadExport).mockResolvedValue({
      data: new Blob(['x']),
      headers: { 'content-disposition': 'attachment; filename="sharegpt_v1_abc.jsonl"' },
    } as never);

    render(<Export />);

    await waitFor(() => {
      expect(screen.getByText('下载')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('下载').closest('button')!);

    await waitFor(() => {
      expect(exporterApi.downloadExport).toHaveBeenCalledWith('sharegpt_v1_abc.jsonl');
    });
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it('should zip selected export files', async () => {
    vi.mocked(exporterApi.getHistory).mockResolvedValue(mockResponse({ exports: mockHistory }));
    vi.mocked(exporterApi.downloadZip).mockResolvedValue({
      data: new Blob(['zip']),
      headers: { 'content-disposition': 'attachment; filename="harvestflow-exports.zip"' },
    } as never);

    render(<Export />);

    await waitFor(() => {
      expect(screen.getAllByText('下载')).toHaveLength(2);
    });

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    fireEvent.click(checkboxes[2]);

    const zipButton = screen.getByRole('button', { name: /打包下载/ });
    await waitFor(() => {
      expect(zipButton).toBeEnabled();
    });
    fireEvent.click(zipButton);

    await waitFor(() => {
      expect(exporterApi.downloadZip).toHaveBeenCalledWith([
        'sharegpt_v1_abc.jsonl',
        'alpaca_v2_def.jsonl',
      ]);
    });
  });
});
