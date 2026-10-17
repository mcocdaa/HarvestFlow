import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import { MainLayout } from './layouts';
import { routes } from './routes';
import { LanguageProvider, useI18n } from './i18n';
import { harvestFlowTheme } from './theme/flow-design-theme';

const AppInner: React.FC = () => {
  const { locale } = useI18n();
  return (
    <ConfigProvider theme={harvestFlowTheme} locale={locale === 'zh' ? zhCN : enUS}>
      <BrowserRouter>
        <MainLayout>
          <Suspense
            fallback={
              <div className="page-loading">
                <Spin size="large" />
              </div>
            }
          >
            <Routes>
              {routes.map((route) => (
                <Route key={route.path} path={route.path} element={route.element} />
              ))}
            </Routes>
          </Suspense>
        </MainLayout>
      </BrowserRouter>
    </ConfigProvider>
  );
};

const App: React.FC = () => {
  return (
    <LanguageProvider>
      <AppInner />
    </LanguageProvider>
  );
};

export default App;
