#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 HciLogin 实时获取 HCI 设备的登录凭证（Cookie 和 CSRFPreventionToken）
"""

from sw_hci_api import HciLogin
import json


def get_hci_login_credentials(ip, username, password, httpport="443"):
    """
    获取 HCI 设备的登录凭证
    
    Args:
        ip: 设备IP地址
        username: 用户名
        password: 密码
        httpport: HTTP端口，默认443
        
    Returns:
        dict: 包含 cookie 和 csrf_token 的字典
    """
    print(f"正在连接设备: {ip}")
    print(f"用户名: {username}")
    
    # 创建 HciLogin 实例（会自动登录）
    hci = HciLogin(ip=ip, username=username, password=password, httpport=httpport)
    
    # 提取登录凭证
    credentials = {
        "ip": ip,
        "cookie": hci.headers.get("Cookie"),
        "csrf_token": hci.headers.get("CSRFPreventionToken"),
        "httpport": httpport
    }
    
    print("\n=== 获取成功 ===")
    print(f"Cookie: {credentials['cookie']}")
    print(f"CSRFPreventionToken: {credentials['csrf_token']}")
    
    return credentials, hci


def save_credentials_to_file(credentials, output_file="hci_credentials.json"):
    """
    将凭证保存到文件
    
    Args:
        credentials: 凭证字典
        output_file: 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(credentials, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 凭证已保存到: {output_file}")


def test_api_call(hci):
    """
    测试 API 调用
    
    Args:
        hci: HciLogin 实例
    """
    print("\n=== 测试 API 调用 ===")
    
    # 测试获取概览信息
    result = hci.get_json(action_url="/vapi/extjs/index/overview", data_dict={})
    
    if result:
        print("✅ API 调用成功")
        print(f"返回数据: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
    else:
        print("❌ API 调用失败")


if __name__ == "__main__":
    # ============ 配置信息 ============
    DEVICE_IP = "10.159.120.200"  # 修改为你的设备IP
    USERNAME = "admin"
    PASSWORD = "Wnst12345"        # 修改为你的密码
    HTTP_PORT = "443"
    # ==================================
    
    # 获取登录凭证
    credentials, hci_instance = get_hci_login_credentials(
        ip=DEVICE_IP,
        username=USERNAME,
        password=PASSWORD,
        httpport=HTTP_PORT
    )
    
    # 保存凭证到文件
    save_credentials_to_file(credentials)
    
    # 测试 API 调用（可选）
    test_api_call(hci_instance)
    
    # 提示：凭证有过期时间，如果遇到 401 认证错误，需要重新登录
    print("\n💡 提示：Cookie 有过期时间，过期后会自动重新登录")