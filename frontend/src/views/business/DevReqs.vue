<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">💡</span>MES需求管理</h1>
      <CommonFilterBar
        :fields="filterFields"
        v-model:model-value="filters"
        @search="onSearch"
        @reset="onResetFromFilterBar"
      >
        <template #actions="scope">
          <el-button type="primary" size="default" @click="scope.search">
            <el-icon style="margin-right: 6px;"><Search /></el-icon>搜索
          </el-button>
          <el-button size="default" @click="scope.reset">
            <el-icon style="margin-right: 6px;"><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" size="default" @click="showModal()">
              <el-icon style="margin-right: 6px;"><Plus /></el-icon>新增
            </el-button>
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

        <el-table-column label="需求ID" prop="request_id" width="160" align="center" class-name="cell-clip" show-overflow-tooltip>
          <template #default="s">
            <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px;">{{ s.row.request_id }}</code>
          </template>
        </el-table-column>

        <el-table-column label="标题" prop="title" min-width="200" align="center" show-overflow-tooltip>
          <template #default="s">{{ s.row.title || '-' }}</template>
        </el-table-column>

        <el-table-column label="优先级" prop="priority" width="100" align="center">
          <template #default="s">
            <span :class="'status-badge ' + getStatusClass(cleanField(s.row.priority))">{{ cleanField(s.row.priority) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" prop="status" width="100" align="center">
          <template #default="s">
            <span :class="'status-badge ' + getStatusClass(cleanField(s.row.status))">{{ cleanField(s.row.status) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="提交人" prop="submitter" min-width="90" align="center" show-overflow-tooltip>
          <template #default="s">{{ s.row.submitter || '-' }}</template>
        </el-table-column>

        <el-table-column label="指派给" prop="assignee" min-width="90" align="center" show-overflow-tooltip>
          <template #default="s">{{ s.row.assignee || '-' }}</template>
        </el-table-column>

        <el-table-column label="期望日期" prop="expected_date" width="120" align="center">
          <template #default="s">{{ s.row.expected_date ? s.row.expected_date.slice(0, 10) : '-' }}</template>
        </el-table-column>

        <el-table-column label="操作" width="210" align="center" fixed="right">
          <template #default="s">
            <template v-if="userStore.canEdit">
              <el-button type="primary" link size="small" @click="showModal(s.row)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button type="warning" link size="small" @click="handleFlow(s.row)">
                <el-icon><Refresh /></el-icon>流转
              </el-button>
            </template>
            <template v-if="userStore.isAdmin">
              <el-button type="danger" link size="small" @click="handleDelete(s.row)">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </template>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :image-size="80" description="暂无数据">
            <template #image>
              <div style="font-size: 44px;">💡</div>
            </template>
          </el-empty>
        </template>
      </el-table>

      <CommonPagination
        v-model:page="page"
        v-model:page-size="pageSize"
        :total="total"
        @change="onPagerChange"
      />
    </div>

    <CommonModal
      v-model:visible="modalVisible"
      :width="680"
      :title="editingId ? '编辑需求' : '新增需求'"
      :title-icon="editingId ? 'bi bi-pencil-square' : 'bi bi-plus-square'"
      :title-icon-color="editingId ? 'var(--primary)' : 'var(--ok)'"
      :show-footer="false"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-6">
          <label class="small">需求ID</label>
          <el-input v-model="form.request_id" clearable />
        </div>
        <div class="col-6">
          <label class="small">标题</label>
          <el-input v-model="form.title" clearable />
        </div>
        <div class="col-6">
          <label class="small">优先级</label>
          <el-select v-model="form.priority" style="width: 100%;">
            <el-option label="紧急" value="紧急" />
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small">状态</label>
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="收集" value="收集" />
            <el-option label="评估" value="评估" />
            <el-option label="开发中" value="开发中" />
            <el-option label="测试" value="测试" />
            <el-option label="上线" value="上线" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small">提交人</label>
          <el-input v-model="form.submitter" clearable />
        </div>
        <div class="col-6">
          <label class="small">指派给</label>
          <el-input v-model="form.assignee" clearable />
        </div>
        <div class="col-6">
          <label class="small">期望日期</label>
          <el-date-picker
            v-model="form.expected_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%;"
          />
        </div>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button :disabled="f.okLoading" @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="handleSave">
            <i v-if="!f.okLoading" class="bi bi-check2" style="margin-right: 4px;"></i>
            {{ f.okLoading ? '保存中...' : '保存' }}
          </el-button>
        </div>
      </template>
    </CommonModal>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { mesApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, Refresh, Plus, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const filters = ref({ keyword: '', priority: '', status: '' })
const modalVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({})

// 用于取消请求的 AbortController
let abortController = null

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const filterFields = computed(() => [
  {
    type: 'input',
    key: 'keyword',
    label: '',
    placeholder: '需求ID/标题/指派/提交',
    minWidth: 220,
    showSearchIcon: true,
    autoSearch: false
  },
  { type: 'divider' },
  {
    type: 'select',
    key: 'priority',
    label: '优先级',
    minWidth: 100,
    options: [
      { label: '全部', value: '' },
      { label: '紧急', value: '紧急' },
      { label: '高', value: '高' },
      { label: '中', value: '中' },
      { label: '低', value: '低' }
    ],
    autoSearch: true
  },
  {
    type: 'select',
    key: 'status',
    label: '状态',
    minWidth: 100,
    options: [
      { label: '全部', value: '' },
      { label: '收集', value: '收集' },
      { label: '评估', value: '评估' },
      { label: '开发中', value: '开发中' },
      { label: '测试', value: '测试' },
      { label: '上线', value: '上线' }
    ],
    autoSearch: true
  }
])

const cleanField = (v) => (v == null ? '' : String(v).replace(/^\s*\|*\s*/, '').replace(/\s*\|*\s*$/, '').trim())

const getStatusClass = (s) => {
  const map = { '紧急': 'severe', '高': 'severe', '中': 'info', '低': 'muted', '收集': 'info', '评估': 'purple', '开发中': 'progress', '测试': 'warn', '上线': 'normal' }
  return map[s] || 'muted'
}

const defaultForm = () => ({
  request_id: '', title: '', priority: '中', status: '收集',
  submitter: '', assignee: '', expected_date: ''
})

const resetFilters = () => {
  filters.value = { keyword: '', priority: '', status: '' }
  page.value = 1
  loadData()
}
// 搜索/筛选：先回到第 1 页再加载，避免停留在旧页码导致“筛选不生效”（筛选后结果变少，旧页码往往为空）
const onSearch = () => {
  page.value = 1
  loadData()
}

const onResetFromFilterBar = () => {
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
    if (filters.value.priority) params.priority = filters.value.priority
    if (filters.value.status)   params.status   = filters.value.status
    
    const res = await mesApi.devreqs(params)
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
    editingId.value = s.request_id
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
  if (!form.value.request_id) {
    ElMessage.warning('请填写需求ID')
    return
  }
  saving.value = true
  try {
    if (editingId.value) await mesApi.update('dev-requests', editingId.value, form.value)
    else                  await mesApi.create('dev-requests', form.value)
    closeModal()
    loadData()
    ElMessage.success(editingId.value ? '需求修改成功' : '需求新增成功')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const reqId = row.request_id || '该需求'
  try {
    await ElMessageBox.confirm(
      `确定要删除需求「${reqId}」吗？此操作不可撤销。`,
      '删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        center: true
      }
    )
    await mesApi.delete('dev-requests', row.request_id)
    ElMessage.success('需求已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '删除失败')
    }
  }
}

const handleFlow = async (s) => {
  const { value } = await ElMessageBox.prompt(
    '请输入新状态 (收集/评估/开发中/测试/上线)',
    '需求流转',
    {
      confirmButtonText: '确认流转',
      cancelButtonText: '取消',
      inputPattern: /^(收集|评估|开发中|测试|上线)$/,
      inputErrorMessage: '状态值不正确',
      inputValue: s.status,
      center: true
    }
  )
  await mesApi.update('dev-requests', s.request_id, { status: value })
  ElMessage.success('需求流转成功')
  loadData()
}

const onPagerChange = () => loadData()

onMounted(() => {
  console.log('DevReqs组件挂载')
  loadData()
})

onUnmounted(() => {
  console.log('DevReqs组件卸载，清理资源')
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  items.value = []
  form.value = {}
  filters.value = { keyword: '', priority: '', status: '' }
})
</script>
