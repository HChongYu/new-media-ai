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
          <el-empty v-if="filteredTopics.length === 0" description="暂无选题" />
          <el-list v-else>
            <el-list-item
              v-for="topic in filteredTopics"
              :key="topic.id"
              :class="{ 'active-topic': selectedTopic?.id === topic.id }"
              @click="selectTopic(topic)"
            >
              <el-list-item-main>
                <div class="topic-title">{{ topic.title }}</div>
                <div class="topic-desc">{{ topic.description }}</div>
              </el-list-item-main>
              <el-list-item-action>
                <el-tag size="small" :type="getTopicStatusType(topic.status)">
                  {{ getTopicStatusText(topic.status) }}
                </el-tag>
              </el-list-item-action>
            </el-list-item>
          </el-list>
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

          <el-button
            type="primary"
            style="width: 100%; margin-top: 20px;"
            :loading="generating"
            @click="generateContent"
          >
            AI 生成内容
          </el-button>
        </Card>
      </el-col>

      <!-- 右侧：内容编辑 -->
      <el-col :span="16">
        <Card title="内容编辑">
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import ContentEditor from '@components/ContentEditor.vue'
import { topicApi, contentApi } from '@services/api'

const router = useRouter()

const topicSearch = ref('')
const topics = ref([])
const selectedTopic = ref<any>(null)
const generating = ref(false)
const saving = ref(false)
const submitting = ref(false)

const contentForm = reactive({
  topic_id: 0,
  title: '',
  content_text: '',
  content_type: 'article',
  platforms: ['xiaohongshu', 'wechat'],
  tone: 'professional',
  length: 'medium'
})

const filteredTopics = computed(() => {
  if (!topicSearch.value) return topics.value
  return topics.value.filter(topic =>
    topic.title.toLowerCase().includes(topicSearch.value.toLowerCase())
  )
})

const fetchData = async () => {
  try {
    const result: any = await topicApi.list({ page: 1, pageSize: 100 })
    if (result?.data) {
      topics.value = result.data.list
    }
  } catch (error) {
    console.error('Failed to fetch topics:', error)
  }
}

const selectTopic = (topic: any) => {
  selectedTopic.value = topic
  contentForm.topic_id = topic.id
  contentForm.title = `关于${topic.title}的分享`
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

// ---- AI 生成内容 ----
const generateContent = async () => {
  if (!selectedTopic.value) {
    ElMessage.warning('请先选择一个选题')
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
    if (result?.data) {
      contentForm.title = result.data.title
      contentForm.content_text = result.data.content_text
      ElMessage.success('内容生成成功')
    }
  } catch (error) {
    console.error('Failed to generate content:', error)
    ElMessage.error('内容生成失败')
  } finally {
    generating.value = false
  }
}

// ---- 保存草稿 ----
const saveDraft = async () => {
  if (!contentForm.title) {
    ElMessage.warning('请输入内容标题')
    return
  }
  if (!contentForm.content_text) {
    ElMessage.warning('请输入内容正文')
    return
  }

  saving.value = true
  try {
    await contentApi.create({
      topic_id: contentForm.topic_id,
      title: contentForm.title,
      content_text: contentForm.content_text,
      content_type: contentForm.content_type,
      platform: contentForm.platforms[0],
    })
    ElMessage.success('草稿保存成功')
    router.push('/content')
  } catch (error) {
    console.error('Failed to save draft:', error)
    ElMessage.error('保存草稿失败')
  } finally {
    saving.value = false
  }
}

// ---- 提交审核 ----
const submitForReview = async () => {
  if (!contentForm.title) {
    ElMessage.warning('请输入内容标题')
    return
  }
  if (!contentForm.content_text) {
    ElMessage.warning('请输入内容正文')
    return
  }

  submitting.value = true
  try {
    // 先创建内容
    const result: any = await contentApi.create({
      topic_id: contentForm.topic_id,
      title: contentForm.title,
      content_text: contentForm.content_text,
      content_type: contentForm.content_type,
      platform: contentForm.platforms[0],
    })

    const contentId = result?.data?.id
    if (contentId) {
      // 提交审核
      await contentApi.review(contentId, {
        status: 'approved',
        review_note: ''
      })
    }
    ElMessage.success('已提交审核')
    router.push('/content')
  } catch (error) {
    console.error('Failed to submit for review:', error)
    ElMessage.error('提交审核失败')
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

.active-topic {
  background: #EFF4FF;
  border: 1px solid #3370FF;
  border-radius: 6px;
}

.topic-title {
  font-weight: 500;
  color: #1F2329;
  margin-bottom: 4px;
}

.topic-desc {
  font-size: 12px;
  color: #8F959E;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
