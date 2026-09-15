<template>
  <div class="login-container" @mousemove="onMouseMove" @click="onContainerClick">
    <!-- 动态背景光球 -->
    <div class="bg-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="orb orb-4"></div>
      <div class="orb orb-5"></div>
    </div>

    <!-- 粒子星空 -->
    <canvas ref="canvasRef" class="particle-canvas"></canvas>

    <!-- 鼠标追踪光晕 -->
    <div class="mouse-glow" :style="mouseGlowStyle"></div>

    <!-- 点击涟漪 -->
    <TransitionGroup name="ripple">
      <div
        v-for="r in ripples"
        :key="r.id"
        class="click-ripple"
        :style="{ left: r.x + 'px', top: r.y + 'px' }"
      ></div>
    </TransitionGroup>

    <!-- 登录卡片 -->
    <div
      ref="cardRef"
      class="login-box"
      :style="cardTiltStyle"
      @mouseenter="onCardMouseEnter"
      @mouseleave="onCardMouseLeave"
    >
      <!-- 旋转彩虹边框 -->
      <div class="rotating-border"></div>

      <!-- 卡片内鼠标聚光灯 -->
      <div class="card-spotlight" :style="cardSpotlightStyle"></div>

      <div class="login-header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="gradient-text">AI自媒体运营平台</h1>
        <p class="typing-text">
          <span>{{ displaySubtitle }}</span>
          <span class="cursor">|</span>
        </p>
      </div>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username" class="form-item-animate" style="animation-delay: 0.3s">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password" class="form-item-animate" style="animation-delay: 0.45s">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item class="form-item-animate" style="animation-delay: 0.6s">
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">登 录</span>
          </el-button>
        </el-form-item>
        
        <div class="login-footer form-item-animate" style="animation-delay: 0.75s">
          <el-link type="info" href="#" target="_blank">忘记密码？</el-link>
          <el-link type="info" href="#" target="_blank">注册账号</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@stores/user'
import { authApi } from '@services/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const canvasRef = ref<HTMLCanvasElement>()
const cardRef = ref<HTMLElement>()

let animationId: number
let particles: Array<{ x: number; y: number; vx: number; vy: number; size: number; opacity: number }> = []
let mouse = { x: 0, y: 0 }

// 鼠标追踪光晕样式
const mouseGlowStyle = computed(() => ({
  left: mouse.x + 'px',
  top: mouse.y + 'px',
}))

// 卡片 3D 倾斜
const tiltX = ref(0)
const tiltY = ref(0)
const isHoveringCard = ref(false)

const cardTiltStyle = computed(() => {
  if (!isHoveringCard.value) return {}
  return {
    transform: `perspective(1000px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg) scale3d(1.02, 1.02, 1.02)`,
  }
})

// 卡片内聚光灯
const cardSpotlightStyle = computed(() => ({
  background: `radial-gradient(circle at ${50 + tiltY.value * 3}% ${50 - tiltX.value * 3}%, rgba(255,255,255,0.08) 0%, transparent 60%)`,
}))

// 点击涟漪
interface Ripple { id: number; x: number; y: number }
const ripples = ref<Ripple[]>([])
let rippleId = 0

const onContainerClick = (e: MouseEvent) => {
  const id = rippleId++
  ripples.value.push({ id, x: e.clientX, y: e.clientY })
  setTimeout(() => {
    ripples.value = ripples.value.filter(r => r.id !== id)
  }, 800)
}

// 鼠标移动
const onMouseMove = (e: MouseEvent) => {
  mouse.x = e.clientX
  mouse.y = e.clientY

  // 粒子鼠标吸引效果
  particles.forEach(p => {
    const dx = mouse.x - p.x
    const dy = mouse.y - p.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < 200) {
      const force = (200 - dist) / 200 * 0.02
      p.vx += dx * force
      p.vy += dy * force
    }
  })

  // 卡片 3D 倾斜
  if (isHoveringCard.value && cardRef.value) {
    const rect = cardRef.value.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const percentX = (mouse.x - centerX) / (rect.width / 2)
    const percentY = (mouse.y - centerY) / (rect.height / 2)
    tiltY.value = percentX * 8
    tiltX.value = -percentY * 8
  }
}

const onCardMouseEnter = () => {
  isHoveringCard.value = true
}

const onCardMouseLeave = () => {
  isHoveringCard.value = false
  tiltX.value = 0
  tiltY.value = 0
}

// 打字机效果
const subtitleFull = '小红书 & 公众号内容管理系统'
const displaySubtitle = ref('')

const startTyping = () => {
  let i = 0
  const type = () => {
    if (i <= subtitleFull.length) {
      displaySubtitle.value = subtitleFull.slice(0, i)
      i++
      setTimeout(type, 80 + Math.random() * 60)
    }
  }
  setTimeout(type, 800)
}

// 粒子星空动画
const initParticles = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  for (let i = 0; i < 100; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      size: Math.random() * 2 + 0.5,
      opacity: Math.random() * 0.5 + 0.2
    })
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    particles.forEach((p, i) => {
      // 阻尼减速
      p.vx *= 0.99
      p.vy *= 0.99

      p.x += p.vx
      p.y += p.vy

      // 边界环绕
      if (p.x < 0) p.x = canvas.width
      if (p.x > canvas.width) p.x = 0
      if (p.y < 0) p.y = canvas.height
      if (p.y > canvas.height) p.y = 0

      // 绘制粒子
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`
      ctx.fill()

      // 连线
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j]
        const dx = p.x - p2.x
        const dy = p.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 130) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = `rgba(255, 255, 255, ${0.12 * (1 - dist / 130)})`
          ctx.lineWidth = 0.6
          ctx.stroke()
        }
      }
    })

    // 鼠标附近的粒子画高亮连线
    particles.forEach(p => {
      const dx = mouse.x - p.x
      const dy = mouse.y - p.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 180) {
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(mouse.x, mouse.y)
        ctx.strokeStyle = `rgba(51, 112, 255, ${0.25 * (1 - dist / 180)})`
        ctx.lineWidth = 0.8
        ctx.stroke()
      }
    })

    animationId = requestAnimationFrame(animate)
  }
  animate()
}

onMounted(() => {
  initParticles()
  startTyping()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId)
})

const form = reactive({
  username: '',
  password: ''
})

const rules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const res: any = await authApi.login({ username: form.username, password: form.password })
    const { token, user } = res.data
    
    if (token && user) {
      userStore.setToken(token)
      userStore.setUser(user)
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error('登录失败，请检查用户名和密码')
    }
  } catch (error) {
    console.error('Login error:', error)
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ===== 背景 ===== */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #EEF2FF, #F5F6F7, #E8F0FE);
  overflow: hidden;
  position: relative;
  cursor: default;
}

.bg-orbs {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #3370FF, transparent);
  top: -100px; left: -100px;
  animation-duration: 18s;
}
.orb-2 {
  width: 350px; height: 350px;
  background: radial-gradient(circle, #5B8DEF, transparent);
  bottom: -80px; right: -80px;
  animation-duration: 22s;
  animation-delay: -5s;
}
.orb-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #7B61FF, transparent);
  top: 50%; left: 60%;
  animation-duration: 25s;
  animation-delay: -10s;
}
.orb-4 {
  width: 250px; height: 250px;
  background: radial-gradient(circle, #36CFC9, transparent);
  top: 30%; left: 10%;
  animation-duration: 20s;
  animation-delay: -3s;
}
.orb-5 {
  width: 200px; height: 200px;
  background: radial-gradient(circle, #00B365, transparent);
  bottom: 20%; left: 40%;
  animation-duration: 23s;
  animation-delay: -7s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(80px, -60px) scale(1.1); }
  50% { transform: translate(-40px, 80px) scale(0.9); }
  75% { transform: translate(60px, 40px) scale(1.05); }
}

.particle-canvas {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

/* ===== 鼠标全局光晕 ===== */
.mouse-glow {
  position: fixed;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(51, 112, 255, 0.1) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 1;
  transition: left 0.1s ease-out, top 0.1s ease-out;
}

/* ===== 点击涟漪 ===== */
.click-ripple {
  position: fixed;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 10;
  animation: rippleExpand 0.8s ease-out forwards;
}

@keyframes rippleExpand {
  0% {
    width: 4px;
    height: 4px;
    opacity: 0.6;
    border: 2px solid rgba(51, 112, 255, 0.4);
  }
  100% {
    width: 300px;
    height: 300px;
    opacity: 0;
    border: 2px solid rgba(51, 112, 255, 0);
  }
}

.ripple-enter-active {
  animation: none;
}
.ripple-leave-active {
  animation: none;
}

/* ===== 登录卡片 ===== */
.login-box {
  width: 420px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  border: 1px solid rgba(222, 224, 227, 0.6);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.08),
    0 4px 12px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 2;
  animation: cardEntry 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  opacity: 0;
  transform: translateY(40px) scale(0.92);
  transition: transform 0.15s ease-out, box-shadow 0.3s ease;
  overflow: hidden;
}

.login-box:hover {
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.1),
    0 6px 16px rgba(0, 0, 0, 0.05);
}

@keyframes cardEntry {
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 卡片内聚光灯 */
.card-spotlight {
  position: absolute;
  inset: 0;
  border-radius: 16px;
  pointer-events: none;
  z-index: 0;
  transition: background 0.15s ease-out;
}

/* ===== 旋转彩虹边框 ===== */
.rotating-border {
  position: absolute;
  inset: -2px;
  border-radius: 18px;
  background: conic-gradient(
    from 0deg,
    #3370FF, #5B8DEF, #7B61FF, #36CFC9, #00B365,
    #3370FF, #5B8DEF, #7B61FF, #36CFC9, #00B365,
    #3370FF
  );
  animation: rotateBorder 6s linear infinite;
  opacity: 0;
  transition: opacity 0.5s ease;
  z-index: -1;
}

.login-box:hover .rotating-border {
  opacity: 0.5;
}

@keyframes rotateBorder {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 用伪元素遮住边框内部，只露出边框 */
.rotating-border::after {
  content: '';
  position: absolute;
  inset: 2px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
}

/* ===== Logo ===== */
.logo-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, #3370FF, #5B8DEF);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  animation: logoEntry 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards;
  opacity: 0;
  transform: scale(0) rotate(-180deg);
  box-shadow: 0 8px 24px rgba(51, 112, 255, 0.35);
  position: relative;
  z-index: 1;
}

.logo-icon::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  background: linear-gradient(135deg, #3370FF, #5B8DEF);
  opacity: 0.2;
  filter: blur(12px);
  z-index: -1;
  animation: logoPulse 3s ease-in-out infinite;
}

@keyframes logoPulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.15); }
}

.logo-icon svg {
  width: 28px;
  height: 28px;
}

@keyframes logoEntry {
  to {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

/* ===== 标题区域 ===== */
.login-header {
  text-align: center;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

/* 渐变流光标题 */
.gradient-text {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 10px;
  letter-spacing: 1px;
  background: linear-gradient(
    90deg,
    #3370FF, #5B8DEF, #7B61FF, #36CFC9, #3370FF
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradientShift 4s linear infinite, fadeSlideUp 0.6s ease 0.15s forwards;
  opacity: 0;
  transform: translateY(15px);
}

@keyframes gradientShift {
  to { background-position: 200% center; }
}

/* 打字机副标题 */
.typing-text {
  font-size: 14px;
  color: #8F959E;
  min-height: 20px;
  animation: fadeSlideUp 0.6s ease 0.25s forwards;
  opacity: 0;
  transform: translateY(15px);
}

.typing-text .cursor {
  color: #3370FF;
  animation: blink 0.8s step-end infinite;
  font-weight: 300;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@keyframes fadeSlideUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== 表单 ===== */
.form-item-animate {
  animation: fadeSlideUp 0.6s ease forwards;
  opacity: 0;
  transform: translateY(15px);
}

.login-form {
  margin-bottom: 0;
  position: relative;
  z-index: 1;
}

/* 输入框飞书风格 */
:deep(.el-input__wrapper) {
  background: #F5F6F7 !important;
  border: 1px solid transparent;
  box-shadow: none !important;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  background: #F2F3F5 !important;
  border-color: #C9CDD4;
  box-shadow: none !important;
}

:deep(.el-input__wrapper.is-focus) {
  background: #FFFFFF !important;
  border-color: #3370FF;
  box-shadow: 0 0 0 2px rgba(51, 112, 255, 0.1) !important;
}

:deep(.el-input__inner) {
  color: #1F2329;
}

:deep(.el-input__inner::placeholder) {
  color: #C9CDD4;
}

:deep(.el-input__prefix .el-icon) {
  color: #8F959E;
}

:deep(.el-input__suffix .el-icon) {
  color: #8F959E;
}

/* ===== 登录按钮 ===== */
.login-button {
  width: 100%;
  height: 44px;
  border: none !important;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 4px;
  background: #3370FF !important;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(51, 112, 255, 0.25);
}

.login-button:hover {
  transform: translateY(-1px);
  background: #245BDB !important;
  box-shadow: 0 4px 16px rgba(51, 112, 255, 0.35);
}

.login-button:active {
  transform: translateY(0);
  background: #1849BD !important;
}

/* 按钮流光 */
.login-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.15),
    transparent
  );
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

/* ===== 底部链接 ===== */
.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

:deep(.el-link__inner) {
  color: #8F959E;
  transition: all 0.3s ease;
}

:deep(.el-link:hover .el-link__inner) {
  color: #3370FF;
}

:deep(.el-form-item__error) {
  color: #F53F3F;
}

/* ===== 响应式 ===== */
@media (max-width: 480px) {
  .login-box {
    width: calc(100vw - 32px);
    padding: 36px 24px;
  }
}
</style>
