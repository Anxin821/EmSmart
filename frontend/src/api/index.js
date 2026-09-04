import axios from 'axios'
import { ElMessage } from 'element-plus'

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
      localStorage.removeItem('worktask_user')
      ElMessage.warning('登录已过期，请重新登录')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 导出API工厂函数
export * from './factory'

// 按业务域导出
export { authApi } from './auth'
export { optionsApi, devicesApi } from './devices'
export { productionApi } from './production'
export { networkApi } from './network'
export { mesApi } from './mes'
export { antivirusApi } from './antivirus'
export { dashboardApi } from './dashboard'
export { usersApi } from './users'
export { projectsApi } from './projects'
export { dutiesApi } from './duties'
export { esopApi } from './esop'

export default api
