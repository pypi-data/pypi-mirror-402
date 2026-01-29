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
         └── duckdb/      # DuckDB 向量索引
```

1. Agent 将重要信息存入 FARM（带标签和元数据）
2. FARM 使用 `bge-small-zh` 模型生成向量，存入 DuckDB
3. Agent 用自然语言搜索，FARM 返回语义相关的记忆

### 搜索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `semantic` | 向量语义搜索 | 自然语言查询，如"用户喜欢什么" |
| `text` | 关键词匹配 | 精确查找，如"Vue" |
| `hybrid` | 混合搜索 | 结合语义和关键词 |

## 安装

```bash
# 从 PyPI 安装
pip install farm-memory

# 或使用 uv
uv add farm-memory

# 初始化存储
farm init
```

## 基本使用

### 添加记忆

```bash
# 简单添加
farm add "用户是后端开发者，主要使用 Python"

# 带标签
farm add "项目使用 FastAPI + PostgreSQL" --tag project --tag tech
```

### 查看记忆

```bash
# 列出所有
farm list

# 按标签过滤
farm list --tag project
```

### 搜索记忆

```bash
# 语义搜索（默认）
farm search "用户擅长什么技术"

# 全文搜索
farm search "Python" --mode text

# 混合搜索
farm search "后端开发" --mode hybrid --vector-weight 0.7
```

### 删除记忆

```bash
farm delete <memory-id>
```

## 下一步

- [CLI 完整命令](cli.md) - 所有命令行选项
- [REST API](api.md) - 程序化接入
- [MCP Server](mcp.md) - Claude 集成
