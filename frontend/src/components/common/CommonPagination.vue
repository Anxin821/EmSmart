<template>
  <!--
    CommonPagination —— 通用分页组件
    内部 = <el-pagination>；对外只暴露我们业务页真正用的参数：
      page / pageSize / total（双向绑定 + change 事件）
    保证后续 Element Plus 分页 API 变更时只改这里。
  -->
  <div class="common-pagination" :class="{ compact }">
    <el-pagination
      :current-page="page"
      @current-change="onPageChange"
      :page-size="pageSize"
      @update:page-size="onPageSizeChange"
      :page-sizes="pageSizes"
      :total="total"
      :layout="layout"
      :background="background"
      :small="size === 'small'"
      :hide-on-single-page="hideOnSinglePage"
    />
  </div>
</template>

<script setup>
/**
 * 对外契约（稳定 API，业务页只需要理解这 5 个 props + 3 个事件）：
 * props:
 *   page                  number   —— 当前页（v-model:page）
 *   pageSize              number   —— 每页条数（v-model:pageSize，默认 20）
 *   total                 number   —— 总数
 *   pageSizes?            number[] —— 可选每页条数（默认 [10,20,50,100]）
 *   layout?               string   —— 布局，默认 "sizes, prev, pager, next, jumper, total"
 *   size?                 'default'|'small'
 *   background?           boolean  —— 按钮带底色（默认 true）
 *   hideOnSinglePage?     boolean  —— 只有 1 页时不显示（默认 false）
 *   compact?              boolean  —— 紧凑版：padding 更小
 * emits:
 *   'update:page' —— 页码变化
 *   'update:pageSize' —— 每页条数变化
 *   'change'      —— 任一变化时触发，payload = { page, pageSize, totalPages }
 */
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  pageSizes: { type: Array, default: () => [10, 20, 50, 100] },
  layout: { type: String, default: 'total, sizes, prev, pager, next, jumper' },
  size: { type: String, default: 'default' },
  background: { type: Boolean, default: true },
  hideOnSinglePage: { type: Boolean, default: false },
  compact: { type: Boolean, default: false }
})
const emit = defineEmits(['update:page', 'update:pageSize', 'change'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const onPageChange = (p) => {
  emit('update:page', p)
  emit('change', { page: p, pageSize: props.pageSize, totalPages: totalPages.value })
}
const onPageSizeChange = (s) => {
  // 切换到新每页条数时，自动回到第 1 页（避免空页/超界页，符合业务直觉）
  emit('update:pageSize', s)
  emit('update:page', 1)
  emit('change', { page: 1, pageSize: s, totalPages: Math.max(1, Math.ceil(props.total / s)) })
}
</script>

<style scoped>
.common-pagination :deep(.el-pagination) {
  padding: 0 24px !important;
}
</style>
