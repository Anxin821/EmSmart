<template>
  <div id="page-container" class="page">
    <!-- 操作按钮通过 Teleport 注入全局顶栏左侧空白区，不占用看板纵向空间 -->
    <Teleport defer to=".topbar-actions">
      <button class="btn btn-sm btn-outline-warning" :disabled="checking" @click="handleCheckAll">
        <span :class="checking ? 'bi bi-arrow-repeat spin' : 'bi bi-lightning-charge'"></span>{{ checking ? '检测中…' : '一键检测' }}
      </button>
      <button v-if="userStore.canEdit" class="btn btn-sm btn-outline-gear" @click="openSettings">
        <span class="bi bi-gear-fill"></span>告警设置
      </button>
    </Teleport>

    <!-- 顶部统计 + 仪表盘 -->
    <div class="top-section">
      <div class="stat-pair">
        <StatCard
          centered
          class="net-stat net-online"
          color="green"
          icon="bi bi-broadcast-pin"
          :num="data?.online_devices ?? 0"
          label="全局在线设备"
        />
        <StatCard
          centered
          class="net-stat net-offline"
          color="red"
          icon="bi bi-wifi-off"
          :num="data?.offline_devices ?? 0"
          label="全局离线设备"
        />
        <StatCard
          centered
          clickable
          class="net-stat net-alert"
          color="yellow"
          icon="bi bi-bell-fill"
          :num="data?.alert_count ?? 0"
          label="未处理告警"
          @click="openAlertsDrawer"
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
        <!-- 自动巡检脚注：不占布局，仅展示巡检节奏与下次刷新倒计时 -->
        <footer class="monitor-foot">
          <span class="mf-dot"></span>自动巡检
          <span class="mf-sep">·</span>{{ refreshInterval }}s/次
          <span class="mf-sep">·</span>上次 {{ data?.last_check_time ? data.last_check_time.slice(11) : '—' }}
          <span class="mf-spacer"></span>
          <span :class="refreshing ? 'bi bi-arrow-repeat spin' : ''"></span>{{ refreshing ? '刷新中' : `${countdown}s 后刷新` }}
        </footer>
      </section>
    </div>

    <!-- 告警记录抽屉：点击「未处理告警」KPI 打开 -->
    <el-drawer
      v-model="alertsDrawer"
      direction="rtl"
      size="480px"
      destroy-on-close
      class="alerts-drawer"
      :with-header="false"
    >
      <div class="ad-wrap">
        <header class="ad-header">
          <div class="ad-title">
            <span class="bi bi-bell-fill ad-title-icon"></span>
            <span>网络告警记录</span>
          </div>
          <button class="ad-close" @click="alertsDrawer = false">
            <span class="bi bi-x-lg"></span>
          </button>
        </header>

        <div class="ad-toolbar">
          <div class="ad-stat">
            <span class="ad-stat-num" :class="{ zero: !openAlertCount }">{{ openAlertCount }}</span>
            <span class="ad-stat-label">条未处理</span>
          </div>
          <button
            v-if="userStore.canEdit"
            class="ad-resolve-all"
            :disabled="!openAlertCount"
            @click="handleResolveAll"
          >
            <span class="bi bi-check2-all"></span>全部标记已处理
          </button>
        </div>

        <div v-loading="alertsLoading" class="ad-body">
          <div v-if="!alertsLoading && !alerts.length" class="ad-empty">
            <span class="bi bi-bell-slash ad-empty-icon"></span>
            <span class="ad-empty-text">暂无告警记录</span>
            <span class="ad-empty-sub">设备离线或 Syslog 命中告警关键词时自动记录并推送钉钉</span>
          </div>

          <div
            v-for="a in alerts"
            :key="a.id"
            class="ad-card"
            :class="a.status === '未处理' ? 'is-open' : 'is-done'"
          >
            <span class="ad-card-bar"></span>
            <div class="ad-card-main">
              <div class="ad-card-head">
                <span class="offline-type" :class="typeClass(a.device_type)">{{ a.device_type }}</span>
                <span v-if="a.alert_type === '日志告警'" class="ad-card-atype">Syslog</span>
                <span class="ad-card-name">{{ a.device_name }}</span>
                <span class="ad-card-status" :class="a.status === '未处理' ? 'st-open' : 'st-done'">
                  <span :class="a.status === '未处理' ? 'bi bi-exclamation-circle-fill' : 'bi bi-check-circle-fill'"></span>
                  {{ a.status }}
                </span>
              </div>
              <div class="ad-card-meta">
                <span><span class="bi bi-geo-alt"></span>{{ a.production_line || '-' }}</span>
                <span><span class="bi bi-hdd-network"></span>{{ a.ip_address || '-' }}</span>
                <span><span class="bi bi-clock"></span>{{ fmtTime(a.created_at) }}</span>
              </div>
              <div class="ad-card-msg">{{ a.message || a.alert_type }}</div>
              <div v-if="a.status === '未处理' && userStore.canEdit" class="ad-card-actions">
                <button class="ad-resolve-one" @click="handleResolve(a.id)">
                  <span class="bi bi-check-lg"></span>标记已处理
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 一键检测结果抽屉：检测完成后自动弹出，实时展示每台设备 Ping 结果 -->
    <el-drawer
      v-model="resultDrawer"
      direction="rtl"
      size="500px"
      destroy-on-close
      class="alerts-drawer"
      :with-header="false"
    >
      <div class="ad-wrap" v-if="checkResult">
        <header class="ad-header">
          <div class="ad-title">
            <span class="bi bi-lightning-charge-fill ad-title-icon" style="color:#D97706;"></span>
            <span>一键检测结果</span>
          </div>
          <button class="ad-close" @click="resultDrawer = false">
            <span class="bi bi-x-lg"></span>
          </button>
        </header>

        <div class="cr-summary">
          <div class="cr-sum-item">
            <span class="cr-sum-num ok">{{ checkResult.online ?? 0 }}</span>
            <span class="cr-sum-label">在线</span>
          </div>
          <div class="cr-sum-item">
            <span class="cr-sum-num bad">{{ checkResult.offline ?? 0 }}</span>
            <span class="cr-sum-label">离线 / 故障</span>
          </div>
          <div class="cr-sum-item">
            <span class="cr-sum-num warn">{{ checkResult.new_alerts ?? 0 }}</span>
            <span class="cr-sum-label">新增告警</span>
          </div>
          <div class="cr-sum-time">
            <span class="bi bi-clock-history"></span>{{ checkResult.checked_at }}
          </div>
        </div>

        <div class="ad-body">
          <!-- 离线设备 -->
          <template v-if="offlineResults.length">
            <div class="cr-section-title bad">
              <span class="bi bi-x-octagon-fill"></span>离线 / 故障设备（{{ offlineResults.length }}）
            </div>
            <div v-for="(r, i) in offlineResults" :key="'off-' + i" class="cr-card is-off">
              <span class="cr-card-bar"></span>
              <div class="cr-card-main">
                <div class="cr-card-head">
                  <span class="offline-type" :class="typeClass(r.device_type)">{{ r.device_type }}</span>
                  <span class="cr-card-name">{{ r.device_name }}</span>
                  <span class="cr-card-state bad">{{ r.status }}</span>
                </div>
                <div class="cr-card-meta">
                  <span><span class="bi bi-geo-alt"></span>{{ r.production_line || '-' }}</span>
                  <span><span class="bi bi-hdd-network"></span>{{ r.ip_address }}</span>
                </div>
              </div>
            </div>
          </template>

          <!-- 在线设备 -->
          <template v-if="onlineResults.length">
            <div class="cr-section-title ok">
              <span class="bi bi-check-circle-fill"></span>在线设备（{{ onlineResults.length }}）
            </div>
            <div class="cr-ok-list">
              <div v-for="(r, i) in onlineResults" :key="'on-' + i" class="cr-ok-row">
                <span class="bi bi-check-circle-fill cr-dot"></span>
                <span class="offline-type" :class="typeClass(r.device_type)">{{ r.device_type }}</span>
                <span class="cr-ok-name">{{ r.device_name }}</span>
                <span class="cr-ok-ip">{{ r.ip_address }}</span>
                <span class="cr-ok-line">{{ r.production_line || '-' }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </el-drawer>

    <!-- 告警通知设置弹窗（顶栏「告警设置」按钮打开） -->
    <el-dialog
      v-model="settingsDialog"
      title="告警通知设置"
      width="560px"
      destroy-on-close
      class="net-settings-dialog"
    >
      <div v-loading="settingsLoading" class="ns-body">
        <el-form :model="settingsForm" label-width="110px" label-position="right">
          <el-form-item label="钉钉 Webhook">
            <el-input
              v-model="settingsForm.dingtalk_webhook"
              clearable
              placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxxx"
            />
          </el-form-item>
          <el-form-item label="加签 Secret">
            <el-input
              v-model="settingsForm.dingtalk_secret"
              type="password"
              show-password
              clearable
              placeholder="机器人安全设置选择「加签」后生成的 SEC"
            />
          </el-form-item>
          <el-form-item label=" ">
            <el-button :loading="settingsTesting" @click="handleTestSettings">
              <span class="bi bi-send" style="margin-right:4px;"></span>发送测试消息
            </el-button>
            <span class="ns-test-hint">将先保存当前配置，再向钉钉群发送一条测试消息</span>
          </el-form-item>
          <el-form-item label="Ping 间隔">
            <el-input-number v-model="settingsForm.ping_interval" :min="10" :max="3600" :step="10" controls-position="right" />
            <span class="ns-hint">秒（后台自动巡检间隔）</span>
          </el-form-item>

          <el-divider content-position="left">Syslog 日志监听（UDP）</el-divider>
          <el-form-item label="启用监听">
            <el-switch v-model="settingsForm.syslog_enabled" active-text="接收设备 Syslog 并自动告警" />
          </el-form-item>
          <el-form-item label="监听端口">
            <el-input-number v-model="settingsForm.syslog_port" :min="1" :max="65535" controls-position="right" :disabled="!settingsForm.syslog_enabled" />
          </el-form-item>
          <el-form-item label="告警关键词">
            <el-input
              v-model="settingsForm.syslog_keywords"
              type="textarea"
              :rows="2"
              placeholder="逗号分隔，如：登录,退出,error,失败,攻击,非法"
              :disabled="!settingsForm.syslog_enabled"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="ns-footer">
          <el-button @click="settingsDialog = false">取消</el-button>
          <el-button type="primary" :loading="settingsSaving" @click="handleSaveSettings">保存设置</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElNotification } from 'element-plus'
import { dashboardApi, networkApi } from '@/api'
import { useUserStore } from '@/stores/user'
import StatCard from '@/components/common/StatCard.vue'

const userStore = useUserStore()
const data = ref(null)
let gaugeChart = null

// 一键检测 / 告警抽屉状态
const checking = ref(false)
const alertsDrawer = ref(false)
const alertsLoading = ref(false)
const alerts = ref([])
const openAlertCount = computed(() => data.value?.alert_count ?? 0)

const fmtTime = (iso) => {
  if (!iso) return '-'
  return iso.replace('T', ' ').slice(0, 19)
}

// 每条线体的健康概览：在线/总数、健康率、状态级别、三类设备各自离线数
// —— 汇报视角：弱化单个设备名，突出“哪条线体有问题、异常几台”（离线明细仍在右侧列表可查）
const activeLines = computed(() =>
  (data.value?.lines ?? [])
    .map((line) => {
      const servers = line.servers ?? []
      const racks   = line.aging_racks ?? []
      const aps     = line.wifi_aps ?? []
      const sOff = servers.filter(s => s.status !== '在线').length
      const rOff = racks.filter(a => a.status !== '在线').length
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

// 自动轮询：与后台 Ping 间隔保持一致，让后台巡检结果实时反映到看板
const refreshInterval = ref(30)
const countdown = ref(30)
const refreshing = ref(false)
let tickTimer = null
let lastOpenCount = null   // 上一次刷新时的未处理告警数，用于识别"新告警"

const loadData = async (silent = false) => {
  if (silent) refreshing.value = true
  try {
    const res = await dashboardApi.network()
    const d = res.data || null
    data.value = d
    // 自动巡检发现新的未处理告警：右上角通知（不阻塞操作），点击打开告警抽屉
    const openCount = d?.alert_count ?? 0
    if (silent && lastOpenCount !== null && openCount > lastOpenCount) {
      ElNotification({
        title: '网络巡检告警',
        message: `后台 Ping 巡检发现 ${openCount - lastOpenCount} 条新的离线告警，点击查看`,
        type: 'warning',
        duration: 10000,
        onClick: () => openAlertsDrawer(),
      })
    }
    lastOpenCount = openCount
    await nextTick()
    renderGauge()
  } catch (e) {
    console.error(e)
  } finally {
    if (silent) refreshing.value = false
  }
}

const startAutoRefresh = async () => {
  // 读取设置中的 Ping 间隔作为看板自动刷新间隔
  try {
    const res = await networkApi.getSettings()
    const sec = Number(res.data?.ping_interval)
    if (sec >= 10) {
      refreshInterval.value = sec
      countdown.value = sec
    }
  } catch (e) {
    console.error(e)
  }
  tickTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      countdown.value = refreshInterval.value
      loadData(true)
      // 告警抽屉打开时连带刷新告警列表
      if (alertsDrawer.value) loadAlerts()
    }
  }, 1000)
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
        fontSize: 40,
        fontWeight: 800,
        formatter: '{value}%',
        color: rateColor,
      },
      data: [{ value: rate, name: '设备在线率' }],
    } ],
  })
}

// 一键检测结果抽屉
const resultDrawer = ref(false)
const checkResult = ref(null)
const offlineResults = computed(() => (checkResult.value?.results || []).filter(r => !r.alive))
const onlineResults = computed(() => (checkResult.value?.results || []).filter(r => r.alive))

const handleCheckAll = async () => {
  checking.value = true
  try {
    const res = await networkApi.checkAll()
    const d = res.data || {}
    checkResult.value = d
    // 看板 KPI / 线体健康 / 仪表盘立即刷新为最新状态
    loadData()
    // 检测结果明细实时展示在抽屉中
    resultDrawer.value = true
    if (d.new_alerts) {
      ElMessage.warning(`检测完成：离线 ${d.offline ?? 0} 台，新增告警 ${d.new_alerts} 条（已推送钉钉）`)
    } else {
      ElMessage.success(`检测完成：在线 ${d.online ?? 0} 台，离线 ${d.offline ?? 0} 台`)
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('一键检测失败，请稍后重试')
  } finally {
    checking.value = false
  }
}

// ---------- 告警抽屉 ----------
const openAlertsDrawer = async () => {
  alertsDrawer.value = true
  loadAlerts()
}

const loadAlerts = async () => {
  alertsLoading.value = true
  try {
    const res = await networkApi.alerts({ page: 1, page_size: 50 })
    alerts.value = res.data?.items || []
  } catch (e) {
    console.error(e)
  } finally {
    alertsLoading.value = false
  }
}

const handleResolve = async (id) => {
  try {
    await networkApi.resolveAlert(id)
    ElMessage.success('告警已处理')
    await loadAlerts()
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('操作失败')
  }
}

const handleResolveAll = async () => {
  try {
    const res = await networkApi.resolveAllAlerts()
    ElMessage.success(res.message || '全部告警已处理')
    await loadAlerts()
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error('操作失败')
  }
}

// ---------- 告警通知设置弹窗 ----------
const settingsDialog = ref(false)
const settingsLoading = ref(false)
const settingsSaving = ref(false)
const settingsTesting = ref(false)
const settingsForm = ref({
  dingtalk_webhook: '',
  dingtalk_secret: '',
  ping_interval: 60,
  syslog_enabled: false,
  syslog_port: 514,
  syslog_keywords: ''
})

const openSettings = async () => {
  settingsDialog.value = true
  settingsLoading.value = true
  try {
    const res = await networkApi.getSettings()
    settingsForm.value = {
      dingtalk_webhook: res.data?.dingtalk_webhook || '',
      dingtalk_secret: res.data?.dingtalk_secret || '',
      ping_interval: res.data?.ping_interval || 60,
      syslog_enabled: !!res.data?.syslog_enabled,
      syslog_port: res.data?.syslog_port || 514,
      syslog_keywords: res.data?.syslog_keywords || ''
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('设置加载失败')
  } finally {
    settingsLoading.value = false
  }
}

const buildSettingsPayload = () => ({
  dingtalk_webhook: (settingsForm.value.dingtalk_webhook || '').trim(),
  dingtalk_secret: (settingsForm.value.dingtalk_secret || '').trim(),
  ping_interval: settingsForm.value.ping_interval || 60,
  syslog_enabled: !!settingsForm.value.syslog_enabled,
  syslog_port: settingsForm.value.syslog_port || 514,
  syslog_keywords: (settingsForm.value.syslog_keywords || '').trim()
})

const handleSaveSettings = async () => {
  const webhook = (settingsForm.value.dingtalk_webhook || '').trim()
  if (webhook && !/^https?:\/\//.test(webhook)) {
    ElMessage.warning('Webhook 地址需以 http(s):// 开头')
    return
  }
  if (!settingsForm.value.ping_interval || settingsForm.value.ping_interval < 10) {
    ElMessage.warning('Ping 间隔不能小于 10 秒')
    return
  }
  settingsSaving.value = true
  try {
    await networkApi.saveSettings(buildSettingsPayload())
    ElMessage.success('设置已保存')
    settingsDialog.value = false
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    settingsSaving.value = false
  }
}

const handleTestSettings = async () => {
  // 先保存再测试，保证测试使用的是弹窗中当前填写的配置
  const webhook = (settingsForm.value.dingtalk_webhook || '').trim()
  if (!webhook) {
    ElMessage.warning('请先填写钉钉 Webhook 地址')
    return
  }
  settingsTesting.value = true
  try {
    await networkApi.saveSettings(buildSettingsPayload())
    await networkApi.testDingtalk()
    ElMessage.success('测试消息已发送，请查看钉钉群')
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.detail || '测试发送失败，请检查 Webhook / Secret')
  } finally {
    settingsTesting.value = false
  }
}

const resize = () => {
  gaugeChart && gaugeChart.resize()
}

onMounted(() => {
  loadData()
  startAutoRefresh()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  if (tickTimer) clearInterval(tickTimer)
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
  overflow: hidden;
  /* 居中堆叠布局已由 StatCard 的 centered prop 提供，这里只保留 hero 卡专属尺寸/圆角 */
}
/* 左侧主题色竖条：一眼区分在线/离线 */
.stat-pair .net-stat::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  z-index: 2;
}
.net-online::before  { background: transparent; }   /* 去掉绿边：在线卡不再显示左侧绿条 */
.net-offline::before { background: transparent; }   /* 去掉红边：离线卡不再显示左侧红条 */
/* 卡片底色：主题色淡渐变 → 白，比纯白更有层次 */
.stat-pair .net-online {
  background: linear-gradient(135deg, #ECFDF5 0%, #FFFFFF 62%) !important;
  border-color: var(--c-divider) !important;   /* 去掉绿边：改中性描边 */
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03) !important;   /* 去掉绿色光晕 */
}
.stat-pair .net-offline {
  background: linear-gradient(135deg, #FEF2F2 0%, #FFFFFF 62%) !important;
  border-color: var(--c-divider) !important;   /* 去掉红边：改中性描边 */
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03) !important;   /* 去掉红色光晕 */
}
/* 图标徽章：圆角实底 + 白色图标 + 主题色投影 */
.stat-pair .net-stat :deep(.icon-box) {
  /* grid 定位由 centered prop 处理，这里只做 hero 卡图标徽章的尺寸/圆角 */
  width: 52px; height: 52px;
  border-radius: 15px;
  display: flex; align-items: center; justify-content: center;
}
.net-online  :deep(.icon-box) { background: linear-gradient(135deg, #10B981, #059669); box-shadow: 0 8px 18px -6px rgba(16, 185, 129, .6); }
.net-offline :deep(.icon-box) { background: linear-gradient(135deg, #EF4444, #DC2626); box-shadow: 0 8px 18px -6px rgba(239, 68, 68, .6); }
.stat-pair .net-stat :deep(.icon-box span) { color: #fff !important; font-size: 28px; }
/* 超大主题色数字：居中/去 padding 由 centered prop 处理，这里只保留 hero 卡的字号与主题色 */
.net-online  :deep(.num) { color: #059669; font-size: 44px; font-weight: 800; line-height: 1; letter-spacing: -1px; }
.net-offline :deep(.num) { color: #DC2626; font-size: 44px; font-weight: 800; line-height: 1; letter-spacing: -1px; }
.stat-pair .net-stat :deep(.label) { font-size: 15px; font-weight: 600; color: var(--c-text-2); letter-spacing: .3px; }
/* 未处理告警卡：黄色主题，数值为 0 时弱化，有告警时醒目 */
.stat-pair .net-alert {
  background: linear-gradient(135deg, #FFFBEB 0%, #FFFFFF 62%) !important;
  border-color: var(--c-divider) !important;
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03) !important;
}
.stat-pair .net-alert :deep(.icon-box) { background: linear-gradient(135deg, #F59E0B, #D97706); box-shadow: 0 8px 18px -6px rgba(245, 158, 11, .6); }
.net-alert :deep(.num) { color: #D97706; font-size: 44px; font-weight: 800; line-height: 1; letter-spacing: -1px; }

/* 顶栏按钮 loading 旋转 */
.spin { display: inline-block; animation: net-spin 1s linear infinite; }
@keyframes net-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 顶栏「告警设置」按钮（Teleport 内容仍带 scoped 属性，样式生效） */
.btn-outline-gear {
  color: #64748B;
  background: #fff;
  border: 1px solid #CBD5E1;
}
.btn-outline-gear:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--primary-50, #EEF4FF);
}

/* ---- 告警抽屉（美化版） ---- */
/* 固定头 + 滚动体：body 裁掉自身滚动，ad-wrap 占满，ad-body 用 min-height:0 获得内部滚动 */
.alerts-drawer :deep(.el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.ad-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ad-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  background: linear-gradient(135deg, #F7FAFF 0%, #EEF4FF 100%);
  border-bottom: 1px solid var(--c-divider);
}
.ad-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text);
}
.ad-title-icon { color: var(--primary); font-size: 18px; }
.ad-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px; height: 30px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--c-text-3);
  cursor: pointer;
  transition: all .15s;
}
.ad-close:hover { background: #E2E8F0; color: var(--c-text); }

.ad-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--c-divider);
}
.ad-stat { display: flex; align-items: baseline; gap: 6px; }
.ad-stat-num { font-size: 24px; font-weight: 800; line-height: 1; color: #DC2626; }
.ad-stat-num.zero { color: #059669; }
.ad-stat-label { font-size: 13px; color: var(--c-text-3); }

/* 「全部标记已处理」：自定义按钮，明确蓝底白字 hover，避免 plain 按钮文字色被全局样式覆盖 */
.ad-resolve-all {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 13px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  color: #2563EB;
  background: #fff;
  border: 1px solid #93C5FD;
  transition: all .15s;
}
.ad-resolve-all:hover:not(:disabled) {
  background: #2563EB;
  border-color: #2563EB;
  color: #fff;
}
.ad-resolve-all:disabled {
  color: #94A3B8;
  border-color: #E2E8F0;
  background: #F8FAFC;
  cursor: not-allowed;
}

.ad-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ad-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 70px 0;
}
.ad-empty-icon { font-size: 38px; color: #CBD5E1; }
.ad-empty-text { font-size: 14px; font-weight: 600; color: var(--c-text-2); }
.ad-empty-sub { font-size: 12px; color: var(--c-text-mute); }

.ad-card {
  display: flex;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #FECACA;
  box-shadow: 0 1px 3px rgba(15, 23, 42, .05);
}
.ad-card.is-done { border-color: var(--c-divider); opacity: .75; }
.ad-card-bar { width: 4px; flex-shrink: 0; background: #EF4444; }
.ad-card.is-done .ad-card-bar { background: #CBD5E1; }
.ad-card-main {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.ad-card-head { display: flex; align-items: center; gap: 8px; }
.ad-card-name {
  flex: 1;
  min-width: 0;
  font-weight: 600;
  font-size: 13.5px;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ad-card-status {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.ad-card-status.st-open { color: #DC2626; }
.ad-card-status.st-done { color: #059669; }
.ad-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-size: 12px;
  color: var(--c-text-3);
}
.ad-card-meta > span { display: inline-flex; align-items: center; gap: 4px; }
.ad-card-meta .bi { font-size: 12px; }
.ad-card-msg {
  font-size: 12.5px;
  line-height: 1.55;
  padding: 6px 10px;
  border-radius: 6px;
  background: #F8FAFC;
  color: var(--c-text-2);
}
.ad-card.is-open .ad-card-msg { background: #FEF2F2; color: #991B1B; }
.ad-card-actions { display: flex; justify-content: flex-end; }
.ad-resolve-one {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  font-size: 12.5px;
  font-weight: 600;
  color: #2563EB;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background .15s;
}
.ad-resolve-one:hover { background: #EFF6FF; }

/* ---- 一键检测结果抽屉 ---- */
.cr-summary {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--c-divider);
  background: #F8FAFC;
}
.cr-sum-item { display: flex; align-items: baseline; gap: 5px; }
.cr-sum-num { font-size: 26px; font-weight: 800; line-height: 1; }
.cr-sum-num.ok { color: #059669; }
.cr-sum-num.bad { color: #DC2626; }
.cr-sum-num.warn { color: #D97706; }
.cr-sum-label { font-size: 12.5px; color: var(--c-text-3); }
.cr-sum-time {
  margin-left: auto;
  font-size: 12px;
  color: var(--c-text-mute);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.cr-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  margin: 4px 0 2px;
}
.cr-section-title.bad { color: #DC2626; }
.cr-section-title.ok { color: #059669; }

.cr-card {
  display: flex;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #FECACA;
  box-shadow: 0 1px 3px rgba(15, 23, 42, .05);
}
.cr-card-bar { width: 4px; flex-shrink: 0; background: #EF4444; }
.cr-card-main {
  flex: 1;
  min-width: 0;
  padding: 9px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.cr-card-head { display: flex; align-items: center; gap: 8px; }
.cr-card-name {
  flex: 1;
  min-width: 0;
  font-weight: 600;
  font-size: 13.5px;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cr-card-state {
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.cr-card-state.bad { color: #DC2626; }
.cr-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-size: 12px;
  color: var(--c-text-3);
}
.cr-card-meta > span { display: inline-flex; align-items: center; gap: 4px; }

.cr-ok-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 6px;
}
.cr-ok-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: #F6FEF9;
  font-size: 12.5px;
}
.cr-ok-row:hover { background: #ECFDF5; }
.cr-dot { color: #10B981; font-size: 13px; flex-shrink: 0; }
.cr-ok-name {
  font-weight: 600;
  color: var(--c-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}
.cr-ok-ip {
  font-family: Consolas, 'Courier New', monospace;
  font-size: 12px;
  color: var(--c-text-3);
}
.cr-ok-line { margin-left: auto; font-size: 12px; color: var(--c-text-mute); white-space: nowrap; }

/* ---- 告警通知设置弹窗（限高：内容超出时仅表单区滚动，头尾固定） ---- */
.net-settings-dialog { margin-top: 5vh !important; margin-bottom: 5vh; }
.net-settings-dialog :deep(.el-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
}
.net-settings-dialog :deep(.el-dialog__header) { flex-shrink: 0; }
.net-settings-dialog :deep(.el-dialog__body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding-top: 8px;
  padding-bottom: 8px;
}
.net-settings-dialog :deep(.el-dialog__footer) { flex-shrink: 0; }
.ns-body {
  max-height: calc(90vh - 150px);
  overflow-y: auto;
  padding-right: 8px;
}
.ns-hint { margin-left: 12px; font-size: 12px; color: var(--c-text-3); }
.ns-tip {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 6px;
  padding: 10px 12px;
  background: #F0F7FF;
  border: 1px solid #DBEAFE;
  border-radius: 8px;
  font-size: 12.5px;
  line-height: 1.6;
  color: #1E40AF;
}
.ns-tip .bi { margin-top: 3px; }
.ns-test-hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--c-text-mute);
}
.ns-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

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
  gap: 0px;
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
/* 三档状态配色：整卡环绕描边（绿=全部正常 / 黄=轻度异常 / 红=严重异常），不再只在左侧着色 */
.lv-ok     { background: linear-gradient(135deg, #F0FDF4 0%, #fff 55%); border: 1.5px solid rgba(16, 185, 129, .45); }
.lv-warn   { background: linear-gradient(135deg, #FFFBEB 0%, #fff 55%); border: 1.5px solid rgba(245, 158, 11, .55); }
.lv-danger { background: linear-gradient(135deg, #FEF2F2 0%, #fff 55%); border: 1.5px solid rgba(239, 68, 68, .6); }

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

/* 设备芯片：整块流动 + 文字不折行。能并排就并排，放不下时整块换到下一行，
   绝不把“服务器 3”拆成两行（之前用刚性 2 列网格，窄卡下 auto 列被压缩导致芯片内文字折行） */
.lh-types {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}
.lh-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--c-text-2);
  background: #F5F7FB;
  border: 1px solid var(--c-divider);
  border-radius: 7px;
  padding: 2px 7px;
  white-space: nowrap;   /* 芯片文字（如“服务器 3”）不折行 */
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

.ad-card-atype {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: #EDE9FE;
  color: #6D28D9;
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

/* 自动巡检脚注：离线卡片底部一行小字，不参与卡片高度/列表布局 */
.monitor-foot {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-top: 1px solid var(--c-divider);
  background: #F8FAFC;
  font-size: 11.5px;
  color: var(--c-text-mute);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.mf-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #10B981;
  flex-shrink: 0;
  animation: mf-pulse 1.6s infinite;
}
@keyframes mf-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(16, 185, 129, .4); }
  70%  { box-shadow: 0 0 0 5px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.mf-sep { color: #CBD5E1; }
.mf-spacer { flex: 1; }

.health-grid::-webkit-scrollbar { width: 6px; }
.health-grid::-webkit-scrollbar-thumb { background: #D8DEEA; border-radius: 4px; }
.health-grid::-webkit-scrollbar-track { background: transparent; }
</style>