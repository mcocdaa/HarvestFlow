import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Spin } from 'antd';
import { MainLayout } from './layouts';
import { routes } from './routes';

const App: React.FC = () => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
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
  );
};

export default App;
