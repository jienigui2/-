#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试虚拟机启动功能
"""

from vm_management_workflow import VMManagementWorkflow

def test_start_vm():
    """简单测试启动虚拟机"""
    print("=" * 80)
    print("简单测试虚拟机启动")
    print("=" * 80)
    
    workflow = VMManagementWorkflow(config_file='config.json')
    
    # 1. 加载配置
    if not workflow.load_config():
        return
    print("✓ 配置加载成功")
    
    # 2. 选择配置
    if not workflow.select_config():
        return
    print("✓ 配置选择成功")
    
    # 3. 获取登录凭证
    if not workflow.get_hci_credentials():
        return
    print("✓ 登录凭证获取成功")
    
    # 4. 获取虚拟机ID
    vm_name = workflow.selected_config.get('target_vm', {}).get('name')
    vmid = workflow.get_vm_id(vm_name)
    if not vmid:
        return
    print(f"✓ 虚拟机ID: {vmid}")
    
    # 5. 测试直接发送启动命令（不等待状态）
    print("\n" + "=" * 80)
    print("步骤1: 直接发送启动命令，不等待状态检查")
    print("=" * 80)
    
    try:
        ip = workflow.hci_credentials.get('ip')
        csrf_token = workflow.hci_credentials.get('csrf_token')
        cookie = workflow.hci_credentials.get('cookie')
        
        curl_command = f"""
curl ^"https://{ip}/vapi/extjs/cluster/vm/{vmid}/status/start^" ^
-X ^"POST^" ^
-H ^"CSRFPreventionToken: {csrf_token}^" ^
-H ^"Cookie: {cookie}^" ^
--insecure
"""
        
        import subprocess
        process = subprocess.Popen(
            curl_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="E:\\1"
        )
        stdout, stderr = process.communicate(timeout=60)
        
        print(f"启动命令退出码: {process.returncode}")
        if stdout:
            print(f"启动响应内容: {stdout}")
        if stderr:
            print(f"启动错误信息: {stderr}")
    except Exception as e:
        print(f"✗ 启动失败: {e}")
    
    # 等待10秒
    print("\n等待10秒...")
    import time
    time.sleep(10)
    
    # 6. 测试使用Playwright获取虚拟机列表
    print("\n" + "=" * 80)
    print("步骤2: 使用Playwright获取虚拟机列表（带参数）")
    print("=" * 80)
    
    try:
        from playwright.sync_api import sync_playwright
        
        url = f"https://{ip}/vapi/json/cluster/vms"
        params = {
            "group_type": "group",
            "sort_type": "",
            "desc": "1",
            "scene": "resources_used"
        }
        
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
            context = browser.new_context(ignore_https_errors=True)
            
            headers = {
                "Accept": "*/*",
                "CSRFPreventionToken": csrf_token,
                "Cookie": cookie,
                "X-Requested-With": "XMLHttpRequest"
            }
            
            resp = context.request.get(url, params=params, headers=headers, timeout=30000)
            
            print(f"响应状态码: {resp.status}")
            print(f"响应内容长度: {len(resp.text())} 字符")
            print(f"响应前500字符: {resp.text()[:500]}")
            
            if resp.status == 200:
                response_data = resp.json()
                print(f"响应success: {response_data.get('success')}")
                groups = response_data.get('data', [])
                print(f"分组数量: {len(groups)}")
                
                for group in groups:
                    vms = group.get('data', [])
                    for vm in vms:
                        if str(vm.get('vmid')) == str(vmid):
                            print(f"✓ 找到虚拟机: 状态={vm.get('status')}, 状态文本={vm.get('status_text')}")
            
            browser.close()
    except Exception as e:
        print(f"✗ 获取列表失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_start_vm()