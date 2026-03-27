import React from 'react';
import { Layout, Menu } from 'antd';
import { MENU_ITEMS } from '../constants/menu';

const { Sider } = Layout;

const SideMenu: React.FC = () => {
  return (
    <Sider width={200} style={{ background: '#fff' }}>
      <Menu
        mode="inline"
        defaultSelectedKeys={['dashboard']}
        style={{ height: '100%', borderRight: 0 }}
        items={MENU_ITEMS.map((item) => ({
          key: item.key,
          icon: item.icon,
          label: <a href={item.path}>{item.label}</a>,
        }))}
      />
    </Sider>
  );
};

export default SideMenu;
