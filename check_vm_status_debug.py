#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试虚拟机启动问题
"""

from vm_management_workflow import VMManagementWorkflow

def debug_vm_start():
    """调试虚拟机启动"""
    print("=" * 80)
    print("调试虚拟机启动问题")
    print("=" * 80)
    
    workflow = VMManagementWorkflow(config_file='config.json')
    
    # 1. 初始化
    workflow.load_config()
    workflow.select_config()
    workflow.get_hci_credentials()
    
    vm_name = workflow.selected_config.get('target_vm', {}).get('name')
    vmid = workflow.get_vm_id(vm_name)
    print(f"\n目标虚拟机ID: {vmid}")
    
    ip = workflow.hci_credentials.get('ip')
    csrf_token = workflow.hci_credentials.get('csrf_token')
    cookie = workflow.hci_credentials.get('cookie')
    
    # 2. 获取当前状态
    print("\n" + "=" * 80)
    print("步骤1: 获取启动前的虚拟机状态")
    print("=" * 80)
    
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = browser.new_context(ignore_https_errors=True)
        
        url = f"https://{ip}/vapi/json/cluster/vms"
        headers = {
            "Accept": "*/*",
            "CSRFPreventionToken": csrf_token,
            "Cookie": cookie,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        resp = context.request.get(url, headers=headers, timeout=30000)
        if resp.status == 200:
            response_data = resp.json()
            groups = response_data.get('data', [])
            for group in groups:
                for vm in group.get('data', []):
                    if str(vm.get('vmid')) == str(vmid):
                        print(f"启动前状态: {vm.get('status')}")
        
        browser.close()
    
    # 3. 发送启动命令（带完整响应输出）
    print("\n" + "=" * 80)
    print("步骤2: 发送启动命令（完整响应）")
    print("=" * 80)
    
    import subprocess
    curl_command = f"""
curl -v -X POST "{ip}/vapi/extjs/cluster/vm/{vmid}/status/start" ^
-H "Accept: */*" ^
-H "CSRFPreventionToken: {csrf_token}" ^
-H "Cookie: {cookie}" ^
-H "X-Requested-With: XMLHttpRequest" ^
-k
"""
    
    print("执行启动命令...")
    print("-" * 80)
    process = subprocess.Popen(
        curl_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 合并stdout和stderr
        text=True,
        cwd="E:\\1"
    )
    stdout, _ = process.communicate(timeout=60)
    
    print("启动命令执行完成")
    print("-" * 80)
    print(f"退出码: {process.returncode}")
    print(f"\n完整响应:\n{stdout}")
    print("-" * 80)
    
    # 4. 等待30秒
    print("\n等待30秒后检查状态...")
    import time
    time.sleep(30)
    
    # 5. 再次获取状态
    print("\n" + "=" * 80)
    print("步骤3: 获取启动后的虚拟机状态")
    print("=" * 80)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = browser.new_context(ignore_https_errors=True)
        
        resp = context.request.get(url, headers=headers, timeout=30000)
        if resp.status == 200:
            response_data = resp.json()
            groups = response_data.get('data', [])
            for group in groups:
                for vm in group.get('data', []):
                    if str(vm.get('vmid')) == str(vmid):
                        status = vm.get('status')
                        print(f"启动30秒后状态: {status}")
                        if status == "running":
                            print("✓ 虚拟机已成功启动")
                        else:
                            print("✗ 虚拟机仍未启动")
                            print("可能原因：")
                            print("  1. 虚拟机启动失败，请检查HCI日志")
                            print("  2. 虚拟机启动需要更长时间")
                            print("  3. 虚拟机配置问题导致无法启动")
        
        browser.close()
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)

if __name__ == "__main__":
    debug_vm_start()