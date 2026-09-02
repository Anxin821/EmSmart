<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">🐛</span>MES BUG 管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" @click="showModal()"><el-icon><Plus /></el-icon>新增</el-button>
          </template>
        </template>
      </CommonFilterBar>
    </div>

    <div class="page-content">
    <el-table
        v-loading="loading"
        :data="items"
        stripe
        border
        style="width: 100%"
        :header-cell-style="{ fontWeight: 600 }"
        :height="'calc(100vh - 210px)'"
      >

        <el-table-column label="BUG ID" prop="bug_id" width="120" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px;">{{ row.bug_id }}</code>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="标题" min-width="200" align="center" show-overflow-tooltip>
          <template #default="{ row }">{{ row.title || '-' }}</template>
        </el-table-column>

        <el-table-column prop="severity" label="严重等级" width="100" align="center">
          <template #default="{ row }">
            <span :class="'status-badge ' + getStatusClass(cleanStatus(row.severity))">{{ cleanStatus(row.severity) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="module" label="模块" min-width="110" align="center" show-overflow-tooltip>
          <template #default="{ row }">{{ row.module || '-' }}</template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <span :class="'status-badge ' + getStatusClass(cleanStatus(row.status))">{{ cleanStatus(row.status) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="discoverer" label="发现人" min-width="90" align="center" show-overflow-tooltip>
          <template #default="{ row }">{{ row.discoverer || '-' }}</template>
        </el-table-column>

        <el-table-column prop="assignee" label="指派给" min-width="90" align="center" show-overflow-tooltip>
          <template #default="{ row }">{{ row.assignee || '-' }}</template>
        </el-table-column>

        <el-table-column prop="deadline" label="截止日期" width="110" align="center">
          <template #default="{ row }">{{ row.deadline ? row.deadline.slice(0, 10) : '-' }}</template>
        </el-table-column>

        <el-table-column label="操作" width="210" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="userStore.canEdit">
              <el-button type="primary" link size="small" @click="showModal(row)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button type="warning" link size="small" @click="handleFlow(row)">
                <el-icon><Refresh /></el-icon>流转
              </el-button>
            </template>
            <template v-if="userStore.isAdmin">
              <el-button type="danger" link size="small" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <CommonPagination
        v-model:page="page"
        v-model:page-size="pageSize"
        :total="total"
        compact
        @change="onPagerChange"
      />
    </div>

    <CommonModal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑BUG' : '新增BUG'"
      width="680px"
      :ok-loading="saving"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-6">
          <label
            class="small form-label"
            :style="editingId ? labelStyleNormal : labelStyleNoRequired"
          >
            BUG ID <span v-if="!editingId" style="font-weight:400;color:#10B981;font-size:12px;margin-left:6px;">（保存时自动生成）</span>
          </label>
          <el-input
            v-model="form.bug_id"
            :disabled="!editingId"
            clearable
            :placeholder="editingId ? '请输入BUG编号' : '保存时按 BG-YYYYMMDD-001 自动编号'"
          />
        </div>
        <div class="col-6">
          <label class="small form-label"><span style="color:var(--danger);">*</span> 标题</label>
          <el-input v-model="form.title" clearable placeholder="请输入BUG标题" maxlength="200" show-word-limit />
        </div>
        <div class="col-6">
          <label class="small form-label">严重等级</label>
          <el-select v-model="form.severity" style="width: 100%;">
            <el-option label="致命" value="致命" />
            <el-option label="严重" value="严重" />
            <el-option label="一般" value="一般" />
            <el-option label="建议" value="建议" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small form-label">模块</label>
          <el-input v-model="form.module" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">状态</label>
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="新建" value="新建" />
            <el-option label="确认" value="确认" />
            <el-option label="修复中" value="修复中" />
            <el-option label="已解决" value="已解决" />
            <el-option label="关闭" value="关闭" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small form-label">发现人</label>
          <el-input v-model="form.discoverer" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">指派给</label>
          <el-input v-model="form.assignee" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">截止日期</label>
          <el-date-picker v-model="form.deadline" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%;" />
        </div>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存</el-button>
        </div>
      </template>
    </CommonModal>
    <!-- 流转弹窗 -->
    <CommonModal
      v-model:visible="flowModalVisible"
      :title="`状态流转 - ${flowRow?.bug_id || ''}`"
      width="460px"
      :ok-loading="flowSaving"
      @ok="submitFlow"
    >
      <el-form label-width="96px" label-position="right">
        <el-form-item label="当前状态">
          <el-tag :type="flowRow?.status==='已解决'||flowRow?.status==='关闭' ? 'success' : flowRow?.status==='修复中' ? 'warning' : flowRow?.status==='确认' ? 'danger' : 'info'">
            {{ flowRow?.status }}
          </el-tag>
        </el-form-item>
        <el-form-item label="流转到" required>
          <el-radio-group v-model="flowStatus">
            <el-radio-button v-for="s in FLOW_STATUSES" :key="s" :value="s">{{ s }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="f.ok">确认流转</el-button>
        </div>
      </template>
    </CommonModal>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { mesApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, Refresh, RefreshRight, Plus } from '@element-plus/icons-vue'
import { useNotify } from '@/composables/useNotify'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const filters = ref({ keyword: '', severity: '', status: '' })
const modalVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const flowSaving = ref(false)
const form = ref({})

// 用于取消请求的 AbortController
let abortController = null

// 流转弹窗
const flowModalVisible = ref(false)
const flowRow = ref(null)
const flowStatus = ref('')
const FLOW_STATUSES = ['新建', '确认', '修复中', '已解决', '关闭']
const labelStyleNormal      = { color: 'var(--c-text-2)' }
const labelStyleNoRequired  = { color: 'var(--c-text-2)', '--required': 'none' }

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const filterFields = [
  { type: 'input', key: 'keyword', label: '', placeholder: 'BUG ID / 标题 / 模块 / 指派', autoSearch: false, clearable: true, minWidth: 260 },
  { type: 'select', key: 'severity', label: '严重等级', placeholder: '全部等级', autoSearch: true, clearable: true,
    options: [
      { label: '全部等级', value: '' },
      { label: '致命', value: '致命' },
      { label: '严重', value: '严重' },
      { label: '一般', value: '一般' },
      { label: '建议', value: '建议' }
    ] },
  { type: 'select', key: 'status', label: '状态', placeholder: '全部状态', autoSearch: true, clearable: true,
    options: [
      { label: '全部状态', value: '' },
      { label: '新建', value: '新建' },
      { label: '确认', value: '确认' },
      { label: '修复中', value: '修复中' },
      { label: '已解决', value: '已解决' },
      { label: '关闭', value: '关闭' }
    ] }
]

const cleanStatus = (v) => (v == null ? '' : String(v).replace(/^\s*\|*\s*/, '').replace(/\s*\|*\s*$/, '').trim())

const getStatusClass = (s) => {
  const map = { '致命': 'severe', '严重': 'severe', '一般': 'muted', '建议': 'muted', '新建': 'fault', '确认': 'severe', '修复中': 'progress', '已解决': 'normal', '关闭': 'normal' }
  return map[s] || 'muted'
}

const defaultForm = () => ({
  bug_id: '', title: '', severity: '一般', module: '',
  status: '新建', discoverer: '', assignee: '', deadline: ''
})

const resetFilters = () => {
  filters.value = { keyword: '', severity: '', status: '' }
  page.value = 1
  loadData()
}
// 搜索/筛选：先回到第 1 页再加载，避免停留在旧页码导致“筛选不生效”（筛选后结果变少，旧页码往往为空）
const onSearch = () => {
  page.value = 1
  loadData()
}

const loadData = async () => {
  // 取消之前的请求（如果有）
  if (abortController) {
    abortController.abort()
  }
  
  abortController = new AbortController()
  loading.value = true
  
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.value.keyword)  params.keyword  = filters.value.keyword
    if (filters.value.severity) params.severity = filters.value.severity
    if (filters.value.status)   params.status   = filters.value.status
    
    const res = await mesApi.bugs(params)
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch(e) {
    // 忽略AbortError
    if (e.name !== 'AbortError') {
      console.error(e)
    }
  } finally {
    loading.value = false
    abortController = null
  }
}

const showModal = (s = null) => {
  if (s) {
    editingId.value = s.bug_id
    form.value = { ...s }
  } else {
    editingId.value = null
    form.value = defaultForm()
  }
  modalVisible.value = true
}

const closeModal = () => {
  modalVisible.value = false
  editingId.value = null
  form.value = {}
}

const handleSave = async () => {
  if (!form.value.title || !String(form.value.title).trim()) {
    toast.warn('请输入 BUG 标题')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await mesApi.update('bugs', editingId.value, form.value)
      toast.success('修改成功')
    } else {
      const r = await mesApi.create('bugs', form.value)
      toast.success(`创建成功 ${r.data?.bug_id ? '（'+r.data.bug_id+'）' : ''}`)
    }
    closeModal()
    loadData()
  } catch (e) {
    toast.error(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const ok = await confirmDelete(`BUG ${row.bug_id}`, '删除后数据不可恢复')
  if (!ok) return
  try {
    await mesApi.delete('bugs', row.bug_id)
    toast.success('BUG删除成功')
    loadData()
  } catch(e) {
    console.error(e)
    toast.error(e.response?.data?.detail || e.response?.data?.message || '删除失败')
  }
}

// ---------- 流转 ----------
const handleFlow = (row) => {
  flowRow.value = row
  flowStatus.value = row.status || '新建'
  flowModalVisible.value = true
}

const submitFlow = async () => {
  if (!flowStatus.value) {
    toast.warn('请选择新状态')
    return
  }
  flowSaving.value = true
  try {
    await mesApi.flow('bugs', flowRow.value.bug_id, flowStatus.value)
    toast.success(`状态已更新为 ${flowStatus.value}`)
    flowModalVisible.value = false
    flowRow.value = null
    loadData()
  } catch (e) {
    toast.error(e.response?.data?.message || '流转失败')
  } finally {
    flowSaving.value = false
  }
}

const onPagerChange = () => loadData()

onMounted(() => {
  console.log('Bugs组件挂载')
  loadData()
})

onUnmounted(() => {
  console.log('Bugs组件卸载，清理资源')
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  items.value = []
  form.value = {}
  filters.value = { keyword: '', severity: '', status: '' }
})
</script>
