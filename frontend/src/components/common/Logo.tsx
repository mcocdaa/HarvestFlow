import React from 'react';

interface LogoProps {
  size?: number;
}

const Logo: React.FC<LogoProps> = ({ size = 28 }) => {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="harvestflow-logo" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#2563EB" />
          <stop offset="1" stopColor="#F59E0B" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#harvestflow-logo)" />
      <path
        d="M8.5 22.5V9.5h3.1v4.9h8.8V9.5h3.1v13h-3.1v-5h-8.8v5H8.5Z"
        fill="#FFFFFF"
      />
    </svg>
  );
};

export default Logo;
