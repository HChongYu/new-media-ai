<template>
  <div class="layout-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="240px" class="sidebar">
        <div class="sidebar-header">
          <h2 class="logo">AI运营平台</h2>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          :router="true"
          class="sidebar-menu"
        >
          <el-menu-item index="/">
            <el-icon><House /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          
          <el-sub-menu index="1">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>选题管理</span>
            </template>
            <el-menu-item index="/topics">
              <span>选题列表</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="2">
            <template #title>
              <el-icon><Edit /></el-icon>
              <span>内容管理</span>
            </template>
            <el-menu-item index="/content">
              <span>内容列表</span>
            </el-menu-item>
            <el-menu-item index="/content/create">
              <span>创建内容</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="3">
            <template #title>
              <el-icon><Picture /></el-icon>
              <span>图片管理</span>
            </template>
            <el-menu-item index="/images">
              <span>图片列表</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="4">
            <template #title>
              <el-icon><Share /></el-icon>
              <span>发布管理</span>
            </template>
            <el-menu-item index="/publish">
              <span>发布记录</span>
            </el-menu-item>
          </el-sub-menu>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
        
        <div class="sidebar-footer">
          <div class="user-info">
            <el-avatar :size="32" :src="userAvatar">
              <span>{{ userName | initial }}</span>
            </el-avatar>
            <div class="user-details">
              <div class="user-name">{{ userName }}</div>
              <div class="user-role">{{ userRole }}</div>
            </div>
          </div>
          <el-button type="danger" text size="small" @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-for="item in breadcrumb" :key="item.path">
                {{ item.meta.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-icon class="bell" size="20"><Bell /></el-icon>
            <el-badge :value="notificationCount" class="notification">
              <el-icon class="bell" size="20"><ChatDotRound /></el-icon>
            </el-badge>
          </div>
        </el-header>
        
        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@stores/user'
import { useRouter } from 'vue-router'
import { authApi } from '@services/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

const userName = computed(() => userStore.user?.username || '管理员')
const userRole = computed(() => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    editor: '编辑',
    viewer: '查看者'
  }
  return roleMap[userStore.user?.role || 'admin'] || '管理员'
})
const userAvatar = computed(() => userStore.user?.avatar || '')

const notificationCount = ref(3)

const breadcrumb = computed(() => {
  const matched = route.matched.filter(item => item.meta.title)
  return matched
})

const handleLogout = async () => {
  try {
    await authApi.logout()
    userStore.clearAuth()
    router.push('/login')
  } catch (error) {
    console.error('Failed to logout:', error)
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background: #F5F6F7;
}

.sidebar {
  background: #FFFFFF;
  border-right: 1px solid #EBEDF0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px 16px;
  text-align: center;
  border-bottom: 1px solid #EBEDF0;
}

.logo {
  color: #1F2329;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.5px;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding: 8px;
}

/* 飞书风格菜单项 */
:deep(.el-menu-item) {
  border-radius: 6px;
  margin-bottom: 2px;
  color: #4E5969;
  height: 40px;
  line-height: 40px;
}

:deep(.el-menu-item:hover) {
  background: #F2F3F5;
  color: #1F2329;
}

:deep(.el-menu-item.is-active) {
  background: #EFF4FF;
  color: #3370FF;
  font-weight: 500;
}

:deep(.el-sub-menu__title) {
  border-radius: 6px;
  margin-bottom: 2px;
  color: #4E5969;
  height: 40px;
  line-height: 40px;
}

:deep(.el-sub-menu__title:hover) {
  background: #F2F3F5;
  color: #1F2329;
}

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
  min-width: auto;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #EBEDF0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.user-details {
  flex: 1;
  overflow: hidden;
}

.user-name {
  color: #1F2329;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  color: #8F959E;
  font-size: 12px;
}

.header {
  background: #FFFFFF;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 52px;
  border-bottom: 1px solid #EBEDF0;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.bell {
  color: #4E5969;
  cursor: pointer;
  transition: color 0.2s;
}

.bell:hover {
  color: #3370FF;
}

.notification {
  position: relative;
}

.main {
  padding: 20px;
  overflow-y: auto;
  height: calc(100vh - 52px);
}
</style>
