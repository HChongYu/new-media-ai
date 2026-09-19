<template>
  <div class="workflow-list" v-loading="loading">
    <PageHeader title="AI 图文工作台" :actions="headerActions" @action="onAction" />

    <Card>
      <template #actions>
        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          style="width: 150px;"
          @change="onFilterChange"
        >
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </template>

      <el-table
        :data="projects"
        style="width: 100%"
        @row-click="openProject"
        :row-class-name="rowClassName"
      >
        <el-table-column label="内容方向 / 最终选题" min-width="280">
          <template #default="{ row }">
            <div class="topic-cell">
              <div class="topic-direction">{{ row.topic_direction || '—' }}</div>
              <div v-if="row.topic" class="topic-selected">
                <el-icon><Promotion /></el-icon>
                <span>{{ row.topic }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="平台" width="100">
          <template #default="{ row }">
            <el-tag :type="row.platform === 'xiaohongshu' ? 'danger' : 'success'" effect="plain">
              {{ platformLabel(row.platform) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusMeta(row.status).type" effect="light">
              {{ statusMeta(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="修改次数" width="90" align="center">
          <template #default="{ row }">
            <el-text v-if="row.revision_count > 0" type="warning">{{ row.revision_count }}</el-text>
            <el-text v-else type="info">0</el-text>
          </template>
        </el-table-column>

        <el-table-column label="配图" width="80" align="center">
          <template #default="{ row }">
            <el-text v-if="row.image_assets?.length">{{ row.image_assets.length }} 张</el-text>
            <el-text v-else type="info">—</el-text>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="openProject(row)">
              {{ row.status === 'completed' ? '查看成果' : '继续处理' }}
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="还没有图文任务，点击右上角「新建图文任务」开始">
            <el-button type="primary" :icon="Plus" @click="goCreate">新建图文任务</el-button>
          </el-empty>
        </template>
      </el-table>

      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          background
          @current-change="paginate"
        />
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Promotion } from '@element-plus/icons-vue'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { workflowApi } from '@services/api'
import type { WorkflowProject, WorkflowProjectStatus } from '@services/api'

const router = useRouter()

const loading = ref(false)
const allProjects = ref<WorkflowProject[]>([])
const projects = ref<WorkflowProject[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const statusFilter = ref<WorkflowProjectStatus | ''>('')

const headerActions: PageAction[] = [
  { label: '新建图文任务', type: 'primary', icon: 'Plus', key: 'create' },
]

const statusOptions: { value: WorkflowProjectStatus; label: string }[] = [
  { value: 'awaiting_select', label: '待选选题' },
  { value: 'writing', label: '撰稿中' },
  { value: 'reviewing', label: '待审核' },
  { value: 'generating_images', label: '配图中' },
  { value: 'completed', label: '已完成' },
]

function statusMeta(status: string): { label: string; type: 'info' | 'warning' | 'primary' | 'success' } {
  const map: Record<string, { label: string; type: 'info' | 'warning' | 'primary' | 'success' }> = {
    awaiting_select: { label: '待选选题', type: 'warning' },
    writing: { label: '撰稿中', type: 'primary' },
    reviewing: { label: '待审核', type: 'warning' },
    generating_images: { label: '配图中', type: 'primary' },
    completed: { label: '已完成', type: 'success' },
  }
  return map[status] || { label: status, type: 'info' }
}

function platformLabel(platform: string): string {
  return platform === 'xiaohongshu' ? '小红书' : '公众号'
}

function rowClassName({ row }: { row: WorkflowProject }): string {
  return row.status === 'completed' ? 'row-completed' : 'row-active'
}

async function loadList() {
  loading.value = true
  try {
    // 后端列表按状态过滤、时间倒序返回，分页在前端完成
    const res: any = await workflowApi.list({
      page: 1,
      page_size: 100,
      status: statusFilter.value || undefined,
    })
    allProjects.value = res?.data || []
    total.value = allProjects.value.length
    paginate()
  } catch (error) {
    console.error('加载工作流列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

function paginate() {
  const start = (page.value - 1) * pageSize.value
  projects.value = allProjects.value.slice(start, start + pageSize.value)
}

function onFilterChange() {
  page.value = 1
  loadList()
}

function goCreate() {
  router.push('/workflows/studio')
}

function openProject(row: WorkflowProject) {
  router.push(`/workflows/studio/${row.thread_id}`)
}

function onAction(action: PageAction) {
  if (action.key === 'create') goCreate()
}

function formatDateTime(value?: string): string {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(loadList)
</script>

<style scoped>
.workflow-list {
  padding: 20px;
}

.topic-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.topic-direction {
  font-size: 14px;
  color: #1F2329;
  font-weight: 500;
}

.topic-selected {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #3370FF;
}

:deep(.el-table .row-active) {
  cursor: pointer;
}

:deep(.el-table .row-completed) {
  cursor: pointer;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
