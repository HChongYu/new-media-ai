<template>
  <div class="topic-list">
    <PageHeader title="选题管理" :actions="pageActions" @action="handlePageAction" />

    <Card>
      <DataList
        ref="dataListRef"
        :query-fields="queryFields"
        :columns="columns"
        :fetch-data="handleFetchData"
        @cell-click="handleCellClick"
      >
        <!-- 选题标题列：可点击跳转 -->
        <template #title="{ row }">
          <el-link type="primary" @click="viewTopic(row.id)">
            {{ row.title }}
          </el-link>
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <el-button type="primary" link @click="viewTopic(row.id)">查看</el-button>
          <el-button type="primary" link @click="editTopic(row.id)">编辑</el-button>
          <el-button type="danger" link @click="deleteTopic(row.id)">删除</el-button>
        </template>
      </DataList>
    </Card>

    <!-- 生成选题对话框 -->
    <el-dialog v-model="generateDialog.visible" title="生成选题" width="500px">
      <DataForm
        ref="generateFormRef"
        v-model="generateDialog.form"
        :fields="generateFields"
        label-width="100px"
      />
      <template #footer>
        <el-button @click="generateDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="generateDialog.loading" @click="confirmGenerate">
          确定生成
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建选题对话框 -->
    <el-dialog v-model="createDialog.visible" title="新建选题" width="500px">
      <DataForm
        ref="createFormRef"
        v-model="createDialog.form"
        :fields="createFields"
        label-width="100px"
      />
      <template #footer>
        <el-button @click="createDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="createDialog.loading" @click="confirmCreate">
          确定新建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { DataList, DataForm } from '@components/data-driven'
import type { FormField, TableColumn, DataListResult } from '@components/data-driven'
import { topicApi } from '@services/api'

const router = useRouter()
const dataListRef = ref()
const generateFormRef = ref()
const createFormRef = ref()

// ---- 查询字段配置 ----
const queryFields: FormField[] = [
  {
    prop: 'status',
    label: '状态',
    cellType: 'select',
    span: 10,
    dataSource: {
      list: [
        { label: '草稿', value: 'draft' },
        { label: '待审核', value: 'pending' },
        { label: '已通过', value: 'approved' },
        { label: '已拒绝', value: 'rejected' },
      ],
    },
  },
  {
    prop: 'keyword',
    label: '关键词',
    cellType: 'input',
    span: 10,
    placeholder: '选题标题',
  },
]

// ---- 表格列配置 ----
const columns: TableColumn[] = [
  { prop: 'title', label: '选题标题', minWidth: 200, slot: 'title' },
  { prop: 'status', label: '状态', width: 100, cellType: 'status' },
  { prop: 'content_count', label: '内容数', width: 80 },
  { prop: 'created_by_name', label: '创建人', width: 100 },
  {
    prop: 'created_at',
    label: '创建时间',
    width: 160,
    sortable: true,
    formatter: (_row, _col, value) => formatDateTime(value),
  },
  { prop: 'actions', label: '操作', width: 160, fixed: 'right', slot: 'actions' },
]

// ---- 页头操作按钮 ----
const pageActions: PageAction[] = [
  { label: '生成选题', type: 'primary', icon: 'LightBulb', key: 'generate' },
  { label: '新建选题', type: 'success', icon: 'Plus', key: 'create' },
]

// ---- 生成选题对话框 ----
const generateDialog = reactive({
  visible: false,
  loading: false,
  form: {} as Record<string, any>,
})

const generateFields: FormField[] = [
  {
    prop: 'keywords',
    label: '关键词',
    cellType: 'input',
    span: 24,
    required: true,
    placeholder: '多个关键词用逗号分隔',
    controlProps: { maxlength: 200, showWordLimit: true },
  },
  {
    prop: 'category',
    label: '分类',
    cellType: 'input',
    span: 24,
    placeholder: '如：科技、生活、教育',
  },
  {
    prop: 'target_audience',
    label: '目标受众',
    cellType: 'input',
    span: 24,
    placeholder: '如：年轻白领、宝妈',
  },
  {
    prop: 'count',
    label: '生成数量',
    cellType: 'number',
    span: 24,
    defaultValue: 5,
    controlProps: { min: 1, max: 20 },
  },
]

// ---- 新建选题对话框 ----
const createDialog = reactive({
  visible: false,
  loading: false,
  form: {} as Record<string, any>,
})

const createFields: FormField[] = [
  {
    prop: 'title',
    label: '选题标题',
    cellType: 'input',
    span: 24,
    required: true,
    placeholder: '请输入选题标题',
  },
  {
    prop: 'description',
    label: '选题描述',
    cellType: 'textarea',
    span: 24,
    required: true,
    placeholder: '请输入选题描述',
    controlProps: { rows: 4, maxlength: 500, showWordLimit: true },
  },
  {
    prop: 'category',
    label: '分类',
    cellType: 'input',
    span: 24,
    placeholder: '可选',
  },
]

// ---- 数据加载回调 ----
async function handleFetchData(params: Record<string, any>): Promise<DataListResult> {
  const result: any = await topicApi.list(params)
  return {
    list: result?.data?.items || [],
    total: result?.data?.pagination?.total || 0,
  }
}

// ---- 日期格式化 ----
function formatDateTime(value: string): string {
  if (!value) return ''
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ---- 页头按钮事件 ----
function handlePageAction(action: PageAction) {
  if (action.key === 'generate') {
    generateDialog.form = { count: 5 }
    generateDialog.visible = true
  } else if (action.key === 'create') {
    createDialog.form = {}
    createDialog.visible = true
  }
}

// ---- 确认生成选题 ----
async function confirmGenerate() {
  const valid = await generateFormRef.value?.validate()
  if (!valid) return

  generateDialog.loading = true
  try {
    // 将逗号分隔的关键词字符串转为数组
    const form = { ...generateDialog.form }
    if (typeof form.keywords === 'string') {
      form.keywords = form.keywords.split(',').map((k: string) => k.trim()).filter(Boolean)
    }
    await topicApi.generate(form)
    ElMessage.success('选题生成成功')
    generateDialog.visible = false
    dataListRef.value?.reload()
  } catch (error) {
    console.error('生成选题失败:', error)
  } finally {
    generateDialog.loading = false
  }
}

// ---- 确认新建选题 ----
async function confirmCreate() {
  const valid = await createFormRef.value?.validate()
  if (!valid) return

  createDialog.loading = true
  try {
    await topicApi.create(createDialog.form)
    ElMessage.success('新建选题成功')
    createDialog.visible = false
    dataListRef.value?.reload()
  } catch (error) {
    console.error('新建选题失败:', error)
  } finally {
    createDialog.loading = false
  }
}

// ---- 表格事件 ----

function handleCellClick(payload: { row: any; prop: string; value: any }) {
  console.log('cell-click:', payload)
}

function viewTopic(id: number) {
  router.push(`/topics/${id}`)
}

function editTopic(id: number) {
  router.push(`/topics/${id}/edit`)
}

async function deleteTopic(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这个选题吗？', '警告', {
      type: 'warning',
    })
    await topicApi.delete(id)
    ElMessage.success('删除成功')
    dataListRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete topic:', error)
    }
  }
}
</script>

<style scoped>
.topic-list {
  padding: 20px;
}
</style>
