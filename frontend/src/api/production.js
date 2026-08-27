import api from './index'

export const productionApi = {
  weekly: (params) => api.get('/production/weekly', { params }),
  monthly: (params) => api.get('/production/monthly', { params }),
  createWeekly: (data) => api.post('/production/weekly', data),
  createMonthly: (data) => api.post('/production/monthly', data),
  updateWeekly: (id, data) => api.put(`/production/weekly/${id}`, data),
  updateMonthly: (id, data) => api.put(`/production/monthly/${id}`, data),
  deleteWeekly: (id) => api.delete(`/production/weekly/${id}`),
  deleteMonthly: (id) => api.delete(`/production/monthly/${id}`),
  generateMonthly: (year, month) => api.post('/production/monthly/generate', { year, month }),
  monthlyTrend: (params) => api.get('/production/monthly/trend', { params }),
  importWeeklyRaw: (formData) => api.post('/production/weekly/import-raw', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}
