<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">📊</span>生产月报管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset()">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit"><el-button type="success" @click="showModal()"><el-icon><Plus /></el-icon>录入</el-button></template>
          <template v-if="userStore.isAdmin"><el-button type="warning" @click="handleGenerate"><el-icon><DataAnalysis /></el-icon>汇总月报</el-button></template>
        </template>
      </CommonFilterBar>
    </div>

    <div v-if="stats.total_output" class="stats-summary-row">
      <StatCard color="green"  icon="bi bi-check-circle-fill" :num="stats.total_output?.toLocaleString() || '0'" label="总产量" delta="汇总值" delta-type="up"    />
      <StatCard color="blue"   icon="bi bi-graph-up"         :num="stats.total_qualified?.toLocaleString() || '0'" label="总合格数" delta="汇总值" delta-type="muted" />
      <StatCard color="yellow" icon="bi bi-percent"          :num="(stats.yield_rate || 0) + '%'"                  label="总直通率" delta="直通率" delta-type="muted" />
    </div>

    <div class="page-content">
    <el-table ref="tableRef" :data="tableData" stripe border height="100%" style="width: 100%;" empty-text="暂无数据">

      <el-table-column prop="year" label="年" width="80" align="center" />

      <el-table-column prop="month" label="月" width="80" align="center" />

      <el-table-column prop="project" label="项目" min-width="200" align="center" show-overflow-tooltip />

      <el-table-column prop="monthly_total_output" label="月总产量" min-width="120" align="center" />

      <el-table-column prop="monthly_qualified_count" label="月合格数" min-width="120" align="center" />

      <el-table-column label="月直通率" width="110" align="center">
        <template #default="{ row }">
          <span class="badge" style="background: var(--ok-bg); color: var(--ok); padding: 2px 10px; border-radius: 12px;">
            {{ row.monthly_yield_rate }}%
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="recorder" label="录入人" min-width="90" align="center">
        <template #default="{ row }">
          {{ row.recorder || '-' }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <template v-if="userStore.canEdit">
            <el-button type="primary" link size="small" @click="showModal(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
          </template>
          <template v-if="userStore.isAdmin">
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
        :total="total"
        compact
      />
    </div>

    <CommonModal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑月报' : '录入月报'"
      width="720px"
      :ok-loading="saving"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-4">
          <label class="small form-label">年</label>
          <el-input-number v-model="form.year" :min="2000" :max="2100" controls-position="right" style="width:100%" />
        </div>
        <div class="col-4">
          <label class="small form-label">月</label>
          <el-input-number v-model="form.month" :min="1" :max="12" controls-position="right" style="width:100%" />
        </div>
        <div class="col-4">
          <label class="small form-label">项目</label>
          <el-select v-model="form.project" placeholder="请选择项目" style="width:100%">
            <el-option v-for="p in projects" :key="p.project_code" :label="p.project_name" :value="p.project_code" />
          </el-select>
        </div>
        <div class="col-4">
          <label class="small form-label">月总产量</label>
          <el-input-number v-model="form.monthly_total_output" :min="0" controls-position="right" style="width:100%" />
        </div>
        <div class="col-4">
          <label class="small form-label">月合格数</label>
          <el-input-number v-model="form.monthly_qualified_count" :min="0" controls-position="right" style="width:100%" />
        </div>
      </div>
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { productionApi, optionsApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight, Plus, DataAnalysis } from '@element-plus/icons-vue'
import { useNotify } from '@/composables/useNotify'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'
import StatCard         from '@/components/common/StatCard.vue'
const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()
const tableRef = ref(null)
const tableData = ref([])
const projects = ref([])
const filters = ref({ year: '', month: '', project: '' })
const stats = ref({})
const modalVisible = ref(false)
const editingId = ref(null)
const form = ref({})
const saving = ref(false)
// 分页
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const projectOptions = computed(() =>
  (projects.value || []).map(p => ({ label: p.project_name, value: p.project_code }))
)
// 年/月改为下拉：值是有限集合（年=近6年、月=1~12），下拉可杜绝非法输入、点选即筛选
// 选项降序排列：「全部」在首位，其后最大（最新）的年/月排在最上面
const currentYear = new Date().getFullYear()
const yearOptions = [
  { label: '全部', value: '' },
  ...Array.from({ length: 6 }, (_, i) => String(currentYear - i)).map(y => ({ label: y, value: y }))
]
const monthOptions = [
  { label: '全部', value: '' },
  ...Array.from({ length: 12 }, (_, i) => String(12 - i)).map(m => ({ label: m, value: m }))
]
const filterFields = computed(() => [
  { type: 'select', key: 'year', label: '年', placeholder: '全部', autoSearch: true, clearable: true, width: 90, options: yearOptions },
  { type: 'select', key: 'month', label: '月', placeholder: '全部', autoSearch: true, clearable: true, width: 90, options: monthOptions },
  { type: 'select', key: 'project', label: '项目', placeholder: '全部', autoSearch: true, clearable: true,
    options: [{ label: '全部', value: '' }, ...projectOptions.value] }
])
const defaultForm = () => ({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  project: 'A',
  monthly_total_output: 0,
  monthly_qualified_count: 0
})
const resetFilters = () => {
  filters.value = { year: '', month: '', project: '' }
  page.value = 1
  loadData()
}
// 搜索/筛选：先回到第 1 页再加载，避免停留在旧页码导致“筛选不生效”（筛选后结果变少，旧页码往往为空）
const onSearch = () => {
  page.value = 1
  loadData()
}
const loadData = async () => {
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.value.year) params.year = filters.value.year
    if (filters.value.month) params.month = filters.value.month
    if (filters.value.project) params.project = filters.value.project
    const res = await productionApi.monthly(params)
    tableData.value = res.data?.items || []
    stats.value = res.data?.extra || {}
    total.value = res.data?.total || 0
    // stats-summary-row 是 v-if，数据加载后才出现会改变 .page-content 高度；
    // 带 height=100% + fixed="right" 的表格不会自动重算，导致固定“操作”列错位/滑动，需手动 doLayout。
    await nextTick()
    tableRef.value?.doLayout()
  } catch (e) {
    console.error(e)
  }
}
const showModal = (row = null) => {
  if (row) {
    editingId.value = row.id
    form.value = { ...row }
  } else {
    editingId.value = null
    form.value = defaultForm()
  }
  modalVisible.value = true
}
const handleSave = async () => {
  saving.value = true
  try {
    if (editingId.value) {
      await productionApi.updateMonthly(editingId.value, form.value)
      toast.success('修改成功')
    } else {
      form.value.recorder = userStore.user?.username
      await productionApi.createMonthly(form.value)
      toast.success('创建成功')
    }
    modalVisible.value = false
    loadData()
  } catch (e) {
    toast.error(e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}
const handleDelete = async (id) => {
  const ok = await confirmDelete('月报记录', '删除后数据不可恢复')
  if (!ok) return
  try {
    await productionApi.deleteMonthly(id)
    toast.success('删除成功')
    loadData()
  } catch (e) {
    toast.error(e.response?.data?.message || '删除失败')
  }
}
const handleGenerate = async () => {
  const year = prompt('请输入年份：', new Date().getFullYear())
  const month = prompt('请输入月份：', new Date().getMonth() + 1)
  if (!year || !month) return
  try {
    await productionApi.generateMonthly(parseInt(year), parseInt(month))
    toast.success('生成成功')
    loadData()
  } catch (e) {
    toast.error('生成失败')
  }
}
watch([page, pageSize], () => {
  loadData()
})
// 窗口尺寸变化时重算表格布局，避免固定列与主体错位
const handleResize = () => tableRef.value?.doLayout()
onMounted(async () => {
  window.addEventListener('resize', handleResize)
  const projRes = await optionsApi.projects()
  projects.value = projRes.data || []
  loadData()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* .page 精确撑满父容器 .content（.content 已是 100vh - 顶栏56 - 内边距40）。
   默认的 height:100vh 会比容器高约 96px，底部被 .content 的 overflow:hidden 裁掉，
   并把表格末尾顶到 fixed 分页条后面 → 最后一行 / 横向滚动条看不全、需手动滑动表头。 */
.page { height: 100%; }
/* 底部为 position:fixed 的分页条预留空间；表格改用 height="100%" 填满剩余区域，
   末尾正好停在分页条上方，表头固定、仅数据区垂直滚动。 */
.page-content { padding-bottom: 48px; }
/* 收紧筛选栏与汇总卡、汇总卡与表格之间的间距 */
.stats-summary-row {
  margin-top: -18px;    /* 越负越靠近上方筛选栏 */
  padding-top: 8px;
  padding-bottom: 6px;  /* 汇总卡与下方表格的间距 */
}
</style>
