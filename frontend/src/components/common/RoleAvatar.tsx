import React from 'react';
import { RobotOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons';
import { getRoleLabel } from '../../constants/display';
import { useI18n } from '../../i18n';

interface RoleAvatarProps {
  role: string;
  size?: number;
  className?: string;
}

const ROLE_ICONS: Record<string, { icon: React.ReactNode; color: string; background: string }> = {
  user: { icon: <UserOutlined />, color: '#2563EB', background: 'rgba(37,99,235,0.12)' },
  assistant: { icon: <RobotOutlined />, color: '#10B981', background: 'rgba(16,185,129,0.12)' },
  system: { icon: <SettingOutlined />, color: '#8B5CF6', background: 'rgba(139,92,246,0.12)' },
};

const RoleAvatar: React.FC<RoleAvatarProps> = ({ role, size = 32, className }) => {
  const { locale } = useI18n();
  const preset = ROLE_ICONS[role] ?? {
    icon: <UserOutlined />,
    color: '#64748B',
    background: 'rgba(100,116,139,0.12)',
  };
  return (
    <span
      className={`role-avatar${className ? ` ${className}` : ''}`}
      title={getRoleLabel(role, locale)}
      style={{
        width: size,
        height: size,
        color: preset.color,
        background: preset.background,
        fontSize: Math.round(size * 0.5),
      }}
    >
      {preset.icon}
    </span>
  );
};

export default RoleAvatar;
