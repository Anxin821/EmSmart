import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Layout from '../components/Layout.vue'
import { authApi } from '../api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    // 父路由仅作为 Layout 包裹层；子路由均使用绝对路径，
    // 使浏览器地址与悬停提示不再出现无意义的 /index 前缀。
    path: '/',
    component: Layout,
    redirect: '/dashboard/aoi',
    children: [
      {
        path: '/dashboard/aoi',
        name: 'AoiDashboard',
        component: () => import('../views/dashboard/AoiDashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/dashboard/network',
        name: 'NetworkDashboard',
        component: () => import('../views/dashboard/NetworkDashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/dashboard/mes',
        name: 'MesDashboard',
        component: () => import('../views/dashboard/MesDashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/dashboard/antivirus',
        name: 'AntivirusDashboard',
        component: () => import('../views/dashboard/AntivirusDashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/dashboard/duties',
        name: 'DutiesDashboard',
        component: () => import('../views/dashboard/DutiesDashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/devices',
        name: 'Devices',
        component: () => import('../views/business/Devices.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/weekly',
        name: 'Weekly',
        component: () => import('../views/business/Weekly.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/monthly',
        name: 'Monthly',
        component: () => import('../views/business/Monthly.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/servers',
        name: 'Servers',
        component: () => import('../views/business/Servers.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/agingracks',
        name: 'AgingRacks',
        component: () => import('../views/business/AgingRacks.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/wifi',
        name: 'Wifi',
        component: () => import('../views/business/Wifi.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/bugs',
        name: 'Bugs',
        component: () => import('../views/business/Bugs.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/devreqs',
        name: 'DevReqs',
        component: () => import('../views/business/DevReqs.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/antivirus',
        name: 'Antivirus',
        component: () => import('../views/business/Antivirus.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('../views/business/Users.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/esop-parts',
        name: 'EsopParts',
        component: () => import('../views/business/EsopParts.vue'),
        meta: { requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // 禁用路由滚动行为，避免某些浏览器兼容性问题
  scrollBehavior: () => ({ left: 0, top: 0 })
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('worktask_token')
  
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/login')
      return
    }
    next()
  } else {
    if (to.path === '/login' && token) {
      next('/dashboard/aoi')
      return
    }
    next()
  }
})

// 添加路由变化后的日志，便于调试
router.afterEach((to, from) => {
  console.log(`路由切换: ${from.path} -> ${to.path}`)
})

// 添加全局错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  // 可以在这里添加错误恢复逻辑
})

// 捕获导航错误
const originalPush = router.push
router.push = function(location) {
  return originalPush.call(this, location).catch(err => {
    if (err.name !== 'NavigationDuplicated') {
      console.error('路由导航错误:', err)
    }
  })
}

export default router
