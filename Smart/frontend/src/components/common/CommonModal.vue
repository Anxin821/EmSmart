<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="onUpdateVisible"
    :title="title"
    :width="width"
    :top="top"
    :align-center="alignCenter"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :modal="true"
    :show-close="false"
    :append-to-body="true"
    @open="$emit('open')"
    @opened="$emit('opened')"
    @close="$emit('close')"
    @closed="$emit('closed')"
  >
    <template #header="{ close }">
      <div class="cm-header" :style="headerStyle">
        <div class="cm-title">
          <span
            v-if="titleIcon"
            :class="titleIcon"
            :style="titleIconStyleObj"
          ></span>
          <slot name="title-text">{{ title }}</slot>
        </div>
        <button class="cm-close" @click="handleClose(close)" aria-label="关闭">
          <span class="bi bi-x-lg"></span>
        </button>
      </div>
    </template>

    <div class="cm-body" :style="bodyStyle">
      <slot name="body">
        <slot />
      </slot>
    </div>

    <template #footer>
      <slot v-if="hasCustomFooter" name="footer" :ok="onOk" :cancel="closeByCancel" :okLoading="okLoading" />
      <div v-else-if="showFooter" class="cm-footer">
        <el-button :disabled="okLoading" @click="closeByCancel">
          {{ cancelText }}
        </el-button>
        <el-button type="primary" :loading="okLoading" @click="onOk">
          {{ okText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { useSlots, computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  titleIcon: { type: String, default: '' },
  titleIconColor: { type: String, default: '' },
  width: { type: [String, Number], default: '560px' },
  top: { type: String, default: '12vh' },
  alignCenter: { type: Boolean, default: false },
  okText: { type: String, default: '保存' },
  cancelText: { type: String, default: '取消' },
  showFooter: { type: Boolean, default: true },
  okLoading: { type: Boolean, default: false },
  closeOnClickModal: { type: Boolean, default: true },
  closeOnPressEscape: { type: Boolean, default: true },
  headerStyle: { type: Object, default: () => ({}) },
  bodyStyle: { type: Object, default: () => ({}) }
})
const emit = defineEmits([
  'update:visible', 'ok', 'cancel',
  'open', 'opened', 'close', 'closed'
])

const slots = useSlots()
const hasCustomFooter = computed(() => !!slots.footer)
const titleIconStyleObj = computed(() => ({
  color: props.titleIconColor || 'var(--primary)'
}))

const onUpdateVisible = (v) => emit('update:visible', !!v)
const handleClose = (elClose) => {
  emit('update:visible', false)
  emit('cancel')
  if (typeof elClose === 'function') elClose()
}
const closeByCancel = () => {
  emit('update:visible', false)
  emit('cancel')
}
const onOk = () => emit('ok')
</script>
