/* eslint-disable react-refresh/only-export-components -- 路由配置模块，导出懒加载组件而非组件实现 */
import React, { lazy } from 'react';

export interface RouteConfig {
  path: string;
  element: React.ReactNode;
}

const Dashboard = lazy(() => import('../pages/Dashboard'));
const Sessions = lazy(() => import('../pages/Sessions'));
const Review = lazy(() => import('../pages/Review'));
const Collect = lazy(() => import('../pages/Collect'));
const Export = lazy(() => import('../pages/Export'));
const Plugins = lazy(() => import('../pages/Plugins'));
const NotFound = lazy(() => import('../pages/NotFound'));

export const routes: RouteConfig[] = [
  { path: '/', element: <Dashboard /> },
  { path: '/sessions', element: <Sessions /> },
  { path: '/review', element: <Review /> },
  { path: '/collect', element: <Collect /> },
  { path: '/export', element: <Export /> },
  { path: '/plugins', element: <Plugins /> },
  { path: '*', element: <NotFound /> },
];
