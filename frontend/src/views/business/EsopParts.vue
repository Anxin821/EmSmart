<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">📋</span> ESOP料号管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="loadData">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset(); loadData()">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" @click="showModal()">
              <el-icon><Plus /></el-icon>录入
            </el-button>
          </template>
        </template>
      </CommonFilterBar>
    </div>

    <div class="page-content">
    <el-table :data="tableData" stripe border :height="'calc(100vh - 340px)'" style="width: 100%;" empty-text="暂无数据">

        <el-table-column label="序号" width="70" align="center">
          <template #default="{ $index }">
            {{ (page - 1) * pageSize + $index + 1 }}
          </template>
        </el-table-column>

        <el-table-column prop="station_name" label="工位" width="100" align="center" />

        <el-table-column prop="process_name" label="工序" min-width="150" align="center" show-overflow-tooltip />

        <el-table-column prop="part_number" label="料号" width="120" align="center" show-overflow-tooltip />

        <el-table-column prop="file_name" label="ESOP文件" min-width="150" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.file_name || '-' }}
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
      :title="editingId ? '编辑料号' : '录入料号'"
      width="600px"
      :ok-loading="saving"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-6">
          <label class="small form-label">工位名称</label>
          <el-input v-model="form.station_name" placeholder="请输入工位名称" />
        </div>
        <div class="col-6">
          <label class="small form-label">工序名称</label>
          <el-input v-model="form.process_name" placeholder="请输入工序名称" />
        </div>
        <div class="col-6">
          <label class="small form-label">料号</label>
          <el-input v-model="form.part_number" placeholder="请输入料号" />
        </div>
        <div class="col-6">
          <label class="small form-label">ESOP文件名称</label>
          <el-input v-model="form.file_name" placeholder="请输入ESOP文件名称" />
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
import { ref, onMounted, watch } from 'vue'
import { esopApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight, Plus } from '@element-plus/icons-vue'
import { useNotify } from '@/composables/useNotify'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal from '@/components/common/CommonModal.vue'
const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = ref({ keyword: '', station_name: '', process_name: '', file_name: '' })
const modalVisible = ref(false)
const editingId = ref(null)
const form = ref({})
const saving = ref(false)
const filterFields = [
  { type: 'input', key: 'keyword', label: '', placeholder: '工位/工序/料号', autoSearch: false, clearable: true, width: 160 },
]
const defaultForm = () => ({
  station_name: '',
  process_name: '',
  part_number: '',
  file_name: '',
})
const resetFilters = () => {
  filters.value = { keyword: '', station_name: '', process_name: '', file_name: '' }
  page.value = 1
  loadData()
}
const loadData = async () => {
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.station_name) params.station_name = filters.value.station_name
    if (filters.value.process_name) params.process_name = filters.value.process_name
    if (filters.value.file_name) params.file_name = filters.value.file_name
    const res = await esopApi.list(params)
    tableData.value = res.data?.items || []
    total.value = res.data?.total || 0
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
      await esopApi.update(editingId.value, form.value)
      toast.success('修改成功')
    } else {
      await esopApi.create(form.value)
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
  const ok = await confirmDelete('ESOP料号', '删除后数据不可恢复')
  if (!ok) return
  try {
    await esopApi.delete(id)
    toast.success('删除成功')
    loadData()
  } catch (e) {
    toast.error(e.response?.data?.message || '删除失败')
  }
}
watch([page, pageSize], () => {
  loadData()
})
onMounted(() => {
  loadData()
})
</script>
