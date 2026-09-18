<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title"><span class="emoji">👥</span></h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canWrite('users')">
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
            <template v-if="userStore.canWrite('users')">
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
      <div class="form-grid">
  <div class="form-item">
    <label class="form-label">用户名 <span class="required">*</span></label>
    <el-input v-model="form.username" clearable placeholder="登录账号" />
  </div>
  <div class="form-item">
    <label class="form-label">姓名</label>
    <el-input v-model="form.full_name" clearable placeholder="真实姓名" />
  </div>
  <div class="form-item">
    <label class="form-label">密码 <span class="required" v-if="!editingId">*</span></label>
    <el-input v-model="form.password" type="password" show-password clearable
              :placeholder="editingId ? '留空则不修改' : '请输入密码'" />
  </div>
  <div class="form-item">
    <label class="form-label">角色</label>
    <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%;">
      <el-option label="admin" value="admin" />
      <el-option label="engineer" value="engineer" />
      <el-option label="viewer" value="viewer" />
    </el-select>
  </div>
  <div class="form-item">
    <label class="form-label">邮箱</label>
    <el-input v-model="form.email" clearable placeholder="email@example.com" />
  </div>
  <div class="form-item">
    <label class="form-label">状态</label>
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
      width="680px"
      :ok-loading="permSaving"
      @ok="handlePermSave"
    >
      <!-- admin 提示 -->
      <el-alert
        v-if="currentUser?.role === 'admin'"
        type="info" :closable="false" show-icon
        title="该用户为 admin 角色，默认拥有全部模块读写权限，此处授权仅对 engineer / viewer 角色生效。"
        style="margin-bottom: 10px;"
      />

      <!-- 工具栏：搜索 + 快捷操作 -->
      <div class="perm-bar">
        <el-input
          v-model="permSearch"
          placeholder="搜索模块..."
          clearable
          size="default"
          class="perm-search"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <div class="perm-quick">
          <el-button size="small" type="primary" plain @click="setAllPerms('write')">全部读写</el-button>
          <el-button size="small" plain @click="setAllPerms('read')">全部只读</el-button>
          <el-button size="small" plain @click="setAllPerms('none')">全部清空</el-button>
        </div>
      </div>

      <!-- 统计 -->
      <div class="perm-summary">
        <span>已授权 <b class="stat-read">{{ permStats.readable }}</b> / {{ permModules.length }} 个模块可读</span>
        <span class="perm-summary-dot">·</span>
        <span><b class="stat-write">{{ permStats.writable }}</b> 个可写</span>
      </div>

      <!-- 模块列表 -->
      <div class="perm-list">
        <div
          v-for="m in filteredPermModules"
          :key="m.key"
          class="perm-row"
          :class="{ 'is-on': perms[m.key]?.can_read }"
        >
          <span :class="['bi', m.icon]" class="perm-row-icon"></span>
          <span class="perm-row-label">{{ m.label }}</span>
          <div class="perm-row-actions">
            <button
              type="button"
              class="perm-btn perm-btn--read"
              :class="{ active: perms[m.key]?.can_read }"
              @click="toggleRead(m.key)"
            >
              <span class="dot"></span>{{ perms[m.key]?.can_read ? '可读' : '不可读' }}
            </button>
            <button
              type="button"
              class="perm-btn perm-btn--write"
              :class="{ active: perms[m.key]?.can_write }"
              :disabled="!perms[m.key]?.can_read"
              @click="toggleWrite(m.key)"
            >
              <span class="dot"></span>{{ perms[m.key]?.can_write ? '可写' : '不可写' }}
            </button>
          </div>
        </div>
        <div v-if="!filteredPermModules.length" class="perm-empty">
          没有匹配「{{ permSearch }}」的模块
        </div>
      </div>

      <div class="perm-tip">
        <span class="bi bi-info-circle"></span>
        联动规则：勾选「可写」自动授予「可读」；取消「可读」自动收回「可写」。
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
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const data = ref([])
const page = ref(1)
const pageSize = ref(20)
const filters = ref({ keyword: '', role: '' })

// 用于取消请求的 AbortController
let _reqSeq = 0

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
  { key: 'warehouse',  label: '库房管理',     icon: 'bi-box-seam' },
  { key: 'users',      label: '用户管理',     icon: 'bi-people' },
]
const modules = permModules.map(m => m.key)
const filteredPermModules = computed(() => {
  const kw = (permSearch.value || '').trim().toLowerCase()
  if (!kw) return permModules
  return permModules.filter(m =>
    m.label.toLowerCase().includes(kw) || m.key.toLowerCase().includes(kw)
  )
})

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
const permSearch = ref('')
const form = ref({})

const defaultForm = () => ({ username: '', full_name: '', password: '', role: 'viewer', email: '', is_active: true })

const getRoleClass = (role) => ({ admin: 'severe', engineer: 'info', viewer: 'muted' }[role] || 'muted')

const onSearch = () => { page.value = 1 }



const showModal = (u = null) => {
  editingId.value = u?.id
  form.value = u ? {
    username:  u.username  || '',
    full_name: u.full_name || '',
    email:     u.email     || '',
    role:      u.role      || 'viewer',
    is_active: u.is_active ?? true,
    password:  '',       // 编辑时留空 = 不改密码
  } : defaultForm()
  modalVisible.value = true
}

const handleSave = async () => {
  if (saving.value) return   // ← 加这行，防双击
  saving.value = true
  try {
    if (editingId.value) {
      await usersApi.update(editingId.value, form.value)
      ElMessage.success('用户修改成功')
    } else {
      // 替换为
const username = (form.value.username || '').trim()
if (!username) {
  ElMessage.warning('请填写用户名')
  saving.value = false
  return
}
if (!/^[a-zA-Z0-9_-]{3,20}$/.test(username)) {
  ElMessage.warning('用户名需为 3-20 位字母 / 数字 / 下划线 / 中划线')
  saving.value = false
  return
}
if (!form.value.password || form.value.password.length < 6) {
  ElMessage.warning('密码长度不能少于 6 位')
  saving.value = false
  return
}
form.value.username = username   // 顺带 trim
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
  permSearch.value = ''          // ← 加这行，每次打开清空搜索
  modules.forEach(m => { perms.value[m] = { can_read: true, can_write: false } })
  ;(u.permissions || []).forEach(p => {
    if (perms.value[p.module_key]) {
      perms.value[p.module_key] = { can_read: p.can_read, can_write: p.can_write }
    }
  })
  permModalVisible.value = true
}

const toggleRead = (key) => {
  if (!perms.value[key]) return
  perms.value[key].can_read = !perms.value[key].can_read
  if (!perms.value[key].can_read) perms.value[key].can_write = false
}
const toggleWrite = (key) => {
  if (!perms.value[key]?.can_read) return
  perms.value[key].can_write = !perms.value[key].can_write
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
  loadData()
})

const loadData = async () => {
  const seq = ++_reqSeq
  try {
    const res = await usersApi.list()
    if (seq !== _reqSeq) return   // 被更新的请求超越，忽略本次结果
    data.value = res.data || []
  } catch (e) {
    console.error(e)
  }
}

// onUnmounted 里删掉 abortController 相关行
onUnmounted(() => {
  data.value = []
  form.value = {}
  filters.value = { keyword: '', role: '' }
})
</script>
<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 16px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text);
}
.required { color: var(--err, #DC2626); }
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
/* 工具栏：搜索 + 快捷操作 */
.perm-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.perm-search { flex: 1; min-width: 180px; }
.perm-quick { display: flex; gap: 6px; flex-shrink: 0; }

/* 统计行 */
.perm-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-bottom: 10px;
  background: var(--c-fill, #f8fafc);
  border-radius: 8px;
  font-size: 13px;
  color: var(--c-text-mute, #64748b);
}
.perm-summary b { font-size: 15px; margin: 0 2px; }
.perm-summary .stat-read  { color: var(--primary, #2c5ce8); }
.perm-summary .stat-write { color: #16a34a; }
.perm-summary-dot { color: var(--c-text-mute, #cbd5e1); }

/* 模块列表 */
.perm-list {
  max-height: 460px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  background: var(--card-bg);
}
.perm-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background .12s;
}
.perm-row + .perm-row { margin-top: 2px; }
.perm-row:hover { background: var(--c-fill, #f8fafc); }


.perm-row-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  color: var(--c-text-mute, #94a3b8);
  flex-shrink: 0;
  transition: color .12s;
}

.perm-row-label {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--c-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color .12s;
}
.perm-row.is-on {
  background: #eff5ff;              /* 淡蓝底，浅色主题安全 */
}
.perm-row.is-on .perm-row-icon {
  color: #2c5ce8;
}
.perm-row.is-on .perm-row-label {
  color: #1a3fb8;                  /* 比主色略深，保证白底对比 */
  font-weight: 600;
}

/* 暗色主题兜底（如果你的项目有 .dark 或 body.dark 类） */
:global(.dark) .perm-row.is-on {
  background: rgba(44, 92, 232, .15);
}
.perm-row-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* 双按钮：可读 / 可写 */
.perm-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 12px;
  min-width: 76px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--c-text-mute, #64748b);
  font-size: 12.5px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
  user-select: none;
}
.perm-btn .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: .4;
  transition: opacity .15s;
}
/* 未激活状态：悬停显示蓝描边 */
.perm-btn:hover:not(:disabled):not(.active) {
  border-color: var(--primary, #2c5ce8);
  color: var(--primary, #2c5ce8);
}

/* 激活状态：悬停加深背景，保持白字 */
.perm-btn--read.active:hover:not(:disabled) {
  background: #1e4bd0;
  border-color: #1e4bd0;
  color: #fff;
}
.perm-btn--write.active:hover:not(:disabled) {
  background: #15803d;
  border-color: #15803d;
  color: #fff;
}
/* active 状态 hover 保持白字 + 稍加深背景 */
.perm-btn--read.active:hover:not(:disabled) {
  background: #1e4bd0;
  border-color: #1e4bd0;
  color: #fff;
}
.perm-btn--write.active:hover:not(:disabled) {
  background: #15803d;
  border-color: #15803d;
  color: #fff;
}
.perm-btn.active .dot { opacity: 1; }
.perm-btn--read.active {
  border-color: var(--primary, #2c5ce8);
  background: var(--primary, #2c5ce8);
  color: #fff;
}
.perm-btn--write.active {
  border-color: #16a34a;
  background: #16a34a;
  color: #fff;
}
.perm-btn:disabled {
  opacity: .35;
  cursor: not-allowed;
}

/* 空状态 */
.perm-empty {
  padding: 36px 0;
  text-align: center;
  color: var(--c-text-mute, #94a3b8);
  font-size: 13px;
}

/* 提示（保留原样式即可，无需改） */
.perm-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--c-text-mute, #94a3b8);
}
.perm-tip .bi { margin-right: 4px; }
.perm-summary { font-size: 12.5px; color: var(--c-text-mute, #64748b); }
.perm-summary b { color: var(--primary, #2c5ce8); font-size: 14px; margin: 0 2px; }
.perm-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--c-text-mute, #94a3b8);
}
.perm-tip .bi { margin-right: 4px; }
</style>