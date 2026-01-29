#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 HCI 设备 API 访问
使用 Playwright 解决 SSL 握手问题
"""

import sys
import os

# 直接从 loginnew.py 模块导入 HciLogin 类，避开有问题的包导入
loginnew_path = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'sw_hci_api')
if loginnew_path not in sys.path:
    sys.path.insert(0, loginnew_path)

import loginnew
HciLogin = loginnew.HciLogin

# 修改 loginnew.py 的请求方式，使用 Playwright 代替 requests
from playwright.sync_api import sync_playwright
import rsa
import binascii

def playwr_hci_login(ip, username, password, httpport="443"):
    """使用 Playwright 完成 HCI 登录"""
    print(f"正在登录 HCI 设备 {ip}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # 1. 获取公钥
        print("正在获取公钥...")
        public_key_url = f"https://{ip}:{httpport}/vapi/json/public_key"
        resp = page.request.get(public_key_url, timeout=30000)
        
        if resp.status != 200:
            print(f"❌ 获取公钥失败，状态码: {resp.status}")
            browser.close()
            return None
        
        try:
            public_key_data = resp.json()
            public_key = public_key_data.get("data")
        except:
            print(f"❌ 响应解析失败")
            browser.close()
            return None
        
        if not public_key:
            print("❌ 响应中没有找到公钥")
            browser.close()
            return None
        
        print(f"✅ 已获取公钥")
        
        # 2. RSA加密密码
        print("正在加密密码...")
        try:
            key = rsa.PublicKey(int(public_key, 16), int("10001", 16))
            password_temp = rsa.encrypt(bytes(password, encoding="utf-8"), key)
            password_rsa = str(binascii.b2a_hex(password_temp), encoding="utf-8")
            print(f"✅ 密码加密完成")
        except Exception as e:
            print(f"❌ 密码加密失败: {e}")
            browser.close()
            return None
        
        # 3. 发送登录请求
        print("正在登录...")
        login_url = f"https://{ip}:{httpport}/vapi/json/access/ticket"
        
        # 设置请求头
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # 构建表单数据
        form_data = f"username={username}&password={password_rsa}"
        
        resp = page.request.post(
            login_url,
            data=form_data,
            headers=login_headers,
            timeout=30000
        )
        
        if resp.status != 200:
            print(f"❌ 登录失败，状态码: {resp.status}")
            browser.close()
            return None
        
        try:
            login_data = resp.json()
        except Exception as e:
            print(f"❌ 登录响应解析失败: {e}")
            browser.close()
            return None
        
        print(f"✅ 登录响应: {login_data}")
        
        # 4. 提取登录凭证
        csrf_token = login_data.get("data", {}).get("CSRFPreventionToken")
        ticket = login_data.get("data", {}).get("ticket")
        
        if not csrf_token or not ticket:
            print("❌ 响应中没有找到CSRFPreventionToken或ticket")
            browser.close()
            return None
        
        print(f"✅ 成功获取登录凭证")
        
        # 5. 返回模拟的 HciLogin 对象（包含必要的属性和上下文）
        class MockHciLogin:
            def __init__(self, context, headers):
                self.headers = headers
                self.context = context
                self.browser = browser
            
            def get_json(self, action_url, data_dict, deeps=2):
                """发送 GET 请求"""
                url = f"https://{ip}:{httpport}/{action_url}"
                # 更新请求头
                headers = self.headers.copy()
                headers["X-Requested-With"] = "XMLHttpRequest"
                
                resp = self.context.request.get(
                    url,
                    params=data_dict,
                    headers=headers,
                    timeout=30000
                )
                
                if resp.status == 200:
                    result = resp.json()
                    print(f"GET 请求响应: {result}")
                    return result
                else:
                    print(f"GET 请求失败，状态码: {resp.status}")
                    return None
            
            def post_json(self, action_url, data_dict, deeps=2):
                """发送 POST 请求"""
                url = f"https://{ip}:{httpport}/{action_url}"
                # 更新请求头
                headers = self.headers.copy()
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers["X-Requested-With"] = "XMLHttpRequest"
                
                resp = self.context.request.post(
                    url,
                    data=data_dict,
                    headers=headers,
                    timeout=30000
                )
                
                if resp.status == 200:
                    result = resp.json()
                    print(f"POST 请求响应: {result}")
                    return result
                else:
                    print(f"POST 请求失败，状态码: {resp.status}")
                    return None
            
            def close(self):
                """关闭连接"""
                self.browser.close()
        
        mock_hci = MockHciLogin(context, {
            "CSRFPreventionToken": csrf_token,
            "Cookie": f"LoginAuthCookie={ticket}"
        })
        
        return mock_hci


if __name__ == "__main__":
    # 使用 Playwright 上下文管理器
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # 1. 获取公钥
        print("正在获取公钥...")
        ip = "10.156.1.50"
        httpport = "443"
        username = "admin"
        password = "Msgt@202601"
        
        public_key_url = f"https://{ip}:{httpport}/vapi/json/public_key"
        resp = page.request.get(public_key_url, timeout=30000)
        
        if resp.status != 200:
            print(f"❌ 获取公钥失败，状态码: {resp.status}")
            browser.close()
            sys.exit(1)
        
        public_key = resp.json().get("data")
        print(f"✅ 已获取公钥")
        
        # 2. RSA加密密码
        print("正在加密密码...")
        key = rsa.PublicKey(int(public_key, 16), int("10001", 16))
        password_temp = rsa.encrypt(bytes(password, encoding="utf-8"), key)
        password_rsa = str(binascii.b2a_hex(password_temp), encoding="utf-8")
        print(f"✅ 密码加密完成")
        
        # 3. 发送登录请求
        print("正在登录...")
        login_url = f"https://{ip}:{httpport}/vapi/json/access/ticket"
        
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        form_data = f"username={username}&password={password_rsa}"
        
        resp = page.request.post(
            login_url,
            data=form_data,
            headers=login_headers,
            timeout=30000
        )
        
        login_data = resp.json()
        print(f"✅ 登录成功")
        
        csrf_token = login_data.get("data", {}).get("CSRFPreventionToken")
        ticket = login_data.get("data", {}).get("ticket")
        
        # 4. 创建 HciLogin 对象
        class HciLogin:
            def __init__(self, context, csrf_token, ticket, ip, httpport):
                self.context = context
                self.csrf_token = csrf_token
                self.ticket = ticket
                self.ip = ip
                self.httpport = httpport
            
            def get_json(self, action_url, data_dict, deeps=2):
                """发送 GET 请求"""
                url = f"https://{self.ip}:{self.httpport}/{action_url}"
                
                headers = {
                    "CSRFPreventionToken": self.csrf_token,
                    "Cookie": f"LoginAuthCookie={self.ticket}",
                    "X-Requested-With": "XMLHttpRequest"
                }
                
                resp = self.context.request.get(
                    url,
                    params=data_dict,
                    headers=headers,
                    timeout=30000
                )
                
                if resp.status == 200:
                    result = resp.json()
                    print(f"GET 请求响应: {result}")
                    return result
                else:
                    print(f"GET 请求失败，状态码: {resp.status}")
                    return None
            
            def post_json(self, action_url, data_dict, deeps=2):
                """发送 POST 请求"""
                url = f"https://{self.ip}:{self.httpport}/{action_url}"
                
                headers = {
                    "CSRFPreventionToken": self.csrf_token,
                    "Cookie": f"LoginAuthCookie={self.ticket}",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest"
                }
                
                resp = self.context.request.post(
                    url,
                    data=data_dict,
                    headers=headers,
                    timeout=30000
                )
                
                if resp.status == 200:
                    result = resp.json()
                    print(f"POST 请求响应: {result}")
                    return result
                else:
                    print(f"POST 请求失败，状态码: {resp.status}")
                    return None
        
        h = HciLogin(context, csrf_token, ticket, ip, httpport)
        
        # 5. 发送 GET 请求
        result = h.get_json(action_url="/vapi/extjs/index/overview", data_dict={})
        
        # 发送 POST 请求示例
        # result = h.post_json(action_url="/vapi/extjs/cluster/vms", data_dict={"group_type": "group"})
        
        # 关闭连接
        browser.close()