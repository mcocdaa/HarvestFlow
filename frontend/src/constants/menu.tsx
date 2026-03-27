import { DashboardOutlined, FolderOutlined, CheckSquareOutlined, ExportOutlined, ApiOutlined } from '@ant-design/icons';
import type { MenuItem } from '../types';

export const MENU_ITEMS: MenuItem[] = [
  { key: 'dashboard', icon: <DashboardOutlined />, label: 'Dashboard', path: '/' },
  { key: 'sessions', icon: <FolderOutlined />, label: 'Sessions', path: '/sessions' },
  { key: 'review', icon: <CheckSquareOutlined />, label: 'Review', path: '/review' },
  { key: 'export', icon: <ExportOutlined />, label: 'Export', path: '/export' },
  { key: 'plugins', icon: <ApiOutlined />, label: 'Plugins', path: '/plugins' },
];

export const APP_NAME = 'HarvestFlow';
