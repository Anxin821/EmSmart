import api from './index'

export const authApi = {
  login: (data) => api.post('/login', data),
  me: () => api.get('/me'),
  updateProfile: (data) => api.put('/users/me', data),
  logout: () => Promise.resolve()
}
