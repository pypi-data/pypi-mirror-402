"""
Math Tools MCP Server v3.0
提供加法和乘法计算工具的MCP服务器
"""

__version__ = "0.16.0"
__author__ = "Math Tools Team"

# 从 service 模块导入 MathServer 类
from .service import MathServer
from .cli import run

__all__ = ["MathServer", "run"]