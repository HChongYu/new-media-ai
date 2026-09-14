<template>
  <el-form
    ref="formRef"
    :model="formData"
    :label-width="labelWidth"
    :disabled="disabled"
    :inline="inline"
    v-bind="$attrs"
  >
    <!-- 网格布局：el-row > el-col > el-form-item > FormCell -->
    <el-row v-if="!inline" :gutter="gutter">
      <el-col
        v-for="field in visibleFields"
        :key="field.prop"
        :span="field.span || defaultSpan"
        v-bind="field.colProps"
      >
        <el-form-item
          :label="field.label"
          :prop="field.prop"
          :rules="getRules(field)"
          v-bind="field.formItemProps"
        >
          <FormCell
            :field="field"
            :form-data="formData"
            :disabled="isFieldDisabled(field)"
            :read-only="readOnly"
            @change="(val: any) => handleFieldChange(field, val)"
          />
        </el-form-item>
      </el-col>
      <!-- 操作按钮区域（插入到栅格布局末尾，通过 offset 右对齐） -->
      <slot name="actions" :form-data="formData" />
    </el-row>

    <!-- 行内布局：el-form-item > FormCell -->
    <template v-else>
      <el-form-item
        v-for="field in visibleFields"
        :key="field.prop"
        :label="field.label"
        :prop="field.prop"
        :rules="getRules(field)"
        v-bind="field.formItemProps"
      >
        <FormCell
          :field="field"
          :form-data="formData"
          :disabled="isFieldDisabled(field)"
          :read-only="readOnly"
          @change="(val: any) => handleFieldChange(field, val)"
        />
      </el-form-item>
      <!-- 行内模式下的操作按钮 -->
      <el-form-item v-if="$slots.actions">
        <slot name="actions" :form-data="formData" />
      </el-form-item>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import FormCell from './FormCell.vue'
import type { FormField, CellType } from './types'

defineOptions({
  name: 'DataForm',
  inheritAttrs: false,
})

const props = withDefaults(
  defineProps<{
    /** 表单数据（v-model） */
    modelValue?: Record<string, any>
    /** 字段配置列表 */
    fields: FormField[]
    /** 标签宽度 */
    labelWidth?: string | number
    /** 栅格间距 */
    gutter?: number
    /** 默认栅格宽度（1-24） */
    defaultSpan?: number
    /** 禁用全部控件 */
    disabled?: boolean
    /** 只读模式（所有控件降级为文本） */
    readOnly?: boolean
    /** 行内表单模式 */
    inline?: boolean
  }>(),
  {
    modelValue: () => ({}),
    labelWidth: '100px',
    gutter: 20,
    defaultSpan: 12,
    disabled: false,
    readOnly: false,
    inline: false,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
  change: [value: Record<string, any>]
}>()

const formRef = ref()

// ---- 内部表单数据（响应式副本） ----
const formData = reactive<Record<string, any>>({})

/** 同步标记：防止双向同步导致的无限循环 */
let syncing = false

/** 根据控件类型返回默认空值 */
function getDefaultForType(cellType?: CellType): any {
  switch (cellType) {
    case 'checkbox':
      return []
    case 'switch':
      return false
    case 'number':
      return 0
    default:
      return ''
  }
}

/** 初始化字段默认值 */
function initDefaults() {
  const source = props.modelValue || {}
  props.fields.forEach((field) => {
    if (field.prop in source && source[field.prop] !== undefined) {
      formData[field.prop] = source[field.prop]
    } else if (field.defaultValue !== undefined) {
      formData[field.prop] = field.defaultValue
    } else {
      formData[field.prop] = getDefaultForType(field.cellType)
    }
  })
}

// 监听外部 modelValue 变化，同步到内部
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      syncing = true
      Object.keys(formData).forEach((key) => delete formData[key])
      Object.assign(formData, val)
      initDefaults()
      nextTick(() => {
        syncing = false
      })
    }
  },
  { immediate: true, deep: true }
)

// 监听内部变化，同步到外部
watch(
  formData,
  () => {
    if (!syncing) {
      emit('update:modelValue', { ...formData })
      emit('change', { ...formData })
    }
  },
  { deep: true }
)

// ---- 可见字段（支持条件渲染） ----
const visibleFields = computed(() => {
  return props.fields.filter((field) => {
    if (field.show === undefined) return true
    if (typeof field.show === 'function') return field.show(formData)
    return field.show
  })
})

// ---- 工具方法 ----

/** 判断字段是否禁用 */
function isFieldDisabled(field: FormField): boolean {
  if (props.disabled) return true
  if (field.disabled === undefined) return false
  if (typeof field.disabled === 'function') return field.disabled(formData)
  return field.disabled
}

/** 获取校验规则（自动生成 required 规则） */
function getRules(field: FormField): any[] {
  if (field.rules) return field.rules
  if (!field.required) return []

  const selectTypes: CellType[] = ['select', 'date', 'datetime', 'radio', 'checkbox']
  const isSelectType = field.cellType ? selectTypes.includes(field.cellType) : false
  return [
    {
      required: true,
      message: isSelectType ? `请选择${field.label}` : `请输入${field.label}`,
      trigger: isSelectType ? 'change' : 'blur',
    },
  ]
}

/** 字段值变化回调 */
function handleFieldChange(field: FormField, value: any) {
  if (field.onChange) {
    field.onChange(value, formData)
  }
}

// ---- 暴露的方法 ----

/** 校验表单，返回 Promise<boolean> */
async function validate(): Promise<boolean> {
  try {
    await formRef.value?.validate()
    return true
  } catch {
    return false
  }
}

/** 获取表单数据 */
function getFormData(): Record<string, any> {
  return { ...formData }
}

/** 设置表单数据（合并） */
function setFormData(data: Record<string, any>) {
  syncing = true
  Object.assign(formData, data)
  nextTick(() => {
    syncing = false
  })
}

/** 重置表单（调用 el-form 的 resetFields） */
function resetFields() {
  formRef.value?.resetFields()
}

/** 清空表单（所有字段设为默认值） */
function clearFields() {
  syncing = true
  props.fields.forEach((field) => {
    formData[field.prop] = field.defaultValue ?? getDefaultForType(field.cellType)
  })
  nextTick(() => {
    syncing = false
    formRef.value?.clearValidate()
  })
}

defineExpose({
  formRef,
  validate,
  getFormData,
  setFormData,
  resetFields,
  clearFields,
})
</script>
