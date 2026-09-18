import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Flex,
  Input,
  List,
  Popconfirm,
  Row,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  DeleteOutlined,
  FolderOpenOutlined,
  ImportOutlined,
  PlusOutlined,
  ReloadOutlined,
  ScanOutlined,
} from '@ant-design/icons';
import { collectorApi } from '../services';
import { useAsyncData } from '../hooks';
import { CopyText, EmptyState, PageHeader } from '../components';
import { formatDateTime } from '../utils';
import type { ImportAllResult, ScanResult, WatchRunResponse, WatchState } from '../types';

const Collect: React.FC = () => {
  const { data, loading, reload } = useAsyncData<{ watch_folders?: string[] }>(
    () => collectorApi.getWatchFolders()
  );
  const folders = useMemo(() => data?.watch_folders ?? [], [data]);

  const { data: watchStateData, loading: watchLoading, reload: reloadWatch } = useAsyncData<WatchState>(
    () => collectorApi.getWatchState()
  );
  const watchState = watchStateData;
  const lastRuns = useMemo(
    () => Object.entries(watchState?.last_runs ?? {}),
    [watchState]
  );

  const [newFolder, setNewFolder] = useState('');
  const [scanFolder, setScanFolder] = useState('');
  const [scanning, setScanning] = useState(false);
  const [importingAll, setImportingAll] = useState(false);
  const [importingFile, setImportingFile] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [importResult, setImportResult] = useState<ImportAllResult | null>(null);
  const [togglingWatch, setTogglingWatch] = useState(false);
  const [runningWatch, setRunningWatch] = useState(false);

  useEffect(() => {
    if (!scanFolder && folders.length > 0) {
      setScanFolder(folders[0]);
    }
  }, [folders, scanFolder]);

  useEffect(() => {
    const timer = setInterval(() => {
      reloadWatch();
    }, 10000);
    return () => clearInterval(timer);
  }, [reloadWatch]);

  const handleToggleWatch = async (enabled: boolean) => {
    setTogglingWatch(true);
    try {
      await (enabled ? collectorApi.watchStart() : collectorApi.watchStop());
      message.success(enabled ? '自动监听已开启' : '自动监听已关闭');
      reloadWatch();
    } catch {
      // 拦截器已统一提示
    } finally {
      setTogglingWatch(false);
    }
  };

  const handleWatchRun = async () => {
    setRunningWatch(true);
    try {
      const res = await collectorApi.watchRun();
      const results = (res.data as WatchRunResponse)?.results ?? {};
      const imported = Object.values(results).reduce((sum, item) => sum + (item.imported ?? 0), 0);
      message.success(`监听扫描完成：新导入 ${imported} 条会话`);
      reloadWatch();
    } catch {
      // 拦截器已统一提示
    } finally {
      setRunningWatch(false);
    }
  };

  const handleAddFolder = async () => {
    const path = newFolder.trim();
    if (!path) return;
    try {
      await collectorApi.addWatchFolder(path);
      message.success('监听目录已添加');
      setNewFolder('');
      reload();
    } catch {
      // 拦截器已统一提示
    }
  };

  const handleRemoveFolder = async (path: string) => {
    try {
      await collectorApi.removeWatchFolder(path);
      message.success('监听目录已移除');
      if (scanFolder === path) {
        setScanFolder('');
      }
      reload();
    } catch {
      // 拦截器已统一提示
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await collectorApi.scan(scanFolder || undefined);
      const result = res.data as ScanResult;
      setScanResult(result);
      if (result.files_found === 0) {
        message.info('该目录下没有可导入的 JSON 文件');
      }
    } catch {
      // 拦截器已统一提示
    } finally {
      setScanning(false);
    }
  };

  const handleImportFile = async (filePath: string) => {
    setImportingFile(filePath);
    try {
      const res = await collectorApi.importFile(filePath);
      message.success(`导入成功，会话 ID：${res.data?.session_id ?? '-'}`);
      handleScan();
    } catch {
      // 拦截器已统一提示
    } finally {
      setImportingFile(null);
    }
  };

  const handleImportAll = async () => {
    setImportingAll(true);
    try {
      const res = await collectorApi.importAll(scanFolder || undefined);
      const result = res.data as ImportAllResult;
      setImportResult(result);
      message.success(`批量导入完成：成功 ${result.imported}，跳过 ${result.skipped}，失败 ${result.failed}`);
      handleScan();
    } catch {
      // 拦截器已统一提示
    } finally {
      setImportingAll(false);
    }
  };

  const fileColumns = [
    {
      title: '文件路径',
      dataIndex: 'file',
      key: 'file',
      ellipsis: true,
      render: (file: string) => (
        <Typography.Text className="flow-mono" style={{ fontSize: 12 }}>
          {file}
        </Typography.Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: { file: string }) => (
        <Button
          type="link"
          size="small"
          icon={<ImportOutlined />}
          loading={importingFile === record.file}
          onClick={() => handleImportFile(record.file)}
        >
          导入
        </Button>
      ),
    },
  ];

  return (
    <div>
      <PageHeader title="采集" description="从本地目录扫描并导入会话文件（JSON），支持自动监听新文件" />

      <Card
        title="自动监听"
        variant="borderless"
        style={{ marginBottom: 16 }}
        extra={
          <Button type="text" icon={<ReloadOutlined />} onClick={reloadWatch} loading={watchLoading} />
        }
      >
        <Flex justify="space-between" align="center" wrap gap={12}>
          <Space wrap>
            <Switch
              checked={watchState?.enabled}
              loading={togglingWatch}
              onChange={handleToggleWatch}
              checkedChildren="开"
              unCheckedChildren="关"
            />
            <Tag color={watchState?.running ? 'green' : 'default'} bordered={false}>
              {watchState?.running ? '运行中' : '未运行'}
            </Tag>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              每 {watchState?.interval ?? 30} 秒扫描一次监听目录，新文件自动导入
            </Typography.Text>
          </Space>
          <Button icon={<ScanOutlined />} loading={runningWatch} onClick={handleWatchRun}>
            立即运行一次
          </Button>
        </Flex>

        {lastRuns.length > 0 && (
          <List
            size="small"
            style={{ marginTop: 12 }}
            dataSource={lastRuns}
            renderItem={([folder, run]) => (
              <List.Item>
                <Typography.Text className="flow-mono" style={{ fontSize: 12 }} ellipsis>
                  {folder}
                </Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {run.at ? formatDateTime(run.at) : '—'} · 导入 {run.imported} / 跳过 {run.skipped} / 失败 {run.failed}
                </Typography.Text>
              </List.Item>
            )}
          />
        )}
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={9}>
          <Card
            title="监听目录"
            variant="borderless"
            extra={
              <Button type="text" icon={<ReloadOutlined />} onClick={reload} loading={loading} />
            }
          >
            <Flex vertical gap={12}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  value={newFolder}
                  onChange={(e) => setNewFolder(e.target.value)}
                  placeholder="如 /data/openclaw/sessions"
                  onPressEnter={handleAddFolder}
                  prefix={<FolderOpenOutlined />}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={handleAddFolder}>
                  添加
                </Button>
              </Space.Compact>

              {folders.length === 0 ? (
                <EmptyState description="暂无监听目录" />
              ) : (
                <List
                  size="small"
                  dataSource={folders}
                  renderItem={(folder) => (
                    <List.Item
                      actions={[
                        <Popconfirm
                          key="remove"
                          title="移除该监听目录？"
                          okText="移除"
                          cancelText="取消"
                          onConfirm={() => handleRemoveFolder(folder)}
                        >
                          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>,
                      ]}
                    >
                      <Typography.Text className="flow-mono" style={{ fontSize: 12 }} ellipsis>
                        {folder}
                      </Typography.Text>
                    </List.Item>
                  )}
                />
              )}
            </Flex>
          </Card>
        </Col>

        <Col xs={24} lg={15}>
          <Card title="扫描与导入" variant="borderless">
            <Flex vertical gap={16}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  value={scanFolder}
                  onChange={(e) => setScanFolder(e.target.value)}
                  placeholder="待扫描目录，留空则使用第一个监听目录"
                  prefix={<FolderOpenOutlined />}
                />
                <Button type="primary" icon={<ScanOutlined />} loading={scanning} onClick={handleScan}>
                  扫描
                </Button>
                <Button
                  icon={<ImportOutlined />}
                  loading={importingAll}
                  disabled={!scanResult || scanResult.files_found === 0}
                  onClick={handleImportAll}
                >
                  全部导入
                </Button>
              </Space.Compact>

              {importResult && (
                <Alert
                  type={importResult.failed > 0 ? 'warning' : 'success'}
                  showIcon
                  closable
                  onClose={() => setImportResult(null)}
                  message={`批量导入：共 ${importResult.total} 个文件`}
                  description={
                    <Flex vertical gap={4}>
                      <span>
                        成功 {importResult.imported}，跳过 {importResult.skipped}，失败 {importResult.failed}
                      </span>
                      {importResult.failed_files.length > 0 && (
                        <span className="flow-mono" style={{ fontSize: 12 }}>
                          失败文件：{importResult.failed_files.join('、')}
                        </span>
                      )}
                    </Flex>
                  }
                />
              )}

              {scanResult ? (
                scanResult.files_found > 0 ? (
                  <>
                    <Flex justify="space-between" align="center">
                      <Space>
                        <Tag color="blue" bordered={false}>
                          {scanResult.files_found} 个文件
                        </Tag>
                        <CopyText
                          text={scanResult.folder_path}
                          mono
                          display={<span style={{ fontSize: 12 }}>{scanResult.folder_path}</span>}
                        />
                      </Space>
                    </Flex>
                    <Table
                      rowKey="file"
                      columns={fileColumns}
                      dataSource={scanResult.files.map((file) => ({ file }))}
                      pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 个文件` }}
                      size="middle"
                    />
                  </>
                ) : (
                  <EmptyState description="该目录下没有可导入的 JSON 文件" />
                )
              ) : (
                <EmptyState description="点击扫描，查看目录中的待导入文件" />
              )}

              <Alert
                type="info"
                showIcon
                message="导入后的会话状态为「待清洗」，可在概览页运行自动清洗或在会话页逐条评分。"
              />
            </Flex>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Collect;
