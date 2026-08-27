import api from './index'

export const esopApi = {
  list: (params) => api.get('/esop-parts', { params }),
  create: (data) => api.post('/esop-parts', data),
  update: (id, data) => api.put(`/esop-parts/${id}`, data),
  delete: (id) => api.delete(`/esop-parts/${id}`),
}
