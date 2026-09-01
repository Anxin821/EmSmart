<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">📝</span>MES 工单管理</h1>
      <CommonFilterBar
        :fields="filterFields"
        v-model:model-value="filters"
        @search="loadData"
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
      style="width: 100%"
      :header-cell-style="{ fontWeight: 600 }"
      :row-style="{ fontSize: '13px' }"
    >

      <el-table-column label="工单号" prop="order_number" width="140">
        <template #default="s">
          <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px; font-weight: 600;">
            {{ s.row.order_number }}
          </code>
        </template>
      </el-table-column>

      <el-table-column label="类型" prop="order_type" width="90">
        <template #default="s">
          <span class="badge" style="padding: 2px 10px; border-radius: 12px; background: var(--info-bg); color: var(--info);">
            {{ s.row.order_type }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="产品" prop="product_name" min-width="200">
        <template #default="s">{{ s.row.product_name || '-' }}</template>
      </el-table-column>

      <el-table-column label="优先级" prop="priority" width="90">
        <template #default="s">
          <span :class="'status-badge ' + getStatusClass(s.row.priority)">{{ s.row.priority }}</span>
        </template>
      </el-table-column>

      <el-table-column label="计划开始" prop="planned_start" width="110">
        <template #default="s">{{ s.row.planned_start ? s.row.planned_start.slice(0, 10) : '-' }}</template>
      </el-table-column>

      <el-table-column label="计划结束" prop="planned_end" width="110">
        <template #default="s">{{ s.row.planned_end ? s.row.planned_end.slice(0, 10) : '-' }}</template>
      </el-table-column>

      <el-table-column label="状态" prop="status" width="90">
        <template #default="s">
          <span :class="'status-badge ' + getStatusClass(s.row.status)">{{ s.row.status }}</span>
        </template>
      </el-table-column>

      <el-table-column label="负责人" prop="responsible_person" min-width="90">
        <template #default="s">{{ s.row.responsible_person || '-' }}</template>
      </el-table-column>

      <el-table-column label="操作" width="180" fixed="right">
        <template #default="s">
          <div class="row-actions">
            <el-button
              v-if="userStore.canEdit"
              type="primary"
              link
              @click="showModal(s.row)"
            >
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button
              v-if="userStore.canEdit"
              type="warning"
              link
              @click="handleFlow(s.row)"
            >
              <el-icon><Refresh /></el-icon> 流转
            </el-button>
            <el-button
              v-if="userStore.isAdmin"
              type="danger"
              link
              @click="handleDelete(s.row)"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :image-size="80" description="暂无数据">
          <template #image>
            <div style="font-size: 44px;">📝</div>
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
      :title="editingId ? '编辑工单' : '新增工单'"
      :title-icon="editingId ? 'bi bi-pencil-square' : 'bi bi-plus-square'"
      :title-icon-color="editingId ? 'var(--primary)' : 'var(--ok)'"
      :show-footer="false"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-6">
          <label class="small">工单号</label>
          <el-input v-model="form.order_number" clearable />
        </div>
        <div class="col-6">
          <label class="small">类型</label>
          <el-select v-model="form.order_type" style="width: 100%;">
            <el-option label="生产" value="生产" />
            <el-option label="维修" value="维修" />
            <el-option label="保养" value="保养" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small">产品名称</label>
          <el-input v-model="form.product_name" clearable />
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
          <label class="small">计划开始</label>
          <el-date-picker
            v-model="form.planned_start"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%;"
          />
        </div>
        <div class="col-6">
          <label class="small">计划结束</label>
          <el-date-picker
            v-model="form.planned_end"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%;"
          />
        </div>
        <div class="col-6">
          <label class="small">状态</label>
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="待开始" value="待开始" />
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="挂起" value="挂起" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small">负责人</label>
          <el-input v-model="form.responsible_person" clearable />
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
const filters = ref({ keyword: '', status: '', priority: '' })
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
    placeholder: '工单号 / 产品 / 负责人',
    minWidth: 260,
    showSearchIcon: true,
    autoSearch: false
  },
  { type: 'divider' },
  {
    type: 'select',
    key: 'status',
    label: '状态',
    minWidth: 130,
    options: [
      { label: '全部状态', value: '' },
      { label: '待开始', value: '待开始' },
      { label: '进行中', value: '进行中' },
      { label: '已完成', value: '已完成' },
      { label: '挂起', value: '挂起' }
    ],
    autoSearch: true
  },
  {
    type: 'select',
    key: 'priority',
    label: '优先级',
    minWidth: 130,
    options: [
      { label: '全部优先级', value: '' },
      { label: '紧急', value: '紧急' },
      { label: '高', value: '高' },
      { label: '中', value: '中' },
      { label: '低', value: '低' }
    ],
    autoSearch: true
  }
])

const getStatusClass = (s) => {
  const map = { '紧急': 'severe', '高': 'severe', '中': 'info', '低': 'muted', '待开始': 'muted', '进行中': 'info', '已完成': 'normal', '挂起': 'warn' }
  return map[s] || 'muted'
}

const defaultForm = () => ({
  order_number: '', order_type: '生产', product_name: '', priority: '中',
  planned_start: '', planned_end: '', status: '待开始', responsible_person: ''
})

const resetFilters = () => {
  filters.value = { keyword: '', status: '', priority: '' }
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
    if (filters.value.status)   params.status   = filters.value.status
    if (filters.value.priority) params.priority = filters.value.priority
    
    const res = await mesApi.orders(params)
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
    editingId.value = s.order_number
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
  if (!form.value.order_number) {
    ElMessage.warning('请填写工单号')
    return
  }
  saving.value = true
  try {
    if (editingId.value) await mesApi.update('work-orders', editingId.value, form.value)
    else                  await mesApi.create('work-orders', form.value)
    closeModal()
    loadData()
    ElMessage.success(editingId.value ? '工单修改成功' : '工单新增成功')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const orderNumber = row.order_number || '该工单'
  try {
    await ElMessageBox.confirm(
      `确定要删除工单「${orderNumber}」吗？此操作不可撤销。`,
      '删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        center: true
      }
    )
    await mesApi.delete('work-orders', row.order_number)
    ElMessage.success('工单已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '删除失败')
    }
  }
}

const handleFlow = async (s) => {
  const { value } = await ElMessageBox.prompt(
    `请输入新状态 (待开始 / 进行中 / 已完成 / 挂起)`,
    '工单流转',
    {
      confirmButtonText: '确认流转',
      cancelButtonText: '取消',
      inputPattern: /^(待开始|进行中|已完成|挂起)$/,
      inputErrorMessage: '状态值不正确',
      inputValue: s.status,
      center: true
    }
  )
  await mesApi.flow('work-orders', s.order_number, value)
  ElMessage.success('工单流转成功')
  loadData()
}

const onPagerChange = () => loadData()

onMounted(() => {
  console.log('Orders组件挂载')
  loadData()
})

onUnmounted(() => {
  console.log('Orders组件卸载，清理资源')
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  items.value = []
  form.value = {}
  filters.value = { keyword: '', status: '', priority: '' }
})
</script>
