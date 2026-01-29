import asyncio
import json
import os
from typing import Any, List
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent

from web_manage_mcp_server.tools.java_tools import JavaTools
from web_manage_mcp_server.utils.config import config_manager

server = Server("web-manage-mcp")
java_tools = JavaTools()

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用工具"""
    return java_tools.get_tools()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    return await java_tools.handle_tool_call(name, arguments)

async def run_server():
    """启动MCP服务器"""
    from mcp.server.stdio import stdio_server
    
    print("MCP服务器启动 - 使用 java_add_api 动态配置认证信息")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="web-manage-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

def main():
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
