import json
from typing import Any, List
from mcp.types import Tool, TextContent
from ..apis.java_api import JavaAPIManager, JavaAPIConfig
from ..utils.config import config_manager


class JavaTools:
    """Java后台管理系统CRUD工具"""
    
    def __init__(self):
        self.api_manager = JavaAPIManager()
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="java_add_api",
                description="添加API配置，连接后台管理系统",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "API名称"},
                        "base_url": {"type": "string", "description": "基础URL，如 http://localhost:8080"},
                        "cookie_name": {"type": "string", "description": "Cookie名称，默认satoken"},
                        "cookie_token": {"type": "string", "description": "登录后的token值"}
                    },
                    "required": ["name", "base_url","cookie_name", "cookie_token"]
                }
            ),
            Tool(
                name="java_create",
                description="创建资源 POST",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "endpoint": {"type": "string", "description": "端点，如 /admin/user"},
                        "data": {"type": "object", "description": "创建数据"}
                    },
                    "required": ["api_name", "endpoint", "data"]
                }
            ),
            Tool(
                name="java_get",
                description="查询资源 GET /{id}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "endpoint": {"type": "string", "description": "端点"},
                        "item_id": {"type": "string", "description": "资源ID"}
                    },
                    "required": ["api_name", "endpoint", "item_id"]
                }
            ),
            Tool(
                name="java_update",
                description="更新资源 PUT，数据需包含id",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "endpoint": {"type": "string", "description": "端点"},
                        "data": {"type": "object", "description": "更新数据，需包含id"}
                    },
                    "required": ["api_name", "endpoint", "data"]
                }
            ),
            Tool(
                name="java_delete",
                description="批量删除 DELETE /batchDelete?ids=1,2,3",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "endpoint": {"type": "string", "description": "端点"},
                        "ids": {"type": "array", "items": {"type": "integer"}, "description": "ID列表"}
                    },
                    "required": ["api_name", "endpoint", "ids"]
                }
            ),
            Tool(
                name="java_list",
                description="分页查询 GET，支持currentPage和pageSize",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "endpoint": {"type": "string", "description": "端点"},
                        "page": {"type": "integer", "description": "页码，默认1"},
                        "size": {"type": "integer", "description": "每页数量，默认10"},
                        "params": {"type": "object", "description": "查询条件"}
                    },
                    "required": ["api_name", "endpoint"]
                }
            ),
            Tool(
                name="java_custom",
                description="自定义请求",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "description": "HTTP方法"},
                        "endpoint": {"type": "string", "description": "端点"},
                        "data": {"type": "object", "description": "请求体"},
                        "params": {"type": "object", "description": "查询参数"}
                    },
                    "required": ["api_name", "method", "endpoint"]
                }
            ),
            Tool(
                name="java_list_apis",
                description="列出已配置的API",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="java_update_token",
                description="更新API的token",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {"type": "string", "description": "API名称"},
                        "token": {"type": "string", "description": "新token"}
                    },
                    "required": ["api_name", "token"]
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, args: dict[str, Any]) -> List[TextContent]:
        try:
            if name == "java_add_api":
                # 使用传入的参数，如果没有提供则使用默认值
                cookie_name = args.get("cookie_name", "satoken")
                cookie_token = args.get("cookie_token", "")
                
                config = JavaAPIConfig(
                    base_url=args["base_url"],
                    cookie_name=cookie_name,
                    cookie_token=cookie_token
                )
                self.api_manager.add(args["name"], config)
                return [TextContent(type="text", text=f"API '{args['name']}' 配置成功")]
            
            elif name == "java_create":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                resp = await api.create(args["endpoint"], args["data"])
                return [TextContent(type="text", text=json.dumps(resp.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_get":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                resp = await api.get(args["endpoint"], args.get("item_id"))
                return [TextContent(type="text", text=json.dumps(resp.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_update":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                resp = await api.update(args["endpoint"], args["data"])
                return [TextContent(type="text", text=json.dumps(resp.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_delete":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                resp = await api.batch_delete(args["endpoint"], args["ids"])
                return [TextContent(type="text", text=json.dumps(resp.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_list":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                params = {"currentPage": args.get("page", 1), "pageSize": args.get("size", 10), **(args.get("params") or {})}
                resp = await api.list(args["endpoint"], params)
                return [TextContent(type="text", text=json.dumps(resp.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_custom":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                resp = await api.custom(args["method"], args["endpoint"], args.get("data"), args.get("params"))
                return [TextContent(type="text", text=json.dumps(resp.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_list_apis":
                apis = self.api_manager.list()
                if not apis:
                    return [TextContent(type="text", text="暂无配置")]
                info = [{"name": n, "base_url": self.api_manager.get(n).config.base_url} for n in apis]
                return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False, indent=2))]
            
            elif name == "java_update_token":
                api = self.api_manager.get(args["api_name"])
                if not api:
                    return [TextContent(type="text", text=f"API '{args['api_name']}' 不存在")]
                api.config.cookie_token = args["token"]
                return [TextContent(type="text", text=f"Token已更新")]
            
            else:
                return [TextContent(type="text", text=f"未知工具: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"错误: {str(e)}")]
