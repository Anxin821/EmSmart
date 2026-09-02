<template>
  <div class="common-filter-bar">
    <template v-for="(field, idx) in normalizedFields" :key="field.key || ('divider-' + idx)">
      <!-- 分隔线：竖线，用于字段分组 -->
      <div v-if="field.type === 'divider'" class="divider"></div>

      <!-- 关键词输入框（带搜索 prefix） -->
      <div v-else-if="field.type === 'input'" class="field">
        <label v-if="field.label">{{ field.label }}</label>
        <el-input
          :style="fieldStyle(field)"
          :model-value="getValue(field)"
          @update:model-value="setValue(field, $event)"
          :placeholder="field.placeholder || '请输入关键词'"
          :clearable="field.clearable !== false"
          :prefix-icon="field.prefixIcon || (field.showSearchIcon ? 'Search' : undefined)"
          :suffix-icon="field.suffixIcon"
          :disabled="field.disabled"
          @keyup.enter="onSearch"
          @clear="onSearchIfAuto(field)"
          @change="onSearchIfAuto(field)"
        />
      </div>

      <!-- 下拉选择框 -->
      <div v-else-if="field.type === 'select'" class="field">
        <label v-if="field.label">{{ field.label }}</label>
        <el-select
          :model-value="getValue(field)"
          @update:model-value="setValue(field, $event); onSearchIfAuto(field)"
          :placeholder="field.placeholder || '请选择'"
          :clearable="field.clearable !== false"
          :disabled="field.disabled"
          :style="fieldStyle(field)"
        >
          <el-option
            v-for="opt in (field.options || [])"
            :key="String(opt.value)"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>

      <!-- 日期选择 -->
      <div v-else-if="field.type === 'date'" class="field">
        <label v-if="field.label">{{ field.label }}</label>
        <el-date-picker
          :model-value="getValue(field)"
          @update:model-value="setValue(field, $event); onSearchIfAuto(field)"
          :type="field.dateType || 'date'"
          :placeholder="field.placeholder || '选择日期'"
          :disabled="field.disabled"
          value-format="YYYY-MM-DD"
          :style="fieldStyle(field)"
        />
      </div>
    </template>

    <!-- 业务自定义操作按钮（搜索/重置/新增/导入导出） -->
    <div class="actions" v-if="$slots.actions">
      <slot name="actions" :filters="props.modelValue" :model="props.modelValue" :reset="resetAll" :search="onSearch" />
    </div>
    <div v-else class="actions">
      <el-button type="primary" @click="onSearch">
        <el-icon><Search /></el-icon>搜索
      </el-button>
      <el-button @click="resetAll">
        <el-icon><RefreshRight /></el-icon>重置
      </el-button>
    </div>
  </div>
</template>

<script setup>
/**
 * CommonFilterBar —— 通用筛选条组件（Element Plus 原子组件装配）
 *
 * 对外契约（业务页使用时只需要看这些，内部 Element Plus 变更不影响外部）：
 *   props:
 *     - fields: Array<FieldConfig>
 *         FieldConfig 类型：
 *           { type: 'divider' }                                                     竖线分隔符
 *           { type: 'input',  key, label?, placeholder?, minWidth?, prefixIcon?,
 *                            showSearchIcon?, clearable?, disabled?, autoSearch? }
 *           { type: 'select', key, label, options:[{label,value}], placeholder?,
 *                              minWidth?, clearable?, disabled?, autoSearch? }
 *           { type: 'date',   key, label, dateType?:'date'|'month'|'year',
 *                              minWidth?, disabled?, autoSearch? }
 *     - modelValue: Object（v-model，双向绑定当前筛选条件对象）
 *   emits:
 *     'update:modelValue' —— 当任意字段变更时
 *     'search'            —— 用户点击"搜索"或字段设置了 autoSearch=true 变更时
 *     'reset'             —— 点击"重置"
 *   slots:
 *     #actions —— 自定义操作区（把搜索/重置/新增/导入导出按钮全交给业务页控制）
 *                 作用域：{ filters, model（同 filters 别名兼容旧写法）, reset, search }
 */
import { computed } from 'vue'
import { Search, RefreshRight } from '@element-plus/icons-vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
  modelValue: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update:modelValue', 'search', 'reset'])

// 允许 fields 里面穿插函数式分组（虽然我们目前都是静态数组）
const normalizedFields = computed(() => (props.fields || []).filter(Boolean))

const getValue = (field) => {
  if (!field.key) return undefined
  return props.modelValue[field.key]
}
const setValue = (field, val) => {
  if (!field.key) return
  emit('update:modelValue', { ...props.modelValue, [field.key]: val })
}

// 宽度样式直接作用在“控件”（el-input/el-select/el-date-picker）上，而不是作用在
// label + 控件 的整块 .field 上——否则 label 会挤占控件宽度，导致下拉框里的
// “全部产线 / 全部优先级”、输入框里的占位符被截断显示不全。
const fieldStyle = (field) => {
  const toPx = (v) => (typeof v === 'number' ? v + 'px' : v)
  const style = {}
  // flex 优先：交给弹性布局，不强制固定宽度
  if (field.flex) { style.flex = field.flex; style.minWidth = 0; return style }
  // width 优先，其次 minWidth；都当作控件的固定宽度（下拉/输入需要明确宽度才能完整显示文字）
  const w = field.width || field.minWidth
  if (w) {
    style.width = toPx(w)
    style.minWidth = toPx(w)
  } else {
    // 未指定宽度：给一个按类型的默认宽度，保证占位符/选项文字完整可见
    const def = (field.type === 'input') ? 180 : 150
    style.width = def + 'px'
    style.minWidth = def + 'px'
  }
  return style
}

// 字段 autoSearch=true（或未设置时默认对 select/date 自动触发）
const onSearchIfAuto = (field) => {
  const shouldAuto = (field.autoSearch !== undefined)
    ? field.autoSearch
    : (field.type === 'select' || field.type === 'date')   // 下拉/日期：默认改完即搜（符合我们 Devices 页 @change=loadData）
  if (shouldAuto) emit('search')
}
const onSearch = () => emit('search')
const resetAll = () => {
  const reset = {}
  for (const f of normalizedFields.value) {
    if (f && f.key) reset[f.key] = (f.defaultValue !== undefined) ? f.defaultValue : ''
  }
  emit('update:modelValue', reset)
  emit('reset')
  emit('search')
}
</script>
