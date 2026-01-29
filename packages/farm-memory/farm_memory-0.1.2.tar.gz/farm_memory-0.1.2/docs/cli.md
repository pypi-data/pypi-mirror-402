# CLI 命令

FARM 提供 `farm` 命令行工具管理记忆。

## 初始化

```bash
farm init [--path PATH]
```

在当前目录创建 `.farm/` 存储目录。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--path` | 存储路径 | `.farm` |

## 添加记忆

```bash
farm add <content> [OPTIONS]
```

| 参数 | 说明 |
|------|------|
| `content` | 记忆内容（必填） |
| `--tag, -t` | 标签，可多次使用 |

示例：
```bash
farm add "用户偏好暗色主题" --tag preference --tag ui
```

## 列出记忆

```bash
farm list [OPTIONS]
```

| 参数 | 说明 |
|------|------|
| `--tag, -t` | 按标签过滤 |

示例：
```bash
farm list
farm list --tag project
```

## 获取记忆

```bash
farm get <memory_id>
```

## 搜索记忆

```bash
farm search <query> [OPTIONS]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索词（必填） | - |
| `--mode, -m` | 搜索模式：semantic, text, hybrid | `semantic` |
| `--vector-weight, -w` | 混合搜索时向量权重 (0-1) | `0.5` |
| `-n, --limit` | 返回数量 | `10` |

示例：
```bash
# 语义搜索（默认）
farm search "用户的技术栈是什么"

# 全文搜索
farm search "Python" --mode text

# 混合搜索，向量权重 0.7
farm search "后端开发" --mode hybrid -w 0.7 -n 5
```

## 删除记忆

```bash
farm delete <memory_id> [--force]
```

| 参数 | 说明 |
|------|------|
| `--force, -f` | 跳过确认 |

## 启动服务

### REST API 服务

```bash
farm serve [OPTIONS]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 监听地址 | `127.0.0.1` |
| `--port` | 监听端口 | `8000` |

### MCP 服务

```bash
farm mcp
```

启动 MCP 服务器，通过 stdio 与 Claude 通信。
