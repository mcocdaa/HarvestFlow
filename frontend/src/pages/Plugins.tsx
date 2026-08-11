import React, { useCallback, useState } from 'react';
import { Card, Table, message, Tabs, Switch } from 'antd';
import { pluginApi } from '../services';
import { useAsyncData } from '../hooks';
import type { Plugin } from '../types';

const Plugins: React.FC = () => {
  const [activeTab, setActiveTab] = useState('collectors');

  const { data, loading, reload } = useAsyncData<{ plugins?: Plugin[] }>(
    useCallback(() => pluginApi.getByType(activeTab), [activeTab])
  );
  const plugins = data?.plugins ?? [];

  const handleToggle = async (plugin: Plugin, enabled: boolean) => {
    try {
      if (enabled) {
        await pluginApi.enable(plugin.key);
      } else {
        await pluginApi.disable(plugin.key);
      }
      message.info(`Plugin ${plugin.name} ${enabled ? 'enabled' : 'disabled'}`);
      reload();
    } catch {
      // Interceptor handles error display
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Author',
      dataIndex: 'author',
      key: 'author',
    },
    {
      title: 'Enabled',
      key: 'enabled',
      render: (_: unknown, record: Plugin) => (
        <Switch
          checked={record.enabled}
          onChange={(checked) => handleToggle(record, checked)}
        />
      ),
    },
  ];

  const tabItems = [
    { key: 'collectors', label: 'Collectors' },
    { key: 'curators', label: 'Curators' },
  ];

  return (
    <div>
      <h1>Plugins</h1>
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
        <Table
          columns={columns}
          dataSource={plugins}
          rowKey="key"
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Plugins;
