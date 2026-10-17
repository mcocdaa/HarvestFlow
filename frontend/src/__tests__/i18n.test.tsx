import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LanguageProvider, useI18n, STORAGE_KEY, translateDynamicText } from '../i18n';
import MainLayout from '../layouts/MainLayout';
import Review from '../pages/Review';

vi.mock('../services', () => ({
  reviewerApi: {
    getStats: vi.fn().mockResolvedValue({
      data: { curated_pending: 3, approved: 10, rejected: 2 },
    }),
    getPending: vi.fn().mockResolvedValue({
      data: {
        sessions: [
          {
            session_id: 'session_001',
            agent_role: 'coding_assistant',
            task_type: 'code_generation',
            status: 'curated',
            quality_auto_score: 4,
            created_at: '2026-01-01T00:00:00Z',
          },
        ],
      },
    }),
    getExtraFields: vi.fn().mockResolvedValue({ data: { fields: [] } }),
    getAuditLogs: vi.fn().mockResolvedValue({ data: { logs: [] } }),
  },
  sessionApi: {
    getSessionContent: vi.fn().mockResolvedValue({
      data: {
        content: {
          messages: [
            { role: 'user', content: 'Hello' },
            { role: 'assistant', content: 'Hi there!' },
          ],
          metadata: { tokens: 100 },
        },
      },
    }),
  },
}));

const ProbeComponent: React.FC = () => {
  const { locale, toggleLocale, t } = useI18n();
  return (
    <div>
      <span data-testid="probe-locale">{locale}</span>
      <span data-testid="probe-text">{t('概览', 'Dashboard')}</span>
      <button data-testid="probe-toggle" onClick={toggleLocale}>
        Toggle
      </button>
    </div>
  );
};

describe('i18n bilingual switching (zh <-> en)', () => {
  beforeEach(() => {
    window.localStorage.removeItem(STORAGE_KEY);
  });

  it('defaults to zh when localStorage is empty and toggles to en and back', () => {
    render(
      <LanguageProvider>
        <ProbeComponent />
      </LanguageProvider>
    );

    expect(screen.getByTestId('probe-locale').textContent).toBe('zh');
    expect(screen.getByTestId('probe-text').textContent).toBe('概览');

    fireEvent.click(screen.getByTestId('probe-toggle'));
    expect(screen.getByTestId('probe-locale').textContent).toBe('en');
    expect(screen.getByTestId('probe-text').textContent).toBe('Dashboard');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('en');

    fireEvent.click(screen.getByTestId('probe-toggle'));
    expect(screen.getByTestId('probe-locale').textContent).toBe('zh');
    expect(screen.getByTestId('probe-text').textContent).toBe('概览');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('zh');
  });

  it('renders MainLayout toggle button and switches menu labels between zh and en', async () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <MainLayout>
            <div>Content</div>
          </MainLayout>
        </MemoryRouter>
      </LanguageProvider>
    );

    const toggleBtn = await screen.findByTestId('lang-toggle-btn');
    expect(toggleBtn.textContent).toContain('EN');
    expect(screen.getByText('概览')).toBeInTheDocument();
    expect(screen.getByText('会话')).toBeInTheDocument();

    fireEvent.click(toggleBtn);

    await waitFor(() => {
      expect(toggleBtn.textContent).toContain('中文');
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Sessions')).toBeInTheDocument();
      expect(screen.getByText('Collector')).toBeInTheDocument();
      expect(screen.getByText('Exporter')).toBeInTheDocument();
      expect(screen.getByText('Plugins')).toBeInTheDocument();
    });
  });

  it('renders Review page in English when locale is en', async () => {
    window.localStorage.setItem(STORAGE_KEY, 'en');
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/review']}>
          <Review />
        </MemoryRouter>
      </LanguageProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Queue/)).toBeInTheDocument();
      expect(screen.getByText(/Shortcuts/)).toBeInTheDocument();
      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Reject')).toBeInTheDocument();
    });
  });

  it('translates dynamic Chinese session/plugin strings in en mode with 0 CJK leaks', () => {
    expect(
      translateDynamicText('生产集群 redis-sentinel 节点偶发 OOMKilled，排查 memory limit 并修复', 'en')
    ).toBe('Production cluster redis-sentinel nodes hit intermittent OOMKilled; inspect memory limits and fix');
    expect(translateDynamicText('数据质量', 'en')).toBe('Data Quality');
    expect(translateDynamicText('优秀', 'en')).toBe('Excellent');
    expect(translateDynamicText('数据质量标记为「较差」时不允许直接通过', 'en')).toBe(
      'Cannot approve directly when Data Quality is marked as Poor'
    );
    const fallback = translateDynamicText('这是一段未预置的动态中文内容测试', 'en');
    expect(/[\u4e00-\u9fff]/.test(fallback)).toBe(false);
  });

  it('translates dynamic English backend strings in zh mode', () => {
    expect(
      translateDynamicText('OpenClaw Agent session collector - reads from local OpenClaw session files', 'zh')
    ).toBe('OpenClaw 会话采集器 — 从本地 OpenClaw 会话目录自动读取轨迹');
    expect(translateDynamicText('k8s_deployment_fix', 'zh')).toBe('K8s 部署排障');
    expect(translateDynamicText('devops_agent', 'zh')).toBe('SRE 运维专家');
    expect(translateDynamicText('oc_e4a5edf0ba23e4f9c4c3ad40c0ab1625', 'zh')).toBe('OpenClaw 助手');
    expect(translateDynamicText('oc_e4a5edf0ba23e4f9c4c3ad40c0ab1625', 'en')).toBe('OpenClaw Agent');
    expect(translateDynamicText('score 4 >= threshold 4', 'zh')).toBe('评分 4 >= 阈值 4');
    expect(translateDynamicText('No sessions found with the given filters', 'zh')).toBe(
      '未找到符合筛选条件的会话'
    );
  });
});
