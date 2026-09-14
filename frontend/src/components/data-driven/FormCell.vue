<template>
  <!-- 自定义插槽 -->
  <slot
    v-if="field.slot"
    :name="field.slot"
    :field="field"
    :form-data="formData"
  />

  <!-- 只读模式 -->
  <span v-else-if="readOnly">
    {{ getDisplayText() }}
  </span>

  <!-- 输入框 -->
  <el-input
    v-else-if="cellType === 'input'"
    v-model="formData[field.prop]"
    :placeholder="field.placeholder || `请输入${field.label}`"
    :disabled="disabled"
    clearable
    v-bind="field.controlProps"
    @change="handleChange"
  />

  <!-- 多行文本 -->
  <el-input
    v-else-if="cellType === 'textarea'"
    v-model="formData[field.prop]"
    type="textarea"
    :rows="field.controlProps?.rows || 4"
    :placeholder="field.placeholder || `请输入${field.label}`"
    :disabled="disabled"
    clearable
    v-bind="field.controlProps"
    @change="handleChange"
  />

  <!-- 下拉选择 -->
  <el-select
    v-else-if="cellType === 'select'"
    v-model="formData[field.prop]"
    :placeholder="field.placeholder || `请选择${field.label}`"
    :disabled="disabled"
    clearable
    v-bind="field.controlProps"
    @change="handleChange"
  >
    <el-option
      v-for="opt in dataSourceList"
      :key="opt[valueKey]"
      :label="opt[labelKey]"
      :value="opt[valueKey]"
      :disabled="opt.disabled"
    />
  </el-select>

  <!-- 数字输入 -->
  <el-input-number
    v-else-if="cellType === 'number'"
    v-model="formData[field.prop]"
    :disabled="disabled"
    v-bind="field.controlProps"
    @change="handleChange"
  />

  <!-- 日期选择 -->
  <el-date-picker
    v-else-if="cellType === 'date'"
    v-model="formData[field.prop]"
    type="date"
    value-format="YYYY-MM-DD"
    :placeholder="field.placeholder || `请选择${field.label}`"
    :disabled="disabled"
    v-bind="field.controlProps"
    @change="handleChange"
  />

  <!-- 日期时间选择 -->
  <el-date-picker
    v-else-if="cellType === 'datetime'"
    v-model="formData[field.prop]"
    type="datetime"
    value-format="YYYY-MM-DD HH:mm:ss"
    :placeholder="field.placeholder || `请选择${field.label}`"
    :disabled="disabled"
    v-bind="field.controlProps"
    @change="handleChange"
  />

  <!-- 单选组 -->
  <el-radio-group
    v-else-if="cellType === 'radio'"
    v-model="formData[field.prop]"
    :disabled="disabled"
    v-bind="field.controlProps"
    @change="handleChange"
  >
    <el-radio
      v-for="opt in dataSourceList"
      :key="opt[valueKey]"
      :value="opt[valueKey]"
    >
      {{ opt[labelKey] }}
    </el-radio>
  </el-radio-group>

  <!-- 多选组 -->
  <el-checkbox-group
    v-else-if="cellType === 'checkbox'"
    v-model="formData[field.prop]"
    :disabled="disabled"
    v-bind="field.controlProps"
    @change="handleChange"
  >
    <el-checkbox
      v-for="opt in dataSourceList"
      :key="opt[valueKey]"
      :value="opt[valueKey]"
    >
      {{ opt[labelKey] }}
    </el-checkbox>
  </el-checkbox-group>

  <!-- 开关 -->
  <el-switch
    v-else-if="cellType === 'switch'"
    v-model="formData[field.prop]"
    :disabled="disabled"
    v-bind="field.controlProps"
    @change="handleChange"
  />

  <!-- 标签 -->
  <el-tag
    v-else-if="cellType === 'tag'"
    :type="getTagType(formData[field.prop])"
    size="small"
  >
    {{ getDisplayText() }}
  </el-tag>

  <!-- 默认：纯文本 -->
  <span v-else>
    {{ getDisplayText() }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormField, CellType } from './types'

defineOptions({ name: 'FormCell' })

const props = withDefaults(
  defineProps<{
    field: FormField
    formData: Record<string, any>
    disabled?: boolean
    readOnly?: boolean
  }>(),
  {
    disabled: false,
    readOnly: false,
  }
)

const emit = defineEmits<{
  change: [value: any]
}>()

/** 计算实际控件类型（只读模式降级为 text） */
const cellType = computed<CellType | undefined>(() => {
  if (props.readOnly) return 'text'
  return props.field.cellType || 'input'
})

/** 数据源列表 */
const dataSourceList = computed(() => props.field.dataSource?.list || [])

/** value 字段名 */
const valueKey = computed(() => props.field.dataSource?.valueKey || 'value')

/** label 字段名 */
const labelKey = computed(() => props.field.dataSource?.labelKey || 'label')

/** 将值通过 dataSource 映射为可读文本 */
function getDisplayText(): string {
  const value = props.formData[props.field.prop]
  if (value === null || value === undefined || value === '') return ''

  const ds = props.field.dataSource
  if (!ds || !ds.list || ds.list.length === 0) {
    if (props.field.cellType === 'date') return formatDate(value, 'date')
    if (props.field.cellType === 'datetime') return formatDate(value, 'datetime')
    return String(value)
  }

  if (Array.isArray(value)) {
    return value
      .map((v) => {
        const matched = ds.list.find((item: any) => item[valueKey.value] === v)
        return matched ? String(matched[labelKey.value]) : String(v)
      })
      .join(', ')
  }

  const matched = ds.list.find((item: any) => item[valueKey.value] === value)
  return matched ? String(matched[labelKey.value]) : String(value)
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

/** 根据 status 值返回 el-tag type */
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

/** 值变化处理 */
function handleChange(val: any) {
  emit('change', val)
}
</script>
