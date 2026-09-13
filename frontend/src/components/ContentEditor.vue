<template>
  <div class="content-editor">
    <div class="editor-header">
      <el-input
        v-model="title"
        placeholder="输入标题..."
        size="large"
        clearable
      />
    </div>
    <div class="editor-toolbar">
      <el-button-group>
        <el-button size="small" @click="formatText('bold')">
          <el-icon><Bold /></Bold></el-icon>
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
import { ref, computed, onMounted } from 'vue'
import { Bold, Italic, Underline, Delete, ChatDotRound } from '@element-plus/icons-vue'

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
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.editor-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  background: #ffffff;
}

.editor-body textarea:focus {
  outline: none;
}

.editor-stats {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #909399;
}

.editor-preview {
  border-top: 1px solid #e4e7ed;
}

.editor-preview h4 {
  padding: 12px 20px;
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  background: #f5f7fa;
  color: #606266;
}

.preview-content {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.preview-content h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
}
</style>
