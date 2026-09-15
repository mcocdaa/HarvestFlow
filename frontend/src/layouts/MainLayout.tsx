import React from 'react';
import { ProLayout } from '@ant-design/pro-components';
import { Badge, Tooltip } from 'antd';
import { GithubOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { APP_NAME, GITHUB_URL, MENU_ITEMS } from '../constants/menu';
import { statsApi } from '../services';
import { useAsyncData } from '../hooks';
import { Logo } from '../components';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: stats } = useAsyncData(() => statsApi.get());
  const pendingCount = stats?.curated_sessions ?? 0;

  const menuRoutes = MENU_ITEMS.map((item) => ({
    path: item.path,
    name: item.label,
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
      menu={{ loading: false, autoClose: false }}
      location={{ pathname: location.pathname }}
      route={{ path: '/', routes: menuRoutes }}
      menuItemRender={(item, dom) => (
        <div
          className="menu-item-link"
          onClick={() => item.path && navigate(item.path)}
        >
          {item.path === '/review' && pendingCount > 0 ? (
            <Badge count={pendingCount} size="small" offset={[10, -2]}>
              {dom}
            </Badge>
          ) : (
            dom
          )}
        </div>
      )}
      actionsRender={() => [
        <Tooltip key="github" title="GitHub 仓库">
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
          colorTextMenu: 'rgba(255,255,255,0.72)',
          colorTextMenuSecondary: 'rgba(255,255,255,0.45)',
          colorTextMenuItemHover: '#FFFFFF',
          colorTextMenuSelected: '#FFFFFF',
          colorBgMenuItemHover: 'rgba(255,255,255,0.08)',
          colorBgMenuItemSelected: 'rgba(37,99,235,0.85)',
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
