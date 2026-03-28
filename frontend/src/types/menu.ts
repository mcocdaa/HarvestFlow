import React from 'react';

export interface MenuItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
}
