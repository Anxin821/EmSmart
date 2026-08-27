import api from './index'

export const mesApi = {
  orders: (params) => api.get('/mes/work-orders', { params }),
  bugs: (params) => api.get('/mes/bugs', { params }),
  devreqs: (params) => api.get('/mes/dev-requests', { params }),
  create: (type, data) => api.post(`/mes/${type}`, data),
  update: (type, id, data) => api.put(`/mes/${type}/${id}`, data),
  delete: (type, id) => api.delete(`/mes/${type}/${id}`),
  flow: (type, id, status) => api.put(`/mes/${type}/${id}/status`, { status }),
  dashboard: () => api.get('/mes/dashboard')
}
