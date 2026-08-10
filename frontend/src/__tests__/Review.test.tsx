import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Review from '../pages/Review';

vi.mock('../services', () => ({
  reviewerApi: {
    getPending: vi.fn(),
    approveSession: vi.fn(),
    rejectSession: vi.fn(),
  },
  sessionApi: {
    getSessionContent: vi.fn(),
  },
}));

import { reviewerApi, sessionApi } from '../services';

// Simulate clipboard API
Object.defineProperty(navigator, 'clipboard', {
  writable: true,
  value: { writeText: vi.fn().mockResolvedValue(undefined) },
});

function mockSession(id: string, status = 'curated') {
  return {
    session_id: id,
    status,
    quality_auto_score: 7,
    agent_role: 'assistant',
    task_type: 'qa',
    created_at: '2026-01-01T00:00:00Z',
  };
}

const mockContent = {
  messages: [
    { role: 'user', content: 'Hello' },
    { role: 'assistant', content: 'Hi there' },
  ],
  metadata: { tokens: 100 },
};

describe('Review Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render review page with session list and approve button', async () => {
    vi.mocked(reviewerApi.getPending).mockResolvedValue({
      data: { sessions: [mockSession('s1'), mockSession('s2'), mockSession('s3')] },
    } as any);
    vi.mocked(sessionApi.getSessionContent).mockResolvedValue({
      data: { content: mockContent },
    } as any);

    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText('通过评审')).toBeInTheDocument();
    });
    expect(reviewerApi.getPending).toHaveBeenCalledTimes(1);
    expect(sessionApi.getSessionContent).toHaveBeenCalledTimes(1);
  });

  it('should call approveSession once and reload the list, loading new first session content', async () => {
    // First load: 3 sessions
    vi.mocked(reviewerApi.getPending)
      .mockResolvedValueOnce({
        data: { sessions: [mockSession('s1'), mockSession('s2'), mockSession('s3')] },
      } as any)
      // After approve: 2 sessions remain (s1 removed)
      .mockResolvedValueOnce({
        data: { sessions: [mockSession('s2'), mockSession('s3')] },
      } as any);
    vi.mocked(sessionApi.getSessionContent)
      .mockResolvedValue({ data: { content: mockContent } } as any);
    vi.mocked(reviewerApi.approveSession)
      .mockResolvedValue({ data: { success: true } } as any);

    render(<Review />);

    // Wait for initial load to complete
    await waitFor(() => {
      expect(screen.getByText('通过评审')).toBeInTheDocument();
    });
    // Initial content loaded for s1
    expect(sessionApi.getSessionContent).toHaveBeenCalledWith('s1');

    // Click approve on the first session
    fireEvent.click(screen.getByText('通过评审'));

    await waitFor(() => {
      // approveSession should be called exactly once
      expect(reviewerApi.approveSession).toHaveBeenCalledTimes(1);
      expect(reviewerApi.approveSession).toHaveBeenCalledWith('s1', '', 3);
    });

    await waitFor(() => {
      // getPending should have been called again to reload
      expect(reviewerApi.getPending).toHaveBeenCalledTimes(2);
      // Content should be loaded for the new first session (s2)
      expect(sessionApi.getSessionContent).toHaveBeenCalledWith('s2');
    });
  });

  it('should prevent double submit on rapid consecutive clicks', async () => {
    vi.mocked(reviewerApi.getPending)
      .mockResolvedValueOnce({
        data: { sessions: [mockSession('s1'), mockSession('s2'), mockSession('s3')] },
      } as any)
      .mockResolvedValueOnce({
        data: { sessions: [mockSession('s2'), mockSession('s3')] },
      } as any);
    vi.mocked(sessionApi.getSessionContent)
      .mockResolvedValue({ data: { content: mockContent } } as any);

    // Make approveSession resolve after a delay to simulate network latency
    vi.mocked(reviewerApi.approveSession)
      .mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ data: { success: true } } as any), 300))
      );

    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText('通过评审')).toBeInTheDocument();
    });

    const approveBtn = screen.getByText('通过评审');

    // Two rapid clicks in the same synchronous tick
    fireEvent.click(approveBtn);
    fireEvent.click(approveBtn);

    await waitFor(() => {
      // approveSession should be called exactly once (second click blocked by submittingRef)
      expect(reviewerApi.approveSession).toHaveBeenCalledTimes(1);
    });
  });

  it('should handle empty session list after approval (all sessions reviewed)', async () => {
    // reset once-queues left by previous tests (clearAllMocks does not clear them)
    vi.mocked(reviewerApi.getPending).mockReset();
    vi.mocked(sessionApi.getSessionContent).mockReset();
    vi.mocked(reviewerApi.approveSession).mockReset();
    // Use mockImplementation to avoid once-queue issues with clearAllMocks
    let getPendingCall = 0;
    vi.mocked(reviewerApi.getPending).mockImplementation(() => {
      getPendingCall++;
      if (getPendingCall === 1) {
        return Promise.resolve({ data: { sessions: [mockSession('s1')] } } as any);
      }
      return Promise.resolve({ data: { sessions: [] } } as any);
    });
    vi.mocked(sessionApi.getSessionContent)
      .mockResolvedValue({ data: { content: mockContent } } as any);
    vi.mocked(reviewerApi.approveSession)
      .mockResolvedValue({ data: { success: true } } as any);

    render(<Review />);

    await waitFor(() => {
      expect(screen.getByText('通过评审')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('通过评审'));

    await waitFor(() => {
      expect(reviewerApi.approveSession).toHaveBeenCalledTimes(1);
      expect(reviewerApi.getPending).toHaveBeenCalledTimes(2);
    });

    // After approval with empty list, session content should be cleared
    await waitFor(() => {
      expect(screen.getByText('暂无对话内容')).toBeInTheDocument();
    });
    const approveBtn = screen.getByRole('button', { name: /通过评审/ });
    expect(approveBtn).toBeDisabled();
  });
});
