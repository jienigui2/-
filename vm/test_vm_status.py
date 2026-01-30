#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试虚拟机状态检查功能
"""

from vm_management_workflow import VMManagementWorkflow

def test_vm_status():
    """测试虚拟机状态检查"""
    print("=" * 80)
    print("测试虚拟机状态检查功能")
    print("=" * 80)
    
    # 创建工作流实例
    workflow = VMManagementWorkflow(config_file='config.json')
    
    # 1. 加载配置文件
    print("\n1. 加载配置文件...")
    if not workflow.load_config():
        print("✗ 加载配置文件失败")
        return
    print("✓ 配置文件加载成功")
    
    # 2. 选择配置
    print("\n2. 选择配置...")
    if not workflow.select_config():
        print("✗ 选择配置失败")
        return
    print("✓ 配置选择成功")
    
    # 3. 获取HCI登录凭证
    print("\n3. 获取HCI登录凭证...")
    if not workflow.get_hci_credentials():
        print("✗ 获取HCI登录凭证失败")
        return
    print("✓ HCI登录凭证获取成功")
    
    # 4. 获取目标虚拟机ID
    print("\n4. 获取目标虚拟机ID...")
    target_vm = workflow.selected_config.get('target_vm', {})
    vm_name = target_vm.get('name')
    print(f"目标虚拟机名称: {vm_name}")
    
    vmid = workflow.get_vm_id(vm_name)
    if not vmid:
        print(f"✗ 无法获取虚拟机 {vm_name} 的ID")
        return
    print(f"✓ 虚拟机ID: {vmid}")
    
    # 5. 测试获取虚拟机状态
    print("\n5. 获取虚拟机状态...")
    status_info = workflow.get_vm_status(vmid)
    
    if status_info:
        status = status_info.get("status")
        status_text = status_info.get("status_text")
        print(f"✓ 虚拟机状态: {status}")
        print(f"✓ 状态文本: {status_text}")
    else:
        print("✗ 无法获取虚拟机状态")
    
    # 6. 无论当前状态如何，尝试启动虚拟机（确保状态为运行中）
    print("\n6. 尝试启动虚拟机...")
    print(f"当前状态信息: {status_info}")
    
    # 直接启动虚拟机，不依赖之前的状态检查
    print("\n正在启动虚拟机...")
    # 只等待状态变为运行中，不等待完全启动
    if workflow.start_vm(vmid, wait_boot_complete=False):
        print("✓ 虚拟机启动成功")
        print("✓ 虚拟机状态已变为运行中")
    else:
        print("✗ 虚拟机启动失败")
    
    # 7. 再次获取虚拟机状态
    print("\n7. 再次获取虚拟机状态...")
    status_info = workflow.get_vm_status(vmid)
    
    if status_info:
        status = status_info.get("status")
        status_text = status_info.get("status_text")
        print(f"✓ 当前虚拟机状态: {status}")
        print(f"✓ 当前状态文本: {status_text}")
    else:
        print("✗ 无法获取虚拟机状态")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_vm_status()