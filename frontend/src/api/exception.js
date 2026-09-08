import api from './index'

export const exceptionApi = {
  list: (params) => api.get('/exception/list', { params }),
  detail: (id) => api.get(`/exception/${id}`),
  create: (data) => api.post('/exception', data),
  update: (id, data) => api.put(`/exception/${id}`, data),
  delete: (id) => api.delete(`/exception/${id}`),
  dashboard: () => api.get('/exception/dashboard/stats'),
}