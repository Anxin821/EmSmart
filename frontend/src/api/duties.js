import api from './index'

export const dutiesApi = {
  list: () => api.get('/job-duties'),
  update: (id, data) => api.put(`/job-duties/${id}`, data),
  create: (data) => api.post('/job-duties', data),
  patch: (id, data) => api.patch(`/job-duties/${id}`, data),
  remove: (id) => api.delete(`/job-duties/${id}`),
}
