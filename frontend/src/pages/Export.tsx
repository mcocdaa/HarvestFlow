import React, { useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Table, Tag, Typography, message } from 'antd';
import { DownloadOutlined, ExportOutlined, ReloadOutlined } from '@ant-design/icons';
import { exporterApi, sessionApi } from '../services';
import { useAsyncData } from '../hooks';
import { CopyText, EmptyState, PageHeader } from '../components';
import {
  DEFAULT_AGENT_ROLES,
  DEFAULT_TASK_TYPES,
  EXPORT_FORMAT_LABELS,
} from '../constants/display';
import { basename, filenameFromDisposition, formatDateTime, parseJsonSafe, saveBlob } from '../utils';
import type { ExportFormats, ExportHistory, ExportParams, ExportResult, Session } from '../types';

const { Option } = Select;

const parseFilterChips = (filters?: string | null): string[] => {
  const parsed = parseJsonSafe<Record<string, unknown>>(filters);
  if (!parsed) return [];
  return Object.entries(parsed)
    .filter(([, value]) => {
      if (value === null || value === undefined || value === '') return false;
      if (Array.isArray(value) && value.length === 0) return false;
      return true;
    })
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join('、') : String(value)}`);
};

const Export: React.FC = () => {
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
    return Array.from(values).map((value) => ({ value }));
  }, [sessions]);

  const taskTypeOptions = useMemo(() => {
    const values = new Set<string>(DEFAULT_TASK_TYPES);
    sessions.forEach((session) => {
      if (session.task_type) values.add(session.task_type);
    });
    return Array.from(values).map((value) => ({ value }));
  }, [sessions]);

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
      message.success(`导出成功：${result.record_count} 条会话`);
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
      message.success(`已开始下载 ${filenames.length} 个文件`);
    } catch {
      // 拦截器已统一提示
    } finally {
      setZipping(false);
    }
  };

  const columns = [
    {
      title: '导出时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (value: string) => (
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          {formatDateTime(value)}
        </Typography.Text>
      ),
    },
    {
      title: '格式',
      dataIndex: 'export_format',
      key: 'export_format',
      width: 110,
      render: (format: string) => (
        <Tag color="blue" bordered={false}>
          {EXPORT_FORMAT_LABELS[format] ?? format}
        </Tag>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
    },
    {
      title: '记录数',
      dataIndex: 'record_count',
      key: 'record_count',
      width: 90,
      render: (count: number) => <Typography.Text strong>{count}</Typography.Text>,
    },
    {
      title: '筛选条件',
      dataIndex: 'filters',
      key: 'filters',
      render: (filters?: string | null) => {
        const chips = parseFilterChips(filters);
        if (chips.length === 0) return <span className="score-empty">全部已通过会话</span>;
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
      title: '文件',
      dataIndex: 'file_path',
      key: 'file_path',
      width: 240,
      render: (filePath: string) => (
        <CopyText
          text={filePath}
          mono
          tooltip="点击复制服务器文件路径"
          display={<span style={{ fontSize: 12 }}>{filePath}</span>}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
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
            下载
          </Button>
        );
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title="导出"
        description="将已通过的会话导出为 ShareGPT / Alpaca 训练格式"
        extra={
          <Button icon={<ReloadOutlined />} onClick={reloadHistory} loading={historyLoading}>
            刷新历史
          </Button>
        }
      />

      <Card title="导出配置" variant="borderless" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleExport}
          initialValues={{ format: formats[0] ?? 'sharegpt', version: 'v1' }}
        >
          <Row gutter={16}>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="format" label="导出格式" rules={[{ required: true, message: '请选择导出格式' }]}>
                <Select placeholder="选择格式">
                  {(formats.length > 0 ? formats : ['sharegpt', 'alpaca']).map((format) => (
                    <Option key={format} value={format}>
                      {EXPORT_FORMAT_LABELS[format] ?? format}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="version" label="版本标识">
                <Input placeholder="如 v1" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="min_score" label="最低人工评分">
                <InputNumber min={1} max={5} style={{ width: '100%' }} placeholder="不限" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="agent_role" label="Agent 角色">
                <Select
                  allowClear
                  showSearch
                  placeholder="不限（可输入自定义值）"
                  options={agentRoleOptions}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="task_type" label="任务类型">
                <Select
                  allowClear
                  showSearch
                  placeholder="不限（可输入自定义值）"
                  options={taskTypeOptions}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} lg={8}>
              <Form.Item name="tags" label="标签">
                <Select
                  mode="tags"
                  allowClear
                  placeholder="输入后回车，需全部匹配"
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
              message={`导出成功：${lastResult.record_count} 条会话 → ${lastResult.filename}`}
              description={
                <CopyText
                  text={lastResult.file_path}
                  mono
                  tooltip="点击复制服务器文件路径"
                  display={<span style={{ fontSize: 12 }}>{lastResult.file_path}</span>}
                />
              }
            />
          )}

          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button type="primary" htmlType="submit" icon={<ExportOutlined />} loading={exporting}>
                导出会话
              </Button>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                仅导出状态为「已通过」的会话，文件保存在服务器导出目录。
              </Typography.Text>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card
        title="导出历史"
        variant="borderless"
        extra={
          <Space>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              已选 {selectedRowKeys.length} 项
            </Typography.Text>
            <Button
              icon={<DownloadOutlined />}
              disabled={selectedRowKeys.length === 0}
              loading={zipping}
              onClick={handleDownloadZip}
            >
              打包下载
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
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
          locale={{ emptyText: <EmptyState description="暂无导出记录" /> }}
        />
      </Card>
    </div>
  );
};

export default Export;
