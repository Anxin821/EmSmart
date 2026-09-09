import api from './index'

export const networkApi = {
  servers: (params) => api.get('/network/servers', { params }),
  agingracks: (params) => api.get('/network/aging-racks', { params }),
  wifi: (params) => api.get('/network/wifi-aps', { params }),
  create: (type, data) => api.post(`/network/${type}`, data),
  update: (type, id, data) => api.put(`/network/${type}/${id}`, data),
  delete: (type, id) => api.delete(`/network/${type}/${id}`),
  checkAll: () => api.post('/network/servers/check-all'),

  // 网络监控设置（钉钉机器人 / Ping 间隔）
  getSettings: () => api.get('/network/settings'),
  saveSettings: (data) => api.put('/network/settings', data),
  testDingtalk: () => api.post('/network/settings/test'),

  // 网络告警
  alerts: (params) => api.get('/network/alerts', { params }),
  resolveAlert: (id) => api.post(`/network/alerts/${id}/resolve`),
  resolveAllAlerts: () => api.post('/network/alerts/resolve-all')
}
