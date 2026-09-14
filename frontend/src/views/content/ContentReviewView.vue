<template>
  <div class="content-review">
    <BackButton />
    <PageHeader title="内容审核" />
    
    <el-row :gutter="20">
      <!-- 内容展示 -->
      <el-col :span="16">
        <Card :title="content?.title || '内容详情'">
          <div class="content-info">
            <div class="info-item">
              <span class="label">创建人：</span>
              <span class="value">{{ content?.created_by_name || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatDate(content?.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">字数：</span>
              <span class="value">{{ content?.word_count || 0 }} 字</span>
            </div>
            <div class="info-item">
              <span class="label">内容类型：</span>
              <span class="value">{{ content?.content_type === 'article' ? '文章' : '图片' }}</span>
            </div>
          </div>
          
          <div class="content-body">
            <MarkdownViewer :content="content?.content_text || ''" />
          </div>
        </Card>
        
        <Card title="关联图片" style="margin-top: 20px;">
          <ImageGrid
            :images="contentImages"
            show-download
            show-delete
            @view="viewImage"
            @delete="deleteImage"
          />
        </Card>
      </el-col>
      
      <!-- 审核操作 -->
      <el-col :span="8">
        <Card title="审核操作">
          <el-form :model="reviewForm" label-width="80px">
            <el-form-item label="审核结果">
              <el-radio-group v-model="reviewForm.status">
                <el-radio value="approved">通过</el-radio>
                <el-radio value="rejected">拒绝</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="审核意见" v-if="reviewForm.status === 'rejected'">
              <el-input
                v-model="reviewForm.review_note"
                type="textarea"
                placeholder="请输入拒绝原因..."
                :rows="4"
              />
            </el-form-item>
            
            <el-form-item label="发布平台">
              <el-checkbox-group v-model="reviewForm.platforms">
                <el-checkbox value="xiaohongshu">小红书</el-checkbox>
                <el-checkbox value="wechat">微信公众号</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
          
          <div class="action-buttons">
            <el-button
              type="success"
              style="width: 100%; margin-bottom: 12px;"
              :loading="reviewing"
              @click="approveContent"
            >
              通过审核
            </el-button>
            <el-button
              type="danger"
              style="width: 100%;"
              :loading="reviewing"
              @click="rejectContent"
            >
              拒绝审核
            </el-button>
          </div>
        </Card>
        
        <Card title="发布操作" style="margin-top: 20px;">
          <el-button
            v-for="platform in platforms"
            :key="platform.value"
            :type="platform.type"
            style="width: 100%; margin-bottom: 12px;"
            :loading="publishing[platform.value]"
            @click="publishContent(platform.value)"
          >
            <el-icon :size="16" style="margin-right: 8px;">
              <component :is="platform.icon" />
            </el-icon>
            发布到 {{ platform.label }}
          </el-button>
        </Card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import MarkdownViewer from '@components/MarkdownViewer.vue'
import ImageGrid from '@components/ImageGrid.vue'
import { contentApi, imageApi, publishApi } from '@services/api'

const route = useRoute()
const router = useRouter()

const contentId = ref<number>(Number(route.params.id))
const content = ref<any>(null)
const contentImages = ref([])
const reviewing = ref(false)
const publishing = ref<Record<string, boolean>>({})
const reviewForm = reactive({
  status: 'approved',
  review_note: '',
  platforms: ['xiaohongshu', 'wechat']
})

const platforms = [
  { value: 'xiaohongshu', label: '小红书', type: 'primary', icon: 'ChatDotRound' },
  { value: 'wechat', label: '微信公众号', type: 'success', icon: 'Bell' }
]

const fetchData = async () => {
  try {
    const result: any = await contentApi.detail(contentId.value)
    if (result?.data) {
      content.value = result.data
    }
    
    const imagesRes: any = await imageApi.byContent(contentId.value)
    if (imagesRes?.data) {
      contentImages.value = imagesRes.data
    }
  } catch (error) {
    console.error('Failed to fetch content:', error)
    ElMessage.error('获取内容详情失败')
  }
}

const approveContent = async () => {
  if (reviewForm.status === 'approved') {
    try {
      reviewing.value = true
      await contentApi.review(contentId.value, {
        status: 'approved',
        review_note: reviewForm.review_note
      })
      ElMessage.success('审核通过')
      router.push('/content')
    } catch (error) {
      console.error('Failed to approve content:', error)
    } finally {
      reviewing.value = false
    }
  }
}

const rejectContent = async () => {
  if (reviewForm.status === 'rejected' && !reviewForm.review_note) {
    ElMessage.warning('请填写拒绝原因')
    return
  }
  
  try {
    reviewing.value = true
    await contentApi.review(contentId.value, {
        status: 'rejected',
        review_note: reviewForm.review_note
      })
    ElMessage.success('审核已拒绝')
    router.push('/content')
  } catch (error) {
    console.error('Failed to reject content:', error)
  } finally {
    reviewing.value = false
  }
}

const publishContent = async (platform: string) => {
  try {
    publishing.value[platform] = true
    await publishApi.create(contentId.value, platform as any)
    ElMessage.success(`已发布到 ${platform}`)
  } catch (error) {
    console.error(`Failed to publish to ${platform}:`, error)
  } finally {
    publishing.value[platform] = false
  }
}

const viewImage = (image: any) => {
  window.open(image.image_url, '_blank')
}

const deleteImage = async (image: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？', '警告', {
      type: 'warning'
    })
    await imageApi.delete(image.id)
    ElMessage.success('删除成功')
    contentImages.value = contentImages.value.filter(i => i.id !== image.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete image:', error)
    }
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.content-review {
  padding: 20px;
}

.content-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.info-item .label {
  color: #909399;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.content-body {
  min-height: 400px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
