<template>
  <div class="settings">
    <PageHeader title="系统设置" :actions="pageActions" />
    
    <el-tabs v-model="activeTab" type="card">
      <!-- 账号设置 -->
      <el-tab-pane label="账号设置" name="account">
        <Card title="账号信息">
          <el-form :model="userForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="userForm.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userForm.email" />
            </el-form-item>
            <el-form-item label="头像">
              <el-upload
                class="avatar-uploader"
                action="/api/upload/avatar"
                :show-file-list="false"
                :on-success="handleAvatarSuccess"
              >
                <img v-if="userForm.avatar" :src="userForm.avatar" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateAccount">保存修改</el-button>
            </el-form-item>
          </el-form>
        </Card>
        
        <Card title="修改密码" style="margin-top: 20px;">
          <el-form :model="passwordForm" label-width="100px">
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updatePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </Card>
      </el-tab-pane>
      
      <!-- AI 设置 -->
      <el-tab-pane label="AI 设置" name="ai">
        <Card title="LLM 配置">
          <el-form :model="aiForm" label-width="120px">
            <el-form-item label="LLM 提供商">
              <el-select v-model="aiForm.llm_provider" placeholder="请选择">
                <el-option label="OpenAI" value="openai" />
                <el-option label="Anthropic" value="anthropic" />
                <el-option label="本地模型" value="local" />
              </el-select>
            </el-form-item>
            <el-form-item label="模型名称">
              <el-input v-model="aiForm.llm_model" placeholder="例如: gpt-4" />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="aiForm.api_key" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateAIConfig">保存配置</el-button>
            </el-form-item>
          </el-form>
        </Card>
        
        <Card title="内容偏好" style="margin-top: 20px;">
          <el-form :model="aiForm" label-width="120px">
            <el-form-item label="默认风格">
              <el-select v-model="aiForm.default_tone" placeholder="请选择">
                <el-option label="专业严谨" value="professional" />
                <el-option label="轻松活泼" value="casual" />
                <el-option label="热情洋溢" value="enthusiastic" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认长度">
              <el-select v-model="aiForm.default_length" placeholder="请选择">
                <el-option label="短篇 (500字以内)" value="short" />
                <el-option label="中篇 (500-1500字)" value="medium" />
                <el-option label="长篇 (1500字以上)" value="long" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updatePreferences">保存偏好</el-button>
            </el-form-item>
          </el-form>
        </Card>
      </el-tab-pane>
      
      <!-- 平台设置 -->
      <el-tab-pane label="平台设置" name="platform">
        <Card title="小红书配置">
          <el-form :model="platformForm.xiaohongshu" label-width="120px">
            <el-form-item label="自动配图">
              <el-switch v-model="platformForm.xiaohongshu.auto_generate_images" />
            </el-form-item>
            <el-form-item label="图片数量">
              <el-slider v-model="platformForm.xiaohongshu.image_count" :min="1" :max="10" />
            </el-form-item>
            <el-form-item label="默认标签">
              <el-tag
                v-for="(tag, index) in platformForm.xiaohongshu.default_tags"
                :key="index"
                closable
                @close="removeTag('xiaohongshu', index)"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-if="xiaohongshuTagInputVisible"
                ref="xiaohongshuTagInput"
                v-model="xiaohongshuTagInputValue"
                class="tag-input"
                size="small"
                @keyup.enter="addTag('xiaohongshu')"
                @blur="addTag('xiaohongshu')"
              />
              <el-button
                v-else
                class="button-new-tag"
                size="small"
                @click="showTagInput('xiaohongshu')"
              >
                + 添加标签
              </el-button>
            </el-form-item>
          </el-form>
        </Card>
        
        <Card title="微信公众号配置" style="margin-top: 20px;">
          <el-form :model="platformForm.wechat" label-width="120px">
            <el-form-item label="自动发布">
              <el-switch v-model="platformForm.wechat.auto_publish" />
            </el-form-item>
            <el-form-item label="默认分类">
              <el-select v-model="platformForm.wechat.default_category" placeholder="请选择">
                <el-option label="技术分享" value="tech" />
                <el-option label="学习笔记" value="note" />
                <el-option label="行业资讯" value="news" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updatePlatformSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </Card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@components/PageHeader.vue'
import Card from '@components/Card.vue'
import { settingsApi } from '@services/api'
import { useUserStore } from '@stores/user'

const userStore = useUserStore()

const activeTab = ref('account')
const xiaohongshuTagInputVisible = ref(false)
const xiaohongshuTagInputValue = ref('')

const userForm = ref({
  username: '',
  email: '',
  avatar: ''
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const aiForm = ref({
  llm_provider: '',
  llm_model: '',
  api_key: '',
  default_tone: 'professional',
  default_length: 'medium'
})

const platformForm = ref({
  xiaohongshu: {
    auto_generate_images: true,
    image_count: 3,
    default_tags: ['AI编程', '技术分享', '学习笔记']
  },
  wechat: {
    auto_publish: false,
    default_category: 'tech'
  }
})

const pageActions = [
  { label: '保存所有设置', type: 'primary', icon: 'Check', key: 'save-all' }
]

const fetchData = async () => {
  try {
    const res: any = await settingsApi.get()
    if (res?.data) {
      const settings = res.data
      aiForm.value = {
        llm_provider: settings.llm_provider || '',
        llm_model: settings.llm_model || '',
        api_key: settings.api_key || '',
        default_tone: settings.default_tone || 'professional',
        default_length: settings.default_length || 'medium'
      }
      platformForm.value = settings.platform_settings || platformForm.value
    }
    
    const user = userStore.user
    if (user) {
      userForm.value = {
        username: user.username,
        email: user.email,
        avatar: user.avatar || ''
      }
    }
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  }
}

const updateAccount = async () => {
  try {
    // TODO: 调用更新账号信息 API
    ElMessage.success('账号信息更新成功')
  } catch (error) {
    console.error('Failed to update account:', error)
  }
}

const updatePassword = async () => {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  
  try {
    // TODO: 调用修改密码 API
    ElMessage.success('密码修改成功')
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (error) {
    console.error('Failed to update password:', error)
  }
}

const updateAIConfig = async () => {
  try {
    await settingsApi.update({
      llm_provider: aiForm.value.llm_provider,
      llm_model: aiForm.value.llm_model,
      api_key: aiForm.value.api_key
    } as any)
    ElMessage.success('AI 配置保存成功')
  } catch (error) {
    console.error('Failed to update AI config:', error)
  }
}

const updatePreferences = async () => {
  try {
    await settingsApi.update({
      default_tone: aiForm.value.default_tone,
      default_length: aiForm.value.default_length
    } as any)
    ElMessage.success('偏好设置保存成功')
  } catch (error) {
    console.error('Failed to update preferences:', error)
  }
}

const updatePlatformSettings = async () => {
  try {
    await settingsApi.update({
      platform_settings: platformForm.value
    } as any)
    ElMessage.success('平台设置保存成功')
  } catch (error) {
    console.error('Failed to update platform settings:', error)
  }
}

const handleAvatarSuccess = (response: any) => {
  if (response.code === 200) {
    userForm.value.avatar = response.data.url
    ElMessage.success('头像上传成功')
  }
}

const showTagInput = (platform: string) => {
  xiaohongshuTagInputVisible.value = true
  setTimeout(() => {
    // TODO: 聚焦输入框
  }, 10)
}

const addTag = (platform: string) => {
  if (xiaohongshuTagInputValue.value) {
    platformForm.value.xiaohongshu.default_tags.push(xiaohongshuTagInputValue.value)
    xiaohongshuTagInputValue.value = ''
  }
  xiaohongshuTagInputVisible.value = false
}

const removeTag = (platform: string, index: number) => {
  platformForm.value.xiaohongshu.default_tags.splice(index, 1)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.settings {
  padding: 20px;
}

.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  object-fit: cover;
}

.avatar-uploader .avatar-uploader-icon {
  width: 100px;
  height: 100px;
  font-size: 28px;
  color: #909399;
  text-align: center;
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
}

.avatar-uploader .avatar-uploader-icon:hover {
  border-color: #409eff;
}

.tag-input {
  margin-top: 8px;
}

.button-new-tag {
  margin-top: 8px;
}
</style>
