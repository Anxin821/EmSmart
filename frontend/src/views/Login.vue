<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="icon">
          <img src="/logo.png" alt="智能工厂管理平台" />
        </div>
        <h3>智能工厂管理平台</h3>
      </div>
      
      <div v-if="errorMsg" class="alert alert-danger">{{ errorMsg }}</div>
      
      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label class="form-label fw-semibold">用户名</label>
          <input 
            type="text" 
            class="form-control" 
            v-model="form.username"
            placeholder="请输入用户名" 
            required 
            autofocus
          >
        </div>
        <div class="mb-4">
          <label class="form-label fw-semibold">密码</label>
          <input 
            type="password" 
            class="form-control" 
            v-model="form.password"
            placeholder="请输入密码" 
            required
          >
        </div>
        <button type="submit" class="btn btn-primary btn-login w-100" :disabled="loading">
          <span v-if="!loading">登 录</span>
          <span v-else class="spinner-border spinner-border-sm"></span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const errorMsg = ref('')

onMounted(() => {
  // 如果已有 token 且未过期，直接跳转
  const token = localStorage.getItem('worktask_token')
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.exp * 1000 > Date.now()) {
        router.push('/dashboard/aoi')
      }
    } catch (e) {
      localStorage.removeItem('worktask_token')
    }
  }
})

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''
  
  try {
    const res = await authApi.login(form.value)
    if (res.code === 200 && res.data.access_token) {
      userStore.setToken(res.data.access_token)
      userStore.setUser({
        username: res.data.username,
        role: res.data.role,
        full_name: res.data.full_name
      })
      router.push('/dashboard/aoi')
    } else {
      errorMsg.value = res.message || '登录失败'
    }
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.message
    errorMsg.value = detail || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>