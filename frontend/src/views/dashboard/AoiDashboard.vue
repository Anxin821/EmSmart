<template>
  <div id="aoi-board" class="page">
    <!-- 操作按钮通过 Teleport 注入全局顶栏左侧空白区，不占用看板纵向空间 -->
    <Teleport defer to=".topbar-actions">
      <button class="btn btn-sm btn-outline-gear" @click="exportPPT" :disabled="exporting">
        <span class="bi" :class="exporting ? 'bi-hourglass-split' : 'bi-file-earmark-ppt'"></span>
        {{ exporting ? '导出中...' : '导出PPT' }}
      </button>
    </Teleport>

    <div class="cockpit">
    <!-- KPI 指标：设备总数 / 可用率 / 本月产量 / 本月直通率 -->
    <div class="stat-grid">
      <StatCard centered color="blue" icon="bi bi-display-fill" :num="stats.total" label="设备总数" clickable @click="goDevices" />
      <StatCard centered :color="availabilityColor" icon="bi bi-check-circle-fill" :num="`${availability}%`">
        <template #label>
          <span class="kpi-sub">
            可用率 ·
            <b class="kpi-ok">正常 {{ stats.normal }}</b>
            <span class="kpi-sep">/</span>
            <b class="kpi-bad">故障 {{ stats.fault }}</b>
            <span class="kpi-sep">/</span>
            <b class="kpi-mute">保养 {{ stats.maintenance }}</b>
          </span>
        </template>
      </StatCard>
      <StatCard centered color="blue" icon="bi bi-box-seam-fill" :num="latestOutput">
        <template #label>
          {{ outputLabel }} (pcs) · 年累 {{ summary.total_output.toLocaleString() }}
        </template>
      </StatCard>
      <StatCard centered :color="yieldColor" icon="bi bi-bullseye" :num="`${latestYield}%`">
        <template #label>
          <span class="kpi-sub">
            {{ yieldLabel }} · 年均 {{ summary.yield_rate }}%
            <span :class="yieldDelta >= 0 ? 'kpi-up' : 'kpi-down'">
              {{ yieldDelta >= 0 ? '↑' : '↓' }}{{ Math.abs(yieldDelta).toFixed(1) }}%
            </span>
          </span>
        </template>
      </StatCard>
    </div>

    <!-- 图表:直通率折线 + 产量柱状 -->
    <div class="card-grid-2">
      <section class="page-section chart-card">
        <header class="section-head">
          <h2 class="sec-title">直通率</h2>
          <div class="sec-actions">
            <small class="text-muted">近 12 个月 · 由周报聚合</small>
          </div>
        </header>
        <div class="section-body no-pad">
          <div id="chart-yield" v-loading="loading" class="chart-container"></div>
        </div>
      </section>

      <section class="page-section chart-card">
        <header class="section-head">
          <h2 class="sec-title">产量</h2>
          <div class="sec-actions">
            <small class="text-muted">近 12 个月 · 各月总产量 (pcs)</small>
          </div>
        </header>
        <div class="section-body no-pad">
          <div id="chart-output" v-loading="loading" class="chart-container"></div>
        </div>
      </section>
    </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { devicesApi, productionApi } from '@/api'
import StatCard from '@/components/common/StatCard.vue'
import { createPresentation, addFullImageSlide, savePresentation, captureElement } from '@/utils/pptExport'

const router = useRouter()
// 点击「设备总数」卡片跳转设备管理页（替代原顶栏“进入管理”按钮）
const goDevices = () => router.push('/devices')

const summary = ref({ total_output: 0, total_qualified: 0, yield_rate: 0, months: 0 })
const trend   = ref([])
// 看板口径的“本月”：优先当前自然月（周报实时聚合），当月尚无数据时回退最新有数据的月份
const boardMonth = ref(null)
const exporting = ref(false)
// loading 既是 loading 遮罩的响应式状态，也是防止轮询与手动刷新并发的锁
const loading = ref(false)

const stats = reactive({ total: 0, normal: 0, fault: 0, maintenance: 0 })

// 设备可用率：只统计"参与生产的设备"（正常 + 故障），保养中的设备不参与
// 例：13 台设备（10 正常 / 0 故障 / 3 保养）→ 10/10 = 100%，符合直觉
const availability = computed(() => {
  const active = stats.normal + stats.fault
  return active ? (stats.normal / active * 100).toFixed(1) : '0.0'
})

// 设备可用率配色：≥95 绿 / ≥85 黄 / 其余红
const availabilityColor = computed(() => {
  const v = parseFloat(availability.value)
  if (v >= 95) return 'green'
  if (v >= 85) return 'yellow'
  return 'red'
})

// 本月直通率配色：≥95 绿 / ≥90 蓝 / ≥80 黄 / 其余红
const yieldColor = computed(() => {
  const v = Number(latestYield.value)
  if (isNaN(v)) return 'blue'
  if (v >= 95) return 'green'
  if (v >= 90) return 'blue'
  if (v >= 80) return 'yellow'
  return 'red'
})

// 当月无数据时，标签诚实展示实际月份；避免“本月产量”实际是 8 月数据的口径误导
const outputLabel = computed(() => {
  if (!boardMonth.value) return '本月产量'
  const cur = new Date().getMonth() + 1
  const m = Number(boardMonth.value.month)
  return m === cur ? '本月产量' : `${m}月产量`
})
const yieldLabel = computed(() => {
  if (!boardMonth.value) return '本月直通率'
  const cur = new Date().getMonth() + 1
  const m = Number(boardMonth.value.month)
  return m === cur ? '本月直通率' : `${m}月直通率`
})

const latestOutput = computed(() => boardMonth.value ? (boardMonth.value.total_output || 0).toLocaleString() : '0')
const latestYield = computed(() => {
  const v = boardMonth.value?.yield_rate
  return (v === null || v === undefined) ? '—' : v
})

// 本月直通率 vs 年均的差值：正数=本月好于年均，负数=本月差于年均
const yieldDelta = computed(() => {
  const cur = Number(latestYield.value) || 0
  const avg = Number(summary.value.yield_rate) || 0
  return cur - avg
})

let chartYield = null, chartOutput = null
const resizeCharts = () => {
  chartYield && chartYield.resize()
  chartOutput && chartOutput.resize()
}

const loadData = async () => {
  if (loading.value) return
  loading.value = true
  try {
    await doLoadData()
  } finally {
    loading.value = false
  }
}

const doLoadData = async () => {
  const [devResult, trendResult] = await Promise.allSettled([
    devicesApi.list({ page_size: 100 }),
    productionApi.monthlyTrend(),
  ])

  // 设备数据
  if (devResult.status === 'fulfilled') {
    const devRes = devResult.value
    const list = devRes?.data?.items || []
    stats.total = list.length
    stats.normal = list.filter(d => d.status === '正常').length
    stats.fault = list.filter(d => d.status === '故障').length
    stats.maintenance = list.filter(d => d.status === '保养中').length
  } else {
    console.error('[AOI Dashboard] devices API failed:', devResult.reason)
  }

  // 月度趋势（后端直接由周报实时聚合：动态月份、最多12个月，新增周报后立即可见）
  if (trendResult.status === 'fulfilled') {
    const payload = trendResult.value?.data || {}
    trend.value = payload.items || []
    // 优先用后端按年汇总的年累/年均；兼容旧结构时前端兜底计算
    if (payload.summary) {
      summary.value = {
        total_output: payload.summary.total_output || 0,
        total_qualified: payload.summary.total_qualified || 0,
        yield_rate: payload.summary.yield_rate || 0,
        months: payload.summary.months || trend.value.length,
      }
    } else {
      const tot_out  = trend.value.reduce((s, d) => s + (d.total_output || 0), 0)
      const tot_qual = trend.value.reduce((s, d) => s + (d.total_qualified || 0), 0)
      summary.value = {
        total_output: tot_out,
        total_qualified: tot_qual,
        yield_rate: tot_out ? (tot_qual / tot_out * 100).toFixed(2) : 0,
        months: trend.value.length,
      }
    }
    // 本月：当前自然月有数据则取当月，否则回退最新月份
    boardMonth.value = payload.current_month || payload.latest_month ||
      (trend.value.length ? trend.value[trend.value.length - 1] : null)
  } else {
    console.error('[AOI Dashboard] monthlyTrend API failed:', trendResult.reason)
  }

  await nextTick()
  renderCharts()
}

const renderCharts = () => {
  const trendData = trend.value || []
  // 12 个月窗口可能跨年，跨年时 X 轴标签加年份（如 25/9），避免两个“9月”无法区分
  const years = new Set(trendData.map(d => d.year))
  const labels = trendData.map(d => years.size > 1 ? `${String(d.year).slice(2)}/${d.month}` : `${d.month}月`)

  // ===== 直通率折线 =====
  if (chartYield) chartYield.dispose()
  chartYield = echarts.init(document.getElementById('chart-yield'))
  chartYield.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (ps) => {
        const d = trendData[ps[0].dataIndex]
        if (!d) return ''
        return `${d.year}年${d.month}月<br/>直通率: <b>${d.yield_rate}%</b><br/>合格: ${(d.total_qualified || 0).toLocaleString()}`
      },
      axisPointer: { type: 'line', lineStyle: { color: '#2C5CE8', type: 'dashed' } },
    },
    grid: { left: 56, right: 28, top: 40, bottom: 36 },
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: labels,
      axisLine: { lineStyle: { color: '#D8DEEA' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value', min: 0, max: 100,
      axisLabel: { formatter: '{value}%', margin: 12 },
      splitLine: { lineStyle: { color: '#F0F2F7' } },
    },
    series: [{
      type: 'line', name: '直通率',
      symbol: 'circle', symbolSize: 9, smooth: false,
      lineStyle: { width: 3, color: '#10B981' },
      itemStyle: { color: '#10B981', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(16,185,129,0.26)' },
          { offset: 1, color: 'rgba(16,185,129,0.04)' },
        ]),
      },
      label: { show: true, position: 'top', formatter: '{c}%', fontSize: 11, color: '#10B981', fontWeight: 600 },
      labelLayout: { moveOverlap: 'shiftY', dx: 3, dy: 4 },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#F59E0B', type: 'dashed', width: 1.5 },
        label: {
          show: true,
          position: 'end',
          formatter: '目标 95%',
          color: '#F59E0B',
          fontSize: 11,
          fontWeight: 600,
        },
        data: [{ yAxis: 95 }],
      },
      data: trendData.map(d => d.yield_rate),
    }],
  })

  // ===== 产量柱状（最新月份高亮） =====
  if (chartOutput) chartOutput.dispose()
  chartOutput = echarts.init(document.getElementById('chart-output'))
  const lastIdx = trendData.length - 1
  chartOutput.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (ps) => {
        const d = trendData[ps[0].dataIndex]
        if (!d) return ''
        return `${d.year}年${d.month}月<br/>总产量: <b>${(d.total_output || 0).toLocaleString()}</b> pcs<br/>合格: ${(d.total_qualified || 0).toLocaleString()} pcs`
      },
    },
    grid: { left: 56, right: 28, top: 40, bottom: 36 },
    xAxis: {
      type: 'category', boundaryGap: true,
      data: labels,
      axisLine: { lineStyle: { color: '#D8DEEA' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F0F2F7' } },
      axisLabel: { fontSize: 11 },
    },
    series: [{
      type: 'bar', name: '产量', barWidth: '44%',
      itemStyle: { borderRadius: [6, 6, 0, 0] },
      label: {
        show: true, position: 'top', fontSize: 11, color: '#2C5CE8', fontWeight: 600,
        formatter: (p) => Number(p.value).toLocaleString(),
      },
      data: trendData.map((d, i) => ({
        value: d.total_output,
        itemStyle: i === lastIdx
          ? {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#3B82F6' },
                { offset: 1, color: '#1D4ED8' },
              ]),
            }
          : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#BFDBFE' },
                { offset: 1, color: '#93C5FD' },
              ]),
            },
      })),
    }],
  })
}

// 实时性：每 60 秒自动轮询；页面从后台切回前台时立即刷新一次
const REFRESH_INTERVAL = 60 * 1000
let refreshTimer = null
const onVisible = () => {
  if (!document.hidden) loadData()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', resizeCharts)
  document.addEventListener('visibilitychange', onVisible)
  refreshTimer = setInterval(loadData, REFRESH_INTERVAL)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  document.removeEventListener('visibilitychange', onVisible)
  if (refreshTimer) clearInterval(refreshTimer)
  chartYield && chartYield.dispose()
  chartOutput && chartOutput.dispose()
})

// 导出PPT：整屏看板截图，仅一页
const exportPPT = async () => {
  exporting.value = true
  try {
    // 操作按钮已移至全局顶栏（不在看板截图范围内），无需再临时隐藏
    const boardImg = await captureElement('aoi-board')
    const pptx = createPresentation('AOI&AI 设备监控看板')
    addFullImageSlide(pptx, boardImg)
    const date = new Date().toISOString().slice(0, 10)
    savePresentation(pptx, `AOI设备监控看板_${date}.pptx`)
  } catch (error) {
    console.error('导出PPT失败:', error)
    alert('导出PPT失败，请重试')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
/* 一屏驾驶舱：看板撑满内容区，KPI + 图表两行弹性自适应视口高度，无页面级滚动 */
.page {
  height: 100%;
  overflow: hidden;
}
.cockpit {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: var(--gap-block);
}
/* 覆盖全局 chart-card 固定最小高，让图表随单元格弹性伸缩 */
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

/* ============ KPI 副标题配色 ============ */
.kpi-sub {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.kpi-sub .kpi-ok   { color: #059669; font-weight: 700; }
.kpi-sub .kpi-bad  { color: #DC2626; font-weight: 700; }
.kpi-sub .kpi-mute { color: #94A3B8; font-weight: 700; }
.kpi-sub .kpi-sep  { color: #CBD5E1; margin: 0 3px; }
.kpi-sub .kpi-up   { color: #059669; font-weight: 700; margin-left: 6px; }
.kpi-sub .kpi-down { color: #DC2626; font-weight: 700; margin-left: 6px; }

/* ============ 图标容器立体化：渐变 + 内高光 + 外光晕 ============ */
/* 覆盖 StatCard 内部图标容器，让它从"贴图色块"变成"立体徽章" */
.stat-grid :deep(.stat-card .icon-box) {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 顶部内高光 + 底部彩色投影，营造立体感 */
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -2px 6px rgba(0, 0, 0, 0.08),
    0 10px 22px -10px var(--icon-glow, rgba(37, 99, 235, 0.5));
}

/* 图标本身：白 + 轻微投影，与渐变底色形成对比 */
.stat-grid :deep(.stat-card .icon-box span) {
  color: #fff !important;
  font-size: 30px;
  line-height: 1;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.18));
}

/* 外部柔光：容器外一圈半径柔化的光晕，让图标"浮"起来 */
.stat-grid :deep(.stat-card .icon-box::after) {
  content: '';
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--icon-glow, rgba(37, 99, 235, 0.45)) 0%, transparent 68%);
  opacity: 0.55;
  z-index: -1;
  pointer-events: none;
}

/* ============ 数字收紧：视觉权重和图标对等 ============ */
.stat-grid :deep(.stat-card .num) {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -1.5px;
  line-height: 1.1;
}

/* ============ 按 color 配置渐变 + 光晕色 ============ */
.stat-grid :deep(.stat-card[data-color="blue"]),
.stat-grid :deep(.stat-card.color-blue) {
  --icon-c1: #60A5FA;
  --icon-c2: #2563EB;
  --icon-glow: rgba(37, 99, 235, 0.5);
}
.stat-grid :deep(.stat-card[data-color="green"]),
.stat-grid :deep(.stat-card.color-green) {
  --icon-c1: #34D399;
  --icon-c2: #059669;
  --icon-glow: rgba(5, 150, 105, 0.5);
}
.stat-grid :deep(.stat-card[data-color="yellow"]),
.stat-grid :deep(.stat-card.color-yellow) {
  --icon-c1: #FBBF24;
  --icon-c2: #D97706;
  --icon-glow: rgba(217, 119, 6, 0.5);
}
.stat-grid :deep(.stat-card[data-color="red"]),
.stat-grid :deep(.stat-card.color-red) {
  --icon-c1: #F87171;
  --icon-c2: #DC2626;
  --icon-glow: rgba(220, 38, 38, 0.5);
}
.stat-grid :deep(.stat-card[data-color="purple"]),
.stat-grid :deep(.stat-card.color-purple) {
  --icon-c1: #A78BFA;
  --icon-c2: #7C3AED;
  --icon-glow: rgba(124, 58, 237, 0.5);
}

/* 图标容器背景：跟随 color 变量渐变 */
.stat-grid :deep(.stat-card .icon-box) {
  background: linear-gradient(135deg,
    var(--icon-c1, #60A5FA) 0%,
    var(--icon-c2, #2563EB) 100%);
}
</style>