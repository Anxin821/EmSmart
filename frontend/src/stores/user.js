import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 前端权限模块 key 清单 —— 与后端 PERMISSION_MODULES 一致 */
const MODULE_KEYS = [
  'devices', 'weekly', 'servers', 'agingracks', 'wifi',
  'orders', 'bugs', 'devreqs', 'antivirus', 'esopparts',
  'exception', 'warehouse', 'users',
]

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('worktask_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('worktask_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isEngineer = computed(() => user.value?.role === 'engineer')
  const canManageProjects = computed(() => ['admin', 'engineer'].includes(user.value?.role))
  const isViewer = computed(() => user.value?.role === 'viewer')
  const canEdit = computed(() => user.value?.role !== 'viewer')

  /** 当前用户权限字典 { module_key: { can_read, can_write } } */
  const permMap = ref(buildPermMap(user.value?.permissions))

  /** 是否有显式的权限数据（旧版无 permissions 字段时回退到角色判断） */
  const _hasPerms = computed(() => {
    if (!user.value) return false
    return Array.isArray(user.value.permissions) && user.value.permissions.length > 0
  })

  function buildPermMap(perms) {
    const map = {}
    if (!Array.isArray(perms)) return map
    perms.forEach(p => {
      if (p && p.module_key) {
        map[p.module_key] = { can_read: !!p.can_read, can_write: !!p.can_write }
      }
    })
    return map
  }

  /** 模块是否可见（导航栏 + 数据查看） */
  function canRead(moduleKey) {
    if (isAdmin.value) return true
    // 旧版（未重新登录）：engineer 默认全部可见，viewer 默认全部不可见
    if (!_hasPerms.value) return user.value?.role === 'engineer'
    return permMap.value[moduleKey]?.can_read === true
  }

  /** 模块是否可写（新增 / 编辑 / 删除） */
  function canWrite(moduleKey) {
    if (isAdmin.value) return true
    // 旧版（未重新登录）：engineer / viewer 沿用原有 preventEdit 逻辑
    if (!_hasPerms.value) return user.value?.role !== 'viewer'
    return permMap.value[moduleKey]?.can_write === true
  }

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('worktask_token', newToken)
  }

  function setUser(newUser) {
    user.value = newUser
    permMap.value = buildPermMap(newUser?.permissions)
    localStorage.setItem('worktask_user', JSON.stringify(newUser))
  }

  function logout() {
    token.value = ''
    user.value = null
    permMap.value = {}
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
    permMap,
    canRead,
    canWrite,
    setToken,
    setUser,
    logout,
  }
})