import React, { useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Table, Tag, Typography, message } from 'antd';
import { DownloadOutlined, ExportOutlined, ReloadOutlined } from '@ant-design/icons';
import { exporterApi, sessionApi } from '../services';
import { useAsyncData } from '../hooks';
import { CopyText, EmptyState, PageHeader } from '../components';
import {
  DEFAULT_AGENT_ROLES,
  DEFAULT_TASK_TYPES,
  getExportFormatLabel,
} from '../constants/display';
import { basename, filenameFromDisposition, formatDateTime, parseJsonSafe, saveBlob } from '../utils';
import { useI18n } from '../i18n';
import type { ExportFormats, ExportHistory, ExportParams, ExportResult, Session } from '../types';

const { Option } = Select;

const FILTER_KEY_ZH: Record<string, string> = {
  min_score: '最低评分',
  agent_role: '角色',
  task_type: '任务类型',
  tags: '标签',
};

const FILTER_KEY_EN: Record<string, string> = {
  min_score: 'Min Score',
  agent_role: 'Role',
  task_type: 'Task',
  tags: 'Tags',
};

const parseFilterChips = (
  filters?: string | null,
  locale: 'zh' | 'en' = 'zh',
  td?: (val: string) => string
): string[] => {
  const parsed = parseJsonSafe<Record<string, unknown>>(filters);
  if (!parsed) return [];
  const sep = locale === 'zh' ? '、' : ', ';
  const keyMap = locale === 'zh' ? FILTER_KEY_ZH : FILTER_KEY_EN;
  return Object.entries(parsed)
    .filter(([, value]) => {
      if (value === null || value === undefined || value === '') return false;
      if (Array.isArray(value) && value.length === 0) return false;
      return true;
    })
    .map(([key, value]) => {
      const label = keyMap[key] ?? key;
      const rawVal = Array.isArray(value)
        ? value.map((v) => (td ? td(String(v)) : String(v))).join(sep)
        : td
          ? td(String(value))
          : String(value);
      return `${label}: ${rawVal}`;
    });
};

const Export: React.FC = () => {
  const { locale, t, td } = useI18n();
  const [form] = Form.useForm();
  const [exporting, setExporting] = useState(false);
  const [lastResult, setLastResult] = useState<ExportResult | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [zipping, setZipping] = useState(false);

  const { data: formatsData } = useAsyncData<ExportFormats>(() => exporterApi.getFormats(true));
  const { data: historyData, loading: historyLoading, reload: reloadHistory } = useAsyncData<{
    exports?: ExportHistory[];
  }>(() => exporterApi.getHistory(50));
  const { data: sessionsData } = useAsyncData<{ sessions?: Session[] }>(() =>
    sessionApi.getSessions({ page: 1, page_size: 100, sort: 'recent' })
  );

  const formats = formatsData?.formats ?? [];
  const history = historyData?.exports ?? [];
  const sessions = useMemo(() => sessionsData?.sessions ?? [], [sessionsData]);

  const agentRoleOptions = useMemo(() => {
    const values = new Set<string>(DEFAULT_AGENT_ROLES);
    sessions.forEach((session) => {
      if (session.agent_role) values.add(session.agent_role);
    });
    return Array.from(values).map((value) => ({ value, label: td(value) || value }));
  }, [sessions, td]);

  const taskTypeOptions = useMemo(() => {
    const values = new Set<string>(DEFAULT_TASK_TYPES);
    sessions.forEach((session) => {
      if (session.task_type) values.add(session.task_type);
    });
    return Array.from(values).map((value) => ({ value, label: td(value) || value }));
  }, [sessions, td]);

  const tagOptions = useMemo(() => {
    const values = new Set<string>();
    sessions.forEach((session) => {
      (session.tags ?? []).forEach((tag) => values.add(tag));
    });
    return Array.from(values).map((value) => ({ value }));
  }, [sessions]);

  const handleExport = async (values: ExportParams) => {
    setExporting(true);
    try {
      const res = await exporterApi.exportSessions(values);
      const result = res.data as ExportResult;
      setLastResult(result);
      message.success(t(`导出成功：${result.record_count} 条会话`, `Exported ${result.record_count} sessions`));
      reloadHistory();
    } catch {
      // 拦截器已统一提示
    } finally {
      setExporting(false);
    }
  };

  const handleDownload = async (filename: string) => {
    setDownloading(filename);
    try {
      const res = await exporterApi.downloadExport(filename);
      saveBlob(res.data as Blob, filenameFromDisposition(res.headers?.['content-disposition'] as string, filename));
    } catch {
      // 拦截器已统一提示
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadZip = async () => {
    const filenames = history
      .filter((item) => selectedRowKeys.includes(item.id))
      .map((item) => basename(item.file_path))
      .filter(Boolean);
    if (filenames.length === 0) return;

    setZipping(true);
    try {
      const res = await exporterApi.downloadZip(filenames);
      saveBlob(
        res.data as Blob,
        filenameFromDisposition(res.headers?.['content-disposition'] as string, 'harvestflow-exports.zip')
      );
      message.success(t(`已开始下载 ${filenames.length} 个文件`, `Downloading ${filenames.length} files`));
    } catch {
      // 拦截器已统一提示
    } finally {
      setZipping(false);
    }
  };

  const columns = [
    {
      title: t('导出时间', 'Exported At'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 155,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 13, whiteSpace: 'nowrap' }}>
          {formatDateTime(value)}
        </Typography.Text>
      ),
    },
    {
      title: t('格式', 'Format'),
      dataIndex: 'export_format',
      key: 'export_format',
      width: 135,
      render: (format: string) => (
        <Tag color="blue" bordered={false}>
          {getExportFormatLabel(format, locale)}
        </Tag>
      ),
    },
    {
      title: t('版本', 'Version'),
      dataIndex: 'version',
      key: 'version',
      width: 82,
    },
    {
      title: t('记录数', 'Records'),
      dataIndex: 'record_count',
      key: 'record_count',
      width: 86,
      render: (count: number) => <Typography.Text strong>{count}</Typography.Text>,
    },
    {
      title: t('筛选条件', 'Filters'),
      dataIndex: 'filters',
      key: 'filters',
      width: 140,
      render: (filters?: string | null) => {
        const chips = parseFilterChips(filters, locale, td);
        if (chips.length === 0) {
          return (
            <span className="score-empty" style={{ whiteSpace: 'nowrap' }}>
              {t('全部已通过会话', 'All approved')}
            </span>
          );
        }
        return (
          <Space size={4} wrap>
            {chips.map((chip) => (
              <Tag key={chip} bordered={false}>
                {chip}
              </Tag>
            ))}
          </Space>
        );
      },
    },
    {
      title: t('文件', 'File'),
      dataIndex: 'file_path',
      key: 'file_path',
      ellipsis: true,
      render: (filePath: string) => (
        <CopyText
          text={filePath}
          mono
          tooltip={t('点击复制服务器文件路径', 'Copy server file path')}
          display={
            <span
              style={{
                fontSize: 12,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: 260,
                display: 'inline-block',
                verticalAlign: 'bottom',
              }}
            >
              {basename(filePath) || filePath}
            </span>
          }
        />
      ),
    },
    {
      title: t('操作', 'Actions'),
      key: 'action',
      width: 110,
      render: (_: unknown, record: ExportHistory) => {
        const filename = basename(record.file_path);
        return (
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            loading={downloading === filename}
            onClick={() => handleDownload(filename)}
          >
            {t('下载', 'Download')}
          </Button>
        );
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('导出', 'Exporter')}
        description={t(
          '将已通过的会话导出为 ShareGPT / Alpaca 训练格式',
          'Export approved sessions into ShareGPT or Alpaca training datasets'
        )}
        extra={
          <Button icon={<ReloadOutlined />} onClick={reloadHistory} loading={historyLoading}>
            {t('刷新历史', 'Refresh History')}
          </Button>
        }
      />

      <Card title={t('导出配置', 'Export Settings')} variant="borderless" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleExport}
          initialValues={{ format: formats[0] ?? 'sharegpt', version: 'v1' }}
        >
          <Row gutter={16}>
            <Col xs={24} md={12} lg={8}>
              <Form.Item
                name="format"
                label={t('导出格式', 'Export Format')}
                rules={[{ required: true, message: t('请选择导出格式', 'Please select export format') }]}
              >
                <Select placeholder={t('选择格式', 'Select format')}>
                  {(formats.length > 0 ? formats : ['sharegpt', 'alpaca']).map((format) => (
                    <Option key={format} value={format}>
                      {getExportFormatLabel(format, locale)}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="version" label={t('版本标识', 'Version Tag')}>
                <Input placeholder={t('如 v1', 'e.g. v1')} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="min_score" label={t('最低人工评分', 'Min Human Score')}>
                <InputNumber min={1} max={5} style={{ width: '100%' }} placeholder={t('不限', 'Any')} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="agent_role" label={t('Agent 角色', 'Agent Role')}>
                <Select
                  allowClear
                  showSearch
                  placeholder={t('不限（可输入自定义值）', 'Any (or type custom role)')}
                  options={agentRoleOptions}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="task_type" label={t('任务类型', 'Task Type')}>
                <Select
                  allowClear
                  showSearch
                  placeholder={t('不限（可输入自定义值）', 'Any (or type custom task)')}
                  options={taskTypeOptions}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="tags" label={t('标签', 'Tags')}>
                <Select
                  mode="tags"
                  allowClear
                  placeholder={t('输入后回车，需全部匹配', 'Press Enter to add (all must match)')}
                  options={tagOptions}
                />
              </Form.Item>
            </Col>
          </Row>

          {lastResult && (
            <Alert
              type="success"
              showIcon
              closable
              onClose={() => setLastResult(null)}
              style={{ marginBottom: 16 }}
              message={t(
                `导出成功：${lastResult.record_count} 条会话 → ${lastResult.filename}`,
                `Exported ${lastResult.record_count} sessions → ${lastResult.filename}`
              )}
              description={
                <CopyText
                  text={lastResult.file_path}
                  mono
                  tooltip={t('点击复制服务器文件路径', 'Copy server file path')}
                  display={<span style={{ fontSize: 12 }}>{lastResult.file_path}</span>}
                />
              }
            />
          )}

          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button type="primary" htmlType="submit" icon={<ExportOutlined />} loading={exporting}>
                {t('导出会话', 'Export Sessions')}
              </Button>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {t(
                  '仅导出状态为「已通过」的会话，文件保存在服务器导出目录。',
                  'Only "Approved" sessions are exported and saved to the server export directory.'
                )}
              </Typography.Text>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card
        title={t('导出历史', 'Export History')}
        variant="borderless"
        extra={
          <Space>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {t(`已选 ${selectedRowKeys.length} 项`, `${selectedRowKeys.length} selected`)}
            </Typography.Text>
            <Button
              icon={<DownloadOutlined />}
              disabled={selectedRowKeys.length === 0}
              loading={zipping}
              onClick={handleDownloadZip}
            >
              {t('打包下载', 'Download ZIP')}
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={history}
          rowKey="id"
          loading={historyLoading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            preserveSelectedRowKeys: true,
          }}
          pagination={{ pageSize: 10, showTotal: (total) => t(`共 ${total} 条`, `${total} total`) }}
          locale={{ emptyText: <EmptyState description={t('暂无导出记录', 'No export records')} /> }}
        />
      </Card>
    </div>
  );
};

export default Export;
