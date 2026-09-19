import request from './request'

// ========== 认证相关 ==========
export const authApi = {
  login: (data: { username: string; password: string }) =>
    request.post('/auth/login', data),
  logout: () =>
    request.post('/auth/logout'),
  me: () =>
    request.get('/auth/me'),
  updateProfile: (data: { email?: string; avatar?: string }) =>
    request.put('/auth/profile', data),
  changePassword: (data: { old_password: string; new_password: string }) =>
    request.put('/auth/password', data)
}

// ========== 选题相关 ==========
export const topicApi = {
  list: (params?: TopicQueryParams) =>
    request.get('/topics', { params }),
  detail: (id: number) =>
    request.get(`/topics/${id}`),
  generate: (data: TopicGenerateParams) =>
    request.post('/topics/generate', data, { timeout: 120000 }),
  create: (data: TopicCreateParams) =>
    request.post('/topics', data),
  update: (id: number, data: TopicUpdateParams) =>
    request.put(`/topics/${id}`, data),
  delete: (id: number) =>
    request.delete(`/topics/${id}`)
}

// ========== 内容相关 ==========
export const contentApi = {
  list: (params?: ContentQueryParams) =>
    request.get('/contents', { params }),
  detail: (id: number) =>
    request.get(`/contents/${id}`),
  generate: (topicId: number, params?: ContentGenerateParams) =>
    request.post(`/topics/${topicId}/content`, params, { timeout: 120000 }),
  create: (data: ContentCreateParams) =>
    request.post('/contents', data),
  update: (id: number, data: ContentUpdateParams) =>
    request.put(`/contents/${id}`, data),
  review: (id: number, data: ContentReviewParams) =>
    request.post(`/contents/${id}/review`, data),
  delete: (id: number) =>
    request.delete(`/contents/${id}`)
}

// ========== 图片相关 ==========
export const imageApi = {
  list: (params?: ImageQueryParams) =>
    request.get('/images', { params }),
  byContent: (contentId: number) =>
    request.get(`/contents/${contentId}/images`),
  generate: (contentId: number, data: ImageGenerateParams) =>
    request.post(`/contents/${contentId}/images/generate`, data, { timeout: 120000 }),
  delete: (id: number) =>
    request.delete(`/images/${id}`)
}

// ========== 发布相关 ==========
export const publishApi = {
  history: (params?: PublishQueryParams) =>
    request.get('/publish/history', { params }),
  create: (contentId: number, platform: 'xiaohongshu' | 'wechat') =>
    request.post(`/contents/${contentId}/publish/${platform}`),
  delete: (id: number) =>
    request.delete(`/publish/${id}`)
}

// ========== 统一图文工作流相关 ==========
export const workflowApi = {
  start: (data: WorkflowStartParams) =>
    request.post('/workflows/start', data, { timeout: 180000 }),
  resume: (threadId: string, data: WorkflowResumeParams) =>
    request.post(`/workflows/${threadId}/resume`, data, { timeout: 300000 }),
  detail: (threadId: string) =>
    request.get(`/workflows/${threadId}`),
  list: (params?: WorkflowListQueryParams) =>
    request.get('/workflows', { params })
}

// ========== 设置相关 ==========
export const settingsApi = {
  get: () =>
    request.get('/settings'),
  update: (data: SettingsUpdateParams) =>
    request.put('/settings', data)
}

// ========== 仪表盘相关 ==========
export const dashboardApi = {
  stats: () =>
    request.get('/dashboard/stats')
}

// ========== 类型定义 ==========
export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  role: 'admin' | 'editor' | 'viewer'
  created_at: string
}

export interface Pagination {
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface Topic {
  id: number
  title: string
  description: string
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  content_count: number
  created_by: number
  created_by_name?: string
  created_at: string
  approved_at?: string
}

export interface TopicQueryParams {
  page?: number
  pageSize?: number
  page_size?: number
  status?: string
  keyword?: string
  start_date?: string
  end_date?: string
}

export interface TopicGenerateParams {
  keywords?: string[]
  category?: string
  target_audience?: string
  content_style?: string
  count?: number
}

export interface TopicCreateParams {
  title: string
  description: string
  category?: string
  tags?: string[]
}

export interface TopicUpdateParams {
  title?: string
  description?: string
  status?: string
  category?: string
  tags?: string[]
}

export interface Content {
  id: number
  topic_id: number
  topic_title?: string
  title: string
  content_text: string
  content_type: 'article' | 'image'
  word_count: number
  status: 'draft' | 'reviewing' | 'approved' | 'published'
  created_by: number
  created_by_name?: string
  reviewed_by?: number
  reviewed_by_name?: string
  created_at: string
  reviewed_at?: string
  published_at?: string
}

export interface ContentQueryParams {
  page?: number
  pageSize?: number
  page_size?: number
  status?: string
  content_type?: string
  topic_id?: number
  keyword?: string
  start_date?: string
  end_date?: string
}

export interface ContentGenerateParams {
  platform?: 'xiaohongshu' | 'wechat'
  tone?: 'professional' | 'casual' | 'enthusiastic'
  length?: 'short' | 'medium' | 'long'
}

export interface ContentCreateParams {
  topic_id: number
  title: string
  content_text: string
  content_type?: 'article' | 'image'
  platform?: 'xiaohongshu' | 'wechat'
}

export interface ContentUpdateParams {
  title?: string
  content_text?: string
  status?: string
}

export interface ContentReviewParams {
  status: 'approved' | 'rejected'
  review_note?: string
}

export interface Image {
  id: number
  content_id: number
  image_url: string
  image_type: 'cover' | 'section' | 'summary'
  prompt: string
  generated_at: string
  width: number
  height: number
  size?: number
}

export interface ImageQueryParams {
  page?: number
  pageSize?: number
  page_size?: number
  content_id?: number
  image_type?: string
  start_date?: string
  end_date?: string
}

export interface ImageGenerateParams {
  image_type?: ('cover' | 'section' | 'summary')[]
  count?: number
  style?: 'minimalist' | 'professional' | 'creative' | 'elegant'
  width?: number
  height?: number
}

export interface PublishRecord {
  id: number
  content_id: number
  content_title?: string
  platform: 'xiaohongshu' | 'wechat'
  post_url?: string
  status: 'pending' | 'published' | 'failed'
  published_at?: string
  error_message?: string
  created_at: string
}

export interface PublishQueryParams {
  page?: number
  pageSize?: number
  page_size?: number
  platform?: string
  status?: string
  start_date?: string
  end_date?: string
}

export interface Settings {
  id: number
  user_id: number
  preferred_topics: string[]
  preferred_formats: string[]
  llm_provider?: string
  llm_model?: string
  image_style?: string
  platform_settings?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface SettingsUpdateParams {
  preferred_topics?: string[]
  preferred_formats?: string[]
  llm_provider?: string
  llm_model?: string
  image_style?: string
  platform_settings?: Record<string, unknown>
}

export type ActivityType = 'topic' | 'content' | 'image' | 'publish'

export interface DashboardActivity {
  type: ActivityType
  ref_id: number
  title: string
  time: string
}

export interface DashboardStats {
  total_topics: number
  total_contents: number
  total_images: number
  published_count: number
  recent_activities: DashboardActivity[]
}

// ========== 统一图文工作流类型 ==========
/** 业务状态：awaiting_select 待选选题 / reviewing 待审核 / completed 已完成 等 */
export type WorkflowProjectStatus =
  | 'awaiting_select'
  | 'writing'
  | 'reviewing'
  | 'generating_images'
  | 'completed'

/** 图中断点：human_select 人工选题 / human_review 人工审稿 / null 已结束 */
export type WorkflowNextStep = 'human_select' | 'human_review' | null

export interface ProposedTopic {
  title: string
  description: string
  category: string
  tags: string[]
}

export interface VisualPoint {
  point: string
  detail: string
  image_prompt: string
}

export interface WorkflowProject {
  id: string
  thread_id: string
  topic_direction: string
  topic: string
  platform: 'xiaohongshu' | 'wechat'
  status: WorkflowProjectStatus
  revision_count: number
  article_content: { title: string; content: string } | null
  image_assets: string[] | null
  created_at: string
  updated_at: string
}

/** GET/start/resume 返回的统一运行状态 */
export interface WorkflowRunState {
  project: WorkflowProject
  next_step: WorkflowNextStep
  interrupt: Record<string, unknown> | null
  completed: boolean
  proposed_topics: ProposedTopic[]
  selected_topic: string
  draft_title: string
  draft_content: string
  final_content: string
  visual_points: VisualPoint[]
  image_urls: string[]
  revision_count: number
}

export interface WorkflowStartParams {
  topic_direction: string
  platform?: 'xiaohongshu' | 'wechat'
}

export interface WorkflowResumeParams {
  action: 'select_topic' | 'review'
  /** action=select_topic 时：选中的标题 */
  data?: string
  /** action=review 时：approve / reject */
  status?: 'approve' | 'reject'
  /** action=review 且 reject 时的修改意见 */
  feedback?: string
}

export interface WorkflowListQueryParams {
  page?: number
  page_size?: number
  status?: WorkflowProjectStatus
}
