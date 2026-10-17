import React, { useMemo, useState } from 'react';
import { Button, Card, Col, Modal, Row, Tabs, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { pluginApi } from '../services';
import { useAsyncData } from '../hooks';
import { EmptyState, PageHeader } from '../components';
import { PluginCard, getPluginDisplayName } from '../components/plugins/PluginCard';
import { getPluginTypeLabel, PLUGIN_TYPE_ORDER } from '../constants/display';
import { useI18n } from '../i18n';
import type { Plugin } from '../types';

const Plugins: React.FC = () => {
  const { t, td } = useI18n();
  const { data, loading, reload } = useAsyncData<{ plugins?: Plugin[] }>(() => pluginApi.getAll());
  const [activeTab, setActiveTab] = useState('all');
  const [togglingKey, setTogglingKey] = useState<string | null>(null);
  const [confirmingPlugin, setConfirmingPlugin] = useState<Plugin | null>(null);

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
    const displayName = getPluginDisplayName(plugin, td);
    setTogglingKey(plugin.key);
    try {
      if (enabled) {
        await pluginApi.enable(plugin.key);
      } else {
        await pluginApi.disable(plugin.key);
      }
      message.success(
        t(
          `插件 ${displayName} 已${enabled ? '启用' : '停用'}`,
          `Plugin ${displayName} ${enabled ? 'enabled' : 'disabled'}`
        )
      );
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
    setConfirmingPlugin(plugin);
  };

  const renderGrid = (list: Plugin[]) => {
    if (list.length === 0) {
      return <EmptyState description={t('该分类下暂无插件', 'No plugins in this category')} />;
    }
    return (
      <Row gutter={[16, 16]}>
        {list.map((plugin) => (
          <Col key={plugin.key} xs={24} md={12} xl={8}>
            <PluginCard
              plugin={plugin}
              toggling={togglingKey === plugin.key}
              onToggle={handleToggle}
            />
          </Col>
        ))}
      </Row>
    );
  };

  const confirmingDisplayName = confirmingPlugin ? getPluginDisplayName(confirmingPlugin, td) : '';

  return (
    <div>
      <Modal
        open={Boolean(confirmingPlugin)}
        title={t(`停用插件 ${confirmingDisplayName}？`, `Disable plugin ${confirmingDisplayName}?`)}
        onOk={async () => {
          if (!confirmingPlugin) return;
          const target = confirmingPlugin;
          setConfirmingPlugin(null);
          await doToggle(target, false);
        }}
        onCancel={() => setConfirmingPlugin(null)}
        okText={t('停用', 'Disable')}
        cancelText={t('取消', 'Cancel')}
        okButtonProps={{ danger: true }}
        destroyOnHidden
      >
        {t(
          '停用后将卸载插件模块及其钩子，相关采集/清洗能力会立即失效。',
          'Disabling unloads the plugin module and its hooks; related collection/curation features will stop immediately.'
        )}
      </Modal>
      <PageHeader
        title={t('插件', 'Plugins')}
        description={t(
          '采集器、清洗器、审核器与服务插件的运行状态管理',
          'Manage runtime status of collector, curator, reviewer, and service plugins'
        )}
        extra={
          <Button icon={<ReloadOutlined />} onClick={reload} loading={loading}>
            {t('刷新', 'Refresh')}
          </Button>
        }
      />
      <Card variant="borderless">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'all',
              label: t(`全部（${plugins.length}）`, `All (${plugins.length})`),
            },
            ...PLUGIN_TYPE_ORDER.map((type) => ({
              key: type,
              label: t(
                `${getPluginTypeLabel(type, 'zh')}（${counts[type] ?? 0}）`,
                `${getPluginTypeLabel(type, 'en')} (${counts[type] ?? 0})`
              ),
            })),
          ]}
        />
        {renderGrid(filtered)}
      </Card>
    </div>
  );
};

export default Plugins;
