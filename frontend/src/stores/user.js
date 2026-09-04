import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('worktask_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('worktask_user') || 'null'))
  
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isEngineer = computed(() => user.value?.role === 'engineer')
  const canManageProjects = computed(() => ['admin', 'engineer'].includes(user.value?.role))
  const isViewer = computed(() => user.value?.role === 'viewer')
  const canEdit = computed(() => user.value?.role !== 'viewer')

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('worktask_token', newToken)
  }

  function setUser(newUser) {
    user.value = newUser
    localStorage.setItem('worktask_user', JSON.stringify(newUser))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('worktask_token')
    localStorage.removeItem('worktask_user')
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isEngineer,
    canManageProjects,
    isViewer,
    canEdit,
    setToken,
    setUser,
    logout
  }
})