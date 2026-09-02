<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;"><span class="emoji">🖥</span>服务器管理</h1>
      <CommonFilterBar v-model="filters" :fields="filterFields" @search="onSearch">
        <template #actions="{ search, reset }">
          <el-button type="primary" @click="search">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="reset(); loadData()">
            <el-icon><RefreshRight /></el-icon>重置
          </el-button>
          <template v-if="userStore.canEdit">
            <el-button type="success" @click="showModal()"><el-icon><Plus /></el-icon>新增服务器</el-button>
          </template>
          <template v-if="userStore.isAdmin && userStore.canEdit">
            <el-button type="warning" @click="checkAll"><el-icon><Monitor /></el-icon>心跳检测</el-button>
          </template>
        </template>
      </CommonFilterBar>
    </div>

    <div class="page-content">
    <el-table ref="tableRef" v-loading="loading" :data="items" stripe border height="100%" style="width: 100%;" empty-text="暂无数据">

      <el-table-column label="服务器ID" prop="server_id" width="120" align="center" show-overflow-tooltip>
        <template #default="{ row }">
          <code style="background: var(--primary-50); padding: 1px 6px; border-radius: 4px;">{{ row.server_id }}</code>
        </template>
      </el-table-column>

      <el-table-column prop="name" label="名称" min-width="150" align="center" show-overflow-tooltip>
        <template #default="{ row }"><span class="fw-semibold" style="color: var(--c-text);">{{ row.name }}</span></template>
      </el-table-column>

      <el-table-column prop="production_line" label="产线" width="80" align="center" />

      <el-table-column prop="rack_location" label="机架" min-width="110" align="center" show-overflow-tooltip>
        <template #default="{ row }">{{ row.rack_location || '-' }}</template>
      </el-table-column>

      <el-table-column prop="ip_address" label="IP" width="130" align="center">
        <template #default="{ row }">
          <span style="font-family: Consolas, 'Courier New', monospace; font-size: var(--fn-sm);">{{ row.ip_address }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="os" label="系统" width="90" align="center" show-overflow-tooltip>
        <template #default="{ row }">{{ row.os || '-' }}</template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <span :class="'status-badge ' + statusClass(row.status)">{{ row.status }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="cpu_usage" label="CPU" width="80" align="center">
        <template #default="{ row }">{{ row.cpu_usage || 0 }}%</template>
      </el-table-column>

      <el-table-column prop="memory_usage" label="内存" width="80" align="center">
        <template #default="{ row }">{{ row.memory_usage || 0 }}%</template>
      </el-table-column>

      <el-table-column prop="responsible_person" label="负责人" min-width="90" align="center" show-overflow-tooltip>
        <template #default="{ row }">{{ row.responsible_person || '-' }}</template>
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
        @change="onPagerChange"
      />
    </div>

    <CommonModal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑服务器' : '新增服务器'"
      width="640px"
      :ok-loading="saving"
      @ok="handleSave"
    >
      <div class="row g-3">
        <div class="col-6">
          <label class="small form-label">服务器ID</label>
          <el-input v-model="form.server_id" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">名称</label>
          <el-input v-model="form.name" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">产线</label>
          <el-select v-model="form.production_line" placeholder="请选择产线" style="width:100%">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small form-label">机架位置</label>
          <el-input v-model="form.rack_location" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">IP地址</label>
          <el-input v-model="form.ip_address" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">操作系统</label>
          <el-input v-model="form.os" clearable />
        </div>
        <div class="col-6">
          <label class="small form-label">状态</label>
          <el-select v-model="form.status" placeholder="请选择状态" style="width:100%">
            <el-option label="在线" value="在线" />
            <el-option label="离线" value="离线" />
            <el-option label="维护" value="维护" />
          </el-select>
        </div>
        <div class="col-6">
          <label class="small form-label">负责人</label>
          <el-input v-model="form.responsible_person" clearable />
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { networkApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, Edit, Delete, RefreshRight, Plus, Monitor } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageLayout       from '@/components/common/PageLayout.vue'
import CommonFilterBar  from '@/components/common/CommonFilterBar.vue'
import CommonPagination from '@/components/common/CommonPagination.vue'
import CommonModal      from '@/components/common/CommonModal.vue'
const userStore = useUserStore()
const tableRef = ref(null)
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const filters = ref({ keyword: '', line: '', status: '' })
const lines = ['1线', '2线', '3线', '4线', '5线', '6线', '7线', '8线']
const modalVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({})
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const filterFields = [
  { type: 'input', key: 'keyword', label: '', placeholder: '服务器ID / 名称 / IP / 负责人', autoSearch: false, clearable: true, minWidth: 260 },
  { type: 'select', key: 'line', label: '产线', placeholder: '全部产线', autoSearch: true, clearable: true,
    options: [{ label: '全部产线', value: '' }, ...lines.map(l => ({ label: l, value: l }))] },
  { type: 'select', key: 'status', label: '状态', placeholder: '全部状态', autoSearch: true, clearable: true,
    options: [
      { label: '全部状态', value: '' },
      { label: '在线', value: '在线' },
      { label: '离线', value: '离线' },
      { label: '维护', value: '维护' }
    ] }
]
const statusClass = (s) => ({ '在线': 'normal', '离线': 'fault', '维护': 'warn' }[s] || 'muted')
const defaultForm = () => ({
  server_id: '', name: '', production_line: '1线', rack_location: '',
  ip_address: '', os: '', status: '在线', responsible_person: ''
})
const resetFilters = () => {
  filters.value = { keyword: '', line: '', status: '' }
  page.value = 1
  loadData()
}
// 搜索/筛选：先回到第 1 页再加载，避免停留在旧页码导致“筛选不生效”（筛选后结果变少，旧页码往往为空）
const onSearch = () => {
  page.value = 1
  loadData()
}

const showModal = (row = null) => {
  if (row) {
    editingId.value = row.server_id
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
      await networkApi.update('servers', editingId.value, form.value)
      ElMessage.success('服务器修改成功')
    } else {
      await networkApi.create('servers', form.value)
      ElMessage.success('服务器新增成功')
    }
    modalVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定删除该服务器？此操作不可撤销。',
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning', center: true }
    )
    await networkApi.delete('servers', id)
    ElMessage.success('服务器已删除')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
const checkAll = async () => {
  try {
    await networkApi.checkAll()
    ElMessage.success('检测完成')
    loadData()
  } catch (e) {
    ElMessage.error('检测失败')
  }
}
const onPagerChange = () => loadData()

// 窗口尺寸变化时重算表格布局，避免固定列与主体错位
const handleResize = () => tableRef.value?.doLayout()


// 清理定时器和异步操作
let abortController = null

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
    
    const res = await networkApi.servers(params)
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
    // 带 height=100% + fixed="right" 的表格不会自动重算，数据变化后需 doLayout 避免固定“操作”列错位/滑动。
    await nextTick()
    tableRef.value?.doLayout()
  }
}

onMounted(() => {
  console.log('Servers组件挂载')
  window.addEventListener('resize', handleResize)
  loadData()
})

onUnmounted(() => {
  console.log('Servers组件卸载，清理资源')
  window.removeEventListener('resize', handleResize)
  // 取消正在进行的请求
  if (abortController) {
    abortController.abort()
  }
  
  // 清理引用
  if (items.value) items.value = []
  if (form.value) form.value = {}
  if (filters.value) filters.value = {}
})
</script>

<style scoped>
/* .page 精确撑满父容器 .content（.content 已是 100vh - 顶栏56 - 内边距40）。
   默认的 height:100vh 会比容器高约 96px，底部被 .content 的 overflow:hidden 裁掉，
   并把表格末尾顶到 fixed 分页条后面 → 最后一行 / 横向滚动条看不全、需手动滑动。 */
.page { height: 100%; }

/* 底部为 position:fixed 的分页条预留空间；表格改用 height="100%" 填满剩余区域，
   末尾正好停在分页条上方，不再被遮挡。 */
.page-content { padding-bottom: 48px; }
</style>
