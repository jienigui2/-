"""
测试 vm_management_workflow 是否能正常运行
"""
import os
import sys
import json

def test_imports():
    """测试依赖库是否可以正常导入"""
    print("=" * 60)
    print("测试1: 检查依赖库导入")
    print("=" * 60)
    
    libraries = [
        'playwright',
        'rsa', 
        'binascii',
        'requests',
        'argparse',
        'urllib.parse'
    ]
    
    failed = []
    for lib in libraries:
        try:
            if lib == 'urllib.parse':
                import urllib.parse
                print(f"✓ {lib} 导入成功")
            else:
                __import__(lib)
                print(f"✓ {lib} 导入成功")
        except ImportError as e:
            print(f"✗ {lib} 导入失败: {e}")
            failed.append(lib)
    
    if failed:
        print(f"\n✗ 以下库导入失败: {', '.join(failed)}")
        return False
    else:
        print("\n✓ 所有依赖库导入成功")
        return True

def test_config_file():
    """测试配置文件是否存在且格式正确"""
    print("\n" + "=" * 60)
    print("测试2: 检查配置文件")
    print("=" * 60)
    
    config_file = 'config.json'
    
    # 检查文件是否存在
    if not os.path.exists(config_file):
        print(f"✗ 配置文件不存在: {config_file}")
        return False
    else:
        print(f"✓ 配置文件存在: {config_file}")
    
    # 尝试读取并解析配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ 配置文件解析成功")
    except Exception as e:
        print(f"✗ 配置文件解析失败: {e}")
        return False
    
    # 验证必需的配置项
    required_keys = [
        'target_vm',
        'network_config',
        'kb_packages',
        'customer_config',
        'login_credentials',
        'hci_device'
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in config:
            missing_keys.append(key)
        else:
            print(f"✓ 配置项 {key} 存在")
    
    if missing_keys:
        print(f"\n✗ 配置文件缺少必需的键: {', '.join(missing_keys)}")
        return False
    
    # 检查 customer_config 文件是否存在
    customer_config_path = config.get('customer_config')
    if customer_config_path and os.path.exists(customer_config_path):
        print(f"✓ 客户配置文件存在: {customer_config_path}")
    elif customer_config_path:
        print(f"⚠ 客户配置文件不存在: {customer_config_path}（警告）")
    else:
        print(f"✗ customer_config 配置为空")
        return False
    
    print("\n✓ 配置文件检查通过")
    return True

def test_peizhi_module():
    """测试 peizhi.py 模块是否可以正常导入"""
    print("\n" + "=" * 60)
    print("测试3: 检查 peizhi.py 模块")
    print("=" * 60)
    
    try:
        import peizhi
        print("✓ peizhi.py 导入成功")
        
        # 检查是否有 run 函数
        if hasattr(peizhi, 'run'):
            print("✓ peizhi.run 函数存在")
            return True
        else:
            print("✗ peizhi.run 函数不存在")
            return False
    except ImportError as e:
        print(f"✗ peizhi.py 导入失败: {e}")
        return False

def test_vm_management_class():
    """测试 VMManagementWorkflow 类是否可以正常初始化"""
    print("\n" + "=" * 60)
    print("测试4: 检查 VMManagementWorkflow 类")
    print("=" * 60)
    
    try:
        from vm_management_workflow import VMManagementWorkflow
        print("✓ VMManagementWorkflow 类导入成功")
        
        # 尝试初始化
        workflow = VMManagementWorkflow('config.json')
        print("✓ VMManagementWorkflow 类初始化成功")
        return True
    except Exception as e:
        print(f"✗ VMManagementWorkflow 初始化失败: {e}")
        return False

def test_network_connectivity():
    """测试 HCI 设备的网络连通性"""
    print("\n" + "=" * 60)
    print("测试5: 检查 HCI 设备网络连通性")
    print("=" * 60)
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        hci_ip = config.get('hci_device', {}).get('ip')
        print(f"HCI 设备 IP: {hci_ip}")
        
        import subprocess
        import platform
        
        # 根据操作系统选择 ping 命令
        system = platform.system().lower()
        if system == 'windows':
            # Windows: ping 4次
            cmd = f'ping -n 4 {hci_ip}'
        else:
            # Linux/Mac: ping 4次
            cmd = f'ping -c 4 {hci_ip}'
        
        print(f"执行命令: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        print(f"Ping 命令退出码: {result.returncode}")
        if result.stdout:
            print(f"输出:\n{result.stdout}")
        
        if result.returncode == 0:
            print(f"✓ HCI 设备 {hci_ip} 网络可达")
            return True
        else:
            print(f"✗ HCI 设备 {hci_ip} 网络不可达")
            return False
            
    except Exception as e:
        print(f"✗ 网络连通性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("VM Management 环境检查")
    print("=" * 80)
    
    tests = [
        ("依赖库导入", test_imports),
        ("配置文件", test_config_file),
        ("peizhi.py 模块", test_peizhi_module),
        ("VMManagementWorkflow 类", test_vm_management_class),
        ("HCI 设备网络连通性", test_network_connectivity),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ {name} 测试过程中出错: {e}")
            results[name] = False
    
    # 打印汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if all(results.values()):
        print("\n✓ 所有测试通过！vm_management 可以正常运行")
        return True
    else:
        print("\n✗ 部分测试失败，请检查相关配置")
        failed_tests = [name for name, result in results.items() if not result]
        print(f"失败的测试: {', '.join(failed_tests)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)