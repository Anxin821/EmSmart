<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">🛡</span> 设备杀毒记录</h1>
      <CommonFilterBar :fields="filterFields" v-model:model-value="filters" @search="onSearch">
        <template #actions="scope">
          <el-button type="primary" size="default" @click="scope.search"><el-icon style="margin-right:6px;"><Search /></el-icon>搜索</el-button>
          <el-button size="default" @click="resetFilters"><el-icon style="margin-right:6px;"><RefreshRight /></el-icon>重置</el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" size="default" @click="openCreateModal"><el-icon style="margin-right:6px;"><Plus /></el-icon>新增记录</el-button>
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
        style="width:100%;"
        :height="'calc(100vh - 210px)'"
        empty-text="暂无数据"
        :header-cell-style="{fontWeight:600}"
      >

        <el-table-column label="设备ID" prop="device_id" min-width="160" align="center" show-overflow-tooltip>
          <template #default="s">
            <span class="fw-semibold" style="color:var(--c-text);">{{ s.row.device_id || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="产线" prop="production_line" min-width="90" align="center" />

        <el-table-column label="杀毒时间" min-width="170" align="center" show-overflow-tooltip>
          <template #default="s">{{ (s.row.antivirus_time || '').slice(0,16).replace('T',' ') || '-' }}</template>
        </el-table-column>

        <el-table-column label="下次杀毒" min-width="170" align="center" show-overflow-tooltip>
          <template #default="s">{{ (s.row.next_antivirus_time || '').slice(0,16).replace('T',' ') || '-' }}</template>
        </el-table-column>

        <el-table-column label="周期" prop="cycle" width="80" align="center" />

        <el-table-column label="状态" prop="status" min-width="100" align="center">
          <template #default="s">
            <span :class="'status-badge ' + statusClass(s.row)">{{ statusText(s.row) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作人" prop="operator" min-width="100" align="center" show-overflow-tooltip>
          <template #default="s">{{ s.row.operator || '-' }}</template>
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
            <template #image><div style="font-size:44px;">🛡</div></template>
          </el-empty>
        </template>
      </el-table>

      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact />
    </div>

    <!-- 新增/编辑 Modal -->
    <CommonModal
      v-model:visible="formModalVisible"
      :title="formMode === 'create' ? '新增杀毒记录' : '编辑杀毒记录'"
      width="680px"
      :ok-loading="saving"
      @ok="submitForm"
    >
      <el-form :model="form" label-width="96px" label-position="right">
        <div class="row g-3">
          <div class="col-6">
            <el-form-item label="设备ID" required>
              <el-input v-model="form.device_id" clearable placeholder="如：PC-8F7A" maxlength="50" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="产线" required>
              <el-select v-model="form.production_line" style="width:100%;">
                <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
                <el-option label="品质线" value="品质线" />
                <el-option label="维修线" value="维修线" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="杀毒时间" required>
              <el-date-picker
                v-model="form.antivirus_time"
                type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="选择日期时间"
                style="width:100%;"
              />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="杀毒周期">
              <el-select v-model="form.cycle" style="width:100%;">
                <el-option label="每天" value="每天" />
                <el-option label="每周" value="每周" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="操作人" required>
              <el-input v-model="form.operator" clearable placeholder="请输入操作人姓名" maxlength="32" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="备注">
              <el-input v-model="form.remark" clearable placeholder="可选" maxlength="200" />
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
import { antivirusApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useNotify } from '@/composables/useNotify'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()
const lines = ['1线','2线','3线','4线','5线','6线','7线','8线']
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const filters = ref({ keyword:'', line:'' })

// 用于取消请求的 AbortController
let abortController = null

// 表单弹窗
const formModalVisible = ref(false)
const formMode = ref('create')
const saving = ref(false)
const editRow = ref(null)
const form = ref({
  device_id: '', production_line: '1线', antivirus_time: '',
  cycle: '每天', operator: '', remark: ''
})

const filterFields = computed(() => [
  {
    type: 'input',
    key: 'keyword',
    label: '',
    placeholder: '设备ID / 操作人',
    minWidth: 260,
    showSearchIcon: true,
    autoSearch: false
  },
  { type: 'divider' },
  {
    type: 'select',
    key: 'line',
    label: '产线',
    minWidth: 140,
    options: [
      { label: '全部', value: '' },
      ...lines.map(l => ({ label: l, value: l })),
      { label: '品质线', value: '品质线' },
      { label: '维修线', value: '维修线' }
    ],
    autoSearch: true
  }
])

/**
 * 根据 next_antivirus_time 与当前时间对比，计算状态（与看板一致的口径）
 * 已杀毒：next_antivirus_time > now
 * 超时未杀毒：next_antivirus_time <= now
 * 待处理：next_antivirus_time 为空
 */
const statusText = (row) => {
  if (!row.next_antivirus_time) return '待处理'
  const now = new Date()
  const next = new Date(row.next_antivirus_time.replace('Z',''))
  return next > now ? '已杀毒' : '超时未杀毒'
}

const statusClass = (row) => {
  const t = statusText(row)
  if (t === '已杀毒')     return 'normal'
  if (t === '超时未杀毒') return 'fault'
  return 'warn'
}

const defaultForm = () => ({
  device_id: '', production_line: '1线', antivirus_time: '',
  cycle: '每天', operator: '', remark: ''
})

const resetFilters = () => {
  filters.value = { keyword:'', line:'' }
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
    // 实际后端 API：device_id / production_line 作为查询参数
    if (filters.value.keyword) params.device_id = filters.value.keyword
    if (filters.value.line)    params.production_line = filters.value.line
    
    const res = await antivirusApi.list(params)
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
  form.value = defaultForm()
  formModalVisible.value = true
}

const openEditModal = (row) => {
  formMode.value = 'edit'
  editRow.value = row
  form.value = {
    device_id: row.device_id ?? '',
    production_line: row.production_line ?? '1线',
    antivirus_time: row.antivirus_time ?? '',
    cycle: row.cycle ?? '每天',
    operator: row.operator ?? '',
    remark: row.remark ?? '',
  }
  formModalVisible.value = true
}

const submitForm = async () => {
  const d = form.value
  if (!d.device_id       || !d.device_id.trim())       { ElMessage.warning('请输入设备ID'); return }
  if (!d.production_line)                              { ElMessage.warning('请选择产线');    return }
  if (!d.antivirus_time)                               { ElMessage.warning('请选择杀毒时间');return }
  if (!d.operator      || !d.operator.trim())         { ElMessage.warning('请输入操作人');  return }
  saving.value = true
  try {
    const payload = { ...d }
    if (formMode.value === 'create') {
      await antivirusApi.create(payload)
      ElMessage.success('创建成功')
    } else {
      await antivirusApi.update(editRow.value.id, payload)
      ElMessage.success('修改成功')
    }
    formModalVisible.value = false
    loadData()
  } catch(e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || (formMode.value === 'create' ? '创建失败' : '修改失败'))
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const ok = await confirmDelete(`设备 ${row.device_id}`, '删除后数据不可恢复')
  if (!ok) return
  try {
    await antivirusApi.delete(row.id)
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
  console.log('Antivirus组件挂载')
  loadData()
})

onUnmounted(() => {
  console.log('Antivirus组件卸载，清理资源')
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  items.value = []
  form.value = defaultForm()
  filters.value = { keyword:'', line:'' }
})
</script>
