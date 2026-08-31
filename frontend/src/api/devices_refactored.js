/**
 * 重构后的devices API - 使用工厂函数
 * 展示如何使用工厂函数减少重复代码
 */

import api from './index'
import { createCrudApi, createOptionsApi } from './factory'

// 使用工厂函数创建标准CRUD API
export const devicesApi = createCrudApi('/devices', {
  // 自定义方法可以覆盖或扩展默认方法
  customMethods: {
    // 自定义导入方法（保留原始逻辑）
    import: (formData) => api.post('/devices/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    
    // 自定义导出方法（保留原始逻辑）
    export: (params) => window.open(`/api/v1/devices/export/excel?${new URLSearchParams(params)}`, '_blank'),
    
    // 自定义详情方法（如果需要不同的路径）
    detail: (id) => api.get(`/devices/detail/${id}`)
  }
})

// 使用工厂函数创建选项API
export const optionsApi = createOptionsApi('/options')

/**
 * 原始devices.js文件对比：
 * 
 * 原始代码（30行）：
 * import api from './index'
 * 
 * export const optionsApi = {
 *   lines: () => api.get('/options/lines'),
 *   projects: () => api.get('/options/projects'),
 *   statuses: (module) => api.get(`/options/statuses/${module}`),
 *   priorities: () => api.get('/options/priorities'),
 *   severities: () => api.get('/options/severities'),
 *   deviceTypes: () => api.get('/options/device-types')
 * }
 * 
 * export const devicesApi = {
 *   list: (params) => api.get('/devices', { params }),
 *   detail: (id) => api.get(`/devices/detail/${id}`),
 *   create: (data) => api.post('/devices', data),
 *   update: (id, data) => api.put(`/devices/${id}`, data),
 *   delete: (id) => api.delete(`/devices/${id}`),
 *   import: (formData) => api.post('/devices/import', formData, {
 *     headers: { 'Content-Type': 'multipart/form-data' }
 *   }),
 *   export: (params) => window.open(`/api/v1/devices/export/excel?${new URLSearchParams(params)}`, '_blank')
 * }
 * 
 * 重构后代码（15行，减少50%）：
 * - 移除了重复的CRUD方法定义
 * - 通过工厂函数自动生成标准方法
 * - 保持对自定义方法的支持
 * - 统一了错误处理和配置
 */