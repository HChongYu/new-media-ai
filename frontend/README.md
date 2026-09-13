# AI自媒体运营平台 - 前端

基于 Vue3 + TypeScript + Element Plus 的 AI 自媒体运营平台前端项目。

## 功能特性

- **选题管理** - AI 辅助选题，内容审核流程
- **内容编辑** - Markdown 编辑器，实时预览
- **图片生成** - 根据内容自动生成配图
- **多平台发布** - 支持小红书、微信公众号发布
- **发布记录** - 查看历史发布记录

## 技术栈

- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Vite** - 构建工具

## 项目结构

```
frontend/
├── src/
│   ├── assets/          # 静态资源
│   │   └── styles/      # 样式文件
│   ├── components/      # 公共组件
│   ├── views/           # 页面视图
│   ├── stores/          # Pinia 状态管理
│   ├── services/        # API 服务
│   ├── router/          # 路由配置
│   ├── composables/     # 组合式函数
│   ├── utils/           # 工具函数
│   └── main.ts          # 入口文件
├── public/              # 公共资源
├── .env.*               # 环境变量
├── package.json         # 项目配置
├── tsconfig.json        # TypeScript 配置
└── vite.config.ts       # Vite 配置
```

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发环境

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

### 代码检查

```bash
npm run lint
```

## 环境变量

复制 `.env.example` 到 `.env.local` 并修改配置：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## 开发说明

### 组件命名
- 单文件组件使用 PascalCase 命名
- 公共组件放在 `src/components/` 目录

### 状态管理
- 使用 Pinia 进行状态管理
- 按功能模块划分 store

### API 调用
- 所有 API 调用统一在 `src/services/api.ts` 中封装
- 使用 axios 进行 HTTP 请求

## 浏览器支持

- Chrome (最新)
- Firefox (最新)
- Safari (最新)
- Edge (最新)

## 许可证

MIT
