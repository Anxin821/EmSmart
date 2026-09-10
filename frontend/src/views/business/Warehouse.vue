<template>
  <div class="page">
    <div class="page-header" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h1 class="page-title" style="margin: 0; white-space: nowrap; display: flex; align-items: center; font-size: 16px;">
        <span class="emoji">📦</span> 库房管理
      </h1>

      <!-- 搜索框：名称 / 型号 / 借用人 / 领用人，兼容扫码枪输入 -->
      <el-input
        v-model="keyword"
        placeholder="名称 / 型号 / 借用人 / 领用人（支持扫码）"
        clearable
        style="width: 300px;"
        @keyup.enter="onSearch"
        @clear="onSearch"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="onSearch"><el-icon style="margin-right:4px;"><Search /></el-icon>搜索</el-button>
      <el-button @click="onReset"><el-icon style="margin-right:4px;"><RefreshRight /></el-icon>重置</el-button>

      <!-- 类型切换 -->
      <el-radio-group v-model="typeFilter" @change="onSearch">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="治具">🔧 治具</el-radio-button>
        <el-radio-button value="耗材">🧴 耗材</el-radio-button>
      </el-radio-group>

      <template v-if="userStore.canEdit">
        <el-button type="success" @click="openEdit(null)"><el-icon style="margin-right:4px;"><Plus /></el-icon>新增物品</el-button>
        <el-button type="warning" @click="openImport"><el-icon style="margin-right:4px;"><Upload /></el-icon>批量导入</el-button>
      </template>
    </div>

    <div class="page-content wh-content">
      <!-- 统计看板 -->
      <div class="wh-stats">
        <div class="wh-stat clickable" :class="{ active: stockStatusFilter === '' && !lowStockOnly }" @click="filterByStatus('')">
          <div class="wh-stat-num">{{ stats.total }}</div>
          <div class="wh-stat-label">总物品</div>
        </div>
        <div class="wh-stat clickable" :class="{ active: stockStatusFilter === 'in_stock' }" @click="filterByStatus('in_stock')">
          <div class="wh-stat-num ok">{{ stats.in_stock }}</div>
          <div class="wh-stat-label">在库</div>
        </div>
        <div class="wh-stat clickable" :class="{ active: stockStatusFilter === 'borrowed' }" @click="filterByStatus('borrowed')">
          <div class="wh-stat-num warn">{{ stats.borrowed_out }}</div>
          <div class="wh-stat-label">借出 / 领用</div>
        </div>
        <div class="wh-stat clickable" :class="{ active: lowStockOnly }" @click="toggleLowStock">
          <div class="wh-stat-num danger">{{ stats.low_stock }}</div>
          <div class="wh-stat-label">低于预警 <el-icon style="vertical-align:-2px;"><ArrowDown /></el-icon></div>
        </div>
      </div>

      <!-- 低库存预警条 -->
      <div v-if="lowItems.length" class="wh-warn-bar">
        <span class="wh-warn-title"><span class="bi bi-exclamation-triangle-fill"></span> 低库存预警：</span>
        <div class="wh-warn-items">
          <span v-for="it in lowItems" :key="it.id" class="wh-warn-chip">
            {{ it.name }}
            <b>{{ it.stock_qty }}</b>/{{ it.warn_qty }}{{ it.unit }}
            <el-button v-if="userStore.canEdit" type="danger" size="small" plain @click.stop="openRestock(it)">补货</el-button>
          </span>
        </div>
      </div>

      <!-- 物品列表 -->
      <el-table
        :data="items"
        v-loading="loading"
        stripe
        border
        :height="'calc(100vh - 360px)'"
        style="width: 100%"
        empty-text="暂无数据"
        :header-cell-style="{ fontWeight: 600, textAlign: 'center' }"
        @row-click="openDetail"
      >
        <el-table-column label="物品名称" min-width="180" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="wh-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="型号/编号" prop="model" min-width="130" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.model" style="font-family: Consolas, monospace;">{{ row.model }}</span>
            <span v-else style="color: var(--c-text-mute);">-</span>
          </template>
        </el-table-column>

        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.part_type === '治具' ? 'primary' : 'success'" size="small" effect="light">
              {{ row.part_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="数量" width="120" align="center">
          <template #default="{ row }">
            <b :style="{ color: row.status === '缺货' ? '#DC2626' : 'var(--c-text)' }">{{ row.qty_text }}</b>
          </template>
        </el-table-column>

        <el-table-column label="货位" prop="location" width="110" align="center">
          <template #default="{ row }">{{ row.location || '-' }}</template>
        </el-table-column>

        <el-table-column label="状态" min-width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="230" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="userStore.canEdit">
              <!-- 治具：在库可借；部分借出时仍有余量可继续借、也可归还；全部借出只能归还 -->
              <el-button v-if="row.part_type === '治具' && (row.status === '在库' || row.status === '部分借出')"
                type="primary" link size="small" @click.stop="openBorrow(row)">借出</el-button>
              <el-button v-if="row.part_type === '治具' && (row.status === '已借出' || row.status === '部分借出')"
                type="warning" link size="small" @click.stop="openReturn(row)">归还</el-button>
              <span v-if="row.part_type === '治具' && row.status === '维修中'"
                class="wh-repair-text">维修中</span>
              <!-- 耗材 -->
              <el-button v-if="row.part_type === '耗材' && row.stock_qty > 0"
                type="primary" link size="small" @click.stop="openConsume(row)">领用</el-button>
              <el-button v-if="row.part_type === '耗材'"
                type="success" link size="small" @click.stop="openRestock(row)">补货</el-button>
              <!-- 管理 -->
              <el-button type="info" link size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button v-if="userStore.isAdmin" type="danger" link size="small" @click.stop="handleDelete(row)">删除</el-button>
            </template>
            <span v-else style="color: var(--c-text-mute); font-size: 12px;">点击行查看详情</span>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty :image-size="80" description="暂无物品...">
            <template #image><div style="font-size:44px;">📦</div></template>
          </el-empty>
        </template>
      </el-table>

      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact />
    </div>

    <!-- 新增 / 编辑物品 -->
    <el-dialog v-model="editDialog" :title="editForm.id ? '编辑物品' : '新增物品'" width="560px" destroy-on-close>
      <el-form :model="editForm" label-width="92px">
        <el-form-item label="物品名称" required>
          <el-input v-model="editForm.name" placeholder="如：测试治具A / 高温胶带" maxlength="100" />
        </el-form-item>
        <el-form-item label="型号/编号">
          <el-input v-model="editForm.model" placeholder="设备型号或内部编号" maxlength="100" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="editForm.part_type" :disabled="!!editForm.id">
            <el-radio value="治具">🔧 治具</el-radio>
            <el-radio value="耗材">🧴 耗材</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editForm.part_type === '治具'" label="总数">
          <el-input-number v-model="editForm.total_qty" :min="0" :max="9999" controls-position="right" />
          <span class="wh-form-hint">治具总数量（新增时可用数=总数）</span>
        </el-form-item>
        <el-form-item v-if="editForm.part_type === '治具' && editForm.id" label="维修状态">
          <el-switch v-model="editForm.in_repair" active-text="维修中（不可借出）" inactive-text="正常" />
        </el-form-item>
        <template v-if="editForm.part_type === '耗材'">
          <el-form-item :label="editForm.id ? '库存数量' : '初始库存'">
            <el-input-number v-model="editForm.total_qty" :min="0" :max="999999" controls-position="right" />
          </el-form-item>
          <el-form-item label="单位">
            <el-input v-model="editForm.unit" placeholder="个 / 卷 / 包 / 瓶…" maxlength="20" style="width: 160px;" />
          </el-form-item>
          <el-form-item label="预警值">
            <el-input-number v-model="editForm.warn_qty" :min="0" :max="999999" controls-position="right" />
            <span class="wh-form-hint">库存 ≤ 预警值时顶部预警并标红</span>
          </el-form-item>
        </template>
        <el-form-item label="货位">
          <el-input v-model="editForm.location" placeholder="如 A01-1-2" maxlength="50" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="editForm.supplier" placeholder="选填" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 治具借出 -->
    <el-dialog v-model="borrowDialog" title="🔧 治具借出" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>可用数量：<b class="ok-text">{{ actionRow.available_qty }}</b> / {{ actionRow.total_qty }}</p>
      </div>
      <el-form :model="borrowForm" label-width="92px">
        <el-form-item label="借用人" required>
          <el-input v-model="borrowForm.operator" placeholder="借用人姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="线体" required>
          <el-select v-model="borrowForm.line" placeholder="选择线体" style="width: 100%;">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="borrowForm.qty" :min="1" :max="actionRow?.available_qty || 1" controls-position="right" />
        </el-form-item>
        <el-form-item label="预计归还">
          <el-date-picker v-model="borrowForm.expected_return" type="date" value-format="YYYY-MM-DD"
            placeholder="选择日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="borrowForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="borrowDialog = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="submitBorrow">确认借出</el-button>
      </template>
    </el-dialog>

    <!-- 治具归还 -->
    <el-dialog v-model="returnDialog" title="🔧 治具归还" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>库存情况：总 {{ actionRow.total_qty }} / 可用 <b class="ok-text">{{ actionRow.available_qty }}</b> / 外借未还 <b class="warn-text">{{ actionRow.total_qty - actionRow.available_qty }}</b></p>
        <p>当前借用人：<b class="warn-text">{{ actionRow.current_borrower || '多笔借出（见操作记录）' }}</b></p>
        <p>借出时间：{{ actionRow.borrow_time || '-' }}　预计归还：{{ actionRow.expected_return || '-' }}</p>
        <p class="wh-return-hint">确认归还将一次性收回全部外借数量（{{ actionRow.total_qty - actionRow.available_qty }} 件）；部分归还请在备注中说明后联系管理员调整总数。</p>
      </div>
      <el-form :model="returnForm" label-width="92px">
        <el-form-item label="备注">
          <el-input v-model="returnForm.remark" type="textarea" :rows="2" maxlength="255" placeholder="归还情况备注（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnDialog = false">取消</el-button>
        <el-button type="warning" :loading="actionLoading" @click="submitReturn">确认归还</el-button>
      </template>
    </el-dialog>

    <!-- 耗材领用 -->
    <el-dialog v-model="consumeDialog" title="🧴 耗材领用" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : 'ok-text'">
          {{ actionRow.stock_qty }}</b> {{ actionRow.unit }}　预警值：{{ actionRow.warn_qty }}
        </p>
      </div>
      <el-form :model="consumeForm" label-width="92px">
        <el-form-item label="领用人" required>
          <el-input v-model="consumeForm.operator" placeholder="领用人姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="线体" required>
          <el-select v-model="consumeForm.line" placeholder="选择线体" style="width: 100%;">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" required>
          <el-input-number v-model="consumeForm.qty" :min="1" :max="actionRow?.stock_qty || 1" controls-position="right" />
          <span class="wh-form-hint">{{ actionRow?.unit }}</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="consumeForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="consumeDialog = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="submitConsume">确认领用</el-button>
      </template>
    </el-dialog>

    <!-- 耗材补货 -->
    <el-dialog v-model="restockDialog" title="🧴 耗材补货" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : ''">
          {{ actionRow.stock_qty }}</b> {{ actionRow.unit }}　预警值：{{ actionRow.warn_qty }}
        </p>
      </div>
      <el-form :model="restockForm" label-width="92px">
        <el-form-item label="补货数量" required>
          <el-input-number v-model="restockForm.qty" :min="1" :max="999999" controls-position="right" />
          <span class="wh-form-hint">{{ actionRow?.unit }}</span>
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="restockForm.supplier" placeholder="选填" maxlength="100" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="restockForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="restockDialog = false">取消</el-button>
        <el-button type="success" :loading="actionLoading" @click="submitRestock">确认补货</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importDialog" title="📥 批量导入物品" width="560px" destroy-on-close>
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="onFileChange"
        :on-remove="onFileRemove"
        :on-exceed="onExceed"
      >
        <div style="padding: 16px 0;">
          <el-icon style="font-size: 42px; color: var(--primary-500);"><UploadFilled /></el-icon>
          <div class="el-upload__text" style="margin-top: 8px;">将 Excel 文件拖到此处，或<em>点击上传</em></div>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx / .xls；表头列：<b>物品名称、型号、类型、数量、货位、单位、预警值、供应商</b>（物品名称必填，类型留空默认耗材）
          </div>
        </template>
      </el-upload>

      <div v-if="importResult" class="wh-import-result">
        <div class="wh-import-summary">
          <span class="ok-text">✅ 成功 {{ importResult.success }} 条</span>
          <span v-if="importResult.failed" class="danger-text">❌ 失败 {{ importResult.failed }} 条</span>
        </div>
        <div v-if="importResult.errors?.length" class="wh-import-errors">
          <div v-for="(msg, i) in importResult.errors" :key="i" class="wh-import-error-line">{{ msg }}</div>
        </div>
      </div>

      <template #footer>
        <el-button @click="importDialog = false">{{ importResult ? '关闭' : '取消' }}</el-button>
        <el-button v-if="!importResult" type="primary" :loading="importing" :disabled="!importFile" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 物品详情（点击行打开） -->
    <el-dialog v-model="detailDialog" title="物品详情" width="620px" destroy-on-close>
      <div v-if="detail" class="wh-detail">
        <div class="wh-detail-head">
          <span class="wh-detail-name">{{ detail.part.name }}</span>
          <el-tag :type="statusTagType(detail.part)" size="small">{{ detail.part.status }}</el-tag>
        </div>

        <el-descriptions :column="2" border size="small" class="wh-desc">
          <el-descriptions-item label="类型">{{ detail.part.part_type }}</el-descriptions-item>
          <el-descriptions-item label="型号/编号">{{ detail.part.model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="货位">{{ detail.part.location || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ detail.part.qty_text }}</el-descriptions-item>
        </el-descriptions>

        <!-- 治具借出信息 -->
        <div v-if="detail.part.part_type === '治具' && (detail.part.status === '已借出' || detail.part.status === '部分借出')" class="wh-detail-block">
          <div class="wh-detail-subtitle">📌 当前借用人</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="借用人">{{ detail.part.current_borrower }}</el-descriptions-item>
            <el-descriptions-item label="借出时间">{{ detail.part.borrow_time }}</el-descriptions-item>
            <el-descriptions-item label="预计归还">{{ detail.part.expected_return || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 耗材低库存提示 -->
        <div v-if="detail.part.part_type === '耗材' && detail.part.stock_qty <= detail.part.warn_qty" class="wh-low-tip">
          <span class="bi bi-exclamation-triangle-fill"></span>
          库存预警：当前剩余 {{ detail.part.stock_qty }} {{ detail.part.unit }}，已低于预警值 {{ detail.part.warn_qty }}，请及时补货！
        </div>

        <!-- 最近操作记录 -->
        <div class="wh-detail-block">
          <div class="wh-detail-subtitle">最近操作记录</div>
          <el-table :data="detail.transactions" size="small" border empty-text="暂无记录">
            <el-table-column label="时间" prop="created_at" width="150" />
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="txTagType(row.tx_type)" size="small">{{ row.tx_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数量" prop="qty" width="60" align="center" />
            <el-table-column label="借/领用人" prop="operator" width="90" show-overflow-tooltip />
            <el-table-column label="线体" prop="line" width="70" align="center" />
            <el-table-column label="备注" prop="remark" min-width="100" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { warehouseApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, RefreshRight, Plus, ArrowDown, Upload, UploadFilled } from '@element-plus/icons-vue'
import { useNotify } from '@/composables/useNotify'
import CommonPagination from '@/components/common/CommonPagination.vue'

const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()

const lines = ['1线', '2线', '3线', '4线', '5线', '6线', '7线', '8线', '品质房', '维修房']

// ---------------- 列表 / 统计 ----------------
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const keyword = ref('')
const typeFilter = ref('')
const lowStockOnly = ref(false)
// 统计卡联动：'' 全部 / 'in_stock' 在库 / 'borrowed' 借出领用
const stockStatusFilter = ref('')
const stats = reactive({ total: 0, in_stock: 0, borrowed_out: 0, low_stock: 0 })
const lowItems = ref([])

const statusTagType = (row) => {
  if (row.part_type === '治具') {
    return { '在库': 'success', '已借出': 'danger', '部分借出': 'warning', '维修中': 'info' }[row.status] || 'info'
  }
  return { '正常': 'success', '低于预警': 'warning', '缺货': 'danger' }[row.status] || 'info'
}
const txTagType = (t) => ({ '借出': 'warning', '归还': 'success', '领用': 'primary', '补货': 'success' }[t] || 'info')

const loadStats = async () => {
  try {
    const res = await warehouseApi.stats()
    Object.assign(stats, res.data || {})
    lowItems.value = res.data?.low_stock_items || []
  } catch (e) { console.error(e) }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (typeFilter.value) params.part_type = typeFilter.value
    if (lowStockOnly.value) params.low_stock = true
    if (stockStatusFilter.value) params.stock_status = stockStatusFilter.value
    const res = await warehouseApi.list(params)
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const refreshAll = () => { loadData(); loadStats() }

const onSearch = () => { page.value = 1; loadData() }
const onReset = () => {
  keyword.value = ''
  typeFilter.value = ''
  lowStockOnly.value = false
  stockStatusFilter.value = ''
  page.value = 1
  loadData()
}
// 统计卡点击：再次点击同一筛选则取消（回到全部）；与“低于预警”互斥
const filterByStatus = (s) => {
  stockStatusFilter.value = stockStatusFilter.value === s ? '' : s
  if (stockStatusFilter.value) lowStockOnly.value = false
  page.value = 1
  loadData()
}
const toggleLowStock = () => {
  lowStockOnly.value = !lowStockOnly.value
  if (lowStockOnly.value) stockStatusFilter.value = ''
  page.value = 1
  loadData()
}

watch([page, pageSize], () => loadData())

// ---------------- 新增 / 编辑 ----------------
const editDialog = ref(false)
const saving = ref(false)
const editForm = reactive({})

const openEdit = (row) => {
  if (row) {
    Object.assign(editForm, {
      id: row.id, name: row.name, model: row.model, part_type: row.part_type,
      total_qty: row.total_qty, unit: row.unit, location: row.location,
      warn_qty: row.warn_qty, supplier: row.supplier, in_repair: row.in_repair,
    })
  } else {
    Object.assign(editForm, {
      id: null, name: '', model: '', part_type: '治具',
      total_qty: 1, unit: '个', location: '', warn_qty: 0, supplier: '', in_repair: false,
    })
  }
  editDialog.value = true
}

const submitEdit = async () => {
  if (!editForm.name?.trim()) { toast.error('请填写物品名称'); return }
  saving.value = true
  try {
    const payload = { ...editForm }
    if (editForm.id) {
      await warehouseApi.update(editForm.id, payload)
      toast.success('修改成功')
    } else {
      await warehouseApi.create(payload)
      toast.success('新增成功')
    }
    editDialog.value = false
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const ok = await confirmDelete('库房物品', `将删除「${row.name}」及其全部流水记录`)
  if (!ok) return
  try {
    await warehouseApi.delete(row.id)
    toast.success('删除成功')
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '删除失败')
  }
}

// ---------------- 批量导入 ----------------
const uploadRef = ref(null)
const importDialog = ref(false)
const importing = ref(false)
const importFile = ref(null)
const importResult = ref(null)

const openImport = () => {
  importFile.value = null
  importResult.value = null
  importDialog.value = true
}

const onFileChange = (file) => {
  const name = (file.name || '').toLowerCase()
  if (!name.endsWith('.xlsx') && !name.endsWith('.xls')) {
    toast.error('仅支持 .xlsx / .xls 文件')
    uploadRef.value?.clearFiles()
    importFile.value = null
    return
  }
  importFile.value = file.raw
  importResult.value = null
}
const onFileRemove = () => { importFile.value = null }
const onExceed = () => { toast.warning('一次只能导入一个文件，请先移除已选文件') }

const handleImport = async () => {
  if (!importFile.value) { toast.error('请先选择 Excel 文件'); return }
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    const res = await warehouseApi.importParts(fd)
    importResult.value = res.data
    if (res.data?.success > 0) {
      toast.success(`导入完成：成功 ${res.data.success} 条，失败 ${res.data.failed} 条`)
      refreshAll()
    } else {
      toast.error('导入失败，请检查文件内容')
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || '导入失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}

// ---------------- 借出 / 归还 / 领用 / 补货 ----------------
const borrowDialog = ref(false)
const returnDialog = ref(false)
const consumeDialog = ref(false)
const restockDialog = ref(false)
const actionLoading = ref(false)
const actionRow = ref(null)
const borrowForm = reactive({ operator: '', line: '', qty: 1, expected_return: '', remark: '' })
const returnForm = reactive({ remark: '' })
const consumeForm = reactive({ operator: '', line: '', qty: 1, remark: '' })
const restockForm = reactive({ qty: 1, supplier: '', remark: '' })

const resetActionForms = () => {
  Object.assign(borrowForm, { operator: '', line: '', qty: 1, expected_return: '', remark: '' })
  Object.assign(returnForm, { remark: '' })
  Object.assign(consumeForm, { operator: '', line: '', qty: 1, remark: '' })
  Object.assign(restockForm, { qty: 1, supplier: '', remark: '' })
}

const openBorrow = (row) => { actionRow.value = row; resetActionForms(); borrowForm.qty = 1; borrowDialog.value = true }
const openReturn = (row) => { actionRow.value = row; resetActionForms(); returnDialog.value = true }
const openConsume = (row) => { actionRow.value = row; resetActionForms(); consumeForm.qty = 1; consumeDialog.value = true }
const openRestock = (row) => { actionRow.value = row; resetActionForms(); restockForm.qty = 1; restockForm.supplier = row.supplier || ''; restockDialog.value = true }

const afterAction = (msg) => {
  toast.success(msg)
  borrowDialog.value = returnDialog.value = consumeDialog.value = restockDialog.value = false
  refreshAll()
}

const submitBorrow = async () => {
  if (!borrowForm.operator?.trim() || !borrowForm.line) { toast.error('请填写借用人并选择线体'); return }
  actionLoading.value = true
  try {
    await warehouseApi.borrow(actionRow.value.id, { ...borrowForm })
    afterAction('借出成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitReturn = async () => {
  actionLoading.value = true
  try {
    await warehouseApi.returnBack(actionRow.value.id, { ...returnForm })
    afterAction('归还成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitConsume = async () => {
  if (!consumeForm.operator?.trim() || !consumeForm.line) { toast.error('请填写领用人并选择线体'); return }
  actionLoading.value = true
  try {
    await warehouseApi.consume(actionRow.value.id, { ...consumeForm })
    afterAction('领用成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitRestock = async () => {
  if (!restockForm.qty || restockForm.qty <= 0) { toast.error('请填写补货数量'); return }
  actionLoading.value = true
  try {
    await warehouseApi.restock(actionRow.value.id, { ...restockForm })
    afterAction('补货成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

// ---------------- 详情 ----------------
const detailDialog = ref(false)
const detail = ref(null)

const openDetail = async (row) => {
  try {
    const res = await warehouseApi.detail(row.id)
    detail.value = res.data
    detailDialog.value = true
  } catch (e) {
    console.error(e)
    toast.error('详情加载失败')
  }
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.wh-content { padding-bottom: 48px; }

/* 统计看板 */
.wh-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 10px;
}
.wh-stat {
  background: #fff;
  border: 1px solid var(--c-divider);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
}
.wh-stat.clickable { cursor: pointer; transition: all .15s; }
.wh-stat.clickable:hover { border-color: #F59E0B; box-shadow: 0 4px 12px rgba(245, 158, 11, .15); }
.wh-stat.active { border-color: #F59E0B; background: #FFFBEB; }
.wh-stat-num { font-size: 26px; font-weight: 800; color: var(--c-text); line-height: 1; }
.wh-stat-num.ok { color: #059669; }
.wh-stat-num.warn { color: #D97706; }
.wh-stat-num.danger { color: #DC2626; }
.wh-stat-label { font-size: 13px; color: var(--c-text-3); }

/* 低库存预警条 */
.wh-warn-bar {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 14px;
  margin-bottom: 10px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 8px;
  font-size: 13px;
}
.wh-warn-title { color: #DC2626; font-weight: 700; white-space: nowrap; padding-top: 3px; }
.wh-warn-items { display: flex; flex-wrap: wrap; gap: 8px; }
.wh-warn-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #fff;
  border: 1px solid #FECACA;
  border-radius: 999px;
  padding: 2px 6px 2px 12px;
  color: var(--c-text-2);
}
.wh-warn-chip b { color: #DC2626; }

/* 表格 */
.wh-name { font-weight: 600; color: var(--c-text); }
.wh-borrower { color: #D97706; font-size: 12px; }
.wh-repair-text { color: var(--c-text-mute); font-size: 12px; }

.wh-form-hint { margin-left: 10px; font-size: 12px; color: var(--c-text-mute); }
.ok-text { color: #059669; }
.warn-text { color: #D97706; }
.danger-text { color: #DC2626; }

/* 操作弹窗信息块 */
.wh-action-info {
  background: #F8FAFC;
  border: 1px solid var(--c-divider);
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--c-text-2);
}
.wh-action-info p { margin: 2px 0; }
.wh-return-hint { color: #92400E; font-size: 12px; line-height: 1.5; margin-top: 6px !important; }

/* 详情弹窗 */
.wh-detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.wh-detail-name { font-size: 17px; font-weight: 700; color: var(--c-text); }
.wh-detail-block { margin-top: 14px; }
.wh-detail-subtitle {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--c-text);
  margin-bottom: 6px;
}
.wh-low-tip {
  margin-top: 14px;
  padding: 10px 14px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 8px;
  color: #DC2626;
  font-size: 13px;
  font-weight: 600;
}
.wh-desc { margin-bottom: 4px; }

/* 批量导入结果 */
.wh-import-result {
  margin-top: 14px;
  border: 1px solid var(--c-divider);
  border-radius: 8px;
  padding: 10px 14px;
  background: #F8FAFC;
}
.wh-import-summary {
  display: flex;
  gap: 18px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 6px;
}
.wh-import-errors {
  max-height: 160px;
  overflow-y: auto;
  border-top: 1px dashed var(--c-divider);
  padding-top: 6px;
}
.wh-import-error-line {
  font-size: 12.5px;
  color: #DC2626;
  line-height: 1.9;
}
</style>
