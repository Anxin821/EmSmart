/**
 * useFilterFields - 过滤器配置辅助函数
 * 
 * 用于简化 CommonFilterBar 组件的 fields 配置，减少重复代码
 * 
 * 使用示例：
 * 
 * 1. 基本使用：
 * const { createInput, createSelect, createDate, createFields } = useFilterFields()
 * 
 * const filterFields = createFields([
 *   createInput('keyword', '用户名 / 姓名 / 邮箱', { label: '' }),
 *   createSelect('role', '角色', [
 *     { label: '全部角色', value: '' },
 *     { label: 'admin', value: 'admin' },
 *     { label: 'engineer', value: 'engineer' }
 *   ])
 * ])
 * 
 * 2. 高级使用：
 * const { input, select, date, divider, fields } = useFilterFields()
 * 
 * const filterFields = fields([
 *   input('keyword', '搜索关键词', { autoSearch: false }),
 *   select('status', '状态', statusOptions, { autoSearch: true }),
 *   divider(),
 *   date('startDate', '开始日期'),
 *   date('endDate', '结束日期', { dateType: 'date' })
 * ])
 * 
 * 3. 快捷函数：
 * const { keywordInput, statusSelect, lineSelect } = useFilterFields()
 * 
 * const filterFields = [
 *   keywordInput('设备ID / 名称 / IP / 负责人'),
 *   lineSelect(lines, { label: '产线' }),
 *   statusSelect(['正常', '故障', '保养中'], { label: '状态' })
 * ]
 */

import { computed } from 'vue'

/**
 * 创建过滤器配置辅助函数
 */
export function useFilterFields() {
  /**
   * 创建输入框过滤器
   * @param {string} key - 字段键名
   * @param {string} placeholder - 占位符文本
   * @param {object} options - 附加选项
   * @returns {object} 输入框配置对象
   */
  const createInput = (key, placeholder, options = {}) => ({
    type: 'input',
    key,
    placeholder,
    autoSearch: false,
    clearable: true,
    showSearchIcon: true,
    ...options
  })

  /**
   * 创建下拉选择过滤器
   * @param {string} key - 字段键名
   * @param {string} label - 标签文本
   * @param {Array} options - 选项数组 [{label, value}]
   * @param {object} config - 配置选项
   * @returns {object} 下拉选择配置对象
   */
  const createSelect = (key, label, options = [], config = {}) => ({
    type: 'select',
    key,
    label,
    placeholder: config.placeholder || `请选择${label}`,
    options: [
      { label: `全部${label}`, value: '' },
      ...options.map(opt => typeof opt === 'string' 
        ? { label: opt, value: opt }
        : opt
      )
    ],
    autoSearch: true,
    clearable: true,
    ...config
  })

  /**
   * 创建日期选择过滤器
   * @param {string} key - 字段键名
   * @param {string} label - 标签文本
   * @param {object} config - 配置选项
   * @returns {object} 日期选择配置对象
   */
  const createDate = (key, label, config = {}) => ({
    type: 'date',
    key,
    label,
    placeholder: config.placeholder || `选择${label}`,
    dateType: config.dateType || 'date',
    autoSearch: true,
    ...config
  })

  /**
   * 创建分隔线
   * @returns {object} 分隔线配置对象
   */
  const createDivider = () => ({
    type: 'divider'
  })

  /**
   * 创建字段数组（计算属性包装）
   * @param {Array} fields - 字段配置数组
   * @returns {import('vue').ComputedRef<Array>} 计算属性字段数组
   */
  const createFields = (fields) => {
    return computed(() => fields.filter(field => field !== null && field !== undefined))
  }

  /**
   * 创建动态字段（非计算属性）
   * @param {Array} fields - 字段配置数组
   * @returns {Array} 字段数组
   */
  const createStaticFields = (fields) => {
    return fields.filter(field => field !== null && field !== undefined)
  }

  /**
   * 创建关键词输入框（常用快捷函数）
   * @param {string} placeholder - 占位符文本
   * @param {object} options - 附加选项
   * @returns {object} 关键词输入框配置
   */
  const createKeywordInput = (placeholder = '请输入关键词', options = {}) => 
    createInput('keyword', placeholder, { label: '', ...options })

  /**
   * 创建状态选择器（常用快捷函数）
   * @param {Array} statusOptions - 状态选项数组
   * @param {object} config - 配置选项
   * @returns {object} 状态选择器配置
   */
  const createStatusSelect = (statusOptions = ['正常', '故障', '保养中'], config = {}) =>
    createSelect('status', config.label || '状态', statusOptions, config)

  /**
   * 创建产线选择器（常用快捷函数）
   * @param {Array} lines - 产线数组
   * @param {object} config - 配置选项
   * @returns {object} 产线选择器配置
   */
  const createLineSelect = (lines = [], config = {}) =>
    createSelect('line', config.label || '产线', lines, config)

  /**
   * 创建年份输入框（常用快捷函数）
   * @param {object} config - 配置选项
   * @returns {object} 年份输入框配置
   */
  const createYearInput = (config = {}) =>
    createInput('year', '请输入年份（数字）', { label: '年', autoSearch: false, ...config })

  /**
   * 创建月份输入框（常用快捷函数）
   * @param {object} config - 配置选项
   * @returns {object} 月份输入框配置
   */
  const createMonthInput = (config = {}) =>
    createInput('month', '请输入月份（数字）', { label: '月', autoSearch: false, ...config })

  /**
   * 创建周数输入框（常用快捷函数）
   * @param {object} config - 配置选项
   * @returns {object} 周数输入框配置
   */
  const createWeekInput = (config = {}) =>
    createInput('week', '请输入周数（数字）', { label: '周', autoSearch: false, ...config })

  /**
   * 创建时间范围过滤器
   * @param {object} config - 配置选项
   * @returns {Array} 时间范围字段数组
   */
  const createDateRange = (config = {}) => {
    const startConfig = config.start || {}
    const endConfig = config.end || {}
    
    return [
      createDate('startDate', startConfig.label || '开始日期', startConfig),
      createDivider(),
      createDate('endDate', endConfig.label || '结束日期', endConfig)
    ]
  }

  /**
   * 验证字段配置
   * @param {object} field - 字段配置对象
   * @returns {boolean} 是否有效
   */
  const validateField = (field) => {
    if (!field || typeof field !== 'object') return false
    if (field.type === 'divider') return true
    if (!field.key || !field.type) return false
    return ['input', 'select', 'date'].includes(field.type)
  }

  /**
   * 转换选项数组格式
   * @param {Array} items - 原始选项数组
   * @param {object} options - 转换选项
   * @returns {Array} 标准格式选项数组
   */
  const normalizeOptions = (items, options = {}) => {
    const { labelKey = 'label', valueKey = 'value', includeAll = true } = options
    
    const normalized = items.map(item => {
      if (typeof item === 'string') {
        return { label: item, value: item }
      }
      if (typeof item === 'object' && item !== null) {
        return { label: item[labelKey] || item.name || item.label, value: item[valueKey] || item.id || item.value }
      }
      return { label: String(item), value: item }
    })
    
    if (includeAll) {
      return [{ label: '全部', value: '' }, ...normalized]
    }
    
    return normalized
  }

  return {
    // 基础创建函数
    createInput,
    createSelect,
    createDate,
    createDivider,
    createFields,
    createStaticFields,
    
    // 快捷函数（完整名称）
    createKeywordInput,
    createStatusSelect,
    createLineSelect,
    createYearInput,
    createMonthInput,
    createWeekInput,
    createDateRange,
    
    // 快捷函数（简写）
    input: createInput,
    select: createSelect,
    date: createDate,
    divider: createDivider,
    fields: createFields,
    staticFields: createStaticFields,
    
    // 常用快捷函数（进一步简化）
    keywordInput: createKeywordInput,
    statusSelect: createStatusSelect,
    lineSelect: createLineSelect,
    yearInput: createYearInput,
    monthInput: createMonthInput,
    weekInput: createWeekInput,
    dateRange: createDateRange,
    
    // 工具函数
    validateField,
    normalizeOptions
  }
}

/**
 * 预定义的常用选项
 */
export const commonOptions = {
  // 状态选项
  statusOptions: [
    { label: '正常', value: '正常' },
    { label: '故障', value: '故障' },
    { label: '保养中', value: '保养中' },
    { label: '离线', value: '离线' },
    { label: '运行中', value: '运行中' }
  ],
  
  // 角色选项
  roleOptions: [
    { label: 'admin', value: 'admin' },
    { label: 'engineer', value: 'engineer' },
    { label: 'viewer', value: 'viewer' },
    { label: 'operator', value: 'operator' },
    { label: 'manager', value: 'manager' }
  ],
  
  // 优先级选项
  priorityOptions: [
    { label: '低', value: '低' },
    { label: '中', value: '中' },
    { label: '高', value: '高' },
    { label: '紧急', value: '紧急' }
  ],
  
  // 严重程度选项
  severityOptions: [
    { label: '低', value: '低' },
    { label: '中', value: '中' },
    { label: '高', value: '高' },
    { label: '严重', value: '严重' }
  ],
  
  // 是否选项
  booleanOptions: [
    { label: '是', value: true },
    { label: '否', value: false }
  ],
  
  // 是/否选项（字符串）
  yesNoOptions: [
    { label: '是', value: '是' },
    { label: '否', value: '否' }
  ]
}

/**
 * 默认导出
 */
export default {
  useFilterFields,
  commonOptions
}