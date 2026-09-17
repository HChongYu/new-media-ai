<template>
  <div class="content-editor">
    <div class="editor-header">
      <el-input
        v-model="title"
        placeholder="输入标题..."
        size="large"
        clearable
        @input="handleTitleInput"
      />
    </div>
    <div class="editor-toolbar">
      <el-button-group>
        <el-button size="small" @click="formatText('bold')">
          <el-icon><Bold /></el-icon>
        </el-button>
        <el-button size="small" @click="formatText('italic')">
          <el-icon><Italic /></el-icon>
        </el-button>
        <el-button size="small" @click="formatText('underline')">
          <el-icon><Underline /></el-icon>
        </el-button>
        <el-button size="small" @click="formatText('strike')">
          <el-icon><Delete /></el-icon>
        </el-button>
        <el-button size="small" @click="formatText('h1')">
          H1
        </el-button>
        <el-button size="small" @click="formatText('h2')">
          H2
        </el-button>
        <el-button size="small" @click="formatText('quote')">
          <el-icon><ChatDotRound /></el-icon>
        </el-button>
      </el-button-group>
      <div class="editor-stats">
        <span>字数: {{ wordCount }}</span>
        <span>预计阅读时间: {{ readTime }} 分钟</span>
      </div>
    </div>
    <div class="editor-body">
      <textarea
        ref="editorRef"
        v-model="content"
        placeholder="开始编写内容..."
        @input="handleInput"
      ></textarea>
    </div>
    <div class="editor-preview" v-if="showPreview">
      <h4>预览</h4>
      <div class="preview-content">
        <h1>{{ title || '标题' }}</h1>
        <div v-html="renderedMarkdown"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Delete, ChatDotRound } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue?: string
  titleValue?: string
  showPreview?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'update:titleValue', value: string): void
}>()

const editorRef = ref<HTMLTextAreaElement | null>(null)
const title = ref(props.titleValue || '')
const content = ref(props.modelValue || '')

// 外部数据变化时同步到编辑器内部：
// 1) 创建页 AI 生成完成后父组件回填 2) 编辑页详情接口异步返回后回显
// 仅在内外值不一致时同步，避免输入时反复赋值导致光标跳动
watch(
  () => props.modelValue,
  (val) => {
    if (val !== content.value) {
      content.value = val || ''
    }
  }
)

watch(
  () => props.titleValue,
  (val) => {
    if (val !== title.value) {
      title.value = val || ''
    }
  }
)

const wordCount = computed(() => {
  return content.value.replace(/\s/g, '').length
})

const readTime = computed(() => {
  const words = wordCount.value
  return Math.ceil(words / 300) // 假设每分钟阅读300字
})

const renderedMarkdown = computed(() => {
  // 简单的Markdown渲染
  let html = content.value
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^(#{1,6})\s+(.*)$/gm, (match, hashes, text) => {
      const level = hashes.length
      return `<h${level}>${text}</h${level}>`
    })
    .replace(/^>\s+(.*)$/gm, '<blockquote>$1</blockquote>')
    .replace(/\n/g, '<br>')
  
  return html
})

onMounted(() => {
  if (editorRef.value) {
    editorRef.value.focus()
  }
})

const handleInput = () => {
  emit('update:modelValue', content.value)
}

const handleTitleInput = () => {
  emit('update:titleValue', title.value)
}

const formatText = (format: string) => {
  if (!editorRef.value) return
  
  const start = editorRef.value.selectionStart
  const end = editorRef.value.selectionEnd
  const text = content.value
  const selectedText = text.substring(start, end)
  
  let formattedText = ''
  
  switch (format) {
    case 'bold':
      formattedText = `**${selectedText}**`
      break
    case 'italic':
      formattedText = `*${selectedText}*`
      break
    case 'underline':
      formattedText = `<u>${selectedText}</u>`
      break
    case 'strike':
      formattedText = `<s>${selectedText}</s>`
      break
    case 'h1':
      formattedText = `# ${selectedText}`
      break
    case 'h2':
      formattedText = `## ${selectedText}`
      break
    case 'quote':
      formattedText = `> ${selectedText}`
      break
  }
  
  const newText = text.substring(0, start) + formattedText + text.substring(end)
  content.value = newText
  emit('update:modelValue', newText)
  
  // 恢复光标位置
  setTimeout(() => {
    editorRef.value!.selectionStart = start + formattedText.length - selectedText.length
    editorRef.value!.selectionEnd = start + formattedText.length - selectedText.length
    editorRef.value!.focus()
  }, 0)
}
</script>

<style scoped>
.content-editor {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #EBEDF0;
  overflow: hidden;
}

.editor-header {
  padding: 14px 20px;
  border-bottom: 1px solid #EBEDF0;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: #F5F6F7;
  border-bottom: 1px solid #EBEDF0;
}

.editor-body {
  padding: 0;
}

.editor-body textarea {
  width: 100%;
  min-height: 400px;
  padding: 20px;
  border: none;
  resize: vertical;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: #1F2329;
  background: #FFFFFF;
}

.editor-body textarea:focus {
  outline: none;
}

.editor-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #8F959E;
}

.editor-preview {
  border-top: 1px solid #EBEDF0;
}

.editor-preview h4 {
  padding: 10px 20px;
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  background: #F5F6F7;
  color: #4E5969;
}

.preview-content {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.preview-content h1 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1F2329;
}
</style>
