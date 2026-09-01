<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><span class="emoji">📋</span>MES 管理看板</h1>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-primary" @click="exportPPT" :disabled="exporting">
          <span class="bi" :class="exporting ? 'bi-hourglass-split' : 'bi-file-earmark-ppt'"></span>
          {{ exporting ? '导出中...' : '导出PPT' }}
        </button>
      </div>
    </div>

    <!-- 顶部 2 张大卡 -->
    <div class="stat-grid" style="grid-template-columns: repeat(2, minmax(0,1fr));">
      <div class="stat-card green-dash">
        <div class="num-big fix-rate">{{ data?.fix_rate ?? 0 }}<em>%</em></div>
        <div class="label">BUG修复率（已解决/全部）</div>
      </div>
      <div class="stat-card red-dash">
        <div class="num-big delivery-rate">{{ data?.delivery_rate ?? 0 }}<em>%</em></div>
        <div class="label">需求完成率（已上线/全部）</div>
      </div>
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
            <span class="dot bg-confirm"></span>确认新增
            <span class="dot bg-fixing"></span>修复中
            <span class="dot bg-closed"></span>解决关闭
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
            <span class="dot bg-assess"></span>收集评估
            <span class="dot bg-testing"></span>开发测试中
            <span class="dot bg-online"></span>上线
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
        <div class="section-body" style="padding: 8px 22px 22px;">
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
        <div class="section-body" style="padding: 8px 22px 22px;">
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
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { mesApi } from '@/api'
import { createPresentation, addTitleSlide, addStatsSlide, addChartSlide, addTableSlide, savePresentation, captureElement, colorMap } from '@/utils/pptExport'

const data = ref(null)
const exporting = ref(false)
let cBugs = null, cReqs = null

const resize = () => {
  cBugs && cBugs.resize()
  cReqs && cReqs.resize()
}

const loadData = async () => {
  try {
    const res = await mesApi.dashboard()
    data.value = res.data || null
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

const handleExportPPT = () => {
  alert('PPT 导出：请在浏览器打印对话框中选择「另存为 PDF」再转 PPT，或等待后端实现（后续迭代）。')
}

// 导出PPT
const exportPPT = async () => {
  exporting.value = true
  try {
    const pptx = createPresentation('MES 管理看板')
    
    // 1. 标题页
    addTitleSlide(pptx, 'MES 管理看板', 'BUG修复率与需求完成率统计')
    
    // 2. 统计指标页
    addStatsSlide(pptx, '核心指标', [
      { label: 'BUG修复率', value: `${data.value?.fix_rate ?? 0}%`, color: colorMap.green },
      { label: '需求完成率', value: `${data.value?.delivery_rate ?? 0}%`, color: colorMap.red }
    ])
    
    // 3. BUG月度图表
    const bugsChart = await captureElement('chart-bugs')
    if (bugsChart) {
      addChartSlide(pptx, 'BUG 月度状态分布', bugsChart)
    }
    
    // 4. 需求月度图表
    const reqsChart = await captureElement('chart-reqs')
    if (reqsChart) {
      addChartSlide(pptx, '需求月度状态分布', reqsChart)
    }
    
    // 5. 风险列表
    if (data.value?.risks?.length > 0) {
      const headers = ['类型', '描述', '数量']
      const rows = data.value.risks.map(r => [
        r.label || '-',
        r.items?.join('、') || '-',
        `${r.value} ${r.unit || ''}`
      ])
      addTableSlide(pptx, '阻塞与风险归因', headers, rows)
    }
    
    // 6. 里程碑
    if (data.value?.milestones) {
      const ms = data.value.milestones
      const headers = ['里程碑', '需求数量', '需求列表']
      const rows = [[
        ms.label || '本月里程碑',
        `${ms.count || 0} 个`,
        ms.items?.join('、') || '-'
      ]]
      addTableSlide(pptx, '本月里程碑 & 下月承诺', headers, rows)
    }
    
    // 保存文件
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
/* 顶部两张超大卡 */
.stat-card.green-dash, .stat-card.red-dash {
  padding: 26px 30px 24px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #E6E9F0;
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
  text-align: center;
}
.stat-card .num-big {
  font-size: 46px;
  font-weight: 700;
  line-height: 1.1;
  margin-top: 6px;
  letter-spacing: -0.5px;
}
.stat-card .num-big em {
  font-size: 22px;
  font-weight: 600;
  font-style: normal;
  margin-left: 2px;
}
.fix-rate       { color: #10B981; }
.delivery-rate  { color: #EF4444; }
.stat-card .label {
  margin-top: 8px;
  color: var(--muted, #6B7280);
  font-size: 13px;
}
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
  gap: 24px;
  padding: 2px 0 18px;
  font-size: 13px;
  color: #4B5563;
}
.chart-legend .dot {
  display: inline-block;
  width: 14px; height: 14px;
  border-radius: 3px;
  vertical-align: -3px;
  margin: 0 6px 0 0;
}
.bg-confirm { background: #EF4444; }
.bg-fixing  { background: #F59E0B; }
.bg-closed  { background: #10B981; }
.bg-assess  { background: #64748B; }
.bg-testing { background: #F97316; }
.bg-online  { background: #10B981; }

/* 风险 / 里程碑块 */
.risk-list { list-style: none; margin: 0; padding: 6px 0 0; }
.risk-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
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
  font-size: 15px; color: #111827; line-height: 1.7;
  display: flex; align-items: center; gap: 8px;
}
.ms-check {
  color: #10B981;
  font-size: 20px;
  font-weight: 700;
}
.ms-list {
  margin-top: 6px;
  padding: 10px 14px;
  background: #F7FAFF;
  border-left: 3px solid #2C5CE8;
  border-radius: 0 6px 6px 0;
  line-height: 1.7;
  font-size: 14px;
  color: #374151;
  max-height: 108px;
  overflow: auto;
}
.ms-list::-webkit-scrollbar-thumb { background: #D8DEEA; border-radius: 4px; }
.ms-list::-webkit-scrollbar      { width: 6px; }

/* 卡尺寸统一 */
.chart-container {
  width: 100%;
  height: 300px;
}
</style>
