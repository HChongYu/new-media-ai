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
  color: #1F2329;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #1F2329;
}

.markdown-content h1 {
  font-size: 22px;
  border-bottom: 1px solid #EBEDF0;
  padding-bottom: 8px;
}

.markdown-content h2 {
  font-size: 18px;
  border-bottom: 1px solid #EBEDF0;
  padding-bottom: 8px;
}

.markdown-content h3 {
  font-size: 15px;
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
  background: #F2F3F5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #FF7D00;
}

.markdown-content pre {
  background: #1E1E1E;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-content pre code {
  background: transparent;
  padding: 0;
  color: #D4D4D4;
  font-size: 13px;
}

.markdown-content blockquote {
  border-left: 4px solid #3370FF;
  padding: 12px 16px;
  margin: 12px 0;
  background: #F5F6F7;
  border-radius: 0 6px 6px 0;
}

.markdown-content blockquote p {
  margin: 0;
  color: #4E5969;
}

.markdown-content a {
  color: #3370FF;
  text-decoration: none;
}

.markdown-content a:hover {
  color: #245BDB;
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
  background: #EFF4FF;
  border-left: 4px solid #3370FF;
}

.markdown-warning {
  background: #FFF7E8;
  border-left: 4px solid #FF7D00;
}
</style>
