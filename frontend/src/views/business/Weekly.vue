<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">📈</span>生产周报管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset()">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit"><el-button type="success" @click="importModalVisible = true"><el-icon><Upload /></el-icon>批量导入</el-button></template>
          <template v-if="userStore.canEdit"><el-button type="success" @click="showModal()"><el-icon><Plus /></el-icon>录入</el-button></template>
        </template>
      </CommonFilterBar>
    </div>

    <div class="page-content">
    <el-table ref="tableRef" :data="tableData" stripe border height="100%" style="width: 100%;" empty-text="暂无数据">

      <el-table-column prop="year" label="年" width="80" align="center" />

      <el-table-column prop="week_number" label="周" width="80" align="center" />

      <el-table-column prop="production_line" label="产线" width="100" align="center" />

      <el-table-column prop="project" label="项目" min-width="200" align="center" show-overflow-tooltip />

      <el-table-column prop="total_output" label="总产量" min-width="110" align="center" />

      <el-table-column prop="qualified_count" label="合格数" min-width="110" align="center" />

      <el-table-column label="直通率" width="100" align="center">
        <template #default="{ row }">
          <span class="badge" style="background: var(--ok-bg); color: var(--ok); padding: 2px 10px; border-radius: 12px;">
            {{ row.yield_rate }}%
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

    <!-- 批量导入弹窗 -->
    <CommonModal
      v-model:visible="importModalVisible"
      title="批量导入检测数据"
      width="560px"
      ok-text="开始导入"
      :ok-loading="importing"
      @ok="handleImport"
    >
      <div class="mb-2">
        <p class="small text-muted mb-2">请上传 DetectionResult 格式的 .xlsx 文件，系统将自动按工站→产线、机型→项目的映射规则汇总为周报数据。</p>
        <el-upload
          ref="uploadRef"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="onImportFileChange"
          :on-remove="onImportFileRemove"
        >
          <div style="padding: 20px 0;">
            <el-icon style="font-size: 40px; color: var(--primary);"><UploadFilled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          </div>
          <template #tip>
            <div class="el-upload__tip">仅支持 .xlsx / .xls 文件</div>
          </template>
        </el-upload>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="primary" :loading="f.okLoading" :disabled="!importFile" @click="f.ok">开始导入</el-button>
        </div>
      </template>
    </CommonModal>
    <CommonModal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑周报' : '录入周报'"
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
          <label class="small form-label">周</label>
          <el-input-number v-model="form.week_number" :min="1" :max="53" controls-position="right" style="width:100%" />
        </div>
        <div class="col-4">
          <label class="small form-label">产线</label>
          <el-select v-model="form.production_line" placeholder="请选择产线" style="width:100%">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </div>
        <div class="col-4">
          <label class="small form-label">项目</label>
          <el-select v-model="form.project" placeholder="请选择项目" style="width:100%">
            <el-option v-for="p in projects" :key="p.project_code" :label="p.project_name" :value="p.project_code" />
          </el-select>
        </div>
        <div class="col-4">
          <label class="small form-label">总产量</label>
          <el-input-number v-model="form.total_output" :min="0" controls-position="right" style="width:100%" />
        </div>
        <div class="col-4">
          <label class="small form-label">合格数</label>
          <el-input-number v-model="form.qualified_count" :min="0" controls-position="right" style="width:100%" />
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
import { Search, Edit, Delete, UploadFilled, RefreshRight, Plus, Upload } from '@element-plus/icons-vue'
import { useNotify } from '@/composables/useNotify'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'
const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()
const tableRef = ref(null)
const tableData = ref([])
const lines = ['1线', '2线', '3线', '4线', '5线', '6线', '7线', '8线']
const projects = ref([])
const filters = ref({ year: '', week: '', line: '' })
const modalVisible = ref(false)
const editingId = ref(null)
const form = ref({})
const saving = ref(false)
// 批量导入
const importModalVisible = ref(false)
const importFile = ref(null)
const importing = ref(false)
const uploadRef = ref(null)
// 分页
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterFields = [
  { type: 'input', key: 'year', label: '年', placeholder: '请输入年份（数字）', autoSearch: false, clearable: true },
  { type: 'input', key: 'week', label: '周', placeholder: '请输入周数（数字）', autoSearch: false, clearable: true },
  { type: 'select', key: 'line', label: '产线', placeholder: '全部', autoSearch: false, clearable: true,
    options: lines.map(l => ({ label: l, value: l })) }
]
const defaultForm = () => ({
  year: new Date().getFullYear(),
  week_number: Math.ceil((new Date().getMonth() + 1) / 4),
  production_line: '1线',
  project: 'A',
  total_output: 0,
  qualified_count: 0
})
const resetFilters = () => {
  filters.value = { year: '', week: '', line: '' }
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
    if (filters.value.week) params.week = filters.value.week
    if (filters.value.line) params.production_line = filters.value.line
    const res = await productionApi.weekly(params)
    tableData.value = res.data?.items || []
    total.value = res.data?.total || 0
    // 带 height=100% + fixed="right" 的表格不会自动重算，数据变化后需 doLayout 避免固定“操作”列错位/滑动。
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
      await productionApi.updateWeekly(editingId.value, form.value)
      toast.success('修改成功')
    } else {
      form.value.recorder = userStore.user?.username
      await productionApi.createWeekly(form.value)
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
  const ok = await confirmDelete('周报记录', '删除后数据不可恢复')
  if (!ok) return
  try {
    await productionApi.deleteWeekly(id)
    toast.success('删除成功')
    loadData()
  } catch (e) {
    toast.error(e.response?.data?.message || '删除失败')
  }
}
const onImportFileChange = (file) => {
  importFile.value = file.raw
}
const onImportFileRemove = () => {
  importFile.value = null
}
const handleImport = async () => {
  if (!importFile.value) return
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const res = await productionApi.importWeeklyRaw(formData)
    importModalVisible.value = false
    importFile.value = null
    if (uploadRef.value) uploadRef.value.clearFiles()
    loadData()
    toast.success(res.message || '导入成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || e.response?.data?.message || '导入失败')
  } finally {
    importing.value = false
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
