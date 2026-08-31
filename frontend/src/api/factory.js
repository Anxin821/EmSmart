/**
 * API工厂函数 - 统一生成标准CRUD API接口
 * 
 * 使用示例：
 * 
 * 1. 基本CRUD API:
 * import { createCrudApi } from './factory'
 * export const devicesApi = createCrudApi('/devices')
 * 
 * 2. 自定义导出函数:
 * export const devicesApi = {
 *   ...createCrudApi('/devices'),
 *   import: (formData) => api.post('/devices/import', formData, {
 *     headers: { 'Content-Type': 'multipart/form-data' }
 *   }),
 *   export: (params) => window.open(`/api/v1/devices/export/excel?${new URLSearchParams(params)}`, '_blank')
 * }
 * 
 * 3. 选项类API:
 * export const optionsApi = createOptionsApi('/options')
 */

import api from './index'

/**
 * 创建标准CRUD API接口
 * @param {string} basePath - API基础路径，如 '/devices'
 * @param {object} options - 配置选项
 * @param {string} options.idParam - ID参数名，默认 ':id'
 * @param {object} options.customMethods - 自定义方法
 * @returns {object} CRUD API对象
 */
export function createCrudApi(basePath, options = {}) {
  const { idParam = ':id', customMethods = {} } = options
  
  const baseMethods = {
    // 列表查询
    list: (params) => api.get(basePath, { params }),
    
    // 获取详情
    detail: (id) => api.get(`${basePath}/${id}`),
    
    // 创建记录
    create: (data) => api.post(basePath, data),
    
    // 更新记录
    update: (id, data) => api.put(`${basePath}/${id}`, data),
    
    // 删除记录
    delete: (id) => api.delete(`${basePath}/${id}`),
    
    // 批量删除
    bulkDelete: (ids) => api.delete(`${basePath}/batch`, { data: { ids } }),
    
    // 导入功能 (基础实现，通常需要自定义)
    import: (formData, config = {}) => {
      const defaultConfig = {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      }
      return api.post(`${basePath}/import`, formData, { ...defaultConfig, ...config })
    },
    
    // 导出功能 (基础实现，通常需要自定义)
    export: (params, config = {}) => {
      const defaultConfig = {
        responseType: 'blob'
      }
      return api.get(`${basePath}/export`, { params, ...defaultConfig, ...config })
    },
    
    // 下载导出文件 (使用window.open方式)
    exportToExcel: (params) => {
      const queryString = new URLSearchParams(params).toString()
      return window.open(`/api/v1${basePath}/export/excel?${queryString}`, '_blank')
    },
    
    // 获取选项
    options: (optionType) => api.get(`${basePath}/options/${optionType}`)
  }
  
  // 合并基础方法和自定义方法
  return {
    ...baseMethods,
    ...customMethods
  }
}

/**
 * 创建选项类API (用于获取下拉选项等)
 * @param {string} basePath - 选项API基础路径，如 '/options'
 * @returns {object} 选项API对象
 */
export function createOptionsApi(basePath = '/options') {
  return {
    // 获取产线选项
    lines: () => api.get(`${basePath}/lines`),
    
    // 获取项目选项
    projects: () => api.get(`${basePath}/projects`),
    
    // 获取状态选项
    statuses: (module) => api.get(`${basePath}/statuses/${module || ''}`),
    
    // 获取优先级选项
    priorities: () => api.get(`${basePath}/priorities`),
    
    // 获取严重程度选项
    severities: () => api.get(`${basePath}/severities`),
    
    // 获取设备类型选项
    deviceTypes: () => api.get(`${basePath}/device-types`),
    
    // 通用选项获取方法
    get: (optionKey, params) => api.get(`${basePath}/${optionKey}`, { params })
  }
}

/**
 * 创建通用API工具函数
 */
export const apiUtils = {
  /**
   * 处理API响应错误
   * @param {Error} error - 错误对象
   * @param {string} defaultMessage - 默认错误消息
   */
  handleError: (error, defaultMessage = '请求失败') => {
    const message = error.response?.data?.message || error.message || defaultMessage
    return Promise.reject(new Error(message))
  },
  
  /**
   * 处理文件下载响应
   * @param {Blob} blob - 文件数据
   * @param {string} filename - 文件名
   */
  downloadFile: (blob, filename) => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },
  
  /**
   * 创建FormData对象
   * @param {object} data - 表单数据
   * @returns {FormData} FormData对象
   */
  createFormData: (data) => {
    const formData = new FormData()
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value)
      }
    })
    return formData
  }
}

/**
 * 创建组合API - 将多个API组合在一起
 * @param {object} apis - API对象集合
 * @returns {object} 组合后的API对象
 */
export function combineApis(apis) {
  return Object.entries(apis).reduce((combined, [name, api]) => {
    combined[name] = api
    return combined
  }, {})
}

export default {
  createCrudApi,
  createOptionsApi,
  apiUtils,
  combineApis
}