import api from './index'

export const optionsApi = {
  lines: () => api.get('/options/lines'),
  projects: () => api.get('/options/projects'),
  statuses: (module) => api.get(`/options/statuses/${module}`),
  priorities: () => api.get('/options/priorities'),
  severities: () => api.get('/options/severities'),
  deviceTypes: () => api.get('/options/device-types')
}

export const devicesApi = {
  list: (params) => api.get('/devices', { params }),
  detail: (id) => api.get(`/devices/detail/${id}`),
  create: (data) => api.post('/devices', data),
  update: (id, data) => api.put(`/devices/${id}`, data),
  delete: (id) => api.delete(`/devices/${id}`),
  import: (formData) => api.post('/devices/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  export: (params) => window.open(`/api/v1/devices/export/excel?${new URLSearchParams(params)}`, '_blank')
}
