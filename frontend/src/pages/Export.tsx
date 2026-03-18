import React, { useEffect, useState } from 'react';
import { Card, Form, Select, InputNumber, Button, Table, message, Space } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { exporterApi } from '../services/api';

const { Option } = Select;

const Export: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [form] = Form.useForm();

  useEffect(() => {
    loadHistory();
    loadFormats();
  }, []);

  const loadHistory = async () => {
    try {
      const res = await exporterApi.getHistory();
      setHistory(res.data || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const loadFormats = async () => {
    try {
      const res = await exporterApi.getFormats();
      form.setFieldValue('format', res.data.default);
    } catch (error) {
      console.error('Failed to load formats:', error);
    }
  };

  const handleExport = async (values: any) => {
    setLoading(true);
    try {
      const res = await exporterApi.exportSessions(values);
      if (res.data.success) {
        message.success(`Exported ${res.data.record_count} sessions to ${res.data.filename}`);
        loadHistory();
      } else {
        message.error(res.data.message || 'Export failed');
      }
    } catch (error) {
      message.error('Export failed');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Format',
      dataIndex: 'export_format',
      key: 'export_format',
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: 'Records',
      dataIndex: 'record_count',
      key: 'record_count',
    },
    {
      title: 'File',
      dataIndex: 'file_path',
      key: 'file_path',
      ellipsis: true,
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
    },
  ];

  return (
    <div>
      <h1>Export</h1>
      <Card title="Export Settings" style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical" onFinish={handleExport}>
          <Form.Item name="format" label="Format" rules={[{ required: true }]}>
            <Select>
              <Option value="sharegpt">ShareGPT</Option>
              <Option value="alpaca">Alpaca</Option>
            </Select>
          </Form.Item>
          <Form.Item name="version" label="Version" initialValue="v1">
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="min_score" label="Min Score (optional)">
            <InputNumber min={1} max={5} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="agent_role" label="Agent Role (optional)">
            <Select allowClear>
              <Option value="backend_dev">Backend Developer</Option>
              <Option value="req_analyst">Requirements Analyst</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<ExportOutlined />}>
              Export Sessions
            </Button>
          </Form.Item>
        </Form>
      </Card>
      <Card title="Export History">
        <Table columns={columns} dataSource={history} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>
    </div>
  );
};

export default Export;
