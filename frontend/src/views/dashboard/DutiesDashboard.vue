<template>
  <div class="page" style="width:100%; min-width:0; box-sizing:border-box;">
    <Teleport defer to=".topbar-actions">
      <button v-if="userStore.isAdmin" class="btn btn-sm btn-outline-primary" @click="openDutyAddModal">
        <span class="bi bi-person-plus"></span>新增岗位
      </button>
    </Teleport>

    <div class="duties-board">
      <!-- 空态 -->
      <div v-if="!duties.length" class="board-empty">
        <div class="board-empty-icon">
          <i class="bi bi-inbox"></i>
        </div>
        <div class="board-empty-text">暂无岗位</div>
        <button v-if="userStore.isAdmin" class="btn btn-primary" @click="openDutyAddModal">
          <span class="bi bi-person-plus"></span>新增岗位
        </button>
      </div>

      <!-- 职称分组 -->
      <section
        v-for="group in groupedByTitle"
        :key="group.key"
        class="duty-section"
        :style="{ '--duty-accent': group.accent }"
      >
        <!-- 分组标题行 -->
        <header class="duty-section-head">
          <span class="duty-section-icon">
            <i class="bi" :class="group.icon"></i>
          </span>
          <span class="duty-section-title">{{ group.title }}</span>
          <span class="duty-section-count">{{ group.duties.length }}</span>
          <span class="duty-section-line"></span>
        </header>

        <!-- 岗位卡片网格 -->
        <div class="duty-cards">
          <article
            v-for="duty in group.duties"
            :key="duty.id"
            class="duty-card"
          >
            <!-- 卡片头：姓名 + 职称 chip + hover 操作 -->
            <div class="duty-card-head">
              <span class="duty-card-name">{{ duty.name }}</span>
              <span class="duty-card-title">{{ duty.title }}</span>
              <div v-if="userStore.isAdmin" class="duty-card-actions">
                <button class="duty-card-btn" title="编辑岗位" @click.stop="openDutyEditModal(duty)">
                  <span class="bi bi-pencil"></span>
                </button>
                <button class="duty-card-btn danger" title="删除岗位" @click.stop="openDutyDeleteModal(duty)">
                  <span class="bi bi-trash3"></span>
                </button>
              </div>
            </div>

            <!-- 卡片主体：唯一滚动区，职责超出时内部滚动 -->
            <div class="duty-card-body">
              <!-- 主要职责 -->
              <div v-if="primaryItems(duty).length" class="duty-block">
                <div
                  v-for="(item, idx) in primaryItems(duty)"
                  :key="'p' + idx"
                  class="duty-line duty-line--primary"
                >
                  <span class="duty-line-text">{{ item.content }}</span>
                </div>
              </div>

              <!-- 次要职责 -->
              <div v-if="secondaryItems(duty).length" class="duty-block">
                <div
                  v-for="(item, idx) in secondaryItems(duty)"
                  :key="'s' + idx"
                  class="duty-line"
                >
                  <span class="duty-line-text">{{ item.content }}</span>
                </div>
              </div>

              <!-- 空态 -->
              <div v-if="!duty.items?.length" class="duty-empty">
                <span class="bi bi-inbox"></span>
                <span>暂无职责</span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <!-- ============ Modal 区 ============ -->

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
          <el-form-item label="所属岗位">
            <div class="item-duty-chip" :style="{ '--duty-accent': getAccent(itemDuty) }">
              <span class="item-duty-avatar">
                <i class="bi" :class="getIcon(itemDuty)"></i>
              </span>
              <span class="item-duty-name">{{ itemDuty?.name }}</span>
              <span class="item-duty-dot">/</span>
              <span class="item-duty-title">{{ itemDuty?.title }}</span>
            </div>
          </el-form-item>
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
          <el-form-item label="职责等级">
            <div class="item-level-switch">
              <div class="item-level-card" :class="{ active: itemForm.is_primary === true }" @click="itemForm.is_primary = true">
                <div class="item-level-icon">
                  <i class="bi bi-star-fill"></i>
                </div>
                <div class="item-level-meta">
                  <div class="item-level-name"><span>主要职责</span></div>
                  <div class="item-level-hint">关键职责，靠前展示</div>
                </div>
                <div class="item-level-check" :class="{ show: itemForm.is_primary === true }">✓</div>
              </div>
              <div class="item-level-card" :class="{ active: itemForm.is_primary === false }" @click="itemForm.is_primary = false">
                <div class="item-level-icon secondary">
                  <i class="bi bi-dash-lg"></i>
                </div>
                <div class="item-level-meta">
                  <div class="item-level-name"><span class="text-slate">次要职责</span></div>
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

    <CommonModal
      v-model:visible="itemDeleteVisible"
      title="确认删除职责"
      width="460px"
      :ok-loading="itemDeleteSaving"
      @ok="submitItemDelete"
    >
      <div style="display:flex;gap:14px;align-items:flex-start;">
        <div style="width:44px;height:44px;flex-shrink:0;border-radius:50%;background:#FEF3C7;color:#D97706;font-size:22px;display:inline-flex;align-items:center;justify-content:center;">
          <span class="bi bi-exclamation-triangle-fill"></span>
        </div>
        <div>
          <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:6px;">确定要删除此职责？</div>
          <div style="font-size:13px;color:var(--c-text-3);line-height:1.6;">
            您即将删除 <b style="color:var(--c-text-2);">"{{ itemDeleteContent }}"</b> 职责条目，该操作无法撤销，是否继续？
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

    <CommonModal
      v-model:visible="dutyModalVisible"
      :title="dutyMode === 'add' ? '新增岗位' : '编辑岗位'"
      width="560px"
      :ok-loading="dutySaving"
      @ok="submitDutyModal"
      align-footer="center"
    >
      <div class="duty-modal-box">
        <el-form :model="dutyForm" label-position="top" class="duty-form-mini">
          <div class="duty-form-row">
            <el-form-item label="人员姓名" required>
              <el-input v-model="dutyForm.name" placeholder="例如：张三" maxlength="20" clearable size="default" />
            </el-form-item>
          </div>
          <div class="duty-form-row">
            <el-form-item label="岗位职称" required>
              <el-select v-model="dutyForm.title" placeholder="请选择职称" clearable filterable size="default" style="width:100%;">
                <el-option label="MES工程师" value="MES工程师" />
                <el-option label="助理工程师" value="助理工程师" />
                <el-option label="技术员" value="技术员" />
              </el-select>
            </el-form-item>
          </div>

          <div class="duty-mini-divider"><span>职责条目管理</span></div>

          <div class="duty-items-wrap">
            <div class="duty-items-stack">
              <div v-for="(row, idx) in dutyForm.items" :key="idx" class="duty-row-simple">
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
                <div class="duty-row-level">
                  <div class="level-chip" :class="{ on: row.is_primary === true }" @click="row.is_primary = true">主</div>
                  <div class="level-chip" :class="{ on: row.is_primary === false }" @click="row.is_primary = false">次</div>
                </div>
                <button class="duty-row-del" type="button" :title="`删除第 ${idx + 1} 条`" @click="removeFormItem(idx)">
                  <span class="bi bi-x-lg"></span>
                </button>
              </div>
              <div v-if="!dutyForm.items.length" class="duty-empty-mini">暂无职责条目，点击下方按钮添加</div>
            </div>
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

    <CommonModal
      v-model:visible="dutyDeleteVisible"
      title="确认删除岗位"
      width="480px"
      :ok-loading="dutyDeleteSaving"
      @ok="submitDutyDelete"
    >
      <div style="display:flex;gap:14px;align-items:flex-start;">
        <div style="width:44px;height:44px;flex-shrink:0;border-radius:50%;background:#FEE2E2;color:#DC2626;font-size:22px;display:inline-flex;align-items:center;justify-content:center;">
          <span class="bi bi-exclamation-diamond-fill"></span>
        </div>
        <div>
          <div style="font-size:15px;font-weight:600;color:#0f172a;margin-bottom:6px;">确定要删除整个岗位？</div>
          <div style="font-size:13px;color:var(--c-text-3);line-height:1.6;">
            您即将删除 <b style="color:var(--c-text-2);">{{ dutyDeleteTarget?.name }} - {{ dutyDeleteTarget?.title }}</b>
            以及其下 <b style="color:var(--c-text-2);">{{ dutyDeleteTarget?.items?.length || 0 }} 条职责</b>。
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

/* ================= 职称分组配置 ================= */
const TITLE_GROUPS = [
  {
    key: 'engineer',
    title: '工程师',
    icon: 'bi-cpu-fill',
    accent: '#4f46e5',
    titles: ['MES工程师', '助理工程师'],
  },
  {
    key: 'technician',
    title: '技术员',
    icon: 'bi-tools',
    accent: '#0891b2',
    titles: ['技术员'],
  },
]

const OTHER_GROUP = {
  key: 'other',
  title: '其他',
  icon: 'bi-person-fill',
  accent: '#0ea5e9',
  titles: [],
}

const titleTheme = {
  'MES工程师':   { icon: 'bi-cpu-fill',          accent: '#4f46e5' },
  '助理工程师':  { icon: 'bi-mortarboard-fill',  accent: '#0d9488' },
  '技术员':      { icon: 'bi-tools',             accent: '#0891b2' },
}
const fallbackTheme = { icon: 'bi-person-fill', accent: '#0ea5e9' }

const getAccent = (duty) => (titleTheme[duty?.title] || fallbackTheme).accent
const getIcon   = (duty) => (titleTheme[duty?.title] || fallbackTheme).icon

const groupedByTitle = computed(() => {
  const groups = TITLE_GROUPS.map((g) => ({ ...g, duties: [] }))
  const other = { ...OTHER_GROUP, duties: [] }
  for (const d of duties.value) {
    const t = d.title || ''
    const g = groups.find((grp) => grp.titles.includes(t))
    if (g) g.duties.push(d)
    else other.duties.push(d)
  }
  const result = groups.filter((g) => g.duties.length > 0)
  if (other.duties.length) result.push(other)
  return result
})

const sortedItems   = (items) => [...(items || [])].sort((a, b) => (b.is_primary ? 1 : 0) - (a.is_primary ? 1 : 0))
const primaryItems  = (duty) => (duty?.items || []).filter((it) => it.is_primary)
const secondaryItems = (duty) => (duty?.items || []).filter((it) => !it.is_primary)

const itemModalVisible = ref(false)
const itemMode = ref('add')
const itemSaving = ref(false)
const itemForm = ref({ content: '', is_primary: true })
const itemDuty = ref(null)
const itemEditIndex = ref(null)

const itemDeleteVisible = ref(false)
const itemDeleteSaving = ref(false)
const itemDeleteTarget = ref(null)
const itemDeleteIndex = ref(null)
const itemDeleteContent = ref('')

const dutyModalVisible = ref(false)
const dutyMode = ref('add')
const dutySaving = ref(false)
const dutyForm = ref({ name: '', title: '', items: [] })
const dutyEditTarget = ref(null)

const dutyDeleteVisible = ref(false)
const dutyDeleteSaving = ref(false)
const dutyDeleteTarget = ref(null)

const addFormItem = () => {
  if (!Array.isArray(dutyForm.value.items)) dutyForm.value.items = []
  dutyForm.value.items.push({
    content: '',
    is_primary: dutyForm.value.items.filter((r) => r.is_primary).length < 2,
  })
}
const removeFormItem = (idx) => {
  if (!Array.isArray(dutyForm.value.items)) return
  dutyForm.value.items.splice(idx, 1)
}

const loadData = async () => {
  try {
    const res = await dutiesApi.list()
    duties.value = res.data || []
  } catch (e) {
    console.error(e)
  }
}

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
    itemEditIndex.value = null
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
    itemDeleteIndex.value = null
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.response?.data?.message || '删除失败')
  } finally {
    itemDeleteSaving.value = false
  }
}

const openDutyAddModal = () => {
  dutyMode.value = 'add'
  dutyForm.value = { name: '', title: '工程师', items: [] }
  dutyEditTarget.value = null
  dutyModalVisible.value = true
}

const openDutyEditModal = (duty) => {
  dutyMode.value = 'edit'
  dutyEditTarget.value = duty
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
/* ================================================================
   页面骨架：固定不滚
   ================================================================ */
.page {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.duties-board {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0px 22px 18px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  box-sizing: border-box;
  background:
    radial-gradient(ellipse 55% 40% at 12% 0%, rgba(79, 70, 229, .045), transparent 65%),
    radial-gradient(ellipse 50% 40% at 88% 100%, rgba(8, 145, 178, .035), transparent 65%),
    #F7F9FC;
}

/* ================================================================
   分组头
   ================================================================ */
.duty-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.duty-section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px;
}

.duty-section-icon {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  color: var(--duty-accent);
  background: color-mix(in srgb, var(--duty-accent) 10%, #fff);
  border: 1px solid color-mix(in srgb, var(--duty-accent) 22%, transparent);
  box-shadow: 0 2px 6px -2px color-mix(in srgb, var(--duty-accent) 35%, transparent);
  flex-shrink: 0;
}

.duty-section-title {
  font-size: 17px;
  font-weight: 800;
  color: #0B1120;
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.duty-section-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 700;
  color: color-mix(in srgb, var(--duty-accent) 78%, #1e293b);
  background: color-mix(in srgb, var(--duty-accent) 10%, #fff);
  border: 1px solid color-mix(in srgb, var(--duty-accent) 20%, transparent);
  font-variant-numeric: tabular-nums;
}

.duty-section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg,
    color-mix(in srgb, var(--duty-accent) 40%, transparent) 0%,
    color-mix(in srgb, var(--duty-accent) 12%, transparent) 30%,
    transparent 100%);
}

/* ================================================================
   卡片网格：所有卡片统一高度，内部职责超出时滚动
   ================================================================ */
.duty-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  grid-auto-rows: 280px;   /* ✅ 去掉底部按钮后，280 就够 */
}

/* ================================================================
   岗位卡片：两段式（头固定 + 主体滚动）
   ================================================================ */
.duty-card {
  position: relative;
  height: 100%;
  border-radius: 14px;
  padding: 14px 16px 14px;   /* ✅ 去底部按钮后底部 padding 恢复为 14 */
  display: flex;
  flex-direction: column;
  gap: 0;
  box-sizing: border-box;
  overflow: hidden;
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--duty-accent) 5%, #fff) 0%,
    #ffffff 60%);
  border: 1px solid color-mix(in srgb, var(--duty-accent) 18%, #E8ECF0);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, .02),
    0 8px 20px -12px color-mix(in srgb, var(--duty-accent) 24%, transparent);
  transition:
    transform .22s cubic-bezier(.2,.7,.2,1),
    box-shadow .22s cubic-bezier(.2,.7,.2,1),
    border-color .22s;
}

.duty-card::before {
  content: '';
  position: absolute;
  top: -40px;
  right: -40px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle,
    color-mix(in srgb, var(--duty-accent) 22%, transparent) 0%,
    transparent 70%);
  pointer-events: none;
  opacity: .9;
}

.duty-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--duty-accent) 45%, transparent);
  box-shadow:
    0 4px 8px rgba(15, 23, 42, .04),
    0 20px 36px -14px color-mix(in srgb, var(--duty-accent) 42%, transparent);
}

/* 卡片头 */
.duty-card-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding-bottom: 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--duty-accent) 12%, #EEF2F7);
  margin-bottom: 8px;
  flex-shrink: 0;
}

.duty-card-name {
  font-size: 17px;
  font-weight: 800;
  color: #0B1120;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  line-height: 1.3;
}

.duty-card-title {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 1;
  padding: 4px 9px;
  border-radius: 6px;
  color: color-mix(in srgb, var(--duty-accent) 82%, #1e293b);
  background: color-mix(in srgb, var(--duty-accent) 9%, #fff);
  border: 1px solid color-mix(in srgb, var(--duty-accent) 22%, transparent);
  white-space: nowrap;
}

.duty-card-actions {
  margin-left: auto;
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity .18s;
  flex-shrink: 0;
}
.duty-card:hover .duty-card-actions { opacity: 1; }
.duty-card-btn {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background .15s, color .15s;
  padding: 0;
  font-size: 12.5px;
}
.duty-card-btn:hover { background: rgba(15, 23, 42, .06); color: #475569; }
.duty-card-btn.danger:hover { background: #FEE2E2; color: #DC2626; }

/* ================================================================
   卡片主体：唯一滚动区
   ================================================================ */
.duty-card-body {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  margin-right: -4px;
}

.duty-card-body::-webkit-scrollbar { width: 6px; }
.duty-card-body::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--duty-accent) 25%, #D8DEEA);
  border-radius: 3px;
}
.duty-card-body::-webkit-scrollbar-thumb:hover {
  background: color-mix(in srgb, var(--duty-accent) 40%, #B8C2D2);
}
.duty-card-body::-webkit-scrollbar-track { background: transparent; }

/* ================================================================
   职责行
   ================================================================ */
.duty-block {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.duty-block + .duty-block {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed color-mix(in srgb, var(--duty-accent) 10%, #EEF2F7);
}

.duty-line {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 6px 4px 22px;
  border-radius: 6px;
  font-size: 13.5px;
  line-height: 1.55;
  color: #64748b;
  transition: background .15s;
}

.duty-line::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 11px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: transparent;
  border: 1.5px solid #cbd5e1;
  box-sizing: border-box;
}

.duty-line--primary {
  color: #0f172a;
  font-weight: 600;
}
.duty-line--primary::before {
  background: var(--duty-accent);
  border: none;
  box-shadow: 0 0 6px color-mix(in srgb, var(--duty-accent) 40%, transparent);
}

.duty-line-text {
  flex: 1;
  min-width: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.duty-line:hover { background: rgba(15, 23, 42, .025); }

/* ================================================================
   卡片内空态
   ================================================================ */
.duty-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 100%;
  padding: 16px 0;
  color: #cbd5e1;
  font-size: 13.5px;
}
.duty-empty .bi { font-size: 22px; }

/* ================================================================
   看板空态
   ================================================================ */
.board-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  padding: 40px 20px;
}
.board-empty-icon {
  font-size: 48px;
  color: #CBD5E1;
  line-height: 1;
}

.board-empty-text { font-size: 16px; }

/* ================================================================
   Modal 内样式
   ================================================================ */
.item-modal-inner {
  background: #fff;
  border-radius: 12px;
  padding: 6px 2px 2px;
}
.item-duty-chip {
  --duty-accent: #4f46e5;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px 6px 6px;
  border-radius: 999px;
  background: linear-gradient(90deg,
    color-mix(in srgb, var(--duty-accent) 10%, #fff),
    color-mix(in srgb, var(--duty-accent) 4%, #fff));
  border: 1px solid color-mix(in srgb, var(--duty-accent) 24%, #e2e8f0);
}
.item-duty-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: var(--duty-accent);
  font-size: 14px;
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--duty-accent) 28%, #e2e8f0),
    0 2px 6px color-mix(in srgb, var(--duty-accent) 18%, transparent);
  flex-shrink: 0;
}
.item-duty-name { font-weight: 600; color: #0f172a; font-size: 13.5px; }
.item-duty-dot { color: #cbd5e1; font-weight: 600; }
.item-duty-title { color: color-mix(in srgb, var(--duty-accent) 70%, #334155); font-size: 12.5px; font-weight: 500; }

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

.item-level-switch { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
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
.item-level-card:hover { border-color: #cbd5e1; transform: translateY(-1px); box-shadow: 0 6px 16px -8px rgba(15,23,42,.15); }
.item-level-card.active { border-color: #d97706; background: linear-gradient(180deg, #fff7ed, #ffffff); box-shadow: 0 8px 20px -10px rgba(217,119,6,.42); }
.item-level-card:nth-of-type(2).active { border-color: #0f766e; background: linear-gradient(180deg, #f0fdfa, #ffffff); box-shadow: 0 8px 20px -10px rgba(15,118,110,.42); }

.item-level-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  background: linear-gradient(180deg, #fef3c7, #fde68a);
  color: #B45309;
  box-shadow: inset 0 0 0 1px rgba(253,224,71,.4), 0 2px 6px rgba(250,204,21,.15);
  flex-shrink: 0;
}
.item-level-icon.secondary {
  background: #F1F5F9;
  color: #475569;
  box-shadow: inset 0 0 0 1px #E2E8F0;
}

.item-level-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.item-level-name { font-size: 13.5px; font-weight: 600; color: #0f172a; line-height: 1.25; }
.item-level-name span:first-child { color: #b45309; }
.item-level-name .text-slate { color: #334155; }
.item-level-hint { font-size: 11.5px; color: #64748b; }

.item-level-check {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: #e2e8f0;
  transform: scale(.8);
  opacity: 0;
  transition: all .2s cubic-bezier(.2,.7,.2,1);
  flex-shrink: 0;
}
.item-level-check.show { opacity: 1; transform: scale(1); background: #d97706; box-shadow: 0 0 0 3px rgba(217,119,6,.14); }
.item-level-card:nth-of-type(2) .item-level-check.show { background: #0f766e; box-shadow: 0 0 0 3px rgba(15,118,110,.14); }

/* 岗位编辑弹窗 */
.duty-modal-box { width: 100%; max-width: 460px; margin: 0 auto; padding: 4px 2px 2px; }
.duty-form-mini { width: 100%; }
.duty-form-mini :deep(.el-form-item) { margin-bottom: 14px; }
.duty-form-mini :deep(.el-form-item__label) {
  width: 100% !important;
  text-align: center !important;
  justify-content: center !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: #475569 !important;
  padding-bottom: 4px !important;
}
.duty-form-mini :deep(.el-input__wrapper),
.duty-form-mini :deep(.el-select__wrapper) {
  border-radius: 10px !important;
  box-shadow: 0 0 0 1px #e2e8f0 inset !important;
}
.duty-form-mini :deep(.el-input__wrapper.is-focus),
.duty-form-mini :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--primary, #2C5CE8) inset !important;
}

.duty-mini-divider { position: relative; text-align: center; margin: 8px 0 14px; }
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

.duty-items-wrap { width: 100%; padding: 4px 2px 2px; background: transparent; border: none; box-sizing: border-box; }
.duty-items-stack { display: flex; flex-direction: column; gap: 8px; align-items: stretch; }

.duty-row-simple {
  display: grid;
  grid-template-columns: 26px 1fr 62px 28px;
  gap: 8px;
  align-items: start;
  padding: 8px;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
  background: #ffffff;
  transition: border-color .16s, background .16s;
}
.duty-row-simple:hover { border-color: #e2e8f0; background: #fafbfc; }
.duty-row-index {
  width: 26px; height: 26px; border-radius: 7px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #94a3b8; background: #f8fafc;
  flex-shrink: 0;
}
.duty-row-index.p { color: #d97706; background: #FFF7ED; box-shadow: inset 0 0 0 1px #FEF3C7; }

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
}

.duty-row-level { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 2px; }
.level-chip {
  height: 26px; border-radius: 7px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 500;
  color: #94a3b8; background: #f8fafc; border: 1px solid #e2e8f0;
  cursor: pointer; user-select: none;
  transition: all .16s;
}
.level-chip:hover { color: #64748b; border-color: #cbd5e1; }
.level-chip.on { color: #ffffff; border-color: transparent; background: #64748b; }
.duty-row-level .level-chip:first-child.on { background: #d97706; }
.duty-row-level .level-chip:nth-child(2).on { background: #0f766e; }

.duty-row-del {
  width: 28px; height: 28px; margin-top: 1px;
  border-radius: 50%; border: none;
  background: #f8fafc; color: #94a3b8;
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0;
  transition: all .16s;
  padding: 0;
}
.duty-row-del:hover { background: #FEE2E2; color: #dc2626; }
.duty-row-del .bi { font-size: 12px; }

.duty-empty-mini {
  text-align: center; padding: 18px 10px;
  border: 1px dashed #e2e8f0; border-radius: 10px;
  color: #94a3b8; font-size: 12.5px; background: #fafbfc;
}

.duty-add-center { display: flex; justify-content: center; margin-top: 12px; }
.duty-add-link-btn {
  height: 32px !important; min-width: 150px;
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