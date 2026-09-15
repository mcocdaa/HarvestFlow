import React, { useMemo, useState } from 'react';
import { Button, Card, Col, Flex, Modal, Row, Space, Switch, Tabs, Tag, Typography, message } from 'antd';
import {
  ApiOutlined,
  AuditOutlined,
  ExperimentOutlined,
  InboxOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { pluginApi } from '../services';
import { useAsyncData } from '../hooks';
import { CopyText, EmptyState, PageHeader } from '../components';
import { PLUGIN_TYPE_COLORS, PLUGIN_TYPE_LABELS, PLUGIN_TYPE_ORDER } from '../constants/display';
import type { Plugin } from '../types';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  collectors: <InboxOutlined />,
  curators: <ExperimentOutlined />,
  reviewers: <AuditOutlined />,
  services: <ApiOutlined />,
};

const Plugins: React.FC = () => {
  const [modal, modalContextHolder] = Modal.useModal();
  const { data, loading, reload } = useAsyncData<{ plugins?: Plugin[] }>(() => pluginApi.getAll());
  const [activeTab, setActiveTab] = useState('all');
  const [togglingKey, setTogglingKey] = useState<string | null>(null);

  const plugins = useMemo(() => data?.plugins ?? [], [data]);

  const counts = useMemo(() => {
    return PLUGIN_TYPE_ORDER.reduce<Record<string, number>>((acc, type) => {
      acc[type] = plugins.filter((plugin) => plugin.plugin_type === type).length;
      return acc;
    }, {});
  }, [plugins]);

  const filtered = useMemo(() => {
    if (activeTab === 'all') return plugins;
    return plugins.filter((plugin) => plugin.plugin_type === activeTab);
  }, [plugins, activeTab]);

  const doToggle = async (plugin: Plugin, enabled: boolean) => {
    setTogglingKey(plugin.key);
    try {
      if (enabled) {
        await pluginApi.enable(plugin.key);
      } else {
        await pluginApi.disable(plugin.key);
      }
      message.success(`插件 ${plugin.name} 已${enabled ? '启用' : '停用'}`);
      reload();
    } catch {
      // 拦截器已统一提示
    } finally {
      setTogglingKey(null);
    }
  };

  const handleToggle = (plugin: Plugin, checked: boolean) => {
    if (checked) {
      doToggle(plugin, true);
      return;
    }
    modal.confirm({
      title: `停用插件 ${plugin.name}？`,
      content: '停用后将卸载插件模块及其钩子，相关采集/清洗能力会立即失效。',
      okText: '停用',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: () => doToggle(plugin, false),
    });
  };

  const renderGrid = (list: Plugin[]) => {
    if (list.length === 0) {
      return <EmptyState description="该分类下暂无插件" />;
    }
    return (
      <Row gutter={[16, 16]}>
        {list.map((plugin) => {
          const color = PLUGIN_TYPE_COLORS[plugin.plugin_type] ?? '#2563EB';
          return (
            <Col key={plugin.key} xs={24} md={12} xl={8}>
              <Card
                variant="borderless"
                style={{ height: '100%' }}
                title={
                  <Space>
                    <span className="stat-card-icon" style={{ width: 32, height: 32, fontSize: 16, color, backgroundColor: `${color}1A` }}>
                      {TYPE_ICONS[plugin.plugin_type] ?? <ApiOutlined />}
                    </span>
                    <Typography.Text strong>{plugin.name}</Typography.Text>
                  </Space>
                }
                extra={
                  <Switch
                    checked={plugin.enabled}
                    loading={togglingKey === plugin.key}
                    onChange={(checked) => handleToggle(plugin, checked)}
                  />
                }
              >
                <Flex vertical gap={8}>
                  <Space size={4} wrap>
                    <Tag color={color} bordered={false}>
                      {PLUGIN_TYPE_LABELS[plugin.plugin_type] ?? plugin.plugin_type}
                    </Tag>
                    <Tag bordered={false}>v{plugin.version}</Tag>
                    {plugin.author && <Tag bordered={false}>{plugin.author}</Tag>}
                  </Space>
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 0, minHeight: 44 }}>
                    {plugin.description || '暂无描述'}
                  </Typography.Paragraph>
                  <CopyText text={plugin.key} mono display={<span style={{ fontSize: 12 }}>{plugin.key}</span>} />
                </Flex>
              </Card>
            </Col>
          );
        })}
      </Row>
    );
  };

  return (
    <div>
      {modalContextHolder}
      <PageHeader
        title="插件"
        description="采集器、清洗器、审核器与服务插件的运行状态管理"
        extra={
          <Button icon={<ReloadOutlined />} onClick={reload} loading={loading}>
            刷新
          </Button>
        }
      />
      <Card variant="borderless">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: 'all', label: `全部（${plugins.length}）` },
            ...PLUGIN_TYPE_ORDER.map((type) => ({
              key: type,
              label: `${PLUGIN_TYPE_LABELS[type]}（${counts[type] ?? 0}）`,
            })),
          ]}
        />
        {renderGrid(filtered)}
      </Card>
    </div>
  );
};

export default Plugins;
