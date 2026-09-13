<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  // 全局错误处理
  window.onerror = (message, source, lineno, colno, error) => {
    console.error('Global error:', { message, source, lineno, colno, error })
  }
  
  window.onunhandledrejection = (event) => {
    console.error('Unhandled rejection:', event.reason)
  }
})
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
