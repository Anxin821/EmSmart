import api from './index'

export const authApi = {
  login: (data) => api.post('/login', data),
  me: () => api.get('/me'),
  logout: () => Promise.resolve()
}
