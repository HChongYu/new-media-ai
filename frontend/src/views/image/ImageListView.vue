<template>
  <div class="image-list">
    <PageHeader title="图片管理" :actions="pageActions" @action="handlePageAction" />

    <Card>
      <DataList
        ref="dataListRef"
        :query-fields="queryFields"
        :columns="columns"
        :fetch-data="handleFetchData"
        :default-page-size="20"
        :page-sizes="[20, 50, 100]"
      >
        <!-- 图片预览列 -->
        <template #image_url="{ row }">
          <el-image
            :src="row.image_url"
            :preview-src-list="[row.image_url]"
            preview-teleported
            fit="cover"
            style="width: 80px; height: 80px; border-radius: 4px;"
          />
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <el-button type="primary" link @click="viewImage(row)">查看</el-button>
          <el-button type="danger" link @click="deleteImage(row)">删除</el-button>
        </template>
      </DataList>
    </Card>

    <!-- 批量生成图片对话框 -->
    <el-dialog v-model="batchGenerateDialog.visible" title="批量生成图片" width="500px">
      <el-form :model="batchGenerateDialog.form" label-width="100px">
        <el-form-item label="内容ID" required>
          <el-input-number
            v-model="batchGenerateDialog.form.content_id"
            :min="1"
            placeholder="请输入内容ID"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="图片类型">
          <el-checkbox-group v-model="batchGenerateDialog.form.image_types">
            <el-checkbox value="cover">封面图</el-checkbox>
            <el-checkbox value="section">正文图</el-checkbox>
            <el-checkbox value="summary">摘要图</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="生成数量">
          <el-slider v-model="batchGenerateDialog.form.count" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="图片风格">
          <el-select v-model="batchGenerateDialog.form.style" placeholder="请选择风格">
            <el-option label="极简" value="minimalist" />
            <el-option label="专业" value="professional" />
            <el-option label="创意" value="creative" />
            <el-option label="优雅" value="elegant" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import type { PageAction } from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { DataList } from '@components/data-driven'
import type { FormField, TableColumn, DataListResult } from '@components/data-driven'
import { imageApi } from '@services/api'

const dataListRef = ref()

// ---- 查询字段配置 ----
const queryFields: FormField[] = [
  {
    prop: 'image_type',
    label: '图片类型',
    cellType: 'select',
    span: 10,
    dataSource: {
      list: [
        { label: '封面图', value: 'cover' },
        { label: '正文图', value: 'section' },
        { label: '摘要图', value: 'summary' },
      ],
    },
  },
  {
    prop: 'content_id',
    label: '内容ID',
    cellType: 'input',
    span: 10,
    placeholder: '内容ID',
  },
]

// ---- 表格列配置 ----
const columns: TableColumn[] = [
  { prop: 'image_url', label: '预览', width: 100, slot: 'image_url' },
  {
    prop: 'image_type',
    label: '类型',
    width: 100,
    cellType: 'tag',
    dataSource: {
      list: [
        { label: '封面图', value: 'cover' },
        { label: '正文图', value: 'section' },
        { label: '摘要图', value: 'summary' },
      ],
    },
  },
  { prop: 'content_id', label: '内容ID', width: 100 },
  { prop: 'prompt', label: '生成提示词', minWidth: 200, showOverflowTooltip: true },
  {
    prop: 'generated_at',
    label: '生成时间',
    width: 160,
    sortable: true,
    formatter: (_row, _col, value) => formatDateTime(value),
  },
  { prop: 'actions', label: '操作', width: 120, fixed: 'right', slot: 'actions' },
]

// ---- 页头操作按钮 ----
const pageActions: PageAction[] = [
  { label: '批量生成', type: 'primary', icon: 'LightBulb', key: 'batch-generate' },
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
  const result: any = await imageApi.list(params)
  return {
    list: result?.data?.list || [],
    total: result?.data?.pagination?.total || 0,
  }
}

// ---- 批量生成对话框 ----
const batchGenerateDialog = reactive({
  visible: false,
  loading: false,
  form: {
    content_id: null as number | null,
    image_types: ['cover'] as string[],
    count: 3,
    style: 'professional'
  }
})

// ---- 页头按钮事件 ----
function handlePageAction(action: PageAction) {
  if (action.key === 'batch-generate') {
    batchGenerateDialog.form = {
      content_id: null,
      image_types: ['cover'],
      count: 3,
      style: 'professional'
    }
    batchGenerateDialog.visible = true
  }
}

// ---- 确认批量生成 ----
async function confirmBatchGenerate() {
  if (!batchGenerateDialog.form.content_id) {
    ElMessage.warning('请输入内容ID')
    return
  }

  batchGenerateDialog.loading = true
  try {
    await imageApi.generate(batchGenerateDialog.form.content_id, {
      image_type: batchGenerateDialog.form.image_types as any,
      count: batchGenerateDialog.form.count,
      style: batchGenerateDialog.form.style as any
    })
    ElMessage.success('图片生成成功')
    batchGenerateDialog.visible = false
    dataListRef.value?.refresh()
  } catch (error) {
    console.error('批量生成图片失败:', error)
  } finally {
    batchGenerateDialog.loading = false
  }
}

// ---- 表格事件 ----
function viewImage(image: any) {
  window.open(image.image_url, '_blank')
}

async function deleteImage(image: any) {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？', '警告', {
      type: 'warning',
    })
    await imageApi.delete(image.id)
    ElMessage.success('删除成功')
    dataListRef.value?.refresh()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete image:', error)
    }
  }
}
</script>

<style scoped>
.image-list {
  padding: 20px;
}
</style>
