<template>
  <div class="page" style="padding: 20px 24px;">
    <div class="page-header">
      <div>
        <h1 class="page-title" style="color: var(--c-text);font-weight: 700;font-size: 18px;margin:0;display:flex;align-items:center;gap:8px;">
          <span style="color:#60a5fa;font-size:18px;">🛡</span>设备杀毒看板
        </h1>
      </div>
    </div>

    <!-- 顶部 4 张统计卡：设备总数 / 已杀毒 / 待杀毒 / 超时未杀毒 -->
    <div style="
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin: 20px 0 28px 0;
    ">
      <div class="anti-stat-card" style="color:#3b82f6;">
        <div class="anti-stat-num">{{ stats.total_devices }}</div>
        <div class="anti-stat-label">设备总数</div>
      </div>
      <div class="anti-stat-card" style="color:#10b981;">
        <div class="anti-stat-num">{{ stats.done_count }}</div>
        <div class="anti-stat-label">已杀毒</div>
      </div>
      <div class="anti-stat-card" style="color:#f59e0b;">
        <div class="anti-stat-num">{{ stats.pending_count }}</div>
        <div class="anti-stat-label">待杀毒</div>
      </div>
      <div class="anti-stat-card" style="color:#ef4444;">
        <div class="anti-stat-num">{{ stats.overdue_count }}</div>
        <div class="anti-stat-label">超时未杀毒</div>
      </div>
    </div>

    <!-- 按线体分布：Element Plus el-table 表格 -->
    <section class="page-section" style="padding:0;overflow:hidden;">
      <div style="font-size:16px;font-weight:600;color:var(--c-text);margin:14px 0 14px 4px;">按线体分布</div>
      <el-table
        :data="distribution"
        border
        stripe
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
            <span style="color:#f59e0b;font-weight:500;">{{ s.row.pending }}</span>
          </template>
        </el-table-column>
        <el-table-column label="超时未杀毒" prop="overdue" min-width="120" align="center">
          <template #default="s">
            <span style="color:#ef4444;font-weight:500;">{{ s.row.overdue }}</span>
          </template>
        </el-table-column>
        <el-table-column label="进度" min-width="320" align="left">
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
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi } from '@/api'
import { ElMessage } from 'element-plus'

const stats = ref({ total_devices: 0, done_count: 0, pending_count: 0, overdue_count: 0 })
const distribution = ref([])

const loadData = async () => {
  try {
    const res = await dashboardApi.antivirus()
    stats.value = {
      total_devices: res.data?.total_devices ?? 0,
      done_count:    res.data?.done_count    ?? 0,
      pending_count: res.data?.pending_count ?? 0,
      overdue_count: res.data?.overdue_count ?? 0,
    }
    distribution.value = res.data?.distribution || []
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '加载杀毒看板数据失败')
    console.error(e)
  }
}

onMounted(loadData)
</script>

<style scoped>
/* ---------- 统计卡片 ---------- */
.anti-stat-card {
  background: #fff;
  border: 1px solid var(--c-divider);
  border-radius: 10px;
  padding: 28px 24px 24px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(15,23,42,.04);
}
.anti-stat-num {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.1;
}
.anti-stat-label {
  margin-top: 8px;
  font-size: 13px;
  color: var(--c-text-3);
}

/* ---------- 进度条（百分比内嵌在进度条上方，模仿截图） ---------- */
.anti-progress-bar {
  width: 100%;
  height: 22px;
  background: #E5E7EB;
  border-radius: 999px;
  overflow: visible;
  position: relative;
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
</style>
