import {
  AppstoreOutlined,
  AuditOutlined,
  DashboardOutlined,
  ExportOutlined,
  FolderOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import type { MenuItem } from '../types';

export const MENU_ITEMS: MenuItem[] = [
  { icon: <DashboardOutlined />, label: '概览', path: '/' },
  { icon: <FolderOutlined />, label: '会话', path: '/sessions' },
  { icon: <AuditOutlined />, label: '审核', path: '/review' },
  { icon: <InboxOutlined />, label: '采集', path: '/collect' },
  { icon: <ExportOutlined />, label: '导出', path: '/export' },
  { icon: <AppstoreOutlined />, label: '插件', path: '/plugins' },
];

export const APP_NAME = 'HarvestFlow';
export const APP_DESCRIPTION = 'AI 会话数据采集与清洗平台';
export const GITHUB_URL = 'https://github.com/mcocdaa/HarvestFlow';
