<template>
  <div class="page" style="width:100%; min-width:0; box-sizing:border-box;">
    <div class="page-header" style="width:100%; min-width:0;">
      <div>
        <h1 class="page-title"><span class="emoji">📋</span>岗位职责看板</h1>
        <div class="page-sub">各岗位核心职责条目管理</div>
      </div>
      <div class="d-flex align-items-center gap-2">
        <template v-if="userStore.canEdit">
          <button class="btn btn-sm btn-outline-primary" @click="openDutyAddModal">
            <span class="bi bi-person-plus"></span>新增岗位
          </button>
        </template>
      </div>
    </div>

    <div class="duties-grid" style="width:100%; min-width:0; box-sizing:border-box;">
      <div
        class="duty-col"
        v-for="(duty, index) in duties"
        :key="duty.id"
        :style="{ '--duty-accent': getAccent(index), width:'100%' }"
      >
        <el-card class="duty-el-card">
          <template #header>
            <div class="duty-header">
              <div class="duty-header-row">
                <span class="duty-icon">{{ getIcon(index) }}</span>
                <div class="duty-title">
                  <div class="duty-name">{{ duty.name }}</div>
                  <div class="duty-role">{{ duty.title }}</div>
                </div>
                <!-- 去掉 header 右上角编辑删除按钮，操作移至 footer -->
              </div>
            </div>
          </template>

          <el-scrollbar class="duty-scroll">
            <div class="duty-body">
              <template v-if="sortedItems(duty.items).length">
                <div
                  v-for="(item, idx) in sortedItems(duty.items)"
                  :key="idx"
                  class="duty-item-row"
                  :class="{ primary: item.is_primary, compact: true, active: isRowActive(duty.id, idx) }"
                  :style="isRowActive(duty.id, idx) ? { background: 'color-mix(in srgb, var(--duty-accent) 8%, #fff) !important', borderColor: 'color-mix(in srgb, var(--duty-accent) 35%, rgba(15,23,42,.12)) !important' } : {}"
                  @click="toggleActiveRow(duty.id, idx)"
                >
                  <span
                    class="duty-item-marker"
                    :class="{ primary: item.is_primary }"
                  >{{ item.is_primary ? '⭐' : '•' }}</span>
                  <el-tooltip
                    :content="item.content"
                    placement="top"
                    effect="light"
                    :show-after="200"
                    :disabled="!item.content || item.content.length < 12"
                  >
                    <div class="duty-item-content single-line" :class="{ primary: item.is_primary }">
                      {{ item.content }}
                    </div>
                  </el-tooltip>
                  <div
                    v-if="userStore.canEdit && isRowActive(duty.id, idx)"
                    class="duty-item-actions duty-item-actions-visible"
                  >
                    <el-button link type="primary" size="small" @click.stop="openItemEditModal(duty, idx, item)">编辑</el-button>
                    <el-button link type="danger"  size="small" @click.stop="openItemDeleteModal(duty, idx)">删除</el-button>
                  </div>
                </div>
              </template>
              <div v-else class="duty-empty">
                <div class="duty-empty-icon">📭</div>
                <div class="duty-empty-title">暂无职责条目</div>
                <div class="duty-empty-hint" v-if="userStore.canEdit">点击下方按钮添加主要/次要职责</div>
              </div>
            </div>
          </el-scrollbar>

          <template #footer v-if="userStore.canEdit">
            <div class="duty-footer-actions">
              <el-button class="duty-edit-btn" @click="openDutyEditModal(duty)">
                <span class="bi bi-pencil-square" style="margin-right:5px;"></span>编辑
              </el-button>
              <el-button class="duty-delete-btn" @click="openDutyDeleteModal(duty)">
                <span class="bi bi-trash3" style="margin-right:5px;"></span>删除
              </el-button>
            </div>
          </template>
        </el-card>
      </div>
    </div>

    <!-- 职责条目：新增 / 编辑 Modal —— 视觉优化：更精致的只读 chip、更宽输入、居中 footer —— -->
    <CommonModal
      v-model:visible="itemModalVisible"
      :title="itemMode === 'add' ? '添加职责' : '编辑职责'"
      width="560px"
      :ok-loading="itemSaving"
      @ok="submitItemModal"
      align-footer="center"
    >
      <div class="item-modal-inner">
        <el-form :model="itemForm" label-width="84px" label-position="right">
          <!-- 所属岗位：改成只读 chip（不再用 disabled input，更美观） -->
          <el-form-item label="所属岗位">
            <div class="item-duty-chip" :style="{ '--duty-accent': (itemDuty ? presetAccents[ duties.value.indexOf(itemDuty) % presetAccents.length ] : presetAccents[0]) }">
              <span class="item-duty-avatar">{{ itemDuty ? presetIcons[ duties.value.indexOf(itemDuty) % presetIcons.length ] : '👤' }}</span>
              <span class="item-duty-name">{{ itemDuty?.name }}</span>
              <span class="item-duty-dot">/</span>
              <span class="item-duty-title">{{ itemDuty?.title }}</span>
            </div>
          </el-form-item>
          <!-- 职责内容：4 行文本域，字数统计 + 柔色焦点框 -->
          <el-form-item label="职责内容" required>
            <el-input
              v-model="itemForm.content"
              type="textarea"
              :rows="4"
              placeholder="请输入职责描述（建议简明扼要）"
              maxlength="200"
              show-word-limit
              resize="none"
              class="item-content-textarea"
            />
          </el-form-item>
          <!-- 职责等级：切换用更大的块状按钮（主/次 更分明） -->
          <el-form-item label="职责等级">
            <div class="item-level-switch">
              <div
                class="item-level-card"
                :class="{ active: itemForm.is_primary === true }"
                @click="itemForm.is_primary = true"
              >
                <div class="item-level-icon">⭐</div>
                <div class="item-level-meta">
                  <div class="item-level-name"><span>主要职责</span></div>
                  <div class="item-level-hint">关键职责，靠前展示</div>
                </div>
                <div class="item-level-check" :class="{ show: itemForm.is_primary === true }">✓</div>
              </div>
              <div
                class="item-level-card"
                :class="{ active: itemForm.is_primary === false }"
                @click="itemForm.is_primary = false"
              >
                <div class="item-level-icon" style="background:#F1F5F9;">•</div>
                <div class="item-level-meta">
                  <div class="item-level-name"><span style="color:#334155;">次要职责</span></div>
                  <div class="item-level-hint">辅助性工作，靠后展示</div>
                </div>
                <div class="item-level-check" :class="{ show: itemForm.is_primary === false }">✓</div>
              </div>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button size="default" style="min-width:110px;height:36px;border-radius:9px;" @click="f.cancel">
            <span class="bi bi-x" style="margin-right:4px;"></span>取消
          </el-button>
          <el-button size="default" type="primary" :loading="f.okLoading" style="min-width:110px;height:36px;border-radius:9px;" @click="f.ok">
            <span class="bi" :class="itemMode === 'add' ? 'bi-plus-lg' : 'bi-check2'" style="margin-right:4px;"></span>
            {{ itemMode === 'add' ? '添加职责' : '保存修改' }}
          </el-button>
        </div>
      </template>
    </CommonModal>

    <!-- 职责条目：删除确认 Modal -->
    <CommonModal
      v-model:visible="itemDeleteVisible"
      title="确认删除职责"
      width="460px"
      :ok-loading="itemDeleteSaving"
      @ok="submitItemDelete"
    >
      <div style="display:flex;gap:14px;align-items:flex-start;">
        <div style="
          width:44px;height:44px;flex-shrink:0;border-radius:50%;
          background:#FEF3C7;color:#D97706;font-size:22px;
          display:inline-flex;align-items:center;justify-content:center;
        ">
          <span class="bi bi-exclamation-triangle-fill"></span>
        </div>
        <div>
          <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:6px;">
            确定要删除此职责？
          </div>
          <div style="font-size:13px;color:var(--c-text-3);line-height:1.6;">
            您即将删除 <b style="color:var(--c-text-2);">"{{ itemDeleteContent }}"</b> 职责条目，
            该操作无法撤销，是否继续？
          </div>
        </div>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="danger" :loading="f.okLoading" @click="f.ok">确认删除</el-button>
        </div>
      </template>
    </CommonModal>

    <!-- 岗位组：新增 / 编辑 Modal —— 更居中 + 更简约：label 上方居中、宽度收紧、分隔线极简、条目素雅 —— -->
    <CommonModal
      v-model:visible="dutyModalVisible"
      :title="dutyMode === 'add' ? '新增岗位' : '编辑岗位'"
      width="560px"
      :ok-loading="dutySaving"
      @ok="submitDutyModal"
      align-footer="center"
    >
      <!-- 外层：一个居中盒子即可，max-width + margin:0 auto，上下左右留白一致，视觉更聚焦 -->
      <div class="duty-modal-box">
        <!-- label-position="top"：标签在上、输入框在下，整体视觉居中，不再有 label 右对齐造成的左偏感 -->
        <el-form :model="dutyForm" label-position="top" class="duty-form-mini">
          <div class="duty-form-row">
            <el-form-item label="人员姓名" required>
              <el-input
                v-model="dutyForm.name"
                placeholder="例如：张三"
                maxlength="20"
                clearable
                size="default"
              />
            </el-form-item>
          </div>
          <div class="duty-form-row">
            <el-form-item label="岗位职称" required>
              <el-select v-model="dutyForm.title" placeholder="请选择或输入职称" clearable filterable allow-create size="default" style="width:100%;">
                <el-option label="工程师" value="工程师" />
                <el-option label="技术员" value="技术员" />
                <el-option label="高级工程师" value="高级工程师" />
                <el-option label="主管" value="主管" />
                <el-option label="组长" value="组长" />
              </el-select>
            </el-form-item>
          </div>

          <!-- 分隔线极简：细灰线 + 居中短标题，无图标、无多余留白 -->
          <div class="duty-mini-divider">
            <span>职责条目管理</span>
          </div>

          <!-- 条目管理区：纯白 + 极淡圆角，无渐变无厚边框，保持简约清爽 -->
          <div class="duty-items-wrap">
            <div class="duty-items-stack">
              <div
                v-for="(row, idx) in dutyForm.items"
                :key="idx"
                class="duty-row-simple"
              >
                <!-- 序号小方块：简约灰底 + 数字，不花哨 -->
                <div class="duty-row-index" :class="{ p: row.is_primary }">{{ idx + 1 }}</div>
                <el-input
                  v-model="row.content"
                  type="textarea"
                  :rows="2"
                  :placeholder="`第 ${idx + 1} 条职责描述`"
                  maxlength="200"
                  show-word-limit
                  resize="none"
                  class="duty-row-input"
                />
                <!-- 主次切换：改为更小更紧凑的 tag 样式按钮 -->
                <div class="duty-row-level">
                  <div
                    class="level-chip"
                    :class="{ on: row.is_primary === true }"
                    @click="row.is_primary = true"
                  >主</div>
                  <div
                    class="level-chip"
                    :class="{ on: row.is_primary === false }"
                    @click="row.is_primary = false"
                  >次</div>
                </div>
                <button
                  class="duty-row-del"
                  type="button"
                  :title="`删除第 ${idx + 1} 条`"
                  @click="removeFormItem(idx)"
                >
                  <span class="bi bi-x-lg"></span>
                </button>
              </div>
              <div v-if="!dutyForm.items.length" class="duty-empty-mini">
                暂无职责条目，点击下方按钮添加
              </div>
            </div>
            <!-- 添加一条职责：简约的小尺寸 outline 按钮，居中，不抢视觉 -->
            <div class="duty-add-center">
              <el-button size="small" class="duty-add-link-btn" @click="addFormItem">
                <span class="bi bi-plus" style="margin-right:4px;"></span>添加一条职责
              </el-button>
            </div>
          </div>
        </el-form>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button size="default" style="min-width:108px;height:36px;border-radius:10px;" @click="f.cancel">取消</el-button>
          <el-button size="default" type="primary" :loading="f.okLoading" style="min-width:118px;height:36px;border-radius:10px;" @click="f.ok">
            {{ dutyMode === 'add' ? '创建岗位' : '保存修改' }}
          </el-button>
        </div>
      </template>
    </CommonModal>

    <!-- 岗位组：删除确认 Modal -->
    <CommonModal
      v-model:visible="dutyDeleteVisible"
      title="确认删除岗位"
      width="480px"
      :ok-loading="dutyDeleteSaving"
      @ok="submitDutyDelete"
    >
      <div style="display:flex;gap:14px;align-items:flex-start;">
        <div style="
          width:44px;height:44px;flex-shrink:0;border-radius:50%;
          background:#FEE2E2;color:#DC2626;font-size:22px;
          display:inline-flex;align-items:center;justify-content:center;
        ">
          <span class="bi bi-exclamation-diamond-fill"></span>
        </div>
        <div>
          <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:6px;">
            确定要删除整个岗位？
          </div>
          <div style="font-size:13px;color:var(--c-text-3);line-height:1.6;">
            您即将删除 <b style="color:var(--c-text-2);">{{ dutyDeleteTarget?.name }} - {{ dutyDeleteTarget?.title }}</b>
            以及其下 <b style="color:var(--c-text-2);">{{ sortedItems(dutyDeleteTarget?.items).length }} 条职责</b>。
            该操作无法撤销，是否继续？
          </div>
        </div>
      </div>
      <template #footer="f">
        <div class="cm-footer">
          <el-button @click="f.cancel">取消</el-button>
          <el-button type="danger" :loading="f.okLoading" @click="f.ok">确认删除岗位</el-button>
        </div>
      </template>
    </CommonModal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { dutiesApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import CommonModal from '@/components/common/CommonModal.vue'

const userStore = useUserStore()
const duties = ref([])

// 点击某条职责才展开"编辑/删除"按钮的激活行：`${dutyId}-${idx}`，null 表示全部收起
const activeRowKey = ref(null)
const toggleActiveRow = (dutyId, idx) => {
  const key = `${dutyId}-${idx}`
  activeRowKey.value = activeRowKey.value === key ? null : key
}
const isRowActive = (dutyId, idx) => activeRowKey.value === `${dutyId}-${idx}`

// 预设卡片颜色 & 图标（超过 4 个岗位时循环使用，前端视觉不依赖后端存储）
const presetAccents = ['#4f46e5', '#0891b2', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0ea5e9', '#be123c']
const presetIcons   = ['🔧', '💻', '🏭', '📡', '🔬', '🎯', '📊', '👷']

const getAccent = (i) => presetAccents[i % presetAccents.length]
const getIcon   = (i) => presetIcons[i % presetIcons.length]

// ================= 职责条目弹窗 =================
const itemModalVisible = ref(false)
const itemMode = ref('add') // 'add' | 'edit'
const itemSaving = ref(false)
const itemForm = ref({ content: '', is_primary: true })
const itemDuty = ref(null)
const itemEditIndex = ref(null)

const itemDeleteVisible = ref(false)
const itemDeleteSaving = ref(false)
const itemDeleteTarget = ref(null)
const itemDeleteIndex = ref(null)
const itemDeleteContent = ref('')

// ================= 岗位组弹窗 =================
const dutyModalVisible = ref(false)
const dutyMode = ref('add') // 'add' | 'edit'
const dutySaving = ref(false)
const dutyForm = ref({ name: '', title: '', items: [] })
const dutyEditTarget = ref(null)

const dutyDeleteVisible = ref(false)
const dutyDeleteSaving = ref(false)
const dutyDeleteTarget = ref(null)

// 在弹窗内就地添加/删除一条职责条目（仅修改表单内存，不立即请求后端）
const addFormItem = () => {
  if (!Array.isArray(dutyForm.value.items)) dutyForm.value.items = []
  dutyForm.value.items.push({
    content: '',
    is_primary: dutyForm.value.items.filter(r => r.is_primary).length < 2, // 前两条默认主要
  })
}
const removeFormItem = (idx) => {
  if (!Array.isArray(dutyForm.value.items)) return
  dutyForm.value.items.splice(idx, 1)
}

// ================= 工具函数 =================
const sortedItems = (items) => {
  return [...(items || [])].sort((a, b) => (b.is_primary ? 1 : 0) - (a.is_primary ? 1 : 0))
}

const loadData = async () => {
  try {
    const res = await dutiesApi.list()
    duties.value = res.data || []
  } catch (e) {
    console.error(e)
  }
}

// ================= 职责条目：增删改 =================
const openItemAddModal = (duty) => {
  itemDuty.value = duty
  itemMode.value = 'add'
  itemForm.value = { content: '', is_primary: true }
  itemModalVisible.value = true
}

const openItemEditModal = (duty, idx, item) => {
  itemDuty.value = duty
  itemEditIndex.value = idx
  itemMode.value = 'edit'
  itemForm.value = { content: item.content, is_primary: item.is_primary }
  itemModalVisible.value = true
}

const submitItemModal = async () => {
  if (!itemForm.value.content || !itemForm.value.content.trim()) {
    ElMessage.warning('请输入职责内容')
    return
  }
  itemSaving.value = true
  try {
    const duty = itemDuty.value
    const items = [...duty.items]
    if (itemMode.value === 'add') {
      items.push({
        content: itemForm.value.content.trim(),
        is_primary: itemForm.value.is_primary,
      })
    } else {
      const sorted = sortedItems(items)
      const sortedItem = sorted[itemEditIndex.value]
      const originalIdx = items.indexOf(sortedItem)
      if (originalIdx >= 0) {
        items[originalIdx] = {
          content: itemForm.value.content.trim(),
          is_primary: itemForm.value.is_primary,
        }
      }
    }
    await dutiesApi.update(duty.id, { items })
    itemModalVisible.value = false
    ElMessage.success(itemMode.value === 'add' ? '添加成功' : '修改成功')
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '保存失败')
  } finally {
    itemSaving.value = false
  }
}

const openItemDeleteModal = (duty, idx) => {
  const sorted = sortedItems(duty.items)
  itemDeleteTarget.value = duty
  itemDeleteIndex.value = idx
  itemDeleteContent.value = sorted[idx]?.content || ''
  itemDeleteVisible.value = true
}

const submitItemDelete = async () => {
  itemDeleteSaving.value = true
  try {
    const duty = itemDeleteTarget.value
    const items = [...duty.items]
    const sorted = sortedItems(items)
    const sortedItem = sorted[itemDeleteIndex.value]
    const originalIdx = items.indexOf(sortedItem)
    if (originalIdx >= 0) items.splice(originalIdx, 1)
    await dutiesApi.update(duty.id, { items })
    itemDeleteVisible.value = false
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '删除失败')
  } finally {
    itemDeleteSaving.value = false
  }
}

// ================= 岗位组：增删改 =================
const openDutyAddModal = () => {
  dutyMode.value = 'add'
  dutyForm.value = { name: '', title: '工程师', items: [] }
  dutyEditTarget.value = null
  dutyModalVisible.value = true
}

const openDutyEditModal = (duty) => {
  dutyMode.value = 'edit'
  dutyEditTarget.value = duty
  // 深拷贝当前所有职责条目到表单，支持一次编辑多条（保留原 id 用于提交时的映射，没有 id 也没关系，后端以 items 全量覆盖）
  dutyForm.value = {
    name: duty.name,
    title: duty.title,
    items: JSON.parse(JSON.stringify(duty.items || [])).map((row) => ({
      id: row.id,
      content: row.content || '',
      is_primary: !!row.is_primary,
    })),
  }
  dutyModalVisible.value = true
}

const submitDutyModal = async () => {
  if (!dutyForm.value.name || !dutyForm.value.name.trim()) {
    ElMessage.warning('请输入人员姓名')
    return
  }
  if (!dutyForm.value.title) {
    ElMessage.warning('请选择/输入岗位职称')
    return
  }
  // 校验：职责条目不能有空白内容（防止提交无效行）
  const items = (dutyForm.value.items || []).map((r) => ({
    id: r.id,
    content: (r.content || '').trim(),
    is_primary: !!r.is_primary,
  }))
  const blankIdx = items.findIndex((r) => !r.content)
  if (blankIdx >= 0) {
    ElMessage.warning(`第 ${blankIdx + 1} 条职责内容不能为空`)
    return
  }
  dutySaving.value = true
  try {
    if (dutyMode.value === 'add') {
      await dutiesApi.create({
        name: dutyForm.value.name.trim(),
        title: dutyForm.value.title,
        items,
        sort_order: duties.value.length + 1,
      })
      ElMessage.success('岗位创建成功，已同步保存职责条目')
    } else {
      // 编辑模式：同时更新元信息（name/title）+ 全量更新 items
      await Promise.all([
        dutiesApi.patch(dutyEditTarget.value.id, {
          name: dutyForm.value.name.trim(),
          title: dutyForm.value.title,
        }),
        dutiesApi.update(dutyEditTarget.value.id, { items }),
      ])
      ElMessage.success('岗位信息与职责已更新')
    }
    dutyModalVisible.value = false
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '保存失败')
  } finally {
    dutySaving.value = false
  }
}

const openDutyDeleteModal = (duty) => {
  dutyDeleteTarget.value = duty
  dutyDeleteVisible.value = true
}

const submitDutyDelete = async () => {
  if (!dutyDeleteTarget.value) return
  dutyDeleteSaving.value = true
  try {
    await dutiesApi.remove(dutyDeleteTarget.value.id)
    dutyDeleteVisible.value = false
    ElMessage.success('岗位已删除')
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '删除失败')
  } finally {
    dutyDeleteSaving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* —— 卡片本体：height:100% 撑满列 → 与同 row 最长的那条卡严格等高；max-height 520px 保底 —— */
.duty-el-card {
  display: flex;
  flex-direction: column;
  width: 100% !important;
  min-width: 0;
  height: 100% !important;
  min-height: 480px;              /* 保底：Header + 6条 Body + Footer ≈ 480px，保证统一高度 */
  max-height: none !important;
  border-radius: 18px !important;
  overflow: hidden;
  border: 1px solid rgba(15,23,42,0.08) !important;
  background: #fff;
  box-shadow:
    0 1px 2px rgba(15,23,42,.04),
    0 6px 20px -8px rgba(15,23,42,.12) !important;
  transition: transform .22s cubic-bezier(.2,.7,.2,1), box-shadow .22s cubic-bezier(.2,.7,.2,1), border-color .22s;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  position: relative;
}
.duty-el-card::before {
  /* hover 时外框泛 accent 微光，不动原 border 避免抖动 */
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--duty-accent, #4f46e5) 50%, transparent),
    transparent 40%,
    transparent 60%,
    color-mix(in srgb, var(--duty-accent, #4f46e5) 30%, transparent)
  );
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
          mask-composite: exclude;
  opacity: 0;
  transition: opacity .22s;
  pointer-events: none;
}
.duty-el-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 2px 6px rgba(15,23,42,.05),
    0 20px 40px -14px color-mix(in srgb, var(--duty-accent, #4f46e5) 38%, rgba(15,23,42,.18)) !important;
  border-color: color-mix(in srgb, var(--duty-accent, #4f46e5) 32%, rgba(15,23,42,0.08)) !important;
}
.duty-el-card:hover::before { opacity: 1; }

.duty-el-card :deep(.el-card__header) {
  padding: 0 !important;
  border-bottom: 0 !important;
  border-radius: 18px 18px 0 0;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow: hidden;          /* 把 header 里的装饰光斑裁在渐变条内，不溢出卡片外 */
  position: relative;
}
.duty-el-card :deep(.el-card__header)::before,
.duty-el-card :deep(.el-card__header)::after {
  /* 两个装饰光斑：一个在左上淡圆，一个在右下亮斜条，让渐变不单调 */
  content: "";
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  opacity: .55;
  pointer-events: none;
}
.duty-el-card :deep(.el-card__header)::before {
  width: 180px; height: 180px;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,.55), transparent 60%);
  left: -60px; top: -70px;
}
.duty-el-card :deep(.el-card__header)::after {
  width: 220px; height: 220px;
  background: radial-gradient(circle at 70% 70%, rgba(255,255,255,.22), transparent 60%);
  right: -80px; bottom: -100px;
  opacity: .7;
  filter: blur(4px);
}
.duty-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  position: relative;   /* 盖在装饰层之上 */
  z-index: 1;
}
.duty-header-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 14px 10px;
  border-top: 1px solid rgba(255,255,255,0.18);
  margin-top: 2px;
}
.duty-header-actions .el-button {
  font-size: 12px !important;
  padding: 2px 8px !important;
  height: 24px !important;
  line-height: 1 !important;
  border-radius: 6px !important;
  background: rgba(255,255,255,.10) !important;
  color: #fff !important;
  opacity: .92;
  transition: background .18s, transform .18s;
}
.duty-header-actions .el-button:hover {
  background: rgba(255,255,255,.22) !important;
  transform: translateY(-1px);
}
/* —— body：flex:1 吃掉剩余 → 滚动内容区固定（6 条高度），footer 贴底 —— */
.duty-el-card :deep(.el-card__body) {
  flex: 1 1 auto;
  min-height: 0;
  min-width: 0;
  max-width: 100%;
  width: 100%;
  background: linear-gradient(180deg, #F8FAFD 0%, #FFFFFF 50%);
  padding: 10px 10px 10px 10px !important;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.duty-el-card :deep(.el-card__footer) {
  border-top: 1px solid rgba(15,23,42,0.06) !important;
  padding: 10px 14px 14px !important;
  background: #ffffff;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

/* ================================================================
   单条职责编辑弹窗（itemModal）美化样式：居中 + 精致 chip + 块状等级卡
   ================================================================ */
.item-modal-inner {
  background: #fff;
  border-radius: 12px;
  padding: 6px 2px 2px;
}
/* 所属岗位 chip：柔和渐变底 + 圆形图标 + 斜杠分隔 */
.item-duty-chip {
  --duty-accent: #4f46e5;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px 6px 6px;
  border-radius: 999px;
  background:
    linear-gradient(90deg,
      color-mix(in srgb, var(--duty-accent) 10%, #fff),
      color-mix(in srgb, var(--duty-accent) 4%, #fff)
    );
  border: 1px solid color-mix(in srgb, var(--duty-accent) 24%, #e2e8f0);
}
.item-duty-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  background: #fff;
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--duty-accent) 28%, #e2e8f0),
              0 2px 6px color-mix(in srgb, var(--duty-accent) 18%, transparent);
  font-size: 15px;
}
.item-duty-name {
  font-weight: 600; color: #0f172a; font-size: 13.5px;
  letter-spacing: .2px;
}
.item-duty-dot {
  color: #cbd5e1; font-weight: 600;
}
.item-duty-title {
  color: color-mix(in srgb, var(--duty-accent) 70%, #334155);
  font-size: 12.5px; font-weight: 500;
}
/* 职责内容文本域：柔色边框 + 圆角 + 聚焦时 accent 描边 */
.item-content-textarea :deep(.el-textarea__inner) {
  border-radius: 10px !important;
  border: 1px solid #dbe2ea !important;
  padding: 10px 12px !important;
  font-size: 14px;
  line-height: 1.55;
  color: #1e293b;
  transition: border-color .18s, box-shadow .18s;
}
.item-content-textarea :deep(.el-textarea__inner:focus) {
  border-color: var(--primary, #2C5CE8) !important;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary, #2C5CE8) 14%, transparent) !important;
}
.item-content-textarea :deep(.el-input__count) {
  font-size: 11px;
  color: #94a3b8;
}

/* 职责等级：两张块状卡片并排（主/次 一眼区分） */
.item-level-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.item-level-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px 10px 10px;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  transition: all .18s cubic-bezier(.2,.7,.2,1);
  position: relative;
}
.item-level-card:hover {
  border-color: #cbd5e1;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px -8px rgba(15,23,42,.15);
}
.item-level-card.active {
  border-color: #d97706;
  background: linear-gradient(180deg, #fff7ed, #ffffff);
  box-shadow: 0 8px 20px -10px rgba(217,119,6,.42), 0 1px 2px rgba(217,119,6,.08);
}
.item-level-card:nth-of-type(2).active {
  border-color: #0f766e;
  background: linear-gradient(180deg, #f0fdfa, #ffffff);
  box-shadow: 0 8px 20px -10px rgba(15,118,110,.42), 0 1px 2px rgba(15,118,110,.08);
}
.item-level-icon {
  width: 34px; height: 34px; border-radius: 9px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 16px;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  box-shadow: inset 0 0 0 1px rgba(253,224,71,.4),
              0 2px 6px rgba(250,204,21,.15);
  flex-shrink: 0;
}
.item-level-meta {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 2px;
}
.item-level-name {
  font-size: 13.5px; font-weight: 600; color: #0f172a; line-height: 1.25;
}
.item-level-name span:first-child {
  color: #b45309;
}
.item-level-hint {
  font-size: 11.5px; color: #64748b; letter-spacing: .1px;
}
.item-level-check {
  width: 20px; height: 20px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fff;
  background: #e2e8f0;
  transform: scale(.8);
  opacity: 0;
  transition: all .2s cubic-bezier(.2,.7,.2,1);
  flex-shrink: 0;
}
.item-level-check.show {
  opacity: 1; transform: scale(1);
  background: #d97706;
  box-shadow: 0 0 0 3px rgba(217,119,6,.14);
}
.item-level-card:nth-of-type(2) .item-level-check.show {
  background: #0f766e;
  box-shadow: 0 0 0 3px rgba(15,118,110,.14);
}

/* ================================================================
   岗位编辑弹窗（职责条目管理）—— 更居中 + 更简约样式
   ================================================================ */
.duty-modal-box {
  width: 100%;
  max-width: 460px;              /* 有效表单宽度收紧，视觉更居中紧凑 */
  margin: 0 auto;                /* 水平居中：关键 */
  padding: 4px 2px 2px;
}
/* label-position=top 的 form：label 文字居中对齐，整体观感不偏左 */
.duty-form-mini { width: 100%; }
.duty-form-mini :deep(.el-form-item) {
  margin-bottom: 14px;
}
.duty-form-mini :deep(.el-form-item__label) {
  width: 100% !important;
  text-align: center !important;
  justify-content: center !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: #475569 !important;
  letter-spacing: .2px;
  padding-bottom: 4px !important;
}
.duty-form-mini :deep(.el-input__wrapper),
.duty-form-mini :deep(.el-select__wrapper) {
  border-radius: 10px !important;
  box-shadow: 0 0 0 1px #e2e8f0 inset !important;
  transition: box-shadow .18s;
}
.duty-form-mini :deep(.el-input__wrapper.is-focus),
.duty-form-mini :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--primary, #2C5CE8) inset !important;
}
.duty-form-row { width: 100%; }

/* 分隔线极简：细灰线穿过 + 中间小字文字灰底衬 */
.duty-mini-divider {
  position: relative;
  text-align: center;
  margin: 8px 0 14px;
}
.duty-mini-divider::before {
  content: "";
  position: absolute;
  left: 0; right: 0; top: 50%;
  height: 1px;
  background: #eef2f7;
}
.duty-mini-divider span {
  position: relative;
  display: inline-block;
  padding: 0 14px;
  background: #ffffff;
  color: #64748b;
  font-size: 12.5px;
  font-weight: 500;
  letter-spacing: .6px;
}

/* 条目管理区：纯白 + 4px 内边距 + 极小圆角，无渐变无厚框 */
.duty-items-wrap {
  width: 100%;
  padding: 4px 2px 2px;
  background: transparent;
  border: none;
  box-sizing: border-box;
}
.duty-items-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;                        /* 条目间距从 10px 压缩到 8px，更紧凑 */
  align-items: stretch;
}

/* 单条职责行：极简四列，无阴影、线框极淡 */
.duty-row-simple {
  display: grid;
  grid-template-columns: 26px 1fr 62px 28px;
  gap: 8px;
  align-items: start;
  padding: 8px 8px 8px 8px;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
  background: #ffffff;
  transition: border-color .16s, background .16s;
}
.duty-row-simple:hover {
  border-color: #e2e8f0;
  background: #fafbfc;
}
/* 序号小方块：极简 */
.duty-row-index {
  width: 26px; height: 26px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  background: #f8fafc;
  flex-shrink: 0;
}
.duty-row-index.p {
  color: #d97706;
  background: #FFF7ED;
  box-shadow: inset 0 0 0 1px #FEF3C7;
}

/* 文本域：更简约 */
.duty-row-input :deep(.el-textarea__inner) {
  border-radius: 8px !important;
  border: 1px solid #e2e8f0 !important;
  padding: 7px 9px !important;
  font-size: 13px !important;
  line-height: 1.55 !important;
  color: #1e293b;
  background: #ffffff;
  transition: border-color .16s, box-shadow .16s;
}
.duty-row-input :deep(.el-textarea__inner:focus) {
  border-color: var(--primary, #2C5CE8) !important;
  box-shadow: 0 0 0 2.5px color-mix(in srgb, var(--primary, #2C5CE8) 12%, transparent) !important;
  background: #ffffff;
}
.duty-row-input :deep(.el-input__count) {
  font-size: 10.5px;
  color: #94a3b8;
  padding-top: 2px;
}

/* 主次切换：两格 chip，"主"选中琥珀、"次"选中青灰 */
.duty-row-level {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  margin-top: 2px;
}
.level-chip {
  height: 26px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  user-select: none;
  transition: all .16s;
}
.level-chip:hover {
  color: #64748b;
  border-color: #cbd5e1;
}
.level-chip.on {
  color: #ffffff;
  border-color: transparent;
  background: #64748b;
}
.duty-row-level .level-chip:first-child.on {
  background: #d97706;
}
.duty-row-level .level-chip:nth-child(2).on {
  background: #0f766e;
}

/* 删除按钮：小尺寸 × 圆形灰色，hover 变红，极简 */
.duty-row-del {
  width: 28px; height: 28px;
  margin-top: 1px;
  border-radius: 50%;
  border: none;
  background: #f8fafc;
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all .16s;
  padding: 0;
}
.duty-row-del:hover {
  background: #FEE2E2;
  color: #dc2626;
}
.duty-row-del .bi { font-size: 12px; }

/* 空状态：简约一行文字 */
.duty-empty-mini {
  text-align: center;
  padding: 18px 10px;
  border: 1px dashed #e2e8f0;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 12.5px;
  background: #fafbfc;
}

/* 添加职责按钮：居中 + 小尺寸 outline 风格（不抢视觉） */
.duty-add-center {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
.duty-add-link-btn {
  height: 32px !important;
  min-width: 150px;
  border-radius: 999px !important;
  background: #ffffff !important;
  border: 1px dashed #cbd5e1 !important;
  color: #475569 !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  padding: 0 14px !important;
  transition: all .18s;
}
.duty-add-link-btn:hover {
  color: var(--primary, #2C5CE8) !important;
  border-color: color-mix(in srgb, var(--primary, #2C5CE8) 50%, #cbd5e1) !important;
  background: color-mix(in srgb, var(--primary, #2C5CE8) 4%, #fff) !important;
}
</style>
