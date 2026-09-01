<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">📦</span> 老化架管理</h1>
      <CommonFilterBar :fields="filterFields" v-model:model-value="filters" @search="loadData">
        <template #actions="scope">
          <el-button type="primary" size="default" @click="scope.search"><el-icon style="margin-right:6px;"><Search /></el-icon>搜索</el-button>
          <el-button size="default" @click="resetFilters"><el-icon style="margin-right:6px;"><RefreshRight /></el-icon>重置</el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" size="default" @click="openCreateModal"><el-icon style="margin-right:6px;"><Plus /></el-icon>新增老化架</el-button>
          </template>
        </template>
      </CommonFilterBar>
    </div>

    <div class="page-content">
    <el-table v-loading="loading" :data="items" stripe border style="width:100%" :height="'calc(100vh - 210px)'" empty-text="暂无数据" :header-cell-style="{fontWeight:600}">

      <el-table-column label="老化架ID" prop="rack_id" width="120" align="center" show-overflow-tooltip>
        <template #default="s">
          <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px;">{{ s.row.rack_id }}</code>
        </template>
      </el-table-column>

      <el-table-column label="名称" prop="name" min-width="200" align="center" show-overflow-tooltip>
        <template #default="s"><span class="fw-semibold" style="color: var(--c-text);">{{ s.row.name }}</span></template>
      </el-table-column>

      <el-table-column label="产线" prop="production_line" width="90" align="center" />

      <el-table-column label="位置" prop="location" min-width="120" align="center" show-overflow-tooltip>
        <template #default="s">{{ s.row.location || '-' }}</template>
      </el-table-column>

      <el-table-column label="IP" prop="ip_address" width="130" align="center" show-overflow-tooltip>
        <template #default="s">
          <span style="font-family: Consolas, 'Courier New', monospace; font-size: var(--fn-sm);">{{ s.row.ip_address }}</span>
        </template>
      </el-table-column>

      <el-table-column label="槽位" width="90" align="center">
        <template #default="s">{{ s.row.used_slots || 0 }}/{{ s.row.total_slots || 0 }}</template>
      </el-table-column>

      <el-table-column label="状态" prop="status" width="90" align="center">
        <template #default="s">
          <span :class="'status-badge ' + statusClass(s.row.status)">{{ s.row.status }}</span>
        </template>
      </el-table-column>

      <el-table-column label="负责人" prop="responsible_person" min-width="90" align="center" show-overflow-tooltip>
        <template #default="s">{{ s.row.responsible_person || '-' }}</template>
      </el-table-column>

      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="s">
          <template v-if="userStore.canEdit">
            <el-button type="primary" link size="small" @click="openEditModal(s.row)">
              <el-icon style="margin-right:2px;"><Edit /></el-icon>编辑
            </el-button>
            <el-button v-if="userStore.isAdmin" type="danger" link size="small" @click="handleDelete(s.row)">
              <el-icon style="margin-right:2px;"><Delete /></el-icon>删除
            </el-button>
          </template>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :image-size="80" description="暂无数据...">
          <template #image><div style="font-size:44px;">📦</div></template>
        </el-empty>
      </template>
    </el-table>

      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact />
    </div>

    <!-- 新增/编辑 Modal -->
    <CommonModal
      v-model:visible="formModalVisible"
      :title="formMode === 'create' ? '新增老化架' : '编辑老化架'"
      width="640px"
      :ok-loading="saving"
      @ok="submitForm"
    >
      <el-form :model="form" label-width="84px" label-position="right">
        <div class="row g-3">
          <div class="col-6">
            <el-form-item label="老化架ID" required>
              <el-input v-model="form.rack_id" clearable placeholder="如：AR-001" maxlength="32" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="名称" required>
              <el-input v-model="form.name" clearable placeholder="请输入老化架名称" maxlength="64" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="产线" required>
              <el-select v-model="form.production_line" style="width:100%;">
                <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="位置">
              <el-input v-model="form.location" clearable placeholder="如：C栋3楼东区" maxlength="64" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="IP地址">
              <el-input v-model="form.ip_address" clearable placeholder="192.168.x.x" maxlength="39" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="总槽位">
              <el-input-number v-model="form.total_slots" :min="0" :max="1000" style="width:100%;" controls-position="right" />
            </el-form-item>
          </div>
          <div class="col-6" v-if="formMode === 'edit'">
            <el-form-item label="已用槽位">
              <el-input-number v-model="form.used_slots" :min="0" :max="form.total_slots || 0" style="width:100%;" controls-position="right" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%;">
                <el-option label="正常" value="正常" />
                <el-option label="故障" value="故障" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="负责人">
              <el-input v-model="form.responsible_person" clearable placeholder="请输入负责人姓名" maxlength="32" />
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="f.ok">
            {{ formMode === 'create' ? '创建' : '保存修改' }}
          </el-button>
        </div>
      </template>
    </CommonModal>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { networkApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight, Plus } from '@element-plus/icons-vue'
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
const filters = ref({ keyword:'', line:'', status:'' })
const lines = ['1线','2线','3线','4线','5线','6线','7线','8线']

// 用于取消请求的 AbortController
let abortController = null

// 表单弹窗
const formModalVisible = ref(false)
const formMode = ref('create')
const saving = ref(false)
const editRow = ref(null)
const form = ref({
  rack_id: '', name: '', production_line: '1线', location: '',
  ip_address: '', total_slots: 40, used_slots: 0, status: '正常', responsible_person: ''
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const filterFields = computed(() => [
  {
    type: 'input',
    key: 'keyword',
    label: '',
    placeholder: '老化架ID / 名称 / IP / 负责人',
    width: 200,
    showSearchIcon: true,
    autoSearch: false
  },
  {
    type: 'select',
    key: 'line',
    label: '产线',
    width: 100,
    options: [
      { label: '全部', value: '' },
      ...lines.map(l => ({ label: l, value: l }))
    ],
    autoSearch: true
  },
  {
    type: 'select',
    key: 'status',
    label: '状态',
    width: 100,
    options: [
      { label: '全部', value: '' },
      { label: '正常', value: '正常' },
      { label: '故障', value: '故障' }
    ],
    autoSearch: true
  }
])

const statusClass = (s) => ({ '正常':'normal', '故障':'fault' }[s] || 'muted')

const resetFilters = () => {
  filters.value = { keyword:'', line:'', status:'' }
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
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.line) params.production_line = filters.value.line
    if (filters.value.status) params.status = filters.value.status
    
    const res = await networkApi.agingracks(params)
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

const openCreateModal = () => {
  formMode.value = 'create'
  editRow.value = null
  form.value = {
    rack_id: '', name: '', production_line: '1线', location: '',
    ip_address: '', total_slots: 40, used_slots: 0, status: '正常', responsible_person: ''
  }
  formModalVisible.value = true
}

const openEditModal = (row) => {
  formMode.value = 'edit'
  editRow.value = row
  form.value = {
    rack_id: row.rack_id ?? '',
    name: row.name ?? '',
    production_line: row.production_line ?? '1线',
    location: row.location ?? '',
    ip_address: row.ip_address ?? '',
    total_slots: typeof row.total_slots === 'number' ? row.total_slots : 40,
    used_slots: typeof row.used_slots === 'number' ? row.used_slots : 0,
    status: row.status ?? '正常',
    responsible_person: row.responsible_person ?? '',
  }
  formModalVisible.value = true
}

const submitForm = async () => {
  const d = form.value
  if (!d.rack_id || !d.rack_id.trim()) { toast.warn('请输入老化架ID'); return }
  if (!d.name    || !d.name.trim())    { toast.warn('请输入名称');       return }
  if (!d.production_line)              { toast.warn('请选择产线');       return }
  saving.value = true
  try {
    if (formMode.value === 'create') {
      await networkApi.create('aging-racks', d)
      toast.success('创建成功')
    } else {
      await networkApi.update('aging-racks', editRow.value.rack_id, d)
      toast.success('修改成功')
    }
    formModalVisible.value = false
    loadData()
  } catch(e) {
    console.error(e)
    toast.error(e.response?.data?.message || (formMode.value === 'create' ? '创建失败' : '修改失败'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const ok = await confirmDelete(`老化架 ${row.name}（${row.rack_id}）`, '删除后数据不可恢复')
  if (!ok) return
  try {
    await networkApi.delete('aging-racks', row.rack_id)
    toast.success('删除成功')
    loadData()
  } catch(e) {
    console.error(e)
    toast.error(e.response?.data?.message || '删除失败')
  }
}

const onPagerChange = () => loadData()

// 监听分页变化
watch([page, pageSize], () => {
  loadData()
})

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
})
</script>
