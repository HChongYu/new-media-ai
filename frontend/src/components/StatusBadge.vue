<template>
  <div class="status-badge" :class="`status-${status}`">
    {{ statusText }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
}>()

const statusText = computed(() => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    reviewing: '审核中',
    published: '已发布',
    failed: '发布失败'
  }
  return statusMap[props.status] || props.status
})
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-draft {
  background: #f0f0f0;
  color: #909399;
}

.status-pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-approved {
  background: #f0f9ff;
  color: #409eff;
}

.status-rejected {
  background: #fef0f0;
  color: #f56c6c;
}

.status-reviewing {
  background: #f4f4f5;
  color: #909399;
}

.status-published {
  background: #f0f9ff;
  color: #67c23a;
}

.status-failed {
  background: #fef0f0;
  color: #f56c6c;
}
</style>
