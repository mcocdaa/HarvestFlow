import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SessionDrawer from '../components/sessions/SessionDrawer';

describe('SessionDrawer', () => {
  const baseSession = {
    session_id: 's1',
    status: 'approved' as const,
    quality_auto_score: 4,
    quality_manual_score: 5,
    agent_role: 'backend_dev',
    task_type: 'coding',
    tools_used: ['read', 'write'],
    tags: ['a', 'b'],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
  };

  it('should render session info and messages', () => {
    const content = {
      session_id: 's1',
      messages: [{ role: 'user', content: 'Hello' }],
      metadata: { tokens: 100 },
      tools_used: ['read', 'write'],
    };

    render(<SessionDrawer open session={baseSession} content={content} onClose={() => {}} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getAllByText('已通过').length).toBeGreaterThan(0);
    expect(screen.getAllByText('backend_dev').length).toBeGreaterThan(0);
    expect(screen.getByText('对话内容（1 条）')).toBeInTheDocument();
  });

  it('should show metadata json after expanding technical info', () => {
    const content = {
      session_id: 's1',
      messages: [{ role: 'user', content: 'Hello' }],
      metadata: { tokens: 100 },
    };

    render(<SessionDrawer open session={baseSession} content={content} onClose={() => {}} />);

    fireEvent.click(screen.getByText('技术信息'));

    expect(screen.getByText(/tokens/)).toBeInTheDocument();
  });

  it('should render empty state when no content', () => {
    render(<SessionDrawer open session={baseSession} content={null} onClose={() => {}} />);

    expect(screen.getByText('暂无对话内容')).toBeInTheDocument();
  });
});
