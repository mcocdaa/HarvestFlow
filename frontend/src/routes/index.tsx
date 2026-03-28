import React from 'react';
import Dashboard from '../pages/Dashboard';
import Sessions from '../pages/Sessions';
import Review from '../pages/Review';
import Export from '../pages/Export';
import Plugins from '../pages/Plugins';

export interface RouteConfig {
  path: string;
  element: React.ReactNode;
}

export const routes: RouteConfig[] = [
  { path: '/', element: <Dashboard /> },
  { path: '/sessions', element: <Sessions /> },
  { path: '/review', element: <Review /> },
  { path: '/export', element: <Export /> },
  { path: '/plugins', element: <Plugins /> },
];
