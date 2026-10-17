import React from 'react';
import { ProLayout } from '@ant-design/pro-components';
import { Badge, Tooltip } from 'antd';
import { GithubOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { APP_NAME, GITHUB_URL, MENU_ITEMS } from '../constants/menu';
import { statsApi } from '../services';
import { useAsyncData } from '../hooks';
import { Logo } from '../components';
import { useI18n } from '../i18n';

const MENU_EN_LABELS: Record<string, string> = {
  '/': 'Dashboard',
  '/sessions': 'Sessions',
  '/review': 'Review',
  '/collect': 'Collector',
  '/export': 'Exporter',
  '/plugins': 'Plugins',
};

const SidebarHeader: React.FC = () => {
  const { locale, toggleLocale } = useI18n();
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        gap: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <Logo size={24} />
        <span
          style={{
            color: '#FFFFFF',
            fontSize: 16,
            fontWeight: 700,
            letterSpacing: '-0.3px',
            lineHeight: 1.2,
            whiteSpace: 'nowrap',
          }}
        >
          {APP_NAME}
        </span>
      </div>
      <button
        type="button"
        data-testid="lang-toggle-btn"
        className="lang-toggle-btn"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          toggleLocale();
        }}
      >
        {locale === 'zh' ? '🌐 EN' : '🌐 中文'}
      </button>
    </div>
  );
};

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { locale, t } = useI18n();
  const { data: stats } = useAsyncData(() => statsApi.get());
  const pendingCount = stats?.curated_sessions ?? 0;

  const menuRoutes = MENU_ITEMS.map((item) => ({
    path: item.path,
    name: locale === 'zh' ? item.label : (MENU_EN_LABELS[item.path] ?? item.label),
    icon: item.icon,
  }));

  return (
    <ProLayout
      className="main-layout"
      title={APP_NAME}
      logo={<Logo />}
      layout="side"
      fixSiderbar
      fixedHeader
      siderWidth={232}
      collapsedButtonRender={false}
      menu={{ loading: false, autoClose: false }}
      location={{ pathname: location.pathname }}
      route={{ path: '/', routes: menuRoutes }}
      menuHeaderRender={() => <SidebarHeader />}
      menuItemRender={(item, dom) => (
        <div
          className="menu-item-link"
          onClick={() => item.path && navigate(item.path)}
        >
          <span className="menu-item-dom">{dom}</span>
          {item.path === '/review' && pendingCount > 0 && (
            <Badge
              count={pendingCount}
              size="small"
              style={{ boxShadow: 'none', marginLeft: 8 }}
            />
          )}
        </div>
      )}
      actionsRender={() => [
        <Tooltip key="github" title={t('GitHub 仓库', 'GitHub Repository')}>
          <a
            className="header-action"
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
          >
            <GithubOutlined />
          </a>
        </Tooltip>,
      ]}
      token={{
        sider: {
          colorMenuBackground: '#0F172A',
          colorTextMenu: 'rgba(255,255,255,0.86)',
          colorTextMenuSecondary: 'rgba(255,255,255,0.65)',
          colorTextMenuItemHover: '#FFFFFF',
          colorTextMenuSelected: '#FFFFFF',
          colorBgMenuItemHover: 'rgba(255,255,255,0.1)',
          colorBgMenuItemSelected: 'rgba(37,99,235,0.9)',
          colorTextMenuTitle: '#FFFFFF',
        },
        header: {
          colorBgHeader: '#FFFFFF',
        },
      }}
      contentStyle={{ padding: 24, minHeight: 'calc(100vh - 56px)' }}
    >
      <div className="content-area">{children}</div>
    </ProLayout>
  );
};

export default MainLayout;
