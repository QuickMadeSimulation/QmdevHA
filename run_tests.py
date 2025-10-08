#!/usr/bin/env python3
"""运行QmdevHA测试的脚本"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("标准输出:")
        print(result.stdout)
    
    if result.stderr:
        print("错误输出:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} 失败 (退出码: {result.returncode})")
        return False
    else:
        print(f"✅ {description} 成功")
        return True


def main():
    """主函数"""
    print("QmdevHA 测试套件")
    print("=" * 50)
    
    # 检查是否在正确的目录
    if not os.path.exists("custom_components/qmdevha"):
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 安装测试依赖
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements_test.txt"], 
                      "安装测试依赖"):
        sys.exit(1)
    
    # 一次性运行所有测试并生成覆盖率报告
    cmd = [
        sys.executable, "-m", "pytest", "tests/", "-v",
        "--cov=custom_components.qmdevha", "--cov-report=term-missing"
    ]
    ok = run_command(cmd, "运行全部测试与覆盖率")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {'通过' if ok else '失败'}")
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
