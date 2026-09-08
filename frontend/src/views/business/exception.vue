<template>
  <div class="page">
    <!-- 头部：标题 + 筛选栏 + 操作按钮 同行排列，与 Monthly.vue 保持一致 -->
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">🔧</span> 异常履历管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search"><el-icon><Search /></el-icon>搜索</el-button>
          <el-button @click="reset"><el-icon><RefreshRight /></el-icon>重置</el-button>
          <el-button type="success" @click="openCreate"><el-icon><Plus /></el-icon>新增异常</el-button>
        </template>
      </CommonFilterBar>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <StatCard centered color="blue" icon="bi bi-list-ul" :num="dashboard.total" label="总异常" />
      <StatCard centered color="red" icon="bi bi-clock" :num="dashboard.pending" label="待处理" clickable @click="setFilter('pending')" />
      <StatCard centered color="yellow" icon="bi bi-hourglass-split" :num="dashboard.processing" label="处理中" clickable @click="setFilter('processing')" />
      <StatCard centered color="green" icon="bi bi-check-circle" :num="dashboard.closed" label="已关闭" clickable @click="setFilter('closed')" />
    </div>

    <!-- 列表 -->
    <div class="page-content">
      <el-table v-loading="loading" :data="items" stripe border height="100%" style="width:100%" @row-click="openDetail" row-class-name="row-clickable">
        <el-table-column prop="exception_no" label="编号" width="140" />
        <el-table-column prop="occurred_time" label="发生时间" width="160">
          <template #default="{ row }">{{ formatTime(row.occurred_time) }}</template>
        </el-table-column>
        <el-table-column prop="exception_type" label="类型" width="100">
          <template #default="{ row }"><span class="status-badge">{{ row.exception_type }}</span></template>
        </el-table-column>
        <el-table-column prop="phenomenon_desc" label="现象描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="responsible_person" label="责任人" width="90" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <span :class="'status-badge ' + statusClass(row.status)">{{ statusLabel(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新" width="160">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="openEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="异常详情" width="720px" destroy-on-close class="exception-detail-dialog">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="编号">{{ detail.exception_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <span :class="'status-badge ' + statusClass(detail.status)">{{ statusLabel(detail.status) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="发生时间">{{ formatTime(detail.occurred_time) }}</el-descriptions-item>
        <el-descriptions-item label="发现人">{{ detail.discoverer || '-' }}</el-descriptions-item>
        <el-descriptions-item label="异常类型">{{ detail.exception_type }}</el-descriptions-item>
        <el-descriptions-item label="异常等级">
          <span :class="'status-badge ' + levelClass(detail.exception_level)">{{ levelLabel(detail.exception_level) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="原因分类">{{ detail.cause_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="责任人">{{ detail.responsible_person || '-' }}</el-descriptions-item>
        <el-descriptions-item label="是否停线">{{ detail.is_stopped ? '是' : '否' }}</el-descriptions-item>
        <el-descriptions-item label="停线时长">{{ detail.is_stopped ? (detail.stop_duration + ' 分钟') : '-' }}</el-descriptions-item>
        <el-descriptions-item label="解决时间">{{ formatTime(detail.resolved_time) }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ detail.created_by || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="现象描述">{{ detail.phenomenon_desc }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="临时措施">{{ detail.temporary_measure || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="根本原因分析">{{ detail.root_cause_analysis || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="长期对策">{{ detail.long_term_solution || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="验证结果">{{ detail.verification_result || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(detail.updated_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div style="text-align:right;">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="primary" @click="openEdit(detail); detailVisible = false">编辑</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新增/编辑弹窗 -->
    <CommonModal v-model:visible="modalVisible" :title="editingId ? '编辑异常' : '新增异常'" width="720px" :ok-loading="saving" @ok="handleSave">
      <el-form :model="form" label-width="90px">
        <div class="row g-3">
          <div class="col-6">
            <el-form-item label="发生时间" required>
              <el-date-picker v-model="form.occurred_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="发现人" required>
              <el-input v-model="form.discoverer" placeholder="发现人姓名" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="异常类型" required>
              <el-select v-model="form.exception_type" style="width:100%">
                <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="异常等级">
              <el-select v-model="form.exception_level" style="width:100%">
                <el-option label="严重" value="critical" />
                <el-option label="一般" value="major" />
                <el-option label="轻微" value="minor" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-12">
            <el-form-item label="现象描述" required>
              <el-input v-model="form.phenomenon_desc" type="textarea" :rows="2" placeholder="请描述异常现象" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="原因分类">
              <el-select v-model="form.cause_category" style="width:100%" clearable>
                <el-option v-for="c in causeOptions" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="责任人">
              <el-input v-model="form.responsible_person" placeholder="责任人" />
            </el-form-item>
          </div>
          <div class="col-12">
            <el-form-item label="临时措施">
              <el-input v-model="form.temporary_measure" type="textarea" :rows="2" placeholder="临时处理措施" />
            </el-form-item>
          </div>
          <div class="col-12">
            <el-form-item label="根本原因分析">
              <el-input v-model="form.root_cause_analysis" type="textarea" :rows="2" placeholder="根本原因分析" />
            </el-form-item>
          </div>
          <div class="col-12">
            <el-form-item label="长期对策">
              <el-input v-model="form.long_term_solution" type="textarea" :rows="2" placeholder="长期对策" />
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="状态">
              <!-- 状态下拉框变短：固定宽度 150px，不再 100% -->
              <el-select v-model="form.status" style="width: 150px;">
                <el-option label="待处理" value="pending" />
                <el-option label="处理中" value="processing" />
                <el-option label="已解决" value="resolved" />
                <el-option label="已关闭" value="closed" />
              </el-select>
            </el-form-item>
          </div>
          <div class="col-6">
            <el-form-item label="停线">
              <!-- 停线相关元素强制在一行，并且分钟不再被遮挡 -->
              <div style="display: flex; align-items: center; gap: 6px; width: 100%; flex-wrap: nowrap;">
                <el-switch v-model="form.is_stopped" :active-value="1" :inactive-value="0" style="flex-shrink: 0;" />
                <span style="color: #909399; font-size: 13px; white-space: nowrap; flex-shrink: 0;">停线时长</span>
                <el-input-number
                  v-model="form.stop_duration"
                  :min="0"
                  style="width: 80px; flex-shrink: 0;"
                  controls-position="right"
                />
                <span style="color: #909399; font-size: 13px; white-space: nowrap; flex-shrink: 0;">分钟</span>
              </div>
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存</el-button>
        </div>
      </template>
    </CommonModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { exceptionApi } from '@/api/exception'
import { useNotify } from '@/composables/useNotify'
import StatCard from '@/components/common/StatCard.vue'
import CommonFilterBar from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal from '@/components/common/CommonModal.vue'
import { Search, RefreshRight, Plus } from '@element-plus/icons-vue'

const { toast, confirmDelete } = useNotify()

// 格式化当前本地时间为 'YYYY-MM-DD HH:mm:ss'，供 el-date-picker value-format 对齐
const fmtNow = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filters = reactive({ keyword: '', type: '', status: '' })

const dashboard = ref({ total: 0, pending: 0, processing: 0, resolved: 0, closed: 0 })

const typeOptions = ['设备异常', '质量异常', '物料异常', '工艺异常', '系统异常', '人员操作', '其他']
const causeOptions = ['设备磨损', '参数偏移', '来料不良', '设计缺陷', '人员失误', '环境异常', '软件Bug', '其他']

const modalVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({})

// 详情弹窗状态
const detailVisible = ref(false)
const detail = ref(null)

const filterFields = computed(() => [
  { type: 'input', key: 'keyword', label: '', placeholder: '编号/现象/发现人', autoSearch: false, minWidth: 180 },
  { type: 'select', key: 'type', label: '类型', options: [{ label: '全部', value: '' }, ...typeOptions.map(t => ({ label: t, value: t }))], autoSearch: true },
  { type: 'select', key: 'status', label: '状态', options: [
    { label: '全部', value: '' },
    { label: '待处理', value: 'pending' },
    { label: '处理中', value: 'processing' },
    { label: '已解决', value: 'resolved' },
    { label: '已关闭', value: 'closed' }
  ], autoSearch: true }
])

const statusLabel = (s) => ({ pending: '待处理', processing: '处理中', resolved: '已解决', closed: '已关闭' }[s] || s)
const statusClass = (s) => {
  const map = { pending: 'warn', processing: 'info', resolved: 'normal', closed: 'normal' }
  return map[s] || 'muted'
}
const levelLabel = (l) => ({ critical: '严重', major: '一般', minor: '轻微' }[l] || l)
const levelClass = (l) => {
  const map = { critical: 'danger', major: 'warn', minor: 'info' }
  return map[l] || 'muted'
}
const formatTime = (v) => v ? new Date(v).toLocaleString('zh-CN') : '-'

const setFilter = (status) => {
  filters.status = status
  page.value = 1
  loadData()
}

// 点击表格行打开详情弹窗
const openDetail = (row) => {
  detail.value = { ...row }
  detailVisible.value = true
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.type) params.type = filters.type
    if (filters.status) params.status = filters.status
    const res = await exceptionApi.list(params)
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const loadDashboard = async () => {
  try {
    const res = await exceptionApi.dashboard()
    dashboard.value = res.data || {}
  } catch (e) { console.error(e) }
}

const onSearch = () => { page.value = 1; loadData() }
const resetFilters = () => {
  Object.assign(filters, { keyword: '', type: '', status: '' })
  page.value = 1
  loadData()
}

const openCreate = () => {
  editingId.value = null
  form.value = {
    occurred_time: fmtNow(),
    discoverer: '',
    exception_type: '',
    exception_level: 'major',
    phenomenon_desc: '',
    cause_category: '',
    temporary_measure: '',
    responsible_person: '',
    root_cause_analysis: '',
    long_term_solution: '',
    status: 'pending',
    is_stopped: 0,
    stop_duration: 0
  }
  modalVisible.value = true
}

const openEdit = (row) => {
  editingId.value = row.id
  form.value = { ...row }
  modalVisible.value = true
}

const handleSave = async () => {
  if (!form.value.occurred_time || !form.value.discoverer || !form.value.exception_type || !form.value.phenomenon_desc) {
    toast.warn('请填写必填字段')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await exceptionApi.update(editingId.value, form.value)
      toast.success('更新成功')
    } else {
      await exceptionApi.create(form.value)
      toast.success('创建成功')
    }
    modalVisible.value = false
    loadData()
    loadDashboard()
  } catch (e) { toast.error('保存失败') }
  finally { saving.value = false }
}

const handleDelete = async (row) => {
  const ok = await confirmDelete(`异常 ${row.exception_no}`, '删除后不可恢复')
  if (!ok) return
  try {
    await exceptionApi.delete(row.id)
    toast.success('删除成功')
    loadData()
    loadDashboard()
  } catch (e) { toast.error('删除失败') }
}

onMounted(() => {
  loadData()
  loadDashboard()
})
</script>

<style scoped>
/* 行可点击提示：鼠标变手型，hover 加深 */
:deep(.row-clickable) {
  cursor: pointer;
}
:deep(.row-clickable:hover) > td {
  background-color: var(--c-hover, #f5f7fa) !important;
}

/* 详情弹窗描述项标签列宽对齐 */
.exception-detail-dialog :deep(.el-descriptions__label) {
  width: 110px;
  color: var(--c-text-2, #64748b);
}
.exception-detail-dialog :deep(.el-descriptions__content) {
  color: var(--c-text, #1e293b);
}

/* 状态徽章 - 等级染色 */
.status-badge.danger { background: #fee2e2; color: #b91c1c; }
</style>