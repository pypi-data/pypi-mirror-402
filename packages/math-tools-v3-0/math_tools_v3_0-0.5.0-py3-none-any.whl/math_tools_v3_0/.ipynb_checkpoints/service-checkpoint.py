"""
我的MCP服务器
"""

from mcp.server.fastmcp import FastMCP
import asyncio
import sys


# 创建MCP服务器实例
mcp = FastMCP("DemoServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    """将两个数字相加
    Args:
        a: 这是参数a的描述
        b: 这是参数b的描述
    """
    print(f"🔢 计算: {a} + {b} = {a + b}")
    return a + b

@mcp.tool()
def multiplya(a,b) -> float:
    """将两个数字相乘"""
    result = a * b
    print(f"🔢 计算: {a} × {b} = {result}")
    return result

@mcp.tool()
def greet(name: str) -> str:
    """向用户问候"""
    greeting = f"👋 你好，{name}！欢迎使用MCP服务器。"
    print(greeting)
    return greeting


def main():
    print("🚀 MCP服务器启动中...")
    print("📡 等待 MCP 客户端连接...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()