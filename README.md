# AI Search - 智能搜索引擎

[从零搭建 AI 搜索引擎：我给装上了智能记忆，还踩了这些坑](https://mp.weixin.qq.com/s/M-Qc6P0q3i5CGVrio9oJng)
一个基于 FastAPI + LangChain + Vue 3 构建的智能搜索引擎，结合 Tavily 搜索和 DeepSeek 大模型，为用户提供带引用的深度信息分析。

## 功能特性

- 🔍 **智能搜索**：输入自然语言问题，自动联网搜索最新信息
- 🤖 **AI 综合回答**：基于搜索结果，由 DeepSeek 生成带引用的深度分析
- 📎 **引用来源**：清晰标注引用来源，支持点击跳转原文
- ⚡ **流式输出**：打字机效果实时显示 AI 回答
- 💾 **智能缓存**：SQLite 持久化缓存，相同问题 24 小时内即时响应
- 📜 **搜索历史**：本地存储搜索历史，支持快速重新搜索
- 💡 **相关问题推荐**：AI 自动生成相关问题，继续深入探索
- 📋 **一键复制**：快速复制 AI 回答到剪贴板
- ⌨️ **键盘快捷键**：`/` 聚焦搜索框、`Esc` 清空输入
- 🎨 **美观界面**：参考 Perplexity 的简洁风格，信息密度高
- 🏆 **结果排序优化**：基于来源权威性（60+ 域名分级）和内容时效性智能重排
- 🖼️ **多模态搜索**：支持网页、图片、视频三种搜索模式
- 🛡️ **安全防护**：Prompt 注入检测、速率限制、XSS 防护、输入验证

## 技术栈

### 后端
- **FastAPI** - 高性能 Web 框架
- **LangChain** - LLM 应用开发框架
- **langchain-tavily** - Tavily 搜索集成
- **OpenAI SDK** - 兼容 DeepSeek API
- **SQLite** - 轻量级持久化缓存
- **SSE (Server-Sent Events)** - 流式输出
- **slowapi** - API 速率限制
- **Pydantic** - 数据验证与配置管理

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vue Router** - 路由管理
- **Tailwind CSS** - 原子化 CSS 框架
- **Marked** - Markdown 解析
- **Highlight.js** - 代码高亮
- **DOMPurify** - HTML 净化（XSS 防护）

## 快速开始

### 1. 环境准备

确保已安装：
- Python 3.10+
- Node.js 18+

### 2. 获取 API 密钥

- **DeepSeek API Key**: 访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册获取
- **Tavily API Key**: 访问 [Tavily](https://tavily.com/) 注册获取

### 3. 后端设置

```bash
cd backend

# 创建虚拟环境（可选但推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

编辑 `.env` 文件：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
TAVILY_API_KEY=your_tavily_api_key_here
```

启动后端服务：
```bash
uvicorn app.main:app --reload --port 8000
```

后端 API 将在 http://localhost:8000 启动

### 4. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 启动

## 项目结构

```
ai-search/
├── backend/
│   ├── app/                     # 应用入口
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI 应用、路由、中间件
│   ├── services/                # 业务逻辑
│   │   ├── __init__.py
│   │   ├── search_service.py    # 搜索核心逻辑（Tavily + DeepSeek）
│   │   ├── rank_service.py      # 结果排序引擎（权威性 + 时效性）
│   │   └── security.py          # Prompt 注入检测 + 输入净化
│   ├── core/                    # 基础设施
│   │   ├── __init__.py
│   │   ├── config.py            # 配置管理（env 加载）
│   │   └── cache_manager.py     # SQLite 缓存管理器
│   ├── data/                    # 缓存数据目录（自动创建）
│   │   └── cache.db
│   ├── requirements.txt         # Python 依赖
│   └── .env.example             # 环境变量示例
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.vue         # 搜索主页
│   │   │   └── Search.vue       # 搜索结果页
│   │   ├── components/
│   │   │   └── MarkdownRenderer.vue
│   │   ├── composables/
│   │   │   └── useSearchHistory.ts
│   │   ├── types.ts             # TypeScript 类型定义
│   │   ├── style.css
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── .gitignore
└── README.md
```

## 使用说明

### 基本搜索

1. 在搜索框中输入你的问题
2. 点击搜索或按回车
3. 等待 AI 生成回答（支持流式显示）
4. 查看右侧「引用来源」卡片，点击编号跳转到原文
5. 点击顶部的「相关问题」继续探索
6. 使用「复制」按钮一键复制回答内容

### 多模态搜索

在搜索结果页的搜索栏下方，可以切换搜索类型：

| 类型 | 说明 | 显示内容 |
|------|------|----------|
| **网页** | 默认模式，搜索网页文本内容 | AI 综合回答 + 引用来源 |
| **图片** | 搜索与主题相关的图片 | 图片网格 + AI 解读 |
| **视频** | 搜索视频平台相关内容 | 视频卡片 + AI 总结 |

点击图片/视频卡片可在新标签页打开原始链接。

### 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `/` | 聚焦搜索框 |
| `Esc` | 清空搜索输入 |

### 缓存机制

系统内置 SQLite 持久化缓存，具有以下特性：

- **命中条件**：相同问题在 24 小时内再次搜索，且搜索结果相似度 ≥ 75%
- **相似度计算**：综合 URL 重合度（50%）、标题关键词重合度（30%）、结果数量比（20%）
- **隐私保护**：查询内容通过 SHA-256 哈希存储，不关联用户身份
- **自动清理**：过期条目自动清除，超出 500 条时按 LRU 策略淘汰

缓存命中时，回答区域会显示绿色「来自缓存 · 即时响应」徽章。

### 结果排序优化

搜索结果的排序由 [rank_service.py](backend/services/rank_service.py) 自动处理，综合考虑以下维度：

| 维度 | 权重 | 说明 |
|------|------|------|
| 来源权威性 | 35% | 60+ 域名分级（gov.cn/arxiv.org/wikipedia.org...），自动识别 .gov/.edu 后缀 |
| 内容时效性 | 25% | 中英文日期识别，24 小时内=1.0，逐年衰减 |
| 原始分数 | 20% | Tavily 搜索 API 返回的相关性评分 |
| 关键词匹配 | 10% | 查询词与标题的匹配程度 |
| 内容丰富度 | 10% | 内容长度与信息量的正比关系 |

### 安全防护

| 防护措施 | 说明 |
|----------|------|
| **Prompt 注入检测** | 30+ 条正则规则覆盖常见攻击模式，置信度 ≥ 0.85 自动拦截（返回 422） |
| **速率限制** | 全局 30 次/分钟，搜索接口 10 次/分钟（基于 IP） |
| **XSS 防护** | DOMPurify 净化所有 HTML 输出 |
| **输入验证** | 查询长度 1-500 字符，`search_type` 白名单校验 |
| **CORS** | 仅允许前端开发服务器来源 |
| **缓存安全** | 查询内容 SHA-256 哈希存储，不存明文 |

可通过 `.env` 配置关闭注入检测或调整阈值：
```env
ENABLE_INJECTION_DETECTION=true
INJECTION_BLOCK_THRESHOLD=0.85
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_SEARCH_PER_MINUTE=10
```

## API 接口

### POST /search
普通搜索接口

请求体：
```json
{
  "query": "你的问题",
  "search_type": "web"
}
```
- `search_type`: `web` | `image` | `video`（默认 `web`）

响应：
```json
{
  "answer": "AI 回答",
  "sources": [
    {
      "title": "...",
      "url": "...",
      "content": "...",
      "score": 0.95,
      "image_url": null,
      "video_url": null
    }
  ],
  "related_questions": ["...", "..."],
  "cache_hit": false,
  "search_type": "web",
  "images": [],
  "video_results": []
}
```

### GET /search/stream?query=xxx
流式搜索接口（SSE）

参数：
- `query`：搜索关键词（1-500 字符）
- `search_type`：`web` | `image` | `video`（默认 `web`）

SSE 事件类型：
| 事件 | 数据 | 说明 |
|------|------|------|
| `sources` | `SearchResult[]` | 搜索来源列表（已排序） |
| `answer` | `string` | AI 回答片段（流式） |
| `images` | `SearchResult[]` | 图片结果（仅 image 模式） |
| `video_results` | `SearchResult[]` | 视频结果（仅 video 模式） |
| `related_questions` | `string[]` | 相关问题列表 |
| `cache_hit` | `boolean` | 缓存命中标识 |
| `done` | - | 完成标记 |

### GET /cache/stats
查询缓存统计信息

响应：
```json
{
  "total_entries": 42,
  "oldest_entry": 1715875200.0,
  "newest_entry": 1715961600.0,
  "db_size_bytes": 204800
}
```

### DELETE /cache
清理过期缓存并强制修剪至 100 条以内

## 开发说明

### 后端开发

后端的 Python 包需要从 `backend/` 目录启动才能正确解析相对导入：

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

文件组织规范：
- `app/` — 应用入口（路由、中间件）
- `services/` — 业务逻辑（搜索、排序、安全）
- `core/` — 基础设施（配置、缓存）

API 自动文档：访问 http://localhost:8000/docs

### 前端开发

- 使用 Vite 作为构建工具
- 使用 Tailwind CSS 进行样式开发
- TypeScript strict 模式

## 注意事项

1. **API 密钥安全**：`.env` 文件已加入 `.gitignore`，切勿将真实密钥提交到版本控制
2. **输入长度限制**：查询最大 500 字符，超出将被拒绝
3. **浏览器兼容性**：流式响应需要现代浏览器支持 `ReadableStream` API
4. **缓存目录**：`backend/data/` 目录会在首次运行时自动创建
5. **CORS 配置**：默认仅允许 `localhost:5173` 和 `127.0.0.1:5173`，生产环境需修改
6. **启动目录**：后端必须从 `backend/` 目录启动（`uvicorn app.main:app --reload --port 8000`）

## 许可证

MIT License
