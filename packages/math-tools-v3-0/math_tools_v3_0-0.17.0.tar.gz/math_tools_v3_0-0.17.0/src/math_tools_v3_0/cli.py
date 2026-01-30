"""
命令行入口
"""

import asyncio
import sys
import argparse
from .service import MathServer


async def main_async():
    """异步主函数"""
    server = MathServer()
    await server.run()


def run():
    """提供给setuptools的入口点"""
    parser = argparse.ArgumentParser(description="Math Tools MCP Server")
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    
    args = parser.parse_args()
    
    if args.version:
        from . import __version__
        print(f"Math Tools MCP Server v{__version__}")
        return
    
    print("启动 Math Tools MCP Server...")
    
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"服务器错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()