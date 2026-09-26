<template>
  <div class="image-list">
    <PageHeader title="图片管理" />

    <Card>
      <DataList
        ref="dataListRef"
        :query-fields="queryFields"
        :columns="columns"
        :fetch-data="handleFetchData"
        :default-page-size="20"
        :page-sizes="[20, 50, 100]"
      >
        <!-- 图片预览列 -->
        <template #image_url="{ row }">
          <el-image
            :src="row.image_url"
            :preview-src-list="[row.image_url]"
            preview-teleported
            fit="cover"
            lazy
            style="width: 80px; height: 80px; border-radius: 4px;"
          />
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <el-button type="primary" link @click="viewImage(row)">查看</el-button>
          <el-button type="danger" link @click="deleteImage(row)">删除</el-button>
        </template>
      </DataList>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { DataList } from '@components/data-driven'
import type { FormField, TableColumn, DataListResult } from '@components/data-driven'
import { imageApi } from '@services/api'

const dataListRef = ref()

// ---- 查询字段配置 ----
const queryFields: FormField[] = [
  {
    prop: 'image_type',
    label: '图片类型',
    cellType: 'select',
    span: 10,
    dataSource: {
      list: [
        { label: '封面图', value: 'cover' },
        { label: '正文图', value: 'section' },
        { label: '摘要图', value: 'summary' },
      ],
    },
  },
  {
    prop: 'content_id',
    label: '内容ID',
    cellType: 'input',
    span: 10,
    placeholder: '内容ID',
  },
]

// ---- 表格列配置 ----
const columns: TableColumn[] = [
  { prop: 'image_url', label: '预览', width: 100, slot: 'image_url' },
  {
    prop: 'image_type',
    label: '类型',
    width: 100,
    cellType: 'tag',
    dataSource: {
      list: [
        { label: '封面图', value: 'cover' },
        { label: '正文图', value: 'section' },
        { label: '摘要图', value: 'summary' },
      ],
    },
  },
  { prop: 'content_id', label: '内容ID', width: 100 },
  { prop: 'prompt', label: '生成提示词', minWidth: 200, showOverflowTooltip: true },
  {
    prop: 'generated_at',
    label: '生成时间',
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
  const result: any = await imageApi.list({
    ...params,
    page_size: params.pageSize,
  })
  return {
    list: result?.data?.items || [],
    total: result?.data?.total || 0,
  }
}

// ---- 表格事件 ----
function viewImage(image: any) {
  window.open(image.image_url, '_blank')
}

async function deleteImage(image: any) {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？', '警告', {
      type: 'warning',
    })
    await imageApi.delete(image.id)
    ElMessage.success('删除成功')
    dataListRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete image:', error)
    }
  }
}
</script>

<style scoped>
.image-list {
  padding: 20px;
}
</style>
