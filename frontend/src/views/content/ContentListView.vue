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
          <el-link type="primary" @click="viewContent(row.id)">
            {{ row.title }}
          </el-link>
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <el-button type="primary" link @click="viewContent(row.id)">查看</el-button>
          <el-button v-if="row.status === 'draft'" type="primary" link @click="editContent(row.id)">编辑</el-button>
          <el-button v-if="row.status === 'approved'" type="success" link @click="reviewContent(row.id)">审核</el-button>
          <el-button type="danger" link @click="deleteContent(row.id)">删除</el-button>
        </template>
      </DataList>
    </Card>

    <!-- 批量生成内容对话框 -->
    <el-dialog v-model="batchGenerateDialog.visible" title="批量生成内容" width="500px">
      <el-form :model="batchGenerateDialog.form" label-width="100px">
        <el-form-item label="选择选题" required>
          <el-select
            v-model="batchGenerateDialog.form.topic_id"
            placeholder="请选择选题"
            filterable
            style="width: 100%;"
          >
            <el-option
              v-for="topic in batchTopics"
              :key="topic.id"
              :label="topic.title"
              :value="topic.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容类型">
          <el-radio-group v-model="batchGenerateDialog.form.content_type">
            <el-radio value="article">文章</el-radio>
            <el-radio value="image">图片</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="发布平台">
          <el-select v-model="batchGenerateDialog.form.platform" placeholder="请选择平台">
            <el-option label="小红书" value="xiaohongshu" />
            <el-option label="微信公众号" value="wechat" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容风格">
          <el-select v-model="batchGenerateDialog.form.tone" placeholder="请选择风格">
            <el-option label="专业严谨" value="professional" />
            <el-option label="轻松活泼" value="casual" />
            <el-option label="热情洋溢" value="enthusiastic" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容长度">
          <el-select v-model="batchGenerateDialog.form.length" placeholder="请选择长度">
            <el-option label="短篇 (500字以内)" value="short" />
            <el-option label="中篇 (500-1500字)" value="medium" />
            <el-option label="长篇 (1500字以上)" value="long" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchGenerateDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="batchGenerateDialog.loading" @click="confirmBatchGenerate">
          确定生成
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
import { DataList } from '@components/data-driven'
import type { FormField, TableColumn, DataListResult } from '@components/data-driven'
import { contentApi, topicApi } from '@services/api'

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
  { prop: 'actions', label: '操作', width: 180, fixed: 'right', slot: 'actions' },
]

// ---- 页头操作按钮 ----
const pageActions: PageAction[] = [
  { label: '创建内容', type: 'primary', icon: 'Plus', key: 'create' },
  { label: '批量生成', type: 'success', icon: 'LightBulb', key: 'batch-generate' },
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
  const result: any = await contentApi.list(params)
  return {
    list: result?.data?.list || [],
    total: result?.data?.pagination?.total || 0,
  }
}

// ---- 批量生成对话框 ----
const batchTopics = ref<any[]>([])
const batchGenerateDialog = reactive({
  visible: false,
  loading: false,
  form: {
    topic_id: null as number | null,
    content_type: 'article',
    platform: 'xiaohongshu',
    tone: 'professional',
    length: 'medium'
  }
})

// ---- 页头按钮事件 ----
function handlePageAction(action: PageAction) {
  if (action.key === 'create') {
    router.push('/content/create')
  } else if (action.key === 'batch-generate') {
    batchGenerateDialog.form = {
      topic_id: null,
      content_type: 'article',
      platform: 'xiaohongshu',
      tone: 'professional',
      length: 'medium'
    }
    fetchTopicsForBatch()
    batchGenerateDialog.visible = true
  }
}

// ---- 获取选题列表（批量生成用） ----
async function fetchTopicsForBatch() {
  try {
    const result: any = await topicApi.list({ page: 1, pageSize: 100 })
    batchTopics.value = result?.data?.list || result?.data?.items || []
  } catch (error) {
    console.error('Failed to fetch topics for batch:', error)
  }
}

// ---- 确认批量生成 ----
async function confirmBatchGenerate() {
  if (!batchGenerateDialog.form.topic_id) {
    ElMessage.warning('请先选择选题')
    return
  }

  batchGenerateDialog.loading = true
  try {
    await contentApi.generate(batchGenerateDialog.form.topic_id, {
      platform: batchGenerateDialog.form.platform as any,
      tone: batchGenerateDialog.form.tone as any,
      length: batchGenerateDialog.form.length as any
    })
    ElMessage.success('内容生成成功')
    batchGenerateDialog.visible = false
    dataListRef.value?.refresh()
  } catch (error) {
    console.error('批量生成内容失败:', error)
  } finally {
    batchGenerateDialog.loading = false
  }
}

// ---- 表格事件 ----
function viewContent(id: number) {
  router.push(`/content/detail/${id}`)
}

function editContent(id: number) {
  router.push(`/content/edit/${id}`)
}

function reviewContent(id: number) {
  router.push(`/content/review/${id}`)
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
