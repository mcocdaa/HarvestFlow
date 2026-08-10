import { DashboardOutlined, FolderOutlined, CheckSquareOutlined, ExportOutlined, ApiOutlined } from '@ant-design/icons';
import type { MenuItem } from '../types';

export const MENU_ITEMS: MenuItem[] = [
  { icon: <DashboardOutlined />, label: 'Dashboard', path: '/' },
  { icon: <FolderOutlined />, label: 'Sessions', path: '/sessions' },
  { icon: <CheckSquareOutlined />, label: 'Review', path: '/review' },
  { icon: <ExportOutlined />, label: 'Export', path: '/export' },
  { icon: <ApiOutlined />, label: 'Plugins', path: '/plugins' },
];

export const APP_NAME = 'HarvestFlow';
