<template>
  <div id="page-container" class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title"><span class="emoji">🌐</span>车间网络看板</h1>
        <div class="page-sub">实时监测车间服务器 / WiFi / 老化架网络节点在线情况</div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-sm btn-outline-warning" @click="handleCheckAll">
          <span class="bi bi-lightning-charge"></span>一键检测
        </button>
      </div>
    </div>

    <!-- 顶部统计 + 仪表盘 -->
    <div class="top-section">
      <div class="stat-pair">
        <div class="stat-box online">
          <div class="stat-num">{{ data?.online_devices ?? 0 }}</div>
          <div class="stat-label">全局在线设备</div>
        </div>
        <div class="stat-box offline">
          <div class="stat-num">{{ data?.offline_devices ?? 0 }}</div>
          <div class="stat-label">全局离线设备</div>
        </div>
      </div>
      <div class="gauge-wrapper">
        <div id="gauge" class="gauge"></div>
      </div>
    </div>

    <!-- 底部：拓扑 + 离线列表 -->
    <div class="bottom-section">
      <section class="topology-card">
        <header class="section-head">
          <h2 class="sec-title">按线体网络拓扑</h2>
          <span class="card-subtitle">{{ data?.lines?.length || 0 }} 个线体 | {{ data?.lines?.reduce((sum, l) => (sum + (l.servers?.length || 0) + (l.aging_racks?.length || 0) + (l.wifi_aps?.length || 0)), 0) }} 个设备</span>
        </header>
        <div class="topology-grid">
          <div
            v-for="line in data?.lines ?? []"
            :key="line.line"
            class="line-col"
          >
            <div class="line-header">
              {{ line.line }}
              <span class="line-count">
                <span class="count" title="服务器">{{ line.servers?.length || 0 }}</span>
                <span class="count" title="老化架">{{ line.aging_racks?.length || 0 }}</span>
                <span class="count" title="WiFi AP">{{ line.wifi_aps?.length || 0 }}</span>
              </span>
            </div>
            <div class="line-body">
              <!-- 服务器 -->
              <div class="device-row" v-if="line.servers?.length">
                <div class="device-label">服务器</div>
                <div class="device-list">
                  <div class="device-item server" v-for="s in line.servers" :key="s.id">
                    <span class="device-icon bi bi-server"></span>
                    <span class="device-name">{{ s.name }}</span>
                    <span class="device-tag" :class="tagClass(s.name)">{{ s.name }}</span>
                  </div>
                </div>
              </div>
              <div class="device-row empty-row" v-else>
                <div class="device-label">服务器</div>
                <div class="device-list"><span class="empty-text">-</span></div>
              </div>

              <!-- 老化架 -->
              <div class="device-row" v-if="line.aging_racks?.length">
                <div class="device-label">老化架</div>
                <div class="device-list">
                  <div class="device-item aging" v-for="a in line.aging_racks" :key="a.id">
                    <span class="device-icon bi bi-box-seam"></span>
                    <span class="device-name">{{ a.name }}</span>
                    <span class="device-tag" :class="{ 'tag-warn': a.status !== '正常', 'tag-ok': a.status === '正常' }">
                      {{ a.status !== '正常' ? '⚠️' : '' }}{{ a.slots }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="device-row empty-row" v-else>
                <div class="device-label">老化架</div>
                <div class="device-list"><span class="empty-text">-</span></div>
              </div>

              <!-- AP -->
              <div class="device-row" v-if="line.wifi_aps?.length">
                <div class="device-label">WiFi AP</div>
                <div class="device-list">
                  <div class="device-item ap" v-for="ap in line.wifi_aps" :key="ap.id">
                    <span class="device-icon bi bi-router"></span>
                    <span class="device-name">{{ ap.ssid || 'AP' }}</span>
                    <span class="ap-bar" :class="{ offline: ap.status !== '在线' }"></span>
                  </div>
                </div>
              </div>
              <div class="device-row empty-row" v-else>
                <div class="device-label">WiFi AP</div>
                <div class="device-list"><span class="empty-text">-</span></div>
              </div>
            </div>
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
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi, networkApi } from '@/api'

const data = ref(null)
let gaugeChart = null

const tagClass = (name) => {
  if (!name) return 'tag-default'
  if (name.includes('信创') || name.includes('Kylin') || name.includes('KEY')) return 'tag-ok'
  if (name.includes('PXE') || name.includes('X86')) return 'tag-info'
  if (name.includes('DHCP')) return 'tag-warn'
  return 'tag-default'
}

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
  if (gaugeChart) gaugeChart.dispose()
  gaugeChart = echarts.init(document.getElementById('gauge'))

  gaugeChart.setOption({
    series: [ {
      type: 'gauge',
      startAngle: 210,
      endAngle: -30,
      min: 0,
      max: 100,
      radius: '85%',
      center: ['50%', '55%'],
      progress: { show: true, width: 14 },
      axisLine: {
        lineStyle: {
          width: 14,
          color: [
            [0.3, '#EF4444'],
            [0.7, '#F59E0B'],
            [1, '#10B981'],
          ],
        },
      },
      pointer: {
        show: true,
        length: '55%',
        width: 4,
        itemStyle: { color: '#1F2937' },
      },
      axisTick: { show: true, length: 5, lineStyle: { color: '#999', width: 1 } },
      splitLine: { show: true, length: 10, lineStyle: { color: '#666', width: 2 } },
      axisLabel: {
        show: true,
        distance: 14,
        color: '#6B7280',
        fontSize: 10,
      },
      anchor: {
        show: true,
        size: 8,
        itemStyle: { color: '#1F2937' },
      },
      title: {
        show: true,
        offsetCenter: [0, '20%'],
        fontSize: 13,
        color: '#6B7280',
      },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '-2%'],
        fontSize: 32,
        fontWeight: 700,
        formatter: '{value}%',
        color: rate >= 90 ? '#10B981' : (rate >= 70 ? '#F59E0B' : '#EF4444'),
      },
      data: [{ value: rate, name: '在线率' }],
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
  padding: 20px 24px;
}

/* ---- 顶部统计区 ---- */
.top-section {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  align-items: stretch;
}

.stat-pair {
  display: flex;
  gap: 12px;
  flex: 1;
}

.stat-box {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  text-align: center;
  border: 1px solid var(--c-divider);
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
}

.stat-box .stat-num {
  font-size: 42px;
  font-weight: 700;
  line-height: 1.1;
}

.stat-box.online .stat-num { color: var(--ok); }
.stat-box.offline .stat-num { color: var(--err); }

.stat-box .stat-label {
  margin-top: 8px;
  color: var(--c-text-3);
  font-size: 13px;
}

.gauge-wrapper {
  width: 280px;
  height: 220px;
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
}

.topology-card {
  flex: 1.4;
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--c-divider);
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
  overflow: hidden;
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
  padding: 12px 16px;
  border-bottom: 1px solid var(--c-divider);
  display: flex;
  justify-content: space-between;
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
  font-size: 12px;
  color: var(--c-text-3);
  font-weight: 400;
}

/* ---- 拓扑网格 ---- */
.topology-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  background: var(--c-divider);
}

.line-col {
  background: #fff;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  overflow: hidden;
}

.line-header {
  padding: 8px 6px;
  text-align: center;
  font-weight: 600;
  font-size: 13px;
  color: var(--c-text);
  background: #F7FAFF;
  border-bottom: 1px solid var(--c-divider);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
}

.line-count {
  display: flex;
  gap: 4px;
}

.count {
  font-size: 10px;
  color: var(--c-text-3);
  background: #fff;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid var(--c-divider);
}

.line-body {
  padding: 6px 4px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.device-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 4px;
}

.device-label {
  font-size: 10px;
  color: var(--c-text-3);
  font-weight: 600;
  width: 48px;
  white-space: nowrap;
}

.device-list {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.empty-row {
  color: var(--c-text-mute);
  background: #f9fafb;
}

.empty-text {
  font-size: 10px;
  color: var(--c-text-mute);
}

.device-item {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 6px;
  border-radius: 5px;
  background: #F7FAFF;
  font-size: 10px;
  line-height: 1.2;
}

.device-item.empty {
  color: var(--c-text-mute);
  background: transparent;
}

.device-icon {
  font-size: 11px;
  color: var(--c-text-3);
  flex-shrink: 0;
}

.device-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--c-text-2);
}

.device-tag {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.tag-default { background: #E5E9F2; color: #4B5563; }
.tag-ok      { background: var(--ok-bg); color: #059669; }
.tag-info    { background: var(--info-bg); color: #1D4ED8; }
.tag-warn    { background: var(--warn-bg); color: #B45309; }

.ap-bar {
  width: 20px;
  height: 3px;
  border-radius: 2px;
  background: var(--ok);
  flex-shrink: 0;
}
.ap-bar.offline {
  background: var(--err);
}

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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 0;
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

.line-body::-webkit-scrollbar { width: 5px; }
.line-body::-webkit-scrollbar-thumb { background: #D8DEEA; border-radius: 4px; }
.line-body::-webkit-scrollbar-track { background: transparent; }
</style>
