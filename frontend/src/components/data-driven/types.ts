/**
 * 数据驱动组件共享类型定义
 */

/** 单元格控件类型 */
export type CellType =
  | 'text' // 纯文本（默认）
  | 'status' // 状态徽章
  | 'tag' // 标签
  | 'date' // 日期（只读时格式化显示，可编辑时日期选择器）
  | 'datetime' // 日期时间
  | 'link' // 链接
  | 'input' // 输入框
  | 'select' // 下拉选择
  | 'number' // 数字输入
  | 'textarea' // 多行文本
  | 'radio' // 单选组
  | 'checkbox' // 多选组
  | 'switch' // 开关

/** 数据源选项 */
export interface DataSourceOption {
  label: string
  value: string | number | boolean
  disabled?: boolean
}

/** 数据源配置（用于 select / radio / checkbox / tag 等的选项映射） */
export interface DataSource {
  /** label 对应的字段名，默认 'label' */
  labelKey?: string
  /** value 对应的字段名，默认 'value' */
  valueKey?: string
  /** 选项列表 */
  list: Record<string, any>[]
}

/** 表格列配置 */
export interface TableColumn {
  /** 字段名 */
  prop: string
  /** 列标题 */
  label: string
  /** 列宽 */
  width?: number | string
  /** 最小列宽 */
  minWidth?: number | string
  /** 对齐方式 */
  align?: 'left' | 'center' | 'right'
  /** 固定列 */
  fixed?: boolean | 'left' | 'right'
  /** 是否可排序 */
  sortable?: boolean
  /** 单元格类型 */
  cellType?: CellType
  /** 数据源（select/tag 等用于值映射） */
  dataSource?: DataSource
  /** 自定义格式化函数 */
  formatter?: (row: any, column: TableColumn, value: any, index: number) => string
  /** 自定义插槽名 */
  slot?: string
  /** 自定义表头插槽名 */
  headerSlot?: string
  /** 控件额外属性（透传给 el-input / el-select 等） */
  controlProps?: Record<string, any>
  /** 是否显示溢出提示，默认 true */
  showOverflowTooltip?: boolean
}

/** 表单字段配置 */
export interface FormField {
  /** 字段名 */
  prop: string
  /** 标签文本 */
  label: string
  /** 栅格宽度（1-24），默认 12（半行） */
  span?: number
  /** 控件类型 */
  cellType?: CellType
  /** 是否必填 */
  required?: boolean
  /** 校验规则 */
  rules?: any[]
  /** 默认值 */
  defaultValue?: any
  /** 占位提示 */
  placeholder?: string
  /** 数据源 */
  dataSource?: DataSource
  /** 是否显示（支持函数形式，接收 formData） */
  show?: boolean | ((formData: Record<string, any>) => boolean)
  /** 是否禁用（支持函数形式，接收 formData） */
  disabled?: boolean | ((formData: Record<string, any>) => boolean)
  /** 控件额外属性 */
  controlProps?: Record<string, any>
  /** el-form-item 额外属性 */
  formItemProps?: Record<string, any>
  /** el-col 额外属性 */
  colProps?: Record<string, any>
  /** 自定义插槽名（完全自定义控件内容） */
  slot?: string
  /** 值变化回调 */
  onChange?: (value: any, formData: Record<string, any>) => void
}

/** 分页配置 */
export interface PaginationConfig {
  page: number
  pageSize: number
  total: number
  pageSizes?: number[]
}

/** 数据列表请求结果 */
export interface DataListResult {
  list: any[]
  total: number
}

/** 查询字段配置（复用 FormField，默认 span 由 DataList 控制） */
export type QueryField = FormField

/** 重置模式 */
export type ClearType = 'default' | 'clear' | 'customize'

/** DataList 按钮配置 */
export interface BtnConfig {
  /** 显示哪些默认按钮，默认 ['query', 'reset'] */
  showBtns?: string[]
  /** 查询按钮列栅格宽度（1-24），默认 6 */
  btnSpan?: number
  /** 查询按钮列左侧偏移量（1-24），默认 18；span+offset=24 时按钮右对齐 */
  btnOffset?: number
  /** 查询按钮文字 */
  queryText?: string
  /** 重置按钮文字 */
  resetText?: string
  /** 查询按钮额外属性（透传给 el-button，如 disabled、type 等） */
  queryProps?: Record<string, any>
  /** 重置按钮额外属性 */
  resetProps?: Record<string, any>
  /** 重置模式：default=还原初始值，clear=全部置空，customize=使用 clearData 合并 */
  clearType?: ClearType
  /** customize 模式下的自定义重置数据 */
  clearData?: Record<string, any>
}
