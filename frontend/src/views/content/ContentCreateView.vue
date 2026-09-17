<template>
  <div class="content-create">
    <BackButton />
    <PageHeader title="创建内容" />

    <el-row :gutter="20">
      <!-- 左侧：选题选择 -->
      <el-col :span="8">
        <Card title="选择选题">
          <el-input
            v-model="topicSearch"
            placeholder="搜索选题..."
            prefix-icon="Search"
            clearable
          />

          <el-scrollbar height="380px" class="topic-scroll">
            <el-empty
              v-if="filteredTopics.length === 0"
              description="暂无选题，请先在选题管理中创建或生成"
              :image-size="70"
            />
            <div
              v-for="topic in filteredTopics"
              v-else
              :key="topic.id"
              class="topic-item"
              :class="{ 'is-active': selectedTopic?.id === topic.id }"
              @click="selectTopic(topic)"
            >
              <div class="topic-item__main">
                <div class="topic-title">{{ topic.title }}</div>
                <div class="topic-desc">{{ topic.description || '暂无描述' }}</div>
              </div>
              <el-tag size="small" :type="getTopicStatusType(topic.status)">
                {{ getTopicStatusText(topic.status) }}
              </el-tag>
            </div>
          </el-scrollbar>
        </Card>

        <Card title="内容设置" style="margin-top: 20px;">
          <el-form :model="contentForm" label-width="80px">
            <el-form-item label="内容类型">
              <el-radio-group v-model="contentForm.content_type">
                <el-radio value="article">文章</el-radio>
                <el-radio value="image">图片</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="发布平台">
              <el-checkbox-group v-model="contentForm.platforms">
                <el-checkbox value="xiaohongshu">小红书</el-checkbox>
                <el-checkbox value="wechat">微信公众号</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="内容风格">
              <el-select v-model="contentForm.tone" placeholder="请选择风格">
                <el-option label="专业严谨" value="professional" />
                <el-option label="轻松活泼" value="casual" />
                <el-option label="热情洋溢" value="enthusiastic" />
              </el-select>
            </el-form-item>

            <el-form-item label="内容长度">
              <el-select v-model="contentForm.length" placeholder="请选择长度">
                <el-option label="短篇 (500字以内)" value="short" />
                <el-option label="中篇 (500-1500字)" value="medium" />
                <el-option label="长篇 (1500字以上)" value="long" />
              </el-select>
            </el-form-item>
          </el-form>

          <el-alert
            v-if="!selectedTopic"
            title="请先在上方选择一个选题，再点击 AI 生成"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 12px;"
          />
          <el-button
            type="primary"
            style="width: 100%; margin-top: 4px;"
            :loading="generating"
            :disabled="!selectedTopic"
            @click="generateContent"
          >
            {{ generating ? 'AI 正在生成中，请稍候...' : 'AI 生成内容' }}
          </el-button>
        </Card>
      </el-col>

      <!-- 右侧：内容编辑 -->
      <el-col :span="16">
        <Card :title="selectedTopic ? `基于选题：${selectedTopic.title}` : '内容编辑'">
          <ContentEditor
            v-model="contentForm.content_text"
            v-model:titleValue="contentForm.title"
            :show-preview="true"
          />
        </Card>

        <div class="action-buttons" style="margin-top: 20px;">
          <el-button :loading="saving" @click="saveDraft">保存草稿</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForReview">提交审核</el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import ContentEditor from '@components/ContentEditor.vue'
import { topicApi, contentApi } from '@services/api'

const route = useRoute()
const router = useRouter()

const topicSearch = ref('')
const topics = ref<any[]>([])
const selectedTopic = ref<any>(null)
const generating = ref(false)
const saving = ref(false)
const submitting = ref(false)

type ContentType = 'article' | 'image'
type Platform = 'xiaohongshu' | 'wechat'
type Tone = 'professional' | 'casual' | 'enthusiastic'
type Length = 'short' | 'medium' | 'long'

interface ContentFormState {
  topic_id: number
  title: string
  content_text: string
  content_type: ContentType
  platforms: Platform[]
  tone: Tone
  length: Length
}

const contentForm = reactive<ContentFormState>({
  topic_id: 0,
  title: '',
  content_text: '',
  content_type: 'article',
  platforms: ['xiaohongshu', 'wechat'],
  tone: 'professional',
  length: 'medium'
})

const filteredTopics = computed(() => {
  const keyword = topicSearch.value.trim().toLowerCase()
  if (!keyword) return topics.value
  return topics.value.filter(
    topic =>
      topic.title?.toLowerCase().includes(keyword) ||
      topic.description?.toLowerCase().includes(keyword)
  )
})

const fetchData = async () => {
  try {
    // 后端分页参数为 page / page_size，响应列表字段为 items
    const result: any = await topicApi.list({ page: 1, page_size: 100 })
    topics.value = result?.data?.items || []

    // 支持从选题列表/详情页带 topicId 跳转过来时自动预选
    const presetId = Number(route.query.topicId)
    if (presetId) {
      const preset = topics.value.find(t => t.id === presetId)
      if (preset) selectTopic(preset)
    }
  } catch (error) {
    console.error('Failed to fetch topics:', error)
    ElMessage.error('获取选题列表失败')
  }
}

const selectTopic = (topic: any) => {
  selectedTopic.value = topic
  contentForm.topic_id = topic.id
  // 仅在标题为空时给一个默认标题，AI 生成后会被正式标题覆盖
  if (!contentForm.title) {
    contentForm.title = `关于${topic.title}的分享`
  }
}

const getTopicStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return statusMap[status] || status
}

const getTopicStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return typeMap[status] || 'info'
}

/** 保存/提交前的统一校验 */
const validateForm = (): boolean => {
  if (!selectedTopic.value || !contentForm.topic_id) {
    ElMessage.warning('请先选择一个选题')
    return false
  }
  if (!contentForm.title.trim()) {
    ElMessage.warning('请输入内容标题')
    return false
  }
  if (!contentForm.content_text.trim()) {
    ElMessage.warning('请输入内容正文，或点击「AI 生成内容」')
    return false
  }
  return true
}

// ---- AI 生成内容（大纲 -> 写作 -> 自动质检返工，由后端 LangGraph 工作流完成）----
const generateContent = async () => {
  if (!selectedTopic.value) {
    ElMessage.warning('请先选择一个选题')
    return
  }
  if (contentForm.platforms.length === 0) {
    ElMessage.warning('请至少选择一个发布平台')
    return
  }

  generating.value = true
  try {
    const params = {
      platform: contentForm.platforms[0],
      tone: contentForm.tone,
      length: contentForm.length
    }
    const result: any = await contentApi.generate(selectedTopic.value.id, params)
    const newId = result?.data?.id
    if (newId) {
      // 后端已将生成结果直接落库，进入内容工作台继续「配图 → 审核 → 发布」
      ElMessage.success('文章已生成，接下来为它配图吧')
      router.replace(`/content/detail/${newId}?step=image`)
    } else {
      ElMessage.error('内容生成失败：返回数据为空')
    }
  } catch (error) {
    console.error('Failed to generate content:', error)
    ElMessage.error('内容生成失败，请检查后端 LLM 配置')
  } finally {
    generating.value = false
  }
}

// ---- 保存草稿 ----
const saveDraft = async () => {
  if (!validateForm()) return

  saving.value = true
  try {
    const result: any = await contentApi.create({
      topic_id: contentForm.topic_id,
      title: contentForm.title,
      content_text: contentForm.content_text,
      content_type: contentForm.content_type,
      platform: contentForm.platforms[0],
    })
    const newId = result?.data?.id
    ElMessage.success('草稿保存成功')
    router.push(newId ? `/content/detail/${newId}` : '/content')
  } catch (error) {
    console.error('Failed to save draft:', error)
  } finally {
    saving.value = false
  }
}

// ---- 提交审核：创建内容（draft）后置为 reviewing，等待审核页人工通过/驳回 ----
const submitForReview = async () => {
  if (!validateForm()) return

  submitting.value = true
  try {
    const result: any = await contentApi.create({
      topic_id: contentForm.topic_id,
      title: contentForm.title,
      content_text: contentForm.content_text,
      content_type: contentForm.content_type,
      platform: contentForm.platforms[0],
    })

    const contentId = result?.data?.id
    if (contentId) {
      await contentApi.update(contentId, { status: 'reviewing' })
    }
    ElMessage.success('已提交审核')
    // 直接进入工作台的审核环节，形成「提交即审核」的连续操作
    router.push(contentId ? `/content/detail/${contentId}?step=review` : '/content')
  } catch (error) {
    console.error('Failed to submit for review:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.content-create {
  padding: 20px;
}

.topic-scroll {
  margin-top: 12px;
}

.topic-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border: 1px solid #EBEDF0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.topic-item:hover {
  background: #F2F3F5;
  border-color: #C9CDD4;
}

.topic-item.is-active {
  background: #EFF4FF;
  border-color: #3370FF;
}

.topic-item__main {
  flex: 1;
  min-width: 0;
}

.topic-title {
  font-weight: 500;
  color: #1F2329;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-desc {
  font-size: 12px;
  color: #8F959E;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
