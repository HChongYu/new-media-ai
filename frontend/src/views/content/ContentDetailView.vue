<template>
  <div class="content-detail">
    <BackButton />
    <PageHeader title="内容详情" :actions="pageActions" @action="handlePageAction" />

    <Card>
      <div class="content-info">
        <div class="info-item">
          <span class="label">创建人：</span>
          <span class="value">{{ content?.created_by_name || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="label">创建时间：</span>
          <span class="value">{{ formatDateTime(content?.created_at) }}</span>
        </div>
        <div class="info-item">
          <span class="label">字数：</span>
          <span class="value">{{ content?.word_count || 0 }} 字</span>
        </div>
        <div class="info-item">
          <span class="label">内容类型：</span>
          <span class="value">{{ content?.content_type === 'article' ? '文章' : '图片' }}</span>
        </div>
        <div class="info-item">
          <span class="label">状态：</span>
          <StatusBadge :status="content?.status" />
        </div>
      </div>

      <div class="content-body">
        <MarkdownViewer :content="content?.content_text || ''" />
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import StatusBadge from '@components/StatusBadge.vue'
import MarkdownViewer from '@components/MarkdownViewer.vue'
import { contentApi } from '@services/api'

const route = useRoute()
const router = useRouter()

const contentId = ref<number>(Number(route.params.id))
const content = ref<any>(null)

const pageActions: PageAction[] = [
  { label: '编辑', type: 'primary', icon: 'Edit', key: 'edit' },
  { label: '删除', type: 'danger', icon: 'Delete', key: 'delete' },
]

function formatDateTime(value: string): string {
  if (!value) return ''
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function fetchData() {
  try {
    const result: any = await contentApi.detail(contentId.value)
    if (result?.data) {
      content.value = result.data
    }
  } catch (error) {
    console.error('Failed to fetch content:', error)
    ElMessage.error('获取内容详情失败')
  }
}

function handlePageAction(action: PageAction) {
  if (action.key === 'edit') {
    router.push(`/content/edit/${contentId.value}`)
  } else if (action.key === 'delete') {
    deleteContent()
  }
}

async function deleteContent() {
  try {
    await ElMessageBox.confirm('确定要删除这个内容吗？', '警告', {
      type: 'warning',
    })
    await contentApi.delete(contentId.value)
    ElMessage.success('删除成功')
    router.push('/content')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete content:', error)
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.content-detail {
  padding: 20px;
}

.content-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  padding: 14px 16px;
  background: #F5F6F7;
  border-radius: 6px;
  border: 1px solid #EBEDF0;
}

.info-item {
  display: flex;
  gap: 6px;
  align-items: center;
}

.info-item .label {
  color: #8F959E;
  font-size: 13px;
}

.info-item .value {
  color: #1F2329;
  font-weight: 500;
  font-size: 13px;
}

.content-body {
  min-height: 400px;
}
</style>
