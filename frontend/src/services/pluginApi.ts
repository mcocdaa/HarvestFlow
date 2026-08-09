import api from './client';

export const pluginApi = {
  getAll: () => api.get('/plugins'),
  getByType: (pluginType: string) => api.get(`/plugins/${pluginType}`),
  enable: (pluginKey: string) => api.post('/plugins/enable', null, { params: { key: pluginKey } }),
  disable: (pluginKey: string) => api.post('/plugins/disable', null, { params: { key: pluginKey } }),
};
