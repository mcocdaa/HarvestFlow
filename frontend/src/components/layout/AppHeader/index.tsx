import React from 'react';
import { Layout } from 'antd';
import { APP_NAME } from '../../../constants/menu';
import '../../../styles/AppHeader.css';

const { Header } = Layout;

const AppHeader: React.FC = () => {
  return (
    <Header className="app-header">
      <div className="header-left">
        <h1 className="app-logo">{APP_NAME}</h1>
      </div>
    </Header>
  );
};

export default AppHeader;
