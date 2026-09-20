import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Review from '../pages/Review';

vi.mock('../services', () => ({
  reviewerApi: {
    getPending: vi.fn(),
    getExtraFields: vi.fn(),
    approveSession: vi.fn(),
    rejectSession: vi.fn(),
    batchApprove: vi.fn(),
    batchReject: vi.fn(),
    getAuditLogs: vi.fn(),
  },
  sessionApi: {
    getSessionContent: vi.fn(),
  },
}));

import { reviewerApi, sessionApi } from '../services';

const mockResponse = <T,>(data: T) => ({ data }) as never;

function mockSession(id: string) {
  return {
    session_id: id,
    status: 'curated' as const,
    quality_auto_score: 4,
    agent_role: 'coding_agent',
    task_type: 'code_refactor',
    created_at: '2026-09-20T12:00:00Z',
  };
}

const mockContent = {
  messages: [
    { role: 'user', content: 'Fix the memory leak in worker' },
    { role: 'assistant', content: 'Here is the fix: use WeakMap instead of Map' },
  ],
  metadata: { tokens: 80 },
};

describe('Review Ergonomics & Three-Column Workspace', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(reviewerApi.getAuditLogs).mockResolvedValue(mockResponse({ logs: [] }));
    vi.mocked(reviewerApi.getExtraFields).mockResolvedValue(mockResponse({ fields: [] }));
    vi.mocked(reviewerApi.getPending).mockResolvedValue(
      mockResponse({ sessions: [mockSession('sess-001'), mockSession('sess-002'), mockSession('sess-003')] })
    );
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue(mockResponse({ content: mockContent }));
    vi.mocked(reviewerApi.approveSession).mockResolvedValue(mockResponse({ success: true }));
    vi.mocked(reviewerApi.rejectSession).mockResolvedValue(mockResponse({ success: true }));
  });

  it('should render three-column layout (Queue 20%, Stream 55%, Decision 25%)', async () => {
    const { container } = render(<Review />);

    await waitFor(() => {
      expect(container.querySelector('.review-col-queue')).toBeInTheDocument();
      expect(container.querySelector('.review-col-content')).toBeInTheDocument();
      expect(container.querySelector('.review-col-decision')).toBeInTheDocument();
      expect(screen.getByText(/待审队列 \(3\)/)).toBeInTheDocument();
      expect(screen.getByText('评审决策')).toBeInTheDocument();
    });
  });

  it('should support A key shortcut to approve session and advance queue', async () => {
    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 3 条/)).toBeInTheDocument();
    });

    // 按键盘 'a' 触发通过评审
    fireEvent.keyDown(window, { key: 'a' });

    await waitFor(() => {
      expect(reviewerApi.approveSession).toHaveBeenCalledWith('sess-001', '', 3, undefined);
      expect(screen.getByText(/第 1 \/ 2 条/)).toBeInTheDocument();
    });
  });

  it('should support R key shortcut to reject session and advance queue', async () => {
    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 3 条/)).toBeInTheDocument();
    });

    // 按键盘 'r' 触发拒绝
    fireEvent.keyDown(window, { key: 'r' });

    await waitFor(() => {
      expect(reviewerApi.rejectSession).toHaveBeenCalledWith('sess-001', '', 3, undefined);
    });
  });

  it('should support 1-5 keys to set quality rating score', async () => {
    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText('质量评分 (直按 1~5 键)')).toBeInTheDocument();
    });

    // 按键盘 '5' 设定为 5 星
    fireEvent.keyDown(window, { key: '5' });

    // 按 'a' 提交
    fireEvent.keyDown(window, { key: 'a' });

    await waitFor(() => {
      expect(reviewerApi.approveSession).toHaveBeenCalledWith('sess-001', '', 5, undefined);
    });
  });

  it('should support J and K keys to navigate queue up and down', async () => {
    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 3 条/)).toBeInTheDocument();
    });

    // 按 'j' 下移游标
    fireEvent.keyDown(window, { key: 'j' });
    await waitFor(() => {
      expect(screen.getByText(/第 2 \/ 3 条/)).toBeInTheDocument();
    });

    // 按 'k' 上移游标
    fireEvent.keyDown(window, { key: 'k' });
    await waitFor(() => {
      expect(screen.getByText(/第 1 \/ 3 条/)).toBeInTheDocument();
    });
  });

  it('should support E key to enter Assistant edit mode and render Diff', async () => {
    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText('Fix the memory leak in worker')).toBeInTheDocument();
      expect(screen.getByText(/编辑 AI 回复 \(E\)/)).toBeInTheDocument();
    });

    // 按 'e' 进入编辑模式
    fireEvent.keyDown(window, { key: 'e' });

    await waitFor(() => {
      expect(screen.getByText(/编辑 AI 回复（就地修正，生产 DPO 对齐数据）/)).toBeInTheDocument();
      expect(screen.getByPlaceholderText('在此编辑修正 AI 的回复...')).toBeInTheDocument();
    });

    // 编辑内容并显示 Diff 对比
    const textarea = screen.getByPlaceholderText('在此编辑修正 AI 的回复...');
    fireEvent.change(textarea, {
      target: { value: 'Here is the improved fix: use WeakMap instead of Map with cleanup' },
    });

    await waitFor(() => {
      expect(screen.getByText('修改前后对比 Diff (DPO 偏好对)')).toBeInTheDocument();
    });
  });
});
