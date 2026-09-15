<template>
  <div class="topic-edit">
    <BackButton />
    <PageHeader title="编辑选题" :actions="pageActions" @action="handlePageAction" />

    <Card>
      <DataForm
        ref="formRef"
        v-model="form"
        :fields="fields"
        label-width="100px"
      />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BackButton from '@components/BackButton.vue'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { DataForm } from '@components/data-driven'
import type { FormField } from '@components/data-driven'
import { topicApi } from '@services/api'

const route = useRoute()
const router = useRouter()

const formRef = ref()
const topicId = ref<number>(Number(route.params.id))
const form = ref<Record<string, any>>({
  title: '',
  description: '',
  category: '',
  status: 'draft',
})

const fields: FormField[] = [
  {
    prop: 'title',
    label: '选题标题',
    cellType: 'input',
    span: 24,
    required: true,
    placeholder: '请输入选题标题',
  },
  {
    prop: 'description',
    label: '选题描述',
    cellType: 'textarea',
    span: 24,
    required: true,
    placeholder: '请输入选题描述',
    controlProps: { rows: 4, maxlength: 500, showWordLimit: true },
  },
  {
    prop: 'category',
    label: '分类',
    cellType: 'input',
    span: 24,
    placeholder: '可选',
  },
  {
    prop: 'status',
    label: '状态',
    cellType: 'select',
    span: 24,
    dataSource: {
      list: [
        { label: '草稿', value: 'draft' },
        { label: '待审核', value: 'pending' },
        { label: '已通过', value: 'approved' },
        { label: '已拒绝', value: 'rejected' },
      ],
    },
  },
]

const pageActions: PageAction[] = [
  { label: '保存', type: 'primary', icon: 'Check', key: 'save' },
  { label: '取消', type: 'info', icon: 'Close', key: 'cancel' },
]

const fetchData = async () => {
  try {
    const result: any = await topicApi.detail(topicId.value)
    if (result?.data) {
      form.value = {
        title: result.data.title || '',
        description: result.data.description || '',
        category: result.data.category || '',
        status: result.data.status || 'draft',
      }
    }
  } catch (error) {
    console.error('Failed to fetch topic detail:', error)
    ElMessage.error('获取选题详情失败')
  }
}

function handlePageAction(action: PageAction) {
  if (action.key === 'save') {
    handleSave()
  } else if (action.key === 'cancel') {
    router.push(`/topic/detail/${topicId.value}`)
  }
}

const handleSave = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  try {
    await topicApi.update(topicId.value, form.value)
    ElMessage.success('保存成功')
    router.push(`/topic/detail/${topicId.value}`)
  } catch (error) {
    console.error('Failed to update topic:', error)
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.topic-edit {
  padding: 20px;
}
</style>
