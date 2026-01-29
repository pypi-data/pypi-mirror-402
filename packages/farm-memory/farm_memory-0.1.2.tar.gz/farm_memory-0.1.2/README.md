# FARM - Filesystem As Remote Memory

为 AI Agent 设计的持久化记忆系统。让 Agent 能够跨会话记住重要信息，并通过语义搜索快速检索。

## 核心功能

- **记忆存储**: 保存对话摘要、用户偏好、学习到的知识
- **多模式搜索**: 支持语义搜索、全文搜索、混合搜索
- **多接口**: MCP Server (Claude)、REST API、CLI

## 技术栈

- **向量搜索**: DuckDB + VSS 扩展 (HNSW 索引)
- **Embedding**: `BAAI/bge-small-zh-v1.5` (中文优化)
- **全文搜索**: 关键词匹配

## 快速开始

```bash
# 安装
pip install farm-memory
# 或
uv add farm-memory

# 初始化存储
farm init

# 添加记忆
farm add "用户偏好 Vue 框架" --tag preference

# 搜索记忆
farm search "前端框架" --mode semantic
farm search "Vue" --mode text
farm search "前端" --mode hybrid

# 启动 API 服务
farm serve
```

## Claude 集成

添加到 Claude 配置 (`~/.claude.json`):

```json
{
  "mcpServers": {
    "farm": {
      "command": "uvx",
      "args": ["farm-memory", "mcp"]
    }
  }
}
```

## 文档

- [快速入门](docs/getting-started.md)
- [CLI 命令](docs/cli.md)
- [REST API](docs/api.md)
- [MCP Server](docs/mcp.md)

## License

MIT
