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
