// src/composables/useCrudList.js
// ============================================================================
// 复用层：统一"列表 CRUD"骨架
//   - filters / loading / list / page、loadData
//   - handleDelete（调 confirmDelete + API delete + toast + reload）
//   - handleImport / handleFileChange（文件 input click → formData 上传 → toast）
//   - handleExport（API 导出）
// —— 13 个业务页面里几乎一模一样的这段代码，现在一行调用即可
// ============================================================================
import { ref, reactive, onMounted } from 'vue'
import { useNotify } from './useNotify'

/**
 * @param {object} api          业务 API 对象，必须包含：list / delete / import / export / [update, create]
 * @param {object} opts
 *   @param {Function} defaultFilters     () => object  默认筛选条件
 *   @param {object}   pagerDefaults      { page:1, size:20 }
 *   @param {boolean}  autoLoadOnMounted  默认 true
 *   @param {string}   deleteLabelProp    删除确认时显示的 item 字段名，例如 'device_id' / 'name'
 */
export function useCrudList(api, opts = {}) {
  const { toast, confirmDelete, notifyError } = useNotify()

  const defaultFilters = (opts.defaultFilters && (typeof opts.defaultFilters === 'function'))
    ? opts.defaultFilters
    : () => ({})

  const filters  = reactive({ page: 1, size: opts.pageSize || 20, ...defaultFilters() })
  const total    = ref(0)
  const loading  = ref(false)
  const list     = ref([])
  const fileRef  = ref(null)    // 指向隐藏的 <input type="file" ref="xxx">

  /** 重置筛选条件到默认值并自动加载列表 */
  const resetFilters = () => {
    Object.keys(filters).forEach(k => delete filters[k])
    Object.assign(filters, { page: 1, size: opts.pageSize || 20, ...defaultFilters() })
    loadData()
  }

  /** 通用加载列表：统一 loading + 处理返回结构两种情况（{ list, total } 或 数组） */
  const loadData = async () => {
    if (!api || !api.list) return
    loading.value = true
    try {
      const data = await api.list(filters)
      if (data && Array.isArray(data.list)) {
        list.value  = data.list
        total.value = typeof data.total === 'number' ? data.total : (data.list?.length || 0)
      } else if (Array.isArray(data)) {
        list.value  = data
        total.value = data.length
      } else {
        list.value  = []
        total.value = 0
      }
    } catch (e) {
      list.value  = []
      total.value = 0
      notifyError(e, '加载列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 通用删除：弹窗 → 调 api.delete → toast → 刷新
   * @param {object|string|number} row
   * @param {object} o
   *   @param {string}  label            显示名（优先）
   *   @param {string}  labelProp        取 row 里哪个字段（labelProp:'name' → '张三'）
   *   @param {string}  successMsg
   *   @param {Function} extra            额外异步步骤（比如先刷新一下再删除？）
   */
  const handleDelete = async (row, o = {}) => {
    let id
    if (typeof row === 'object') {
      if (o.idProp) {
        id = row[o.idProp]
      } else {
        id = row.id
      }
    } else {
      id = row
    }
    if (id == null) return
    let label = o.label || ''
    if (!label && o.labelProp && typeof row === 'object') label = row[o.labelProp]
    const ok = await confirmDelete(label, o.extraMsg || '')
    if (!ok) return
    try {
      await api.delete(id)
      toast.success(o.successMsg || '删除成功')
      if (o.onDeleted) await o.onDeleted(row)
      await loadData()
    } catch (e) {
      notifyError(e, o.failMsg || '删除失败')
    }
  }

  /** 导入：先点隐藏 input 选文件 → handleFileChange 处理上传 */
  const triggerImport = () => fileRef.value && fileRef.value.click()

  const handleFileChange = async (e, o = {}) => {
    const file = e?.target?.files?.[0]
    if (!file) return
    if (!api || !api.import) {
      toast.warn('当前模块未配置导入接口')
      e.target.value = ''
      return
    }
    const fd = new FormData()
    const fileField = o.fileField || 'file'
    if (o.extraFormData) {
      Object.entries(o.extraFormData).forEach(([k, v]) => fd.append(k, v))
    }
    fd.append(fileField, file)
    try {
      await api.import(fd)
      toast.success(o.successMsg || '导入成功')
      if (o.onImported) await o.onImported()
      await loadData()
    } catch (e) {
      notifyError(e, o.failMsg || '导入失败，请检查文件格式后重试')
    } finally {
      // 清空 input，下次选同一个文件依然触发 change
      if (e?.target) e.target.value = ''
    }
  }

  /** 导出：直接下载 blob 或交给 API 层处理 */
  const handleExport = async (o = {}) => {
    if (!api || !api.export) { toast.warn('当前模块未配置导出接口'); return }
    try {
      await api.export({ ...filters, ...(o.extraParams || {}) })
      if (o.successMsg) toast.success(o.successMsg)
    } catch (e) {
      notifyError(e, o.failMsg || '导出失败')
    }
  }

  /** 分页 change —— CommonPagination 发的是一个对象 { page, pageSize, totalPages } */
  const onPagerChange = (payload) => {
    if (!payload || typeof payload !== 'object') return
    if (typeof payload.page === 'number')     filters.page = payload.page
    if (typeof payload.pageSize === 'number') filters.size = payload.pageSize
    loadData()
  }

  // 默认 onMounted 自动加载一次
  if (opts.autoLoadOnMounted !== false) {
    onMounted(() => loadData())
  }

  return {
    // 状态
    filters, list, total, loading, fileRef,
    // 基础动作
    resetFilters, loadData, onPagerChange,
    // CRUD 动作
    handleDelete,
    triggerImport, handleFileChange,
    handleExport,
  }
}
