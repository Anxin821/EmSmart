<template>
  <div id="mes-board" class="page">
    <!-- 操作按钮通过 Teleport 注入全局顶栏左侧空白区，不占用看板纵向空间 -->
    <Teleport defer to=".topbar-actions">
      <button class="btn btn-sm btn-outline-primary" @click="exportPPT" :disabled="exporting">
        <span class="bi" :class="exporting ? 'bi-hourglass-split' : 'bi-file-earmark-ppt'"></span>
        {{ exporting ? '导出中...' : '导出PPT' }}
      </button>
    </Teleport>

    <div class="cockpit">
    <!-- KPI 指标：BUG修复率 / 需求完成率 / 未关闭BUG / 延期需求 -->
    <div class="stat-grid">
      <StatCard centered color="green" icon="bi bi-bug-fill" :num="`${data?.fix_rate ?? 0}%`" label="BUG修复率" />
      <StatCard centered color="blue" icon="bi bi-check2-circle" :num="`${data?.delivery_rate ?? 0}%`" label="需求完成率" />
      <StatCard centered color="red" icon="bi bi-exclamation-octagon-fill" :num="openBugCount" label="未关闭BUG" clickable @click="showOpenBugsModal(null)" />
      <StatCard centered color="yellow" icon="bi bi-alarm-fill" :num="overdueReqCount" label="延期需求" clickable @click="showOverdueReqModal(null)" />
    </div>

    <!-- 两张堆叠柱状图 -->
    <div class="card-grid-2">
      <section class="page-section chart-card">
        <header class="section-head">
          <h2 class="sec-title">BUG 月度状态分布</h2>
        </header>
        <div class="section-body no-pad">
          <div id="chart-bugs" class="chart-container"></div>
          <div class="chart-legend bug-legend">
            <span class="lg-item"><span class="dot bg-confirm"></span>确认新增</span>
            <span class="lg-item"><span class="dot bg-fixing"></span>修复中</span>
            <span class="lg-item"><span class="dot bg-closed"></span>解决关闭</span>
          </div>
        </div>
      </section>

      <section class="page-section chart-card">
        <header class="section-head">
          <h2 class="sec-title">需求月度状态分布</h2>
        </header>
        <div class="section-body no-pad">
          <div id="chart-reqs" class="chart-container"></div>
          <div class="chart-legend req-legend">
            <span class="lg-item"><span class="dot bg-assess"></span>收集评估</span>
            <span class="lg-item"><span class="dot bg-testing"></span>开发测试中</span>
            <span class="lg-item"><span class="dot bg-online"></span>上线</span>
          </div>
        </div>
      </section>
    </div>

    <!-- 底部 2 块：风险 + 里程碑 -->
    <div class="card-grid-2">
      <section class="page-section risk-card">
        <header class="section-head">
          <h2 class="sec-title"><span class="sec-emoji warn">⚠️</span>阻塞与风险归因 (TOP{{ data?.risks?.length || 2 }})</h2>
        </header>
        <div class="section-body" style="padding: 4px 18px 12px;">
          <div v-if="!data" class="empty-state">加载中…</div>
          <ul v-else class="risk-list">
            <li v-for="(r, idx) in data.risks" :key="idx">
              <span class="risk-bullet" :style="{background: r.icon==='p0_bug' ? '#EF4444' : '#F59E0B'}"></span>
              <span class="risk-title">
                <b>{{ r.label }}</b>：{{ r.value }} {{ r.unit }}
                <template v-if="r.items && r.items.length">
                  <span v-if="r.items.length" class="risk-detail">
                    ({{ r.items.join('、') }})
                  </span>
                </template>
                <span v-else class="risk-detail muted">（暂无）</span>
              </span>
            </li>
          </ul>
        </div>
      </section>

      <section class="page-section milestone-card">
        <header class="section-head">
          <h2 class="sec-title"><span class="sec-emoji ok">✅</span>本月里程碑 & 下月承诺</h2>
        </header>
        <div class="section-body" style="padding: 4px 18px 12px;">
          <div v-if="!data" class="empty-state">加载中…</div>
          <div v-else class="milestone-box">
            <div class="ms-top">
              <span class="ms-check bi bi-check2-circle"></span>
              <b>{{ data.milestones?.label }}</b>：{{ data.milestones?.count }} 个需求
            </div>
            <div class="ms-list">
              ({{ data.milestones?.items?.join('、') || '' }})
            </div>
          </div>
        </div>
      </section>
    </div>
    </div>

    <!-- 未关闭 BUG 弹窗 -->
    <el-dialog
      v-model="openBugModalVisible"
      :title="openBugTitle"
      width="900px"
      align-center
      destroy-on-close
    >
      <el-table :data="openBugRecords" stripe border style="width:100%;" max-height="420" empty-text="暂无未关闭 BUG">
        <el-table-column prop="bug_id" label="BUG ID" min-width="140" align="center" show-overflow-tooltip />
        <el-table-column prop="title" label="标题" min-width="200" align="center" show-overflow-tooltip />
        <el-table-column prop="severity" label="严重等级" width="100" align="center">
          <template #default="s"><span :class="'status-badge ' + getStatusClass(cleanStatus(s.row.severity))">{{ cleanStatus(s.row.severity) }}</span></template>
        </el-table-column>
        <el-table-column prop="module" label="模块" min-width="110" align="center" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center" />
        <el-table-column prop="discoverer" label="发现人" width="100" align="center" />
        <el-table-column prop="assignee" label="指派给" width="100" align="center" />
        <el-table-column prop="deadline" label="截止日期" width="120" align="center" />
        <el-table-column label="录入时间" width="160" align="center">
          <template #default="s">{{ formatTime(s.row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div class="dialog-footer-bar">
          <el-button class="dialog-close-btn" @click="openBugModalVisible = false">关闭</el-button>
          <span class="dialog-total">共 {{ openBugTotal }} 条记录</span>
        </div>
      </template>
    </el-dialog>

    <!-- 延期需求 弹窗 -->
    <el-dialog
      v-model="overdueReqModalVisible"
      :title="overdueReqTitle"
      width="900px"
      align-center
      destroy-on-close
    >
      <el-table :data="overdueReqRecords" stripe border style="width:100%;" max-height="420" empty-text="暂无延期需求">
        <el-table-column prop="request_id" label="需求ID" min-width="140" align="center" show-overflow-tooltip />
        <el-table-column prop="title" label="标题" min-width="200" align="center" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="100" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center" />
        <el-table-column prop="submitter" label="提交人" width="100" align="center" />
        <el-table-column prop="assignee" label="指派给" width="100" align="center" />
        <el-table-column prop="expected_date" label="期望日期" width="120" align="center" />
        <el-table-column label="录入时间" width="160" align="center">
          <template #default="s">{{ formatTime(s.row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div class="dialog-footer-bar">
          <el-button class="dialog-close-btn" @click="overdueReqModalVisible = false">关闭</el-button>
          <span class="dialog-total">共 {{ overdueReqTotal }} 条记录</span>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount, getCurrentInstance } from 'vue'
import * as echarts from 'echarts'
import { mesApi } from '@/api'
import StatCard from '@/components/common/StatCard.vue'
import { ElMessage } from 'element-plus'
import { createPresentation, addFullImageSlide, savePresentation, captureElement } from '@/utils/pptExport'

const data = ref(null)

// KPI 派生指标：按真实 BUG 列表计算，和弹窗保持一致。
const openBugCount = ref(0)
const overdueReqCount = ref(0)
const exporting = ref(false)
let cBugs = null, cReqs = null

// 未关闭 BUG 弹窗数据
const openBugModalVisible = ref(false)
const openBugTitle = ref('未关闭 BUG')
const openBugRecords = ref([])
const openBugTotal = ref(0)
const openBugLoading = ref(false) // 防止重复打开
const openBugLastOpen = ref(0)    // 时间戳防抖
// 全局防重复（跨组件实例）
if (typeof window !== 'undefined' && !window.__openBugDialog) window.__openBugDialog = false

// 延期需求 弹窗数据
const overdueReqModalVisible = ref(false)
const overdueReqTitle = ref('延期需求')
const overdueReqRecords = ref([])
const overdueReqTotal = ref(0)
const overdueReqLoading = ref(false) // 防止重复打开
const overdueReqLastOpen = ref(0)    // 时间戳防抖
if (typeof window !== 'undefined' && !window.__overdueReqDialog) window.__overdueReqDialog = false

// 工具：清理字段显示
const cleanStatus = (v) => (v == null ? '-' : String(v))
// 时间格式化（与需求时间保持一致，显示到分钟）
const formatTime = (v) => (v ? String(v).replace('T', ' ').slice(0, 16) : '-')
const getStatusClass = (s) => {
  const map = { '致命': 'severe', '严重': 'severe', '一般': 'muted', '建议': 'muted', '确认新增': 'severe', '修复中': 'progress', '解决关闭': 'normal' }
  return map[s] || 'muted'
}

// 点击显示未关闭 BUG 列表（与杀毒超时弹窗一致风格）
const showOpenBugsModal = async () => {
  const now = Date.now()
  if (openBugModalVisible.value || openBugLoading.value || (now - openBugLastOpen.value) < 800) return
  // 跨实例全局锁
  if (typeof window !== 'undefined' && window.__openBugDialog) {
    console.warn('openBug blocked by global lock')
    return
  }
  openBugLastOpen.value = now
  openBugLoading.value = true
  if (typeof window !== 'undefined') window.__openBugDialog = true
  const vm = getCurrentInstance()
  console.trace('showOpenBugsModal triggered, instance uid=', vm?.uid)
  openBugModalVisible.value = true
  openBugRecords.value = []
  openBugTotal.value = 0
  try {
    const params = { page: 1, page_size: 100 }
    const res = await mesApi.bugs(params)
    // 过滤未关闭（非 '解决关闭'）
    const items = res.data?.items || []
    const list = items.filter(i => (i.status || '') !== '解决关闭')
    openBugRecords.value = list
    openBugTotal.value = list.length
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '加载未关闭BUG失败')
  } finally {
    openBugLoading.value = false
    if (typeof window !== 'undefined') window.__openBugDialog = false
    // 防止紧接着又触发，短时内保留 lastOpen，1.5s 后清除
    setTimeout(() => { openBugLastOpen.value = 0 }, 1500)
  }
}

// 点击显示延期需求（按期望日期计算 overdue，与风险数据一致）
const showOverdueReqModal = async () => {
  const now = Date.now()
  if (overdueReqModalVisible.value || overdueReqLoading.value || (now - overdueReqLastOpen.value) < 800) return
  // 跨实例全局锁
  if (typeof window !== 'undefined' && window.__overdueReqDialog) {
    console.warn('overdueReq blocked by global lock')
    return
  }
  overdueReqLastOpen.value = now
  overdueReqLoading.value = true
  if (typeof window !== 'undefined') window.__overdueReqDialog = true
  const vm = getCurrentInstance()
  console.trace('showOverdueReqModal triggered, instance uid=', vm?.uid)
  overdueReqModalVisible.value = true
  overdueReqRecords.value = []
  overdueReqTotal.value = 0

  const params = { page: 1, page_size: 100 }

  // 先直接获取全部（客户端过滤更可靠），再按需尝试后端筛选作为备用
  try {
    const res = await mesApi.devreqs(params)
    const items = (res && (res.data?.items || res.items || res.data || [])) || []

    const todayStart = new Date(); todayStart.setHours(0,0,0,0)
    const list = items.filter(i => {
      const expectedRaw = i.expected_date || i.expected || ''
      if (!expectedRaw) return false
      let expectedDate
      try {
        expectedDate = new Date(expectedRaw)
        if (isNaN(expectedDate)) expectedDate = new Date(String(expectedRaw).slice(0,10))
      } catch (err) {
        return false
      }
      expectedDate.setHours(0,0,0,0)
      return expectedDate.getTime() < todayStart.getTime() && (i.status || '') !== '上线'
    })

    console.debug('showOverdueReqModal: fetched', items.length, 'items, filtered', list.length)

    if (list.length > 0) {
      overdueReqRecords.value = list
      overdueReqTotal.value = list.length
    } else if (items.length > 0) {
      const marked = items.map(i => {
        const expectedRaw = i.expected_date || i.expected || ''
        let expectedDate = null
        try { expectedDate = new Date(expectedRaw) } catch(e) { expectedDate = null }
        const isOverdue = expectedDate ? (new Date(expectedDate).setHours(0,0,0,0) < new Date().setHours(0,0,0,0)) : false
        return { ...i, _isOverdue: isOverdue }
      })
      overdueReqRecords.value = marked
      overdueReqTotal.value = marked.length
      ElMessage.info('后端返回了 ' + items.length + ' 条需求，但没有符合延期筛选，已显示全部以便检查')
    } else {
      overdueReqRecords.value = []
      overdueReqTotal.value = 0
    }
  } catch (err) {
    console.warn('showOverdueReqModal primary fetch failed, trying backend filters', err)
    // 备用：尝试后端筛选
    const attempts = [
      (p) => mesApi.devreqs({ ...p, status: 'overdue' }),
      (p) => mesApi.devreqs({ ...p, overdue: true })
    ]
    let lastErr = null
    for (const fn of attempts) {
      try {
        const res = await fn(params)
        const items = (res && (res.data?.items || res.items || res.data || [])) || []
        overdueReqRecords.value = items
        overdueReqTotal.value = items.length
        lastErr = null
        break
      } catch (e) {
        lastErr = e
        console.warn('showOverdueReqModal attempt failed:', e)
      }
    }
    if (lastErr) {
      console.error('加载延期需求最终失败：', lastErr)
      const msg = lastErr?.response?.data?.message || lastErr?.message || '加载延期需求失败'
      ElMessage.error(msg)
    }
  } finally {
    overdueReqLoading.value = false
    if (typeof window !== 'undefined') window.__overdueReqDialog = false
    setTimeout(() => { overdueReqLastOpen.value = 0 }, 1500)
  }
}

const resize = () => {
  cBugs && cBugs.resize()
  cReqs && cReqs.resize()
}

const loadData = async () => {
  try {
    const res = await mesApi.dashboard()
    data.value = res.data || null

    // 先同步未关闭 BUG 数：与弹窗使用同一份真实数据源（mesApi.bugs）
    try {
      const bugRes = await mesApi.bugs({ page: 1, page_size: 100 })
      const items = bugRes.data?.items || []
      const openList = items.filter(i => (i.status || '') !== '解决关闭')
      openBugCount.value = openList.length
    } catch (err) {
      console.warn('计算未关闭 BUG 数时拉取 bugs 失败：', err)
      openBugCount.value = Math.max((data.value?.bug_count ?? 0) - (data.value?.bug_fixed ?? 0), 0)
    }

    // 同步计算延期需求数：以 devreqs 接口为准，按期望日期且非上线视为延期
    try {
      const r = await mesApi.devreqs({ page: 1, page_size: 100 })
      const items = (r && (r.data?.items || r.items || r.data || [])) || []
      const todayStart = new Date(); todayStart.setHours(0,0,0,0)
      const overdueList = items.filter(i => {
        const expectedRaw = i.expected_date || i.expected || ''
        if (!expectedRaw) return false
        let expectedDate
        try {
          expectedDate = new Date(expectedRaw)
          if (isNaN(expectedDate)) expectedDate = new Date(String(expectedRaw).slice(0,10))
        } catch (err) { return false }
        expectedDate.setHours(0,0,0,0)
        return expectedDate.getTime() < todayStart.getTime() && (i.status || '') !== '上线'
      })
      overdueReqCount.value = overdueList.length
    } catch (err) {
      console.warn('计算延期需求数时拉取 devreqs 失败：', err)
      const r = (data.value?.risks || []).find(x => x.icon === 'overdue_req')
      overdueReqCount.value = r?.value ?? 0
    }

    await nextTick()
    renderCharts()
  } catch (e) {
    console.error(e)
  }
}

const renderCharts = () => {
  const bugMonths = (data.value?.bug_monthly || [])
  const reqMonths = (data.value?.req_monthly || [])
  const bugOrder = data.value?.bug_status_order || ['确认新增', '修复中', '解决关闭']
  const reqOrder = data.value?.req_status_order || ['收集评估', '开发测试中', '上线']

  // ---- BUG 堆叠柱 ----
  if (cBugs) cBugs.dispose()
  cBugs = echarts.init(document.getElementById('chart-bugs'))
  const bugColors = { '确认新增': '#EF4444', '修复中': '#F59E0B', '解决关闭': '#10B981' }
  cBugs.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: { left: 40, right: 20, top: 24, bottom: 44 },
    xAxis: {
      type: 'category',
      data: bugMonths.map(m => m.label),
      axisLine: { lineStyle: { color: '#D8DEEA' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '数量',
      nameLocation: 'start',
      nameTextStyle: { padding: [0, 0, 14, -20], fontSize: 11, color: '#6B7280' },
      splitLine: { lineStyle: { color: '#F0F2F7' } },
    },
    series: bugOrder.map(status => ({
      name: status,
      type: 'bar',
      stack: 'total',
      emphasis: { focus: 'series' },
      barWidth: '56%',
      itemStyle: { color: bugColors[status] },
      label: {
        show: true,
        position: 'inside',
        formatter: (p) => (p.value > 0 ? p.value : ''),
        color: '#fff',
        fontSize: 11,
        fontWeight: 600,
      },
      data: bugMonths.map(m => m[status] || 0),
    })),
  })

  // ---- REQ 堆叠柱 ----
  if (cReqs) cReqs.dispose()
  cReqs = echarts.init(document.getElementById('chart-reqs'))
  const reqColors = { '收集评估': '#64748B', '开发测试中': '#F97316', '上线': '#10B981' }
  cReqs.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: { left: 40, right: 20, top: 24, bottom: 44 },
    xAxis: {
      type: 'category',
      data: reqMonths.map(m => m.label),
      axisLine: { lineStyle: { color: '#D8DEEA' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '数量',
      nameLocation: 'start',
      nameTextStyle: { padding: [0, 0, 14, -20], fontSize: 11, color: '#6B7280' },
      splitLine: { lineStyle: { color: '#F0F2F7' } },
    },
    series: reqOrder.map(status => ({
      name: status,
      type: 'bar',
      stack: 'total',
      emphasis: { focus: 'series' },
      barWidth: '56%',
      itemStyle: { color: reqColors[status] },
      label: {
        show: true,
        position: 'inside',
        formatter: (p) => (p.value > 0 ? p.value : ''),
        color: '#fff',
        fontSize: 11,
        fontWeight: 600,
      },
      data: reqMonths.map(m => m[status] || 0),
    })),
  })
}

// 导出PPT：整屏看板截图，仅一页
const exportPPT = async () => {
  exporting.value = true
  try {
    // 操作按钮已移至全局顶栏（不在看板截图范围内），无需再临时隐藏
    const boardImg = await captureElement('mes-board')
    const pptx = createPresentation('MES 管理看板')
    addFullImageSlide(pptx, boardImg)
    const date = new Date().toISOString().slice(0, 10)
    savePresentation(pptx, `MES管理看板_${date}.pptx`)
  } catch (error) {
    console.error('导出PPT失败:', error)
    alert('导出PPT失败，请重试')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  cBugs && cBugs.dispose()
  cReqs && cReqs.dispose()
})
</script>

<style scoped>
/* 一屏驾驶舱：撑满内容区，KPI / 图表 / 风险里程碑 三行弹性自适应视口，无页面级滚动 */
.page {
  height: 100%;
  overflow: hidden;
}
.cockpit {
  flex: 1;
  min-height: 0;
  display: grid;
  /* 三行：KPI(auto) / 图表(1fr 独占全部剩余高度，最高最显眼) / 底部风险·里程碑(auto 按内容自适应，不再出现滚动条；内容变高时图表自动让位，不会溢出屏) */
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 12px;
}
/* 卡片头收紧：全局 14px 18px → 10px 16px，省出纵向空间给图表 */
.cockpit .section-head { padding: 10px 16px; }
/* KPI 卡内边距收紧，压低首行高度 */
.cockpit :deep(.stat-card) { padding: 12px 16px; }
/* 覆盖全局 chart-card 固定最小高，图表随单元格弹性伸缩 */
.cockpit .chart-card { min-height: 0; }
.cockpit .chart-card .section-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.cockpit .chart-card .chart-container {
  flex: 1;
  min-height: 0;
  height: auto;
  width: 100%;
}
/* 底部风险 / 里程碑卡：卡内滚动，长列表不撑破一屏 */
.cockpit .risk-card,
.cockpit .milestone-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.cockpit .risk-card .section-body,
.cockpit .milestone-card .section-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
/* KPI 卡居中 + 副信息换行已由 StatCard 的 centered prop 统一提供（见模板 <StatCard centered>），此处不再重复 */
.sec-emoji {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  margin-right: 6px;
  border-radius: 6px;
}
.sec-emoji.warn { background: rgba(245,158,11,0.12); }
.sec-emoji.ok   { background: rgba(16,185,129,0.12); }

/* 自定义 legend（放在图块下方，与截图对齐） */
.chart-legend {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 24px;
  padding: 0 0 6px;
  font-size: 13px;
  color: #4B5563;
}
/* 每个「色块 + 文字」包成一组 inline-flex，align-items:center 保证色块与文字垂直居中对齐
   （flex 布局下 vertical-align 对色块无效，必须靠分组 + align-items） */
.lg-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.chart-legend .dot {
  width: 14px; height: 14px;
  border-radius: 3px;
  flex-shrink: 0;
}
.bg-confirm { background: #EF4444; }
.bg-fixing  { background: #F59E0B; }
.bg-closed  { background: #10B981; }
.bg-assess  { background: #64748B; }
.bg-testing { background: #F97316; }
.bg-online  { background: #10B981; }

/* 风险 / 里程碑块 */
.risk-list { list-style: none; margin: 0; padding: 2px 0 0; }
.risk-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px dashed #EEF0F6;
}
.risk-list li:last-child { border-bottom: none; }
.risk-bullet {
  width: 8px; height: 8px; border-radius: 50%;
  margin-top: 9px;
  flex-shrink: 0;
}
.risk-title { font-size: 14px; color: #111827; line-height: 1.6; }
.risk-detail.muted { color: #9CA3AF; }
.risk-detail { color: #6B7280; font-weight: 400; margin-left: 4px; }

.milestone-box { padding: 4px 0; }
.ms-top {
  font-size: 15px; color: #111827; line-height: 1.5;
  display: flex; align-items: center; gap: 8px;
}
.ms-check {
  color: #10B981;
  font-size: 20px;
  font-weight: 700;
}
.ms-list {
  margin-top: 4px;
  padding: 8px 12px;
  background: #F7FAFF;
  border-left: 3px solid #2C5CE8;
  border-radius: 0 6px 6px 0;
  line-height: 1.5;
  font-size: 14px;
  color: #374151;
}
.ms-list::-webkit-scrollbar-thumb { background: #D8DEEA; border-radius: 4px; }
.ms-list::-webkit-scrollbar      { width: 6px; }

.dialog-footer-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 38px;
}
.dialog-close-btn {
  margin: 0 auto;
}
.dialog-total {
  position: absolute;
  right: 0;
  color: var(--c-text-3);
  font-size: 13px;
  white-space: nowrap;
}

/* 卡尺寸统一：图表随容器高度自适应 */
.chart-container {
  width: 100%;
  height: 100%;
}
</style>
