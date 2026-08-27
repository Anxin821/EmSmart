<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">
          <span class="emoji">🖥️</span>AOI&AI 设备监控看板
        </h1>
        <div class="page-sub">设备运行状态、产线分布与产量直通率总览</div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-secondary" @click="loadData">
          <span class="bi bi-arrow-clockwise"></span>刷新
        </button>
        <router-link class="btn btn-sm btn-primary" to="/devices">
          <span class="bi bi-arrow-right"></span>进入管理
        </router-link>
      </div>
    </div>

    <!-- 顶部 4 张设备统计卡 -->
    <div class="stat-grid">
      <div class="stat-card blue">
        <div class="icon-box"><span class="bi bi-pc-display-fill"></span></div>
        <div class="num">{{ stats.total }}</div>
        <div class="label">设备总数</div>
      </div>
      <div class="stat-card green">
        <div class="icon-box"><span class="bi bi-check-circle-fill"></span></div>
        <div class="num">{{ stats.normal }}</div>
        <div class="label">正常运行</div>
      </div>
      <div class="stat-card red">
        <div class="icon-box"><span class="bi bi-exclamation-triangle-fill"></span></div>
        <div class="num">{{ stats.fault }}</div>
        <div class="label">故障设备</div>
      </div>
      <div class="stat-card yellow">
        <div class="icon-box"><span class="bi bi-wrench-adjustable"></span></div>
        <div class="num">{{ stats.maintenance }}</div>
        <div class="label">保养中</div>
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

    <!-- 近四周数据快照 + 产线设备位置 -->
    <div class="card-grid-2">
      <!-- 近四周数据快照 -->
      <section class="page-section">
        <header class="section-head">
          <h2 class="sec-title">近四周数据快照</h2>
          <div class="sec-actions">
            <small class="text-muted">按产量排序</small>
          </div>
        </header>
        <div class="section-body no-pad table-wrap">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>产线</th><th>项目</th><th>产量</th><th>合格数</th><th>直通率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in recentWeeks" :key="idx">
                <td>{{ row.production_line }}</td>
                <td>{{ row.project }}</td>
                <td>{{ row.total_output?.toLocaleString() }}</td>
                <td>{{ row.qualified_count?.toLocaleString() }}</td>
                <td>
                  <span v-if="row.yield_rate" class="rate-num" :style="{ color: row.yield_rate >= 90 ? '#10B981' : row.yield_rate >= 80 ? '#F59E0B' : '#EF4444' }">
                    {{ row.yield_rate }}%
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
              <tr v-if="!recentWeeks.length">
                <td colspan="5"><div class="empty-state"><span class="big-emoji">📭</span>暂无数据</div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 产线设备位置 -->
      <section class="page-section">
        <header class="section-head">
          <h2 class="sec-title">产线设备位置</h2>
          <div class="sec-actions">
            <small class="text-muted">按线体分组</small>
          </div>
        </header>
        <div class="section-body no-pad">
          <div class="device-grid">
            <div v-for="group in lineGroups" :key="group.line" class="device-line-group">
              <div class="device-line-title">
                <span class="line-dot" :style="{ background: group.color }"></span>
                {{ group.line }}
                <span class="line-count">({{ group.devices.length }})</span>
              </div>
              <div class="device-tags" v-if="group.devices.length">
                <template v-for="dev in group.devices" :key="dev.id">
                  <span class="device-tag" :class="getStatusClass(dev.status)" :title="`${dev.name} · ${dev.status}`">
                    {{ dev.device_type }}-{{ dev.name }}
                  </span>
                </template>
              </div>
              <div v-else class="text-muted small">暂无设备</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { devicesApi, productionApi } from '@/api'

const devices = ref([])
const summary = ref({ total_output: 0, total_qualified: 0, yield_rate: 0, months: 0 })
const trend   = ref([])
const recentWeeks = ref([])

const stats = reactive({ total: 0, normal: 0, fault: 0, maintenance: 0 })

const lineColors = ['#2C5CE8', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#EC4899', '#84CC16']
const lineGroups = computed(() => {
  const map = {}
  devices.value.forEach(d => {
    const line = d.production_line || '未分配'
    if (!map[line]) map[line] = { line, devices: [] }
    map[line].devices.push(d)
  })
  return Object.values(map).map((g, i) => ({
    ...g,
    color: lineColors[i % lineColors.length],
  })).sort((a, b) => {
    const na = parseInt(a.line) || 99, nb = parseInt(b.line) || 99
    return na - nb
  })
})

const getStatusClass = (status) => {
  const map = { '正常': 'normal', '故障': 'fault', '保养中': 'warn' }
  return map[status] || 'muted'
}

let chartYield = null, chartOutput = null
const resizeCharts = () => {
  chartYield && chartYield.resize()
  chartOutput && chartOutput.resize()
}

const loadData = async () => {
  const [devResult, trendResult, weekResult] = await Promise.allSettled([
    devicesApi.list({ page_size: 100 }),
    productionApi.monthlyTrend(),
    productionApi.weekly({ page_size: 100 }),
  ])

  // 设备数据
  if (devResult.status === 'fulfilled') {
    const devRes = devResult.value
    const list = devRes?.data?.items || []
    devices.value = list
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

  // 周报数据
  if (weekResult.status === 'fulfilled') {
    const weekRes = weekResult.value
    const weeks = weekRes?.data?.items || []
    recentWeeks.value = weeks
      .sort((a, b) => (b.week_number || 0) - (a.week_number || 0))
      .slice(0, 40)
      .sort((a, b) => (b.total_output || 0) - (a.total_output || 0))
      .slice(0, 10)
  } else {
    console.error('[AOI Dashboard] weekly API failed:', weekResult.reason)
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
</script>

<style scoped>
.device-grid {
  display: flex; flex-direction: column; gap: 12px;
  padding: 4px 4px 10px;
}
.device-line-group {
  background: #F8FAFC;
  border-radius: 10px;
  padding: 10px 12px;
  border: 1px solid #F1F5F9;
}
.device-line-title {
  font-weight: 600;
  font-size: 13.5px;
  color: #0F172A;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.line-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.line-count {
  color: #64748B;
  font-weight: 400;
  font-size: 12.5px;
}
.device-tags {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.device-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 500;
  background: #EFF6FF;
  color: #1D4ED8;
  border: 1px solid #DBEAFE;
  transition: transform .12s ease;
}
.device-tag:hover { transform: translateY(-1px); }
.device-tag.normal { background: #ECFDF5; color: #047857; border-color: #D1FAE5; }
.device-tag.fault  { background: #FEF2F2; color: #B91C1C; border-color: #FEE2E2; }
.device-tag.warn   { background: #FFFBEB; color: #B45309; border-color: #FEF3C7; }
.device-tag.muted  { background: #F1F5F9; color: #64748B; border-color: #E2E8F0; }
.rate-num { font-weight: 600; }
</style>
