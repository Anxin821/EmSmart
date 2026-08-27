import api from './index'

export const dashboardApi = {
  aoi: () => api.get('/dashboard/aoi'),
  network: () => api.get('/dashboard/network'),
  networkSummary: () => api.get('/dashboard/network-summary'),
  networkDevices: (params) => api.get('/dashboard/network-devices-detail', { params }),
  mes: () => api.get('/mes/dashboard'),
  // 杀毒看板路由由 antivirus_router 提供（前缀 /antivirus/*），而非 routers/dashboard
  antivirus: () => api.get('/antivirus/dashboard')
}
