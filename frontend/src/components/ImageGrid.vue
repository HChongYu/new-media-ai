<template>
  <div class="image-grid">
    <div v-for="image in images" :key="image.id" class="image-item">
      <div class="image-wrapper">
        <img :src="image.image_url" :alt="image.image_type" @click="viewImage(image)" />
        <div class="image-overlay">
          <el-tag size="small" :type="getImageTypeColor(image.image_type)">
            {{ getImageTypeText(image.image_type) }}
          </el-tag>
        </div>
      </div>
      <div class="image-actions">
        <el-button
          v-if="showDownload"
          type="primary"
          size="small"
          @click="downloadImage(image)"
        >
          下载
        </el-button>
        <el-button
          v-if="showDelete"
          type="danger"
          size="small"
          @click="deleteImage(image)"
        >
          删除
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

defineProps<{
  images: Image[]
  showDownload?: boolean
  showDelete?: boolean
}>()

const emit = defineEmits<{
  (e: 'view', image: Image): void
  (e: 'delete', image: Image): void
}>()

const getImageTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    cover: '封面图',
    section: '正文图',
    summary: '摘要图'
  }
  return typeMap[type] || type
}

const getImageTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    cover: 'primary',
    section: 'success',
    summary: 'warning'
  }
  return colorMap[type] || 'info'
}

const viewImage = (image: Image) => {
  emit('view', image)
}

const downloadImage = async (image: Image) => {
  try {
    const response = await fetch(image.image_url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `image-${image.id}.${blob.type.split('/')[1] || 'png'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Download failed:', error)
    // 降级方案：直接打开图片
    window.open(image.image_url, '_blank')
  }
}

const deleteImage = (image: Image) => {
  emit('delete', image)
}

export interface Image {
  id: number
  image_url: string
  image_type: 'cover' | 'section' | 'summary'
}
</script>

<style scoped>
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.image-item {
  background: #FFFFFF;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #EBEDF0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.image-wrapper {
  position: relative;
  width: 100%;
  padding-top: 75%; /* 4:3 aspect ratio */
  overflow: hidden;
  cursor: pointer;
}

.image-wrapper img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
}

.image-actions {
  padding: 12px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  border-top: 1px solid #EBEDF0;
}
</style>
