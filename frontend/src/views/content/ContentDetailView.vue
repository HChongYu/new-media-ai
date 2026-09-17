<template>
  <div class="workspace" v-loading="loading">
    <BackButton />
    <PageHeader title="内容工作台" :actions="headerActions" @action="handleHeaderAction" />

    <!-- 全流程步骤条 -->
    <Card>
      <el-steps :active="activeStep" align-center finish-status="success">
        <el-step title="撰写文案" description="AI 生成或手动撰写" />
        <el-step title="智能配图" description="封面 / 正文 / 摘要图" />
        <el-step
          title="内容审核"
          description="通过后解锁发布"
          :status="content?.status === 'rejected' ? 'error' : undefined"
        />
        <el-step title="多平台发布" description="小红书 / 微信公众号" />
      </el-steps>
    </Card>

    <!-- 下一步引导条 -->
    <el-alert
      v-if="guide"
      :type="guide.type"
      :closable="false"
      show-icon
      class="guide-alert"
    >
      <template #title>
        <div class="guide-inner">
          <span>{{ guide.text }}</span>
          <span class="guide-actions">
            <el-button
              v-for="action in guide.actions"
              :key="action.key"
              :type="action.type"
              :plain="action.plain"
              size="small"
              @click="onGuideAction(action)"
            >
              {{ action.label }}
            </el-button>
          </span>
        </div>
      </template>
    </el-alert>

    <!-- 阶段 1：文案 -->
    <Card>
      <div id="step-content" class="step-anchor">
        <div class="step-head">
          <div class="step-no" :class="stepClass('content')">
            <el-icon v-if="stepClass('content') === 'done'"><Check /></el-icon>
            <el-icon v-else-if="stepClass('content') === 'locked'"><Lock /></el-icon>
            <span v-else>1</span>
          </div>
          <div class="step-title">
            <div class="step-name">撰写文案</div>
            <div class="step-desc">选题：{{ content?.topic_title || '—' }} · {{ content?.word_count || 0 }} 字 · 创建人 {{ content?.created_by_name || '—' }}</div>
          </div>
          <StatusBadge v-if="content" :status="content.status" />
        </div>

        <div class="step-body">
          <h2 class="article-title">{{ content?.title }}</h2>
          <MarkdownViewer :content="content?.content_text || ''" />
        </div>

        <div v-if="content?.status === 'rejected' && content?.review_note" class="reject-note">
          <el-alert type="error" :closable="false" show-icon>
            <template #title>驳回原因：{{ content.review_note }}</template>
          </el-alert>
        </div>

        <div class="step-footer">
          <el-button
            v-if="content?.status !== 'reviewing'"
            type="primary"
            plain
            :icon="Edit"
            @click="goEdit"
          >
            编辑文案
          </el-button>
          <el-button
            v-if="content?.status === 'draft' || content?.status === 'rejected'"
            type="primary"
            :loading="submitting"
            @click="submitForReview"
          >
            提交审核
          </el-button>
          <el-tag v-if="content?.status === 'reviewing'" type="warning" effect="plain">
            审核中，内容暂不可修改
          </el-tag>
        </div>
      </div>
    </Card>

    <!-- 阶段 2：配图 -->
    <Card>
      <div id="step-image" class="step-anchor">
        <div class="step-head">
          <div class="step-no" :class="stepClass('image')">
            <el-icon v-if="stepClass('image') === 'done'"><Check /></el-icon>
            <el-icon v-else-if="stepClass('image') === 'locked'"><Lock /></el-icon>
            <span v-else>2</span>
          </div>
          <div class="step-title">
            <div class="step-name">智能配图</div>
            <div class="step-desc">AI 根据文案一键生成封面图、正文插图、摘要图（可跳过，审核前后均可生成）</div>
          </div>
          <el-tag v-if="images.length" type="success" effect="plain">已生成 {{ images.length }} 张</el-tag>
        </div>

        <div class="step-body">
          <el-empty
            v-if="images.length === 0"
            description="还没有配图，点击下方按钮一键生成"
            :image-size="80"
          />
          <ImageGrid
            v-else
            :images="images"
            show-download
            show-delete
            @view="viewImage"
            @delete="removeImage"
          />
        </div>

        <div class="step-footer">
          <el-button type="primary" :icon="Picture" :loading="imageDialog.loading" @click="openImageDialog">
            {{ images.length ? '继续生成配图' : 'AI 一键生成配图' }}
          </el-button>
        </div>
      </div>
    </Card>

    <!-- 阶段 3：审核 -->
    <Card>
      <div id="step-review" class="step-anchor">
        <div class="step-head">
          <div class="step-no" :class="stepClass('review')">
            <el-icon v-if="stepClass('review') === 'done'"><Check /></el-icon>
            <el-icon v-else-if="stepClass('review') === 'locked'"><Lock /></el-icon>
            <el-icon v-else-if="stepClass('review') === 'error'"><Close /></el-icon>
            <span v-else>3</span>
          </div>
          <div class="step-title">
            <div class="step-name">内容审核</div>
            <div class="step-desc">
              <template v-if="content?.status === 'reviewing'">等待审核人处理</template>
              <template v-else-if="content?.status === 'approved' || content?.status === 'published'">
                审核通过 · {{ content?.reviewed_by_name || '—' }} · {{ formatDateTime(content?.reviewed_at) }}
              </template>
              <template v-else>提交审核后在此处理</template>
            </div>
          </div>
        </div>

        <div class="step-body">
          <!-- 草稿：锁定 -->
          <el-empty
            v-if="content?.status === 'draft'"
            description="请先在第 1 步提交审核"
            :image-size="70"
          />

          <!-- 驳回 -->
          <el-alert
            v-else-if="content?.status === 'rejected'"
            type="error"
            :closable="false"
            show-icon
            title="审核已驳回，请按驳回原因修改文案后重新提交"
            style="margin-bottom: 12px;"
          />

          <!-- 审核中：审核操作 -->
          <el-form
            v-else-if="content?.status === 'reviewing'"
            :model="reviewForm"
            label-width="80px"
            class="review-form"
          >
            <el-form-item label="审核结果">
              <el-radio-group v-model="reviewForm.status">
                <el-radio value="approved">审核通过（可进入发布）</el-radio>
                <el-radio value="rejected">驳回修改</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="reviewForm.status === 'rejected'" label="驳回原因">
              <el-input
                v-model="reviewForm.review_note"
                type="textarea"
                :rows="3"
                placeholder="请说明需要修改的问题"
              />
            </el-form-item>
          </el-form>

          <!-- 已通过 -->
          <el-result
            v-else
            icon="success"
            title="审核已通过"
            sub-title="内容已具备发布条件，请在第 4 步选择平台发布"
            style="padding: 12px 0;"
          />
        </div>

        <div class="step-footer">
          <template v-if="content?.status === 'reviewing'">
            <el-button type="danger" plain :loading="reviewing" @click="rejectContent">驳回</el-button>
            <el-button type="success" :loading="reviewing" @click="approveContent">审核通过</el-button>
          </template>
          <el-button
            v-else-if="content?.status === 'rejected'"
            type="primary"
            :loading="submitting"
            @click="submitForReview"
          >
            修改完毕，重新提交审核
          </el-button>
        </div>
      </div>
    </Card>

    <!-- 阶段 4：发布 -->
    <Card>
      <div id="step-publish" class="step-anchor">
        <div class="step-head">
          <div class="step-no" :class="stepClass('publish')">
            <el-icon v-if="stepClass('publish') === 'done'"><Check /></el-icon>
            <el-icon v-else-if="stepClass('publish') === 'locked'"><Lock /></el-icon>
            <span v-else>4</span>
          </div>
          <div class="step-title">
            <div class="step-name">多平台发布</div>
            <div class="step-desc">同内容可分别发布到小红书与微信公众号</div>
          </div>
        </div>

        <div class="step-body">
          <el-empty
            v-if="content?.status !== 'approved' && content?.status !== 'published'"
            description="审核通过后解锁发布"
            :image-size="70"
          />

          <div v-else class="platform-list">
            <div v-for="platform in platforms" :key="platform.value" class="platform-item">
              <div class="platform-info">
                <el-icon :size="22" :color="platform.color">
                  <component :is="platform.icon" />
                </el-icon>
                <div>
                  <div class="platform-name">{{ platform.label }}</div>
                  <div class="platform-sub">{{ platform.desc }}</div>
                </div>
              </div>

              <!-- 已发布 -->
              <template v-if="publishedRecord(platform.value)">
                <el-tag type="success" effect="dark" size="large">
                  已发布 · {{ formatDateTime(publishedRecord(platform.value)?.published_at) }}
                </el-tag>
                <el-button type="primary" plain @click="openPost(publishedRecord(platform.value))">
                  查看链接
                </el-button>
              </template>

              <!-- 发布失败 -->
              <template v-else-if="failedRecord(platform.value)">
                <el-tag type="danger" effect="plain" size="large">发布失败</el-tag>
                <el-button type="danger" plain @click="doPublish(platform.value)">重试发布</el-button>
              </template>

              <!-- 未发布 -->
              <el-button
                v-else
                :type="platform.value === 'xiaohongshu' ? 'danger' : 'success'"
                :loading="publishing[platform.value]"
                @click="doPublish(platform.value)"
              >
                发布到{{ platform.label }}
              </el-button>
            </div>
          </div>
        </div>

        <div v-if="records.some(r => r.status === 'failed')" class="step-footer">
          <el-text type="danger" size="small">
            失败原因：{{ records.find(r => r.status === 'failed')?.error_message || '未知错误' }}
          </el-text>
        </div>
      </div>
    </Card>

    <!-- AI 配图生成对话框 -->
    <el-dialog v-model="imageDialog.visible" title="AI 生成配图" width="520px">
      <el-form :model="imageDialog.form" label-width="90px">
        <el-form-item label="图片类型">
          <el-checkbox-group v-model="imageDialog.form.image_types">
            <el-checkbox value="cover">封面图（吸引眼球的主视觉）</el-checkbox>
            <el-checkbox value="section">正文图（配合段落的插图）</el-checkbox>
            <el-checkbox value="summary">摘要图（核心要点信息图）</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="生成数量">
          <el-slider v-model="imageDialog.form.count" :min="1" :max="9" show-input />
        </el-form-item>
        <el-form-item label="图片风格">
          <el-select v-model="imageDialog.form.style" style="width: 100%;">
            <el-option label="极简" value="minimalist" />
            <el-option label="专业" value="professional" />
            <el-option label="创意" value="creative" />
            <el-option label="优雅" value="elegant" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-alert
        type="info"
        :closable="false"
        title="AI 将根据当前文案内容自动构思画面并逐张生成，通常需要 30-90 秒"
        style="margin-bottom: 12px;"
      />
      <template #footer>
        <el-button @click="imageDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="imageDialog.loading" @click="confirmGenerateImages">
          开始生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check, Lock, Close, Edit, Picture,
} from '@element-plus/icons-vue'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import StatusBadge from '@components/StatusBadge.vue'
import MarkdownViewer from '@components/MarkdownViewer.vue'
import ImageGrid from '@components/ImageGrid.vue'
import { contentApi, imageApi, publishApi } from '@services/api'

type StepKey = 'content' | 'image' | 'review' | 'publish'
type PlatformValue = 'xiaohongshu' | 'wechat'

const route = useRoute()
const router = useRouter()

const contentId = ref<number>(Number(route.params.id))
const loading = ref(false)
const submitting = ref(false)
const reviewing = ref(false)
const publishing = reactive<Record<string, boolean>>({})

const content = ref<any>(null)
const images = ref<any[]>([])
const records = ref<any[]>([])

const reviewForm = reactive({
  status: 'approved' as 'approved' | 'rejected',
  review_note: '',
})

const imageDialog = reactive({
  visible: false,
  loading: false,
  form: {
    image_types: ['cover', 'section', 'summary'] as string[],
    count: 3,
    style: 'professional',
  },
})

const platforms: {
  value: PlatformValue
  label: string
  desc: string
  icon: string
  color: string
}[] = [
  { value: 'xiaohongshu', label: '小红书', desc: '种草笔记 · 图文首发', icon: 'Star', color: '#F53F3F' },
  { value: 'wechat', label: '微信公众号', desc: '深度长文 · 订阅推送', icon: 'ChatLineRound', color: '#00B365' },
]

const headerActions: PageAction[] = [
  { label: '删除内容', type: 'danger', icon: 'Delete', key: 'delete' },
]

// ---- 步骤状态计算 ----
const activeStep = computed(() => {
  const map: Record<string, number> = {
    draft: 0,
    rejected: 0,
    reviewing: 2,
    approved: 3,
    published: 4,
  }
  return map[content.value?.status] ?? 0
})

function stepClass(key: StepKey): 'done' | 'active' | 'locked' | 'error' {
  const status = content.value?.status
  if (key === 'content') {
    if (status === 'reviewing' || status === 'approved' || status === 'published') return 'done'
    return 'active'
  }
  if (key === 'image') {
    return images.value.length > 0 ? 'done' : 'active'
  }
  if (key === 'review') {
    if (status === 'approved' || status === 'published') return 'done'
    if (status === 'reviewing') return 'active'
    if (status === 'rejected') return 'error'
    return 'locked'
  }
  // publish
  if (status === 'published' || records.value.some(r => r.status === 'published')) return 'done'
  if (status === 'approved') return 'active'
  return 'locked'
}

// ---- 顶部引导条 ----
interface GuideAction {
  key: string
  label: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  plain?: boolean
}
interface GuideState {
  type: 'success' | 'warning' | 'info' | 'error'
  text: string
  actions: GuideAction[]
}

const guide = computed<GuideState | null>(() => {
  const status = content.value?.status
  const note = content.value?.review_note
  if (status === 'draft') {
    return {
      type: 'info',
      text: '当前在第 1 步：文案还是草稿。确认内容无误后提交审核，即可进入配图与发布环节。',
      actions: [
        { key: 'edit', label: '编辑文案', type: 'primary', plain: true },
        { key: 'submit', label: '提交审核', type: 'primary' },
      ],
    }
  }
  if (status === 'rejected') {
    return {
      type: 'error',
      text: `审核未通过${note ? '：' + note : '，请修改后重新提交'}。`,
      actions: [
        { key: 'edit', label: '去修改', type: 'primary', plain: true },
        { key: 'submit', label: '重新提交审核', type: 'primary' },
      ],
    }
  }
  if (status === 'reviewing') {
    return {
      type: 'warning',
      text: '当前在第 3 步：内容等待审核。通过后即可一键发布到多个平台。',
      actions: [{ key: 'goto-review', label: '立即审核', type: 'primary' }],
    }
  }
  if (status === 'approved') {
    return {
      type: 'success',
      text: '审核已通过！现在可以一键发布到小红书 / 微信公众号。',
      actions: [{ key: 'goto-publish', label: '去发布', type: 'primary' }],
    }
  }
  if (status === 'published') {
    return {
      type: 'success',
      text: '内容已完成发布，可在第 4 步查看各平台发布链接。',
      actions: [{ key: 'goto-publish', label: '查看发布链接', type: 'primary', plain: true }],
    }
  }
  return null
})

function onGuideAction(action: { key: string }) {
  switch (action.key) {
    case 'edit':
      goEdit()
      break
    case 'submit':
      submitForReview()
      break
    case 'goto-review':
      scrollToStep('review')
      break
    case 'goto-publish':
      scrollToStep('publish')
      break
  }
}

// ---- 数据加载 ----
async function loadAll() {
  loading.value = true
  try {
    const [detailRes, imageRes, recordRes] = await Promise.all([
      contentApi.detail(contentId.value),
      imageApi.byContent(contentId.value),
      publishApi.history({ page: 1, page_size: 100 }),
    ])
    content.value = (detailRes as any)?.data || null
    images.value = (imageRes as any)?.data || []
    const allRecords = (recordRes as any)?.data?.items || []
    records.value = allRecords.filter((r: any) => r.content_id === contentId.value)
  } catch (error) {
    console.error('Failed to load workspace:', error)
    ElMessage.error('加载内容工作台失败')
  } finally {
    loading.value = false
  }
}

// ---- 阶段 1：提交审核 ----
async function submitForReview() {
  submitting.value = true
  try {
    await contentApi.update(contentId.value, { status: 'reviewing' })
    ElMessage.success('已提交审核，请在下方完成审核')
    await loadAll()
    scrollToStep('review')
  } catch (error) {
    console.error('Failed to submit:', error)
  } finally {
    submitting.value = false
  }
}

function goEdit() {
  router.push(`/content/edit/${contentId.value}`)
}

// ---- 阶段 2：配图 ----
function openImageDialog() {
  imageDialog.visible = true
}

async function confirmGenerateImages() {
  if (imageDialog.form.image_types.length === 0) {
    ElMessage.warning('请至少选择一种图片类型')
    return
  }
  imageDialog.loading = true
  try {
    await imageApi.generate(contentId.value, {
      image_type: imageDialog.form.image_types as any,
      count: imageDialog.form.count,
      style: imageDialog.form.style as any,
    })
    ElMessage.success('配图生成完成')
    imageDialog.visible = false
    const res: any = await imageApi.byContent(contentId.value)
    images.value = res?.data || []
    scrollToStep('image')
  } catch (error) {
    console.error('Failed to generate images:', error)
    ElMessage.error('配图生成失败，请稍后重试')
  } finally {
    imageDialog.loading = false
  }
}

function viewImage(image: any) {
  window.open(image.image_url, '_blank')
}

async function removeImage(image: any) {
  try {
    await ElMessageBox.confirm('确定删除这张配图吗？', '提示', { type: 'warning' })
    await imageApi.delete(image.id)
    images.value = images.value.filter(i => i.id !== image.id)
    ElMessage.success('已删除')
  } catch (error) {
    if (error !== 'cancel') console.error('Failed to delete image:', error)
  }
}

// ---- 阶段 3：审核 ----
async function approveContent() {
  reviewing.value = true
  try {
    await contentApi.review(contentId.value, { status: 'approved', review_note: '' })
    ElMessage.success('审核通过，可以发布了')
    await loadAll()
    scrollToStep('publish')
  } catch (error) {
    console.error('Failed to approve:', error)
  } finally {
    reviewing.value = false
  }
}

async function rejectContent() {
  if (!reviewForm.review_note.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  reviewing.value = true
  try {
    await contentApi.review(contentId.value, {
      status: 'rejected',
      review_note: reviewForm.review_note,
    })
    ElMessage.success('已驳回')
    reviewForm.review_note = ''
    await loadAll()
    scrollToStep('content')
  } catch (error) {
    console.error('Failed to reject:', error)
  } finally {
    reviewing.value = false
  }
}

// ---- 阶段 4：发布 ----
function publishedRecord(platform: PlatformValue) {
  return records.value.find(r => r.platform === platform && r.status === 'published')
}

function failedRecord(platform: PlatformValue) {
  return records.value.find(r => r.platform === platform && r.status === 'failed')
}

async function doPublish(platform: PlatformValue) {
  publishing[platform] = true
  try {
    await publishApi.create(contentId.value, platform)
    ElMessage.success(`已发布到${platform === 'xiaohongshu' ? '小红书' : '微信公众号'}`)
    await loadAll()
  } catch (error) {
    console.error('Failed to publish:', error)
  } finally {
    publishing[platform] = false
  }
}

function openPost(record: any) {
  if (record?.post_url) window.open(record.post_url, '_blank')
}

// ---- 头部操作 ----
async function handleHeaderAction(action: PageAction) {
  if (action.key === 'delete') {
    try {
      await ElMessageBox.confirm('删除后不可恢复，确定删除该内容及其配图关联吗？', '警告', {
        type: 'warning',
      })
      await contentApi.delete(contentId.value)
      ElMessage.success('已删除')
      router.push('/content')
    } catch (error) {
      if (error !== 'cancel') console.error('Failed to delete:', error)
    }
  }
}

// ---- 工具 ----
function formatDateTime(value?: string): string {
  if (!value) return '—'
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function scrollToStep(step: StepKey) {
  nextTick(() => {
    document.getElementById(`step-${step}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

onMounted(async () => {
  await loadAll()
  const step = route.query.step as StepKey | undefined
  if (step) scrollToStep(step)
})
</script>

<style scoped>
.workspace {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.guide-alert :deep(.el-alert__content) {
  width: 100%;
}

.guide-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.guide-actions {
  display: inline-flex;
  gap: 8px;
}

.step-anchor {
  scroll-margin-top: 80px;
}

.step-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.step-no {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-no.done {
  background: #00B365;
  color: #fff;
}

.step-no.active {
  background: #3370FF;
  color: #fff;
}

.step-no.locked {
  background: #F2F3F5;
  color: #8F959E;
}

.step-no.error {
  background: #F53F3F;
  color: #fff;
}

.step-title {
  flex: 1;
  min-width: 0;
}

.step-name {
  font-size: 15px;
  font-weight: 600;
  color: #1F2329;
}

.step-desc {
  font-size: 12px;
  color: #8F959E;
  margin-top: 2px;
}

.step-body {
  padding-left: 42px;
}

.article-title {
  font-size: 18px;
  font-weight: 600;
  color: #1F2329;
  margin: 0 0 16px;
}

.reject-note {
  padding-left: 42px;
  margin-bottom: 12px;
}

.step-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #EBEDF0;
}

.review-form {
  max-width: 560px;
}

.platform-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 42px;
}

.platform-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border: 1px solid #EBEDF0;
  border-radius: 8px;
  background: #FAFBFC;
}

.platform-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.platform-name {
  font-size: 14px;
  font-weight: 600;
  color: #1F2329;
}

.platform-sub {
  font-size: 12px;
  color: #8F959E;
  margin-top: 2px;
}
</style>
