<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span class="emoji">📦</span> 库房管理</h1>

      <div class="ph-right-group">
        <el-input v-model="keyword" placeholder="名称 / 型号 / 借用人（支持扫码）" clearable
          style="width: 300px;" @keyup.enter="onSearch" @clear="onSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button @click="onSearch">搜索</el-button>
        <template v-if="userStore.canEdit">
          <el-button @click="openImport">批量导入</el-button>
          <el-button type="primary" @click="openEdit(null)">新增物品</el-button>
        </template>
      </div>
    </div>

    <div class="page-content wh-content">
      <div class="wh-tabs-row">
      <el-tabs v-model="activeTab" @tab-change="onTabChange" class="wh-tabs">
        <el-tab-pane label="🔧 治具" name="治具" />
        <el-tab-pane label="🧴 耗材" name="耗材" />
      </el-tabs>
      <div class="wh-mode-switch">
        <el-button text @click="txDrawer = true">操作记录</el-button>
        <el-button v-if="userStore.canEdit" type="warning" @click="openCartDrawer">
          <el-icon><ShoppingCart /></el-icon>
          借出/领用<span v-if="cartItems.length" class="cart-badge">{{ cartTotalQty }}</span>
        </el-button>
      </div>
    </div>

      <!-- 统计看板（精简） -->
      <div class="wh-stats">
        <template v-if="activeTab === '治具'">
          <div class="wh-stat clickable" :class="{ active: stockStatusFilter === 'in_stock' }" @click="filterByStatus('in_stock')">
            <div class="wh-stat-num ok">{{ stats.in_stock }}</div>
            <div class="wh-stat-label">在库</div>
          </div>
          <div class="wh-stat clickable" :class="{ active: stockStatusFilter === 'borrowed' }" @click="filterByStatus('borrowed')">
            <div class="wh-stat-num warn">{{ stats.borrowed_out }}</div>
            <div class="wh-stat-label">借出</div>
          </div>
        </template>
        <template v-else>
          <div class="wh-stat clickable" :class="{ active: stockStatusFilter === 'in_stock' }" @click="filterByStatus('in_stock')">
            <div class="wh-stat-num ok">{{ stats.in_stock }}</div>
            <div class="wh-stat-label">正常</div>
          </div>
          <div class="wh-stat clickable" :class="{ active: stockStatusFilter === 'low_stock' }" @click="filterByStatus('low_stock')">
            <div class="wh-stat-num danger">{{ stats.low_stock }}</div>
            <div class="wh-stat-label">低于预警</div>
          </div>
        </template>
      </div>

      <!-- 低库存预警条 -->
      <div v-if="lowItems.length" class="wh-warn-bar">
        <span class="wh-warn-title"><el-icon><WarningFilled /></el-icon> 低库存预警：</span>
        <div class="wh-warn-items">
          <span v-for="it in lowItems" :key="it.id" class="wh-warn-chip">
            {{ it.name }}
            <b>{{ it.stock_qty }}</b>/{{ it.warn_qty }}{{ it.unit }}
            <el-button v-if="userStore.canEdit" type="danger" size="small" plain @click.stop="openRestock(it)">补货</el-button>
          </span>
        </div>
      </div>

      <!-- 物品列表 -->
      <div class="wh-table-wrap">
      <el-table
        :data="items"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        empty-text="暂无数据"
        :header-cell-style="{ fontWeight: 600 }"
        @row-click="openDetail"
      >
        <el-table-column label="物品名称" min-width="180" align="left" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="wh-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="型号/编号" prop="model" min-width="130" align="left" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.model" style="font-family: Consolas, monospace;">{{ row.model }}</span>
            <span v-else style="color: var(--c-text-mute);">-</span>
          </template>
        </el-table-column>

        <!-- 治具专属列 -->
        <template v-if="activeTab === '治具'">
          <el-table-column label="总数" prop="total_qty" width="90" align="center" />
          <el-table-column label="可用" width="90" align="center">
            <template #default="{ row }"><b class="ok-text">{{ row.available_qty }}</b></template>
          </el-table-column>
          <el-table-column label="外借" width="90" align="center">
            <template #default="{ row }">
              <b :class="row.total_qty - row.available_qty > 0 ? 'warn-text' : ''">{{ row.total_qty - row.available_qty }}</b>
            </template>
          </el-table-column>
        </template>

        <!-- 耗材专属列 -->
        <template v-else>
          <el-table-column label="库存" width="100" align="center">
            <template #default="{ row }">
              <b :style="{ color: row.status === '缺货' ? '#DC2626' : 'var(--c-text)' }">{{ row.stock_qty }}</b>
              <span style="font-size:12px;color:var(--c-text-mute)"> {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="预警值" prop="warn_qty" width="90" align="center" />
        </template>

        <el-table-column label="货位" prop="location" width="110" align="left">
          <template #default="{ row }">{{ row.location || '-' }}</template>
        </el-table-column>

        <el-table-column label="状态" min-width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="320" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="userStore.canEdit">
              <!-- 治具 -->
              <template v-if="row.part_type === '治具'">
                <el-button v-if="row.status === '维修中'" type="info" link size="small" disabled>维修中</el-button>
                <template v-else>
                  <el-button v-if="row.available_qty > 0"
                    type="primary" link size="small" @click.stop="openBorrow(row)">借出</el-button>
                  <el-button v-else type="info" link size="small" disabled @click.stop="toast.warn(`「${row.name}」库存不足，请先补货`)">借出</el-button>
                  <el-button v-if="row.status === '已借出' || row.status === '部分借出'"
                    type="warning" link size="small" @click.stop="openReturn(row)">归还</el-button>
                  <el-button v-else type="info" link size="small" disabled>归还</el-button>
                </template>
              </template>
              <!-- 耗材 -->
              <template v-else>
                <el-button v-if="row.stock_qty > 0"
                  type="primary" link size="small" @click.stop="openConsume(row)">领用</el-button>
                <el-button v-else type="info" link size="small" @click.stop="toast.warn(`「${row.name}」库存不足，请及时补货`)">领用</el-button>
                <el-button type="success" link size="small" @click.stop="openRestock(row)">补货</el-button>
              </template>
              <!-- 公共 -->
              <el-button type="info" link size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button v-if="userStore.isAdmin" type="danger" link size="small" @click.stop="handleDelete(row)">删除</el-button>
            </template>
            <span v-else style="color: var(--c-text-mute); font-size: 12px;">点击行查看详情</span>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty :image-size="80" description="暂无物品...">
            <template #image><div style="font-size:44px;">📦</div></template>
          </el-empty>
        </template>
      </el-table>
      </div>

      <CommonPagination v-model:page="page" v-model:page-size="pageSize" :total="total" compact />
    </div>

    <!-- 购物车抽屉（扫码 + 借出/领用/归还 一站式） -->
    <el-drawer
      v-model="cartDrawer"
      direction="rtl"
      size="480px"
      destroy-on-close
      class="cart-drawer"
      :with-header="false"
    >
      <div class="cd-wrap">
        <header class="cd-header">
          <div class="cd-title">
            <el-icon><ShoppingCart /></el-icon>
            <span>{{ scanModeName }}</span>
            <span v-if="cartItems.length" class="cd-count">{{ cartTotalQty }} 件</span>
          </div>
          <el-button text @click="cartDrawer = false"><el-icon><Close /></el-icon></el-button>
        </header>

        <!-- 模式选择 -->
        <div class="cd-mode-bar">
          <el-radio-group v-model="scanMode" size="small">
            <el-radio-button label="borrow" v-if="activeTab === '治具'">借出</el-radio-button>
            <el-radio-button label="return" v-if="activeTab === '治具'">归还</el-radio-button>
            <el-radio-button label="consume" v-if="activeTab === '耗材'">领用</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 扫码输入 -->
        <div class="cd-scan-bar">
          <el-input
            ref="scanInputRef"
            v-model="scanKeyword"
            :placeholder="scanPlaceholder"
            clearable
            @keyup.enter="onScan"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>

        <!-- 购物车列表 -->
        <div class="cd-body">
          <div v-if="!cartItems.length" class="cd-empty">
            <span style="font-size:36px;">📦</span>
            <p>暂无添加物品</p>
            <span class="cd-empty-sub">扫码或输入物品名称，回车添加</span>
          </div>

          <div v-else class="cd-list">
            <div v-for="item in cartItems" :key="item.id" class="cd-row">
              <div class="cd-row-info">
                <span class="cd-row-name">{{ item.name }}</span>
                <span class="cd-row-model">{{ item.model || '-' }}</span>
              </div>
              <div class="cd-row-qty">
                <el-button size="small" circle @click="changeQty(item, -1)"><el-icon><Minus /></el-icon></el-button>
                <span class="cd-qty-num">{{ item.qty }}</span>
                <el-button size="small" circle @click="changeQty(item, 1)" :disabled="item.qty >= item.maxQty">
                  <el-icon><Plus /></el-icon></el-button>
                <span class="cd-qty-limit">/{{ item.maxQty }}</span>
              </div>
              <el-button text type="danger" size="small" @click="removeFromCart(item.id)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 底部信息 + 提交 -->
        <footer class="cd-footer">
          <div class="cd-form-row" v-if="scanMode !== 'return'">
            <el-input v-model="scanForm.operator" placeholder="借用人/领用人姓名 *" maxlength="50" />
            <el-select v-model="scanForm.line" placeholder="线体 *" style="width:110px;">
              <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
            </el-select>
          </div>
          <div class="cd-form-row" v-if="scanMode === 'borrow'">
            <el-date-picker v-model="scanForm.expected_return" type="date" value-format="YYYY-MM-DD"
              placeholder="预计归还日期" style="width:100%;" />
          </div>
          <el-input v-model="scanForm.remark" placeholder="备注（选填）" maxlength="255" />
          <div class="cd-submit-row">
            <el-button text type="danger" :disabled="!cartItems.length" @click="clearCart">清空</el-button>
            <el-button type="primary" size="large" :loading="scanSubmitting"
              :disabled="!cartItems.length" @click="submitBatch">
              <el-icon><Check /></el-icon>
              提交（{{ cartTotalQty }} 件）
            </el-button>
          </div>
        </footer>
      </div>
    </el-drawer>

    <!-- 新增 / 编辑物品 -->
    <el-dialog v-model="editDialog" :title="editForm.id ? '编辑物品' : '新增物品'" width="560px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="92px">
        <el-form-item label="物品名称" prop="name" required>
          <el-input v-model="editForm.name" placeholder="如：测试治具A / 高温胶带" maxlength="100" />
        </el-form-item>
        <el-form-item label="型号/编号">
          <el-input v-model="editForm.model" placeholder="设备型号或内部编号" maxlength="100" />
        </el-form-item>
        <el-form-item label="类型" prop="part_type" required>
          <el-radio-group v-model="editForm.part_type" :disabled="!!editForm.id">
            <el-radio value="治具">🔧 治具</el-radio>
            <el-radio value="耗材">🧴 耗材</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editForm.part_type === '治具'" label="总数">
          <el-input-number v-model="editForm.total_qty" :min="0" :max="9999" controls-position="right" />
          <span class="wh-form-hint">治具总数量（新增时可用数=总数）</span>
        </el-form-item>
        <el-form-item v-if="editForm.part_type === '治具' && editForm.id" label="维修状态">
          <el-switch v-model="editForm.in_repair" active-text="维修中（不可借出）" inactive-text="正常" />
        </el-form-item>
        <template v-if="editForm.part_type === '耗材'">
          <el-form-item :label="editForm.id ? '库存数量' : '初始库存'">
            <el-input-number v-model="editForm.total_qty" :min="0" :max="999999" controls-position="right" />
          </el-form-item>
          <el-form-item label="单位">
            <el-input v-model="editForm.unit" placeholder="个 / 卷 / 包 / 瓶…" maxlength="20" style="width: 160px;" />
          </el-form-item>
          <el-form-item label="预警值">
            <el-input-number v-model="editForm.warn_qty" :min="0" :max="999999" controls-position="right" />
            <span class="wh-form-hint">库存 ≤ 预警值时顶部预警并标红</span>
          </el-form-item>
        </template>
        <el-form-item label="货位">
          <el-input v-model="editForm.location" placeholder="如 A01-1-2" maxlength="50" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="editForm.supplier" placeholder="选填" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 治具借出 -->
    <el-dialog v-model="borrowDialog" title="🔧 治具借出" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>可用数量：<b class="ok-text">{{ actionRow.available_qty }}</b> / {{ actionRow.total_qty }}</p>
      </div>
      <el-form :model="borrowForm" label-width="92px">
        <el-form-item label="借用人" required>
          <el-input v-model="borrowForm.operator" placeholder="借用人姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="线体" required>
          <el-select v-model="borrowForm.line" placeholder="选择线体" style="width: 100%;">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="borrowForm.qty" :min="1" :max="actionRow?.available_qty || 1" controls-position="right" />
        </el-form-item>
        <el-form-item label="预计归还">
          <el-date-picker v-model="borrowForm.expected_return" type="date" value-format="YYYY-MM-DD"
            placeholder="选择日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="borrowForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="borrowDialog = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="submitBorrow">确认借出</el-button>
      </template>
    </el-dialog>

    <!-- 治具归还 -->
    <el-dialog v-model="returnDialog" title="🔧 治具归还" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>库存情况：总 {{ actionRow.total_qty }} / 可用 <b class="ok-text">{{ actionRow.available_qty }}</b> / 外借未还 <b class="warn-text">{{ actionRow.total_qty - actionRow.available_qty }}</b></p>
        <p>当前借用人：<b class="warn-text">{{ actionRow.current_borrower || '多笔借出（见操作记录）' }}</b></p>
        <p>借出时间：{{ actionRow.borrow_time || '-' }}　预计归还：{{ actionRow.expected_return || '-' }}</p>
        <p class="wh-return-hint">确认归还将一次性收回全部外借数量（{{ actionRow.total_qty - actionRow.available_qty }} 件）；部分归还请在备注中说明后联系管理员调整总数。</p>
      </div>
      <el-form :model="returnForm" label-width="92px">
        <el-form-item label="备注">
          <el-input v-model="returnForm.remark" type="textarea" :rows="2" maxlength="255" placeholder="归还情况备注（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnDialog = false">取消</el-button>
        <el-button type="warning" :loading="actionLoading" @click="submitReturn">确认归还</el-button>
      </template>
    </el-dialog>

    <!-- 耗材领用 -->
    <el-dialog v-model="consumeDialog" title="🧴 耗材领用" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : 'ok-text'">
          {{ actionRow.stock_qty }}</b> {{ actionRow.unit }}　预警值：{{ actionRow.warn_qty }}
        </p>
      </div>
      <el-form :model="consumeForm" label-width="92px">
        <el-form-item label="领用人" required>
          <el-input v-model="consumeForm.operator" placeholder="领用人姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="线体" required>
          <el-select v-model="consumeForm.line" placeholder="选择线体" style="width: 100%;">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" required>
          <el-input-number v-model="consumeForm.qty" :min="1" :max="actionRow?.stock_qty || 1" controls-position="right" />
          <span class="wh-form-hint">{{ actionRow?.unit }}</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="consumeForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="consumeDialog = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="submitConsume">确认领用</el-button>
      </template>
    </el-dialog>

    <!-- 耗材补货 -->
    <el-dialog v-model="restockDialog" title="🧴 耗材补货" width="480px" destroy-on-close>
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : ''">
          {{ actionRow.stock_qty }}</b> {{ actionRow.unit }}　预警值：{{ actionRow.warn_qty }}
        </p>
      </div>
      <el-form :model="restockForm" label-width="92px">
        <el-form-item label="补货数量" required>
          <el-input-number v-model="restockForm.qty" :min="1" :max="999999" controls-position="right" />
          <span class="wh-form-hint">{{ actionRow?.unit }}</span>
        </el-form-item>
        <el-form-item label="供应商">
          <el-input v-model="restockForm.supplier" placeholder="选填" maxlength="100" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="restockForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="restockDialog = false">取消</el-button>
        <el-button type="success" :loading="actionLoading" @click="submitRestock">确认补货</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importDialog" title="📥 批量导入物品" width="560px" destroy-on-close>
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="onFileChange"
        :on-remove="onFileRemove"
        :on-exceed="onExceed"
      >
        <div style="padding: 16px 0;">
          <el-icon style="font-size: 42px; color: var(--primary-500);"><UploadFilled /></el-icon>
          <div class="el-upload__text" style="margin-top: 8px;">将 Excel 文件拖到此处，或<em>点击上传</em></div>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx / .xls；表头列：<b>物品名称、型号、类型、数量、货位、单位、预警值、供应商</b>（物品名称必填，类型留空默认耗材）
          </div>
        </template>
      </el-upload>

      <div v-if="importResult" class="wh-import-result">
        <div class="wh-import-summary">
          <span class="ok-text">✅ 成功 {{ importResult.success }} 条</span>
          <span v-if="importResult.failed" class="danger-text">❌ 失败 {{ importResult.failed }} 条</span>
        </div>
        <div v-if="importResult.errors?.length" class="wh-import-errors">
          <div v-for="(msg, i) in importResult.errors" :key="i" class="wh-import-error-line">{{ msg }}</div>
        </div>
      </div>

      <template #footer>
        <el-button @click="importDialog = false">{{ importResult ? '关闭' : '取消' }}</el-button>
        <el-button v-if="!importResult" type="primary" :loading="importing" :disabled="!importFile" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 物品详情（点击行打开） -->
    <el-dialog v-model="detailDialog" title="物品详情" width="620px" destroy-on-close>
      <div v-if="detail" class="wh-detail">
        <div class="wh-detail-head">
          <span class="wh-detail-name">{{ detail.part.name }}</span>
          <el-tag :type="statusTagType(detail.part)" size="small">{{ detail.part.status }}</el-tag>
        </div>

        <el-descriptions :column="2" border size="small" class="wh-desc">
          <el-descriptions-item label="类型">{{ detail.part.part_type }}</el-descriptions-item>
          <el-descriptions-item label="型号/编号">{{ detail.part.model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="货位">{{ detail.part.location || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数量">{{ detail.part.qty_text }}</el-descriptions-item>
        </el-descriptions>

        <!-- 治具借出信息 -->
        <div v-if="detail.part.part_type === '治具' && (detail.part.status === '已借出' || detail.part.status === '部分借出')" class="wh-detail-block">
          <div class="wh-detail-subtitle">📌 当前借用人</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="借用人">{{ detail.part.current_borrower }}</el-descriptions-item>
            <el-descriptions-item label="借出时间">{{ detail.part.borrow_time }}</el-descriptions-item>
            <el-descriptions-item label="预计归还">{{ detail.part.expected_return || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 耗材低库存提示 -->
        <div v-if="detail.part.part_type === '耗材' && detail.part.stock_qty <= detail.part.warn_qty" class="wh-low-tip">
          <span class="bi bi-exclamation-triangle-fill"></span>
          库存预警：当前剩余 {{ detail.part.stock_qty }} {{ detail.part.unit }}，已低于预警值 {{ detail.part.warn_qty }}，请及时补货！
        </div>

        <!-- 最近操作记录 -->
        <div class="wh-detail-block">
          <div class="wh-detail-subtitle">最近操作记录</div>
          <el-table :data="detail.transactions" size="small" border empty-text="暂无记录">
            <el-table-column label="时间" prop="created_at" width="150" />
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="txTagType(row.tx_type)" size="small">{{ row.tx_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数量" prop="qty" width="60" align="center" />
            <el-table-column label="借/领用人" prop="operator" width="90" show-overflow-tooltip />
            <el-table-column label="线体" prop="line" width="70" align="center" />
            <el-table-column label="备注" prop="remark" min-width="100" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 操作记录抽屉（可查询） -->
    <el-drawer v-model="txDrawer" title="操作记录" size="800px" destroy-on-close @open="loadTxData">
      <div class="tx-filter">
        <el-input v-model="txKeyword" placeholder="物品名称 / 借领用人" clearable
          style="width: 240px;" @keyup.enter="loadTxData" @clear="loadTxData">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="txTypeFilter" placeholder="操作类型" clearable style="width: 130px;" @change="loadTxData">
          <el-option label="借出" value="借出" />
          <el-option label="归还" value="归还" />
          <el-option label="领用" value="领用" />
          <el-option label="补货" value="补货" />
        </el-select>
        <el-button @click="loadTxData">查询</el-button>
      </div>
      <el-table :data="txRecords" v-loading="txLoading" stripe border size="small" empty-text="暂无记录"
        :header-cell-style="{ fontWeight: 600 }">
        <el-table-column label="时间" prop="created_at" width="155" align="center" />
        <el-table-column label="操作" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="txTagType(row.tx_type)" size="small">{{ row.tx_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="物品名称" prop="part_name" min-width="140" show-overflow-tooltip />
        <el-table-column label="数量" prop="qty" width="60" align="center" />
        <el-table-column label="借/领用人" prop="operator" width="100" show-overflow-tooltip />
        <el-table-column label="线体" prop="line" width="80" align="center" />
        <el-table-column label="备注" prop="remark" min-width="120" show-overflow-tooltip />
      </el-table>
      <div style="margin-top: 16px;">
        <CommonPagination v-model:page="txPage" v-model:page-size="txPageSize" :total="txTotal" compact />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed, nextTick } from 'vue'
import { warehouseApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { Search, RefreshRight, Plus, ArrowDown, Upload, UploadFilled, WarningFilled,
         ShoppingCart, Delete, Minus, Close, Check } from '@element-plus/icons-vue'
import { useNotify } from '@/composables/useNotify'
import CommonPagination from '@/components/common/CommonPagination.vue'

const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()

const lines = ['1线', '2线', '3线', '4线', '5线', '6线', '7线', '8线', '品质房', '维修房']

// ---------------- 列表 / 统计 ----------------
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const keyword = ref('')
const activeTab = ref('治具')
// 统计卡联动：'' 全部 / 'in_stock' 在库 / 'borrowed' 借出领用 / 'low_stock' 低于预警
const stockStatusFilter = ref('')
const stats = reactive({ total: 0, in_stock: 0, borrowed_out: 0, low_stock: 0 })
const lowItems = ref([])

// 操作记录抽屉（可查询）
const txDrawer = ref(false)
const txRecords = ref([])
const txKeyword = ref('')
const txTypeFilter = ref('')
const txPage = ref(1)
const txPageSize = ref(20)
const txTotal = ref(0)
const txLoading = ref(false)

const loadTxData = async () => {
  txLoading.value = true
  try {
    const params = { page: txPage.value, page_size: txPageSize.value }
    if (txKeyword.value) params.keyword = txKeyword.value
    if (txTypeFilter.value) params.tx_type = txTypeFilter.value
    const res = await warehouseApi.transactions(params)
    txRecords.value = res.data?.items || []
    txTotal.value = res.data?.total || 0
  } catch (e) {
    console.error('加载操作记录失败:', e)
    txRecords.value = []
    txTotal.value = 0
  } finally {
    txLoading.value = false
  }
}

watch([txPage, txPageSize], () => { if (txDrawer.value) loadTxData() })

const statusTagType = (row) => {
  if (row.part_type === '治具') {
    return { '在库': 'success', '已借出': 'danger', '部分借出': 'warning', '维修中': 'info' }[row.status] || 'info'
  }
  return { '正常': 'success', '低于预警': 'warning', '缺货': 'danger' }[row.status] || 'info'
}
const txTagType = (t) => ({ '借出': 'warning', '归还': 'success', '领用': 'primary', '补货': 'success' }[t] || 'info')

const loadStats = async () => {
  try {
    const res = await warehouseApi.stats({ part_type: activeTab.value })
    Object.assign(stats, res.data || {})
    lowItems.value = res.data?.low_stock_items || []
  } catch (e) { console.error(e) }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    params.part_type = activeTab.value
    if (stockStatusFilter.value) params.stock_status = stockStatusFilter.value
    const res = await warehouseApi.list(params)
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const refreshAll = () => { loadData(); loadStats() }

const onSearch = () => { page.value = 1; loadData() }
const onTabChange = () => {
  page.value = 1
  stockStatusFilter.value = ''
  refreshAll()
}
const onReset = () => {
  keyword.value = ''
  stockStatusFilter.value = ''
  page.value = 1
  loadData()
}
// 统计卡点击：再次点击同一筛选则取消（回到全部）
const filterByStatus = (s) => {
  stockStatusFilter.value = stockStatusFilter.value === s ? '' : s
  page.value = 1
  loadData()
}
watch([page, pageSize], () => loadData())

// ---------------- 新增 / 编辑 ----------------
const editDialog = ref(false)
const editFormRef = ref(null)
const saving = ref(false)
const editRules = {
  name: [{ required: true, message: '请填写物品名称', trigger: 'blur' }],
  part_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}
const editForm = reactive({
  id: null, name: '', model: '', part_type: '治具',
  total_qty: 1, unit: '个', location: '', warn_qty: 0, supplier: '', in_repair: false,
})

const openEdit = (row) => {
  if (row) {
    Object.assign(editForm, {
      id: row.id, name: row.name, model: row.model, part_type: row.part_type,
      total_qty: row.total_qty, unit: row.unit, location: row.location,
      warn_qty: row.warn_qty, supplier: row.supplier, in_repair: row.in_repair,
    })
  } else {
    Object.assign(editForm, {
      id: null, name: '', model: '', part_type: '治具',
      total_qty: 1, unit: '个', location: '', warn_qty: 0, supplier: '', in_repair: false,
    })
  }
  editDialog.value = true
}

const submitEdit = async () => {
  try {
    await editFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload = { ...editForm }
    if (editForm.id) {
      await warehouseApi.update(editForm.id, payload)
      toast.success('修改成功')
    } else {
      await warehouseApi.create(payload)
      toast.success('新增成功')
    }
    editDialog.value = false
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || e.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  const ok = await confirmDelete('库房物品', `将删除「${row.name}」及其全部流水记录`)
  if (!ok) return
  try {
    await warehouseApi.delete(row.id)
    toast.success('删除成功')
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '删除失败')
  }
}

// ---------------- 批量导入 ----------------
const uploadRef = ref(null)
const importDialog = ref(false)
const importing = ref(false)
const importFile = ref(null)
const importResult = ref(null)

const openImport = () => {
  importFile.value = null
  importResult.value = null
  importDialog.value = true
}

const onFileChange = (file) => {
  const name = (file.name || '').toLowerCase()
  if (!name.endsWith('.xlsx') && !name.endsWith('.xls')) {
    toast.error('仅支持 .xlsx / .xls 文件')
    uploadRef.value?.clearFiles()
    importFile.value = null
    return
  }
  importFile.value = file.raw
  importResult.value = null
}
const onFileRemove = () => { importFile.value = null }
const onExceed = () => { toast.warning('一次只能导入一个文件，请先移除已选文件') }

const handleImport = async () => {
  if (!importFile.value) { toast.error('请先选择 Excel 文件'); return }
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    const res = await warehouseApi.importParts(fd)
    importResult.value = res.data
    if (res.data?.success > 0) {
      toast.success(`导入完成：成功 ${res.data.success} 条，失败 ${res.data.failed} 条`)
      refreshAll()
    } else {
      toast.error('导入失败，请检查文件内容')
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || '导入失败，请检查文件格式')
  } finally {
    importing.value = false
  }
}

// ---------------- 借出 / 归还 / 领用 / 补货 ----------------
const borrowDialog = ref(false)
const returnDialog = ref(false)
const consumeDialog = ref(false)
const restockDialog = ref(false)
const actionLoading = ref(false)
const actionRow = ref(null)
const borrowForm = reactive({ operator: '', line: '', qty: 1, expected_return: '', remark: '' })
const returnForm = reactive({ remark: '' })
const consumeForm = reactive({ operator: '', line: '', qty: 1, remark: '' })
const restockForm = reactive({ qty: 1, supplier: '', remark: '' })

const resetActionForms = () => {
  Object.assign(borrowForm, { operator: '', line: '', qty: 1, expected_return: '', remark: '' })
  Object.assign(returnForm, { remark: '' })
  Object.assign(consumeForm, { operator: '', line: '', qty: 1, remark: '' })
  Object.assign(restockForm, { qty: 1, supplier: '', remark: '' })
}

const openBorrow = (row) => { actionRow.value = row; resetActionForms(); borrowForm.qty = 1; borrowDialog.value = true }
const openReturn = (row) => { actionRow.value = row; resetActionForms(); returnDialog.value = true }
const openConsume = (row) => { actionRow.value = row; resetActionForms(); consumeForm.qty = 1; consumeDialog.value = true }
const openRestock = (row) => { actionRow.value = row; resetActionForms(); restockForm.qty = 1; restockForm.supplier = row.supplier || ''; restockDialog.value = true }

const afterAction = (msg) => {
  toast.success(msg)
  borrowDialog.value = returnDialog.value = consumeDialog.value = restockDialog.value = false
  refreshAll()
}

const submitBorrow = async () => {
  if (!borrowForm.operator?.trim() || !borrowForm.line) { toast.error('请填写借用人并选择线体'); return }
  actionLoading.value = true
  try {
    await warehouseApi.borrow(actionRow.value.id, { ...borrowForm })
    afterAction('借出成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitReturn = async () => {
  actionLoading.value = true
  try {
    await warehouseApi.returnBack(actionRow.value.id, { ...returnForm })
    afterAction('归还成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitConsume = async () => {
  if (!consumeForm.operator?.trim() || !consumeForm.line) { toast.error('请填写领用人并选择线体'); return }
  actionLoading.value = true
  try {
    await warehouseApi.consume(actionRow.value.id, { ...consumeForm })
    afterAction('领用成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitRestock = async () => {
  if (!restockForm.qty || restockForm.qty <= 0) { toast.error('请填写补货数量'); return }
  actionLoading.value = true
  try {
    await warehouseApi.restock(actionRow.value.id, { ...restockForm })
    afterAction('补货成功')
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

// ---------------- 详情 ----------------
const detailDialog = ref(false)
const detail = ref(null)

const openDetail = async (row) => {
  try {
    const res = await warehouseApi.detail(row.id)
    detail.value = res.data
    detailDialog.value = true
  } catch (e) {
    console.error(e)
    toast.error('详情加载失败')
  }
}

onMounted(() => {
  loadData()
  loadStats()
})

// ---------------- 扫码购物车（抽屉模式） ----------------
const cartDrawer = ref(false)
const scanMode = ref('borrow')             // 'borrow' | 'return' | 'consume'
const scanKeyword = ref('')
const scanLoading = ref(false)
const scanInputRef = ref(null)
const cartItems = ref([])                  // [{ id, name, model, part_type, qty, maxQty }]
const scanSubmitting = ref(false)
const scanForm = reactive({ operator: '', line: '', expected_return: '', remark: '' })

const scanModeName = computed(() => {
  const map = { borrow: '治具借出', return: '治具归还', consume: '耗材领用' }
  return map[scanMode.value] || '借出/领用'
})

const scanPlaceholder = computed(() => {
  const map = {
    borrow: '扫码或输入治具名称/型号，回车添加',
    return: '扫码或输入治具名称/型号，回车添加到归还列表',
    consume: '扫码或输入耗材名称/型号，回车添加',
  }
  return map[scanMode.value] || '扫码或搜索'
})

const cartTotalQty = computed(() => cartItems.value.reduce((s, i) => s + i.qty, 0))

const focusScanInput = () => { nextTick(() => scanInputRef.value?.focus()) }

// 切换 Tab 时重置扫码模式
watch(activeTab, (t) => {
  scanMode.value = t === '治具' ? 'borrow' : 'consume'
  cartItems.value = []
})

const openCartDrawer = () => {
  cartDrawer.value = true
  nextTick(focusScanInput)
}

const onScan = async () => {
  const kw = scanKeyword.value.trim()
  if (!kw) return
  scanLoading.value = true
  try {
    const res = await warehouseApi.list({ keyword: kw, part_type: activeTab.value, page: 1, page_size: 5 })
    const found = res.data?.items || []
    if (!found.length) {
      toast.error('未找到匹配物品')
    } else if (found.length === 1) {
      addToCart(found[0])
      scanKeyword.value = ''
      focusScanInput()
    } else {
      // 多条匹配：让用户选第一个，后续可优化为弹窗选择
      addToCart(found[0])
      toast.info(`匹配到 ${found.length} 条，已添加第一条「${found[0].name}」`)
      scanKeyword.value = ''
      focusScanInput()
    }
  } catch (e) {
    console.error(e)
    toast.error('搜索失败')
  } finally {
    scanLoading.value = false
  }
}

const addToCart = (item) => {
  // 计算可用上限
  let maxQty = 0
  if (scanMode.value === 'borrow') {
    maxQty = item.available_qty || 0
  } else if (scanMode.value === 'return') {
    maxQty = (item.total_qty || 0) - (item.available_qty || 0)   // 当前借出数
  } else {
    maxQty = item.stock_qty || item.total_qty || 0
  }
  if (maxQty <= 0) {
    toast.error(`「${item.name}」${scanMode.value === 'return' ? '没有借出记录' : '库存不足'}`)
    return
  }
  // 已在购物车则 +1
  const existing = cartItems.value.find(c => c.id === item.id)
  if (existing) {
    if (existing.qty >= maxQty) { toast.error(`「${item.name}」已达上限 ${maxQty}`); return }
    existing.qty++
    existing.maxQty = maxQty
  } else {
    cartItems.value.push({ id: item.id, name: item.name, model: item.model, part_type: item.part_type, qty: 1, maxQty })
  }
}

const changeQty = (item, delta) => {
  const newQty = item.qty + delta
  if (newQty < 1) { removeFromCart(item.id); return }
  if (newQty > item.maxQty) { toast.error(`上限 ${item.maxQty}`); return }
  item.qty = newQty
}

const removeFromCart = (id) => { cartItems.value = cartItems.value.filter(c => c.id !== id) }
const clearCart = () => { cartItems.value = [] }

const submitBatch = async () => {
  if (!cartItems.value.length) return
  // 借出/领用需要借用人 + 线体
  if (scanMode.value !== 'return') {
    if (!scanForm.operator?.trim()) { toast.error('请填写借用人/领用人'); return }
    if (!scanForm.line) { toast.error('请选择线体'); return }
  }
  scanSubmitting.value = true
  const results = { ok: 0, fail: 0, errors: [] }
  try {
    for (const item of cartItems.value) {
      try {
        const payload = { qty: item.qty, remark: scanForm.remark }
        if (scanMode.value === 'return') {
          await warehouseApi.returnBack(item.id, payload)
        } else {
          payload.operator = scanForm.operator
          payload.line = scanForm.line
          if (scanMode.value === 'borrow') {
            payload.expected_return = scanForm.expected_return
            await warehouseApi.borrow(item.id, payload)
          } else {
            await warehouseApi.consume(item.id, payload)
          }
        }
        results.ok++
      } catch (e) {
        results.fail++
        results.errors.push(`${item.name}: ${e.response?.data?.detail || '操作失败'}`)
      }
    }
    if (results.fail === 0) {
      toast.success(`全部成功（${results.ok} 件）`)
      clearCart()
    } else {
      toast.error(`成功 ${results.ok} 件，失败 ${results.fail} 件：\n${results.errors.join('\n')}`)
      // 移除成功的物品，保留失败的
      cartItems.value = cartItems.value.filter(item => {
        return !results.errors.some(e => e.startsWith(item.name + ':'))
      })
    }
    refreshAll()
  } catch (e) {
    toast.error('批量提交失败')
  } finally {
    scanSubmitting.value = false
  }
}
</script>

<style scoped>
/* 间距 / 圆角 Token */
:root {
  --sp-1: 8px; --sp-2: 12px; --sp-3: 16px; --sp-4: 24px;
  --r-sm: 6px; --r-md: 8px; --r-lg: 12px; --r-pill: 999px;
}
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
/* 顶部标题栏（与筛选合并为一行） */
.page-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px var(--sp-2);
  border-bottom: 1px solid var(--c-divider);
  flex-wrap: wrap;
  flex-shrink: 0;    /* ← 新增 */
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.ph-right-group {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 内容区 — flex 撑满 */
.wh-content {
  display: flex;
  flex-direction: column;
  flex: 1;                /* ← 撑满 .page 剩余高度 */
  min-height: 0;          /* ← 关键：允许内部收缩 */
  padding-bottom: 16px;   /* ← 关键：给 fixed 分页条预留空间 */
  box-sizing: border-box;
}
.wh-tabs { flex-shrink: 0; }
.wh-tabs-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.wh-stats { flex-shrink: 0; }
.wh-warn-bar { flex-shrink: 0; }
.wh-table-wrap { flex: 1; min-height: 0; }
.wh-table-wrap :deep(.el-table) { height: 100%; }

/* 统计看板 */
.wh-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
  margin-bottom: 10px;
}
.wh-stat {
  background: #fff;
  border: 1px solid var(--c-divider);
  border-radius: var(--r-md);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(15, 23, 42, .03);
}
.wh-stat.clickable { cursor: pointer; transition: all .15s; }
.wh-stat.clickable:hover { border-color: #93C5FD; box-shadow: 0 4px 12px rgba(59,130,246,.10); }
.wh-stat.active { border-color: #3B82F6; background: #EFF6FF; }
.wh-stat-num { font-size: 26px; font-weight: 800; color: var(--c-text); line-height: 1; }
.wh-stat-num.ok { color: #059669; }
.wh-stat-num.warn { color: #D97706; }
.wh-stat-num.danger { color: #DC2626; }
.wh-stat-label { font-size: 13px; color: var(--c-text-3); }

/* 低库存预警条 */
.wh-warn-bar {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-1);
  padding: var(--sp-1) 14px;
  margin-bottom: 10px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: var(--r-sm);
  font-size: 13px;
}
.wh-warn-title { color: #DC2626; font-weight: 700; white-space: nowrap; padding-top: 3px; display: flex; align-items: center; gap: 4px; }
.wh-warn-items { display: flex; flex-wrap: wrap; gap: var(--sp-1); }
.wh-warn-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #fff;
  border: 1px solid #FECACA;
  border-radius: var(--r-pill);
  padding: 2px 6px 2px var(--sp-2);
  color: var(--c-text-2);
}
.wh-warn-chip b { color: #DC2626; }

/* 表格 */
.wh-name { font-weight: 600; color: var(--c-text); }
.wh-repair-text { color: var(--c-text-mute); font-size: 12px; }

/* 操作记录抽屉筛选 */
.tx-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.wh-form-hint { margin-left: 10px; font-size: 12px; color: var(--c-text-mute); }
.ok-text { color: #059669; }
.warn-text { color: #D97706; }
.danger-text { color: #DC2626; }

/* 操作弹窗信息块 */
.wh-action-info {
  background: #F8FAFC;
  border: 1px solid var(--c-divider);
  border-radius: var(--r-sm);
  padding: 10px 14px;
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--c-text-2);
}
.wh-action-info p { margin: 2px 0; }
.wh-return-hint { color: #92400E; font-size: 12px; line-height: 1.5; margin-top: 6px !important; }

/* 详情弹窗 */
.wh-detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: var(--sp-2);
}
.wh-detail-name { font-size: 17px; font-weight: 700; color: var(--c-text); }
.wh-detail-block { margin-top: 14px; }
.wh-detail-subtitle {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--c-text);
  margin-bottom: 6px;
}
.wh-low-tip {
  margin-top: 14px;
  padding: 10px 14px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: var(--r-sm);
  color: #DC2626;
  font-size: 13px;
  font-weight: 600;
}
.wh-desc { margin-bottom: 4px; }

/* 批量导入结果 */
.wh-import-result {
  margin-top: 14px;
  border: 1px solid var(--c-divider);
  border-radius: var(--r-sm);
  padding: 10px 14px;
  background: #F8FAFC;
}
.wh-import-summary {
  display: flex;
  gap: 18px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 6px;
}
.wh-import-errors {
  max-height: 160px;
  overflow-y: auto;
  border-top: 1px dashed var(--c-divider);
  padding-top: 6px;
}
.wh-import-error-line {
  font-size: 12.5px;
  color: #DC2626;
  line-height: 1.9;
}

/* ---- 模式切换 ---- */
.wh-mode-switch { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.cart-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; margin-left: 6px;
  font-size: 12px; font-weight: 700;
  background: #DC2626; color: #fff;
  border-radius: 9px; padding: 0 5px;
}

/* ---- 购物车抽屉 ---- */
.cart-drawer :deep(.el-drawer__body) {
  padding: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden;
}
.cd-wrap { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.cd-header {
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 15px 20px;
  background: linear-gradient(135deg, #F7FAFF 0%, #EEF4FF 100%);
  border-bottom: 1px solid var(--c-divider);
}
.cd-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 700; }
.cd-count { font-size: 13px; font-weight: 600; color: var(--primary, #2563EB); }

.cd-mode-bar { flex-shrink: 0; padding: 10px 20px; border-bottom: 1px solid var(--c-divider); }
.cd-scan-bar { flex-shrink: 0; padding: 10px 20px; border-bottom: 1px solid var(--c-divider); }

.cd-body {
  flex: 1; min-height: 0; overflow-y: auto; padding: 12px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.cd-empty {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 60px 0; color: var(--c-text-mute);
}
.cd-empty p { margin: 0; font-size: 14px; }
.cd-empty-sub { font-size: 12px; }

.cd-list { display: flex; flex-direction: column; gap: 8px; }
.cd-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border: 1px solid var(--c-divider); border-radius: 8px;
  background: var(--c-bg);
}
.cd-row-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.cd-row-name { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cd-row-model { font-size: 12px; color: var(--c-text-mute); font-family: Consolas, monospace; }
.cd-row-qty { display: flex; align-items: center; gap: 6px; }
.cd-qty-num { font-weight: 700; font-size: 16px; min-width: 32px; text-align: center; }
.cd-qty-limit { font-size: 12px; color: var(--c-text-mute); }

.cd-footer {
  flex-shrink: 0;
  display: flex; flex-direction: column; gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--c-divider);
  background: var(--c-bg-soft, #f5f7fa);
}
.cd-form-row { display: flex; gap: 8px; }
.cd-submit-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
</style>