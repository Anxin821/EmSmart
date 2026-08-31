<template>
  <div class="page">
    <!-- 页面标题区域 -->
    <div class="page-header">
      <div class="page-header-left">
        <slot name="header-left">
          <div v-if="title" class="page-header-content">
            <h1 class="page-title">
              <span v-if="icon" class="emoji">{{ icon }}</span>
              {{ title }}
            </h1>
            <div v-if="subtitle" class="page-sub">{{ subtitle }}</div>
            <div v-if="stats" class="page-stats">
              <span v-for="(stat, index) in stats" :key="index" class="stat-item">
                {{ stat }}
              </span>
            </div>
          </div>
        </slot>
      </div>
      
      <div class="page-header-right">
        <slot name="header-right">
          <div class="d-flex align-items-center gap-2">
            <slot name="header-actions"></slot>
          </div>
        </slot>
      </div>
    </div>

    <!-- 页面内容区域 -->
    <section class="page-section" :class="{ 'no-pad': noPadding }" :style="sectionStyle">
      <slot name="section-header" v-if="$slots['section-header']">
        <div v-if="sectionTitle" class="section-head">
          <div class="sec-title">{{ sectionTitle }}</div>
          <div class="sec-actions">
            <slot name="section-actions"></slot>
          </div>
        </div>
      </slot>
      
      <div class="section-body" :class="{ 'no-pad': bodyNoPadding }">
        <slot></slot>
      </div>
      
      <slot name="section-footer"></slot>
    </section>

    <!-- 其他插槽 -->
    <slot name="footer"></slot>
  </div>
</template>

<script setup>
/**
 * PageLayout - 通用页面布局组件
 * 
 * 使用示例：
 * 
 * 基本用法：
 * <PageLayout title="页面标题" icon="🔍" subtitle="页面副标题">
 *   <template #header-actions>
 *     <button @click="handleAction">操作按钮</button>
 *   </template>
 *   
 *   <!-- 页面内容 -->
 *   <CommonFilterBar />
 *   <el-table />
 *   <CommonPagination />
 * </PageLayout>
 * 
 * 高级用法：
 * <PageLayout>
 *   <template #header-left>
 *     <div>自定义标题区域</div>
 *   </template>
 *   
 *   <template #section-header>
 *     <div>自定义分区标题</div>
 *   </template>
 *   
 *   <template #default>
 *     <div>主要内容</div>
 *   </template>
 * </PageLayout>
 */

import { computed } from 'vue'

const props = defineProps({
  // 标题区域配置
  title: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  stats: {
    type: Array,
    default: () => []
  },
  
  // 内容区域配置
  sectionTitle: {
    type: String,
    default: ''
  },
  noPadding: {
    type: Boolean,
    default: false
  },
  bodyNoPadding: {
    type: Boolean,
    default: false
  },
  sectionStyle: {
    type: Object,
    default: () => ({})
  }
})

// 计算属性：是否显示默认标题
const hasDefaultHeader = computed(() => {
  return !props.title && !props.subtitle && !props.stats?.length
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header-left {
  flex: 1;
  min-width: 0;
}

.page-header-right {
  flex-shrink: 0;
}

.page-header-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--c-text);
  line-height: 1;
}

.page-title .emoji {
  font-size: 18px;
}

.page-sub {
  margin-top: 4px;
  font-size: var(--fn-sm);
  color: var(--c-text-light);
}

.page-stats {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  font-size: var(--fn-sm);
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--primary-50);
  border-radius: var(--radius-sm);
  color: var(--primary);
}

/* 兼容现有样式 */
:deep(.page-header) {
  align-items: flex-end !important;
}
</style>