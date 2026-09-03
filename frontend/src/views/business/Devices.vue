<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 16px; flex-wrap: nowrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center;"><span class="emoji">🔍</span> AOI&AI 设备管理</h1>
      <CommonFilterBar :model-value="filters" :fields="filterFields" @update:model-value="val => Object.assign(filters, val)" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" @click="showModal()">
              <el-icon><Plus /></el-icon>新增设备
            </el-button>
          </template>
        </template>
      </CommonFilterBar>
    </div>
    <div class="page-content">
    <el-table v-loading="loading" :data="devices" stripe border :height="'calc(100vh - 210px)'" style="width: 100%;" empty-text="暂无数据">

      <el-table-column label="设备ID" prop="device_id" width="120" align="center" show-overflow-tooltip>
        <template #default="{ row }">
          <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px;">{{ row.device_id }}</code>
        </template>
      </el-table-column>

      <el-table-column prop="name" label="名称" min-width="200" align="center" show-overflow-tooltip>
        <template #default="{ row }"><span class="fw-semibold" style="color: var(--c-text);">{{ row.name }}</span></template>
      </el-table-column>

      <el-table-column prop="device_type" label="类型" width="80" align="center">
        <template #default="{ row }">
          <span class="badge" :style="{ background: row.device_type === 'AOI' ? 'var(--info-bg)' : 'var(--purple-bg)', color: row.device_type === 'AOI' ? 'var(--info)' : 'var(--purple)', padding: '2px 10px', borderRadius: '12px' }">{{ row.device_type }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="production_line" label="产线" width="80" align="center" />

      <el-table-column prop="location" label="位置" min-width="120" align="center" show-overflow-tooltip>
        <template #default="{ row }">{{ row.location || '-' }}</template>
      </el-table-column>

      <el-table-column prop="ip_address" label="IP" width="130" align="center">
        <template #default="{ row }">
          <span style="font-family: Consolas, 'Courier New', monospace; font-size: var(--fn-sm);">{{ row.ip_address || '-' }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <span :class="'status-badge ' + getStatusClass(cleanStatus(row.status))">{{ cleanStatus(row.status) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="responsible_person" label="负责人" min-width="90" align="center" show-overflow-tooltip>
        <template #default="{ row }">{{ row.responsible_person || '-' }}</template>
      </el-table-column>

      <el-table-column prop="install_date" label="安装日期" width="110" align="center">
        <template #default="{ row }">{{ row.install_date || '-' }}</template>
      </el-table-column>

      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <template v-if="userStore.canEdit">
            <el-button type="primary" link size="small" @click="showModal(row)">
              <el-icon><Edit /></el-icon>编辑
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
      />
    </div>
  </div>
  <!-- 模态框保持在PageLayout外部 -->
  <CommonModal
    :visible="crud.modalVisible"
    @update:visible="v => crud.modalVisible = v"
    :title="crud.isEdit() ? '编辑设备' : '新增设备'"
    width="640px"
    :ok-loading="crud.modalSaving"
    @ok="handleSave"
  >
    <div class="row g-3">
      <div class="col-6">
        <label class="small form-label">设备ID <span style="color: var(--err);">*</span></label>
        <el-input v-model="crud.form.device_id" placeholder="如 AOI-001" clearable />
      </div>
      <div class="col-6">
        <label class="small form-label">名称 <span style="color: var(--err);">*</span></label>
        <el-input v-model="crud.form.name" clearable />
      </div>
      <div class="col-6">
        <label class="small form-label">类型</label>
        <el-select v-model="crud.form.device_type" style="width: 100%;">
          <el-option label="AOI" value="AOI" />
          <el-option label="AI"  value="AI"  />
        </el-select>
      </div>
      <div class="col-6">
        <label class="small form-label">产线</label>
        <el-select v-model="crud.form.production_line" style="width: 100%;">
          <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
        </el-select>
      </div>
      <div class="col-6">
        <label class="small form-label">状态</label>
        <el-select v-model="crud.form.status" style="width: 100%;">
          <el-option label="正常"   value="正常" />
          <el-option label="故障"   value="故障" />
          <el-option label="保养中" value="保养中" />
        </el-select>
      </div>
      <div class="col-6">
        <label class="small form-label">负责人</label>
        <el-input v-model="crud.form.responsible_person" clearable placeholder="请输入负责人姓名" />
      </div>
      <div class="col-6">
        <label class="small form-label">IP地址</label>
        <el-input v-model="crud.form.ip_address" clearable placeholder="192.168.x.x" />
      </div>
      <div class="col-6">
        <label class="small form-label">安装日期</label>
        <el-date-picker v-model="crud.form.install_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%;" />
      </div>
      <div class="col-12">
        <label class="small form-label">位置</label>
        <el-input v-model="crud.form.location" clearable placeholder="车间位置描述" />
      </div>
    </div>
    <template #footer="f">
      <div class="cm-footer">
        <el-button @click="f.cancel">取消</el-button>
        <el-button type="primary" :loading="f.okLoading" @click="f.ok">保存</el-button>
      </div>
    </template>
  </CommonModal>
  <input type="file" ref="fileInput" accept=".xlsx,.xls" style="display:none" @change="handleFileChange">
</template>
<script setup>
import { computed, onUnmounted, watch } from 'vue'
import { devicesApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight, Plus } from '@element-plus/icons-vue'
// ========= 复用层引入（逻辑复用，减少样板代码） =========
import { useNotify }    from '@/composables/useNotify'
import { useCrudModal } from '@/composables/useCrudModal'
import { useCrudList }  from '@/composables/useCrudList'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'
const userStore = useUserStore()
const { toast } = useNotify()
const lines = ['1线', '2线', '3线', '4线', '5线', '6线', '7线', '8线']
const filterFields = [
  { type: 'input',  key: 'keyword', label: '',          placeholder: '设备ID / 名称 / IP / 负责人', autoSearch: false, clearable: true, width: 220 },
  { type: 'select', key: 'line',    label: '产线',      placeholder: '全部', autoSearch: true, clearable: true, width: 90,
    options: [{ label: '全部', value: '' }, ...lines.map(l => ({ label: l, value: l }))] },
  { type: 'select', key: 'status',  label: '状态',      placeholder: '全部', autoSearch: true, clearable: true, width: 100,
    options: [{ label: '全部', value: '' }, { label: '正常', value: '正常' }, { label: '故障', value: '故障' }, { label: '保养中', value: '保养中' }] },
  { type: 'select', key: 'type',    label: '类型',      placeholder: '全部', autoSearch: true, clearable: true, width: 90,
    options: [{ label: '全部', value: '' }, { label: 'AOI', value: 'AOI' }, { label: 'AI', value: 'AI' }] },
]
/* ====================== 业务纯函数（小而集中，方便 UT/复用） ====================== */
const cleanStatus = (s) => (s == null ? '正常' : String(s).replace(/^\s*\|*\s*/, '').replace(/\s*\|*\s*$/, '').trim() || '正常')
const getStatusClass = (s) => ({ '正常': 'normal', '故障': 'fault', '保养中': 'warn' }[s] || 'muted')
const defaultForm = () => ({
  device_id: '', name: '', device_type: 'AOI', production_line: '1线',
  location: '', ip_address: '', status: '正常', responsible_person: '', install_date: '',
})
/* ================ 列表 CRUD（useCrudList 统一封装了 filters/loading/list/total/loadData/delete/import/export） ================ */
const listAdapter = {
  list:   async ({ page, size, keyword, line, status, type }) => {
    const p = { page, page_size: size }
    if (keyword) p.keyword = keyword
    if (line)    p.production_line = line
    if (status)  p.status = status
    if (type)    p.device_type = type
    const res = await devicesApi.list(p)
    return { list: res.data?.items || [], total: res.data?.total || 0 }
  },
  delete: (id) => devicesApi.delete(id),
  import: (fd) => devicesApi.import(fd),
  export: (extra) => devicesApi.export(extra),
}
const {
  filters, list: devices, total, loading,
  fileRef: fileInput,
  resetFilters, loadData,
  handleDelete: del, triggerImport: handleImport, handleFileChange, handleExport: doExport,
  onPagerChange,
} = useCrudList(listAdapter, {
  defaultFilters: () => ({ keyword: '', line: '', status: '', type: '' }),
  pageSize: 20,
})
// 外层包装：点表格的删除按钮时，把设备名/ID传进去让确认弹窗更友好
const handleDelete = (row) => del(row, {
  idProp: 'id',
  labelProp: 'name',
  extraMsg: `设备ID ${row.device_id || ''} 将一并删除其所有关联数据`,
  successMsg: '设备已删除',
})
const handleExport = () => doExport()
// 搜索/筛选：先回到第 1 页再加载，避免停留在旧页码导致“筛选不生效”（筛选后结果变少，旧页码往往为空）
const onSearch = () => {
  filters.page = 1
  loadData()
}
/* ================ 新增 / 编辑弹窗（useCrudModal 统一封装 visible/editing/form/saving/showCreate/showEdit/close/submit） ================ */
const crud = useCrudModal(defaultForm)
const showModal = (dev = null) => (dev ? crud.showEdit(dev) : crud.showCreate())
const closeModal = () => crud.close()
const handleSave = () => crud.submit(
  async ({ form, editing, isEdit }) => {
    const payload = { ...form }
    payload.status = cleanStatus(payload.status)
    return isEdit
      ? await devicesApi.update(editing.item_id, payload)
      : await devicesApi.create(payload)
  },
  {
    validate: ({ form }) => (!form.device_id || !form.name) ? '请填写 设备ID 与 名称' : true,
    successMsg: ({ isEdit }) => isEdit ? '设备修改成功' : '设备新增成功',
    onSaved:    () => loadData(),
  }
)
const page      = computed({
  get: () => filters.page || 1,
  set: (v) => { filters.page = v }
})
const pageSize  = computed({
  get: () => filters.size || 20,
  set: (v) => { filters.size = v; filters.page = 1 }
})
const totalPages = computed(() => Math.ceil((total.value || 0) / (pageSize.value || 1)))

// 监听分页变化，自动加载数据
watch([page, pageSize], () => {
  loadData()
})
</script>

<style scoped>
/* Devices 页头部：标题 + 搜索框 + 筛选下拉 + 搜索/重置/新增 全部保持单行水平，不换行 */
.page-header :deep(.common-filter-bar) {
  flex: 0 1 auto;      /* 不主动伸展；空间不足时允许整体收缩 */
  min-width: 0;        /* 允许收缩到内容宽度以下，配合关键词框弹性伸缩 */
  flex-wrap: nowrap;   /* 关键：字段与按钮不换行，始终排在同一行 */
}
/* 关键词搜索框改为固定宽度（刚好容下占位符），外层 field 不再弹性拉伸，
   与产线/状态/类型下拉、操作按钮一起紧凑排在同一行 */
.page-header :deep(.common-filter-bar > .field:first-child) {
  flex: 0 0 auto;
}
</style>
