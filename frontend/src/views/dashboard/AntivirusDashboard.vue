<template>
  <div id="anti-board" class="page">
    <!-- 操作按钮通过 Teleport 注入全局顶栏左侧空白区，不占用看板纵向空间 -->
    <Teleport defer to=".topbar-actions">
      <button class="btn btn-sm btn-outline-primary" @click="exportPPT" :disabled="exporting">
        <span class="bi" :class="exporting ? 'bi-hourglass-split' : 'bi-file-earmark-ppt'"></span>
        {{ exporting ? '导出中...' : '导出PPT' }}
      </button>
    </Teleport>

    <!-- 顶部 4 张统计卡：统一走 StatCard 组件（与其它看板观感一致） -->
    <div class="stat-grid kpi-row">
      <StatCard centered color="blue" icon="bi bi-pc-display" :num="stats.total_devices" label="设备总数" />
      <StatCard centered color="green" icon="bi bi-check-circle-fill" :num="stats.done_count" label="已杀毒" />
      <StatCard
        centered
        color="yellow"
        icon="bi bi-clock-history"
        :num="stats.pending_count"
        label="待杀毒"
        clickable
        @click="showPendingModal(null)"
      />
      <StatCard
        centered
        color="red"
        icon="bi bi-shield-exclamation"
        :num="stats.overdue_count"
        label="超时未杀毒"
        clickable
        @click="showOverdueModal(null)"
      />
    </div>

    <!-- 按线体分布：Element Plus el-table 表格（卡内滚动，不被一屏 overflow 裁切） -->
    <section class="page-section table-section">
      <div class="table-title">按线体分布</div>
      <div class="table-scroll">
      <el-table
        :data="distribution"
        border
        stripe
        height="100%"
        style="width:100%;"
        empty-text="暂无数据"
        :header-cell-style="{ fontWeight: 600, fontSize: '14px' }"
      >
        <el-table-column label="线体" prop="line" min-width="100" align="center">
          <template #default="s">
            <span style="font-weight:600;color:var(--c-text);">{{ s.row.line }}</span>
          </template>
        </el-table-column>
        <el-table-column label="设备总数" prop="total" min-width="100" align="center" />
        <el-table-column label="已杀毒" prop="done" min-width="100" align="center">
          <template #default="s">
            <span style="color:#10b981;font-weight:500;">{{ s.row.done }}</span>
          </template>
        </el-table-column>
        <el-table-column label="待杀毒" prop="pending" min-width="100" align="center">
          <template #default="s">
            <span
              v-if="s.row.pending > 0"
              style="color:#f59e0b;font-weight:500;cursor:pointer;text-decoration:underline;"
              @click="showPendingModal(s.row.line)"
            >{{ s.row.pending }}</span>
            <span v-else style="color:#f59e0b;font-weight:500;">{{ s.row.pending }}</span>
          </template>
        </el-table-column>
        <el-table-column label="超时未杀毒" prop="overdue" min-width="120" align="center">
          <template #default="s">
            <span v-if="s.row.overdue > 0" style="color:#ef4444;font-weight:500;cursor:pointer;text-decoration:underline;" @click="showOverdueModal(s.row.line)">{{ s.row.overdue }}</span>
            <span v-else style="color:#ef4444;font-weight:500;">{{ s.row.overdue }}</span>
          </template>
        </el-table-column>
        <el-table-column label="进度" min-width="320" align="center">
          <template #default="s">
            <div class="anti-progress-bar" :class="'bar-' + s.row.level">
              <div class="anti-progress-inner" :style="{ width: s.row.progress + '%' }"></div>
              <div class="anti-progress-text" :class="'txt-' + s.row.level">{{ s.row.progress }}%</div>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :image-size="80" description="暂无数据...">
            <template #image><div style="font-size:44px;">📋</div></template>
          </el-empty>
        </template>
      </el-table>
      </div>
    </section>

    <!-- 超时未杀毒记录弹窗 -->
    <el-dialog
      v-model="overdueModalVisible"
      :title="overdueLine ? overdueLine + ' - 超时未杀毒记录' : '全部超时未杀毒记录'"
      width="900px"
      align-center
      destroy-on-close
    >
      <el-table :data="overdueRecords" stripe border style="width:100%;" max-height="420" empty-text="暂无超时记录">
        <el-table-column prop="device_id" label="设备ID" min-width="140" align="center" show-overflow-tooltip />
        <el-table-column prop="production_line" label="线体" width="90" align="center" />
        <el-table-column prop="cycle" label="周期" width="80" align="center" />
        <el-table-column label="上次杀毒时间" min-width="170" align="center">
          <template #default="s">{{ (s.row.antivirus_time || '').slice(0, 19).replace('T', ' ') }}</template>
        </el-table-column>
        <el-table-column label="应杀毒时间" min-width="170" align="center">
          <template #default="s">{{ (s.row.next_antivirus_time || '').slice(0, 19).replace('T', ' ') }}</template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="100" align="center">
          <template #default="s">{{ s.row.operator || '-' }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div class="dialog-footer-bar">
          <span class="dialog-total">共 {{ overdueTotal }} 条记录</span>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="pendingModalVisible"
      :title="pendingLine ? pendingLine + ' - 待杀毒记录' : '全部待杀毒记录'"
      width="900px"
      align-center
      destroy-on-close
    >
      <el-table :data="pendingRecords" stripe border style="width:100%;" max-height="420" empty-text="暂无待杀毒记录">
        <el-table-column prop="device_id" label="设备ID" min-width="140" align="center" show-overflow-tooltip />
        <el-table-column prop="production_line" label="线体" width="90" align="center" />
        <el-table-column prop="cycle" label="周期" width="80" align="center" />
        <el-table-column label="上次杀毒时间" min-width="170" align="center">
          <template #default="s">{{ (s.row.antivirus_time || '').slice(0, 19).replace('T', ' ') }}</template>
        </el-table-column>
        <el-table-column label="应杀毒时间" min-width="170" align="center">
          <template #default="s">{{ (s.row.next_antivirus_time || '').slice(0, 19).replace('T', ' ') }}</template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="100" align="center">
          <template #default="s">{{ s.row.operator || '-' }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div class="dialog-footer-bar">
          <span class="dialog-total">共 {{ pendingTotal }} 条记录</span>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi, antivirusApi } from '@/api'
import StatCard from '@/components/common/StatCard.vue'
import { ElMessage } from 'element-plus'
import { createPresentation, addFullImageSlide, savePresentation, captureElement } from '@/utils/pptExport'

const stats = ref({ total_devices: 0, done_count: 0, pending_count: 0, overdue_count: 0 })
const distribution = ref([])
const exporting = ref(false)

// 超时/待杀毒记录弹窗
const overdueModalVisible = ref(false)
const overdueLine = ref(null)
const overdueRecords = ref([])
const overdueTotal = ref(0)

const pendingModalVisible = ref(false)
const pendingLine = ref(null)
const pendingRecords = ref([])
const pendingTotal = ref(0)

const showOverdueModal = async (line) => {
  overdueLine.value = line
  overdueModalVisible.value = true
  overdueRecords.value = []
  overdueTotal.value = 0
  try {
    const params = { page: 1, page_size: 200, status: 'overdue' }
    if (line) params.production_line = line
    const res = await antivirusApi.overdueRecords(params)
    overdueRecords.value = res.data?.items || []
    overdueTotal.value = res.data?.total || 0
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '加载超时记录失败')
  }
}

const showPendingModal = async (line) => {
  pendingLine.value = line
  pendingModalVisible.value = true
  pendingRecords.value = []
  pendingTotal.value = 0
  try {
    const params = { page: 1, page_size: 200, status: 'pending' }
    if (line) params.production_line = line
    const res = await antivirusApi.overdueRecords(params)
    pendingRecords.value = res.data?.items || []
    pendingTotal.value = res.data?.total || 0
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '加载待杀毒记录失败')
  }
}

const loadData = async () => {
  try {
    const res = await dashboardApi.antivirus()
    stats.value = {
      total_devices: res.data?.total_devices ?? 0,
      done_count:    res.data?.done_count    ?? 0,
      pending_count: res.data?.pending_count ?? 0,
      overdue_count: res.data?.overdue_count ?? 0,
    }
    // 根据进度设置 level，供样式使用：
    // - >= 90% => success (绿色)
    // - 60-89% => muted   (中性/深色文本)
    // - < 60%  => danger  (红色)
    distribution.value = (res.data?.distribution || []).map(item => {
      const progress = Number(item.progress) || 0
      let level = 'muted'
      if (progress >= 90) level = 'success'
      else if (progress < 60) level = 'danger'
      return { ...item, progress, level }
    })
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '加载杀毒看板数据失败')
    console.error(e)
  }
}

onMounted(loadData)

// 导出PPT：整屏看板截图，仅一页
const exportPPT = async () => {
  exporting.value = true
  try {
    // 操作按钮已移至全局顶栏（不在看板截图范围内），无需再临时隐藏
    const boardImg = await captureElement('anti-board')
    const pptx = createPresentation('设备杀毒看板')
    addFullImageSlide(pptx, boardImg)
    const date = new Date().toISOString().slice(0, 10)
    savePresentation(pptx, `设备杀毒看板_${date}.pptx`)
  } catch (error) {
    console.error('导出PPT失败:', error)
    ElMessage.error('导出PPT失败，请重试')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
/* 一屏驾驶舱：KPI 行固定，表格卡吃掉剩余高度并在卡内滚动，行多也不被裁切 */
.page {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--gap-block);
  padding: 0;
}
.kpi-row { flex-shrink: 0; }
.table-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.table-title {
  flex-shrink: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--c-text);
  padding: 14px 0 14px 4px;
  text-align: center;
}
.table-scroll {
  flex: 1;
  min-height: 0;
}

/* ---------- 进度条（百分比内嵌在进度条上方，模仿截图） ---------- */
.anti-progress-bar {
  width: 100%;
  max-width: 520px;
  height: 22px;
  background: #E5E7EB;
  border-radius: 999px;
  overflow: visible;
  position: relative;
  display: block;
  margin: 0 auto; /* 居中 */
}
.anti-progress-inner {
  height: 100%;
  border-radius: 999px;
  transition: width .3s ease;
}
.bar-muted   .anti-progress-inner { background: #CBD5E1; }
.bar-danger  .anti-progress-inner { background: #EF4444; }
.bar-success .anti-progress-inner { background: #22C55E; }

.anti-progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: auto;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.2px;
  pointer-events: none;
}
.txt-muted   { color: #475569; }
.txt-danger  { color: #ffffff; }
.txt-success { color: #ffffff; }

.dialog-footer-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 28px;
}
.dialog-total {
  color: var(--c-text-3);
  font-size: 13px;
  white-space: nowrap;
  text-align: center;
}
</style>
