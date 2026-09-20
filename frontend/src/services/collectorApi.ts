import api from './client';

export const collectorApi = {
  scan: (folderPath?: string) =>
    api.get('/collector/scan', { params: { folder_path: folderPath } }),
  importFile: (filePath: string) =>
    api.post('/collector/import', null, { params: { file_path: filePath } }),
  importAll: (folderPath?: string) =>
    api.post('/collector/import-all', null, { params: { folder_path: folderPath } }),
  addWatchFolder: (folderPath: string) =>
    api.post('/collector/watch-folder', null, { params: { folder_path: folderPath } }),
  removeWatchFolder: (folderPath: string) =>
    api.delete('/collector/watch-folder', { params: { folder_path: folderPath } }),
  getWatchFolders: () => api.get('/collector/watch-folders'),
  getWatchState: () => api.get('/collector/watch-state'),
  watchStart: () => api.post('/collector/watch-start'),
  watchStop: () => api.post('/collector/watch-stop'),
  watchRun: () => api.post('/collector/watch-run'),
  importContent: (content: string, filename?: string) =>
    api.post('/collector/import-content', { content, filename }),
};
