import api from './client';

export const pluginApi = {
  getAll: () => api.get('/plugins'),
  getByType: (pluginType: string) => api.get(`/plugins/${pluginType}`),
  getDetails: (pluginType: string, pluginName: string) => api.get(`/plugins/${pluginType}/${pluginName}`),
  getFrontend: (pluginType: string, pluginName: string) => api.get(`/plugins/${pluginType}/${pluginName}/frontend`),
  enable: (pluginName: string) => api.post(`/plugins/${pluginName}/enable`),
  disable: (pluginName: string) => api.post(`/plugins/${pluginName}/disable`),
};
