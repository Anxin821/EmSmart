<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">👥</span>用户管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.isAdmin">
            <el-button type="success" @click="showModal()">
              <el-icon><Plus /></el-icon>新增用户
            </el-button>
          </template>
          <el-button @click="loadData">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </template>
      </CommonFilterBar>
    </div>

    <div class="page-content">
    <el-table :data="listFiltered" stripe border :height="'calc(100vh - 210px)'" style="width: 100%;" empty-text="暂无数据">

        <el-table-column prop="username" label="用户名" width="150" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <b>{{ row.username }}</b>
            <div v-if="row.full_name && row.full_name !== row.username" style="font-size:12px;color:var(--c-text-mute,#94a3b8);font-weight:normal;">{{ row.full_name }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="role" label="角色" width="110" align="center">
          <template #default="{ row }">
            <span :class="'status-badge ' + getRoleClass(row.role)">{{ row.role }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="email" label="邮箱" min-width="160" align="center" show-overflow-tooltip>
          <template #default="{ row }">{{ row.email || '-' }}</template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.is_active" class="status-badge normal">正常</span>
            <span v-else class="status-badge muted">禁用</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="120" align="center">
          <template #default="{ row }">{{ (row.created_at || '').slice(0, 10) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="210" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="userStore.isAdmin">
              <el-button type="primary" link size="small" @click="showModal(row)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button type="warning" link size="small" @click="showPermModal(row)">
                <el-icon><Key /></el-icon>权限
              </el-button>
              <el-button type="danger" link size="small" @click="handleDelete(row.id)">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <CommonPagination
        v-model:page="page"
        v-model:page-size="pageSize"
        :total="filteredCount"
        compact
      />
    </div>

    <!-- 用户新增/编辑弹框 -->
    <CommonModal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑用户' : '新增用户'"
      width="560px"
      :ok-loading="saving"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-6">
          <label class="small form-label">用户名 <span style="color: var(--err);">*</span></label>
          <el-input v-model="form.username" clearable placeholder="登录账号" />
        </div>
        <div class="col-6">
          <label class="small form-label">姓名</label>
          <el-input v-model="form.full_name" clearable placeholder="真实姓名" />
        </div>
        <div class="col-6">
          <label class="small form-label">密码 <span style="color: var(--err);" v-if="!editingId">*</span></label>
          <el-input v-model="form.password" type="password" show-password clearable
                    :placeholder="editingId ? '留空则不修改' : '请输入密码'" />
        </div>
        <div class="col-6">
          <label class="small form-label">角色</label>
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%;">
            <el-option label="admin" value="admin" />
            <el-option label="engineer" value="engineer" />
            <el-option label="viewer" value="viewer" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small form-label">邮箱</label>
          <el-input v-model="form.email" clearable placeholder="email@example.com" />
        </div>
        <div class="col-6">
          <label class="small form-label">状态</label>
          <el-select v-model="form.is_active" placeholder="请选择状态" style="width: 100%;">
            <el-option label="正常" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </div>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存</el-button>
        </div>
      </template>
    </CommonModal>
    <!-- 权限设置弹框 -->
    <CommonModal
      v-model:visible="permModalVisible"
      :title="'权限设置 - ' + (currentUser?.username || '')"
      width="820px"
      :ok-loading="permSaving"
      @ok="handlePermSave"
    >
      <!-- admin 提示：admin 角色默认拥有全部权限，细项授权不生效 -->
      <el-alert
        v-if="currentUser?.role === 'admin'"
        type="info" :closable="false" show-icon
        title="该用户为 admin 角色，默认拥有全部模块的读写权限，此处授权仅对 engineer / viewer 角色生效。"
        style="margin-bottom: 12px;"
      />
      <!-- 快捷操作 + 授权统计 -->
      <div class="perm-toolbar">
        <div class="perm-quick">
          <el-button size="small" type="primary" plain @click="setAllPerms('write')">全部读写</el-button>
          <el-button size="small" plain @click="setAllPerms('read')">全部只读</el-button>
          <el-button size="small" plain @click="setAllPerms('none')">全部清空</el-button>
        </div>
        <div class="perm-summary">
          可访问 <b>{{ permStats.readable }}</b> / {{ permModules.length }} 个模块，
          可写入 <b>{{ permStats.writable }}</b> 个
        </div>
      </div>

      <el-row :gutter="12">
        <el-col v-for="m in permModules" :key="m.key" :span="8" style="margin-bottom: 12px;">
          <div class="mod-perm-card" :class="{ 'perm-on': perms[m.key]?.can_read }">
            <div class="mod-title">
              <span :class="['bi', m.icon]" style="color: var(--primary); margin-right: 6px;"></span>
              {{ m.label }}
            </div>
            <div class="perm-checks">
              <el-checkbox v-model="perms[m.key].can_read" @change="onReadChange(m.key)">
                <span style="font-size: 13px;">可读取</span>
              </el-checkbox>
              <el-checkbox v-model="perms[m.key].can_write" @change="onWriteChange(m.key)">
                <span style="font-size: 13px;">可写入</span>
              </el-checkbox>
            </div>
          </div>
        </el-col>
      </el-row>
      <div class="perm-tip">
        <span class="bi bi-info-circle"></span>
        联动规则：勾选「可写入」自动授予「可读取」；取消「可读取」自动收回「可写入」。
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存权限</el-button>
        </div>
      </template>
    </CommonModal>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { usersApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, Key, RefreshRight, Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const data = ref([])
const page = ref(1)
const pageSize = ref(20)
const filters = ref({ keyword: '', role: '' })

// 用于取消请求的 AbortController
let abortController = null

const filterFields = [
  { type: 'input', key: 'keyword', label: '', placeholder: '用户名 / 姓名 / 邮箱', autoSearch: false, clearable: true, minWidth: 175 },
  { type: 'select', key: 'role', label: '角色', placeholder: '全部', autoSearch: true, clearable: true, width: 120,
    options: [
      { label: '全部', value: '' },
      { label: 'admin', value: 'admin' },
      { label: 'engineer', value: 'engineer' },
      { label: 'viewer', value: 'viewer' }
    ] }
]

// 权限模块清单（与后端 app.core.auth.PERMISSION_MODULES 一一对应）
const permModules = [
  { key: 'devices',    label: '设备管理',     icon: 'bi-cpu' },
  { key: 'weekly',     label: '生产周报',     icon: 'bi-graph-up-arrow' },
  { key: 'servers',    label: '服务器管理',   icon: 'bi-server' },
  { key: 'agingracks', label: '老化架管理',   icon: 'bi-box-seam' },
  { key: 'wifi',       label: 'WiFi AP 管理', icon: 'bi-wifi' },
  { key: 'orders',     label: 'MES 工单',     icon: 'bi-clipboard-data' },
  { key: 'bugs',       label: 'MES BUG',      icon: 'bi-bug' },
  { key: 'devreqs',    label: 'MES 需求',     icon: 'bi-lightbulb' },
  { key: 'antivirus',  label: '设备杀毒记录', icon: 'bi-shield-check' },
  { key: 'esopparts',  label: 'ESOP料号管理', icon: 'bi-file-earmark-text' },
  { key: 'exception',  label: '异常履历管理', icon: 'bi-exclamation-triangle' },
  { key: 'users',      label: '用户管理',     icon: 'bi-people' },
]
const modules = permModules.map(m => m.key)

// 客户端筛选 + 分页：filteredData 全量过滤结果，listFiltered 当前页切片
const filteredData = computed(() => {
  let arr = data.value
  if (filters.value.keyword) {
    const kw = String(filters.value.keyword).toLowerCase()
    arr = arr.filter(u =>
      (u.username || '').toLowerCase().includes(kw) ||
      (u.full_name || '').toLowerCase().includes(kw) ||
      (u.email || '').toLowerCase().includes(kw)
    )
  }
  if (filters.value.role) arr = arr.filter(u => u.role === filters.value.role)
  return arr
})

const filteredCount = computed(() => filteredData.value.length)

const listFiltered = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

const modalVisible = ref(false)
const permModalVisible = ref(false)
const editingId = ref(null)
const currentUser = ref(null)
const saving = ref(false)
const permSaving = ref(false)
const perms = ref({})
const form = ref({})

const defaultForm = () => ({ username: '', full_name: '', password: '', role: 'viewer', email: '', is_active: true })

const getRoleClass = (role) => ({ admin: 'severe', engineer: 'info', viewer: 'muted' }[role] || 'muted')

const onSearch = () => { page.value = 1 }

const loadData = async () => {
  // 取消之前的请求（如果有）
  if (abortController) {
    abortController.abort()
  }
  
  abortController = new AbortController()
  
  try {
    const res = await usersApi.list()
    data.value = res.data || []
  } catch(e) {
    // 忽略AbortError
    if (e.name !== 'AbortError') {
      console.error(e)
    }
  } finally {
    abortController = null
  }
}

const showModal = (u = null) => {
  editingId.value = u?.id
  form.value = u ? { ...u, password: '' } : defaultForm()
  modalVisible.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    if (editingId.value) {
      await usersApi.update(editingId.value, form.value)
      ElMessage.success('用户修改成功')
    } else {
      if (!form.value.username || !form.value.password) {
        ElMessage.warning('请填写用户名与密码')
        saving.value = false
        return
      }
      await usersApi.create(form.value)
      ElMessage.success('用户新增成功')
    }
    modalVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定删除该用户？此操作不可撤销。',
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning', center: true }
    )
    await usersApi.delete(id)
    ElMessage.success('用户已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

const showPermModal = (u) => {
  currentUser.value = u
  modules.forEach(m => { perms.value[m] = { can_read: true, can_write: false } })
  ;(u.permissions || []).forEach(p => {
    if (perms.value[p.module_key]) {
      perms.value[p.module_key] = { can_read: p.can_read, can_write: p.can_write }
    }
  })
  permModalVisible.value = true
}

// 权限联动：勾选「可写入」自动授予「可读取」；取消「可读取」自动收回「可写入」
const onWriteChange = (key) => {
  if (perms.value[key]?.can_write) perms.value[key].can_read = true
}
const onReadChange = (key) => {
  if (!perms.value[key]?.can_read) perms.value[key].can_write = false
}

// 快捷授权
const setAllPerms = (mode) => {
  modules.forEach(m => {
    perms.value[m] = {
      can_read: mode !== 'none',
      can_write: mode === 'write'
    }
  })
}

// 授权统计
const permStats = computed(() => {
  let readable = 0, writable = 0
  modules.forEach(m => {
    if (perms.value[m]?.can_read) readable++
    if (perms.value[m]?.can_write) writable++
  })
  return { readable, writable }
})

const handlePermSave = async () => {
  permSaving.value = true
  try {
    const payload = {
      permissions: modules.map(m => ({
        module_key: m,
        can_read: perms.value[m]?.can_read ?? false,
        can_write: perms.value[m]?.can_write ?? false,
      }))
    }
    await usersApi.permissions(currentUser.value.id, payload)
    permModalVisible.value = false
    ElMessage.success('权限保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    permSaving.value = false
  }
}

onMounted(() => {
  console.log('Users组件挂载')
  loadData()
})

onUnmounted(() => {
  console.log('Users组件卸载，清理资源')
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  data.value = []
  form.value = {}
  filters.value = { keyword: '', role: '' }
})
</script>
<style scoped>
.mod-perm-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  background: var(--card-bg);
  transition: border-color .15s, box-shadow .15s, background .15s;
}
/* 已授权读取的模块卡片高亮，未授权置灰 */
.mod-perm-card.perm-on {
  border-color: var(--primary, #2c5ce8);
  background: rgba(44, 92, 232, .05);
  box-shadow: 0 2px 8px rgba(44, 92, 232, .08);
}
.mod-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--c-text);
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--border-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.perm-checks {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 10px;
  padding-left: 4px;
}
.perm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--c-fill, #f8fafc);
  border-radius: 8px;
}
.perm-summary { font-size: 12.5px; color: var(--c-text-mute, #64748b); }
.perm-summary b { color: var(--primary, #2c5ce8); font-size: 14px; margin: 0 2px; }
.perm-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--c-text-mute, #94a3b8);
}
.perm-tip .bi { margin-right: 4px; }
</style>
