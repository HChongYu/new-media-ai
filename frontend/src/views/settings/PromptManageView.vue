<template>
  <div class="prompt-manage">
    <PageHeader title="提示词管理" />

    <Card title="提示词列表">
      <template #actions>
        <el-tag size="small" type="info">
          修改发布后实时生效，无需重启服务
        </el-tag>
      </template>

      <el-table :data="summaries" v-loading="loading" stripe>
        <el-table-column prop="name" label="提示词" min-width="180">
          <template #default="{ row }">
            <div class="prompt-name">{{ row.name }}</div>
            <div class="prompt-key">{{ row.key }}</div>
          </template>
        </el-table-column>
        <el-table-column label="最新版本" width="100">
          <template #default="{ row }">
            {{ row.latest_version ? `v${row.latest_version}` : '内置' }}
          </template>
        </el-table-column>
        <el-table-column label="当前生效" min-width="220">
          <template #default="{ row }">
            <template v-if="row.active.length">
              <el-tag
                v-for="item in row.active"
                :key="item.id"
                :type="item.variant === 'main' ? 'success' : 'warning'"
                size="small"
                class="variant-tag"
              >
                {{ item.variant === 'main' ? `主干 v${item.version}` : `变体${item.variant} v${item.version} · ${item.traffic_percent}%` }}
              </el-tag>
            </template>
            <span v-else class="prompt-key">代码内置兜底</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDrawer(row)">
              版本管理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </Card>

    <!-- 版本管理抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="`版本管理 · ${currentSummary?.name || ''}`"
      size="60%"
      destroy-on-close
    >
      <div class="drawer-toolbar">
        <el-tag v-if="currentSummary?.in_experiment" type="warning">
          A/B 实验进行中
        </el-tag>
        <div class="toolbar-spacer" />
        <el-button
          v-if="currentSummary?.in_experiment"
          type="warning"
          plain
          @click="handleStopExperiment"
        >
          停止实验
        </el-button>
        <el-button @click="openExperimentDialog">发起 A/B 实验</el-button>
        <el-button type="primary" @click="openCreateDialog">新建版本</el-button>
      </div>

      <el-table :data="versions" v-loading="versionLoading" row-key="id" stripe>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="content-preview">
              <pre>{{ row.content }}</pre>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="版本" width="80">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变体 / 流量" width="120">
          <template #default="{ row }">
            <span v-if="row.variant === 'main'">主干</span>
            <span v-else>变体 {{ row.variant }} · {{ row.traffic_percent }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="change_note" label="版本说明" min-width="160" show-overflow-tooltip />
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!(row.status === 'active' && row.variant === 'main')"
              type="primary"
              link
              @click="handleActivate(row)"
            >
              {{ row.status === 'archived' && row.version < (currentSummary?.latest_version || 0) ? '回滚' : '发布' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 新建版本 -->
    <el-dialog v-model="createDialogVisible" title="新建提示词版本" width="640px">
      <el-alert
        type="info"
        :closable="false"
        class="dialog-alert"
        title="已基于最新版本内容预填；{占位符} 必须保留，否则该节点无法渲染。"
      />
      <el-input
        v-model="createForm.change_note"
        placeholder="版本说明（如：强化小红书 emoji 风格）"
        class="dialog-field"
      />
      <el-input
        v-model="createForm.content"
        type="textarea"
        :rows="16"
        placeholder="提示词正文"
      />
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="handleCreate">
          保存为草稿
        </el-button>
      </template>
    </el-dialog>

    <!-- 发起 A/B 实验 -->
    <el-dialog v-model="experimentDialogVisible" title="发起 A/B 实验" width="480px">
      <el-alert
        type="info"
        :closable="false"
        class="dialog-alert"
        title="主干版本保持当前生效版本，其余流量按工作流 thread_id 哈希分配给变体，同一工作流始终命中同一版本。"
      />
      <el-form label-width="100px">
        <el-form-item label="实验变体版本">
          <el-select v-model="experimentForm.version" placeholder="选择一个版本">
            <el-option
              v-for="row in experimentCandidates"
              :key="row.id"
              :label="`v${row.version}${row.change_note ? ' · ' + row.change_note : ''}`"
              :value="row.version"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="变体流量占比">
          <el-input-number
            v-model="experimentForm.traffic_percent"
            :min="1"
            :max="99"
          />
          <span class="percent-hint">%（剩余 {{ 100 - experimentForm.traffic_percent }}% 走主干）</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="experimentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="handleStartExperiment">
          开启实验
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import {
  promptApi,
  type PromptKeySummary,
  type PromptVersion,
  type PromptVersionStatus
} from '@services/api'

const loading = ref(false)
const actionLoading = ref(false)
const summaries = ref<PromptKeySummary[]>([])

const drawerVisible = ref(false)
const versionLoading = ref(false)
const currentSummary = ref<PromptKeySummary | null>(null)
const versions = ref<PromptVersion[]>([])

const createDialogVisible = ref(false)
const createForm = reactive({ content: '', change_note: '' })

const experimentDialogVisible = ref(false)
const experimentForm = reactive({ version: null as number | null, traffic_percent: 20 })

const statusLabel = (status: PromptVersionStatus) =>
  ({ draft: '草稿', active: '生效中', archived: '已归档' })[status]

const statusTagType = (status: PromptVersionStatus) =>
  ({ draft: 'info', active: 'success', archived: '' })[status] as 'info' | 'success' | ''

const formatTime = (iso: string) => iso.replace('T', ' ').slice(0, 16)

/** 实验候选：排除当前主干的其它版本（草稿 / 归档都可直接拉起做实验） */
const experimentCandidates = computed(() =>
  versions.value.filter((row) => {
    const main = currentSummary.value?.active.find((item) => item.variant === 'main')
    return !main || row.version !== main.version
  })
)

const loadSummaries = async () => {
  loading.value = true
  try {
    const res = await promptApi.listKeys()
    summaries.value = res.data
  } finally {
    loading.value = false
  }
}

const loadVersions = async () => {
  if (!currentSummary.value) return
  versionLoading.value = true
  try {
    const res = await promptApi.listVersions(currentSummary.value.key)
    versions.value = res.data
    const summary = summaries.value.find((item) => item.key === currentSummary.value?.key)
    if (summary) {
      summary.active = versions.value.filter((row) => row.status === 'active')
      summary.in_experiment = summary.active.some((row) => row.variant !== 'main')
      summary.latest_version = versions.value[0]?.version ?? summary.latest_version
    }
  } finally {
    versionLoading.value = false
  }
}

const openDrawer = async (row: PromptKeySummary) => {
  currentSummary.value = row
  drawerVisible.value = true
  await loadVersions()
}

const openCreateDialog = () => {
  const latest = versions.value[0]
  createForm.content = latest?.content || ''
  createForm.change_note = ''
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!createForm.content.trim()) {
    ElMessage.warning('提示词内容不能为空')
    return
  }
  if (!currentSummary.value) return
  actionLoading.value = true
  try {
    await promptApi.createVersion(currentSummary.value.key, {
      content: createForm.content,
      change_note: createForm.change_note || undefined
    })
    ElMessage.success('草稿已创建，发布后生效')
    createDialogVisible.value = false
    await loadVersions()
  } finally {
    actionLoading.value = false
  }
}

const handleActivate = async (row: PromptVersion) => {
  if (!currentSummary.value) return
  const isRollback =
    row.status === 'archived' && row.version < (currentSummary.value.latest_version || 0)
  try {
    await ElMessageBox.confirm(
      isRollback
        ? `确认回滚到 v${row.version}？当前生效版本将被归档。`
        : `确认发布 v${row.version}？发布后节点立即使用该版本，进行中的实验会终止。`,
      isRollback ? '版本回滚' : '发布版本',
      { type: 'warning' }
    )
  } catch {
    return
  }
  actionLoading.value = true
  try {
    await promptApi.activate(currentSummary.value.key, row.version)
    ElMessage.success(isRollback ? '已回滚' : '已发布')
    await loadVersions()
  } finally {
    actionLoading.value = false
  }
}

const openExperimentDialog = () => {
  experimentForm.version = experimentCandidates.value[0]?.version ?? null
  experimentForm.traffic_percent = 20
  experimentDialogVisible.value = true
}

const handleStartExperiment = async () => {
  if (!currentSummary.value || experimentForm.version === null) {
    ElMessage.warning('请选择实验变体版本')
    return
  }
  actionLoading.value = true
  try {
    await promptApi.startExperiment(currentSummary.value.key, {
      variants: [{ version: experimentForm.version, traffic_percent: experimentForm.traffic_percent }]
    })
    ElMessage.success('A/B 实验已开启')
    experimentDialogVisible.value = false
    await loadVersions()
  } finally {
    actionLoading.value = false
  }
}

const handleStopExperiment = async () => {
  if (!currentSummary.value) return
  try {
    await ElMessageBox.confirm('确认停止实验？全部流量将回归主干版本。', '停止 A/B 实验', {
      type: 'warning'
    })
  } catch {
    return
  }
  actionLoading.value = true
  try {
    await promptApi.stopExperiment(currentSummary.value.key)
    ElMessage.success('实验已停止')
    await loadVersions()
  } finally {
    actionLoading.value = false
  }
}

onMounted(loadSummaries)
</script>

<style scoped>
.prompt-name {
  font-weight: 500;
  color: #1f2329;
}

.prompt-key {
  font-size: 12px;
  color: #8f959e;
}

.variant-tag {
  margin-right: 6px;
}

.drawer-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.toolbar-spacer {
  flex: 1;
}

.content-preview {
  padding: 8px 16px;
}

.content-preview pre {
  margin: 0;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.6;
  color: #4e5969;
  background: #f7f8fa;
  border-radius: 6px;
  padding: 12px;
}

.dialog-alert {
  margin-bottom: 14px;
}

.dialog-field {
  margin-bottom: 12px;
}

.percent-hint {
  margin-left: 10px;
  color: #8f959e;
  font-size: 13px;
}
</style>
