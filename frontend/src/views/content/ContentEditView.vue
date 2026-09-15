<template>
  <div class="content-edit">
    <BackButton />
    <PageHeader title="编辑内容" />

    <Card>
      <ContentEditor
        v-model="contentForm.content_text"
        v-model:titleValue="contentForm.title"
        :show-preview="true"
      />
    </Card>

    <div class="action-buttons" style="margin-top: 20px;">
      <el-button :loading="saving" @click="saveContent">保存</el-button>
      <el-button type="primary" @click="goBack">返回</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import ContentEditor from '@components/ContentEditor.vue'
import { contentApi } from '@services/api'

const route = useRoute()
const router = useRouter()

const contentId = ref<number>(Number(route.params.id))
const saving = ref(false)

const contentForm = reactive({
  title: '',
  content_text: '',
})

async function fetchData() {
  try {
    const result: any = await contentApi.detail(contentId.value)
    if (result?.data) {
      contentForm.title = result.data.title || ''
      contentForm.content_text = result.data.content_text || ''
    }
  } catch (error) {
    console.error('Failed to fetch content:', error)
    ElMessage.error('获取内容详情失败')
  }
}

async function saveContent() {
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
    await contentApi.update(contentId.value, {
      title: contentForm.title,
      content_text: contentForm.content_text,
    })
    ElMessage.success('保存成功')
    router.push(`/content/detail/${contentId.value}`)
  } catch (error) {
    console.error('Failed to save content:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.back()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.content-edit {
  padding: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
