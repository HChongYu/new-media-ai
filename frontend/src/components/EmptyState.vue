<template>
  <div class="empty-state">
    <div class="empty-icon">
      <slot name="icon">
        <el-icon :size="64" color="#c0c4cc">
          <Box />
        </el-icon>
      </slot>
    </div>
    <p class="empty-text">{{ text }}</p>
    <div v-if="hasAction" class="empty-action">
      <slot name="action"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  text?: string
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 20px;
}

.empty-text {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.empty-action {
  margin-top: 20px;
}
</style>
