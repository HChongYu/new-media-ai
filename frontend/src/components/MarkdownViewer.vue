<template>
  <div class="markdown-content" v-html="renderedMarkdown"></div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import mdContainer from 'markdown-it-container'

const props = defineProps<{
  content: string
}>()

const md = ref<MarkdownIt | null>(null)

onMounted(() => {
  md.value = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
    breaks: true
  })

  // 自定义容器样式
  md.value.use(mdContainer, 'tip', {
    validate: function (params: string) {
      return params.trim().match(/^tip\s*(.*)$/)
    },
    render: function (tokens: any, idx: number) {
      if (tokens[idx].nesting === 1) {
        return '<div class="markdown-tip">\n'
      } else {
        return '</div>\n'
      }
    }
  })

  md.value.use(mdContainer, 'warning', {
    validate: function (params: string) {
      return params.trim().match(/^warning\s*(.*)$/)
    },
    render: function (tokens: any, idx: number) {
      if (tokens[idx].nesting === 1) {
        return '<div class="markdown-warning">\n'
      } else {
        return '</div>\n'
      }
    }
  })
})

const renderedMarkdown = computed(() => {
  if (!md.value) return ''
  return md.value.render(props.content)
})
</script>

<style scoped>
.markdown-content {
  line-height: 1.8;
  color: #303133;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #303133;
}

.markdown-content h1 {
  font-size: 24px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 20px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.markdown-content h3 {
  font-size: 16px;
}

.markdown-content p {
  margin: 8px 0;
  line-height: 1.8;
}

.markdown-content ul,
.markdown-content ol {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content li {
  margin: 4px 0;
}

.markdown-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #e6a23c;
}

.markdown-content pre {
  background: #282c34;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-content pre code {
  background: transparent;
  padding: 0;
  color: #abb2bf;
  font-size: 14px;
}

.markdown-content blockquote {
  border-left: 4px solid #409eff;
  padding: 12px 16px;
  margin: 12px 0;
  background: #f5f7fa;
  border-radius: 0 6px 6px 0;
}

.markdown-content blockquote p {
  margin: 0;
  color: #606266;
}

.markdown-content a {
  color: #409eff;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content img {
  max-width: 100%;
  border-radius: 6px;
  margin: 12px 0;
}

.markdown-tip,
.markdown-warning {
  padding: 12px 16px;
  border-radius: 6px;
  margin: 12px 0;
}

.markdown-tip {
  background: #f0f9ff;
  border-left: 4px solid #409eff;
}

.markdown-warning {
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
}
</style>
