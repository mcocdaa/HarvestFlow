import React from 'react';
import { Layout, Menu } from 'antd';
import { MENU_ITEMS } from '../../../constants/menu';
import type { MenuItem } from '../../../types';
import '../../../styles/SideMenu.css';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;

const SideMenu: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;

  const getMenuItems = () => {
    return MENU_ITEMS.map((item: MenuItem) => ({
      key: item.key,
      icon: item.icon,
      label: item.label,
      onClick: () => navigate(item.path),
    }));
  };

  return (
    <Sider
      className="side-menu"
      width={240}
      theme="dark"
    >
      <div className="sidebar-content">
        <Menu
          mode="inline"
          selectedKeys={[currentPath === '/' ? 'dashboard' : currentPath.substring(1)]}
          style={{ height: '100%', borderRight: 0 }}
          items={getMenuItems()}
        />
      </div>
    </Sider>
  );
};

export default SideMenu;
