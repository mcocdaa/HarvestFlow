import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import Sessions from '../pages/Sessions';

vi.mock('../services', () => ({
  sessionApi: {
    getSessions: vi.fn(),
    getSessionContent: vi.fn(),
    updateSession: vi.fn(),
    deleteSession: vi.fn(),
  },
  curatorApi: {
    evaluate: vi.fn(),
  },
}));

import { curatorApi, sessionApi } from '../services';

const mockResponse = (data: unknown) => ({ data }) as never;

const sessions = [
  {
    session_id: 's1',
    status: 'curated',
    quality_auto_score: 4,
    quality_manual_score: null,
    agent_role: 'backend_dev',
    task_type: 'coding',
    tags: ['math'],
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    session_id: 's2',
    status: 'raw',
    quality_auto_score: null,
    quality_manual_score: null,
    agent_role: null,
    task_type: null,
    tags: [],
    created_at: '2026-01-02T00:00:00Z',
  },
];

describe('Sessions Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(sessionApi.getSessions).mockResolvedValue(mockResponse({ sessions, total: 2 }));
  });

  it('should load sessions via ProTable request', async () => {
    render(<Sessions />);

    await waitFor(() => {
      expect(sessionApi.getSessions).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1, page_size: 20, sort: 'recent' })
      );
      expect(screen.getByText('coding')).toBeInTheDocument();
      expect(screen.getByText('未分类')).toBeInTheDocument();
    });
  });

  it('should open drawer with session content', async () => {
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue(
      mockResponse({ content: { messages: [{ role: 'user', content: 'Hello from session' }] } })
    );

    render(<Sessions />);

    await waitFor(() => {
      expect(screen.getByText('coding')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole('button', { name: /查看/ })[0]);

    await waitFor(() => {
      expect(sessionApi.getSessionContent).toHaveBeenCalledWith('s1');
      expect(screen.getByText('Hello from session')).toBeInTheDocument();
    });
  });

  it(
    'should delete session after confirmation',
    async () => {
      vi.mocked(sessionApi.deleteSession).mockResolvedValue(mockResponse(undefined));

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('coding')).toBeInTheDocument();
      });

      fireEvent.click(screen.getAllByRole('button', { name: /删除/ })[0]);
      const tooltip = await screen.findByRole('tooltip');
      fireEvent.click(within(tooltip).getByRole('button', { name: /删\s*除/ }));

      await waitFor(() => {
        expect(sessionApi.deleteSession).toHaveBeenCalledWith('s1');
      });
    },
    15000
  );

  it('should evaluate raw session only', async () => {
    vi.mocked(curatorApi.evaluate).mockResolvedValue(
      mockResponse({ score: 3, is_high_value: false, auto_approved: false })
    );

    render(<Sessions />);

    await waitFor(() => {
      expect(screen.getByText('coding')).toBeInTheDocument();
    });

    // 只有 raw 状态的行才有「评分」按钮
    const evaluateButtons = screen.getAllByRole('button', { name: /评分/ });
    expect(evaluateButtons).toHaveLength(1);

    fireEvent.click(evaluateButtons[0]);

    await waitFor(() => {
      expect(curatorApi.evaluate).toHaveBeenCalledWith('s2');
    });
  });
});
