/**
 * Composables 统一导出文件
 * 
 * 使用示例：
 * import { useCrudList, useFilterFields, commonOptions } from '@/composables'
 */

// 导出所有组合函数
export { useCrudList } from './useCrudList'
export { useCrudModal } from './useCrudModal'
export { useFilterFields } from './useFilterFields'

// 注意：useNotify 可能包含内部状态，按需导出
export { useNotify } from './useNotify'

// 导出常用选项和工具
export { commonOptions } from './useFilterFields'

/**
 * 常用的组合函数工具集
 */
export const composableUtils = {
  /**
   * 创建CRUD页面标准配置
   * @param {object} api - API对象
   * @param {object} options - 配置选项
   * @returns {object} 包含列表和模态框的组合
   */
  createCrudConfig: (api, options = {}) => {
    const listConfig = useCrudList(api.list, {
      defaultFilters: options.defaultFilters || (() => ({})),
      pageSize: options.pageSize || 20,
      ...options.listOptions
    })
    
    const modalConfig = useCrudModal(options.emptyForm || (() => ({})), {
      beforeShow: options.beforeShow,
      onSaved: options.onSaved
    })
    
    return {
      ...listConfig,
      ...modalConfig,
      // 常用组合方法
      handleSave: options.handleSave || (async () => {
        return modalConfig.submit(async ({ form, isEdit, editing }) => {
          return isEdit 
            ? await api.update(editing.id, form)
            : await api.create(form)
        }, {
          successMsg: options.successMsg || ({ isEdit }) => isEdit ? '修改成功' : '新增成功',
          onSaved: () => listConfig.loadData(),
          ...options.saveOptions
        })
      })
    }
  },
  
  /**
   * 创建标准过滤器配置
   * @param {Array} fieldDefinitions - 字段定义
   * @returns {import('vue').ComputedRef<Array>} 过滤器字段数组
   */
  createStandardFilters: (fieldDefinitions) => {
    const { createFields } = useFilterFields()
    return createFields(fieldDefinitions)
  }
}

// 默认导出所有内容
export default {
  useCrudList,
  useCrudModal,
  useFilterFields,
  useNotify,
  commonOptions,
  composableUtils
}