<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="brand">
        <img src="/logo.png" alt="产品Logo" class="brand-logo" />
        智能工厂管理平台
      </div>

      <div class="nav-title">数据看板</div>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'AoiDashboard' }" @click="go('/dashboard/aoi')">
        <span class="bi bi-bar-chart-fill" aria-hidden="true"></span>AOI&AI 看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'NetworkDashboard' }" @click="go('/dashboard/network')">
        <span class="bi bi-hdd-network-fill" aria-hidden="true"></span>车间网络看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'MesDashboard' }" @click="go('/dashboard/mes')">
        <span class="bi bi-clipboard-data-fill" aria-hidden="true"></span>MES 看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'AntivirusDashboard' }" @click="go('/dashboard/antivirus')">
        <span class="bi bi-shield-check" aria-hidden="true"></span>杀毒看板
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'DutiesDashboard' }" @click="go('/dashboard/duties')">
        <span class="bi bi-list-check" aria-hidden="true"></span>岗位职责看板
      </button>

      <div class="nav-title">业务管理</div>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Devices' }" @click="go('/devices')">
        <span class="bi bi-cpu-fill" aria-hidden="true"></span>AOI&AI 设备管理
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
        <span class="bi bi-wifi" aria-hidden="true"></span>WiFi AP 管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Orders' }" @click="go('/orders')">
        <span class="bi bi-journal-text" aria-hidden="true"></span>MES 工单管理
      </button>
      <button type="button" class="nav-link" :class="{ active: $route.name === 'Bugs' }" @click="go('/bugs')">
        <span class="bi bi-bug-fill" aria-hidden="true"></span>MES BUG 管理
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
        <!-- 面包屑：简化为只保留「首页」可点击返回 -->
        <div class="crumb">
          <router-link class="crumb-link" :to="HOME_PATH" title="返回首页">
            <span class="bi bi-house-door-fill" style="color: var(--primary);"></span>
            <span>首页</span>
          </router-link>
        </div>

        <!-- 快捷按钮 -->
        <div class="actions">
          <button class="icon-btn" title="刷新当前页" @click="reload">
            <span class="bi bi-arrow-clockwise"></span>
          </button>
          <button class="icon-btn" title="全屏切换" @click="toggleFullscreen">
            <span class="bi bi-arrows-fullscreen"></span>
          </button>
        </div>

        <!-- 用户区 -->
        <div class="user">
          <span class="avatar">{{ avatarText }}</span>
          <div class="meta">
            <span class="u-name">{{ userStore.user?.full_name || userStore.user?.username }}</span>
            <span class="u-role">
              {{ roleLabel }} · {{ userStore.user?.username }}
            </span>
          </div>
          <button class="btn btn-sm btn-outline-secondary" @click="handleLogout">
            <span class="bi bi-box-arrow-right"></span>退出
          </button>
        </div>
      </div>

      <div class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

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
  router.push('/')
}
const reload = () => router.go(0)
const toggleFullscreen = () => {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.()
  else document.exitFullscreen?.()
}
</script>

<style scoped>
/* Layout.scoped 不再重复定义 layout 骨架。
   全局骨架已在 styles.css（权威来源）。
   这里只放本组件独有的路由过渡样式与专属差异化。 */

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity .2s ease, transform .2s ease;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(6px); }
.fade-slide-leave-to   { opacity: 0; transform: translateY(-4px); }
</style>
