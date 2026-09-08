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

// ============================================================
// 【修改】删除确认弹窗：按模板格式显示
// 模板：确认删除异常 EXC-20260908-001（质量异常 - 测试）？删除后不可恢复。
// ============================================================
/**
 * 删除确认弹窗：居中 + 警告色 + 危险红色"确认删除"按钮
 *
 * 用法1（字符串，兼容旧用法）：
 *   const ok = await confirmDelete('设备ID：ABC-01')
 *
 * 用法2（对象，推荐）：
 *   const ok = await confirmDelete({
 *     name: 'EXC-20260908-001',    // 编号/名称
 *     type: '质量异常',             // 类型
 *     desc: '测试',                 // 描述/现象
 *     prefix: '异常'                // 前缀（可选，如：异常/BUG/工单）
 *   })
 */
export async function confirmDelete(item, extra = '') {
  let name = ''
  let type = ''
  let desc = ''
  let prefix = ''
  let extraMsg = extra || '删除后不可恢复'

  // 判断参数类型：如果是对象，提取字段
  if (typeof item === 'object' && item !== null) {
    // 提取名称
    name = item.name || item.label || item.title || item.id || item.exception_no ||
           item.bug_id || item.request_id || item.order_number || item.device_id ||
           item.rack_id || item.ap_id || item.server_id || item.username || ''

    // 提取类型
    type = item.type || item.category || item.exception_type || item.severity ||
           item.priority || item.order_type || item.device_type || item.role || ''

    // 提取描述
    desc = item.desc || item.description || item.content || item.phenomenon_desc ||
           item.title || item.full_name || item.product_name || item.ssid ||
           item.name || ''

    // 提取前缀（如：异常 / BUG / 工单）
    prefix = item.prefix || ''

    // 提取额外提示
    if (item.extra) extraMsg = item.extra
    if (item.extraMsg) extraMsg = item.extraMsg
  } else {
    // 兼容旧用法：直接传字符串
    name = String(item || '该条目')
  }

  // ============================================================
  // 【核心修改】按照模板构建消息
  // 模板：确认删除异常 EXC-20260908-001（质量异常 - 测试）？删除后不可恢复。
  // ============================================================
  let message = ''

  // 构建名称部分：前缀 + 编号
  let fullName = name
  if (prefix) {
    fullName = `${prefix} ${name}`
  }

  // 构建类型+描述部分
  let detail = ''
  if (type && desc) {
    detail = `（${type} - ${desc}）`
  } else if (type) {
    detail = `（${type}）`
  } else if (desc) {
    const shortDesc = desc.length > 30 ? desc.slice(0, 30) + '…' : desc
    detail = `（${shortDesc}）`
  }

  // 组装最终消息
  message = `确认删除${fullName}${detail}？${extraMsg}。`

  try {
    await ElMessageBox.confirm(
      message,
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