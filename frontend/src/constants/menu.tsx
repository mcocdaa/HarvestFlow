import {
  AppstoreOutlined,
  AuditOutlined,
  DashboardOutlined,
  ExportOutlined,
  FolderOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { getStoredLocale } from '../i18n';
import type { Locale } from '../i18n';
import type { MenuItem } from '../types';

export const MENU_ITEMS: MenuItem[] = [
  { icon: <DashboardOutlined />, label: '概览', path: '/' },
  { icon: <FolderOutlined />, label: '会话', path: '/sessions' },
  { icon: <AuditOutlined />, label: '审核', path: '/review' },
  { icon: <InboxOutlined />, label: '采集', path: '/collect' },
  { icon: <ExportOutlined />, label: '导出', path: '/export' },
  { icon: <AppstoreOutlined />, label: '插件', path: '/plugins' },
];

export const MENU_ITEMS_EN: MenuItem[] = [
  { icon: <DashboardOutlined />, label: 'Dashboard', path: '/' },
  { icon: <FolderOutlined />, label: 'Sessions', path: '/sessions' },
  { icon: <AuditOutlined />, label: 'Review', path: '/review' },
  { icon: <InboxOutlined />, label: 'Collector', path: '/collect' },
  { icon: <ExportOutlined />, label: 'Exporter', path: '/export' },
  { icon: <AppstoreOutlined />, label: 'Plugins', path: '/plugins' },
];

export const getMenuItems = (locale: Locale = getStoredLocale()): MenuItem[] =>
  locale === 'zh' ? MENU_ITEMS : MENU_ITEMS_EN;

export const APP_NAME = 'HarvestFlow';
export const APP_DESCRIPTION = 'AI 会话数据采集与清洗平台';
export const APP_DESCRIPTION_EN = 'AI Session Data Collection & Curation Platform';
export const getAppDescription = (locale: Locale = getStoredLocale()): string =>
  locale === 'zh' ? APP_DESCRIPTION : APP_DESCRIPTION_EN;
export const GITHUB_URL = 'https://github.com/mcocdaa/HarvestFlow';
