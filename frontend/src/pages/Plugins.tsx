import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, message, Tabs } from 'antd';
import { pluginApi } from '../services/api';

const Plugins: React.FC = () => {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('collectors');

  useEffect(() => {
    loadPlugins();
  }, [activeTab]);

  const loadPlugins = async () => {
    setLoading(true);
    try {
      const res = await pluginApi.getAll();
      const allPlugins = res.data.plugins || [];
      const filtered = allPlugins.filter((p: any) => p.plugin_type === activeTab);
      setPlugins(filtered);
    } catch (error) {
      console.error('Failed to load plugins:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (plugin: any, enable: boolean) => {
    try {
      if (enable) {
        await pluginApi.enable(plugin.name);
      } else {
        await pluginApi.disable(plugin.name);
      }
      message.success(`Plugin ${enable ? 'enabled' : 'disabled'}`);
      loadPlugins();
    } catch (error) {
      message.error('Operation failed');
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
      title: 'Has Frontend',
      dataIndex: 'frontend_entry',
      key: 'frontend_entry',
      render: (has: string) => has ? <Tag color="green">Yes</Tag> : <Tag>No</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Button size="small" onClick={() => handleToggle(record, false)}>
          Disable
        </Button>
      ),
    },
  ];

  const tabItems = [
    { key: 'collectors', label: 'Collectors' },
    { key: 'curators', label: 'Curators' },
    { key: 'reviewers', label: 'Reviewers' },
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
          rowKey="name"
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Plugins;
