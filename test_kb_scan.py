import subprocess
import sys
import os

# 测试KB_scan.py
def test_kb_scan():
    print("=" * 80)
    print("测试KB_scan.py")
    print("=" * 80)
    
    # 构建命令
    kb_scan_cmd = [sys.executable, "KB_scan.py"]
    print(f"执行命令: {' '.join(kb_scan_cmd)}")
    
    # 执行命令并捕获输出
    process = subprocess.Popen(
        kb_scan_cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="E:\\1"
    )
    
    # 获取输出和错误
    stdout, stderr = process.communicate()
    exit_code = process.returncode
    
    # 打印结果
    print(f"退出码: {exit_code}")
    print("\n标准输出:")
    print(stdout)
    print("\n标准错误:")
    print(stderr)
    
    if exit_code == 0:
        print("\n✓ KB_scan.py 测试通过")
    else:
        print("\n✗ KB_scan.py 测试失败")
    
    return exit_code == 0

# 测试kb_scan_report.py
def test_kb_scan_report():
    print("\n" + "=" * 80)
    print("测试kb_scan_report.py")
    print("=" * 80)
    
    # 构建命令
    kb_scan_report_cmd = [sys.executable, "kb_scan_report.py"]
    print(f"执行命令: {' '.join(kb_scan_report_cmd)}")
    
    # 执行命令并捕获输出
    process = subprocess.Popen(
        kb_scan_report_cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="E:\\1"
    )
    
    # 获取输出和错误
    stdout, stderr = process.communicate()
    exit_code = process.returncode
    
    # 打印结果
    print(f"退出码: {exit_code}")
    print("\n标准输出:")
    print(stdout)
    print("\n标准错误:")
    print(stderr)
    
    if exit_code == 0:
        print("\n✓ kb_scan_report.py 测试通过")
    else:
        print("\n✗ kb_scan_report.py 测试失败")
    
    return exit_code == 0

if __name__ == "__main__":
    print("开始测试KB扫描相关脚本...")
    
    # 运行测试
    test1_result = test_kb_scan()
    test2_result = test_kb_scan_report()
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"KB_scan.py: {'通过' if test1_result else '失败'}")
    print(f"kb_scan_report.py: {'通过' if test2_result else '失败'}")
    
    if test1_result and test2_result:
        print("\n✓ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n✗ 部分测试失败！")
        sys.exit(1)
