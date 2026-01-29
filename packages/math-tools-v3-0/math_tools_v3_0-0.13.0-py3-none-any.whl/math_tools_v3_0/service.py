# """
# 使用mcp
# 简单的MCP数学服务器 - 只实现加法和乘法
# """

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建服务器
server = Server("MathServer")


# 工具列表
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="add",
            description="将两个整数相加",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "第一个数"},
                    "b": {"type": "integer", "description": "第二个数"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="multiply", 
            description="将两个数字相乘",
            inputSchema={
                "type": "object", 
                "properties": {
                    "a": {"type": "number", "description": "第一个数"},
                    "b": {"type": "number", "description": "第二个数"}
                },
                "required": ["a", "b"]
            }
        )
    ]


# 工具调用处理
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "add":
        a = arguments["a"]
        b = arguments["b"]
        result = a + b
        print(f"计算: {a} + {b} = {result}")
        return [TextContent(type="text", text=str(result))]
    
    elif name == "multiply":
        a = arguments["a"]
        b = arguments["b"]
        result = a * b
        print(f"计算: {a} × {b} = {result}")
        return [TextContent(type="text", text=str(result))]
    
    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


# 主函数
async def main():
    print("MCP数学服务器已启动")
    print("支持的工具: add, multiply")
    
    # 创建初始化选项
    options = server.create_initialization_options()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    asyncio.run(main())