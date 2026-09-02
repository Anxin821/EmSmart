<template>
  <!--
    StatCard —— 通用统计卡组件
    与 styles.css 里的 .stat-card 语义 1:1 对应，只是抽成独立组件便于 Dashboard 页复用
    （1 处改卡片样式 = 所有页面 20+ 张卡一起变，避免 CSS class 复制粘贴）
  -->
  <div
    class="stat-card"
    :class="[colorClass, { clickable }]"
    :style="cardStyle"
    @click="onClick"
  >
    <div class="icon-box"><span :class="icon"></span></div>
    <div class="num">
      <slot name="num">{{ displayNum }}</slot>
    </div>
    <div class="label">
      <slot name="label">{{ label }}</slot>
    </div>
    <span
      v-if="delta !== undefined && delta !== null && delta !== ''"
      class="delta"
      :class="deltaClass"
    >
      <slot name="delta">{{ delta }}</slot>
    </span>
  </div>
</template>

<script setup>
/**
 * 对外契约：
 * props:
 *   color   —— 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'gray'（默认 blue）
 *   icon    —— bootstrap-icons class，如 'bi bi-check-circle-fill'
 *   num     —— 展示的数字 / 文本（也可用 slot #num 自定义渲染带单位等）
 *   label   —— 描述文字（如 "正常运行（台）"）
 *   delta?  —— 右上角小徽标文字（如 "正常率 98%"），传 ''/undefined/null 则不显示
 *   deltaType? —— 'up' | 'down' | 'muted'（默认 muted）
 *   clickable? boolean —— 整张卡是否鼠标可点击（cursor pointer + 轻微 hover）
 * emits:
 *   'click' —— clickable=true 时点击整张卡触发
 */
import { computed } from 'vue'

const props = defineProps({
  color:     { type: String, default: 'blue' },
  icon:      { type: String, default: 'bi bi-graph-up' },
  num:       { type: [String, Number], default: 0 },
  label:     { type: String, default: '' },
  delta:     { type: [String, Number], default: '' },
  deltaType: { type: String, default: 'muted' },
  clickable: { type: Boolean, default: false }
})
const emit = defineEmits(['click'])

const colorClass = computed(() => {
  const valid = ['blue','green','red','yellow','purple','gray']
  return valid.includes(props.color) ? props.color : 'blue'
})
const deltaClass = computed(() => {
  const valid = ['up','down','muted']
  return valid.includes(props.deltaType) ? props.deltaType : 'muted'
})
const displayNum = computed(() => props.num ?? 0)
const cardStyle = computed(() =>
  props.clickable
    ? { cursor: 'pointer', transition: 'transform .15s ease, box-shadow .15s ease' }
    : {}
)
// clickable 时点击整张卡向外抛出 click，供看板做“点击数字下钻”等交互
const onClick = () => { if (props.clickable) emit('click') }
</script>

<style scoped>
/* 与全局 styles.css 中 .stat-card 保持一致的 Grid 容器布局（关键）
   —— 避免抽成组件后，scoped 样式缺失 display:grid，
      导致 .icon-box（grid-row 1/span 2 col 1）无法生效，
      num/label 会与 .icon-box 在 44px 左列重叠或整体错位（"icon-box 挡文字" 根因之一）*/
.stat-card {
  position: relative;
  padding: 16px 18px;
  border-radius: var(--radius, 12px);
  background: var(--c-card, #ffffff);
  border: 1px solid var(--c-divider, #E2E8F0);
  box-shadow: var(--shadow-card, 0 2px 10px rgba(15,23,42,.05));
  display: grid;
  grid-template-columns: 44px 1fr;
  grid-template-rows: auto auto;
  column-gap: 14px;
  row-gap: 6px;
  align-items: center;
  min-height: 96px;
  transition: transform .15s, box-shadow .15s;
  overflow: hidden;
}
.stat-card:hover {
  transform: var(--stat-hover-transform, translateY(-1px));
  box-shadow: 0 4px 14px rgba(15,23,42,.06), 0 0 0 1px rgba(44,92,232,.08);
}
/* 可点击卡：右下角 chevron 提示“可下钻”，解决纯 cursor:pointer 无视觉暗示的问题 */
.stat-card.clickable::after {
  content: "\203A";
  position: absolute;
  right: 14px; bottom: 10px;
  font-size: 18px;
  line-height: 1;
  color: var(--c-text-mute, #94A3B8);
  opacity: .65;
  transition: transform .15s ease, color .15s ease, opacity .15s ease;
}
.stat-card.clickable:hover::after {
  color: var(--primary, #2C5CE8);
  opacity: 1;
  transform: translateX(2px);
}
/* 保证 scoped 下也能继承 num / label 列位置（Grid 规范：必须写 grid-column 才会对齐第二列）*/
:deep(.num)   {
  grid-column: 2;
  /* delta 占右上角约 80px，预留右侧空间避免数字和 delta 文字叠 */
  padding-right: 84px;
  max-width: 100%;
  box-sizing: border-box;
}
:deep(.label) {
  grid-column: 2;
  /* 与 num 对齐到左侧同一垂直线，右侧同样避让 delta 区块 */
  padding-right: 84px;
  max-width: 100%;
  box-sizing: border-box;
}
:deep(.delta) { grid-column: auto; }
</style>
