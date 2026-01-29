# """
# 我的MCP服务器
# """

"""
使用 FastMCP - 带参数模式检查的版本
"""

from mcp.server.fastmcp import FastMCP

# 创建 FastMCP 服务器
mcp = FastMCP("MathServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    """将两个整数相加
    
    Args:
        a: 第一个加数，必须是整数
        b: 第二个加数，必须是整数
    
    Returns:
        两个整数的和
        
    Example:
        >>> add(2, 3)
        5
    """
    result = a + b
    print(f"🔢 计算: {a} + {b} = {result}")
    return result

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """将两个数字相乘
    
    Args:
        a: 被乘数，可以是整数或小数
        b: 乘数，可以是整数或小数
    
    Returns:
        两个数字的乘积
        
    Example:
        >>> multiply(3.5, 2)
        7.0
    """
    result = a * b
    print(f"🔢 计算: {a} × {b} = {result}")
    return result

@mcp.tool()
def greet(name: str, greeting: str = "你好") -> str:
    """向用户问候
    
    Args:
        name: 用户的姓名，可以是中文或英文
        greeting: 问候语，默认为"你好"
    
    Returns:
        完整的问候语
        
    Example:
        >>> greet("张三")
        "你好，张三！"
    """
    message = f"{greeting}，{name}！"
    print(f"👋 {message}")
    return message




def main():
    print("🚀 MCP数学服务器已启动")
    
    print("\n📡 等待 MCP 客户端连接...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()






# """
# 使用mcp
# 简单的MCP数学服务器 - 只实现加法和乘法
# """

# import asyncio
# import json
# from mcp.server import Server
# from mcp.server.stdio import stdio_server
# from mcp.types import Tool, TextContent

# # 创建服务器
# server = Server("MathServer")


# # 工具列表
# @server.list_tools()
# async def list_tools():
#     return [
#         Tool(
#             name="add",
#             description="将两个整数相加",
#             inputSchema={
#                 "type": "object",
#                 "properties": {
#                     "a": {"type": "integer", "description": "第一个数"},
#                     "b": {"type": "integer", "description": "第二个数"}
#                 },
#                 "required": ["a", "b"]
#             }
#         ),
#         Tool(
#             name="multiply", 
#             description="将两个数字相乘",
#             inputSchema={
#                 "type": "object", 
#                 "properties": {
#                     "a": {"type": "number", "description": "第一个数"},
#                     "b": {"type": "number", "description": "第二个数"}
#                 },
#                 "required": ["a", "b"]
#             }
#         )
#     ]


# # 工具调用处理
# @server.call_tool()
# async def call_tool(name: str, arguments: dict):
#     if name == "add":
#         a = arguments["a"]
#         b = arguments["b"]
#         result = a + b
#         print(f"计算: {a} + {b} = {result}")
#         return [TextContent(type="text", text=str(result))]
    
#     elif name == "multiply":
#         a = arguments["a"]
#         b = arguments["b"]
#         result = a * b
#         print(f"计算: {a} × {b} = {result}")
#         return [TextContent(type="text", text=str(result))]
    
#     else:
#         return [TextContent(type="text", text=f"未知工具: {name}")]


# # 主函数
# async def main():
#     print("MCP数学服务器已启动")
#     print("支持的工具: add, multiply")
    
#     # 创建初始化选项
#     options = server.create_initialization_options()
    
#     async with stdio_server() as (read_stream, write_stream):
#         await server.run(read_stream, write_stream, options)


# if __name__ == "__main__":
#     asyncio.run(main())