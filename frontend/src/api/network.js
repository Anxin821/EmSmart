import api from './index'

export const networkApi = {
  servers: (params) => api.get('/network/servers', { params }),
  agingracks: (params) => api.get('/network/aging-racks', { params }),
  wifi: (params) => api.get('/network/wifi-aps', { params }),
  create: (type, data) => api.post(`/network/${type}`, data),
  update: (type, id, data) => api.put(`/network/${type}/${id}`, data),
  delete: (type, id) => api.delete(`/network/${type}/${id}`),
  checkAll: () => api.post('/network/servers/check-all')
}
