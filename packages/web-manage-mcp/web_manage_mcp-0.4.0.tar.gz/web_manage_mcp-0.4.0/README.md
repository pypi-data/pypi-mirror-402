# Web管理MCP服务器

Java后台管理系统CRUD操作的MCP工具，支持Sa-Token鉴权。

## 功能

- 创建资源 (POST)
- 查询资源 (GET /{id})
- 更新资源 (PUT)
- 批量删除 (DELETE /batchDelete?ids=)
- 分页查询 (GET ?currentPage=&pageSize=)
- 自定义请求

## 安装

```bash
uvx install web-manage-mcp
```

## MCP配置

```json
{
  "mcpServers": {
    "web-manage-mcp": {
      "command": "uvx",
      "args": ["web-manage-mcp"]
    }
  }
}
```

**注意**: 不再需要在环境变量中配置认证信息，所有认证信息通过 `java_add_api` 工具动态配置。

## 工具列表

| 工具 | 描述 | 参数 |
|-----|------|-----|
| `java_add_api` | 添加API配置 | `name`, `base_url`, `cookie_name?`, `cookie_token?` |
| `java_create` | 创建资源 POST | `api_name`, `endpoint`, `data` |
| `java_get` | 查询资源 GET /{id} | `api_name`, `endpoint`, `item_id` |
| `java_update` | 更新资源 PUT | `api_name`, `endpoint`, `data` |
| `java_delete` | 批量删除 DELETE | `api_name`, `endpoint`, `ids` |
| `java_list` | 分页查询 GET | `api_name`, `endpoint`, `page?`, `size?`, `params?` |
| `java_custom` | 自定义请求 | `api_name`, `method`, `endpoint`, `data?`, `params?` |
| `java_list_apis` | 列出已配置API | 无 |
| `java_update_token` | 更新token | `api_name`, `token` |

## 使用示例

```javascript
// 1. 配置API（包含认证信息）
java_add_api({
  "name": "admin",
  "base_url": "http://localhost:8080",
  "cookie_name": "satoken",  // 可选，默认为 "satoken"
  "cookie_token": "your-actual-token-value"  // 必填，实际的登录token
})

// 2. 查询用户列表
java_list({
  "api_name": "admin",
  "endpoint": "/admin/user",
  "page": 1,
  "size": 10
})

// 3. 新增用户
java_create({
  "api_name": "admin",
  "endpoint": "/admin/user",
  "data": {"username": "test", "password": "123456"}
})

// 4. 更新用户
java_update({
  "api_name": "admin",
  "endpoint": "/admin/user",
  "data": {"id": 1, "username": "test2"}
})

// 5. 删除用户
java_delete({
  "api_name": "admin",
  "endpoint": "/admin/user",
  "ids": [1, 2, 3]
})

// 6. 更新token（如果token过期）
java_update_token({
  "api_name": "admin",
  "token": "new-token-value"
})
```

## 支持的后台接口

适配以下接口模式：
- `/admin/user` - 用户管理
- `/admin/role` - 角色管理
- `/admin/permission` - 权限管理
- `/admin/dict` - 字典管理
- `/admin/notice` - 通知管理
- `/admin/operLog` - 操作日志
- `/admin/front-user` - 前台用户
- `/admin/com-query` - 通用查询

## License

MIT
