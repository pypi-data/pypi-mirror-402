# REST API

启动服务：
```bash
farm serve --host 0.0.0.0 --port 8000
```

基础 URL: `http://localhost:8000`

## 健康检查

```http
GET /health
```

响应：
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## 记忆管理

### 创建记忆

```http
POST /api/v1/memories
Content-Type: application/json

{
  "content": "记忆内容",
  "tags": ["tag1", "tag2"],
  "metadata": {"key": "value"}
}
```

响应：
```json
{
  "id": "uuid",
  "content": "记忆内容",
  "tags": ["tag1", "tag2"],
  "metadata": {"key": "value"},
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 列出记忆

```http
GET /api/v1/memories
GET /api/v1/memories?tag=project
```

### 获取单条记忆

```http
GET /api/v1/memories/{id}
```

### 更新记忆

```http
PATCH /api/v1/memories/{id}
Content-Type: application/json

{
  "content": "更新后的内容",
  "tags": ["new-tag"]
}
```

### 删除记忆

```http
DELETE /api/v1/memories/{id}
```

### 搜索记忆

```http
POST /api/v1/memories/search
Content-Type: application/json

{
  "query": "搜索词",
  "limit": 10,
  "mode": "semantic",
  "vector_weight": 0.5
}
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `query` | string | 搜索词（必填） | - |
| `limit` | int | 返回数量 | `10` |
| `mode` | string | 搜索模式：`semantic`, `text`, `hybrid` | `semantic` |
| `vector_weight` | float | 混合搜索时向量权重 (0-1) | `0.5` |

响应：
```json
[
  {
    "id": "uuid",
    "source_type": "memory",
    "content": "匹配的内容",
    "score": 0.85,
    "metadata": {}
  }
]
```

## 文件管理

### 写入文件

```http
PUT /api/v1/files/{path}
Content-Type: application/json

{
  "content": "文件内容"
}
```

### 读取文件元数据

```http
GET /api/v1/files/{path}
```

### 读取文件内容

```http
GET /api/v1/files/{path}/content
```

### 列出文件

```http
GET /api/v1/files
```

### 删除文件

```http
DELETE /api/v1/files/{path}
```

### 搜索文件

```http
POST /api/v1/files/search
Content-Type: application/json

{
  "query": "搜索词",
  "limit": 10,
  "mode": "semantic"
}
```

## 错误响应

```json
{
  "detail": "错误信息"
}
```

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
