<template>
  <div class="app-layout" :class="{ 'sidebar-hidden': sidebarHidden }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="brand" @click="go(HOME_PATH)" style="cursor: pointer;">
        <img src="/logo.png" alt="产品Logo" class="brand-logo" />
        智能工厂管理平台
      </div>

      <!-- 侧边栏导航：手风琴分组 -->
<div class="nav-scroll">

  <!-- ============ 数据看板 ============ -->
  <div class="nav-group" :class="{ expanded: expandedGroups.dashboard }">
    <button
      type="button"
      class="nav-group-title"
      @click="toggleGroup('dashboard')"
    >
      <span class="bi bi-grid-1x2-fill nav-group-icon" aria-hidden="true"></span>
      <span class="nav-group-text">数据看板</span>
      <span class="bi bi-chevron-right nav-group-arrow" aria-hidden="true"></span>
    </button>
    <transition name="nav-collapse">
      <div v-show="expandedGroups.dashboard" class="nav-group-body">
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
      </div>
    </transition>
  </div>

  <!-- ============ AI 设备 ============ -->
  <div class="nav-group" :class="{ expanded: expandedGroups.aiDevice }">
    <button
      type="button"
      class="nav-group-title"
      @click="toggleGroup('aiDevice')"
    >
      <span class="bi bi-cpu-fill nav-group-icon" aria-hidden="true"></span>
      <span class="nav-group-text">AI 设备</span>
      <span class="bi bi-chevron-right nav-group-arrow" aria-hidden="true"></span>
    </button>
    <transition name="nav-collapse">
      <div v-show="expandedGroups.aiDevice" class="nav-group-body">
        <button v-if="userStore.canRead('devices')" type="button" class="nav-link" :class="{ active: $route.name === 'Devices' }" @click="go('/devices')">
          <span class="bi bi-cpu-fill" aria-hidden="true"></span>AOI&AI设备管理
        </button>
        <button v-if="userStore.canRead('weekly')" type="button" class="nav-link" :class="{ active: $route.name === 'Weekly' }" @click="go('/weekly')">
          <span class="bi bi-graph-up-arrow" aria-hidden="true"></span>生产周报管理
        </button>
      </div>
    </transition>
  </div>

  <!-- ============ 网络 ============ -->
  <div class="nav-group" :class="{ expanded: expandedGroups.network }">
    <button
      type="button"
      class="nav-group-title"
      @click="toggleGroup('network')"
    >
      <span class="bi bi-hdd-network-fill nav-group-icon" aria-hidden="true"></span>
      <span class="nav-group-text">网络</span>
      <span class="bi bi-chevron-right nav-group-arrow" aria-hidden="true"></span>
    </button>
    <transition name="nav-collapse">
      <div v-show="expandedGroups.network" class="nav-group-body">
        <button v-if="userStore.canRead('servers')" type="button" class="nav-link" :class="{ active: $route.name === 'Servers' }" @click="go('/servers')">
          <span class="bi bi-server" aria-hidden="true"></span>服务器管理
        </button>
        <button v-if="userStore.canRead('agingracks')" type="button" class="nav-link" :class="{ active: $route.name === 'AgingRacks' }" @click="go('/agingracks')">
          <span class="bi bi-box-seam-fill" aria-hidden="true"></span>老化架管理
        </button>
        <button v-if="userStore.canRead('wifi')" type="button" class="nav-link" :class="{ active: $route.name === 'Wifi' }" @click="go('/wifi')">
          <span class="bi bi-wifi" aria-hidden="true"></span>WiFi AP管理
        </button>
        <button v-if="userStore.canRead('antivirus')" type="button" class="nav-link" :class="{ active: $route.name === 'Antivirus' }" @click="go('/antivirus')">
          <span class="bi bi-shield-shaded" aria-hidden="true"></span>设备杀毒记录
        </button>
      </div>
    </transition>
  </div>

  <!-- ============ MES ============ -->
  <div class="nav-group" :class="{ expanded: expandedGroups.mes }">
    <button
      type="button"
      class="nav-group-title"
      @click="toggleGroup('mes')"
    >
      <span class="bi bi-clipboard-data-fill nav-group-icon" aria-hidden="true"></span>
      <span class="nav-group-text">MES</span>
      <span class="bi bi-chevron-right nav-group-arrow" aria-hidden="true"></span>
    </button>
    <transition name="nav-collapse">
      <div v-show="expandedGroups.mes" class="nav-group-body">
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
      </div>
    </transition>
  </div>

  <!-- ============ 库房与系统 ============ -->
  <div class="nav-group" :class="{ expanded: expandedGroups.system }">
    <button
      type="button"
      class="nav-group-title"
      @click="toggleGroup('system')"
    >
      <span class="bi bi-hdd-stack-fill nav-group-icon" aria-hidden="true"></span>
      <span class="nav-group-text">库房与系统</span>
      <span class="bi bi-chevron-right nav-group-arrow" aria-hidden="true"></span>
    </button>
    <transition name="nav-collapse">
      <div v-show="expandedGroups.system" class="nav-group-body">
        <button v-if="userStore.canRead('warehouse')" type="button" class="nav-link" :class="{ active: $route.name === 'Warehouse' }" @click="go('/warehouse')">
          <span class="bi bi-box-seam-fill" aria-hidden="true"></span>库房管理
        </button>
        <button v-if="userStore.canRead('users')" type="button" class="nav-link" :class="{ active: $route.name === 'Users' }" @click="go('/users')">
          <span class="bi bi-people-fill" aria-hidden="true"></span>用户管理
        </button>
      </div>
    </transition>
  </div>

</div>
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
import { computed, ref, reactive, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// ================= 基础状态 =================
const showMenu = ref(false)
const sidebarHidden = ref(false)
const SIDEBAR_HIDDEN_KEY = 'app_sidebar_hidden'

// ================= 手风琴分组展开状态 =================
const expandedGroups = reactive({
  dashboard: true,
  aiDevice: false,
  network: false,
  mes: false,
  system: false,
})

const ROUTE_GROUP_MAP = {
  AoiDashboard: 'dashboard',
  NetworkDashboard: 'dashboard',
  MesDashboard: 'dashboard',
  AntivirusDashboard: 'dashboard',
  DutiesDashboard: 'dashboard',
  Devices: 'aiDevice',
  Weekly: 'aiDevice',
  Servers: 'network',
  AgingRacks: 'network',
  Wifi: 'network',
  Antivirus: 'network',
  Bugs: 'mes',
  DevReqs: 'mes',
  Exception: 'mes',
  EsopParts: 'mes',
  Warehouse: 'system',
  Users: 'system',
}

const toggleGroup = (key) => {
  // 直接取反：展开的可以收起，收起的可以展开，互不影响
  expandedGroups[key] = !expandedGroups[key]
}

const syncGroupFromRoute = () => {
  const groupKey = ROUTE_GROUP_MAP[route.name]
  if (!groupKey) return
  Object.keys(expandedGroups).forEach(k => { expandedGroups[k] = false })
  expandedGroups[groupKey] = true
}

// ================= 侧边栏切换 =================
const toggleSidebar = () => {
  sidebarHidden.value = !sidebarHidden.value
  try {
    localStorage.setItem(SIDEBAR_HIDDEN_KEY, sidebarHidden.value ? '1' : '0')
  } catch { /* 隐私模式忽略 */ }
}

// ================= 生命周期 =================
onMounted(() => {
  try {
    sidebarHidden.value = localStorage.getItem(SIDEBAR_HIDDEN_KEY) === '1'
  } catch { /* 忽略 */ }
  syncGroupFromRoute()
})

watch(
  () => route.name,
  () => syncGroupFromRoute()
)

// ================= 其他 state =================
const profileDialogVisible = ref(false)
const profileSaving = ref(false)
const profileForm = ref({
  full_name: userStore.user?.full_name || '',
  email: userStore.user?.email || '',
  password: '',
  confirmPassword: ''
})

// ================= 路由标题映射 =================
const NAME_MAP = {
  AoiDashboard:        ['数据看板', 'AOI&AI 看板'],
  NetworkDashboard:    ['数据看板', '车间网络看板'],
  MesDashboard:        ['数据看板', 'MES 看板'],
  AntivirusDashboard:  ['数据看板', '杀毒看板'],
  DutiesDashboard:     ['数据看板', '岗位职责看板'],
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

const currentTitle = computed(() => {
  const name = route.name
  if (!name) return ''
  const entry = NAME_MAP[name]
  return entry ? entry[1] : ''
})

const HOME_PATH = '/dashboard/aoi'

const roleMap = { admin: '管理员', engineer: '工程师', viewer: '只读用户' }
const roleLabel = computed(() => roleMap[userStore.user?.role] || userStore.user?.role || '')
const avatarText = computed(() => {
  const s = userStore.user?.full_name || userStore.user?.username || 'U'
  return s.slice(-2)
})

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
/* ================================================================
   手风琴分组
   ================================================================ */
.nav-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 4px 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-scroll::-webkit-scrollbar {
  width: 4px;
}
.nav-scroll::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 2px;
}
.nav-scroll:hover::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, .15);
}

/* ---------- 分组容器 ---------- */
.nav-group {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* ---------- 分组标题 ---------- */
.nav-group-title {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  padding: 0 10px;
  border: none;
  background: transparent;
  color: var(--c-text-2, #475569);
  font-size: 13.5px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
  white-space: nowrap;
  overflow: hidden;
  flex-shrink: 0;
  font-family: inherit;
  transition: background .15s, color .15s;
}

.nav-group-title:hover {
  background: rgba(15, 23, 42, .04);
  color: var(--c-text, #0f172a);
}

/* 分组图标（跟子项图标同样大小） */
.nav-group-icon {
  font-size: 16px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
  line-height: 1;
  color: var(--c-text-3, #94A3B8);
  transition: color .15s;
}

.nav-group-title:hover .nav-group-icon {
  color: var(--primary, #2C5CE8);
}

/* 展开时：图标高亮主色 */
.nav-group.expanded .nav-group-icon {
  color: var(--primary, #2C5CE8);
}

.nav-group-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 展开箭头：默认指向右，展开时旋转 90° */
.nav-group-arrow {
  font-size: 12px;
  color: var(--c-text-3, #94A3B8);
  flex-shrink: 0;
  transition: transform .24s cubic-bezier(.4, 0, .2, 1), color .15s;
}

.nav-group.expanded .nav-group-arrow {
  transform: rotate(90deg);
  color: var(--primary, #2C5CE8);
}

/* ---------- 分组内的子项列表 ---------- */
.nav-group-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0 4px 0;
  overflow: hidden;
}

/* 子项缩进：跟分组标题的图标对齐 */
.nav-group-body .nav-link {
  padding-left: 34px;   /* 10px 分组 padding + 20px 图标宽 + 4px gap */
}

/* ---------- 展开/收起动画 ---------- */
.nav-collapse-enter-active,
.nav-collapse-leave-active {
  transition: max-height .24s cubic-bezier(.4, 0, .2, 1), opacity .18s;
  overflow: hidden;
}

.nav-collapse-enter-from,
.nav-collapse-leave-to {
  max-height: 0;
  opacity: 0;
}

.nav-collapse-enter-to,
.nav-collapse-leave-from {
  max-height: 400px;   /* 足够大，能容纳最长组的项 */
  opacity: 1;
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