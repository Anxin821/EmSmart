<template>
  <CommonModal
    v-model:visible="isShown"
    :title="title"
    :width="width"
    :ok-loading="loading"
    :ok-text="okText"
    :cancel-text="cancelText"
    :close-on-click-modal="false"
    align-center
    title-icon="bi bi-exclamation-triangle-fill"
    :title-icon-color="danger ? '#D97706' : '#2C5CE8'"
    @ok="onConfirmClick"
    @cancel="$emit('cancel')"
  >
    <div class="cd-layout">
      <!-- 左侧：大圆图标（黄=危险删除 / 蓝=普通确认） -->
      <div class="cd-icon-circle" :class="{ warn: danger, info: !danger }">
        <span :class="icon"></span>
      </div>
      <!-- 右侧：主标题 + 描述（可带高亮 label） -->
      <div class="cd-text">
        <div class="cd-title">{{ titleText }}</div>
        <div class="cd-desc" v-html="descHtml"></div>
        <div v-if="hint" class="cd-hint">{{ hint }}</div>
      </div>
    </div>
  </CommonModal>
</template>

<script setup>
import { computed, ref } from 'vue'
import CommonModal from './CommonModal.vue'

const props = defineProps({
  // ========== 外部驱动：v-model:visible ==========
  visible:     { type: Boolean, default: false },
  // ========== 内容 ==========
  /** 弹窗标题 */
  title:       { type: String,  default: '删除确认' },
  /** 弹窗内第一行大字（主描述） */
  titleText:   { type: String,  default: '确定要删除该条目？' },
  /** 条目名称（会被 <b> 加粗，显示为"您即将删除「xxx」..."） */
  itemLabel:   { type: String,  default: '' },
  /** 条目类型（"职责条目"/"岗位"/"设备"/"用户"），用于描述文本 */
  itemKind:    { type: String,  default: '条目' },
  /** 补充说明文字（可选） */
  hint:        { type: String,  default: '该操作无法撤销，是否继续？' },
  /** 是否为危险删除（true=黄图标 + 红色确认按钮） */
  danger:      { type: Boolean, default: true },
  /** 自定义 emoji 图标（danger 默认 ⚠️，info 默认 ℹ️） */
  icon:        { type: String,  default: '' },
  // ========== 外观 ==========
  width:       { type: String,  default: '460px' },
  okText:      { type: String,  default: '确认删除' },
  cancelText:  { type: String,  default: '取消' },
  /** ok 按钮 loading（外部传入，避免内部二次状态） */
  loading:     { type: Boolean, default: false },
})
const emit = defineEmits([
  'update:visible',
  'ok',      // 用户点"确认删除/确认" → 父级执行真正删除，完成后再关闭（或外部 loading 控制）
  'cancel',  // 用户点"取消"
])

const isShown = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const descHtml = computed(() => {
  if (props.itemLabel) {
    return `您即将删除${props.itemKind ? `「${props.itemKind}」` : ''} <b class="cd-label">"${props.itemLabel}"</b>。`
  }
  return `您即将删除该${props.itemKind || '条目'}。`
})

const onConfirmClick = () => emit('ok')
</script>

<style scoped>
.cd-layout {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 4px 2px 6px;
}
.cd-icon-circle {
  width: 48px; height: 48px;
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.cd-icon-circle.warn {
  background: #FEF3C7;
  color: #D97706;
  box-shadow: 0 0 0 4px rgba(253, 224, 71, 0.28);
}
.cd-icon-circle.info {
  background: #DBEAFE;
  color: #2C5CE8;
  box-shadow: 0 0 0 4px rgba(147, 197, 253, 0.28);
}
.cd-text {
  flex: 1;
  min-width: 0;
  display: flex; flex-direction: column; gap: 6px;
  padding-top: 2px;
}
.cd-title {
  font-size: 15px;
  font-weight: 600;
  color: #0F172A;
  line-height: 1.4;
}
.cd-desc {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
}
.cd-label {
  color: #0F172A;
  font-weight: 600;
}
.cd-hint {
  font-size: 12.5px;
  color: #94A3B8;
  letter-spacing: .1px;
}
</style>
