# AI自媒体运营平台

基于 Vue3 + TypeScript + Element Plus + LangGraph 的 AI 自媒体运营平台。

## 功能特性

- **选题管理** - AI 辅助选题，内容审核流程
- **内容编辑** - Markdown 编辑器，实时预览
- **图片生成** - 根据内容自动生成配图
- **多平台发布** - 支持小红书、微信公众号发布
- **发布记录** - 查看历史发布记录

## 技术栈

### 前端
- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Vite** - 构建工具

### 后端
- **FastAPI** - Web 框架
- **LangGraph** - AI 工作流编排
- **SQLAlchemy** - ORM
- **PostgreSQL** - 数据库
- **Redis** - 缓存

## 项目结构

```
op-ai/
├── backend/              # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── llm/
│   │   ├── utils/
│   │   └── exceptions/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/             # 前端界面 (Vue3)
│   ├── src/
│   │   ├── assets/       # 静态资源
│   │   ├── components/   # 公共组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── services/     # API 服务
│   │   ├── router/       # 路由配置
│   │   ├── composables/  # 组合式函数
│   │   └── main.ts       # 入口文件
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docker-compose.yml
└── README.md
```

## 快速开始

### 安装依赖

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd frontend
yarn install
```

### 开发环境

```bash
# 启动后端
cd backend
uvicorn app.main:app --reload

# 启动前端
cd frontend
yarn dev
```

访问 http://localhost:3000

### 生产构建

```bash
# 构建前端
cd frontend
yarn build

# 启动后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 环境变量

### 后端 (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/opai
REDIS_URL=redis://localhost:6379
LLM_API_KEY=your_api_key_here
```

### 前端 (.env.development)
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## Docker 部署

```bash
docker-compose up -d
```

## 许可证

MIT
