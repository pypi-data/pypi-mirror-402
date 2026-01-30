import sys
import os

# 添加包路径
package_path = '/workspace/朝阳项目/mcp服务/test-0119/MCP/math-tools-v3/src/math_tools_v3_0'
sys.path.insert(0, os.path.dirname(package_path))

print("=== 测试导入 ===")
try:
    from math_tools_v3_0 import MathServer, run, __version__
    print(f"✓ 成功导入 MathServer: {MathServer}")
    print(f"✓ 成功导入 run: {run}")
    print(f"✓ 版本: {__version__}")
    
    # 测试创建实例
    server = MathServer()
    print(f"✓ 成功创建 MathServer 实例: {server}")
    
    # 测试实例方法
    print(f"✓ server 对象有 run 方法: {hasattr(server, 'run')}")
    print(f"✓ server 对象有 server 属性: {hasattr(server, 'server')}")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    print("\n尝试直接导入 service 模块...")
    try:
        from math_tools_v3_0 import service
        print(f"service 模块内容:")
        for attr in dir(service):
            if not attr.startswith('_'):
                print(f"  - {attr}: {getattr(service, attr)}")
    except Exception as e2:
        print(f"直接导入也失败: {e2}")
except Exception as e:
    print(f"✗ 其他错误: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 检查包结构 ===")
try:
    import math_tools_v3_0
    print("包内容:")
    for attr in dir(math_tools_v3_0):
        if not attr.startswith('_'):
            print(f"  - {attr}: {getattr(math_tools_v3_0, attr)}")
except Exception as e:
    print(f"检查失败: {e}")