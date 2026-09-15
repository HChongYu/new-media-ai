<template>
  <div class="page-header">
    <div class="header-left">
      <BackButton v-if="showBack" />
      <h1 class="page-title">{{ title }}</h1>
    </div>
    <div v-if="actions?.length > 0" class="header-right">
      <el-button
        v-for="(action, index) in actions"
        :key="index"
        :type="action.type || 'primary'"
        :plain="action.plain"
        :icon="action.icon"
        @click="handleAction(action)"
      >
        {{ action.label }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
// import { defineProps, defineEmits } from 'vue'

const props = defineProps<{
  title: string
  showBack?: boolean
  actions?: PageAction[]
}>()

const emit = defineEmits<{
  (e: 'action', action: PageAction): void
}>()

const handleAction = (action: PageAction) => {
  emit('action', action)
}

export interface PageAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  plain?: boolean
  icon?: string
  key: string
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1F2329;
  margin: 0;
}
</style>
