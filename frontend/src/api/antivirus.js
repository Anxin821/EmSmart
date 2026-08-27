import api from './index'

export const antivirusApi = {
  list: (params) => api.get('/antivirus/records', { params }),
  create: (data) => api.post('/antivirus/records', data),
  update: (id, data) => api.put(`/antivirus/records/${id}`, data),
  delete: (id) => api.delete(`/antivirus/records/${id}`),
  dashboard: () => api.get('/antivirus/dashboard')
}
