import React from 'react';
import { Layout } from 'antd';
import { APP_NAME } from '../constants/menu';

const { Header } = Layout;

const AppHeader: React.FC = () => {
  return (
    <Header style={{ background: '#001529', padding: '0 24px', color: '#fff', fontSize: 20 }}>
      {APP_NAME}
    </Header>
  );
};

export default AppHeader;
