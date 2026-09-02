<template>
  <div class="app-layout">
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
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Devices' }" @click="go('/devices')">
        <span class="bi bi-cpu-fill" aria-hidden="true"></span>AOI&AI设备管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Weekly' }" @click="go('/weekly')">
        <span class="bi bi-graph-up-arrow" aria-hidden="true"></span>生产周报管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Monthly' }" @click="go('/monthly')">
        <span class="bi bi-bar-chart-line-fill" aria-hidden="true"></span>生产月报管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Servers' }" @click="go('/servers')">
        <span class="bi bi-server" aria-hidden="true"></span>服务器管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'AgingRacks' }" @click="go('/agingracks')">
        <span class="bi bi-box-seam-fill" aria-hidden="true"></span>老化架管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Wifi' }" @click="go('/wifi')">
        <span class="bi bi-wifi" aria-hidden="true"></span>WiFi AP管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Orders' }" @click="go('/orders')">
        <span class="bi bi-journal-text" aria-hidden="true"></span>MES工单管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Bugs' }" @click="go('/bugs')">
        <span class="bi bi-bug-fill" aria-hidden="true"></span>MES BUG管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'DevReqs' }" @click="go('/devreqs')">
        <span class="bi bi-lightbulb-fill" aria-hidden="true"></span>MES 需求管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Antivirus' }" @click="go('/antivirus')">
        <span class="bi bi-shield-shaded" aria-hidden="true"></span>设备杀毒记录
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'EsopParts' }" @click="go('/esop-parts')">
        <span class="bi bi-file-earmark-text-fill" aria-hidden="true"></span>ESOP料号管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Users' }" @click="go('/users')">
        <span class="bi bi-people-fill" aria-hidden="true"></span>用户管理
      </button>
    </aside>

    <!-- 主内容区 -->
    <main class="main">
      <div class="topbar">
        <!-- 用户区 -->
        <div class="user-right">
          <div class="user" @mouseenter="showMenu = true" @mouseleave="showMenu = false">
            <span class="avatar">{{ avatarText }}</span>
            <span class="username">{{ userStore.user?.full_name || userStore.user?.username }}</span>
            <!-- 下拉菜单 -->
            <div class="user-menu" :class="{ show: showMenu }">
              <button class="menu-item" @click="handleProfile">
                <span class="bi bi-person-circle"></span>个人中心
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
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 下拉菜单显示状态
const showMenu = ref(false)

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
  Monthly:      ['业务管理', '生产月报管理'],
  Servers:      ['业务管理', '服务器管理'],
  AgingRacks:   ['业务管理', '老化架管理'],
  Wifi:         ['业务管理', 'WiFi AP 管理'],
  Orders:       ['业务管理', 'MES 工单管理'],
  Bugs:         ['业务管理', 'MES BUG 管理'],
  DevReqs:      ['业务管理', 'MES 需求管理'],
  Antivirus:    ['业务管理', '设备杀毒记录'],
  EsopParts:    ['业务管理', 'ESOP料号管理'],
  Users:        ['业务管理', '用户管理']
}

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

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

</script>

<style scoped>
/* Layout 样式由全局 styles.css 定义 */
</style>
