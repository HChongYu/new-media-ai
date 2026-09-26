<template>
  <div class="content-list">
    <PageHeader title="内容管理" :actions="pageActions" @action="handlePageAction" />

    <Card>
      <DataList
        ref="dataListRef"
        :query-fields="queryFields"
        :columns="columns"
        :fetch-data="handleFetchData"
      >
        <!-- 内容标题列：可点击跳转 -->
        <template #title="{ row }">
          <el-link type="primary" @click="openWorkspace(row.id)">
            {{ row.title }}
          </el-link>
        </template>

        <!-- 操作列：根据状态给出下一步主动作，统一进入内容工作台 -->
        <template #actions="{ row }">
          <el-button type="primary" link @click="openWorkspace(row.id)">查看</el-button>
          <el-button
            v-if="getNextAction(row.status)"
            :type="getNextAction(row.status)!.type"
            link
            @click="openWorkspace(row.id, getNextAction(row.status)!.step)"
          >
            {{ getNextAction(row.status)!.label }}
          </el-button>
          <el-button type="danger" link @click="deleteContent(row.id)">删除</el-button>
        </template>
      </DataList>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { DataList } from '@components/data-driven'
import type { FormField, TableColumn, DataListResult } from '@components/data-driven'
import { contentApi } from '@services/api'

const router = useRouter()
const dataListRef = ref()

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
        { label: '审核中', value: 'reviewing' },
        { label: '已通过', value: 'approved' },
        { label: '已驳回', value: 'rejected' },
        { label: '已发布', value: 'published' },
      ],
    },
  },
  {
    prop: 'content_type',
    label: '类型',
    cellType: 'select',
    span: 10,
    dataSource: {
      list: [
        { label: '文章', value: 'article' },
        { label: '图片', value: 'image' },
      ],
    },
  },
  {
    prop: 'keyword',
    label: '关键词',
    cellType: 'input',
    span: 10,
    placeholder: '标题/内容',
  },
]

// ---- 表格列配置 ----
const columns: TableColumn[] = [
  { prop: 'title', label: '内容标题', minWidth: 200, slot: 'title' },
  { prop: 'topic_title', label: '关联选题', minWidth: 150 },
  {
    prop: 'content_type',
    label: '类型',
    width: 100,
    cellType: 'tag',
    dataSource: {
      list: [
        { label: '文章', value: 'article' },
        { label: '图片', value: 'image' },
      ],
    },
  },
  { prop: 'status', label: '状态', width: 100, cellType: 'status' },
  { prop: 'word_count', label: '字数', width: 80 },
  { prop: 'created_by_name', label: '创建人', width: 100 },
  {
    prop: 'created_at',
    label: '创建时间',
    width: 160,
    sortable: true,
    formatter: (_row, _col, value) => formatDateTime(value),
  },
  { prop: 'actions', label: '操作', width: 200, fixed: 'right', slot: 'actions' },
]

// ---- 页头操作按钮 ----
const pageActions: PageAction[] = [
  { label: '创建内容', type: 'primary', icon: 'Plus', key: 'create' },
]

// ---- 日期格式化 ----
function formatDateTime(value: string): string {
  if (!value) return ''
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ---- 数据加载回调 ----
async function handleFetchData(params: Record<string, any>): Promise<DataListResult> {
  const result: any = await contentApi.list({
    ...params,
    page_size: params.pageSize,
  })
  return {
    list: result?.data?.items || [],
    total: result?.data?.total || 0,
  }
}

// ---- 页头按钮事件 ----
function handlePageAction(action: PageAction) {
  if (action.key === 'create') {
    router.push('/content/create')
  }
}

// ---- 表格事件 ----
/** 按内容状态给出「下一步」主动作，全部汇入内容工作台 */
function getNextAction(status: string): { label: string; type: string; step: string } | null {
  switch (status) {
    case 'draft':
    case 'rejected':
      return { label: '继续完善', type: 'primary', step: 'content' }
    case 'reviewing':
      return { label: '去审核', type: 'warning', step: 'review' }
    case 'approved':
      return { label: '去发布', type: 'success', step: 'publish' }
    case 'published':
      return { label: '发布详情', type: 'success', step: 'publish' }
    default:
      return null
  }
}

function openWorkspace(id: number, step?: string) {
  router.push(step ? `/content/detail/${id}?step=${step}` : `/content/detail/${id}`)
}

async function deleteContent(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这个内容吗？', '警告', {
      type: 'warning',
    })
    await contentApi.delete(id)
    ElMessage.success('删除成功')
    dataListRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete content:', error)
    }
  }
}
</script>

<style scoped>
.content-list {
  padding: 20px;
}
</style>
