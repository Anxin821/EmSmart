import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截 - 添加 token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('worktask_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截 - 处理错误
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('worktask_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (data) => api.post('/login', data),
  me: () => api.get('/me'),
  logout: () => Promise.resolve()
}

// Options API
export const optionsApi = {
  lines: () => api.get('/options/lines'),
  projects: () => api.get('/options/projects'),
  statuses: (module) => api.get(`/options/statuses/${module}`),
  priorities: () => api.get('/options/priorities'),
  severities: () => api.get('/options/severities'),
  deviceTypes: () => api.get('/options/device-types')
}

// Devices API
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

// Production API
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

// Network API (servers, aging racks, wifi)
export const networkApi = {
  servers: (params) => api.get('/network/servers', { params }),
  agingracks: (params) => api.get('/network/aging-racks', { params }),
  wifi: (params) => api.get('/network/wifi-aps', { params }),
  create: (type, data) => api.post(`/network/${type}`, data),
  update: (type, id, data) => api.put(`/network/${type}/${id}`, data),
  delete: (type, id) => api.delete(`/network/${type}/${id}`),
  checkAll: () => api.post('/network/servers/check-all')
}

// MES API (orders, bugs, devreqs)
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

// Antivirus API
export const antivirusApi = {
  list: (params) => api.get('/antivirus/records', { params }),
  create: (data) => api.post('/antivirus/records', data),
  update: (id, data) => api.put(`/antivirus/records/${id}`, data),
  delete: (id) => api.delete(`/antivirus/records/${id}`),
  dashboard: () => api.get('/antivirus/dashboard')
}

// Dashboard API
export const dashboardApi = {
  aoi: () => api.get('/dashboard/aoi'),
  network: () => api.get('/dashboard/network'),
  networkSummary: () => api.get('/dashboard/network-summary'),
  networkDevices: (params) => api.get('/dashboard/network-devices-detail', { params }),
  mes: () => api.get('/mes/dashboard'),
  // 杀毒看板路由由 antivirus_router 提供（前缀 /antivirus/*），而非 routers/dashboard
  antivirus: () => api.get('/antivirus/dashboard')
}

// Users API
export const usersApi = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  permissions: (id, data) => api.put(`/users/${id}/permissions`, data)
}

// Projects API
export const projectsApi = {
  list: () => api.get('/projects'),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`)
}

// Responsibilities API
export const dutiesApi = {
  list: () => api.get('/job-duties'),
  update: (id, data) => api.put(`/job-duties/${id}`, data),
  create: (data) => api.post('/job-duties', data),
  patch: (id, data) => api.patch(`/job-duties/${id}`, data),
  remove: (id) => api.delete(`/job-duties/${id}`),
}

export default api