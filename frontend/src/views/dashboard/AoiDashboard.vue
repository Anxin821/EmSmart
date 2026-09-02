<template>
  <div id="aoi-board" class="page">
    <div class="page-header">
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-primary" @click="exportPPT" :disabled="exporting">
          <span class="bi" :class="exporting ? 'bi-hourglass-split' : 'bi-file-earmark-ppt'"></span>
          {{ exporting ? '导出中...' : '导出PPT' }}
        </button>
        <router-link class="btn btn-sm btn-primary" to="/devices">
          <span class="bi bi-arrow-right"></span>进入管理
        </router-link>
      </div>
    </div>

    <div class="cockpit">
    <!-- KPI 指标：设备总数 / 可用率 / 本月产量 / 本月直通率 -->
    <div class="stat-grid">
      <div class="stat-card blue">
        <div class="icon-box"><span class="bi bi-pc-display-fill"></span></div>
        <div class="num">{{ stats.total }}</div>
        <div class="label">设备总数</div>
      </div>
      <div class="stat-card green">
        <div class="icon-box"><span class="bi bi-check-circle-fill"></span></div>
        <div class="num">{{ availability }}%</div>
        <div class="label">设备可用率（正常 {{ stats.normal }} / 故障 {{ stats.fault }}）</div>
      </div>
      <div class="stat-card purple">
        <div class="icon-box"><span class="bi bi-box-seam-fill"></span></div>
        <div class="num">{{ latestOutput }}</div>
        <div class="label">本月产量 · 年累 {{ summary.total_output.toLocaleString() }}</div>
      </div>
      <div class="stat-card yellow">
        <div class="icon-box"><span class="bi bi-bullseye"></span></div>
        <div class="num">{{ latestYield }}%</div>
        <div class="label">本月直通率 · 年均 {{ summary.yield_rate }}%</div>
      </div>
    </div>

    <!-- 图表:直通率折线 + 产量柱状 -->
    <div class="card-grid-2">
      <section class="page-section chart-card">
        <header class="section-head">
          <h2 class="sec-title">直通率</h2>
          <div class="sec-actions">
            <small class="text-muted">按月份趋势</small>
          </div>
        </header>
        <div class="section-body no-pad">
          <div id="chart-yield" class="chart-container"></div>
        </div>
      </section>

      <section class="page-section chart-card">
        <header class="section-head">
          <h2 class="sec-title">产量</h2>
          <div class="sec-actions">
            <small class="text-muted">各月总产量</small>
          </div>
        </header>
        <div class="section-body no-pad">
          <div id="chart-output" class="chart-container"></div>
        </div>
      </section>
    </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { devicesApi, productionApi } from '@/api'
import { createPresentation, addFullImageSlide, savePresentation, captureElement } from '@/utils/pptExport'

const summary = ref({ total_output: 0, total_qualified: 0, yield_rate: 0, months: 0 })
const trend   = ref([])
const exporting = ref(false)

const stats = reactive({ total: 0, normal: 0, fault: 0, maintenance: 0 })

// KPI 派生指标：设备可用率 / 本月产量 / 本月直通率（本月取月度趋势最后一项）
const availability = computed(() => stats.total ? (stats.normal / stats.total * 100).toFixed(1) : '0.0')
const latestMonth = computed(() => (trend.value && trend.value.length) ? trend.value[trend.value.length - 1] : null)
const latestOutput = computed(() => latestMonth.value ? (latestMonth.value.total_output || 0).toLocaleString() : '0')
const latestYield = computed(() => latestMonth.value ? (latestMonth.value.yield_rate || 0) : '0.00')

let chartYield = null, chartOutput = null
const resizeCharts = () => {
  chartYield && chartYield.resize()
  chartOutput && chartOutput.resize()
}

const loadData = async () => {
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

  // 月度趋势
  if (trendResult.status === 'fulfilled') {
    const trendRes = trendResult.value
    trend.value = trendRes?.data?.items || []
    const tot_out  = trend.value.reduce((s, d) => s + (d.total_output || 0), 0)
    const tot_qual = trend.value.reduce((s, d) => s + (d.total_qualified || 0), 0)
    summary.value = {
      total_output: tot_out,
      total_qualified: tot_qual,
      yield_rate: tot_out ? (tot_qual / tot_out * 100).toFixed(2) : 0,
      months: trend.value.length,
    }
  } else {
    console.error('[AOI Dashboard] monthlyTrend API failed:', trendResult.reason)
  }

  await nextTick()
  renderCharts()
}

const renderCharts = () => {
  const labels = (trend.value || []).map(d => `${d.month}月`)
  const trendData = trend.value || []

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
    grid: { left: 56, right: 28, top: 36, bottom: 36 },
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
      data: trendData.map(d => d.yield_rate),
    }],
  })

  if (chartOutput) chartOutput.dispose()
  chartOutput = echarts.init(document.getElementById('chart-output'))
  chartOutput.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (ps) => {
        const d = trendData[ps[0].dataIndex]
        if (!d) return ''
        return `${d.year}年${d.month}月<br/>总产量: <b>${(d.total_output || 0).toLocaleString()}</b><br/>合格: ${(d.total_qualified || 0).toLocaleString()}`
      },
    },
    grid: { left: 56, right: 28, top: 36, bottom: 36 },
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
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#5B83F0' },
          { offset: 1, color: '#2C5CE8' },
        ]),
        borderRadius: [6, 6, 0, 0],
      },
      label: {
        show: true, position: 'top', fontSize: 11, color: '#2C5CE8', fontWeight: 600,
        formatter: (p) => Number(p.value).toLocaleString(),
      },
      data: trendData.map(d => d.total_output),
    }],
  })
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', resizeCharts)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  chartYield && chartYield.dispose()
  chartOutput && chartOutput.dispose()
})

// 导出PPT：整屏看板截图，仅一页
const exportPPT = async () => {
  exporting.value = true
  const boardEl = document.getElementById('aoi-board')
  const headerEl = boardEl?.querySelector('.page-header')
  try {
    // 截图前临时隐藏右上角操作按钮，导出图更干净
    if (headerEl) headerEl.style.visibility = 'hidden'
    await new Promise(r => setTimeout(r, 60))
    const boardImg = await captureElement('aoi-board')
    const pptx = createPresentation('AOI&AI 设备监控看板')
    addFullImageSlide(pptx, boardImg)
    const date = new Date().toISOString().slice(0, 10)
    savePresentation(pptx, `AOI设备监控看板_${date}.pptx`)
  } catch (error) {
    console.error('导出PPT失败:', error)
    alert('导出PPT失败，请重试')
  } finally {
    if (headerEl) headerEl.style.visibility = ''
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
.page-header {
  justify-content: flex-end;
  padding: 10px var(--gap-block);
  margin-bottom: 12px;
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
/* KPI 卡副信息允许换行，避免被省略号截断 */
.cockpit .stat-card .label {
  padding-right: 0;
  white-space: normal;
  line-height: 1.4;
}
</style>
