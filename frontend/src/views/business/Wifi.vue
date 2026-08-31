<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><span class="emoji">📡</span> WiFi AP 管理</h1>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-secondary" @click="resetFilters"><span class="bi bi-funnel"></span>重置筛选</button>
        <template v-if="userStore.canEdit">
          <button class="btn btn-sm btn-outline-primary" @click="openCreateModal"><span class="bi bi-plus-lg"></span>新增AP</button>
        </template>
      </div>
    </div>

      <CommonFilterBar :fields="filterFields" v-model:model-value="filters" @search="loadData" @reset="onResetFromFilterBar">
        <template #actions="scope">
          <el-button type="primary" size="default" @click="scope.search"><el-icon style="margin-right:6px;"><Search /></el-icon>搜索</el-button>
          <el-button size="default" @click="resetFilters"><el-icon style="margin-right:6px;"><RefreshRight /></el-icon>重置</el-button>
        </template>
      </CommonFilterBar>

    <el-table v-loading="loading" :data="items" stripe border style="width:100%" empty-text="暂无数据" :header-cell-style="{fontWeight:600}">

        <el-table-column label="AP ID" prop="ap_id" min-width="120" align="center">
          <template #default="s">
            <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px;">{{ s.row.ap_id }}</code>
          </template>
        </el-table-column>

        <el-table-column label="SSID" prop="ssid" min-width="140" align="center" show-overflow-tooltip>
          <template #default="s"><span class="fw-semibold" style="color: var(--c-text);">{{ s.row.ssid }}</span></template>
        </el-table-column>

        <el-table-column label="产线" prop="production_line" min-width="90" align="center" />

        <el-table-column label="IP" prop="ip_address" min-width="130" align="center" show-overflow-tooltip>
          <template #default="s">
            <span style="font-family: Consolas, 'Courier New', monospace; font-size: var(--fn-sm);">{{ s.row.ip_address }}</span>
          </template>
        </el-table-column>

        <el-table-column label="位置" prop="location" min-width="140" align="center" show-overflow-tooltip>
          <template #default="s">{{ s.row.location || '-' }}</template>
        </el-table-column>

        <el-table-column label="信道" prop="channel" min-width="90" align="center" />

        <el-table-column label="已连接" prop="connected_devices" min-width="100" align="center">
          <template #default="s">{{ s.row.connected_devices || 0 }}</template>
        </el-table-column>

        <el-table-column label="状态" prop="status" min-width="100" align="center">
          <template #default="s">
            <span :class="'status-badge ' + statusClass(s.row.status)">{{ s.row.status }}</span>
          </template>
        </el-table-column>

        <el-table-column label="负责人" prop="responsible_person" min-width="110" align="center" show-overflow-tooltip>
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
            <template #image><div style="font-size:44px;">📡</div></template>
          </el-empty>
        </template>
      </el-table>

      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact @change="onPagerChange" />
    <!-- 新增/编辑 Modal -->
    <CommonModal
      v-model:visible="formModalVisible"
      :title="formMode === 'create' ? '新增AP' : '编辑AP'"
      width="640px"
      :ok-loading="saving"
      @ok="submitForm"
    >
      <el-form :model="form" label-width="84px" label-position="right">
        <div class="row g-3">
          <div class="col-6">
            <el-form-item label="AP ID" required>
              <el-input v-model="form.ap_id" clearable placeholder="如：AP-001" maxlength="32" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="SSID" required>
              <el-input v-model="form.ssid" clearable placeholder="WiFi 名称" maxlength="64" />
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
            <el-form-item label="IP地址">
              <el-input v-model="form.ip_address" clearable placeholder="192.168.x.x" maxlength="39" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="位置">
              <el-input v-model="form.location" clearable placeholder="如：C栋3楼东区" maxlength="64" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="信道">
              <el-input-number v-model="form.channel" :min="1" :max="233" style="width:100%;" controls-position="right" />
            </el-form-item>
          </div>
          <div class="col-6" v-if="formMode === 'edit'">
            <el-form-item label="已连接设备">
              <el-input-number v-model="form.connected_devices" :min="0" :max="1000" style="width:100%;" controls-position="right" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width:100%;">
                <el-option label="在线" value="在线" />
                <el-option label="离线" value="离线" />
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
        <el-button @click="f.cancel">取消</el-button>
        <el-button type="primary" :loading="f.okLoading" @click="f.ok">
          {{ formMode === 'create' ? '创建' : '保存修改' }}
        </el-button>
      </template>
    </CommonModal>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { networkApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight } from '@element-plus/icons-vue'
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
  ap_id: '', ssid: '', production_line: '1线', ip_address: '',
  location: '', channel: 6, connected_devices: 0, status: '在线', responsible_person: ''
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const filterFields = computed(() => [
  {
    type: 'input',
    key: 'keyword',
    label: '',
    placeholder: 'AP ID / SSID / IP / 负责人',
    minWidth: 260,
    showSearchIcon: true,
    autoSearch: false
  },
  { type: 'divider' },
  {
    type: 'select',
    key: 'line',
    label: '产线',
    minWidth: 130,
    options: [
      { label: '全部产线', value: '' },
      ...lines.map(l => ({ label: l, value: l }))
    ],
    autoSearch: true
  },
  {
    type: 'select',
    key: 'status',
    label: '状态',
    minWidth: 130,
    options: [
      { label: '全部状态', value: '' },
      { label: '在线', value: '在线' },
      { label: '离线', value: '离线' }
    ],
    autoSearch: true
  }
])

const statusClass = (s) => ({ '在线':'normal', '离线':'fault' }[s] || 'muted')

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
    
    const res = await networkApi.wifi(params)
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
    ap_id: '', ssid: '', production_line: '1线', ip_address: '',
    location: '', channel: 6, connected_devices: 0, status: '在线', responsible_person: ''
  }
  formModalVisible.value = true
}

const openEditModal = (row) => {
  formMode.value = 'edit'
  editRow.value = row
  form.value = {
    ap_id: row.ap_id ?? '',
    ssid: row.ssid ?? '',
    production_line: row.production_line ?? '1线',
    ip_address: row.ip_address ?? '',
    location: row.location ?? '',
    channel: typeof row.channel === 'number' ? row.channel : 6,
    connected_devices: typeof row.connected_devices === 'number' ? row.connected_devices : 0,
    status: row.status ?? '在线',
    responsible_person: row.responsible_person ?? '',
  }
  formModalVisible.value = true
}

const submitForm = async () => {
  const d = form.value
  if (!d.ap_id || !d.ap_id.trim()) { toast.warn('请输入 AP ID');  return }
  if (!d.ssid  || !d.ssid.trim())  { toast.warn('请输入 SSID');   return }
  if (!d.production_line)          { toast.warn('请选择产线');    return }
  saving.value = true
  try {
    if (formMode.value === 'create') {
      await networkApi.create('wifi-aps', d)
      toast.success('创建成功')
    } else {
      await networkApi.update('wifi-aps', String(editRow.value.id || editRow.value.ap_id), d)
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
  const ok = await confirmDelete(`AP ${row.ap_id}`, '删除后数据不可恢复')
  if (!ok) return
  try {
    await networkApi.delete('wifi-aps', String(row.id || row.ap_id))
    toast.success('删除成功')
    loadData()
  } catch(e) {
    console.error(e)
    toast.error(e.response?.data?.message || '删除失败')
  }
}

const onPagerChange = () => loadData()

onMounted(() => {
  console.log('Wifi组件挂载')
  loadData()
})

onUnmounted(() => {
  console.log('Wifi组件卸载，清理资源')
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  items.value = []
  form.value = {
    ap_id: '', ssid: '', production_line: '1线', ip_address: '',
    location: '', channel: 6, connected_devices: 0, status: '在线', responsible_person: ''
  }
  filters.value = { keyword:'', line:'', status:'' }
})
</script>
