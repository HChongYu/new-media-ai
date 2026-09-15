<template>
  <div class="card" :class="{ 'card-bordered': bordered }">
    <div v-if="title" class="card-header">
      <h3 class="card-title">{{ title }}</h3>
      <div v-if="actions" class="card-actions">
        <slot name="actions"></slot>
      </div>
    </div>
    <div class="card-body">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  bordered?: boolean
}>()
</script>

<style scoped>
.card {
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #EBEDF0;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-bordered {
  border: 1px solid #DEE0E3;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #EBEDF0;
}

.card-title {
  font-size: 15px;
  font-weight: 500;
  color: #1F2329;
}

.card-body {
  padding: 20px;
}
</style>
