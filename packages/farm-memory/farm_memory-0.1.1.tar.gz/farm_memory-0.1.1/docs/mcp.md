# MCP Server

FARM 提供 MCP (Model Context Protocol) 服务，让 Claude 直接调用记忆管理功能。

## 配置

### Claude Code

编辑 `~/.claude.json`：

```json
{
  "mcpServers": {
    "farm": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/farm", "farm", "mcp"]
    }
  }
}
```

### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)：

```json
{
  "mcpServers": {
    "farm": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/farm", "farm", "mcp"]
    }
  }
}
```

## 可用工具

配置后，Claude 可以使用以下工具：

### 记忆操作

| 工具 | 说明 |
|------|------|
| `memory_create` | 创建新记忆 |
| `memory_get` | 获取指定记忆 |
| `memory_update` | 更新记忆内容 |
| `memory_delete` | 删除记忆 |
| `memory_list` | 列出所有记忆 |
| `memory_search` | 语义搜索记忆 |

### 文件操作

| 工具 | 说明 |
|------|------|
| `file_read` | 读取文件内容 |
| `file_write` | 写入文件 |
| `file_list` | 列出文件 |

## 使用示例

配置完成后，在与 Claude 对话时可以这样使用：

```
用户: 记住我喜欢用 Vue 框架

Claude: [调用 memory_create]
        已保存：用户偏好 Vue 框架

用户: 我之前说过喜欢什么前端框架？

Claude: [调用 memory_search，查询 "前端框架 偏好"]
        根据记录，你之前提到喜欢使用 Vue 框架。
```

## 调试

手动测试 MCP 服务：

```bash
# 启动 MCP 服务
uv run farm mcp

# 服务通过 stdio 通信，启动后等待 JSON-RPC 输入
```

查看 Claude 的 MCP 日志：
- Claude Code: 检查终端输出
- Claude Desktop: `~/Library/Logs/Claude/mcp*.log` (macOS)
