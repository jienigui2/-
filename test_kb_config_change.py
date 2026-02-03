#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试KB配置更改时的状态清除机制
"""

import os
import json
import configparser
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vm_management_workflow import load_module_state, save_module_state, load_kb_test_config

# 测试文件路径
MODULE_STATE_FILE = "module_state.json"
CONFIG_FILE = "all.ini"

def backup_config():
    """
    备份当前配置文件
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def restore_config(backup_content):
    """
    恢复配置文件
    """
    if backup_content:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(backup_content)

def modify_kb_config(kb_number, target_id):
    """
    修改KB配置
    """
    config_parser = configparser.ConfigParser()
    config_parser.read(CONFIG_FILE, encoding='utf-8')
    
    if 'kb_test' not in config_parser:
        config_parser['kb_test'] = {}
    
    config_parser['kb_test']['kb_number'] = kb_number
    config_parser['kb_test']['target_id'] = target_id
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        config_parser.write(f)

def test_kb_config_change():
    """
    测试KB配置更改时的状态清除机制
    """
    print("="*60)
    print("开始测试KB配置更改时的状态清除机制")
    print("="*60)
    
    # 备份当前配置
    config_backup = backup_config()
    print("✓ 已备份当前配置")
    
    try:
        # 1. 初始化状态
        print("\n1. 初始化测试状态...")
        
        # 创建初始状态
        initial_state = {
            "kb_config": {
                "kb_number": "KB-WACAP-20260116-Wlan-2025111403",
                "target_id": "001"
            },
            "download_kb": {
                "status": "completed",
                "kb_sign_file": "test_path/sign.tgz",
                "kb_file_path": "test_path/package.tgz",
                "kb_file_name": "package.tgz",
                "timestamp": 1234567890
            },
            "upgrade_kb": {
                "status": "completed",
                "timestamp": 1234567890
            },
            "kb_scan": {
                "status": "completed",
                "timestamp": 1234567890
            }
        }
        
        save_module_state(initial_state)
        print("✓ 已创建初始测试状态")
        
        # 2. 验证初始状态
        print("\n2. 验证初始状态...")
        state = load_module_state()
        print(f"   初始KB配置: {state.get('kb_config', {})}")
        print(f"   初始下载状态: {state.get('download_kb', {})}")
        print(f"   初始升级状态: {state.get('upgrade_kb', {})}")
        print(f"   初始扫描状态: {state.get('kb_scan', {})}")
        
        # 3. 修改KB配置
        print("\n3. 修改KB配置...")
        new_kb_number = "KB-WACAP-20260203-Test-001"
        new_target_id = "002"
        modify_kb_config(new_kb_number, new_target_id)
        print(f"   已修改KB配置为: kb_number={new_kb_number}, target_id={new_target_id}")
        
        # 4. 重新加载状态并验证
        print("\n4. 验证配置更改后的状态...")
        updated_state = load_module_state()
        print(f"   更新后KB配置: {updated_state.get('kb_config', {})}")
        print(f"   更新后下载状态: {updated_state.get('download_kb', {})}")
        print(f"   更新后升级状态: {updated_state.get('upgrade_kb', {})}")
        print(f"   更新后扫描状态: {updated_state.get('kb_scan', {})}")
        
        # 5. 验证状态是否被正确清除
        print("\n5. 验证状态清除结果...")
        download_status = updated_state.get('download_kb', {})
        upgrade_status = updated_state.get('upgrade_kb', {})
        scan_status = updated_state.get('kb_scan', {})
        
        if download_status.get('status') == 'idle' and download_status.get('kb_file_path') is None:
            print("✓ 下载状态已正确清除")
        else:
            print("✗ 下载状态清除失败")
        
        if upgrade_status.get('status') == 'idle':
            print("✓ 升级状态已正确清除")
        else:
            print("✗ 升级状态清除失败")
        
        if scan_status.get('status') == 'idle':
            print("✓ 扫描状态已正确清除")
        else:
            print("✗ 扫描状态清除失败")
        
        # 6. 验证KB配置是否更新
        kb_config = updated_state.get('kb_config', {})
        if kb_config.get('kb_number') == new_kb_number and kb_config.get('target_id') == new_target_id:
            print("✓ KB配置已正确更新")
        else:
            print("✗ KB配置更新失败")
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        
    finally:
        # 恢复原始配置
        restore_config(config_backup)
        print("\n✓ 已恢复原始配置")
        
        # 清理测试状态
        if os.path.exists(MODULE_STATE_FILE):
            os.remove(MODULE_STATE_FILE)
            print("✓ 已清理测试状态文件")

if __name__ == "__main__":
    test_kb_config_change()
