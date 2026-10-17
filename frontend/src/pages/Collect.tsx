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
import { useI18n } from '../i18n';
import type { ImportAllResult, ScanResult, WatchRunResponse, WatchState } from '../types';

const Collect: React.FC = () => {
  const { t } = useI18n();
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
      message.success(
        enabled
          ? t('自动监听已开启', 'Auto-watch enabled')
          : t('自动监听已关闭', 'Auto-watch disabled')
      );
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
      message.success(t(`监听扫描完成：新导入 ${imported} 条会话`, `Watch scan done: ${imported} sessions imported`));
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
      message.success(t('监听目录已添加', 'Watch folder added'));
      setNewFolder('');
      reload();
    } catch {
      // 拦截器已统一提示
    }
  };

  const handleRemoveFolder = async (path: string) => {
    try {
      await collectorApi.removeWatchFolder(path);
      message.success(t('监听目录已移除', 'Watch folder removed'));
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
        message.info(t('该目录下没有可导入的 JSON 文件', 'No importable JSON files found in this folder'));
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
      message.success(
        t(
          `导入成功，会话 ID：${res.data?.session_id ?? '-'}`,
          `Imported session ID: ${res.data?.session_id ?? '-'}`
        )
      );
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
      message.success(
        t(
          `批量导入完成：成功 ${result.imported}，跳过 ${result.skipped}，失败 ${result.failed}`,
          `Batch import complete: ${result.imported} imported, ${result.skipped} skipped, ${result.failed} failed`
        )
      );
      handleScan();
    } catch {
      // 拦截器已统一提示
    } finally {
      setImportingAll(false);
    }
  };

  const fileColumns = [
    {
      title: t('文件路径', 'File Path'),
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
      title: t('操作', 'Actions'),
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
          {t('导入', 'Import')}
        </Button>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('采集', 'Collector')}
        description={t(
          '从本地目录扫描并导入会话文件（JSON），支持自动监听新文件',
          'Scan and import session JSON files from local directories with auto-watch support'
        )}
      />

      <Card
        title={t('自动监听', 'Auto-Watch')}
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
              checkedChildren={t('开', 'On')}
              unCheckedChildren={t('关', 'Off')}
            />
            <Tag color={watchState?.running ? 'green' : 'default'} bordered={false}>
              {watchState?.running ? t('运行中', 'Running') : t('未运行', 'Stopped')}
            </Tag>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {t(
                `每 ${watchState?.interval ?? 30} 秒扫描一次监听目录，新文件自动导入`,
                `Scans watched folders every ${watchState?.interval ?? 30}s and auto-imports new files`
              )}
            </Typography.Text>
          </Space>
          <Button icon={<ScanOutlined />} loading={runningWatch} onClick={handleWatchRun}>
            {t('立即运行一次', 'Run Now')}
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
                  {run.at ? formatDateTime(run.at) : '—'} ·{' '}
                  {t(
                    `导入 ${run.imported} / 跳过 ${run.skipped} / 失败 ${run.failed}`,
                    `Imported ${run.imported} / Skipped ${run.skipped} / Failed ${run.failed}`
                  )}
                </Typography.Text>
              </List.Item>
            )}
          />
        )}
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={9}>
          <Card
            title={t('监听目录', 'Watch Folders')}
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
                  placeholder={t('如 /data/openclaw/sessions', 'e.g. /data/openclaw/sessions')}
                  onPressEnter={handleAddFolder}
                  prefix={<FolderOpenOutlined />}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={handleAddFolder}>
                  {t('添加', 'Add')}
                </Button>
              </Space.Compact>

              {folders.length === 0 ? (
                <EmptyState description={t('暂无监听目录', 'No watch folders configured')} />
              ) : (
                <List
                  size="small"
                  dataSource={folders}
                  renderItem={(folder) => (
                    <List.Item
                      actions={[
                        <Popconfirm
                          key="remove"
                          title={t('移除该监听目录？', 'Remove this watch folder?')}
                          okText={t('移除', 'Remove')}
                          cancelText={t('取消', 'Cancel')}
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
          <Card title={t('扫描与导入', 'Scan & Import')} variant="borderless">
            <Flex vertical gap={16}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  value={scanFolder}
                  onChange={(e) => setScanFolder(e.target.value)}
                  placeholder={t('待扫描目录，留空则使用第一个监听目录', 'Folder to scan (leave blank for first watched folder)')}
                  prefix={<FolderOpenOutlined />}
                />
                <Button type="primary" icon={<ScanOutlined />} loading={scanning} onClick={handleScan}>
                  {t('扫描', 'Scan')}
                </Button>
                <Button
                  icon={<ImportOutlined />}
                  loading={importingAll}
                  disabled={!scanResult || scanResult.files_found === 0}
                  onClick={handleImportAll}
                >
                  {t('全部导入', 'Import All')}
                </Button>
              </Space.Compact>

              {importResult && (
                <Alert
                  type={importResult.failed > 0 ? 'warning' : 'success'}
                  showIcon
                  closable
                  onClose={() => setImportResult(null)}
                  message={t(`批量导入：共 ${importResult.total} 个文件`, `Batch Import: ${importResult.total} files`)}
                  description={
                    <Flex vertical gap={4}>
                      <span>
                        {t(
                          `成功 ${importResult.imported}，跳过 ${importResult.skipped}，失败 ${importResult.failed}`,
                          `Imported ${importResult.imported}, Skipped ${importResult.skipped}, Failed ${importResult.failed}`
                        )}
                      </span>
                      {importResult.failed_files.length > 0 && (
                        <span className="flow-mono" style={{ fontSize: 12 }}>
                          {t('失败文件：', 'Failed files: ')}
                          {importResult.failed_files.join(t('、', ', '))}
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
                          {t(`${scanResult.files_found} 个文件`, `${scanResult.files_found} files`)}
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
                      pagination={{ pageSize: 10, showTotal: (total) => t(`共 ${total} 个文件`, `${total} files`) }}
                      size="middle"
                    />
                  </>
                ) : (
                  <EmptyState description={t('该目录下没有可导入的 JSON 文件', 'No importable JSON files found in this folder')} />
                )
              ) : (
                <EmptyState description={t('点击扫描，查看目录中的待导入文件', 'Click Scan to view importable files in folder')} />
              )}

              <Alert
                type="info"
                showIcon
                message={t(
                  '导入后的会话状态为「待清洗」，可在概览页运行自动清洗或在会话页逐条评分。',
                  'Imported sessions start as "Raw". Run Auto-Curate on Dashboard or score them individually on Sessions.'
                )}
              />
            </Flex>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Collect;
