<template>
  <div class="data-list">
    <!-- 查询表单区域 -->
    <div v-if="showQuery && queryFields.length" class="data-list__query">
      <DataForm ref="queryFormRef" v-model="queryData" :fields="queryFields" :inline="false"
        :label-width="queryLabelWidth">
        <!-- 查询按钮：作为表单栅格最后一行，通过 span+offset 右对齐 -->
        <template #actions>
          <el-col :span="btn.btnSpan" :offset="btn.btnOffset" class="data-list__query-actions">
            <!-- 查询按钮 -->
            <el-button v-if="btn.showBtns.includes('query')" type="primary" :loading="queryLoading"
              :disabled="queryBtnDisabled" v-bind="btn.queryProps" @click="handleQuery">
              <el-icon v-if="!queryLoading">
                <Search />
              </el-icon>
              <span>{{ btn.queryText }}</span>
            </el-button>
            <!-- 重置按钮 -->
            <el-button v-if="btn.showBtns.includes('reset')" :disabled="resetBtnDisabled" v-bind="btn.resetProps"
              @click="handleReset">
              {{ btn.resetText }}
            </el-button>
            <!-- 额外按钮插槽 -->
            <slot name="query-extra" />
          </el-col>
        </template>
      </DataForm>
    </div>

    <!-- 工具栏插槽 -->
    <div v-if="$slots.toolbar" class="data-list__toolbar">
      <slot name="toolbar" />
    </div>

    <!-- 表格区域 -->
    <DataTable ref="dataTableRef" :data="tableData" :columns="columns" :loading="loading" v-bind="$attrs"
      @cell-click="(payload: any) => $emit('cell-click', payload)">
      <!-- 透传所有插槽 -->
      <template v-for="(_, name) in $slots" #[name]="slotData" :key="name">
        <slot :name="name" v-bind="slotData ?? {}" />
      </template>
    </DataTable>

    <!-- 分页区域 -->
    <div v-if="showPagination" class="data-list__pagination">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
        :total="pagination.total" :page-sizes="pageSizes" layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange" @current-change="handlePageChange" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import DataForm from './DataForm.vue'
import DataTable from './DataTable.vue'
import type { FormField, TableColumn, DataListResult, BtnConfig } from './types'

defineOptions({
  name: 'DataList',
  inheritAttrs: false,
})

const props = withDefaults(
  defineProps<{
    /** 查询字段配置 */
    queryFields?: FormField[]
    /** 表格列配置 */
    columns: TableColumn[]
    /**
     * 数据获取回调
     * 接收 { page, pageSize, ...queryData }，返回 { list, total }
     */
    fetchData: (params: Record<string, any>) => Promise<DataListResult>
    /** 是否显示查询区域 */
    showQuery?: boolean
    /** 是否显示分页 */
    showPagination?: boolean
    /** 是否挂载时自动加载 */
    autoFetch?: boolean
    /** 查询表单 label 宽度 */
    queryLabelWidth?: string | number
    /** 分页大小选项 */
    pageSizes?: number[]
    /** 默认每页条数 */
    defaultPageSize?: number
    /** 按钮配置 */
    btnConfig?: BtnConfig
  }>(),
  {
    queryFields: () => [],
    showQuery: true,
    showPagination: true,
    autoFetch: true,
    queryLabelWidth: '80px',
    pageSizes: () => [10, 20, 50, 100],
    defaultPageSize: 10,
    btnConfig: () => ({}),
  }
)

defineEmits<{
  'cell-click': [payload: { row: any; prop: string; value: any }]
}>()

// ---- 按钮配置（合并默认值） ----
const btn = computed(() => ({
  showBtns: props.btnConfig.showBtns ?? ['query', 'reset'],
  btnSpan: props.btnConfig.btnSpan ?? 6,
  btnOffset: props.btnConfig.btnOffset ?? 18,
  queryText: props.btnConfig.queryText ?? '查询',
  resetText: props.btnConfig.resetText ?? '重置',
  queryProps: props.btnConfig.queryProps ?? {},
  resetProps: props.btnConfig.resetProps ?? {},
  clearType: props.btnConfig.clearType ?? 'default',
  clearData: props.btnConfig.clearData ?? {},
}))

const queryFormRef = ref()
const dataTableRef = ref()
const loading = ref(false)
const queryLoading = ref(false)
const tableData = ref<any[]>([])

const queryData = reactive<Record<string, any>>({})

const pagination = reactive({
  page: 1,
  pageSize: props.defaultPageSize,
  total: 0,
})

// ---- 查询/重置按钮 disabled 状态 ----

/** 查询按钮是否禁用（loading 中禁用） */
const queryBtnDisabled = computed(() => queryLoading.value)

/** 重置按钮是否禁用（loading 中禁用） */
const resetBtnDisabled = computed(() => queryLoading.value)

// ---- 组装请求参数 ----

function buildParams(): Record<string, any> {
  return {
    page: pagination.page,
    pageSize: pagination.pageSize,
    ...queryData,
  }
}

// ---- 加载数据 ----

async function loadData() {
  loading.value = true
  queryLoading.value = true
  try {
    const params = buildParams()
    const result = await props.fetchData(params)
    tableData.value = result.list || []
    pagination.total = result.total || 0
  } catch (error) {
    console.error('[DataList] 加载数据失败:', error)
    tableData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
    queryLoading.value = false
  }
}

// ---- 查询按钮：先校验表单，通过后重置到第一页加载 ----

async function handleQuery() {
  if (queryFormRef.value) {
    const valid = await queryFormRef.value.validate()
    if (!valid) return
  }
  pagination.page = 1
  loadData()
}

// ---- 重置按钮：根据 clearType 执行不同清空策略 ----

function handleReset() {
  const { clearType, clearData } = btn.value
  if (clearType === 'default') {
    queryFormRef.value?.resetFields()
  } else if (clearType === 'clear') {
    Object.keys(queryData).forEach((key) => {
      queryData[key] = ''
    })
  } else if (clearType === 'customize') {
    Object.keys(queryData).forEach((key) => {
      if (key in clearData) {
        queryData[key] = clearData[key]
      } else {
        queryData[key] = ''
      }
    })
  }
  pagination.page = 1
  loadData()
}

// ---- 分页 ----

function handleSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadData()
}

function handlePageChange(page: number) {
  pagination.page = page
  loadData()
}

// ---- 暴露方法 ----

function refresh() {
  loadData()
}

function reload() {
  pagination.page = 1
  loadData()
}

onMounted(() => {
  if (props.autoFetch) {
    loadData()
  }
})

defineExpose({
  queryFormRef,
  dataTableRef,
  loading,
  queryLoading,
  tableData,
  queryData,
  pagination,
  loadData,
  refresh,
  reload,
})
</script>

<style scoped>
.data-list__query {
  margin-bottom: 16px;
}

.data-list__query-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-end;
}

.data-list__toolbar {
  margin-bottom: 12px;
}

.data-list__pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
