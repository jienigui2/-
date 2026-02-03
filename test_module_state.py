#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模块状态管理功能
"""

import json
import os
import time

# 模块状态文件路径
MODULE_STATE_FILE = "module_state.json"

# 加载模块状态
def load_module_state():
    """
    加载模块状态文件
    
    Returns:
        dict: 模块状态字典
    """
    if not os.path.exists(MODULE_STATE_FILE):
        return {
            "prepare": {
                "status": "idle",
                "config_loaded": False,
                "timestamp": None
            },
            "download_kb": {
                "status": "idle",
                "kb_sign_file": None,
                "kb_file_path": None,
                "kb_file_name": None,
                "timestamp": None
            },
            "kb_conflict": {
                "status": "idle",
                "timestamp": None
            },
            "recover_snapshot": {
                "status": "idle",
                "vmid": None,
                "snapshot_id": None,
                "timestamp": None
            },
            "modify_ip": {
                "status": "idle",
                "ip_address": None,
                "timestamp": None
            },
            "recover_customer_config": {
                "status": "idle",
                "timestamp": None
            },
            "check_reboot": {
                "status": "idle",
                "timestamp": None
            },
            "upgrade_kb": {
                "status": "idle",
                "timestamp": None
            },
            "kb_scan": {
                "status": "idle",
                "timestamp": None
            }
        }
    
    try:
        with open(MODULE_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误: 加载模块状态文件失败: {e}")
        return {
            "prepare": {
                "status": "idle",
                "config_loaded": False,
                "timestamp": None
            },
            "download_kb": {
                "status": "idle",
                "kb_sign_file": None,
                "kb_file_path": None,
                "kb_file_name": None,
                "timestamp": None
            },
            "kb_conflict": {
                "status": "idle",
                "timestamp": None
            },
            "recover_snapshot": {
                "status": "idle",
                "vmid": None,
                "snapshot_id": None,
                "timestamp": None
            },
            "modify_ip": {
                "status": "idle",
                "ip_address": None,
                "timestamp": None
            },
            "recover_customer_config": {
                "status": "idle",
                "timestamp": None
            },
            "check_reboot": {
                "status": "idle",
                "timestamp": None
            },
            "upgrade_kb": {
                "status": "idle",
                "timestamp": None
            },
            "kb_scan": {
                "status": "idle",
                "timestamp": None
            }
        }

# 保存模块状态
def save_module_state(state):
    """
    保存模块状态到文件
    
    Args:
        state: 模块状态字典
    """
    try:
        with open(MODULE_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print(f"成功: 模块状态已保存到 {MODULE_STATE_FILE}")
    except Exception as e:
        print(f"错误: 保存模块状态文件失败: {e}")

# 测试函数
def test_module_state():
    """
    测试模块状态管理功能
    """
    print("=" * 50)
    print("开始测试模块状态管理功能")
    print("=" * 50)
    
    # 1. 测试初始状态
    print("\n1. 测试初始状态:")
    state = load_module_state()
    print(json.dumps(state, indent=2, ensure_ascii=False))
    
    # 2. 测试更新准备模块状态
    print("\n2. 测试更新准备模块状态:")
    state["prepare"]["status"] = "completed"
    state["prepare"]["config_loaded"] = True
    state["prepare"]["timestamp"] = time.time()
    save_module_state(state)
    
    # 3. 测试更新下载KB包模块状态
    print("\n3. 测试更新下载KB包模块状态:")
    state["download_kb"]["status"] = "completed"
    state["download_kb"]["kb_sign_file"] = "F:\KB\KB12345\KB_SIGN.txt"
    state["download_kb"]["kb_file_path"] = "F:\KB\KB12345\KB12345.tgz"
    state["download_kb"]["kb_file_name"] = "KB12345.tgz"
    state["download_kb"]["timestamp"] = time.time()
    save_module_state(state)
    
    # 4. 测试重新加载状态
    print("\n4. 测试重新加载状态:")
    new_state = load_module_state()
    print(json.dumps(new_state, indent=2, ensure_ascii=False))
    
    # 5. 测试依赖检查
    print("\n5. 测试依赖检查:")
    if new_state["prepare"]["status"] == "completed":
        print("✓ 准备模块已完成")
    else:
        print("✗ 准备模块未完成")
    
    if new_state["download_kb"]["status"] == "completed":
        print("✓ 下载KB包模块已完成")
        print(f"  KB包路径: {new_state['download_kb']['kb_file_path']}")
        print(f"  KB包名称: {new_state['download_kb']['kb_file_name']}")
    else:
        print("✗ 下载KB包模块未完成")
    
    print("\n" + "=" * 50)
    print("模块状态管理功能测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_module_state()
