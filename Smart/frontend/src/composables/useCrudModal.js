// src/composables/useCrudModal.js
// ============================================================================
// 复用层：统一"新增 / 编辑弹窗"的所有状态（visible / editingId / form / saving + show/close/save 流程）
// —— 让每个业务页不必在 <script setup> 里重复写 20~30 行一样的变量和打开/关闭逻辑
// ============================================================================
import { ref, reactive, cloneVNode, isVNode } from 'vue'
import { useNotify } from './useNotify'

/**
 * 默认空表单生成器（创建新表单时的初始值）
 */
const defaultEmptyForm = () => ({})

/**
 * @param {Function} emptyFormFactory  () => object  生成新增时的空表单
 * @param {object}   opts              { beforeShow, onSaved }
 * @returns
 */
export function useCrudModal(emptyFormFactory = defaultEmptyForm, opts = {}) {
  const { toast } = useNotify()

  const visible  = ref(false)
  const editing  = ref(null)        // 当前编辑的原行对象（用于判断是 add / edit，或回显）
  const saving   = ref(false)
  const form     = reactive(emptyFormFactory())

  /** 重置表单为空值 */
  const resetForm = () => {
    Object.keys(form).forEach(k => delete form[k])
    Object.assign(form, emptyFormFactory())
  }

  /** 打开"新增"弹窗 */
  const showCreate = (preset = {}) => {
    resetForm()
    if (preset && typeof preset === 'object') Object.assign(form, preset)
    editing.value = null
    visible.value = true
    if (opts.beforeShow) opts.beforeShow({ mode: 'add', form })
  }

  /** 打开"编辑"弹窗：把传入的 row 浅拷贝到 form 回显 */
  const showEdit = (row) => {
    resetForm()
    editing.value = row || null
    if (row) Object.assign(form, JSON.parse(JSON.stringify(row)))
    visible.value = true
    if (opts.beforeShow) opts.beforeShow({ mode: 'edit', form, row })
  }

  /** 关闭弹窗并清空状态 */
  const close = () => {
    visible.value = false
    saving.value  = false
  }

  /**
   * 统一保存流程：传一个 async 保存函数进来即可
   *   saveRunner({ form, editing, isAdd, isEdit }) → Promise<any>
   *   返回 { ok, res }
   */
  const submit = async (saveRunner, opts2 = {}) => {
    if (!saveRunner) return { ok: false }
    const isAdd  = editing.value == null
    const isEdit = !isAdd

    // 用户自定义校验：返回 true 表示通过；返回字符串则作为错误提示 toast 出来
    if (opts2.validate) {
      const vr = await opts2.validate({ form, isAdd, isEdit, editing: editing.value })
      if (vr === false) return { ok: false }
      if (typeof vr === 'string') { toast.warn(vr); return { ok: false } }
    }

    saving.value = true
    try {
      const res = await saveRunner({ form, editing: editing.value, isAdd, isEdit })
      if (opts2.successMsg !== false) {
        // successMsg=true 用默认；string 用自定义；function 用函数返回值
        let msg = opts2.successMsg
        if (msg === true || msg == null) msg = isAdd ? '新增成功' : '修改成功'
        if (typeof msg === 'function') msg = msg({ form, res, isAdd, isEdit })
        if (msg) toast.success(msg)
      }
      close()
      if (opts2.onSaved) await opts2.onSaved({ form, res, isAdd, isEdit })
      return { ok: true, res }
    } catch (e) {
      const { notifyError } = useNotify()
      notifyError(e, opts2.failMsg || '保存失败')
      return { ok: false, error: e }
    } finally {
      saving.value = false
    }
  }

  return {
    // 状态 —— 使用 getter/setter 包装 ref，避免外部 v-model 替换 ref 本身
    get modalVisible()  { return visible.value },
    set modalVisible(v) { visible.value = v },
    get modalSaving()   { return saving.value },
    set modalSaving(v)  { saving.value = v },
    editing,
    form,
    isAdd:  () => editing.value == null,
    isEdit: () => editing.value != null,
    // 动作
    showCreate,
    showEdit,
    close,
    submit,
    resetForm,
  }
}
