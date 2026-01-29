# CLI 命令

FARM 提供 `farm` 命令行工具管理记忆。

## 初始化

```bash
uv run farm init [--path PATH]
```

在当前目录创建 `.farm/` 存储目录。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--path` | 存储路径 | `.farm` |

## 添加记忆

```bash
uv run farm add <content> [OPTIONS]
```

| 参数 | 说明 |
|------|------|
| `content` | 记忆内容（必填） |
| `--tag, -t` | 标签，可多次使用 |

示例：
```bash
uv run farm add "用户偏好暗色主题" --tag preference --tag ui
```

## 列出记忆

```bash
uv run farm list [OPTIONS]
```

| 参数 | 说明 |
|------|------|
| `--tag, -t` | 按标签过滤 |

示例：
```bash
uv run farm list
uv run farm list --tag project
```

## 获取记忆

```bash
uv run farm get <memory_id>
```

## 搜索记忆

```bash
uv run farm search <query> [OPTIONS]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索词（必填） | - |
| `--semantic, -s` | 启用语义搜索 | false |
| `-n, --limit` | 返回数量 | 10 |

示例：
```bash
# 关键词搜索
uv run farm search "Python"

# 语义搜索
uv run farm search "用户的技术栈是什么" --semantic -n 5
```

## 删除记忆

```bash
uv run farm delete <memory_id> [--force]
```

| 参数 | 说明 |
|------|------|
| `--force, -f` | 跳过确认 |

## 启动服务

### REST API 服务

```bash
uv run farm serve [OPTIONS]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 监听地址 | `127.0.0.1` |
| `--port` | 监听端口 | `8000` |

### MCP 服务

```bash
uv run farm mcp
```

启动 MCP 服务器，通过 stdio 与 Claude 通信。
