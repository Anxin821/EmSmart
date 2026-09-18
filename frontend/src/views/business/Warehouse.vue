<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title"><span class="emoji">📦</span></h1>

      <div class="ph-right-group">
        <el-input v-model="borrowKeyword" placeholder="扫码搜索物品，回车添加至借领/归还列表" clearable
          style="width: 320px;" @keyup.enter="onBorrowSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button v-if="userStore.canWrite('warehouse')" type="warning" @click="openBorrowDialog">
          <el-icon><ShoppingCart /></el-icon>
          借领/归还<span v-if="cartItems.length" class="cart-badge">{{ cartTotalQty }}</span>
        </el-button>
        <template v-if="userStore.canWrite('warehouse')">
          <el-button @click="openImport">批量导入</el-button>
          <el-button type="primary" @click="openEdit(null)">新增物品</el-button>
        </template>
      </div>
    </div>

    <div class="page-content wh-content">
      <div class="wh-tabs-row">
        <el-tabs v-model="activeTab" @tab-change="onTabChange" class="wh-tabs">
          <el-tab-pane label="首页" name="首页" />
          <el-tab-pane label="治具" name="治具" />
          <el-tab-pane label="耗材" name="耗材" />
          <el-tab-pane label="出入库记录" name="出入库记录" />
        </el-tabs>
      </div>

      <!-- 主区域：Tab 切换 -->
      <div class="wh-main">
        <!-- ── 出入库记录 Tab ── -->
        <template v-if="activeTab === '出入库记录'">
          <div class="wh-table-section">
            <div class="wh-table-wrap">
              <el-table :data="filteredTxRecords" v-loading="txLoading" stripe border size="small" empty-text="暂无记录"
  :header-cell-style="{ fontWeight: 600, textAlign: 'center' }" height="100%"
  :row-class-name="tableRowClassName">
                <el-table-column label="时间" width="140" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-date-picker v-model="txFilterTimeRange" type="daterange" range-separator="至"
                        start-placeholder="开始" end-placeholder="结束" size="small" style="width:100%;"
                        clearable @change="txPage=1;loadTxData()" />
                    </div>
                    <span v-else>{{ row.created_at }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="65" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-dropdown trigger="click" @command="v => { txFilterType=v; txPage=1; loadTxData() }">
                        <span class="tx-filter-trigger">{{ txFilterType || '全部' }}</span>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item command="">全部</el-dropdown-item>
                            <el-dropdown-item command="借出">借出</el-dropdown-item>
                            <el-dropdown-item command="归还">归还</el-dropdown-item>
                            <el-dropdown-item command="领用">领用</el-dropdown-item>
                            <el-dropdown-item command="补货">补货</el-dropdown-item>
                            <el-dropdown-item command="减少">减少</el-dropdown-item>
                            <el-dropdown-item command="维修">维修</el-dropdown-item>
                            <el-dropdown-item command="丢失">丢失</el-dropdown-item>
                            <el-dropdown-item command="损坏">损坏</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                    <el-tag v-else-if="(row.tx_type === '借出' || row.tx_type === '领用') && row.return_time" type="success" size="small">归还</el-tag>
                    <el-tag v-else :type="txTagType(row.tx_type)" size="small">{{ row.tx_type }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="物品" prop="part_name" min-width="140" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-input v-model="txFilterPart" size="small" placeholder="搜索" clearable
                        @change="txPage=1;loadTxData()" />
                    </div>
                    <span v-else-if="row.part_type === '治具' && row.model">{{ txPartDisplay(row) }}</span>
                    <span v-else>{{ row.part_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="数量" width="50" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <span class="part-sort-btn" :class="{ active: !!txSortOrder }"
                        :data-order="txSortOrder || 'off'"
                        @click.stop="toggleTxSort(txSortOrder)">
                        {{ txSortOrder === 'asc' ? '↑' : txSortOrder === 'desc' ? '↓' : '⇅' }}
                      </span>
                    </div>
                    <span v-else>{{ row.qty }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="借/领人" width="85" align="center" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-input v-model="txFilterOperator" size="small" placeholder="搜索" clearable
                        @change="txPage=1;loadTxData()" />
                    </div>
                    <span v-else>{{ row.operator }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="部门负责人" width="85" align="center" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-input v-model="txFilterDepartmentManager" size="small" placeholder="搜索" clearable
                        @change="txPage=1;loadTxData()" />
                    </div>
                    <span v-else>{{ row.department_manager || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="线体" width="70" align="center" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-dropdown popper-class="tx-line-popper" trigger="click" @command="v => { txFilterLine=v; txPage=1; loadTxData() }">
                        <span class="tx-filter-trigger">{{ txFilterLine || '全部' }}</span>
                        <template #dropdown>
                          <el-dropdown-menu class="tx-line-menu">
                            <el-dropdown-item command="">全部</el-dropdown-item>
                            <el-dropdown-item v-for="l in lines" :key="l" :command="l">{{ l }}</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                    <span v-else>{{ row.line || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="借出时间" width="135" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-date-picker v-model="txFilterBorrowDate" type="date" placeholder="筛选日期" size="small"
                        style="width:100%;" clearable @change="txPage=1;loadTxData()" />
                    </div>
                    <span v-else>{{ row.borrow_time || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="归还时间" width="135" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-date-picker v-model="txFilterReturnDate" type="date" placeholder="筛选日期" size="small"
                        style="width:100%;" clearable @change="txPage=1;loadTxData()" />
                    </div>
                    <span v-else>{{ row.return_time || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="备注" min-width="60" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-input v-model="txFilterRemark" size="small" placeholder="搜索" clearable
                        @change="txPage=1;loadTxData()" />
                    </div>
                    <div v-else class="tx-remark-cell" @click.stop="userStore.canWrite('warehouse') && openEditRemark(row)">
                      <span>{{ row.remark || '-' }}</span>
                      <el-icon v-if="userStore.canWrite('warehouse')" class="tx-remark-edit"><EditPen /></el-icon>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <CommonPagination v-model:page="txPage" v-model:page-size="txPageSize" :total="txTotal" compact />
          </div>
        </template>

        <!-- ── 首页 Tab：看板仪表盘 ── -->
        <template v-else-if="activeTab === '首页'">
  <div v-if="statsLoading" class="wh-dashboard-skeleton">
    <div class="sk-kpi-row">
      <div v-for="i in 5" :key="i" class="sk-card">
        <div class="sk-card-line sk-w40"></div>
        <div class="sk-card-line sk-w60 sk-h32"></div>
        <div class="sk-card-line sk-w30"></div>
      </div>
    </div>
    <div class="sk-body">
      <div class="sk-panel sk-panel-wide">
        <div class="sk-panel-head"><div class="sk-line sk-w30"></div></div>
        <div v-for="i in 4" :key="'o'+i" class="sk-row"><div class="sk-line sk-w70"></div></div>
      </div>
      <div class="sk-panel-stack">
        <div v-for="s in 3" :key="'p'+s" class="sk-panel">
          <div class="sk-panel-head"><div class="sk-line sk-w40"></div></div>
          <div v-for="j in 2" :key="'pp'+j" class="sk-row"><div class="sk-line sk-w55"></div></div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="wh-dashboard">
    <!-- ── 5 张 KPI 卡片 ── -->
    <div class="kpi-row">
      <div class="kpi-card kpi-card--danger" @click="onKpiClick('overdue')">
        <div class="kpi-head">
          <span class="kpi-icon"><el-icon><Timer /></el-icon></span>
          <span class="kpi-label">超期未还</span>
        </div>
        <div class="kpi-value">{{ sd.overdue_count || 0 }}</div>
        <div class="kpi-sub">{{ kpiSub(sd.overdue_count, '一切正常') }}</div>
      </div>

      <div class="kpi-card kpi-card--warning" @click="onKpiClick('lowstock')">
        <div class="kpi-head">
          <span class="kpi-icon"><el-icon><Box /></el-icon></span>
          <span class="kpi-label">低库存</span>
        </div>
        <div class="kpi-value">{{ sd.low_stock || 0 }}</div>
        <div class="kpi-sub">{{ kpiSub(sd.low_stock, '库存充足') }}</div>
      </div>

      <div class="kpi-card kpi-card--repair" @click="onKpiClick('repair')">
        <div class="kpi-head">
          <span class="kpi-icon"><el-icon><Tools /></el-icon></span>
          <span class="kpi-label">维修</span>
        </div>
        <div class="kpi-value">{{ sd.repair_count || 0 }}</div>
        <div class="kpi-sub">{{ kpiSub(sd.repair_count, '无维修') }}</div>
      </div>

      <div class="kpi-card kpi-card--lost" @click="onKpiClick('lost')">
        <div class="kpi-head">
          <span class="kpi-icon"><el-icon><Search /></el-icon></span>
          <span class="kpi-label">丢失</span>
        </div>
        <div class="kpi-value">{{ sd.lost_count || 0 }}</div>
        <div class="kpi-sub">{{ kpiSub(sd.lost_count, '无丢失') }}</div>
      </div>

      <div class="kpi-card kpi-card--damaged" @click="onKpiClick('damaged')">
        <div class="kpi-head">
          <span class="kpi-icon"><el-icon><Warning /></el-icon></span>
          <span class="kpi-label">损坏</span>
        </div>
        <div class="kpi-value">{{ sd.damaged_count || 0 }}</div>
        <div class="kpi-sub">{{ kpiSub(sd.damaged_count, '无损坏') }}</div>
      </div>
    </div>

    <!-- ── 主体：左大右小 ── -->
    <div class="wh-dashboard-body">
      <!-- 左侧：超期未还 -->
      <div class="panel panel--overdue">
                <div class="panel-head">

          <span class="panel-title">借出超期未还</span>
        </div>

        <div v-if="!sd.overdue_items?.length" class="panel-empty panel-empty--good">
          <span class="empty-emoji">🎉</span>
          <span>暂无超期，一切正常</span>
        </div>

        <div v-else class="overdue-list">
          <div
            v-for="it in sd.overdue_items?.slice(0, 20)"
            :key="it.id"
            class="overdue-row"
            :class="{ 'is-critical': it.overdue_days > 7 }">
            <div class="od-days">
              <b>{{ it.overdue_days }}</b>
              <span>天</span>
            </div>
            <div class="od-info">
              <div class="od-title">
                <span class="od-name">{{ it.name }}</span>
                <span class="od-model" v-if="it.model">{{ it.model }}</span>
              </div>
              <div class="od-meta">
                <span class="od-meta-item">
                  <el-icon><User /></el-icon>{{ it.borrower || '-' }}
                </span>
                <span class="od-sep">·</span>
                <span class="od-meta-item">
                  <el-icon><Location /></el-icon>{{ it.line || '-' }}
                </span>
              </div>
            </div>
            <div class="od-actions">
              <el-button size="small" plain @click.stop="remindBorrower(it)">催还</el-button>
              <el-button size="small" type="warning" @click.stop="openReturn(it)">归还</el-button>
            </div>
          </div>

          <div v-if="sd.overdue_items?.length > 20" class="overdue-more">
            <el-button text type="primary" size="small" @click="onKpiClick('overdue')">
              查看全部（{{ sd.overdue_items.length }} 条）
            </el-button>
          </div>
        </div>
      </div>

            <!-- 右侧：三个堆叠面板 -->
                  <!-- 右侧：待处理卡片 -->
      <div class="pending-card">
        <div class="pending-head">
          <span class="pending-title">待处理</span>
        </div>

        <div
          v-if="sd.low_stock_items?.length || pendingMixedItems.length"
          class="pending-body"
        >
          <!-- 低库存（保留明细，因为有"补货"操作） -->
          <div v-if="sd.low_stock_items?.length" class="pending-section">
            <div class="ps-row">
              <span class="ps-dot" style="background: #D97706"></span>
              <span class="ps-label">低库存</span>
              <span class="ps-count">{{ sd.low_stock || 0 }}</span>
            </div>
            <div class="ps-list">
              <div v-for="it in sd.low_stock_items" :key="it.id" class="mini-row">
                <span class="mini-name">{{ it.name }}</span>
                <span class="mini-num">{{ it.stock_qty }}/{{ it.warn_qty }}{{ it.unit }}</span>
                <el-button size="small" plain @click.stop="openRestock(it)">补货</el-button>
              </div>
            </div>
          </div>

          <!-- 维修 / 丢失 / 损坏：混排列表 -->
          <div v-if="pendingMixedItems.length" class="pending-mixed">
            <div
              v-for="it in pendingMixedItems"
              :key="it._type + '-' + it.id"
              class="pending-mixed-row"
            >
              <span class="mini-tag" :class="'mini-tag--' + it._type">{{ it._label }}</span>
              <span class="mini-name">{{ it.name }}</span>
              <span v-if="it.current_borrower || it.borrower" class="mini-info">
                {{ it.current_borrower || it.borrower }}
              </span>
              <span v-if="it.borrow_time || it.borrow_time" class="mini-time">
                {{ (it.borrow_time || '').slice(0, 10) }}
              </span>
              <el-button size="small" plain @click.stop="onPendingAction(it)">
                {{ it._actionText }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 全部为空 -->
        <div v-if="!sd.overdue_items?.length" class="panel-empty panel-empty--good">
          <span class="empty-emoji">🎉</span>
          <span>暂无待办</span>
        </div>
      </div>
    </div>
  </div>
</template>

        <!-- ── 治具 / 耗材 Tab：物品列表 ── -->
        <template v-else>
          <div class="wh-table-section">
            <!-- 筛选行已嵌入表格内部第一行 -->
            <div class="wh-table-wrap">
              <el-table
                :data="items"
                v-loading="loading"
                stripe
                border
                style="width: 100%"
                empty-text="暂无数据"
                :header-cell-style="{ fontWeight: 600, textAlign: 'center' }"
                @row-click="onTableRowClick"
                :row-class-name="tableRowClassName"
                >
                <el-table-column label="物品名称" min-width="180" align="center" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div v-if="row._isFilter && activeTab === '治具'" class="jig-fbr-cell">
                      <el-input v-model="jigFilterName" size="small" placeholder="搜索名称" clearable
                        @change="page=1;loadData()" />
                    </div>
                    <div v-else-if="row._isFilter && activeTab === '耗材'" class="jig-fbr-cell">
                      <el-input v-model="consFilterName" size="small" placeholder="搜索名称" clearable
                        @change="page=1;loadData()" />
                    </div>
                    <span v-else class="wh-name">{{ row.name }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="型号" prop="model" min-width="130" align="center" show-overflow-tooltip
                  v-if="activeTab !== '耗材'">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-input v-model="jigFilterModel" size="small" placeholder="搜索型号" clearable
                        @change="page=1;loadData()" />
                    </div>
                    <span v-else-if="row.model" class="wh-model">{{ row.model }}</span>
                    <span v-else class="wh-model-empty">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="编号" prop="code" min-width="130" align="center" show-overflow-tooltip
                  v-if="activeTab !== '耗材'">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-input v-model="jigFilterCode" size="small" placeholder="搜索编号" clearable
                        @change="page=1;loadData()" />
                    </div>
                    <span v-else-if="row.code" class="wh-model">{{ row.code }}</span>
                    <span v-else class="wh-model-empty">-</span>
                  </template>
                </el-table-column>

                <template v-if="activeTab === '治具'">
                  <el-table-column label="总数" prop="total_qty" width="70" align="center">
                    <template #default="{ row }">
                      <div v-if="row._isFilter" class="jig-fbr-cell">
                        <span class="part-sort-btn" :class="{ active: !!jigSortTotal }"
                          :data-order="jigSortTotal || 'off'"
                          @click.stop="togglePartSort('jigSortTotal')">
                          {{ jigSortTotal === 'asc' ? '↑' : jigSortTotal === 'desc' ? '↓' : '⇅' }}
                        </span>
                      </div>
                      <span v-else>{{ row.total_qty }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="可用" width="70" align="center">
                    <template #default="{ row }">
                      <div v-if="row._isFilter" class="jig-fbr-cell">
                        <span class="part-sort-btn" :class="{ active: !!jigSortAvailable }"
                          :data-order="jigSortAvailable || 'off'"
                          @click.stop="togglePartSort('jigSortAvailable')">
                          {{ jigSortAvailable === 'asc' ? '↑' : jigSortAvailable === 'desc' ? '↓' : '⇅' }}
                        </span>
                      </div>
                      <b v-else class="ok-text">{{ row.available_qty }}</b>
                    </template>
                  </el-table-column>
                </template>

                <template v-else>
                  <el-table-column label="库存" width="100" align="center">
                    <template #default="{ row }">
                      <div v-if="row._isFilter" class="jig-fbr-cell">
                        <span class="part-sort-btn" :class="{ active: !!consSortStock }"
                          :data-order="consSortStock || 'off'"
                          @click.stop="togglePartSort('consSortStock')">
                          {{ consSortStock === 'asc' ? '↑' : consSortStock === 'desc' ? '↓' : '⇅' }}
                        </span>
                      </div>
                      <b v-else :style="{ color: row.status === '缺货' ? '#DC2626' : 'var(--c-text)' }">{{ row.stock_qty }}</b>
                      <span v-if="!row._isFilter" style="font-size:12px;color:var(--c-text-mute)"> {{ row.unit }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="预警值" prop="warn_qty" width="80" align="center">
                    <template #default="{ row }">
                      <div v-if="row._isFilter" class="jig-fbr-cell">
                        <span class="part-sort-btn" :class="{ active: !!consSortWarn }"
                          :data-order="consSortWarn || 'off'"
                          @click.stop="togglePartSort('consSortWarn')">
                          {{ consSortWarn === 'asc' ? '↑' : consSortWarn === 'desc' ? '↓' : '⇅' }}
                        </span>
                      </div>
                      <span v-else>{{ row.warn_qty }}</span>
                    </template>
                  </el-table-column>
                </template>

                <el-table-column label="货位" prop="location" width="120" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter && activeTab === '治具'" class="jig-fbr-cell">
                      <el-input v-model="jigFilterLocation" size="small" placeholder="搜索货位" clearable
                        @change="page=1;loadData()" />
                    </div>
                    <div v-else-if="row._isFilter && activeTab === '耗材'" class="jig-fbr-cell">
                      <el-input v-model="consFilterLocation" size="small" placeholder="搜索货位" clearable
                        @change="page=1;loadData()" />
                    </div>
                    <span v-else-if="row.location" class="loc-tags">
                      <el-tag size="small" class="loc-tag">{{ row.location.split(/[,，、]/)[0].trim() }}</el-tag>
                      <el-popover v-if="row.location.split(/[,，、]/).length > 1" placement="bottom" trigger="click" :width="200">
                        <template #reference>
                          <span class="loc-more">+{{ row.location.split(/[,，、]/).length - 1 }}</span>
                        </template>
                        <div class="loc-tags" style="padding:4px 0;">
                          <el-tag v-for="loc in row.location.split(/[,，、]/).map(s=>s.trim()).filter(Boolean).slice(1)"
                            :key="loc" size="small" class="loc-tag" style="margin:2px;">{{ loc }}</el-tag>
                        </div>
                      </el-popover>
                    </span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>

                <el-table-column label="状态" min-width="80" align="center">
                  <template #default="{ row }">
                    <div v-if="row._isFilter && activeTab === '治具'" class="jig-fbr-cell">
                      <el-dropdown trigger="click" @command="v => { jigFilterStatus=v; page=1; loadData() }">
                        <span class="tx-filter-trigger">{{ jigFilterStatus || '全部' }}</span>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item command="">全部</el-dropdown-item>
                            <el-dropdown-item command="在库">在库</el-dropdown-item>
                            <el-dropdown-item command="借出">借出</el-dropdown-item>
                            <el-dropdown-item command="维修">维修</el-dropdown-item>
                            <el-dropdown-item command="报损">报损</el-dropdown-item>
                            <el-dropdown-item command="报失">报失</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                    <div v-else-if="row._isFilter && activeTab === '耗材'" class="jig-fbr-cell">
                      <el-dropdown trigger="click" @command="v => { consFilterStatus=v; page=1; loadData() }">
                        <span class="tx-filter-trigger">{{ consFilterStatus || '全部' }}</span>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item command="">全部</el-dropdown-item>
                            <el-dropdown-item command="正常">正常</el-dropdown-item>
                            <el-dropdown-item command="预警">预警</el-dropdown-item>
                            <el-dropdown-item command="缺货">缺货</el-dropdown-item>
                            <el-dropdown-item command="维修">维修</el-dropdown-item>
                            <el-dropdown-item command="报损">报损</el-dropdown-item>
                            <el-dropdown-item command="报失">报失</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </div>
                    <el-tag v-else :type="statusTagType(row)" size="small">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>

                <el-table-column label="操作" width="210" align="center" fixed="right">
                  <template #default="{ row }">
                    <div v-if="row._isFilter" class="jig-fbr-cell">
                      <el-button size="small"
                        @click.stop="activeTab === '治具' ? resetJigFilters() : resetConsFilters()">重置</el-button>
                    </div>
                    <template v-else>
                      <template v-if="userStore.canWrite('warehouse')">
                        <template v-if="row.part_type === '治具'">
                          <el-button v-if="row.available_qty - (row.repair_qty || 0) > 0"
                            type="primary" link size="small" @click.stop="openBorrow(row)">借领</el-button>
                          <el-button v-else type="info" link size="small" disabled @click.stop="toast.warn(`「${row.name}」可借数量不足`)">借领</el-button>
                          <el-button v-if="row.status === '借出'" type="warning" link size="small"
                            @click.stop="openReturn(row)">归还</el-button>
                          <el-button v-else type="info" link size="small" disabled>归还</el-button>
                        </template>
                        <template v-else>
                          <el-button v-if="row.stock_qty > 0"
                            type="primary" link size="small" @click.stop="openConsume(row)">借领</el-button>
                          <el-button v-else type="info" link size="small" disabled @click.stop="toast.warn(`「${row.name}」库存不足`)">借领</el-button>
                          <el-button type="warning" link size="small" @click.stop="openReturn(row)">归还</el-button>
                        </template>
                        <el-dropdown @command="(cmd) => handleMoreCommand(cmd, row)" trigger="click">
                          <el-button type="info" link size="small" @click.stop>更多<el-icon style="margin-left:2px"><ArrowDown /></el-icon></el-button>
                          <template #dropdown>
                            <el-dropdown-menu>
                              <el-dropdown-item command="restock">补货</el-dropdown-item>
                              <el-dropdown-item v-if="row.part_type === '治具' && row.repair_qty > 0" command="finish_repair">已维修</el-dropdown-item>
                              <el-dropdown-item v-if="row.part_type === '治具' && row.status === '借出'" command="loss">报失</el-dropdown-item>
                              <el-dropdown-item v-if="row.part_type === '治具' && row.status === '借出'" command="damaged">报损</el-dropdown-item>
                              <el-dropdown-item v-if="row.part_type === '治具' && row.status === '借出'" command="found_back">已找回</el-dropdown-item>
                              <el-dropdown-item v-if="row.part_type === '治具' && row.status === '借出'" command="repair_damaged">已修复</el-dropdown-item>
                              <el-dropdown-item command="edit">编辑</el-dropdown-item>
                              <el-dropdown-item v-if="userStore.canWrite('warehouse')" command="delete">删除</el-dropdown-item>
                            </el-dropdown-menu>
                          </template>
                        </el-dropdown>
                      </template>
                      <span v-else style="color: var(--c-text-mute); font-size: 12px;">点击行查看详情</span>
                    </template>
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
        </template>
      </div>
    </div>

    <!-- 借领 / 归还 弹框 -->
    <el-dialog v-model="cartDialog" :title="scanModeName" width="1000px" destroy-on-close
  :close-on-click-modal="false" @opened="focusScanInput" class="cart-dialog"
  modal-class="cart-modal">
      <div class="cd-wrap">
        <div class="cd-mode-bar">
  <div class="cd-mode-switch">
    <button
      type="button"
      class="cd-mode-btn cd-mode-borrow"
      :class="{ active: scanMode === 'borrow' }"
      @click="scanMode = 'borrow'"
    >
      <span class="bi bi-box-arrow-up-right"></span>
      <span class="cd-mode-label">借领</span>
    </button>
    <button
      type="button"
      class="cd-mode-btn cd-mode-return"
      :class="{ active: scanMode === 'return' }"
      @click="scanMode = 'return'"
    >
      <span class="bi bi-box-arrow-in-down"></span>
      <span class="cd-mode-label">归还</span>
    </button>
  </div>
</div>

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
  <span v-if="item.part_type === '耗材'" class="cd-row-tag">耗材</span>
  <span v-else class="cd-row-model">{{ item.model || '-' }}</span>
</div>
              <template v-if="scanMode === 'return'">
                <div class="cd-return-records" v-if="item.activeRecords?.length">
                  <div v-for="rec in item.activeRecords" :key="rec.id"
                    class="cd-return-rec"
                    :class="{ active: item.selectedRecordId === rec.id }"
                    @click="item.selectedRecordId = rec.id">
                    <span class="cd-rec-operator">{{ rec.operator || '未知' }}</span>
                    <span class="cd-rec-line" v-if="rec.line">【{{ rec.line }}】</span>
                    <span class="cd-rec-time">{{ formatTime(rec.borrow_time) }}</span>
                    <span class="cd-rec-actions">
  <el-button size="small" class="cd-rec-btn cd-rec-btn--repair"  @click.stop="cartAction('repair', item, rec)">维修</el-button>
  <el-button size="small" class="cd-rec-btn cd-rec-btn--loss"    @click.stop="cartAction('loss', item, rec)">报失</el-button>
  <el-button size="small" class="cd-rec-btn cd-rec-btn--damaged" @click.stop="cartAction('damaged', item, rec)">报损</el-button>
</span>
                  </div>
                </div>
                <div v-else-if="item.loadingRecords" class="cd-rec-loading">加载中…</div>
                <div v-else class="cd-rec-empty">无活跃记录</div>
              </template>
              <template v-else>
                <div class="cd-row-qty">
                  <el-button circle @click="changeQty(item, -1)"><el-icon><Minus /></el-icon></el-button>
                  <span class="cd-qty-num">{{ item.qty }}</span>
                  <el-button circle @click="changeQty(item, 1)" :disabled="item.qty >= item.maxQty">
                    <el-icon><Plus /></el-icon></el-button>
                  <span class="cd-qty-limit">/{{ item.maxQty }}</span>
                </div>
              </template>
              <el-button text type="danger" @click="removeFromCart(item.id)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <footer class="cd-footer">
  <!-- 第一行：借领人 / 部门负责人 / 线体（等宽平分） -->
  <div class="cd-form-row" v-if="scanMode !== 'return'">
    <el-select v-model="scanForm.operator" filterable allow-create clearable
      placeholder="借领人姓名" class="cd-field">
      <el-option v-for="o in operatorOptions" :key="o" :label="o" :value="o">
        <div class="mem-option">
          <span>{{ o }}</span>
          <el-button text size="small" class="mem-del-btn" @click.stop="deleteOperator(o)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </el-option>
    </el-select>
    <el-select v-model="scanForm.department_manager" filterable allow-create clearable
      placeholder="部门负责人" class="cd-field">
      <el-option v-for="d in departmentManagerOptions" :key="d" :label="d" :value="d">
        <div class="mem-option">
          <span>{{ d }}</span>
          <el-button text size="small" class="mem-del-btn" @click.stop="deleteDepartmentManager(d)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </el-option>
    </el-select>
    <el-select v-model="scanForm.line" clearable placeholder="线体" class="cd-field">
      <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
    </el-select>
  </div>
  <div v-else class="cd-return-hint">
    <el-icon><InfoFilled /></el-icon>
    <span>请在上方物品行中点击选中要归还的记录</span>
  </div>

  <!-- 第二行：备注 + 清空 + 提交 -->
  <div class="cd-submit-row">
    <el-input v-model="scanForm.remark" placeholder="备注（选填）" maxlength="255" class="cd-remark-input" />
    <el-button text type="danger" :disabled="!cartItems.length" @click="clearCart">清空</el-button>
    <el-button type="primary" size="large" :loading="scanSubmitting"
      :disabled="!cartItems.length" @click="submitBatch">
      <el-icon><Check /></el-icon>
      提交（{{ cartTotalQty }} 件）
    </el-button>
  </div>
</footer>
      </div>
    </el-dialog>

    <!-- 新增 / 编辑物品 -->
    <el-dialog v-model="editDialog" :title="editForm.id ? '编辑物品' : '新增物品'" width="560px" destroy-on-close :close-on-click-modal="true">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="92px">
        <el-form-item label="物品名称" prop="name" required>
          <el-input v-model="editForm.name" placeholder="如：测试治具A/高温胶带" maxlength="100" />
        </el-form-item>
        <el-form-item v-if="editForm.part_type !== '耗材'" label="型号">
          <el-input v-model="editForm.model" placeholder="设备型号" maxlength="100" />
        </el-form-item>
        <el-form-item v-if="editForm.part_type !== '耗材'" label="编号">
          <el-input v-model="editForm.code" placeholder="内部编号" maxlength="100" />
        </el-form-item>
        <el-form-item label="类型" prop="part_type" required>
          <el-radio-group v-model="editForm.part_type" :disabled="!!editForm.id">
            <el-radio value="治具">治具</el-radio>
            <el-radio value="耗材">耗材</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editForm.part_type === '治具'" label="总数">
          <template v-if="!editForm.id || userStore.isAdmin">
            <el-input-number v-model="editForm.total_qty" :min="0" :max="9999" controls-position="right" :disabled="!userStore.isAdmin" />
          </template>
          <span v-else class="wh-form-static">{{ editForm.total_qty }}</span>
          <span class="wh-form-hint">治具总数量</span>
          <span v-if="!userStore.isAdmin" class="wh-form-hint" style="color:var(--el-color-warning);margin-left:4px;">仅管理员可设置</span>
        </el-form-item>
        <template v-if="editForm.part_type === '耗材'">
          <el-form-item :label="editForm.id ? '库存数量' : '初始库存'">
            <template v-if="!editForm.id || userStore.isAdmin">
              <el-input-number v-model="editForm.total_qty" :min="0" :max="999999" controls-position="right" :disabled="!userStore.isAdmin" />
            </template>
            <span v-else class="wh-form-static">{{ editForm.total_qty }} {{ editForm.unit }}</span>
            <span v-if="!userStore.isAdmin" class="wh-form-hint" style="color:var(--el-color-warning);margin-left:4px;">仅管理员可设置</span>
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
          <el-select v-model="editLocationList" multiple filterable allow-create default-first-option
            placeholder="输入货位后回车添加" style="width:100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 治具借出 -->
    <el-dialog v-model="borrowDialog" title="治具借出" width="480px" destroy-on-close :close-on-click-modal="true">
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>可用数量：<b class="ok-text">{{ actionRow.available_qty - (actionRow.repair_qty || 0) }}</b> / {{ actionRow.total_qty }}</p>
      </div>
      <el-form :model="borrowForm" label-width="92px">
        <el-form-item label="领用人" required>
          <el-select v-model="borrowForm.operator" filterable allow-create clearable placeholder="借用人姓名" style="width:100%;">
            <el-option v-for="o in operatorOptions" :key="o" :label="o" :value="o">
              <div class="mem-option">
                <span>{{ o }}</span>
                <el-button text size="small" class="mem-del-btn" @click.stop="deleteOperator(o)">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="部门负责人">
          <el-select v-model="borrowForm.department_manager" filterable allow-create clearable placeholder="部门负责人姓名（选填）" style="width:100%;">
            <el-option v-for="d in departmentManagerOptions" :key="d" :label="d" :value="d">
              <div class="mem-option">
                <span>{{ d }}</span>
                <el-button text size="small" class="mem-del-btn" @click.stop="deleteDepartmentManager(d)">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="线体" required>
          <el-select v-model="borrowForm.line" placeholder="选择线体" style="width: 100%;">
            <el-option v-for="l in lines" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="borrowForm.qty" :min="1" :max="actionRow ? (actionRow.available_qty - (actionRow.repair_qty || 0)) : 1" controls-position="right" />
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

    <!-- 归还（治具按借出记录 / 耗材按领用记录） -->
    <el-dialog v-model="returnDialog" :title="(actionRow?.part_type === '耗材') ? '耗材归还' : '治具归还'"
               width="800px" destroy-on-close :close-on-click-modal="true" @open="loadBorrowRecords">
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p v-if="actionRow.part_type === '治具'">总 {{ actionRow.total_qty }} / 可用 <b class="ok-text">{{ actionRow.available_qty }}</b> / 外借 <b class="warn-text">{{ actionRow.total_qty - actionRow.available_qty }}</b></p>
        <p v-else>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : 'ok-text'">{{ actionRow.stock_qty }}</b></p>
      </div>
      <div v-loading="borrowRecordsLoading">
        <div v-if="!borrowRecords.length" class="tx-empty-tip">暂无记录</div>
        <el-table v-else :data="borrowRecords" border size="small" empty-text="暂无记录">
          <el-table-column :label="actionRow?.part_type === '耗材' ? '领用人' : '借用人'"
                           :prop="actionRow?.part_type === '耗材' ? 'operator' : 'borrower'" width="60" show-overflow-tooltip />
          <el-table-column label="部门负责人" :prop="actionRow?.part_type === '耗材' ? 'department_manager' : 'department_manager'" width="85" show-overflow-tooltip />
          <el-table-column label="线体" prop="line" width="60" align="center" />
          <el-table-column label="数量" prop="qty" width="60" align="center" />
          <el-table-column label="借出/领用时间" prop="borrow_time" width="140" align="center" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <!-- 耗材记录：根据 tx_type 和 return_time 显示状态 -->
              <el-tag v-if="row.tx_type" :type="
                row.return_time ? 'success' :
                row.tx_type === '维修' ? 'info' :
                row.tx_type === '丢失' ? 'danger' :
                row.tx_type === '损坏' ? 'danger' :
                'primary'
              " size="small">
                {{ row.return_time ? '归还' :
                   row.tx_type === '维修' ? '维修中' :
                   row.tx_type === '丢失' ? '已丢失' :
                   row.tx_type === '损坏' ? '已损坏' : '已领用' }}
              </el-tag>
              <!-- 治具记录：status -->
              <el-tag v-else :type="row.status === '借出' ? 'warning' : row.status === '维修' ? 'info' : row.status === '丢失' ? 'danger' : row.status === '损坏' ? 'danger' : 'success'" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" align="center">
            <template #default="{ row }">
              <template v-if="actionRow?.part_type === '耗材'">
                <!-- 耗材：根据 tx_type 显示不同操作 -->
                <template v-if="!row.return_time && row.tx_type === '领用'">
                  <el-button type="warning" link size="small" @click="submitReturn(row)">归还</el-button>
                  <el-button type="danger" link size="small" @click="submitToRepair(row)">转维修</el-button>
                  <el-button type="info" link size="small" @click="submitLoss(row)">报失</el-button>
                  <el-button type="danger" link size="small" @click="submitDamaged(row)">报损</el-button>
                </template>
                <el-button v-else-if="!row.return_time && row.tx_type === '维修'" type="warning" link size="small" @click="openFinishRepair(row)">已维修</el-button>
                <el-button v-else-if="!row.return_time && row.tx_type === '丢失'" type="success" link size="small" @click="submitFoundBack(row)">已找回</el-button>
                <el-button v-else-if="!row.return_time && row.tx_type === '损坏'" type="success" link size="small" @click="submitRepairDamaged(row)">已修复</el-button>
                <span v-else style="color: var(--c-text-mute); font-size: 12px;">已处理</span>
              </template>
              <template v-else>
                <!-- 治具：根据不同状态显示不同操作 -->
                <template v-if="row.status === '借出'">
                  <el-button type="warning" link size="small" @click="submitReturn(row)">归还</el-button>
                  <el-button type="danger" link size="small" @click="submitToRepair(row)">转维修</el-button>
                  <el-button type="info" link size="small" @click="submitLoss(row)">报失</el-button>
                  <el-button type="danger" link size="small" @click="submitDamaged(row)">报损</el-button>
                </template>
                <el-button v-else-if="row.status === '维修'" type="warning" link size="small" @click="openFinishRepair(row)">已维修</el-button>
                <el-button v-else-if="row.status === '丢失'" type="success" link size="small" @click="submitFoundBack(row)">已找回</el-button>
                <el-button v-else-if="row.status === '损坏'" type="success" link size="small" @click="submitRepairDamaged(row)">已修复</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="returnDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 耗材领用 -->
    <el-dialog v-model="consumeDialog" title="耗材领用" width="480px" destroy-on-close :close-on-click-modal="true">
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无编号' }}）</p>
        <p>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : 'ok-text'">
          {{ actionRow.stock_qty }}</b> {{ actionRow.unit }}　预警值：{{ actionRow.warn_qty }}
        </p>
      </div>
      <el-form :model="consumeForm" label-width="92px">
        <el-form-item label="领用人" required>
          <el-select v-model="consumeForm.operator" filterable allow-create clearable placeholder="领用人姓名" style="width:100%;">
            <el-option v-for="o in operatorOptions" :key="o" :label="o" :value="o">
              <div class="mem-option">
                <span>{{ o }}</span>
                <el-button text size="small" class="mem-del-btn" @click.stop="deleteOperator(o)">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="部门负责人">
          <el-select v-model="consumeForm.department_manager" filterable allow-create clearable placeholder="部门负责人姓名（选填）" style="width:100%;">
            <el-option v-for="d in departmentManagerOptions" :key="d" :label="d" :value="d">
              <div class="mem-option">
                <span>{{ d }}</span>
                <el-button text size="small" class="mem-del-btn" @click.stop="deleteDepartmentManager(d)">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </el-option>
          </el-select>
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
    <el-dialog v-model="restockDialog" :title="(actionRow?.part_type === '治具' ? '治具' : '耗材') + '补货'" width="480px" destroy-on-close :close-on-click-modal="true">
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '-' }}）</p>
        <template v-if="actionRow.part_type === '耗材'">
          <p>当前库存：<b :class="actionRow.stock_qty <= actionRow.warn_qty ? 'danger-text' : ''">
            {{ actionRow.stock_qty }}</b> {{ actionRow.unit }}　预警值：{{ actionRow.warn_qty }}
          </p>
        </template>
        <template v-else>
          <p>总 {{ actionRow.total_qty }} / 可用 <b class="ok-text">{{ actionRow.available_qty }}</b> / 外借 <b class="warn-text">{{ actionRow.total_qty - actionRow.available_qty }}</b></p>
        </template>
      </div>
      <el-form :model="restockForm" label-width="92px">
        <el-form-item label="补货数量" required>
          <el-input-number v-model="restockForm.qty" :min="1" :max="999999" controls-position="right" />
          <span class="wh-form-hint" v-if="actionRow?.unit">{{ actionRow.unit }}</span>
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

    <!-- 已维修 -->
    <el-dialog v-model="finishRepairDialog" title="已维修" width="420px" destroy-on-close :close-on-click-modal="true">
      <div class="wh-action-info" v-if="actionRow">
        <p><b>{{ actionRow.name }}</b>（{{ actionRow.model || '无型号' }}）</p>
        <p>当前维修中数量：<b class="danger-text">{{ actionRow.repair_qty || 0 }}</b></p>
      </div>
      <el-form :model="finishRepairForm" label-width="92px">
        <el-form-item label="完成数量" required>
          <el-input-number v-model="finishRepairForm.qty" :min="1" :max="actionRow?.repair_qty || 1" controls-position="right" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="finishRepairForm.remark" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="finishRepairDialog = false">取消</el-button>
        <el-button type="success" :loading="actionLoading" @click="submitFinishRepair">确认完成</el-button>
      </template>
    </el-dialog>

    <!-- 编辑备注 -->
    <el-dialog v-model="remarkDialog" title="编辑备注" width="420px" destroy-on-close :close-on-click-modal="true">
      <div class="wh-action-info" v-if="remarkRow">
        <p>{{ remarkRow.part_name }} - {{ remarkRow.tx_type }} {{ remarkRow.qty }}</p>
        <p>借/领人：{{ remarkRow.operator || '-' }}</p>
      </div>
      <el-input v-model="remarkEditing" type="textarea" :rows="3" maxlength="255" placeholder="输入备注内容" />
      <template #footer>
        <el-button @click="remarkDialog = false">取消</el-button>
        <el-button type="primary" :loading="remarkSaving" @click="submitRemark">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importDialog" title="📥 批量导入物品" width="560px" destroy-on-close :close-on-click-modal="true">
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
          <div class="el-upload__tip wh-import-tip">
            <span>支持 .xlsx / .xls；表头列：<b>物品名称、型号、编号、类型、数量、货位、单位、预警值</b></span>
            <el-link type="primary" :underline="false" @click.stop="downloadTemplate">下载模板</el-link>
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
    <el-dialog v-model="detailDialog" title="物品详情" width="640px" destroy-on-close :close-on-click-modal="true">
      <div v-if="detail" class="wh-detail">
        <div class="wh-detail-head">
          <span class="wh-detail-name">{{ detail.part.name }}</span>
          <el-tag :type="statusTagType(detail.part)" size="small">{{ detail.part.status }}</el-tag>
        </div>

        <el-descriptions :column="2" border size="small" class="wh-desc">
          <el-descriptions-item label="类型">{{ detail.part.part_type }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.part.part_type !== '耗材'" label="型号">{{ detail.part.model || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.part.part_type !== '耗材'" label="编号">{{ detail.part.code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="货位">
            <span v-if="detail.part.location" class="loc-tags">
              <el-tag v-for="loc in detail.part.location.split(/[,，、]/).map(s=>s.trim()).filter(Boolean)" :key="loc"
                size="small" class="loc-tag">{{ loc }}</el-tag>
            </span>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="数量">{{ detail.part.qty_text }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.part.part_type === '治具'" label="维修中">
            <el-tag :type="detail.part.repair_qty > 0 ? 'danger' : 'success'" size="small">
              {{ detail.part.repair_qty > 0 ? `${detail.part.repair_qty} 件维修中` : '正常' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 治具当前借出记录 -->
        <div v-if="detail.part.part_type === '治具' && detail.borrow_records?.length" class="wh-detail-block">
          <div class="wh-detail-subtitle">📌 当前借出记录</div>
          <el-table :data="detail.borrow_records" size="small" border empty-text="暂无">
            <el-table-column label="借用人" prop="borrower" width="90" show-overflow-tooltip />
            <el-table-column label="部门负责人" prop="department_manager" width="100" show-overflow-tooltip />
            <el-table-column label="线体" prop="line" width="70" align="center" />
            <el-table-column label="数量" prop="qty" width="60" align="center" />
            <el-table-column label="借出时间" prop="borrow_time" width="145" align="center" />
          </el-table>
        </div>

        <!-- 耗材低库存提示 -->
        <div v-if="detail.part.part_type === '耗材' && detail.part.stock_qty <= detail.part.warn_qty" class="wh-low-tip">
          <span class="bi bi-exclamation-triangle-fill"></span>
          库存预警：当前剩余 {{ detail.part.stock_qty }} {{ detail.part.unit }}，已低于预警值 {{ detail.part.warn_qty }}，请及时补货！
        </div>

        <!-- 最近操作记录 -->
        <div class="wh-detail-block">
          <div class="wh-detail-subtitle">最近出入库记录</div>
          <el-table :data="detail.transactions" size="small" border empty-text="暂无记录">
            <el-table-column label="时间" prop="created_at" width="150" />
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.return_time" type="success" size="small">归还</el-tag>
                <el-tag v-else :type="txTagType(row.tx_type)" size="small">{{ row.tx_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数量" prop="qty" width="60" align="center" />
            <el-table-column label="借/领人" prop="operator" width="90" show-overflow-tooltip />
            <el-table-column label="备注" prop="remark" min-width="100" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { warehouseApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { useNotify } from '@/composables/useNotify'
import CommonPagination from '@/components/common/CommonPagination.vue'
import {
  Search, Plus, Minus, Close, Check, EditPen, ArrowDown,
  InfoFilled, ShoppingCart, UploadFilled,
  Timer, Box, Tools, Warning, User, Location,
} from '@element-plus/icons-vue'

const userStore = useUserStore()
const { toast, confirmDelete } = useNotify()

const lines = ['1线', '2线', '3线', '4线', '5线', '6线', '7线', '8线', '9线', '工程', '品质', '维修', '解析']
const operatorOptions = ref([])
const departmentManagerOptions = ref([])
const HIDDEN_OP_KEY = 'wh_hidden_operators'
const HIDDEN_DM_KEY = 'wh_hidden_department_managers'
const loadOperators = async () => {
  try {
    const raw = (await warehouseApi.operators()).data || []
    const hidden = new Set(JSON.parse(localStorage.getItem(HIDDEN_OP_KEY) || '[]'))
    operatorOptions.value = raw.filter(o => !hidden.has(o))
  } catch { /* 静默 */ }
}
const loadDepartmentManagers = async () => {
  try {
    const raw = (await warehouseApi.departmentManagers()).data || []
    const hidden = new Set(JSON.parse(localStorage.getItem(HIDDEN_DM_KEY) || '[]'))
    departmentManagerOptions.value = raw.filter(d => !hidden.has(d))
  } catch { /* 静默 */ }
}
const deleteOperator = (name) => {
  const s = new Set(JSON.parse(localStorage.getItem(HIDDEN_OP_KEY) || '[]'))
  s.add(name)
  localStorage.setItem(HIDDEN_OP_KEY, JSON.stringify([...s]))
  operatorOptions.value = operatorOptions.value.filter(o => o !== name)
}
const deleteDepartmentManager = (name) => {
  const s = new Set(JSON.parse(localStorage.getItem(HIDDEN_DM_KEY) || '[]'))
  s.add(name)
  localStorage.setItem(HIDDEN_DM_KEY, JSON.stringify([...s]))
  departmentManagerOptions.value = departmentManagerOptions.value.filter(d => d !== name)
}

// ---------------- 列表 ----------------
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
/** 筛选行虚拟对象，避免重复创建 */
const FILTER_ROW = Object.freeze({ id: -1, _isFilter: true })
const loading = ref(false)
const borrowKeyword = ref('')
const activeTab = ref('首页')

// 治具 Tab 筛选
const jigFilterName = ref('')
const jigFilterModel = ref('')
const jigFilterCode = ref('')
const jigFilterLocation = ref('')
const jigFilterStatus = ref('')
const resetJigFilters = () => {
  jigFilterName.value = ''
  jigFilterModel.value = ''
  jigFilterCode.value = ''
  jigFilterLocation.value = ''
  jigFilterStatus.value = ''
  page.value = 1; loadData()
}
// 耗材 Tab 筛选
const consFilterName = ref('')
const consFilterLocation = ref('')
const consFilterStatus = ref('')
const resetConsFilters = () => {
  consFilterName.value = ''
  consFilterLocation.value = ''
  consFilterStatus.value = ''
  page.value = 1; loadData()
}

// 出入库记录
const txRecords = ref([])
const txPage = ref(1)
const txPageSize = ref(20)
const txTotal = ref(0)
const txLoading = ref(false)
const txFilterTimeRange = ref(null)
const txFilterType = ref('')
const txFilterPart = ref('')
const txFilterOperator = ref('')
const txFilterRemark = ref('')
const txFilterDepartmentManager = ref('')
const txFilterLine = ref('')
const txFilterBorrowDate = ref(null)
const txFilterReturnDate = ref(null)
const txSortOrder = ref('')

// 治具/耗材排序状态
const jigSortTotal = ref('')
const jigSortAvailable = ref('')
const consSortStock = ref('')
const consSortWarn = ref('')
const PART_SORT_REFS = { jigSortTotal, jigSortAvailable, consSortStock, consSortWarn }
const SORT_FIELDS = {
  jigSortTotal: 'total_qty', jigSortAvailable: 'available_qty',
  consSortStock: 'stock_qty', consSortWarn: 'warn_qty',
}

const filteredTxRecords = computed(() => [FILTER_ROW, ...txRecords.value])

const loadTxData = async () => {
  txLoading.value = true
  try {
    const params = { page: txPage.value, page_size: txPageSize.value }
    if (txFilterType.value) {
      if (txFilterType.value === '归还') {
        params.is_returned = true
      } else {
        params.tx_type = txFilterType.value
      }
    }
    if (txFilterTimeRange.value) {
      const [d0] = txFilterTimeRange.value
      if (d0) params.date_from = formatDate(d0)
      const d1 = txFilterTimeRange.value[1]
      if (d1) params.date_to = formatDate(d1)
    }
    const kwParts = []
    if (txFilterPart.value?.trim()) kwParts.push(txFilterPart.value.trim())
    if (txFilterOperator.value?.trim()) kwParts.push(txFilterOperator.value.trim())
    if (txFilterRemark.value?.trim()) kwParts.push(txFilterRemark.value.trim())
    if (txFilterDepartmentManager.value?.trim()) kwParts.push(txFilterDepartmentManager.value.trim())
    if (txFilterLine.value?.trim()) kwParts.push(txFilterLine.value.trim())
    if (kwParts.length) params.keyword = kwParts.join(' ')
    if (txFilterBorrowDate.value) {
      const d = txFilterBorrowDate.value
      params.borrow_date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
    }
    if (txFilterReturnDate.value) {
      const d = txFilterReturnDate.value
      params.return_date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
    }
    if (txSortOrder.value) {
      params.sort_by = 'qty'
      params.sort_order = txSortOrder.value
    }
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

const toggleTxSort = (cur) => {
  if (!cur) { txSortOrder.value = 'asc' }
  else if (cur === 'asc') { txSortOrder.value = 'desc' }
  else { txSortOrder.value = '' }
  txPage.value = 1
  loadTxData()
}

const togglePartSort = (refName) => {
  const r = PART_SORT_REFS[refName]
  if (!r) return
  r.value = !r.value ? 'asc' : r.value === 'asc' ? 'desc' : ''
  page.value = 1
  loadData()
}

watch([txPage, txPageSize], () => loadTxData())

const statusTagType = (row) => {
  if (row.part_type === '治具') {
    return { '在库': 'success', '借出': 'warning', '维修': 'info', '报损': 'danger', '报失': 'danger' }[row.status] || 'info'
  }
  return { '正常': 'success', '预警': 'warning', '缺货': 'danger', '维修': 'info', '报损': 'danger', '报失': 'danger' }[row.status] || 'info'
}
const txTagType = (t) => ({ '借出': 'primary', '归还': 'success', '领用': 'primary', '补货': 'success', '减少': 'warning', '维修': 'info', '丢失': 'danger', '损坏': 'danger' }[t] || 'info')
/** 治具流水显示：优先去掉 part_name 末尾重复的 ` - {model}` 再判断是否拼接 */
const txPartDisplay = (row) => {
  let name = row.part_name || ''
  if (row.model && name.endsWith(` - ${row.model}`)) {
    name = name.slice(0, -(row.model.length + 3))
  }
  if (!name.startsWith(row.model)) {
    name = `${row.model}-${name}`
  }
  return name
}

// ---------------- 看板统计 ----------------
const statsLoading = ref(false)
const sd = ref({
  total: 0, in_stock: 0, borrowed_out: 0,
  repair_count: 0, lost_count: 0, damaged_count: 0,
  low_stock: 0, pending_total: 0,
  good_rate: 0, return_rate: 0, stock_rate: 0,
  low_stock_items: [], repair_items: [], lost_items: [], damaged_items: [],
  overdue_count: 0, overdue_items: [],
})

const loadStats = async () => {
  if (activeTab.value === '出入库记录') return
  statsLoading.value = true
  try {
    const res = await warehouseApi.stats({ part_type: activeTab.value === '首页' ? null : activeTab.value })
    sd.value = res.data || sd.value
  } catch (e) { console.error(e) }
  finally { statsLoading.value = false }
}
/** 维修/丢失/损坏合并成一条混合列表 */
const pendingMixedItems = computed(() => {
  const rows = []
  sd.value.repair_items?.forEach(it => rows.push({
    ...it, _type: 'repair', _label: '维修', _actionText: '已维修',
  }))
  sd.value.lost_items?.forEach(it => rows.push({
    ...it, _type: 'lost', _label: '丢失', _actionText: '已找回',
  }))
  sd.value.damaged_items?.forEach(it => rows.push({
    ...it, _type: 'damaged', _label: '损坏', _actionText: '已修复',
  }))
  return rows
})

/** 统一处理按钮 */
const onPendingAction = (it) => {
  if (it._type === 'repair') openFinishRepair(it)
  else if (it._type === 'lost') submitFoundBack(it)
  else if (it._type === 'damaged') submitRepairDamaged(it)
}
const kpiSub = (count, emptyText) => (count > 0 ? '点击查看明细' : emptyText)
const formatDate = (d) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`

const STATS_POLL_INTERVAL = 30000  // 30s 无感轮询
const statsTimer = ref(null)
const startStatsPolling = () => {
  stopStatsPolling()
  // 页面不可见时不轮询
  if (document.hidden) return
  loadStats()  // 立即刷新一次
  statsTimer.value = setInterval(() => {
    if (activeTab.value === '首页' && !document.hidden) loadStats()
  }, STATS_POLL_INTERVAL)
}
const stopStatsPolling = () => {
  if (statsTimer.value) {
    clearInterval(statsTimer.value)
    statsTimer.value = null
  }
}
/** 页面可见性变化 → 切回前台时立即刷新首页数据 */
const onVisibilityChange = () => {
  if (!document.hidden && activeTab.value === '首页') {
    startStatsPolling()  // 重新启动轮询 + 立即刷新
  }
}

/** KPI 卡片点击 → 跳对应 Tab */
const onKpiClick = (type) => {
  const STATUS_MAP = {
    overdue: { tab: '治具', status: '借出' },
    lowstock: { tab: '耗材', status: '预警' },
    repair: { tab: '治具', status: '维修' },
    lost: { tab: '治具', status: '报失' },
    damaged: { tab: '治具', status: '报损' },
  }
  const cfg = STATUS_MAP[type]
  if (!cfg) return
  // 设置筛选
  if (cfg.tab === '治具') {
    jigFilterStatus.value = cfg.status
    consFilterStatus.value = ''
  } else {
    consFilterStatus.value = cfg.status
    jigFilterStatus.value = ''
  }
  activeTab.value = cfg.tab
  // 直接加载数据（不走 onTabChange，避免手动切 Tab 时被清空）
  loadData()
  loadStats()
  if (cfg.tab === '治具' || cfg.tab === '耗材') stopStatsPolling()
}

/** 催还：复制文案到剪贴板（后续可换成调后端通知接口） */
const remindBorrower = (item) => {
  const days = item.overdue_days || 0
  const text = `${item.borrower || '你好'}，你借用的「${item.name}」已超过 ${days} 天未归还，请尽快归还。谢谢！`
  const fallbackCopy = () => {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try { document.execCommand('copy') } catch { /* ignore */ }
    document.body.removeChild(ta)
    toast.success('催还信息已复制，请粘贴发送')
  }
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text)
      .then(() => toast.success('催还信息已复制，请粘贴发送'))
      .catch(fallbackCopy)
  } else {
    fallbackCopy()
  }
}
const loadData = async () => {
  if (activeTab.value === '出入库记录') { items.value = []; total.value = 0; return }
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (activeTab.value !== '首页') params.part_type = activeTab.value

    // 状态筛选改为后端参数，分页/总数全部由后端保证一致
    if (activeTab.value === '治具' && jigFilterStatus.value) {
      params.status = jigFilterStatus.value
    } else if (activeTab.value === '耗材' && consFilterStatus.value) {
      params.status = consFilterStatus.value
    }

    let kw = ''
    if (activeTab.value === '治具') {
      const parts = [jigFilterName.value, jigFilterModel.value, jigFilterCode.value, jigFilterLocation.value]
        .filter(Boolean)
      if (parts.length) kw = parts.join(' ')
    } else if (activeTab.value === '耗材') {
      const parts = [consFilterName.value, consFilterLocation.value].filter(Boolean)
      if (parts.length) kw = parts.join(' ')
    }
    if (kw) params.keyword = kw

    for (const [key, field] of Object.entries(SORT_FIELDS)) {
      const val = PART_SORT_REFS[key].value
      if (val) { params.sort_by = field; params.sort_order = val; break }
    }

    const res = await warehouseApi.list(params)
    let loaded = res.data?.items || []
    total.value = res.data?.total || 0

    if (activeTab.value === '治具' || activeTab.value === '耗材') {
      items.value = [FILTER_ROW, ...loaded]
    } else {
      items.value = loaded
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const refreshAll = () => {
  if (activeTab.value === '出入库记录') { loadTxData(); return }
  if (activeTab.value === '首页') { loadStats(); loadTxData(); return }
  loadData(); loadStats(); loadTxData()
}

const onTabChange = () => {
  // 手动切 Tab — 清空当前 Tab 的状态筛选，避免 KPI 带入的过滤残留
  jigFilterStatus.value = ''
  consFilterStatus.value = ''
  if (activeTab.value === '出入库记录') {
    stopStatsPolling()
    if (txPage.value !== 1) txPage.value = 1; else loadTxData()
  } else if (activeTab.value === '首页') {
    loadStats()
    loadTxData()
    startStatsPolling()
  } else {
    stopStatsPolling()
    if (page.value !== 1) page.value = 1; else loadData()
    loadStats()
  }
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
  id: null, name: '', model: '', code: '', part_type: '治具',
  total_qty: 1, unit: '个', location: '', warn_qty: 0,
})
const editLocationList = ref([])

const openEdit = (row) => {
  if (row) {
    Object.assign(editForm, {
      id: row.id, name: row.name, model: row.model, code: row.code || '', part_type: row.part_type,
      total_qty: row.total_qty, unit: row.unit, location: row.location,
      warn_qty: row.warn_qty,
    })
    editLocationList.value = row.location ? row.location.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : []
  } else {
    Object.assign(editForm, {
      id: null, name: '', model: '', code: '', part_type: '治具',
      total_qty: 1, unit: '个', location: '', warn_qty: 0,
    })
    editLocationList.value = []
  }
  editDialog.value = true
}

const submitEdit = async () => {
  try {
    await editFormRef.value.validate()
  } catch {
    return
  }

  // 新增物品时确认入库数量
  if (!editForm.id) {
    const label = editForm.part_type === '治具' ? '治具' : '耗材'
    const { ElMessageBox } = await import('element-plus')
    try {
      await ElMessageBox.confirm(
        `新增「${editForm.name}」\n入库数量：${editForm.total_qty} ${editForm.unit}`,
        `${label}入库确认`,
        { confirmButtonText: '确认入库', cancelButtonText: '取消', type: 'info' }
      )
    } catch {
      return // 用户取消
    }
  }

  saving.value = true
  try {
    const payload = { ...editForm }
    // 货位从标签列表合并为逗号分隔字符串
    payload.location = editLocationList.value.join(', ')
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
  const ok = await confirmDelete('治具仓物品', `将删除「${row.name}」及其首页流水记录`)
  if (!ok) return
  try {
    await warehouseApi.delete(row.id)
    toast.success('删除成功')
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '删除失败')
  }
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  if (isNaN(d.getTime())) return t
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
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

const downloadTemplate = async () => {
  try {
    const res = await warehouseApi.downloadTemplate()
    // 兼容三种返回：Blob / AxiosResponse(.data 是 Blob) / 包装对象(.data.data 是 Blob)
    const blob = res instanceof Blob
      ? res
      : (res?.data instanceof Blob ? res.data : new Blob([res?.data ?? res]))
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '物品导入模板.xlsx'
    document.body.appendChild(a)   // ← Firefox 必须 append 才能 click
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
    toast.error('下载模板失败')
  }
}

// ---------------- 借出 / 归还 / 领用 / 补货 / 维修 ----------------
const borrowDialog = ref(false)
const returnDialog = ref(false)
const consumeDialog = ref(false)
const restockDialog = ref(false)
const finishRepairDialog = ref(false)
const actionLoading = ref(false)
const actionRow = ref(null)
const borrowForm = reactive({ operator: '', department_manager: '', line: '', qty: 1, remark: '' })
const consumeForm = reactive({ operator: '', department_manager: '', line: '', qty: 1, remark: '' })
const restockForm = reactive({ qty: 1, remark: '' })
const finishRepairForm = reactive({ qty: 1, remark: '' })

const borrowRecords = ref([])
const borrowRecordsLoading = ref(false)

const resetActionForms = () => {
  Object.assign(borrowForm, { operator: '', department_manager: '', line: '', qty: 1, remark: '' })
  Object.assign(consumeForm, { operator: '', department_manager: '', line: '', qty: 1, remark: '' })
  Object.assign(restockForm, { qty: 1, remark: '' })
  Object.assign(finishRepairForm, { qty: 1, remark: '' })
}

const openBorrow = (row) => { actionRow.value = row; resetActionForms(); borrowForm.qty = 1; borrowDialog.value = true }
const openReturn = (row) => { actionRow.value = row; resetActionForms(); returnDialog.value = true }
const openConsume = (row) => { actionRow.value = row; resetActionForms(); consumeForm.qty = 1; consumeDialog.value = true }
const openRestock = (row) => { actionRow.value = row; resetActionForms(); restockForm.qty = 1; restockDialog.value = true }
const handleMoreCommand = (cmd, row) => {
  if (cmd === 'restock') openRestock(row)
  else if (cmd === 'finish_repair') openFinishRepair(row)
  else if (cmd === 'edit') openEdit(row)
  else if (cmd === 'delete') handleDelete(row)
  else if (cmd === 'loss') openLoss(row)
  else if (cmd === 'damaged') openDamaged(row)
  else if (cmd === 'repair_damaged' || cmd === 'found_back') openReturn(row)
}

const openLoss = (row) => {
  actionRow.value = row
  returnDialog.value = true
}

const openDamaged = (row) => {
  actionRow.value = row
  returnDialog.value = true
}

const openFinishRepair = (row) => {
  if (row && typeof row.repair_qty === 'number') {
    actionRow.value = row
  }
  resetActionForms()
  finishRepairForm.qty = actionRow.value?.repair_qty || 1
  finishRepairDialog.value = true
}

const loadBorrowRecords = async () => {
  if (!actionRow.value) return
  borrowRecordsLoading.value = true
  try {
    if (actionRow.value.part_type === '耗材') {
      const res = await warehouseApi.consumeRecords(actionRow.value.id, true)
      borrowRecords.value = res.data || []
    } else {
      const res = await warehouseApi.borrowRecords(actionRow.value.id, true)
      borrowRecords.value = res.data || []
    }
  } catch (e) {
    console.error(e)
    borrowRecords.value = []
  } finally {
    borrowRecordsLoading.value = false
  }
}

const submitBorrow = async () => {
  if (!borrowForm.operator?.trim() || !borrowForm.line) { toast.error('请填写借用人并选择线体'); return }
  actionLoading.value = true
  try {
    await warehouseApi.borrow(actionRow.value.id, { ...borrowForm })
    toast.success('借出成功')
    borrowDialog.value = false
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitReturn = async (record) => {
  actionLoading.value = true
  try {
    const payload = actionRow.value.part_type === '耗材'
      ? { consume_tx_id: record.id }
      : { borrow_record_id: record.id }
    await warehouseApi.returnBack(actionRow.value.id, payload)
    toast.success('归还成功')
    removeFromCart(actionRow.value.id)
    await loadBorrowRecords()
    refreshAll()
    if (!borrowRecords.value.length) {
      returnDialog.value = false
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitToRepair = async (record) => {
  actionLoading.value = true
  try {
    await warehouseApi.toRepair(actionRow.value.id, { borrow_record_id: record.id })
    toast.success('已转维修')
    removeFromCart(actionRow.value.id)
    await loadBorrowRecords()
    refreshAll()
    if (!borrowRecords.value.length) {
      returnDialog.value = false
    }
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitLoss = async (record) => {
  try {
    const { ElMessageBox } = await import('element-plus')
    const { value } = await ElMessageBox.prompt('请输入报失原因（选填）', '治具报失确认', {
      confirmButtonText: '确认报失', cancelButtonText: '取消', inputType: 'textarea',
    })
    actionLoading.value = true
    await warehouseApi.loss(actionRow.value.id, { borrow_record_id: record.id, remark: value || '' })
    toast.success('已报失')
    removeFromCart(actionRow.value.id)
    await loadBorrowRecords()
    refreshAll()
    if (!borrowRecords.value.length) {
      returnDialog.value = false
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      toast.error(e.response?.data?.detail || '操作失败')
    }
  } finally { actionLoading.value = false }
}

const submitDamaged = async (record) => {
  try {
    const { ElMessageBox } = await import('element-plus')
    const { value } = await ElMessageBox.prompt('请输入报损原因（选填）', '治具报损确认', {
      confirmButtonText: '确认报损', cancelButtonText: '取消', inputType: 'textarea',
    })
    actionLoading.value = true
    await warehouseApi.damaged(actionRow.value.id, { borrow_record_id: record.id, remark: value || '' })
    toast.success('已报损')
    removeFromCart(actionRow.value.id)
    await loadBorrowRecords()
    refreshAll()
    if (!borrowRecords.value.length) {
      returnDialog.value = false
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      toast.error(e.response?.data?.detail || '操作失败')
    }
  } finally { actionLoading.value = false }
}

const submitFoundBack = async (record) => {
  try {
    const { ElMessageBox } = await import('element-plus')
    const { value } = await ElMessageBox.prompt('请输入备注（选填）', '已找回确认', {
      confirmButtonText: '确认', cancelButtonText: '取消', inputType: 'textarea',
    })
    actionLoading.value = true
    const borrowRecordId = record.borrow_record_id || record.id
    const partId = record.borrow_record_id ? record.id : actionRow.value?.id
    if (!partId) { toast.error('无法获取物品信息'); return }
    await warehouseApi.foundBack(partId, { borrow_record_id: borrowRecordId, remark: value || '' })
    toast.success('已找回')
    removeFromCart(partId)
    await loadBorrowRecords()
    refreshAll()
    if (!borrowRecords.value.length) {
      returnDialog.value = false
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      toast.error(e.response?.data?.detail || '操作失败')
    }
  } finally { actionLoading.value = false }
}

const submitRepairDamaged = async (record) => {
  try {
    const { ElMessageBox } = await import('element-plus')
    const { value } = await ElMessageBox.prompt('请输入备注（选填）', '已修复确认', {
      confirmButtonText: '确认', cancelButtonText: '取消', inputType: 'textarea',
    })
    actionLoading.value = true
    const borrowRecordId = record.borrow_record_id || record.id
    const partId = record.borrow_record_id ? record.id : actionRow.value?.id
    if (!partId) { toast.error('无法获取物品信息'); return }
    await warehouseApi.repairDamaged(partId, { borrow_record_id: borrowRecordId, remark: value || '' })
    toast.success('已修复')
    removeFromCart(partId)
    await loadBorrowRecords()
    refreshAll()
    if (!borrowRecords.value.length) {
      returnDialog.value = false
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      toast.error(e.response?.data?.detail || '操作失败')
    }
  } finally { actionLoading.value = false }
}

const submitConsume = async () => {
  if (!consumeForm.operator?.trim() || !consumeForm.line) { toast.error('请填写领用人并选择线体'); return }
  actionLoading.value = true
  try {
    await warehouseApi.consume(actionRow.value.id, { ...consumeForm })
    toast.success('领用成功')
    consumeDialog.value = false
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitRestock = async () => {
  if (!restockForm.qty || restockForm.qty <= 0) { toast.error('请填写补货数量'); return }
  actionLoading.value = true
  try {
    await warehouseApi.restock(actionRow.value.id, { ...restockForm })
    toast.success('补货成功')
    restockDialog.value = false
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

const submitFinishRepair = async () => {
  if (!finishRepairForm.qty || finishRepairForm.qty <= 0) { toast.error('请填写完成数量'); return }
  actionLoading.value = true
  try {
    await warehouseApi.finishRepair(actionRow.value.id, { ...finishRepairForm })
    toast.success('已维修')
    finishRepairDialog.value = false
    refreshAll()
  } catch (e) {
    toast.error(e.response?.data?.detail || '操作失败')
  } finally { actionLoading.value = false }
}

// ---------------- 备注编辑 ----------------
const remarkDialog = ref(false)
const remarkRow = ref(null)
const remarkEditing = ref('')
const remarkSaving = ref(false)

const openEditRemark = (row) => {
  remarkRow.value = row
  remarkEditing.value = row.remark || ''
  remarkDialog.value = true
}

const submitRemark = async () => {
  if (!remarkRow.value) return
  remarkSaving.value = true
  try {
    await warehouseApi.updateTxRemark(remarkRow.value.id, remarkEditing.value)
    toast.success('备注已更新')
    remarkRow.value.remark = remarkEditing.value
    const idx = txRecords.value.findIndex(t => t.id === remarkRow.value.id)
    if (idx >= 0) txRecords.value[idx].remark = remarkEditing.value
    remarkDialog.value = false
  } catch (e) {
    toast.error(e.response?.data?.detail || '保存失败')
  } finally {
    remarkSaving.value = false
  }
}

// ---------------- 详情 ----------------
const detailDialog = ref(false)
const detail = ref(null)

const openDetail = async (row) => {
  // 仅在表格内有实际文本选区（非 collapsed）时才阻止，避免误伤页面其他处选中
  const sel = window.getSelection()
  if (sel && !sel.isCollapsed && sel.toString().trim()) return
  try {
    const res = await warehouseApi.detail(row.id)
    detail.value = res.data
    detailDialog.value = true
  } catch (e) {
    console.error(e)
    toast.error('详情加载失败')
  }
}

const onTableRowClick = (row) => {
  if (row._isFilter) return
  openDetail(row)
}

const tableRowClassName = ({ row }) => {
  return row._isFilter ? 'filter-row' : ''
}

onMounted(() => {
  if (activeTab.value === '首页') {
    loadStats()
    startStatsPolling()
  } else {
    loadData()
    loadStats()
  }
  loadTxData()
  loadOperators()
  loadDepartmentManagers()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  stopStatsPolling()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

// ---------------- 扫码出入库弹框 ----------------
const cartDialog = ref(false)
const scanMode = ref('borrow')
const scanKeyword = ref('')
const scanInputRef = ref(null)
const cartItems = ref([])
const scanSubmitting = ref(false)
const scanForm = reactive({ operator: '', department_manager: '', line: '', remark: '' })

const scanModeName = computed(() => ({ borrow: '借领', return: '归还' }[scanMode.value] || '借领'))

const scanPlaceholder = computed(() => ({
  borrow: '扫码或输入物品名称/型号，回车添加到借领列表',
  return: '扫码或输入名称/型号，回车添加到归还列表',
}[scanMode.value] || '扫码或搜索'))

const cartTotalQty = computed(() => cartItems.value.reduce((s, i) => s + i.qty, 0))

const focusScanInput = () => { nextTick(() => scanInputRef.value?.focus()) }

watch(activeTab, () => {
  scanMode.value = 'borrow'
  cartItems.value = []
})

const onBorrowSearch = async () => {
  const kw = borrowKeyword.value.trim()
  if (!kw) { toast.warn('请输入物品名称或扫码'); return }
  borrowKeyword.value = ''
  const added = await doScanSearch(kw)
  if (added > 0 && !cartDialog.value) {
    cartDialog.value = true
    nextTick(focusScanInput)
  }
}

/** 归还弹框内统一操作：维修/报失/报损 */
const ACTION_MAP = {
  repair:  { api: warehouseApi.toRepair,  label: '维修', successMsg: '已转维修' },
  loss:    { api: warehouseApi.loss,      label: '报失', successMsg: '已报失' },
  damaged: { api: warehouseApi.damaged,   label: '报损', successMsg: '已报损' },
}
const cartAction = async (type, item, rec) => {
  const { label, api, successMsg } = ACTION_MAP[type]
  try {
    const { ElMessageBox } = await import('element-plus')
    const { value } = await ElMessageBox.prompt(`请输入${label}原因（选填）`, `${label}确认`, {
      confirmButtonText: `确认${label}`, cancelButtonText: '取消', inputType: 'textarea',
    })
    await api(item.id, { borrow_record_id: rec.id, remark: value || '' })
    toast.success(successMsg)
    removeFromCart(item.id)
    refreshAll()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      toast.error(e.response?.data?.detail || '操作失败')
    }
  }
}

const openBorrowDialog = () => {
  cartDialog.value = true
  nextTick(focusScanInput)
}

const doScanSearch = async (kw) => {
  try {
    const res = await warehouseApi.list({ keyword: kw, page: 1, page_size: 50 })
    const items = res.data?.items || []
    if (!items.length) {
      toast.error(`未找到「${kw}」匹配物品`)
      return 0
    }

    // 治具按型号精确过滤（不波及耗材）
    let targetItems = items
    if (items.some(i => i.part_type === '治具' && i.model === kw)) {
      targetItems = [
        ...items.filter(i => i.part_type === '治具' && i.model === kw),
        ...items.filter(i => i.part_type !== '治具'),
      ]
    }

    // ────────── 归还模式 ──────────
    if (scanMode.value === 'return') {
      const beforeLen = cartItems.value.length
      for (const item of targetItems) addToCart(item, 1)
      const newlyAdded = cartItems.value.length - beforeLen
      if (newlyAdded === 0) {
        toast.warn(`「${targetItems.map(i => i.name).join('、')}」无待归还记录`)
        return 0
      }
      const removed = await loadCartItemsRecords()
      const finalCount = cartItems.value.length - beforeLen
      if (finalCount === 0 && removed.length) {
        toast.warn(`「${removed.join('、')}」无待归还记录`)
        return 0
      }
      toast.success(`已添加 ${finalCount} 件到归还列表`)
      return cartItems.value.length
    }

    // ────────── 借领模式 ──────────
    let added = 0
    for (const item of targetItems) {
      const prevLen = cartItems.value.length
      addToCart(item, 1)
      if (cartItems.value.length > prevLen) added++
    }
    if (added > 0) {
      toast.success(`已添加 ${added} 件到列表`)
      return cartItems.value.length
    }

    // 借领无货 → 尝试切归还
    scanMode.value = 'return'
    const beforeLen = cartItems.value.length
    for (const item of targetItems) addToCart(item, 1)
    const newlyAdded = cartItems.value.length - beforeLen
    if (newlyAdded === 0) {
      scanMode.value = 'borrow'
      toast.warn('该物品当前可借/领数量不足，且无待归还记录')
      return 0
    }
    const removed = await loadCartItemsRecords()
    const finalCount = cartItems.value.length - beforeLen
    if (finalCount > 0) {
      toast.success(`已自动切换至归还模式，添加 ${finalCount} 件`)
      return cartItems.value.length
    }
    // 加进去又被清空 → 还原模式
    scanMode.value = 'borrow'
    cartItems.value = cartItems.value.slice(0, beforeLen)
    toast.warn(`「${removed.join('、') || targetItems.map(i => i.name).join('、')}」无待归还记录`)
    return 0
  } catch (e) {
    console.error(e)
    toast.error('搜索失败')
    return 0
  }
}

const onScan = async () => {
  const kw = scanKeyword.value.trim()
  if (!kw) { toast.warn('请输入物品名称或扫码'); return }
  scanKeyword.value = ''
  await doScanSearch(kw)   // 提示交给 doScanSearch 统一处理
}

const addToCart = (item, forceQty) => {
  let maxQty = 0
  if (scanMode.value === 'return') {
    if (item.part_type === '治具') {
      maxQty = (item.total_qty || 0) - (item.available_qty || 0)
    } else {
      // 耗材无 total_qty/available_qty 字段，给占位值；真实记录由 loadCartItemsRecords 查
      maxQty = 1
    }
  } else {
    if (item.part_type === '治具') {
      maxQty = (item.available_qty || 0) - (item.repair_qty || 0)
    } else {
      maxQty = item.stock_qty || item.total_qty || 0
    }
  }
  if (forceQty !== undefined) {
    const existing = cartItems.value.find(c => c.id === item.id)
    if (existing) return
    if (maxQty <= 0) return
    cartItems.value.push({ id: item.id, name: item.name, model: item.model, part_type: item.part_type, qty: forceQty, maxQty })
    return
  }
  if (maxQty <= 0) {
    toast.error(`「${item.name}」${scanMode.value === 'return' ? '没有借出记录' : '库存不足'}`)
    return
  }
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

const loadCartItemsRecords = async () => {
  const removed = []
  // 只加载尚未加载过的
  const pending = cartItems.value.filter(item => !item.activeRecords)
  if (!pending.length) return removed
  await Promise.all(pending.map(async (item) => {
    item.loadingRecords = true
    try {
      const isCon = item.part_type === '耗材'
      const records = (isCon
        ? (await warehouseApi.consumeRecords(item.id, true)).data
        : (await warehouseApi.borrowRecords(item.id, true)).data) || []
      const field = isCon ? 'tx_type' : 'status'
      const active = records
        .filter(r => ['领用', '借出'].includes(r[field]))
        .map(r => ({ ...r }))
      active.forEach(r => {
        if (!isCon && r.borrower !== undefined) r.operator = r.borrower
      })
      item.activeRecords = active
      if (item.activeRecords.length > 0) {
        item.selectedRecordId = item.activeRecords[0].id
      } else if (scanMode.value === 'return') {
        removed.push(item.name)
      }
    } catch (e) {
      console.warn('加载记录失败:', item.name, e)
    } finally {
      item.loadingRecords = false
    }
  }))
  cartItems.value = cartItems.value.filter(item => {
    const hasRecords = item.activeRecords && item.activeRecords.length > 0
    if (!hasRecords && scanMode.value === 'return') return false
    return true
  })
  return removed
}

watch(scanMode, (mode) => {
  // 仅清理状态，不调 loadCartItemsRecords —— 由 doScanSearch 或 onBorrowSearch 显式调用
  if (mode === 'borrow') {
    cartItems.value.forEach(item => {
      delete item.activeRecords
      delete item.selectedRecordId
      delete item.loadingRecords
    })
  }
})

const submitBatch = async () => {
  if (!cartItems.value.length) return
  if (scanMode.value !== 'return') {
    if (!scanForm.operator?.trim()) { toast.error('请填写借用人/领用人'); return }
    if (!scanForm.line) { toast.error('请选择线体'); return }
  }
  scanSubmitting.value = true
  const results = { ok: 0, fail: 0, errors: [] }
  try {
    // ── 借出提醒：检查操作人是否有未归还的治具 ──
    if (scanMode.value === 'borrow') {
      const jigItems = cartItems.value.filter(i => i.part_type === '治具')
      if (jigItems.length > 0 && scanForm.operator?.trim()) {
        const unreturned = (await warehouseApi.unreturnedCheck(scanForm.operator.trim())).data || []
        // 排除本次正要借出的物品（不重复提醒）
        const toBorrowIds = new Set(jigItems.map(i => i.id))
        const otherUnreturned = unreturned.filter(u => !toBorrowIds.has(u.part_id))
        if (otherUnreturned.length > 0) {
          const { ElMessageBox } = await import('element-plus')
          const itemList = otherUnreturned.map(u =>
            `　· ${u.part_name}${u.part_model ? `（${u.part_model}）` : ''} ×${u.qty}`
          ).join('\n')
          const msg = `"${scanForm.operator}" 尚有未归还的治具：\n\n${itemList}\n\n确定继续借出吗？`
          try {
            await ElMessageBox.confirm(msg, '借出提醒', {
              confirmButtonText: '继续借出', cancelButtonText: '取消', type: 'warning',
            })
          } catch {
            scanSubmitting.value = false
            return  // 用户取消
          }
        }
      }
    }
    for (const item of cartItems.value) {
      try {
        const payload = { qty: item.qty, remark: scanForm.remark }
        if (scanMode.value === 'return') {
          if (!item.selectedRecordId) {
            results.errors.push(`${item.name}: 请点击左侧记录选中要归还的项`)
            results.fail++
            continue
          }
          const isCon = item.part_type === '耗材'
          const record = item.activeRecords?.find(r => r.id === item.selectedRecordId)
          if (!record) {
            results.errors.push(`${item.name}: 选中的记录不存在`)
            results.fail++
            continue
          }
          const retPayload = isCon
            ? { consume_tx_id: record.id }
            : { borrow_record_id: record.id }
          await warehouseApi.returnBack(item.id, retPayload)
        } else {
          payload.operator = scanForm.operator
          payload.department_manager = scanForm.department_manager
          payload.line = scanForm.line
          if (item.part_type === '治具') {
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
      toast.success(`提交成功（${results.ok} 件）`)
      clearCart()
      cartDialog.value = false
    } else {
      // 失败详情弹出框，避免 toast 超长截断
      const { ElMessageBox } = await import('element-plus')
      const escapeHtml = (s) => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      ElMessageBox.alert(
        results.errors.map(e => `• ${escapeHtml(e)}`).join('<br>'),
        `提交结果：成功 ${results.ok} 件，失败 ${results.fail} 件`,
        { dangerouslyUseHTMLString: true, confirmButtonText: '知道了' }
      )
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
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* ================================================================
   出入库弹框：固定高度 + 顶部/底部固定 + 仅列表滚动
   关键：从 .cart-modal 出发选，scoped 才能命中
   ================================================================ */

/* ① overlay 双层锁死：禁止整页滚动 */
:global(.cart-modal),
:global(.cart-modal .el-overlay-dialog) {
  overflow: hidden !important;
}

/* ② dialog 本体：从 overlay 出发的后代选择器，一定命中 */
:global(.cart-modal .el-dialog) {
  height: 92vh !important;
  max-height: 92vh !important;
  margin: 4vh auto !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}
:global(.cart-modal .el-dialog__header) {
  flex-shrink: 0 !important;
}
:global(.cart-modal .el-dialog__body) {
  flex: 1 !important;
  min-height: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}

/* ③ cd-wrap 撑满 body —— 组件内元素，scoped 直接命中 */
.cd-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ④ 上中下三段固定不压缩 */
.cd-mode-bar,
.cd-scan-bar,
.cd-footer {
  flex-shrink: 0;
}

/* ⑤ cd-body 吃满剩余 */
.cd-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ⑥ cd-list 唯一滚动区 */
.cd-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ---------- 出入库弹框内部元素 ---------- */
.cd-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 60px 0;
  color: var(--c-text-mute);
}
.cd-empty p { margin: 0; font-size: 14px; }
.cd-empty-sub { font-size: 12px; }

.cd-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--c-divider);
  border-radius: 8px;
  background: var(--c-bg);
  flex-shrink: 0;
}
.cd-row-info { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.cd-row-name { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cd-row-model { font-size: 12px; color: var(--c-text-mute); font-family: Consolas, monospace; }
.cd-row-tag {
  display: inline-block;
  align-self: flex-start;
  font-size: 11px;
  font-weight: 500;
  color: var(--c-text-mute, #94A3B8);
  background: #EEF2F6;
  padding: 1px 6px;
  border-radius: 4px;
  line-height: 1.4;
}
.cd-row-qty { display: flex; align-items: center; gap: 8px; }
.cd-row-qty .el-button { --el-button-size: 32px; font-size: 16px; }
.cd-row .el-button--warning { height: 32px; font-size: 14px; padding: 0 16px; }
.cd-row .el-button--danger.is-text { --el-button-size: 32px; font-size: 16px; }
.cd-qty-num { font-weight: 700; font-size: 16px; min-width: 32px; text-align: center; }
.cd-qty-limit { font-size: 12px; color: var(--c-text-mute); }

.cd-mode-bar {
  padding: 14px 20px;
  border-bottom: 1px solid var(--c-divider);
}

/* 借领/归还：两个大 Segment 按钮，各占一半宽 */
.cd-mode-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.cd-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 54px;
  border: 1.5px solid #E2E8F0;
  background: #FAFBFC;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  color: #64748B;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  outline: none;
  letter-spacing: 0.4px;
}

.cd-mode-btn .bi {
  font-size: 22px;
  line-height: 1;
}

.cd-mode-btn:hover:not(.active) {
  border-color: #93C5FD;
  background: #EFF6FF;
  color: #2563EB;
}

/* 借领：选中时橙色（往外借 / 警示感） */
.cd-mode-btn.cd-mode-borrow.active {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  border-color: #D97706;
  color: #FFFFFF;
  box-shadow: 0 8px 20px -8px rgba(217, 119, 6, 0.55);
}

/* 归还：选中时绿色（往回收 / 完成感） */
.cd-mode-btn.cd-mode-return.active {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  border-color: #059669;
  color: #FFFFFF;
  box-shadow: 0 8px 20px -8px rgba(5, 150, 105, 0.55);
}

/* 选中态图标微动效 */
.cd-mode-btn.active .bi {
  animation: cd-mode-pop 0.28s ease-out;
}
@keyframes cd-mode-pop {
  0%   { transform: scale(0.85); }
  60%  { transform: scale(1.12); }
  100% { transform: scale(1); }
}
.cd-scan-bar {
  padding: 10px 20px;
  border-bottom: 1px solid var(--c-divider);
}
.cd-footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--c-divider);
  background: var(--c-bg-soft, #f5f7fa);
}

/* 第一行：三个字段等宽平分整行 */
.cd-form-row {
  display: flex;
  gap: 10px;
}
.cd-form-row .cd-field {
  flex: 1;
  min-width: 0;   /* 关键：允许收缩，长内容省略号 */
}

/* 第二行：备注 + 按钮同行 */
.cd-submit-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cd-submit-row .cd-remark-input {
  flex: 1;
  min-width: 0;
}

/* ---------- 页面其他样式 ---------- */
.page-header {
  display: flex;
  align-items: center;
  min-height: 52px;
  gap: 10px;
  padding: var(--sp-1, 6px) 4px;
  border-bottom: 1px solid var(--c-divider);
  flex-wrap: wrap;
  flex-shrink: 0;
  box-sizing: border-box;
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  line-height: 1.2;
  height: 32px;
}
.page-title .emoji {
  line-height: 1;
}
.ph-right-group {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.wh-model {
  display: block;
  font-family: Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wh-model-empty {
  display: block;
  color: var(--c-text-mute);
}
.wh-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding-bottom: 16px;
  box-sizing: border-box;
}
.wh-tabs { flex-shrink: 0; }
.wh-tabs-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.wh-main {
  display: flex;
  flex: 1;
  min-height: 0;
  margin-top: 10px;
  overflow: hidden;
}
.wh-table-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.wh-table-wrap {
  flex: 1;
  min-height: 0;
}
.wh-table-wrap :deep(.el-table) { height: 100%; }
.wh-table-wrap :deep(.filter-row) {
  position: sticky;
  top: 0;
  z-index: 3;
  background: var(--el-bg-color, #fff);
}
.tx-filter-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 6px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1;
  color: var(--c-text-mute);
  user-select: none;
  transition: background .15s;
}
.tx-filter-trigger:hover { background: var(--c-bg-mute); }
.tx-line-popper { z-index: 9999 !important; }
.tx-line-menu { max-height: 280px; overflow-y: auto; }
.tx-line-menu .el-dropdown-menu__item { justify-content: center; }
.jig-fbr-cell {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
/* 三种类型标签颜色 */
.mini-tag--repair  { background: #FEF9C3; color: #CA8A04; }
.mini-tag--lost    { background: #F3E8FF; color: #7C3AED; }
.mini-tag--damaged { background: #CFFAFE; color: #0891B2; }

/* 混合列表容器 */
.pending-mixed {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px 10px;
  border-top: 1px solid #F8FAFC;
}
/* ============ 首页右侧：待处理卡片 ============ */
.pending-card {
  --accent: #D97706;              /* 指示条 / 数字强调色 */
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #E8ECF0;
  border-radius: 16px;
  padding: 16px 18px 14px;
  min-height: 0;
  overflow: hidden;
}

.pending-head {
  display: flex;
  align-items: center;
  justify-content: center;        /* ✅ 标题居中 */
  gap: 6px;
  padding-bottom: 10px;
  border-bottom: 1px solid #F1F5F9;
  flex-shrink: 0;
}
.pending-indicator {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--accent, #94A3B8);
  flex-shrink: 0;
}
.pending-title {
  font-size: 14px;
  font-weight: 700;
  color: #0B1120;
  letter-spacing: .2px;
}

/* 卡片主体：唯一滚动区 */
.pending-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 低库存分组 */
.pending-section { padding: 0 2px; }

.ps-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 6px 6px;
  font-size: 13px;
}
.ps-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ps-label {
  font-weight: 600;
  color: #0B1120;
}
.ps-count {
  margin-left: auto;
  min-width: 22px;
  height: 18px;
  padding: 0 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #FEF3C7;
  color: #92400E;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.ps-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 4px;
}

/* 空状态：与左侧 panel-empty 保持一致 */
.pending-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  font-size: 13px;
  padding: 24px 0;
  gap: 8px;
}
.pending-mixed-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 6px;
  border-radius: 6px;
  font-size: 13px;
  transition: background .15s;
}
.pending-mixed-row:hover {
  background: #F8FAFC;
}
.pending-mixed-row .mini-name {
  flex: 1;
  min-width: 0;
}
.jig-fbr-cell :deep(.el-input) { width: 100%; min-width: 0; }
.jig-fbr-cell :deep(.el-input__wrapper) { padding: 0 4px; height: 28px; }
.jig-fbr-cell :deep(.el-input__inner) { text-align: center; height: 28px; font-size: 12px; }
.jig-fbr-cell :deep(.el-select) { width: 100%; min-width: 0; }
.jig-fbr-cell :deep(.el-select__wrapper) { justify-content: center; height: 28px; }
.jig-fbr-cell :deep(.el-date-editor) { width: 100% !important; min-width: 0 !important; flex-wrap: nowrap; }
.jig-fbr-cell :deep(.el-date-editor .el-input__wrapper) { height: 28px; justify-content: center; }
.jig-fbr-cell :deep(.el-date-editor .el-input__inner) { text-align: center; }
.jig-fbr-cell :deep(.el-date-editor .el-range-input) { font-size: 12px; text-align: center; }
.jig-fbr-cell :deep(.el-date-editor .el-range-separator) { font-size: 11px; padding: 0 2px; }
.jig-fbr-cell :deep(.el-date-editor .el-range__icon) { display: none; }
.jig-fbr-cell :deep(.el-dropdown-menu__item) { justify-content: center; }
.part-sort-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 24px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1;
  color: var(--c-text-mute);
  user-select: none;
  transition: background .15s;
}
.part-sort-btn:hover { background: var(--c-bg-mute); }
.part-sort-btn.active { background: var(--el-color-primary); color: #fff; }
.tx-remark-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}
.tx-remark-cell .tx-remark-edit {
  font-size: 12px;
  color: var(--primary, #2563EB);
  opacity: 0;
  transition: opacity .15s;
}
.tx-remark-cell:hover .tx-remark-edit { opacity: 1; }
.tx-empty-tip {
  text-align: center;
  color: var(--c-text-mute);
  padding: 30px 0;
  font-size: 13px;
}
.wh-name { font-weight: 600; color: var(--c-text); }
.wh-form-hint { margin-left: 10px; font-size: 12px; color: var(--c-text-mute); }
.wh-form-static { font-size: 14px; font-weight: 600; color: var(--c-text, #0B1120); line-height: 32px; }
.loc-tags { display: inline-flex; gap: 4px; flex-wrap: wrap; align-items: center; }
.loc-tag { white-space: nowrap; }
.loc-more { cursor: pointer; font-size: 12px; color: var(--el-color-primary); font-weight: 600; white-space: nowrap; }
.ok-text { color: #059669; }
.warn-text { color: #D97706; }
.danger-text { color: #DC2626; }
.wh-action-info {
  background: #F8FAFC;
  border: 1px solid var(--c-divider);
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--c-text-2);
}
.wh-action-info p { margin: 2px 0; }
.wh-detail-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
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
  border-radius: 6px;
  color: #DC2626;
  font-size: 13px;
  font-weight: 600;
}
.wh-desc { margin-bottom: 4px; }
.wh-import-tip { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; line-height: 1.2; }
.wh-import-tip .el-link { flex-shrink: 0; }
.wh-import-result {
  margin-top: 14px;
  border: 1px solid var(--c-divider);
  border-radius: 6px;
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
.wh-mode-switch { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.cart-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; margin-left: 6px;
  font-size: 12px; font-weight: 700;
  background: #DC2626; color: #fff;
  border-radius: 9px; padding: 0 5px;
}

/* ============ 首页Tab：看板仪表盘 v3 ============ */
.wh-dashboard {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  flex-shrink: 0;
}

.kpi-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 18px 16px;
  background: #fff;
  border: 1px solid #E8ECF0;
  border-radius: 16px;
  cursor: pointer;
  overflow: hidden;
  align-items: center;        /* 新增：交叉轴居中 */
  text-align: center;         /* 新增：文字居中 */
  transition: transform .25s cubic-bezier(.4,0,.2,1),
              box-shadow .25s cubic-bezier(.4,0,.2,1),
              border-color .25s;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: -30px;
  right: -30px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--glow-soft) 0%, transparent 70%);
  pointer-events: none;
}

.kpi-card:hover {
  border-color: var(--main);
  box-shadow: 0 12px 28px -8px var(--glow);
}

.kpi-card--danger  { --main: #DC2626; --soft: #FEE2E2; --glow-soft: rgba(220,38,38,.10); --glow: rgba(220,38,38,.35); }
.kpi-card--warning { --main: #D97706; --soft: #FEF3C7; --glow-soft: rgba(217,119,6,.10); --glow: rgba(217,119,6,.35); }
.kpi-card--repair  { --main: #CA8A04; --soft: #FEF9C3; --glow-soft: rgba(202,138,4,.10); --glow: rgba(202,138,4,.35); }
.kpi-card--lost    { --main: #7C3AED; --soft: #F3E8FF; --glow-soft: rgba(124,58,237,.10); --glow: rgba(124,58,237,.35); }
.kpi-card--damaged { --main: #0891B2; --soft: #CFFAFE; --glow-soft: rgba(8,145,178,.10); --glow: rgba(8,145,178,.35); }

.kpi-head {
  display: flex;
  align-items: center;
  justify-content: center;   /* ✅ 新增 */
  gap: 8px;
  position: relative;
  z-index: 1;
}
.kpi-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--soft);
  color: var(--main);
  font-size: 16px;
}
.kpi-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  letter-spacing: .2px;
}
.kpi-value {
  font-size: 38px;
  font-weight: 800;
  line-height: 1;
  text-align: center;   /* ✅ 可选 */
  color: var(--main);
  letter-spacing: -1.2px;
  font-variant-numeric: tabular-nums;
  position: relative;
  z-index: 1;
}
.kpi-sub {
  font-size: 12px;
  text-align: center;   /* ✅ 可选 */
  color: #94A3B8;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.wh-dashboard-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.panel {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #E8ECF0;
  border-radius: 16px;
  padding: 16px 18px 14px;
  min-height: 0;
  overflow: hidden;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: center;   /* ✅ 新增：标题组整体居中 */
  gap: 6px;
  padding-bottom: 10px;
  border-bottom: 1px solid #F1F5F9;
  flex-shrink: 0;
}
.panel-indicator {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: var(--accent, #94A3B8);
  flex-shrink: 0;
}
.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: #0B1120;
  letter-spacing: .2px;
}

.panel--overdue { --accent: #DC2626; --soft: #FEE2E2; }
.panel--warning { --accent: #D97706; --soft: #FEF3C7; }
.panel--repair  { --accent: #CA8A04; --soft: #FEF9C3; }
.panel--lost    { --accent: #7C3AED; --soft: #F3E8FF; }

.panel-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  font-size: 13px;
  padding: 24px 0;
  gap: 8px;
}
.panel-empty--good {
  color: #16A34A;
  font-weight: 600;
  font-size: 14px;
}
.empty-emoji { font-size: 20px; }

.panel-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 10px;
}

.overdue-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 12px;
}
.overdue-more {
  flex-shrink: 0;
  text-align: center;
  padding: 4px 0 2px;
}
.overdue-row {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #F1F5F9;
  transition: all .2s;
}
.overdue-row:hover {
  border-color: #E2E8F0;
  box-shadow: 0 4px 12px rgba(0,0,0,.05);
}
.overdue-row.is-critical {
  background: linear-gradient(90deg, #FEF2F2 0%, #FFF8F8 100%);
  border-color: #FECACA;
}
.overdue-row.is-critical:hover {
  box-shadow: 0 4px 12px rgba(220,38,38,.12);
}

.od-days {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  color: #92400E;
  flex-shrink: 0;
}
.od-days b {
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
  font-variant-numeric: tabular-nums;
}
.od-days span {
  font-size: 11px;
  font-weight: 600;
  margin-top: 2px;
  opacity: .8;
}
.is-critical .od-days {
  background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
  color: #991B1B;
}

.od-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.od-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}
.od-name {
  font-size: 14px;
  font-weight: 600;
  color: #0B1120;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.od-model {
  font-size: 11px;
  color: #94A3B8;
  font-family: Consolas, "SF Mono", monospace;
  flex-shrink: 0;
}
.od-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748B;
}
.od-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.od-meta-item .el-icon { font-size: 12px; }
.od-sep { color: #CBD5E1; }

.od-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.panel-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}
.panel--warning,
.panel--repair,
.panel--lost {
  flex: 0 1 auto;
  min-height: 0;
}

.mini-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 8px;
  border-radius: 8px;
  font-size: 13px;
  transition: background .15s;
}
.mini-row:hover { background: #F8FAFC; }

.mini-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent, #94A3B8);
  flex-shrink: 0;
}
.mini-name {
  flex: 1;
  min-width: 0;
  font-weight: 500;
  color: #0B1120;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mini-num {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent, #DC2626);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.mini-info {
  font-size: 12px;
  color: #94A3B8;
  white-space: nowrap;
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.mini-time {
  font-size: 11px;
  color: #CBD5E1;
  white-space: nowrap;
  flex-shrink: 0;
}
.mini-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 7px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  letter-spacing: .2px;
}
.mini-tag--lost    { background: #F3E8FF; color: #7C3AED; }
.mini-tag--damaged { background: #CFFAFE; color: #0891B2; }

@media (max-width: 1200px) {
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 1000px) {
  .wh-dashboard-body { grid-template-columns: 1fr; }
  .sk-body { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .kpi-value { font-size: 32px; }
}
@media (max-width: 800px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .kpi-value { font-size: 28px; }
  .kpi-card { padding: 14px; gap: 8px; }
  .wh-pending-summary { padding: 4px 10px; }
}

/* 记忆下拉 */
.mem-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.mem-del-btn {
  flex-shrink: 0;
  margin-left: 12px;
  color: #999;
  font-size: 12px;
}
.mem-del-btn:hover { color: #DC2626; }

/* 归还模式：借款人列表 */
.cd-return-records {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.cd-return-rec {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border: 1px solid var(--c-divider, #e5e7eb);
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
  user-select: none;
}
.cd-return-rec:hover { border-color: var(--el-color-primary); color: var(--el-color-primary); }
.cd-return-rec.active {
  background: var(--el-color-primary);
  color: #fff;
  border-color: var(--el-color-primary);
}
.cd-rec-operator { font-weight: 700; font-size: 13px; }
.cd-rec-line { opacity: .85; font-size: 11px; }
.cd-rec-time { opacity: .7; font-size: 11px; }
.cd-rec-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.cd-rec-actions .cd-rec-btn + .cd-rec-btn {
  margin-left: 0;
}
.cd-rec-btn {
  flex: 0 0 auto;
  width: 52px;
  min-width: 52px;
  height: 24px;
  padding: 0 !important;
  margin: 0 !important;
  font-size: 12px;
  line-height: 1;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
/* 三种颜色：只覆盖颜色变量，不动尺寸 */
.cd-rec-btn--repair {
  --el-button-text-color: #D97706;
  --el-button-border-color: #FCD34D;
  --el-button-bg-color: #FFFBEB;
  --el-button-hover-text-color: #FFFFFF;
  --el-button-hover-bg-color: #F59E0B;
  --el-button-hover-border-color: #F59E0B;
  --el-button-active-text-color: #FFFFFF;
  --el-button-active-bg-color: #D97706;
  --el-button-active-border-color: #D97706;
}

.cd-rec-btn--loss {
  --el-button-text-color: #475569;
  --el-button-border-color: #CBD5E1;
  --el-button-bg-color: #F8FAFC;
  --el-button-hover-text-color: #FFFFFF;
  --el-button-hover-bg-color: #64748B;
  --el-button-hover-border-color: #64748B;
  --el-button-active-text-color: #FFFFFF;
  --el-button-active-bg-color: #475569;
  --el-button-active-border-color: #475569;
}

.cd-rec-btn--damaged {
  --el-button-text-color: #DC2626;
  --el-button-border-color: #FCA5A5;
  --el-button-bg-color: #FEF2F2;
  --el-button-hover-text-color: #FFFFFF;
  --el-button-hover-bg-color: #DC2626;
  --el-button-hover-border-color: #DC2626;
  --el-button-active-text-color: #FFFFFF;
  --el-button-active-bg-color: #B91C1C;
  --el-button-active-border-color: #B91C1C;
}
.cd-rec-loading { font-size: 12px; color: #999; padding: 4px 0; }
.cd-rec-empty { font-size: 12px; color: #ccc; padding: 4px 0; }
.cd-return-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fefce8;
  border-radius: 6px;
  font-size: 13px;
  color: #92400e;
}

/* ── 骨架屏 ── */
.wh-dashboard-skeleton {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}
.sk-kpi-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  flex-shrink: 0;
}
.sk-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  background: #fff;
  border: 1px solid #E8ECF0;
  border-radius: 16px;
}
.sk-card-line { height: 14px; border-radius: 6px; background: linear-gradient(90deg, #F1F5F9 25%, #E8ECF0 50%, #F1F5F9 75%); background-size: 200% 100%; animation: sk-shimmer 1.5s ease infinite; }
.sk-w30 { width: 30%; }
.sk-w40 { width: 40%; }
.sk-w55 { width: 55%; }
.sk-w60 { width: 60%; }
.sk-w70 { width: 70%; }
.sk-h32 { height: 32px; border-radius: 8px; }
.sk-body {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
}
.sk-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid #E8ECF0;
  border-radius: 16px;
}
.sk-panel-head { padding-bottom: 12px; border-bottom: 1px solid #F1F5F9; }
.sk-panel-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sk-line {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, #F1F5F9 25%, #E8ECF0 50%, #F1F5F9 75%);
  background-size: 200% 100%;
  animation: sk-shimmer 1.5s ease infinite;
}
.sk-row { padding: 8px 0; }
@keyframes sk-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>