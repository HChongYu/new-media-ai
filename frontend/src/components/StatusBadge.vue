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
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  line-height: 20px;
}

.status-draft {
  background: #F2F3F5;
  color: #8F959E;
}

.status-pending {
  background: #FFF7E8;
  color: #FF7D00;
}

.status-approved {
  background: #EFF4FF;
  color: #3370FF;
}

.status-rejected {
  background: #FFECE8;
  color: #F53F3F;
}

.status-reviewing {
  background: #F2F3F5;
  color: #8F959E;
}

.status-published {
  background: #E8FFEA;
  color: #00B365;
}

.status-failed {
  background: #FFECE8;
  color: #F53F3F;
}
</style>
