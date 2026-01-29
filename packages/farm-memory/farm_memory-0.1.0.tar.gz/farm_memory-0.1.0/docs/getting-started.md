# 快速入门

## 什么是 FARM？

FARM (Filesystem As Remote Memory) 是为 AI Agent 设计的持久化记忆系统。

### 解决的问题

AI Agent（如 Claude）的对话是无状态的，每次新会话都会"失忆"。FARM 让 Agent 能够：

- 记住用户偏好和习惯
- 保存重要的对话摘要
- 存储学习到的知识和经验
- 跨会话检索相关信息

### 工作原理

```
用户 <-> Agent <-> FARM
              |
              v
         .farm/
         ├── memories/    # JSON 文件存储
         └── chroma/      # 向量索引
```

1. Agent 将重要信息存入 FARM（带标签和元数据）
2. FARM 自动建立向量索引
3. Agent 用自然语言搜索，FARM 返回语义相关的记忆

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd farm

# 安装依赖（需要 uv）
uv sync

# 初始化存储
uv run farm init
```

## 基本使用

### 添加记忆

```bash
# 简单添加
uv run farm add "用户是后端开发者，主要使用 Python"

# 带标签
uv run farm add "项目使用 FastAPI + PostgreSQL" --tag project --tag tech
```

### 查看记忆

```bash
# 列出所有
uv run farm list

# 按标签过滤
uv run farm list --tag project
```

### 搜索记忆

```bash
# 关键词搜索
uv run farm search "Python"

# 语义搜索（推荐）
uv run farm search "用户擅长什么技术" --semantic
```

### 删除记忆

```bash
uv run farm delete <memory-id>
```

## 下一步

- [CLI 完整命令](cli.md) - 所有命令行选项
- [REST API](api.md) - 程序化接入
- [MCP Server](mcp.md) - Claude 集成
