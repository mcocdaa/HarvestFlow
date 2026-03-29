import React from 'react';
import { Layout, Input, Avatar, Dropdown, Space } from 'antd';
import { SearchOutlined, UserOutlined } from '@ant-design/icons';
import { APP_NAME } from '../../../constants/menu';
import '../../../styles/AppHeader.css';

const { Header } = Layout;

const AppHeader: React.FC = () => {
  const userMenuItems = [
    { key: 'profile', label: '个人资料' },
    { key: 'settings', label: '设置' },
    { key: 'logout', label: '退出登录' },
  ];

  return (
    <Header className="app-header">
      <div className="header-left">
        <h1 className="app-logo">{APP_NAME}</h1>
      </div>
      <div className="header-center">
        <Input
          className="global-search"
          placeholder="搜索 Sessions..."
          prefix={<SearchOutlined />}
          allowClear
        />
      </div>
      <div className="header-right">
        <Dropdown menu={{ items: userMenuItems || [] }} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#2563EB' }} />
            <span className="user-name">Admin</span>
          </Space>
        </Dropdown>
      </div>
    </Header>
  );
};

export default AppHeader;
