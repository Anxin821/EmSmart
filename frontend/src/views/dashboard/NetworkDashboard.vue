<template>
  <div id="page-container" class="page">
    <!-- 操作按钮通过 Teleport 注入全局顶栏左侧空白区，不占用看板纵向空间 -->
    <Teleport defer to=".topbar-actions">
      <button class="btn btn-sm btn-outline-warning" @click="handleCheckAll">
        <span class="bi bi-lightning-charge"></span>一键检测
      </button>
    </Teleport>

    <!-- 顶部统计 + 仪表盘 -->
    <div class="top-section">
      <div class="stat-pair">
        <StatCard
          class="net-stat net-online"
          color="green"
          icon="bi bi-broadcast-pin"
          :num="data?.online_devices ?? 0"
          label="全局在线设备"
        />
        <StatCard
          class="net-stat net-offline"
          color="red"
          icon="bi bi-wifi-off"
          :num="data?.offline_devices ?? 0"
          label="全局离线设备"
        />
      </div>
      <div class="gauge-wrapper">
        <div id="gauge" class="gauge"></div>
      </div>
    </div>

    <!-- 底部：拓扑 + 离线列表 -->
    <div class="bottom-section">
      <section class="topology-card">
        <header class="section-head">
          <h2 class="sec-title">按线体网络健康度</h2>
          <span class="card-subtitle">{{ activeLines.length }} 条线体在网 | 共 {{ data?.total_devices ?? 0 }} 台设备</span>
        </header>
        <div class="health-grid">
          <div
            v-for="ls in activeLines"
            :key="ls.line"
            class="line-health"
            :class="'lv-' + ls.level"
          >
            <div class="lh-top">
              <span class="lh-name">{{ ls.line }}</span>
              <span class="lh-pill">
                <template v-if="ls.level === 'ok'"><span class="bi bi-check-circle-fill"></span>全部正常</template>
                <template v-else><span class="bi bi-exclamation-triangle-fill"></span>异常 {{ ls.offline }} 台</template>
              </span>
            </div>

            <div class="lh-metric">
              <span class="lh-rate">{{ ls.rate }}<small>%</small></span>
              <span class="lh-frac">在线 <b>{{ ls.online }}</b> / {{ ls.total }} 台</span>
            </div>

            <div class="lh-bar"><i :style="{ width: ls.rate + '%' }"></i></div>

            <div class="lh-types">
              <span class="lh-chip" :class="{ off: ls.servers.off }">
                <span class="bi bi-server"></span>服务器 {{ ls.servers.total }}<em v-if="ls.servers.off">-{{ ls.servers.off }}</em>
              </span>
              <span class="lh-chip" :class="{ off: ls.racks.off }">
                <span class="bi bi-box-seam"></span>老化架 {{ ls.racks.total }}<em v-if="ls.racks.off">-{{ ls.racks.off }}</em>
              </span>
              <span class="lh-chip" :class="{ off: ls.aps.off }">
                <span class="bi bi-router"></span>AP {{ ls.aps.total }}<em v-if="ls.aps.off">-{{ ls.aps.off }}</em>
              </span>
            </div>
          </div>

          <div v-if="!activeLines.length" class="lh-empty">
            <span class="bi bi-inbox"></span>暂无线体设备数据
          </div>
        </div>
      </section>

      <section class="offline-card">
        <header class="section-head">
          <h2 class="sec-title">离线设备列表</h2>
          <span class="badge" :class="data?.offline_list?.length ? 'badge-danger' : 'badge-success'">
            {{ data?.offline_list?.length || 0 }}
          </span>
        </header>
        <div class="offline-body">
          <div v-if="!data" class="empty-state">加载中…</div>
          <div v-else-if="!data.offline_list?.length" class="all-ok">
            <span class="bi bi-check-circle-fill" style="color: var(--ok); font-size: 22px;"></span>
            <span>所有设备正常</span>
          </div>
          <div v-else class="offline-list">
            <div v-for="(item, idx) in data.offline_list" :key="idx" class="offline-item">
              <span class="offline-type" :class="typeClass(item.type)">{{ item.type }}</span>
              <span class="offline-name">{{ item.name }}</span>
              <span class="offline-line">{{ item.line }}</span>
              <span class="offline-status">{{ item.status }}</span>
              <span class="offline-ip">{{ item.ip }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi, networkApi } from '@/api'
import StatCard from '@/components/common/StatCard.vue'

const data = ref(null)
let gaugeChart = null

// 每条线体的健康概览：在线/总数、健康率、状态级别、三类设备各自离线数
// —— 汇报视角：弱化单个设备名，突出“哪条线体有问题、异常几台”（离线明细仍在右侧列表可查）
const activeLines = computed(() =>
  (data.value?.lines ?? [])
    .map((line) => {
      const servers = line.servers ?? []
      const racks   = line.aging_racks ?? []
      const aps     = line.wifi_aps ?? []
      const sOff = servers.filter(s => s.status !== '在线').length
      const rOff = racks.filter(a => a.status !== '正常').length
      const aOff = aps.filter(ap => ap.status !== '在线').length
      const total   = servers.length + racks.length + aps.length
      const offline = sOff + rOff + aOff
      const online  = total - offline
      const rate    = total ? Math.round(online / total * 100) : 0
      let level = 'empty'
      if (total > 0) level = offline === 0 ? 'ok' : (rate >= 70 ? 'warn' : 'danger')
      return {
        line: line.line, total, online, offline, rate, level,
        servers: { total: servers.length, off: sOff },
        racks:   { total: racks.length,   off: rOff },
        aps:     { total: aps.length,     off: aOff },
      }
    })
    .filter(ls => ls.total > 0)
)

const typeClass = (type) => {
  if (type === '服务器') return 'type-server'
  if (type === '老化架') return 'type-aging'
  if (type === 'WiFi AP') return 'type-ap'
  return ''
}

const loadData = async () => {
  try {
    const res = await dashboardApi.network()
    data.value = res.data || null
    await nextTick()
    renderGauge()
  } catch (e) {
    console.error(e)
  }
}

const renderGauge = () => {
  const rate = data.value?.online_rate ?? 0
  // 阈值配色：≥90 绿 / ≥70 黄 / 其余红，与健康卡状态色统一
  const rateColor = rate >= 90 ? '#10B981' : (rate >= 70 ? '#F59E0B' : '#EF4444')
  if (gaugeChart) gaugeChart.dispose()
  gaugeChart = echarts.init(document.getElementById('gauge'))

  // 简洁环形进度：去掉刻度/锚点/指针，只保留进度环 + 中心超大在线率数字
  gaugeChart.setOption({
    series: [ {
      type: 'gauge',
      startAngle: 90,
      endAngle: -270,
      min: 0,
      max: 100,
      radius: '88%',
      center: ['50%', '52%'],
      pointer: { show: false },
      progress: {
        show: true,
        overlap: false,
        roundCap: true,
        clip: false,
        width: 16,
        itemStyle: { color: rateColor },
      },
      axisLine: { lineStyle: { width: 16, color: [[1, '#EEF2F7']] } },
      splitLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      anchor: { show: false },
      title: {
        show: true,
        offsetCenter: [0, '34%'],
        fontSize: 15,
        fontWeight: 600,
        color: '#6B7280',
      },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '-2%'],
        fontSize: 44,
        fontWeight: 800,
        formatter: '{value}%',
        color: rateColor,
      },
      data: [{ value: rate, name: '设备在线率' }],
    } ],
  })
}

const handleCheckAll = async () => {
  try {
    await networkApi.checkAll()
    loadData()
  } catch (e) {
    console.error(e)
  }
}

const resize = () => {
  gaugeChart && gaugeChart.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  gaugeChart && gaugeChart.dispose()
})
</script>

<style scoped>
.page {
  /* 关键：全局 .page 为 height:100vh，但看板实际渲染在 .content（已扣除顶栏+内边距）内，
     100vh 会超出内容区被 overflow:hidden 裁掉底部。改为 height:100% 贴合内容区，杜绝裁切。 */
  height: 100%;
  padding: 0px 24px;
  box-sizing: border-box;
}

/* ---- 顶部统计区 ---- */
.top-section {
  display: flex;
  gap: 16px;
  margin-bottom: 5px;  /* 👈 减小底部外边距：从16px→12px */
  margin-top: 1px;     /* 👈 添加顶部外边距：增加12px */
  margin-left: -8px;    /* 👈 减小左侧外边距：从0→-8px */
  margin-right: -8px;   /* 👈 减小右侧外边距：从0→-8px */
  align-items: stretch;
  height: 180px;
  flex-shrink: 0;
}

.stat-pair {
  display: flex;
  gap: 14px;
  flex: 1;
}
/* KPI 卡统一走 StatCard 组件；以下为汇报场景对这两张 hero 卡的视觉强化 */
.stat-pair .stat-card {
  flex: 1;
  min-width: 0;
  position: relative;
  padding: 16px 20px;
  border-radius: 16px;
  /* 居中堆叠：单列网格，图标 → 数字 → 标签 → 占比 全部水平+垂直居中 */
  grid-template-columns: 1fr;
  justify-items: center;
  align-content: center;
  row-gap: 6px;
  text-align: center;
  overflow: hidden;
}
/* 左侧主题色竖条：一眼区分在线/离线 */
.stat-pair .net-stat::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  z-index: 2;
}
.net-online::before  { background: linear-gradient(180deg, #34D399, #059669); }
.net-offline::before { background: linear-gradient(180deg, #F87171, #DC2626); }
/* 卡片底色：主题色淡渐变 → 白，比纯白更有层次 */
.stat-pair .net-online {
  background: linear-gradient(135deg, #ECFDF5 0%, #FFFFFF 62%) !important;
  border-color: rgba(16, 185, 129, .26) !important;
  box-shadow: 0 6px 18px -8px rgba(16, 185, 129, .35) !important;
}
.stat-pair .net-offline {
  background: linear-gradient(135deg, #FEF2F2 0%, #FFFFFF 62%) !important;
  border-color: rgba(239, 68, 68, .26) !important;
  box-shadow: 0 6px 18px -8px rgba(239, 68, 68, .35) !important;
}
/* 图标徽章：圆角实底 + 白色图标 + 主题色投影 */
.stat-pair .net-stat :deep(.icon-box) {
  grid-row: auto; grid-column: 1;   /* 取消全局 1/span2 左栏定位，改为堆叠首行居中 */
  width: 52px; height: 52px;
  border-radius: 15px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 2px;
}
.net-online  :deep(.icon-box) { background: linear-gradient(135deg, #10B981, #059669); box-shadow: 0 8px 18px -6px rgba(16, 185, 129, .6); }
.net-offline :deep(.icon-box) { background: linear-gradient(135deg, #EF4444, #DC2626); box-shadow: 0 8px 18px -6px rgba(239, 68, 68, .6); }
.stat-pair .net-stat :deep(.icon-box span) { color: #fff !important; font-size: 28px; }
/* 超大主题色数字：单列居中，去掉避让 delta 的右 padding */
.net-online  :deep(.num) { grid-column: 1; padding-right: 0; text-align: center; color: #059669; font-size: 44px; font-weight: 800; line-height: 1; letter-spacing: -1px; }
.net-offline :deep(.num) { grid-column: 1; padding-right: 0; text-align: center; color: #DC2626; font-size: 44px; font-weight: 800; line-height: 1; letter-spacing: -1px; }
.stat-pair .net-stat :deep(.label) { grid-column: 1; padding-right: 0; text-align: center; font-size: 15px; font-weight: 600; color: var(--c-text-2); letter-spacing: .3px; }

.gauge-wrapper {
  width: 320px;
  height: 100%;
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--c-divider);
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
  display: flex;
  align-items: center;
  justify-content: center;
}

.gauge {
  width: 100%;
  height: 100%;
}

/* ---- 底部区 ---- */
.bottom-section {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.topology-card {
  flex: 1.4;
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--c-divider);
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.offline-card {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--c-divider);
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-head {
  position: relative;
  padding: 12px 16px;
  border-bottom: 1px solid var(--c-divider);
  display: flex;
  justify-content: center;   /* 标题居中 */
  align-items: center;
}

.sec-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text);
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-subtitle {
  position: absolute;   /* 靠右，不占中间标题的居中位 */
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: var(--c-text-3);
  font-weight: 400;
}

/* ---- 线体健康概览卡 ---- */
.health-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 14px 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  align-content: start;
}
@media (max-width: 1200px) { .health-grid { grid-template-columns: repeat(2, 1fr); } }

.line-health {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 10px;
  padding: 14px 16px 13px;
  border: 1px solid var(--c-divider);
  border-radius: 12px;
  background: #fff;
  overflow: hidden;
  transition: transform .18s ease, box-shadow .18s ease;
}
.line-health:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px -12px rgba(15, 23, 42, .28);
}
/* 左侧状态色条 */
.line-health::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
}
/* 三档状态配色：绿=全部正常 / 黄=轻度异常 / 红=严重异常 */
.lv-ok::before     { background: #10B981; }
.lv-warn::before   { background: #F59E0B; }
.lv-danger::before { background: #EF4444; }
.lv-ok     { background: linear-gradient(135deg, #F0FDF4 0%, #fff 55%); border-color: rgba(16, 185, 129, .25); }
.lv-warn   { background: linear-gradient(135deg, #FFFBEB 0%, #fff 55%); border-color: rgba(245, 158, 11, .3); }
.lv-danger { background: linear-gradient(135deg, #FEF2F2 0%, #fff 55%); border-color: rgba(239, 68, 68, .32); }

.lh-top {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.lh-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text);
  letter-spacing: .3px;
}
.lh-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}
.lv-ok .lh-pill     { background: var(--ok-bg);   color: #059669; }
.lv-warn .lh-pill   { background: var(--warn-bg); color: #B45309; }
.lv-danger .lh-pill { background: var(--err-bg);  color: #DC2626; }

.lh-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.lh-rate {
  font-size: 34px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
}
.lh-rate small { font-size: 18px; font-weight: 700; margin-left: 1px; }
.lv-ok .lh-rate     { color: #059669; }
.lv-warn .lh-rate   { color: #D97706; }
.lv-danger .lh-rate { color: #DC2626; }
.lh-frac { font-size: 13px; color: var(--c-text-3); }
.lh-frac b { color: var(--c-text); font-size: 14px; }

.lh-bar {
  align-self: stretch;   /* 居中堆叠下仍保持进度条满宽，不塔缩 */
  height: 7px;
  border-radius: 999px;
  background: #EEF2F7;
  overflow: hidden;
}
.lh-bar i { display: block; height: 100%; border-radius: 999px; transition: width .5s ease; }
.lv-ok .lh-bar i     { background: linear-gradient(90deg, #34D399, #10B981); }
.lv-warn .lh-bar i   { background: linear-gradient(90deg, #FBBF24, #F59E0B); }
.lv-danger .lh-bar i { background: linear-gradient(90deg, #F87171, #EF4444); }

.lh-types { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; }
.lh-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--c-text-2);
  background: #F5F7FB;
  border: 1px solid var(--c-divider);
  border-radius: 7px;
  padding: 3px 8px;
}
.lh-chip .bi { font-size: 12px; color: var(--c-text-3); }
.lh-chip em { font-style: normal; font-weight: 700; color: #DC2626; }
.lh-chip.off { background: var(--err-bg); border-color: rgba(239, 68, 68, .3); }

.lh-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 0;
  color: var(--c-text-mute);
  font-size: 14px;
}
.lh-empty .bi { font-size: 32px; }

/* ---- 离线列表 ---- */
.offline-body {
  flex: 1;
  overflow: auto;
  padding: 12px 16px;
}

.empty-state {
  text-align: center;
  color: var(--c-text-mute);
  padding: 40px 0;
}

.all-ok {
  height: 100%;              /* 撑满 offline-body 内容区 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;   /* 垂直居中 */
  gap: 12px;
  color: var(--ok);
  font-size: 15px;
}

.offline-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.offline-item {
  display: grid;
  grid-template-columns: 56px 1fr 56px 48px 90px;
  gap: 8px;
  align-items: center;
  padding: 8px 10px;
  border-radius: 6px;
  background: #FFF5F5;
  border: 1px solid #FECACA;
  font-size: 12px;
}

.offline-type {
  font-weight: 600;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  text-align: center;
  white-space: nowrap;
}

.type-server { background: #DBEAFE; color: #1D4ED8; }
.type-aging  { background: #FEF3C7; color: #B45309; }
.type-ap     { background: #E0E7FF; color: #4338CA; }

.offline-name {
  color: var(--c-text);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.offline-line {
  color: var(--c-text-3);
  font-size: 11px;
  text-align: center;
}

.offline-status {
  color: var(--err);
  font-weight: 600;
  font-size: 11px;
  text-align: center;
}

.offline-ip {
  color: var(--c-text-3);
  font-size: 11px;
  font-family: monospace;
  text-align: right;
}

.badge {
  position: absolute;   /* 靠右，不占中间标题的居中位 */
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.badge-success {
  background: var(--ok-bg);
  color: var(--ok);
}

.badge-danger {
  background: var(--err-bg);
  color: var(--err);
}

/* 滚动条美化 */
.offline-body::-webkit-scrollbar { width: 6px; }
.offline-body::-webkit-scrollbar-thumb { background: #D8DEEA; border-radius: 4px; }
.offline-body::-webkit-scrollbar-track { background: transparent; }

.health-grid::-webkit-scrollbar { width: 6px; }
.health-grid::-webkit-scrollbar-thumb { background: #D8DEEA; border-radius: 4px; }
.health-grid::-webkit-scrollbar-track { background: transparent; }
</style>
