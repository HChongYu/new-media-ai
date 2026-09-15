<template>
  <div class="publish-history">
    <PageHeader title="发布记录" />

    <Card>
      <DataList
        ref="dataListRef"
        :query-fields="queryFields"
        :columns="columns"
        :fetch-data="handleFetchData"
      >
        <!-- 发布链接列 -->
        <template #post_url="{ row }">
          <el-link v-if="row.post_url" :href="row.post_url" target="_blank" type="primary">
            查看原文
          </el-link>
          <span v-else>-</span>
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <el-button v-if="row.post_url" type="primary" link @click="viewPost(row.post_url)">
            查看
          </el-button>
          <el-button v-if="row.status === 'failed'" type="warning" link @click="retryPublish(row)">
            重试
          </el-button>
        </template>
      </DataList>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { DataList } from '@components/data-driven'
import type { FormField, TableColumn, DataListResult } from '@components/data-driven'
import { publishApi } from '@services/api'

const dataListRef = ref()

// ---- 查询字段配置 ----
const queryFields: FormField[] = [
  {
    prop: 'platform',
    label: '平台',
    cellType: 'select',
    span: 10,
    dataSource: {
      list: [
        { label: '小红书', value: 'xiaohongshu' },
        { label: '微信公众号', value: 'wechat' },
      ],
    },
  },
  {
    prop: 'status',
    label: '状态',
    cellType: 'select',
    span: 10,
    dataSource: {
      list: [
        { label: '待发布', value: 'pending' },
        { label: '已发布', value: 'published' },
        { label: '发布失败', value: 'failed' },
      ],
    },
  },
]

// ---- 表格列配置 ----
const columns: TableColumn[] = [
  { prop: 'content_title', label: '内容标题', minWidth: 200 },
  {
    prop: 'platform',
    label: '发布平台',
    width: 120,
    cellType: 'tag',
    dataSource: {
      list: [
        { label: '小红书', value: 'xiaohongshu' },
        { label: '微信公众号', value: 'wechat' },
      ],
    },
  },
  { prop: 'status', label: '状态', width: 100, cellType: 'status' },
  { prop: 'post_url', label: '发布链接', minWidth: 200, slot: 'post_url' },
  {
    prop: 'published_at',
    label: '发布时间',
    width: 160,
    formatter: (_row, _col, value) => (value ? formatDateTime(value) : '-'),
  },
  {
    prop: 'created_at',
    label: '创建时间',
    width: 160,
    sortable: true,
    formatter: (_row, _col, value) => formatDateTime(value),
  },
  { prop: 'actions', label: '操作', width: 120, fixed: 'right', slot: 'actions' },
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
  const result: any = await publishApi.history(params)
  return {
    list: result?.data?.list || [],
    total: result?.data?.pagination?.total || 0,
  }
}

// ---- 表格事件 ----
function viewPost(url: string) {
  window.open(url, '_blank')
}

async function retryPublish(record: any) {
  try {
    await publishApi.create(record.content_id, record.platform)
    ElMessage.success('重新发布成功')
    dataListRef.value?.refresh()
  } catch (error) {
    console.error('Failed to retry publish:', error)
    ElMessage.error('重新发布失败')
  }
}
</script>

<style scoped>
.publish-history {
  padding: 20px;
}
</style>
