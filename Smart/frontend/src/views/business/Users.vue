<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><span class="emoji">👥</span>用户管理</h1>
        <div class="page-sub">
          共 <b style="color: var(--primary);">{{ data.length }}</b> 位用户
        </div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-secondary" @click="loadData">
          <span class="bi bi-arrow-clockwise"></span>刷新
        </button>
        <template v-if="userStore.isAdmin">
          <button class="btn btn-sm btn-outline-primary" @click="showModal()">
            <span class="bi bi-plus-lg"></span>新增用户
          </button>
        </template>
      </div>
    </div>

    <section class="page-section" style="padding: 0; overflow: hidden;">
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
        </template>
      </CommonFilterBar>

      <el-table :data="listFiltered" stripe border style="width: 100%;" empty-text="暂无数据">
        <el-table-column prop="username" label="用户名" width="130" align="center" show-overflow-tooltip>
          <template #default="{ row }"><b>{{ row.username }}</b></template>
        </el-table-column>
        <el-table-column prop="full_name" label="姓名" min-width="110" align="center" show-overflow-tooltip>
          <template #default="{ row }">{{ row.full_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="110" align="center">
          <template #default="{ row }">
            <span :class="'status-badge ' + getRoleClass(row.role)">{{ row.role }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" align="center" show-overflow-tooltip>
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
        v-model:pageSize="pageSize"
        :total="filteredCount"
        compact
      />
    </section>

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
        <el-button @click="f.cancel">取消</el-button>
        <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存</el-button>
      </template>
    </CommonModal>

    <!-- 权限设置弹框 -->
    <CommonModal
      v-model:visible="permModalVisible"
      :title="'权限设置 - ' + (currentUser?.username || '')"
      width="720px"
      :ok-loading="permSaving"
      @ok="handlePermSave"
    >
      <el-row :gutter="16">
        <el-col v-for="m in modules" :key="m" :span="8" style="margin-bottom: 16px;">
          <div class="mod-perm-card">
            <div class="mod-title">
              <span class="bi bi-folder2" style="color: var(--primary); margin-right: 6px;"></span>
              {{ moduleLabel(m) }}
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 10px; padding-left: 4px;">
              <el-checkbox v-model="perms[m].can_read">可读取</el-checkbox>
              <el-checkbox v-model="perms[m].can_write">可写入</el-checkbox>
            </div>
          </div>
        </el-col>
      </el-row>
      <template #footer="f">
        <el-button @click="f.cancel">取消</el-button>
        <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存权限</el-button>
      </template>
    </CommonModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usersApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, Key, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const data = ref([])
const page = ref(1)
const pageSize = ref(20)
const filters = ref({ keyword: '', role: '' })

const filterFields = [
  { type: 'input', key: 'keyword', label: '', placeholder: '用户名 / 姓名 / 邮箱', autoSearch: false, clearable: true },
  { type: 'select', key: 'role', label: '角色', placeholder: '全部角色', autoSearch: true, clearable: true,
    options: [
      { label: '全部角色', value: '' },
      { label: 'admin', value: 'admin' },
      { label: 'engineer', value: 'engineer' },
      { label: 'viewer', value: 'viewer' }
    ] }
]

const moduleLabel = (k) => ({
  devices: '设备管理', weekly: '周报', monthly: '月报',
  servers: '服务器', agingracks: '老化架', wifi: 'WiFi AP',
  orders: '工单', bugs: 'BUG', devreqs: '需求',
  antivirus: '杀毒记录', users: '用户管理'
}[k] || k)

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
const modules = ['devices', 'weekly', 'monthly', 'servers', 'agingracks', 'wifi', 'orders', 'bugs', 'devreqs', 'antivirus', 'users']
const perms = ref({})
const form = ref({})

const defaultForm = () => ({ username: '', full_name: '', password: '', role: 'viewer', email: '', is_active: true })

const getRoleClass = (role) => ({ admin: 'severe', engineer: 'info', viewer: 'muted' }[role] || 'muted')

const onSearch = () => { page.value = 1 }

const loadData = async () => {
  try {
    const res = await usersApi.list()
    data.value = res.data || []
  } catch (e) {
    console.error(e)
  }
}

const showModal = (u = null) => {
  editingId.value = u?.user_id
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

const handlePermSave = async () => {
  permSaving.value = true
  try {
    await usersApi.permissions(currentUser.value.user_id, perms.value)
    permModalVisible.value = false
    ElMessage.success('权限保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    permSaving.value = false
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.mod-perm-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  background: var(--card-bg);
}
.mod-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--c-text);
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--border-2);
}
</style>
