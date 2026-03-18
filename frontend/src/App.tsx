import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { DashboardOutlined, FolderOutlined, CheckSquareOutlined, ExportOutlined, ApiOutlined } from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Review from './pages/Review';
import Export from './pages/Export';
import Plugins from './pages/Plugins';

const { Header, Sider, Content } = Layout;

const App: React.FC = () => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ background: '#001529', padding: '0 24px', color: '#fff', fontSize: 20 }}>
          HarvestFlow
        </Header>
        <Layout>
          <Sider width={200} style={{ background: '#fff' }}>
            <Menu
              mode="inline"
              defaultSelectedKeys={['dashboard']}
              style={{ height: '100%', borderRight: 0 }}
              items={[
                { key: 'dashboard', icon: <DashboardOutlined />, label: <a href="/">Dashboard</a> },
                { key: 'sessions', icon: <FolderOutlined />, label: <a href="/sessions">Sessions</a> },
                { key: 'review', icon: <CheckSquareOutlined />, label: <a href="/review">Review</a> },
                { key: 'export', icon: <ExportOutlined />, label: <a href="/export">Export</a> },
                { key: 'plugins', icon: <ApiOutlined />, label: <a href="/plugins">Plugins</a> },
              ]}
            />
          </Sider>
          <Layout style={{ padding: '24px' }}>
            <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 280 }}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/sessions" element={<Sessions />} />
                <Route path="/review" element={<Review />} />
                <Route path="/export" element={<Export />} />
                <Route path="/plugins" element={<Plugins />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Layout>
    </BrowserRouter>
  );
};

export default App;
