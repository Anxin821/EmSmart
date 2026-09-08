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

    <!-- 紧凑看板：统计条（KPI+指标合并一行，可点击筛选）+ 两个分析面板 -->
    <div v-if="dashboard.total" class="exc-dash">
      <div class="exc-statbar">
        <div class="exc-stat clickable" :class="{ active: !filters.status && !filters.level && !filters.stopped }" @click="clearStatFilters">
          <span class="s-num s-blue">{{ dashboard.total }}</span>
          <span class="s-label">总异常</span>
        </div>
        <div class="exc-stat clickable" :class="{ active: filters.status === 'pending' }" @click="setStat('status', 'pending')">
          <span class="s-num s-red">{{ dashboard.pending }}</span>
          <span class="s-label">待处理</span>
        </div>
        <div class="exc-stat clickable" :class="{ active: filters.status === 'resolved' }" @click="setStat('status', 'resolved')">
          <span class="s-num s-green">{{ dashboard.resolved }}</span>
          <span class="s-label">已解决</span>
        </div>
        <div class="exc-divider"></div>
        <div class="exc-stat clickable" :class="{ active: filters.status === 'resolved' }" @click="setStat('status', 'resolved')">
          <span class="s-num s-green">{{ dashboard.resolution_rate ?? 0 }}<small>%</small></span>
          <span class="s-label">解决率</span>
        </div>
        <div class="exc-stat clickable" :class="{ active: filters.level === 'critical' }" @click="setStat('level', 'critical')">
          <span class="s-num s-red">{{ dashboard.by_level?.critical ?? 0 }}</span>
          <span class="s-label">严重</span>
        </div>
        <div class="exc-stat clickable" :class="{ active: filters.level === 'major' }" @click="setStat('level', 'major')">
          <span class="s-num s-orange">{{ dashboard.by_level?.major ?? 0 }}</span>
          <span class="s-label">一般</span>
        </div>
        <div class="exc-stat clickable" :class="{ active: filters.level === 'minor' }" @click="setStat('level', 'minor')">
          <span class="s-num s-blue2">{{ dashboard.by_level?.minor ?? 0 }}</span>
          <span class="s-label">轻微</span>
        </div>
        <div class="exc-stat clickable" :class="{ active: filters.stopped === '1' }" @click="setStat('stopped', '1')">
          <span class="s-num s-purple">{{ dashboard.stopped ?? 0 }}</span>
          <span class="s-label">停线</span>
        </div>
      </div>

      <div class="exc-panel-grid">
        <div class="exc-panel">
          <div class="exc-panel-head">
            <span class="exc-panel-title"><span class="bi bi-pie-chart-fill"></span>异常类型分布</span>
            <span class="exc-panel-hint">点击行按类型筛选</span>
          </div>
          <div class="exc-types-body">
            <div
              v-for="t in (dashboard.by_type || [])" :key="t.type"
              class="exc-type-row" @click="filterByType(t.type)"
              :class="{ active: filters.type === t.type }"
            >
              <span class="exc-type-name">{{ t.type }}</span>
              <div class="exc-type-bar">
                <div class="seg seg-done" :style="{ width: typePct(t, 'resolved') + '%' }"></div>
                <div class="seg seg-pend" :style="{ width: typePct(t, 'pending') + '%' }"></div>
              </div>
              <span class="exc-type-count">
                <b>{{ t.total }}</b>
                <em v-if="t.pending" class="pend-tag">{{ t.pending }}</em>
              </span>
            </div>
          </div>
        </div>

        <div class="exc-panel">
          <div class="exc-panel-head">
            <span class="exc-panel-title"><span class="bi bi-graph-up-arrow"></span>近14天趋势</span>
            <span class="exc-legend"><i class="lg-dot lg-new"></i>新增<i class="lg-dot lg-done"></i>解决</span>
          </div>
          <div class="exc-trend-body">
            <div v-for="d in (dashboard.trend || [])" :key="d.date" class="exc-trend-col" :title="`${d.date} 新增${d.new} / 解决${d.resolved}`">
              <div class="exc-trend-bars">
                <div class="tbar tbar-new" :style="{ height: trendH(d.new) }"></div>
                <div class="tbar tbar-done" :style="{ height: trendH(d.resolved) }"></div>
              </div>
              <span class="exc-trend-label">{{ d.date.slice(3) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 无数据时的占位统计条（保持布局稳定） -->
    <div v-else class="exc-dash">
      <div class="exc-statbar">
        <div class="exc-stat"><span class="s-num s-blue">0</span><span class="s-label">总异常</span></div>
        <div class="exc-stat"><span class="s-num s-red">0</span><span class="s-label">待处理</span></div>
        <div class="exc-stat"><span class="s-num s-green">0</span><span class="s-label">已解决</span></div>
        <div class="exc-divider"></div>
        <div class="exc-stat"><span class="s-num s-green">0<small>%</small></span><span class="s-label">解决率</span></div>
        <div class="exc-stat"><span class="s-num s-red">0</span><span class="s-label">严重</span></div>
        <div class="exc-stat"><span class="s-num s-orange">0</span><span class="s-label">一般</span></div>
        <div class="exc-stat"><span class="s-num s-blue2">0</span><span class="s-label">轻微</span></div>
        <div class="exc-stat"><span class="s-num s-purple">0</span><span class="s-label">停线</span></div>
      </div>
    </div>

    <!-- 列表：表格区域 flex 撑满剩余空间，表头固定、表体内部滚动；分页条常驻底部 -->
    <div class="page-content exc-list">
      <div class="table-wrap">
        <el-table v-loading="loading" :data="items" stripe border height="100%" style="width:100%" @row-click="openDetail" row-class-name="row-clickable">
          <el-table-column prop="exception_no" label="编号" width="150" />
          <el-table-column prop="occurred_time" label="发生时间" width="155">
            <template #default="{ row }">{{ formatTime(row.occurred_time) }}</template>
          </el-table-column>
          <el-table-column prop="exception_type" label="类型" width="95">
            <template #default="{ row }"><span class="status-badge">{{ row.exception_type }}</span></template>
          </el-table-column>
          <el-table-column prop="phenomenon_desc" label="现象描述" min-width="220" show-overflow-tooltip />
          <el-table-column prop="responsible_person" label="责任人" width="85" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <span :class="'status-badge ' + statusClass(row.status)">{{ statusLabel(row.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="155">
            <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click.stop="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="异常详情" width="720px" destroy-on-close :close-on-click-modal="false" class="exception-detail-dialog">
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
        <el-descriptions-item label="停线情况">
          <span :class="'status-badge ' + (detail.is_stopped ? 'danger' : 'normal')">
            {{ detail.is_stopped ? '是，停线 ' + detail.stop_duration + ' 分钟' : '否' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">{{ detail.created_by || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="现象描述">{{ detail.phenomenon_desc }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="临时措施">{{ detail.temporary_measure || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="根本原因分析">{{ detail.root_cause_analysis || '-' }}</el-descriptions-item>
        <el-descriptions-item :span="2" label="长期对策">{{ detail.long_term_solution || '-' }}</el-descriptions-item>
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
    <CommonModal v-model:visible="modalVisible" :title="editingId ? '编辑异常' : '新增异常'" width="720px" :ok-loading="saving" :close-on-click-modal="false" @ok="handleSave">
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
              <!-- 默认「待处理」，新增/编辑均可选择 -->
              <el-select v-model="form.status" style="width: 150px;">
                <el-option label="待处理" value="pending" />
                <el-option label="已解决" value="resolved" />
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
import { ref, computed, onMounted } from 'vue'
import { exceptionApi } from '@/api/exception'
import { useNotify } from '@/composables/useNotify'
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
const filters = ref({ keyword: '', type: '', status: '', level: '', stopped: '' })

const dashboard = ref({ total: 0, pending: 0, resolved: 0, resolution_rate: 0, by_level: {}, stopped: 0, by_type: [], trend: [] })

const typeOptions = ['设备异常', '质量异常', '物料异常', '工艺异常', '系统异常', '网络异常', '人员操作', '其他']
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
    { label: '已解决', value: 'resolved' }
  ], autoSearch: true }
])

// 两态闭环：未解决（含历史“处理中”）显示待处理，已解决（含历史“已关闭”）显示已解决
const statusLabel = (s) => (['resolved', 'closed'].includes(s) ? '已解决' : '待处理')
const statusClass = (s) => (['resolved', 'closed'].includes(s) ? 'normal' : 'warn')
const levelLabel = (l) => ({ critical: '严重', major: '一般', minor: '轻微' }[l] || l)
const levelClass = (l) => {
  const map = { critical: 'danger', major: 'warn', minor: 'info' }
  return map[l] || 'muted'
}
const formatTime = (v) => v ? new Date(v).toLocaleString('zh-CN') : '-'

// 统计条点击：按维度筛选（同一项再点一次取消）
// kind: status(pending/resolved) / level(critical/major/minor) / stopped(1)
const setStat = (kind, val) => {
  filters.value[kind] = filters.value[kind] === val ? '' : val
  page.value = 1
  loadData()
}

// 点击「总异常」：清除所有看板维度筛选
const clearStatFilters = () => {
  filters.value.status = ''
  filters.value.level = ''
  filters.value.stopped = ''
  page.value = 1
  loadData()
}

// 点击类型分布行 → 按该类型筛选（再点一次取消）
const filterByType = (type) => {
  filters.value.type = filters.value.type === type ? '' : type
  page.value = 1
  loadData()
}

// 类型分布条：条长按该类型数量占“最大类型”的比例缩放，段内再按 已解决/待处理 拆分
const typePct = (t, key) => {
  const max = Math.max(1, ...(dashboard.value.by_type || []).map(x => x.total))
  return Math.round((t[key] / max) * 100)
}

// 趋势柱高度：按 14 天内最大值归一到 72px，最小 2px 保留可见
const trendH = (n) => {
  const max = Math.max(1, ...(dashboard.value.trend || []).map(d => Math.max(d.new, d.resolved)))
  return Math.max(2, Math.round((n / max) * 72)) + 'px'
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
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.type) params.type = filters.value.type
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.level) params.level = filters.value.level
    if (filters.value.stopped) params.stopped = filters.value.stopped
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
  filters.value = { keyword: '', type: '', status: '', level: '', stopped: '' }
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
/* ===== 页面纵向布局：看板固定高度不压缩，表格区吃掉剩余空间 ===== */
.exc-dash {
  flex-shrink: 0;
  padding: 0 var(--gap-block);
  margin-bottom: 8px;
}
/* 列表区：flex 列布局，页面本身不滚动，由表体内部滚动 → 表头常驻 */
.exc-list {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-top: 0;
}
.exc-list .table-wrap {
  flex: 1;
  min-height: 0;
}
.exc-list :deep(.common-pagination) {
  flex-shrink: 0;
  padding: 8px 0 4px;
}

/* ===== 紧凑统计条：8 个指标一行排开，替代大卡片节省纵向空间 ===== */
.exc-statbar {
  display: flex;
  align-items: stretch;
  gap: 4px;
  background: var(--c-card, #fff);
  border: 1px solid var(--c-divider, #e2e8f0);
  border-radius: 10px;
  box-shadow: var(--shadow-card, 0 2px 8px rgba(15,23,42,.04));
  padding: 6px 10px;
  margin-bottom: 10px;
  overflow-x: auto;
}
.exc-stat {
  flex: 1;
  min-width: 74px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  padding: 4px 6px;
  border-radius: 8px;
}
.exc-stat.clickable { cursor: pointer; transition: background .15s, box-shadow .15s; }
.exc-stat.clickable:hover { background: var(--c-hover, #f1f5f9); }
/* 点击筛选后的选中态：浅蓝底 + 主色描边 */
.exc-stat.clickable.active {
  background: rgba(44, 92, 232, .09);
  box-shadow: inset 0 0 0 1px var(--primary, #2c5ce8);
}
.s-num { font-size: 22px; font-weight: 700; line-height: 1.2; }
.s-num small { font-size: 12px; font-weight: 600; margin-left: 1px; }
.s-label { font-size: 12px; color: var(--c-text-mute, #94a3b8); white-space: nowrap; }
.s-blue { color: #2563eb; } .s-red { color: #dc2626; } .s-green { color: #16a34a; }
.s-orange { color: #d97706; } .s-blue2 { color: #0891b2; } .s-purple { color: #7c3aed; }
.exc-divider { width: 1px; background: var(--c-divider, #e2e8f0); margin: 4px 6px; flex: 0 0 1px; }

/* ===== 分析面板 ===== */
.exc-panel-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 10px;
}
@media (max-width: 900px) { .exc-panel-grid { grid-template-columns: 1fr; } }
.exc-panel {
  background: var(--c-card, #fff);
  border: 1px solid var(--c-divider, #e2e8f0);
  border-radius: 10px;
  box-shadow: var(--shadow-card, 0 2px 8px rgba(15,23,42,.04));
  padding: 10px 14px;
}
.exc-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.exc-panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text, #1e293b);
  display: flex;
  align-items: center;
  gap: 6px;
}
.exc-panel-title .bi { color: var(--primary, #2c5ce8); }
.exc-panel-hint { font-size: 11px; color: var(--c-text-mute, #94a3b8); }

/* 类型分布 */
.exc-types-body { display: flex; flex-direction: column; gap: 5px; max-height: 172px; overflow-y: auto; }
.exc-type-row {
  display: grid;
  grid-template-columns: 78px 1fr 52px;
  align-items: center;
  gap: 10px;
  padding: 2px 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background .15s;
}
.exc-type-row:hover { background: var(--c-hover, #f1f5f9); }
.exc-type-row.active { background: rgba(44,92,232,.08); }
.exc-type-name {
  font-size: 12.5px;
  color: var(--c-text, #1e293b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.exc-type-bar {
  display: flex;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--c-fill, #f1f5f9);
}
.exc-type-bar .seg { height: 100%; transition: width .3s; }
.exc-type-bar .seg-done { background: linear-gradient(90deg, #22c55e, #16a34a); }
.exc-type-bar .seg-pend { background: linear-gradient(90deg, #f87171, #ef4444); }
.exc-type-count { display: flex; align-items: center; justify-content: flex-end; gap: 6px; font-size: 12.5px; }
.exc-type-count b { color: var(--c-text, #1e293b); }
.pend-tag {
  font-style: normal;
  font-size: 10px;
  color: #dc2626;
  background: #fee2e2;
  min-width: 18px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  padding: 0 5px;
  border-radius: 8px;
  white-space: nowrap;
}

/* 14天趋势（压缩高度） */
.exc-legend { font-size: 11px; color: var(--c-text-mute, #94a3b8); display: flex; align-items: center; gap: 4px; }
.lg-dot { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-left: 6px; }
.lg-new { background: #60a5fa; }
.lg-done { background: #34d399; }
.exc-trend-body {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 104px;
  padding-top: 4px;
}
.exc-trend-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: 3px;
  min-width: 0;
}
.exc-trend-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 78px;
}
.tbar { width: 7px; border-radius: 3px 3px 0 0; min-height: 2px; transition: height .3s; }
.tbar-new { background: #60a5fa; }
.tbar-done { background: #34d399; }
.exc-trend-label { font-size: 10px; color: var(--c-text-mute, #94a3b8); white-space: nowrap; transform: scale(.9); }

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