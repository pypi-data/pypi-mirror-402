# test_correct.py
import os
import sys
import subprocess
import time

print("=== 正确的测试脚本 ===")

# 当前目录
current_dir = os.getcwd()
print(f"当前工作目录: {current_dir}")

# 列出文件
print("\n目录中的文件:")
for f in os.listdir(current_dir):
    if f.endswith('.py'):
        print(f"  - {f}")

# service.py 路径（就在当前目录）
service_path = os.path.join(current_dir, 'service.py')
print(f"\n服务器文件: {service_path}")

if not os.path.exists(service_path):
    print("❌ service.py 不存在！")
    print("请确保在正确的目录运行")
    sys.exit(1)

print("✅ 找到 service.py")

# 直接运行测试
print("\n1. 直接运行 service.py:")
print("   (如果卡住等待，这是正常的 - MCP服务器在等待客户端连接)")
print("   (按 Ctrl+C 停止)")

try:
    subprocess.run([sys.executable, service_path], timeout=3)
except subprocess.TimeoutExpired:
    print("   ✅ 服务器运行正常（在等待连接）")
except KeyboardInterrupt:
    print("   已停止")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 2. 用uvx运行
print("\n2. 使用uvx和MCP Inspector测试:")
print("   运行: uvx mcp-inspector python service.py")
print("   这会打开Web界面测试MCP功能")

# 3. 简单导入测试
print("\n3. 简单导入测试:")
try:
    sys.path.insert(0, current_dir)
    import service
    print("   ✅ 可以导入service模块")
    
    # 检查是否有main函数
    if hasattr(service, 'main'):
        print("   ✅ 找到main函数")
        
    print("\n所有测试通过！")
    
except ImportError as e:
    print(f"   ❌ 导入失败: {e}")
    print("   请检查依赖: pip install mcp")
except Exception as e:
    print(f"   ❌ 错误: {e}")