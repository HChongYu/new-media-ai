import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { store } from '@stores/index'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@views/login/LoginView.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('@views/layout/LayoutView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'topics',
        name: 'TopicList',
        component: () => import('@views/topic/TopicListView.vue'),
        meta: { title: '选题管理' }
      },
      {
        path: 'topics/:id',
        name: 'TopicDetail',
        component: () => import('@views/topic/TopicDetailView.vue'),
        meta: { title: '选题详情' }
      },
      {
        path: 'content',
        name: 'ContentList',
        component: () => import('@views/content/ContentListView.vue'),
        meta: { title: '内容管理' }
      },
      {
        path: 'content/create',
        name: 'ContentCreate',
        component: () => import('@views/content/ContentCreateView.vue'),
        meta: { title: '创建内容' }
      },
      {
        path: 'content/:id/review',
        name: 'ContentReview',
        component: () => import('@views/content/ContentReviewView.vue'),
        meta: { title: '内容审核' }
      },
      {
        path: 'images',
        name: 'ImageList',
        component: () => import('@views/image/ImageListView.vue'),
        meta: { title: '图片管理' }
      },
      {
        path: 'publish',
        name: 'PublishHistory',
        component: () => import('@views/publish/PublishHistoryView.vue'),
        meta: { title: '发布记录' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@views/settings/SettingsView.vue'),
        meta: { title: '系统设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - AI自媒体运营平台` : 'AI自媒体运营平台'
  
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  if (to.path === '/login' && token) {
    next('/')
    return
  }
  
  next()
})

export default router
