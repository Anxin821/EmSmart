<template>
  <div class="app-layout" :class="{ 'sidebar-hidden': sidebarHidden }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="brand" @click="go(HOME_PATH)" style="cursor: pointer;">
        <img src="/logo.png" alt="产品Logo" class="brand-logo" />
        智能工厂管理平台
      </div>

      <div class="nav-title">数据看板</div>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'AoiDashboard' }" @click="go('/dashboard/aoi')">
        <span class="bi bi-bar-chart-fill" aria-hidden="true"></span>AOI&AI看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'NetworkDashboard' }" @click="go('/dashboard/network')">
        <span class="bi bi-hdd-network-fill" aria-hidden="true"></span>网络看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'MesDashboard' }" @click="go('/dashboard/mes')">
        <span class="bi bi-clipboard-data-fill" aria-hidden="true"></span>MES看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'AntivirusDashboard' }" @click="go('/dashboard/antivirus')">
        <span class="bi bi-shield-check" aria-hidden="true"></span>杀毒看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'DutiesDashboard' }" @click="go('/dashboard/duties')">
        <span class="bi bi-list-check" aria-hidden="true"></span>职责看板
      </button>

      <div class="nav-title">业务管理</div>
      <button v-if="userStore.canRead('devices')" type="button" class="nav-link" :class="{ active: $route.name === 'Devices' }" @click="go('/devices')">
        <span class="bi bi-cpu-fill" aria-hidden="true"></span>AOI&AI设备管理
      </button>
      <button v-if="userStore.canRead('weekly')" type="button" class="nav-link" :class="{ active: $route.name === 'Weekly' }" @click="go('/weekly')">
        <span class="bi bi-graph-up-arrow" aria-hidden="true"></span>生产周报管理
      </button>
      <button v-if="userStore.canRead('servers')" type="button" class="nav-link" :class="{ active: $route.name === 'Servers' }" @click="go('/servers')">
        <span class="bi bi-server" aria-hidden="true"></span>服务器管理
      </button>
      <button v-if="userStore.canRead('agingracks')" type="button" class="nav-link" :class="{ active: $route.name === 'AgingRacks' }" @click="go('/agingracks')">
        <span class="bi bi-box-seam-fill" aria-hidden="true"></span>老化架管理
      </button>
      <button v-if="userStore.canRead('wifi')" type="button" class="nav-link" :class="{ active: $route.name === 'Wifi' }" @click="go('/wifi')">
        <span class="bi bi-wifi" aria-hidden="true"></span>WiFi AP管理
      </button>
      <button v-if="userStore.canRead('bugs')" type="button" class="nav-link" :class="{ active: $route.name === 'Bugs' }" @click="go('/bugs')">
        <span class="bi bi-bug-fill" aria-hidden="true"></span>MES BUG管理
      </button>
      <button v-if="userStore.canRead('devreqs')" type="button" class="nav-link" :class="{ active: $route.name === 'DevReqs' }" @click="go('/devreqs')">
        <span class="bi bi-lightbulb-fill" aria-hidden="true"></span>MES 需求管理
      </button>
      <button v-if="userStore.canRead('exception')" type="button" class="nav-link" :class="{ active: $route.name === 'Exception' }" @click="go('/exception')">
        <span class="bi bi-exclamation-triangle-fill" aria-hidden="true"></span>异常履历管理
      </button>
      <button v-if="userStore.canRead('esopparts')" type="button" class="nav-link" :class="{ active: $route.name === 'EsopParts' }" @click="go('/esop-parts')">
        <span class="bi bi-file-earmark-text-fill" aria-hidden="true"></span>ESOP料号管理
      </button>
      <button v-if="userStore.canRead('antivirus')" type="button" class="nav-link" :class="{ active: $route.name === 'Antivirus' }" @click="go('/antivirus')">
        <span class="bi bi-shield-shaded" aria-hidden="true"></span>设备杀毒记录
      </button>
      <button v-if="userStore.canRead('warehouse')" type="button" class="nav-link" :class="{ active: $route.name === 'Warehouse' }" @click="go('/warehouse')">
        <span class="bi bi-box-seam-fill" aria-hidden="true"></span>库房管理
      </button>
      <button v-if="userStore.canRead('users')" type="button" class="nav-link" :class="{ active: $route.name === 'Users' }" @click="go('/users')">
        <span class="bi bi-people-fill" aria-hidden="true"></span>用户管理
      </button>
    </aside>

    <!-- 主内容区 -->
    <main class="main">
      <div class="topbar">
  <button
  type="button"
  class="sidebar-toggle"
  @click="toggleSidebar"
  :title="sidebarHidden ? '显示侧边栏' : '隐藏侧边栏'"
>
  <svg
  viewBox="0 0 24 24"
  width="22"
  height="22"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  <rect x="3" y="4" width="18" height="16" rx="6" ry="6" />
  <line x1="9" y1="4" x2="9" y2="20" />
</svg>
</button>
<!-- ✅ 新增：当前模块标题 -->
  <h1 v-if="currentTitle" class="topbar-title">{{ currentTitle }}</h1>
  <div class="topbar-actions"></div>

  <div class="user-right">
          <div class="user" @mouseenter="showMenu = true" @mouseleave="showMenu = false">
            <span class="avatar">{{ avatarText }}</span>
            <span class="username">{{ userStore.user?.full_name || userStore.user?.username }}</span>
            <!-- 下拉菜单 -->
            <div class="user-menu" :class="{ show: showMenu }">
              <button class="menu-item" @click="openProfileDialog">
                <span class="bi bi-person-circle"></span>个人信息
              </button>
              <button class="menu-item" @click="handleLogout">
                <span class="bi bi-box-arrow-right"></span>安全退出
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="content">
        <router-view />
      </div>
    </main>
  </div>

  <el-dialog
    v-model="profileDialogVisible"
    title="个人信息"
    width="500px"
    destroy-on-close
    :close-on-click-modal="false"
    class="profile-dialog"
    center
  >
    <div class="profile-dialog-shell">
      <div class="profile-header-card">
        <div class="profile-avatar">{{ avatarText }}</div>
        <div class="profile-header-text">
          <div class="profile-name">{{ userStore.user?.full_name || userStore.user?.username || '用户' }}</div>
          <div class="profile-role">{{ userStore.user?.username ? `用户名：${userStore.user.username}` : (roleLabel || '普通用户') }}</div>
        </div>
      </div>

      <el-form :model="profileForm" label-width="90px" label-position="left" class="profile-form">
        <el-form-item label="姓名">
          <el-input v-model="profileForm.full_name" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" clearable />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="profileForm.password" type="password" show-password placeholder="不修改请留空" clearable />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="profileForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" clearable />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <div class="cm-footer profile-footer">
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="profileSaving" @click="handleProfileSave">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
onMounted(() => {
  // 恢复上次的隐藏状态
  try {
    sidebarHidden.value = localStorage.getItem(SIDEBAR_HIDDEN_KEY) === '1'
  } catch { /* 忽略 */ }
})
// 下拉菜单显示状态
const showMenu = ref(false)
// 侧边栏是否隐藏（false = 显示，true = 隐藏）
const sidebarHidden = ref(false)
const SIDEBAR_HIDDEN_KEY = 'app_sidebar_hidden'

// 切换显示/隐藏
const toggleSidebar = () => {
  sidebarHidden.value = !sidebarHidden.value
  try {
    localStorage.setItem(SIDEBAR_HIDDEN_KEY, sidebarHidden.value ? '1' : '0')
  } catch { /* 隐私模式忽略 */ }
}
const profileDialogVisible = ref(false)
const profileSaving = ref(false)
const profileForm = ref({
  full_name: userStore.user?.full_name || '',
  email: userStore.user?.email || '',
  password: '',
  confirmPassword: ''
})

// 路由 → 分组+标题 映射（保持 NAME_MAP 常量便于后续扩展）
const NAME_MAP = {
  // 数据看板
  AoiDashboard:        ['数据看板', 'AOI&AI 看板'],
  NetworkDashboard:    ['数据看板', '车间网络看板'],
  MesDashboard:        ['数据看板', 'MES 看板'],
  AntivirusDashboard:  ['数据看板', '杀毒看板'],
  DutiesDashboard:     ['数据看板', '岗位职责看板'],
  // 业务管理
  Devices:      ['业务管理', 'AOI&AI 设备管理'],
  Weekly:       ['业务管理', '生产周报管理'],
  Servers:      ['业务管理', '服务器管理'],
  AgingRacks:   ['业务管理', '老化架管理'],
  Wifi:         ['业务管理', 'WiFi AP 管理'],
  Bugs:         ['业务管理', 'MES BUG 管理'],
  DevReqs:      ['业务管理', 'MES 需求管理'],
  Antivirus:    ['业务管理', '设备杀毒记录'],
  EsopParts:   ['业务管理', 'ESOP料号管理'],
  Warehouse:   ['业务管理', '库房管理'],
  Exception:   ['业务管理', '异常履历管理'],
  Users:       ['业务管理', '用户管理']
}
// 当前模块标题（用于顶栏显示）
const currentTitle = computed(() => {
  const name = route.name
  if (!name) return ''
  const entry = NAME_MAP[name]
  return entry ? entry[1] : ''
})

// 面包屑可点击路径：首页 = 数据看板默认页
const HOME_PATH = '/dashboard/aoi'

const roleMap = { admin: '管理员', engineer: '工程师', viewer: '只读用户' }
const roleLabel = computed(() => roleMap[userStore.user?.role] || userStore.user?.role || '')
const avatarText = computed(() => {
  const s = userStore.user?.full_name || userStore.user?.username || 'U'
  return s.slice(-2)  // 中文名取末 2 字，英文首字母习惯可自行改
})

// 侧边栏点击导航：用 button 而非 <a href>，避免浏览器左下角弹出 URL 预览
const go = (path) => router.push(path)

const openProfileDialog = () => {
  showMenu.value = false
  profileForm.value = {
    full_name: userStore.user?.full_name || '',
    email: userStore.user?.email || '',
    password: '',
    confirmPassword: ''
  }
  profileDialogVisible.value = true
}

const handleProfileSave = async () => {
  const payload = {}
  if (profileForm.value.full_name !== (userStore.user?.full_name || '')) payload.full_name = profileForm.value.full_name
  if (profileForm.value.email !== (userStore.user?.email || '')) payload.email = profileForm.value.email

  if (profileForm.value.password || profileForm.value.confirmPassword) {
    if (profileForm.value.password !== profileForm.value.confirmPassword) {
      ElMessage.error('两次输入的密码不一致')
      return
    }
    if (profileForm.value.password.length < 6) {
      ElMessage.error('新密码长度不能少于 6 位')
      return
    }
    payload.password = profileForm.value.password
  }

  if (!Object.keys(payload).length) {
    ElMessage.info('没有需要更新的信息')
    return
  }

  profileSaving.value = true
  try {
    const res = await authApi.updateProfile(payload)
    const nextUser = {
      ...userStore.user,
      ...(res.data || {}),
      full_name: profileForm.value.full_name || userStore.user?.full_name || '',
      email: profileForm.value.email || userStore.user?.email || ''
    }
    userStore.setUser(nextUser)
    ElMessage.success(res.message || '个人信息已更新')
    profileDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || err.response?.data?.message || '更新失败')
  } finally {
    profileSaving.value = false
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

</script>

<style scoped>
/* ================================================================
   侧边栏隐藏：宽度过渡到 0
   ================================================================ */
.sidebar {
  transition:
    width .28s cubic-bezier(.4, 0, .2, 1),
    flex-basis .28s cubic-bezier(.4, 0, .2, 1),
    padding .28s cubic-bezier(.4, 0, .2, 1),
    opacity .18s cubic-bezier(.4, 0, .2, 1);
  overflow: hidden;
  will-change: width;
  flex-shrink: 0;
}

.app-layout.sidebar-hidden .sidebar {
  width: 0 !important;
  min-width: 0 !important;
  max-width: 0 !important;
  flex-basis: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  opacity: 0;
  pointer-events: none;
}

/* 主内容区自动撑满 */
.main {
  transition: all .28s cubic-bezier(.4, 0, .2, 1);
  min-width: 0;
}

/* ================================================================
   顶栏的侧边栏开关按钮
   ================================================================ */
.sidebar-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  color: #0f172a;
  border-radius: 8px;
  cursor: pointer;
  padding: 0;
  margin-right: 8px;
  flex-shrink: 0;
  transition: background .15s, color .15s;
}
/* ================================================================
   顶栏当前模块标题
   ================================================================ */
.topbar-title {
  /* 复位 h1 默认样式 */
  margin: 0;
  padding: 0;

  font-size: 15px;
  font-weight: 600;
  color: var(--c-text, #0f172a);
  letter-spacing: -0.01em;
  line-height: 1.3;

  /* 不要被压缩 */
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;           /* 标题很长时截断，不挤压右侧 */
}

/* 可选：在标题左边加一条淡竖线，跟折叠按钮做视觉分隔 */
.topbar-title::before {
  content: '';
  display: inline-block;
  width: 1px;
  height: 14px;
  background: var(--c-divider, #E2E8F0);
  vertical-align: middle;
  margin-right: 12px;
  position: relative;
  top: -1px;
}
.sidebar-toggle:hover {
  background: rgba(15, 23, 42, .06);
  color: var(--primary, #2C5CE8);
}
.sidebar-toggle:active {
  transform: scale(.96);
}
.sidebar-toggle svg {
  display: block;        /* 去掉 inline-svg 的基线空隙 */
}
.sidebar-toggle .bi {
  font-size: 22px;                    /* ✅ 从 18 → 22，跟参考图尺寸感接近 */
  line-height: 1;
  font-weight: 700;                   /* ✅ Bootstrap Icons 支持，笔画更粗 */
}
.profile-dialog :deep(.el-dialog) {
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.16);
}

.profile-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f7faff 0%, #eef4ff 100%);
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--c-divider);
  text-align: center;
}

.profile-dialog :deep(.el-dialog__title) {
  display: block;
  width: 100%;
  text-align: center;
}

.profile-dialog :deep(.el-dialog__headerbtn) {
  top: 16px;
  right: 16px;
}

.profile-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #fff;
}

.profile-dialog :deep(.el-dialog__footer) {
  padding: 12px 20px 16px;
  background: #fff;
  border-top: 1px solid var(--c-divider);
}

.profile-dialog-shell {
  padding: 18px 20px 8px;
}

.profile-header-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 14px 16px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(44,92,232,0.06), rgba(59,130,246,0.02));
  border: 1px solid rgba(44,92,232,0.08);
  border-radius: 14px;
}

.profile-header-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.profile-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.profile-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text);
}

.profile-role {
  font-size: 12px;
  color: var(--c-text-3);
  margin-top: 2px;
  letter-spacing: 0.1px;
}

.profile-form {
  margin-top: 2px;
}

.profile-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.profile-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.22) inset;
}

.profile-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(44, 92, 232, 0.5) inset;
}

.profile-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}
</style>