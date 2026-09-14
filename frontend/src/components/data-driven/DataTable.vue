<template>
  <el-table
    ref="tableRef"
    :data="data"
    v-loading="loading"
    stripe
    border
    v-bind="$attrs"
  >
    <el-table-column
      v-for="col in columns"
      :key="col.prop"
      :prop="col.prop"
      :label="col.label"
      :width="col.width"
      :min-width="col.minWidth"
      :align="col.align || 'center'"
      :fixed="col.fixed"
      :sortable="col.sortable"
      :show-overflow-tooltip="col.showOverflowTooltip !== false"
    >
      <template #default="scope">
        <!-- 1. 自定义插槽 -->
        <slot
          v-if="col.slot"
          :name="col.slot"
          :row="scope.row"
          :index="scope.$index"
          :column="col"
        />

        <!-- 2. 自定义格式化函数 -->
        <span v-else-if="col.formatter">
          {{ col.formatter(scope.row, col, scope.row[col.prop], scope.$index) }}
        </span>

        <!-- 3. 状态徽章 -->
        <StatusBadge
          v-else-if="col.cellType === 'status'"
          :status="scope.row[col.prop]"
        />

        <!-- 4. 标签 -->
        <el-tag
          v-else-if="col.cellType === 'tag'"
          :type="getTagType(scope.row[col.prop])"
          size="small"
        >
          {{ getDisplayText(scope.row[col.prop], col) }}
        </el-tag>

        <!-- 5. 链接 -->
        <el-link
          v-else-if="col.cellType === 'link'"
          type="primary"
          @click="$emit('cell-click', { row: scope.row, prop: col.prop, value: scope.row[col.prop] })"
        >
          {{ scope.row[col.prop] }}
        </el-link>

        <!-- 6. 日期（只读模式或不可编辑） -->
        <span v-else-if="(col.cellType === 'date' || col.cellType === 'datetime') && readOnly">
          {{ formatDate(scope.row[col.prop], col.cellType) }}
        </span>

        <!-- 7. 可编辑：日期选择器 -->
        <el-date-picker
          v-else-if="col.cellType === 'date'"
          v-model="scope.row[col.prop]"
          type="date"
          value-format="YYYY-MM-DD"
          size="small"
          v-bind="col.controlProps"
        />
        <el-date-picker
          v-else-if="col.cellType === 'datetime'"
          v-model="scope.row[col.prop]"
          type="datetime"
          value-format="YYYY-MM-DD HH:mm:ss"
          size="small"
          v-bind="col.controlProps"
        />

        <!-- 8. 可编辑：下拉选择 -->
        <el-select
          v-else-if="col.cellType === 'select' && !readOnly"
          v-model="scope.row[col.prop]"
          size="small"
          v-bind="col.controlProps"
        >
          <el-option
            v-for="opt in getDataSourceList(col)"
            :key="opt[getValueKey(col)]"
            :label="opt[getLabelKey(col)]"
            :value="opt[getValueKey(col)]"
          />
        </el-select>

        <!-- 9. 可编辑：数字输入 -->
        <el-input-number
          v-else-if="col.cellType === 'number' && !readOnly"
          v-model="scope.row[col.prop]"
          size="small"
          v-bind="col.controlProps"
        />

        <!-- 10. 可编辑：多行文本 -->
        <el-input
          v-else-if="col.cellType === 'textarea' && !readOnly"
          v-model="scope.row[col.prop]"
          type="textarea"
          :rows="col.controlProps?.rows || 2"
          size="small"
          v-bind="col.controlProps"
        />

        <!-- 11. 可编辑：输入框 -->
        <el-input
          v-else-if="col.cellType === 'input' && !readOnly"
          v-model="scope.row[col.prop]"
          size="small"
          v-bind="col.controlProps"
        />

        <!-- 12. 只读模式下的可编辑控件降级为文本 -->
        <span v-else-if="col.cellType && readOnly">
          {{ getDisplayText(scope.row[col.prop], col) }}
        </span>

        <!-- 13. 默认：纯文本（支持 dataSource 映射） -->
        <span v-else>
          {{ getDisplayText(scope.row[col.prop], col) }}
        </span>
      </template>

      <!-- 自定义表头 -->
      <template v-if="col.headerSlot" #header="scope">
        <slot :name="col.headerSlot" v-bind="scope" />
      </template>
    </el-table-column>

    <!-- 空数据插槽 -->
    <template #empty>
      <slot name="empty">
        <el-empty description="暂无数据" />
      </slot>
    </template>
  </el-table>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import StatusBadge from '@components/StatusBadge.vue'
import type { TableColumn } from './types'

defineOptions({
  name: 'DataTable',
  inheritAttrs: false,
})

withDefaults(
  defineProps<{
    data: any[]
    columns: TableColumn[]
    loading?: boolean
    readOnly?: boolean
  }>(),
  {
    loading: false,
    readOnly: false,
  }
)

defineEmits<{
  'cell-click': [payload: { row: any; prop: string; value: any }]
}>()

const tableRef = ref()

/** 获取数据源列表 */
function getDataSourceList(col: TableColumn): any[] {
  return col.dataSource?.list || []
}

/** 获取 value 字段名 */
function getValueKey(col: TableColumn): string {
  return col.dataSource?.valueKey || 'value'
}

/** 获取 label 字段名 */
function getLabelKey(col: TableColumn): string {
  return col.dataSource?.labelKey || 'label'
}

/**
 * 根据 dataSource 将 value 映射为可读文本
 * 用于 select / tag 等控件的值显示
 */
function getDisplayText(value: any, col: TableColumn): string {
  if (value === null || value === undefined || value === '') return ''

  const ds = col.dataSource
  if (!ds || !ds.list || ds.list.length === 0) return String(value)

  const valueKey = getValueKey(col)
  const labelKey = getLabelKey(col)
  const matched = ds.list.find((item: any) => item[valueKey] === value)
  return matched ? String(matched[labelKey]) : String(value)
}

/** 日期格式化 */
function formatDate(value: any, type: string): string {
  if (!value) return ''
  const d = new Date(value)
  if (isNaN(d.getTime())) return String(value)

  const pad = (n: number) => String(n).padStart(2, '0')
  const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  if (type === 'datetime') {
    return `${date} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  return date
}

/** 根据 status 值返回 el-tag 的 type */
function getTagType(value: any): '' | 'success' | 'warning' | 'danger' | 'info' {
  const tagTypeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    reviewing: '',
    published: 'success',
    failed: 'danger',
  }
  return tagTypeMap[value] || ''
}

// 暴露 el-table 实例方法
defineExpose({
  tableRef,
  toggleRowSelection: (row: any, selected?: boolean) => {
    tableRef.value?.toggleRowSelection(row, selected)
  },
  clearSelection: () => {
    tableRef.value?.clearSelection()
  },
  toggleAllSelection: () => {
    tableRef.value?.toggleAllSelection()
  },
})
</script>
