// src/composables/useNotify.js
// ============================================================================
// 复用层：统一的"消息提示 + 确认弹窗"封装
// —— 让所有业务页面都不用再手动 import ElMessage/ElMessageBox，也不用关心文字、按钮、居中、危险按钮染色、失败回退等细节
// ============================================================================
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 右上角轻提示：成功 / 失败 / 警告 / 消息
 *   toast.success('操作成功')
 *   toast.error('xxx 失败')
 *   toast.warn('请填写必填项')
 */
export const toast = {
  success: (msg, duration = 2200) => ElMessage({ type: 'success', message: msg, duration, showClose: true }),
  error:   (msg, duration = 2800) => ElMessage({ type: 'error',   message: msg || '操作失败', duration, showClose: true }),
  warn:    (msg, duration = 2400) => ElMessage({ type: 'warning', message: msg || '', duration, showClose: true }),
  info:    (msg, duration = 2200) => ElMessage({ type: 'info',    message: msg || '', duration, showClose: true }),
}

/** 从 axios 错误对象里拿出后端给的错误消息 */
const errMsg = (e, fallback = '操作失败') => e?.response?.data?.message || e?.message || fallback

/**
 * 删除确认弹窗：居中 + 警告色 + 危险红色"确认删除"按钮
 * 用法：
 *   const confirmed = await confirmDelete('设备ID：ABC-01')
 *   if (!confirmed) return
 */
export async function confirmDelete(itemLabel = '', extra = '') {
  try {
    await ElMessageBox.confirm(
      `确定删除${itemLabel ? `「${itemLabel}」` : '该条目'}？${extra || '删除后数据不可恢复'}，是否继续？`,
      '删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
        center: true,
        draggable: false,
        closeOnClickModal: false,
      }
    )
    return true
  } catch {
    return false
  }
}

/**
 * 通用确认弹窗（非删除场景，如"确定导出？""确定要提交吗？"）
 */
export async function confirmAction({
  content = '确定执行该操作？',
  title = '操作确认',
  confirmText = '确定',
  cancelText = '取消',
  type = 'info',   // info / warning / success
  danger = false,
} = {}) {
  try {
    await ElMessageBox.confirm(content, title, {
      confirmButtonText: confirmText,
      cancelButtonText: cancelText,
      type,
      center: true,
      draggable: false,
      confirmButtonClass: danger ? 'el-button--danger' : '',
    })
    return true
  } catch {
    return false
  }
}

/** 把 axios 错误格式化成可读错误并 toast，返回格式化后的消息 */
export function notifyError(e, fallback = '操作失败') {
  const msg = errMsg(e, fallback)
  toast.error(msg)
  return msg
}

/** 统一 "try / catch + toast 成功失败" 的包裹器，简化页面里的 handleSave / handleDelete 样板代码 */
export async function runWithToast(opts) {
  const { action, success = '操作成功', fail = '操作失败', onSuccess } = opts || {}
  try {
    const res = await action()
    if (success) toast.success(success)
    onSuccess && (await onSuccess(res))
    return { ok: true, res }
  } catch (e) {
    notifyError(e, fail)
    return { ok: false, error: e }
  }
}

export function useNotify() {
  return { toast, confirmDelete, confirmAction, notifyError, runWithToast, errMsg }
}
