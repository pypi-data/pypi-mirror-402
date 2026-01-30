"""
简单的MCP数学服务器 - 只实现加法和乘法
"""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class MathServer:
    """MathServer 类"""
    
    def __init__(self):
        self.server = Server("MathServer")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置服务器处理器"""
        
        @self.server.list_tools()
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
        
        @self.server.call_tool()
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
    
    async def run(self):
        """运行服务器"""
        print("MCP数学服务器已启动")
        print("支持的工具: add, multiply")
        
        options = self.server.create_initialization_options()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, options)


# 保持向后兼容性，创建 server 实例
server = MathServer()


# 主函数
async def main():
    """主入口函数"""
    math_server = MathServer()
    await math_server.run()


if __name__ == "__main__":
    asyncio.run(main())