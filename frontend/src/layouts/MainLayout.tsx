import React from 'react';
import { Layout } from 'antd';
import { AppHeader, SideMenu } from '../components';
import '../styles/MainLayout.css';

const { Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <Layout className="main-layout">
      <AppHeader />
      <Layout className="main-body">
        <SideMenu />
        <Content className="content-area">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
