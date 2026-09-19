<template>
  <div class="studio" v-loading="loading" element-loading-text="正在恢复任务进度…">
    <BackButton />
    <PageHeader title="图文创作工作台" :actions="headerActions" @action="onHeaderAction" />

    <!-- 全流程步骤条 -->
    <Card>
      <el-steps :active="activeStep" align-center finish-status="success">
        <el-step title="输入方向" description="想做什么内容" />
        <el-step title="AI 规划选题" description="3-5 个候选" />
        <el-step title="人工选题" description="选定一个开写" />
        <el-step title="AI 撰稿" description="可带意见反复改" />
        <el-step title="人工审核" description="通过 / 退回重写" />
        <el-step title="视觉配图" description="知识点卡片图" />
      </el-steps>
    </Card>

    <!-- 忙碌遮罩（等待 AI 长耗时节点） -->
    <div v-if="busy" class="busy-bar">
      <el-icon class="is-loading" :size="18"><Loading /></el-icon>
      <span>{{ busyText }}</span>
    </div>

    <!-- ========== 阶段 0：发起任务 ========== -->
    <Card v-if="!run" title="新建图文任务">
      <el-form :model="startForm" label-width="92px" class="start-form" @submit.prevent>
        <el-form-item label="内容方向" required>
          <el-input
            v-model="startForm.topic_direction"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="例如：LangGraph 人工中断（Human-in-the-loop）实战教程"
          />
        </el-form-item>
        <el-form-item label="目标平台">
          <el-radio-group v-model="startForm.platform">
            <el-radio-button value="xiaohongshu">小红书（短文 + 竖版配图）</el-radio-button>
            <el-radio-button value="wechat">微信公众号（深度长文 + 横版配图）</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="发起后 AI 会先规划 3-5 个选题，系统会暂停等你挑选；撰稿后还会再暂停一次等你审核，期间关掉页面也不会丢失进度。"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :icon="MagicStick"
            :loading="busy"
            @click="handleStart"
          >
            开始规划选题
          </el-button>
        </el-form-item>
      </el-form>
    </Card>

    <!-- 运行中容器 -->
    <template v-else>
      <!-- 任务信息条 -->
      <Card>
        <div class="task-meta">
          <div class="meta-item">
            <span class="meta-label">内容方向</span>
            <span class="meta-value">{{ run.project.topic_direction }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">平台</span>
            <el-tag :type="run.project.platform === 'xiaohongshu' ? 'danger' : 'success'" effect="plain" size="small">
              {{ platformLabel(run.project.platform) }}
            </el-tag>
          </div>
          <div class="meta-item" v-if="run.selected_topic">
            <span class="meta-label">已选选题</span>
            <span class="meta-value">{{ run.selected_topic }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">任务编号</span>
            <el-text type="info" size="small" class="thread-id">{{ run.project.thread_id }}</el-text>
          </div>
        </div>
      </Card>

      <!-- Checkpoint 丢失兜底 -->
      <Card v-if="checkpointLost">
        <el-result
          icon="warning"
          title="工作流运行状态已不可用"
          sub-title="当前服务以内存模式运行且服务已重启，无法继续该任务的中断恢复；已完成的成果仍可在下方查看（如有）。"
        >
          <template #extra>
            <el-button type="primary" @click="goCreate">新建图文任务</el-button>
            <el-button @click="goList">返回列表</el-button>
          </template>
        </el-result>
      </Card>

      <!-- ========== 阶段 1：人工选题 ========== -->
      <Card v-if="run.next_step === 'human_select'" title="第一步：从 AI 规划的选题中选一个">
        <template #actions>
          <el-tag type="warning" effect="dark">等待人工选择</el-tag>
        </template>

        <el-row :gutter="16">
          <el-col
            v-for="(topic, index) in run.proposed_topics"
            :key="topic.title"
            :xs="24"
            :sm="12"
            :md="8"
          >
            <div
              class="topic-card"
              :class="{ selected: selectedTitle === topic.title }"
              @click="selectedTitle = topic.title"
            >
              <div class="topic-card-index">选题 {{ index + 1 }}</div>
              <div class="topic-card-title">{{ topic.title }}</div>
              <div class="topic-card-desc">{{ topic.description }}</div>
              <div class="topic-card-tags">
                <el-tag v-if="topic.category" size="small" type="primary" effect="plain">
                  {{ topic.category }}
                </el-tag>
                <el-tag
                  v-for="tag in topic.tags?.slice(0, 2)"
                  :key="tag"
                  size="small"
                  effect="plain"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <el-icon v-if="selectedTitle === topic.title" class="topic-card-check">
                <CircleCheckFilled />
              </el-icon>
            </div>
          </el-col>
        </el-row>

        <div class="panel-footer">
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedTitle"
            :loading="busy"
            @click="handleSelectTopic"
          >
            使用「{{ selectedTitle || '请先选择选题' }}」开始撰稿
          </el-button>
        </div>
      </Card>

      <!-- ========== 阶段 2：人工审核 ========== -->
      <Card v-if="run.next_step === 'human_review'" title="第二步：审核 AI 初稿">
        <template #actions>
          <el-tag type="warning" effect="dark">等待人工审核</el-tag>
        </template>

        <el-alert
          v-if="run.revision_count > 0"
          type="warning"
          :closable="false"
          show-icon
          class="revise-alert"
          :title="`这是第 ${run.revision_count + 1} 版初稿（已按你的意见重写 ${run.revision_count} 次）`"
          description="如果仍不满意可以继续退回重写，直到满意后再审核通过。"
        />

        <h2 class="draft-title">{{ run.draft_title }}</h2>
        <MarkdownViewer :content="run.draft_content" />

        <el-divider />

        <div class="review-box">
          <div class="review-label">
            <el-icon><ChatLineSquare /></el-icon>
            <span>修改意见（选「退回重写」时必填，AI 会据此重写）</span>
          </div>
          <el-input
            v-model="feedback"
            type="textarea"
            :rows="4"
            maxlength="1000"
            show-word-limit
            placeholder="例如：第二段太啰嗦，需要补充一段可运行的代码示例；结尾加一个实战练习。"
          />
          <div class="review-actions">
            <el-button
              type="danger"
              plain
              size="large"
              :loading="busy"
              @click="handleReject"
            >
              退回重写
            </el-button>
            <el-button
              type="success"
              size="large"
              :loading="busy"
              @click="handleApprove"
            >
              审核通过，生成配图
            </el-button>
          </div>
        </div>
      </Card>

      <!-- ========== 阶段 3：已完成 ========== -->
      <template v-if="run.completed">
        <Card>
          <el-result
            icon="success"
            title="图文内容已全部生成"
            :sub-title="`共提炼 ${run.visual_points.length} 个知识点，生成 ${run.image_urls.length} 张配图`"
          >
            <template #extra>
              <el-button type="primary" @click="goCreate">
                <el-icon style="margin-right: 4px;"><Plus /></el-icon>
                再创建一个任务
              </el-button>
              <el-button @click="goList">返回任务列表</el-button>
            </template>
          </el-result>
        </Card>

        <!-- 知识点卡片 + 配图 -->
        <Card title="小红书知识卡片">
          <el-row :gutter="16">
            <el-col
              v-for="(point, index) in run.visual_points"
              :key="index"
              :xs="24"
              :sm="12"
              :md="8"
            >
              <div class="visual-card">
                <div class="visual-index">{{ index + 1 }}</div>
                <el-image
                  v-if="run.image_urls[index]"
                  :src="run.image_urls[index]"
                  :preview-src-list="run.image_urls"
                  :initial-index="index"
                  fit="cover"
                  class="visual-image"
                  preview-teleported
                />
                <div v-else class="visual-image visual-image-fail">
                  <el-icon :size="28"><PictureFilled /></el-icon>
                  <span>该张图片生成失败</span>
                </div>
                <div class="visual-point">{{ point.point }}</div>
                <div class="visual-detail">{{ point.detail }}</div>
              </div>
            </el-col>
          </el-row>
        </Card>

        <!-- 最终文章 -->
        <Card title="最终文案">
          <template #actions>
            <el-button type="primary" plain size="small" :icon="CopyDocument" @click="copyArticle">
              复制全文
            </el-button>
          </template>
          <h2 class="draft-title">{{ finalTitle }}</h2>
          <MarkdownViewer :content="run.final_content" />
        </Card>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  MagicStick,
  Plus,
  Loading,
  CopyDocument,
} from '@element-plus/icons-vue'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import MarkdownViewer from '@components/MarkdownViewer.vue'
import { workflowApi } from '@services/api'
import type { WorkflowRunState } from '@services/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const busy = ref(false)
const busyText = ref('')
const run = ref<WorkflowRunState | null>(null)

const startForm = ref({
  topic_direction: '',
  platform: 'xiaohongshu' as 'xiaohongshu' | 'wechat',
})
const selectedTitle = ref('')
const feedback = ref('')

const headerActions: PageAction[] = [
  { label: '新建任务', type: 'primary', plain: true, icon: 'Plus', key: 'create' },
  { label: '任务列表', type: 'info', plain: true, icon: 'List', key: 'list' },
]

// ---- 步骤条进度 ----
const activeStep = computed(() => {
  if (!run.value) return 0
  if (run.value.completed) return 6
  if (run.value.next_step === 'human_select') return 2
  if (run.value.next_step === 'human_review') return 4
  // busy 过渡中：选题提交后、审核提交后由 busyText 体现
  return 0
})

// Checkpoint 丢失：业务记录在，但图状态拿不到（如 MemorySaver 重启）
const checkpointLost = computed(() => {
  if (!run.value || run.value.completed) return false
  return run.value.next_step === null
})

const finalTitle = computed(() => {
  return run.value?.project.article_content?.title || run.value?.draft_title || '最终文案'
})

function platformLabel(platform: string): string {
  return platform === 'xiaohongshu' ? '小红书' : '微信公众号'
}

async function applyRun(res: any, syncUrl = true) {
  const data = res?.data as WorkflowRunState | undefined
  if (!data) return
  run.value = data
  if (syncUrl && data.project.thread_id && !route.params.threadId) {
    // 发起后把 thread_id 写入 URL，刷新即可恢复
    router.replace(`/workflows/studio/${data.project.thread_id}`)
  }
  if (data.next_step === 'human_select' && !selectedTitle.value) {
    selectedTitle.value = ''
  }
}

// ---- 发起 ----
async function handleStart() {
  const direction = startForm.value.topic_direction.trim()
  if (!direction) {
    ElMessage.warning('请先填写内容方向')
    return
  }
  busy.value = true
  busyText.value = 'AI 正在规划选题，通常需要 10-30 秒…'
  try {
    const res = await workflowApi.start({
      topic_direction: direction,
      platform: startForm.value.platform,
    })
    await applyRun(res)
    ElMessage.success('选题已生成，请挑选一个')
  } catch (error) {
    console.error('启动工作流失败:', error)
  } finally {
    busy.value = false
  }
}

// ---- 人工选题 ----
async function handleSelectTopic() {
  if (!selectedTitle.value || !run.value) return
  busy.value = true
  busyText.value = 'AI 正在撰写初稿，通常需要 30-90 秒…'
  try {
    const res = await workflowApi.resume(run.value.project.thread_id, {
      action: 'select_topic',
      data: selectedTitle.value,
    })
    await applyRun(res, false)
    ElMessage.success('初稿已生成，请审核')
  } catch (error) {
    console.error('选题恢复失败:', error)
  } finally {
    busy.value = false
  }
}

// ---- 退回重写 ----
async function handleReject() {
  const note = feedback.value.trim()
  if (!note) {
    ElMessage.warning('退回重写时必须填写修改意见')
    return
  }
  if (!run.value) return
  busy.value = true
  busyText.value = 'AI 正在按你的意见重写初稿…'
  try {
    const res = await workflowApi.resume(run.value.project.thread_id, {
      action: 'review',
      status: 'reject',
      feedback: note,
    })
    await applyRun(res, false)
    feedback.value = ''
    ElMessage.success('已按修改意见重写，请再次审核')
  } catch (error) {
    console.error('退回重写失败:', error)
  } finally {
    busy.value = false
  }
}

// ---- 审核通过 ----
async function handleApprove() {
  if (!run.value) return
  busy.value = true
  busyText.value = '正在提炼知识点并并行生成配图，预计 1-3 分钟，请勿关闭页面…'
  try {
    const res = await workflowApi.resume(run.value.project.thread_id, {
      action: 'review',
      status: 'approve',
    })
    await applyRun(res, false)
    ElMessage.success('审核通过，配图已生成')
  } catch (error) {
    console.error('审核通过失败:', error)
  } finally {
    busy.value = false
  }
}

// ---- 恢复已有任务（刷新 / 从列表进入）----
async function restore(threadId: string) {
  loading.value = true
  try {
    const res: any = await workflowApi.detail(threadId)
    await applyRun(res, false)
  } catch (error) {
    console.error('恢复任务失败:', error)
  } finally {
    loading.value = false
  }
}

async function copyArticle() {
  const text = run.value
    ? `# ${finalTitle.value}\n\n${run.value.final_content}`
    : ''
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('全文已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

function goCreate() {
  router.push('/workflows/studio')
}

function goList() {
  router.push('/workflows')
}

function onHeaderAction(action: PageAction) {
  if (action.key === 'create') goCreate()
  if (action.key === 'list') goList()
}

onMounted(() => {
  const threadId = route.params.threadId as string | undefined
  if (threadId) restore(threadId)
})
</script>

<style scoped>
.studio {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.start-form {
  max-width: 720px;
}

.busy-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #EFF4FF;
  border: 1px solid #D4E3FF;
  border-radius: 8px;
  color: #245BDB;
  font-size: 13px;
}

.busy-bar .is-loading {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 任务信息条 */
.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-size: 13px;
  color: #8F959E;
}

.meta-value {
  font-size: 13px;
  color: #1F2329;
  font-weight: 500;
}

.thread-id {
  font-family: 'Courier New', monospace;
}

/* 选题卡片 */
.topic-card {
  position: relative;
  border: 2px solid #EBEDF0;
  border-radius: 10px;
  padding: 18px 16px 14px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.2s;
  background: #FAFBFC;
  height: calc(100% - 16px);
}

.topic-card:hover {
  border-color: #94BFFF;
  background: #FFFFFF;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(51, 112, 255, 0.12);
}

.topic-card.selected {
  border-color: #3370FF;
  background: #F5F9FF;
  box-shadow: 0 4px 12px rgba(51, 112, 255, 0.18);
}

.topic-card-index {
  font-size: 12px;
  color: #8F959E;
  margin-bottom: 6px;
}

.topic-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1F2329;
  line-height: 1.5;
  margin-bottom: 8px;
}

.topic-card-desc {
  font-size: 13px;
  color: #4E5969;
  line-height: 1.7;
  margin-bottom: 12px;
}

.topic-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-card-check {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 20px;
  color: #3370FF;
}

.panel-footer {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

/* 审稿 */
.revise-alert {
  margin-bottom: 16px;
}

.draft-title {
  font-size: 18px;
  font-weight: 600;
  color: #1F2329;
  margin: 0 0 16px;
}

.review-box {
  background: #FAFBFC;
  border: 1px solid #EBEDF0;
  border-radius: 8px;
  padding: 16px;
}

.review-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #4E5969;
  margin-bottom: 10px;
}

.review-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

/* 知识卡片 */
.visual-card {
  border: 1px solid #EBEDF0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
  background: #FFFFFF;
  transition: box-shadow 0.2s;
}

.visual-card:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.visual-index {
  position: absolute;
  z-index: 1;
  margin: 10px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(51, 112, 255, 0.9);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-image {
  width: 100%;
  height: 260px;
  display: block;
}

.visual-image-fail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #F7F8FA;
  color: #8F959E;
  font-size: 13px;
}

.visual-point {
  padding: 12px 14px 4px;
  font-size: 15px;
  font-weight: 600;
  color: #1F2329;
}

.visual-detail {
  padding: 0 14px 14px;
  font-size: 13px;
  color: #4E5969;
  line-height: 1.7;
}
</style>
