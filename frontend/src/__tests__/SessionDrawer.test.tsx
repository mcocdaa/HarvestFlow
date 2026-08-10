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
    created_at: '2026-01-01T00:00:00Z',
  };

  it('should render session info and whitelisted metadata keys', () => {
    const content = {
      session_id: 's1',
      messages: [{ role: 'user' as const, content: 'Hello' }],
      metadata: { tokens: 100 },
      agent_role: 'backend_dev',
      task_type: 'coding',
      tools_used: ['read', 'write'],
      tags: ['a', 'b'],
    };

    render(<SessionDrawer visible session={baseSession} content={content} onClose={() => {}} />);

    // Messages rendered
    expect(screen.getByText('Hello')).toBeInTheDocument();

    // Expand metadata collapse panel
    fireEvent.click(screen.getByText('技术详情'));

    // Whitelisted metadata keys rendered
    expect(screen.getByText('agent_role:')).toBeInTheDocument();
    expect(screen.getAllByText('backend_dev').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('task_type:')).toBeInTheDocument();
    expect(screen.getByText('tools_used:')).toBeInTheDocument();
    expect(screen.getByText('tags:')).toBeInTheDocument();
    // session_id top-level key should NOT be rendered as metadata
    expect(screen.queryByText('session_id:')).not.toBeInTheDocument();
  });

  it('should render empty state when no content', () => {
    render(<SessionDrawer visible session={baseSession} content={null} onClose={() => {}} />);

    expect(screen.getByText('暂无对话内容')).toBeInTheDocument();
  });
});
