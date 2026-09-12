import api from './index'

export const warehouseApi = {
  // 统计看板（总物品 / 在库 / 借出领用 / 低于预警 + 预警明细）
  // part_type: '治具' | '耗材'，按 Tab 分别统计，避免总治具/总耗材混在一起
  stats: (params) => api.get('/warehouse/stats', { params }),
  // 物品列表（keyword 名称/型号/借用人/领用人；part_type 治具/耗材；low_stock 仅低库存）
  list: (params) => api.get('/warehouse/parts', { params }),
  detail: (id) => api.get(`/warehouse/parts/${id}`),
  create: (data) => api.post('/warehouse/parts', data),
  update: (id, data) => api.put(`/warehouse/parts/${id}`, data),
  delete: (id) => api.delete(`/warehouse/parts/${id}`),
  // 治具借出 / 归还
  borrow: (id, data) => api.post(`/warehouse/parts/${id}/borrow`, data),
  returnBack: (id, data) => api.post(`/warehouse/parts/${id}/return`, data),
  // 治具转维修 / 维修完成
  toRepair: (id, data) => api.post(`/warehouse/parts/${id}/to-repair`, data),
  finishRepair: (id, data) => api.post(`/warehouse/parts/${id}/finish-repair`, data),
  // 治具报失 / 报损
  loss: (id, data) => api.post(`/warehouse/parts/${id}/loss`, data),
  damaged: (id, data) => api.post(`/warehouse/parts/${id}/damaged`, data),
  // 借出记录列表（active_only: true 只看未归还的）
  borrowRecords: (id, active_only = true) => api.get(`/warehouse/parts/${id}/borrow-records`, { params: { active_only } }),
  // 耗材领用 / 补货
  consume: (id, data) => api.post(`/warehouse/parts/${id}/consume`, data),
  restock: (id, data) => api.post(`/warehouse/parts/${id}/restock`, data),
  // 批量导入（Excel：.xlsx / .xls）
  importParts: (formData) => api.post('/warehouse/parts/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  }),
  // 借出/领用操作流水（全部物品）
  transactions: (params) => api.get('/warehouse/transactions', { params }),
  // 编辑出入库记录备注
  updateTxRemark: (txId, remark) => api.put(`/warehouse/transactions/${txId}/remark`, { remark }),
}
