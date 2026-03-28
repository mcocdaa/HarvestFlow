import api from './client';

export const collectorApi = {
  scanFolder: (folderPath?: string) => api.post('/collector/scan', null, { params: { folder_path: folderPath } }),
  importSession: (filePath: string) => api.post('/collector/import', null, { params: { file_path: filePath } }),
  importAll: (folderPath?: string) => api.post('/collector/import/all', null, { params: { folder_path: folderPath } }),
  getConfig: () => api.get('/collector/config'),
  addWatchFolder: (folderPath: string) => api.post('/collector/config/add-folder', null, { params: { folder_path: folderPath } }),
};
