import requests
import json
from playwright.sync_api import sync_playwright

# ============ HCI 设备登录配置 ============
HCI_DEVICE_IP = "10.156.1.50"
HCI_USERNAME = "admin"
HCI_PASSWORD = "Msgt@202601"
HCI_HTTP_PORT = "443"
# =========================================


def get_hci_credentials_with_context():
    """使用Playwright实时获取 HCI 设备的登录凭证，并返回context对象"""
    try:
        print(f"正在登录 HCI 设备 {HCI_DEVICE_IP}...")
        
        # 处理asyncio循环冲突问题
        import asyncio
        try:
            # 尝试关闭现有的asyncio循环
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                loop.close()
        except:
            pass
        
        # 使用Playwright完成登录（可以处理SSL问题）
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # 1. 获取公钥
        print("正在获取公钥...")
        public_key_url = f"https://{HCI_DEVICE_IP}:{HCI_HTTP_PORT}/vapi/json/public_key"
        resp = page.request.get(public_key_url, timeout=30000)
        
        if resp.status != 200:
            print(f"❌ 获取公钥失败，状态码: {resp.status}")
            p.stop()
            return None
        
        try:
            public_key_data = resp.json()
            public_key = public_key_data.get("data")
        except:
            print(f"❌ 响应解析失败")
            p.stop()
            return None
        
        if not public_key:
            print("❌ 响应中没有找到公钥")
            p.stop()
            return None
        
        print(f"✅ 已获取公钥")
        
        # 2. RSA加密密码
        print("正在加密密码...")
        try:
            import rsa
            import binascii
            
            key = rsa.PublicKey(int(public_key, 16), int("10001", 16))
            password_temp = rsa.encrypt(bytes(HCI_PASSWORD, encoding="utf-8"), key)
            password_rsa = str(binascii.b2a_hex(password_temp), encoding="utf-8")
            print(f"✅ 密码加密完成")
        except Exception as e:
            print(f"❌ 密码加密失败: {e}")
            p.stop()
            return None
        
        # 3. 发送登录请求
        print("正在登录...")
        login_url = f"https://{HCI_DEVICE_IP}:{HCI_HTTP_PORT}/vapi/json/access/ticket"
        
        # 设置请求头
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # 构建表单数据
        form_data = f"username={HCI_USERNAME}&password={password_rsa}"
        
        resp = page.request.post(
            login_url,
            data=form_data,
            headers=login_headers,
            timeout=30000
        )
        
        if resp.status != 200:
            print(f"❌ 登录失败，状态码: {resp.status}")
            print(f"响应内容: {resp.text()}")
            p.stop()
            return None
        
        try:
            login_data = resp.json()
        except Exception as e:
            print(f"❌ 登录响应解析失败: {e}")
            print(f"响应内容: {resp.text()}")
            p.stop()
            return None
        
        print(f"✅ 登录响应: {login_data}")
        
        # 4. 提取登录凭证
        csrf_token = login_data.get("data", {}).get("CSRFPreventionToken")
        ticket = login_data.get("data", {}).get("ticket")
        
        if not csrf_token or not ticket:
            print("❌ 响应中没有找到CSRFPreventionToken或ticket")
            p.stop()
            return None
        
        credentials = {
            "csrf_token": csrf_token,
            "cookie": f"LoginAuthCookie={ticket}",
            "context": context,
            "playwright": p,
            "browser": browser
        }
        
        print(f"✅ 成功获取登录凭证")
        
        return credentials
            
    except Exception as e:
        print(f"❌ 获取 HCI 登录凭证失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_vmid_by_name(vm_name, credentials):
    """
    通过虚拟机名称查找虚拟机ID
    
    Args:
        vm_name: 虚拟机名称
        credentials: HCI登录凭证
    
    Returns:
        str: 虚拟机ID，如果未找到则返回 None
    """
    print(f"正在查找虚拟机: {vm_name}")
    
    context = credentials["context"]
    
    # 请求 URL：获取集群虚拟机列表
    url = f"https://{HCI_DEVICE_IP}/vapi/json/cluster/vms"
    
    headers = {
        "Accept": "*/*",
        "CSRFPreventionToken": credentials["csrf_token"],
        "Cookie": credentials["cookie"],
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        params = {
            "group_type": "group",
            "sort_type": "",
            "desc": "1",
            "scene": "resources_used"
        }
        
        resp = context.request.get(url, params=params, headers=headers, timeout=30000)
        
        if resp.status != 200:
            print(f"❌ 获取虚拟机列表失败，状态码: {resp.status}")
            return None
        
        response_data = resp.json()
        
        if response_data.get("success") != 1:
            print(f"❌ 获取虚拟机列表失败")
            print(f"响应: {response_data}")
            return None
        
        # 解析虚拟机列表（数据是分组的）
        groups = response_data.get("data", [])
        
        # 在所有组中查找虚拟机
        for group in groups:
            vms = group.get("data", [])
            for vm in vms:
                if vm.get("name") == vm_name:
                    vmid = vm.get("vmid")
                    print(f"✅ 找到虚拟机: {vm_name}, ID: {vmid}")
                    return vmid
        
        print(f"❌ 未找到虚拟机名称: {vm_name}")
        print(f"可用的虚拟机:")
        vm_count = 0
        for group in groups:
            vms = group.get("data", [])
            for vm in vms:
                print(f"   - {vm.get('name')} (ID: {vm.get('vmid')})")
                vm_count += 1
                if vm_count >= 10:
                    print(f"   ... 还有更多")
                    break
            if vm_count >= 10:
                break
        
        return None
        
    except Exception as e:
        print(f"❌ 查询虚拟机列表失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_vm_snapshot(vm_name_or_id=None, snapname=None, description=None):
    """
    发起创建虚拟机快照的请求
    使用Playwright发送API请求，避免SSL握手问题
    
    Args:
        vm_name_or_id: 虚拟机名称或ID (如 "XMG5100_2.127_0001" 或 "5370079826048")
        snapname: 快照名称 (如 "2026-01-21_15-01-11")
        description: 快照描述
    
    Returns:
        dict: 包含请求参数和响应数据的字典
    """
    # 1. 实时获取登录凭证和Playwright context
    credentials = get_hci_credentials_with_context()
    if not credentials:
        print("无法获取登录凭证，终止执行")
        return None
    
    context = credentials["context"]
    playwright_instance = credentials["playwright"]
    browser = credentials["browser"]
    
    # 2. 获取用户输入（如果未提供参数）
    import sys
    if vm_name_or_id is None and len(sys.argv) > 1:
        vm_name_or_id = sys.argv[1]
    elif vm_name_or_id is None:
        print("请提供虚拟机名称或ID")
        print("用法: python vm_new.py <虚拟机名或ID> [快照名称] [快照描述]")
        print("示例: python vm_new.py \"XMG5100_2.127_0001\" \"2026-01-21_15-01-11\" \"测试快照\"")
        print("      python vm_new.py 5370079826048 \"2026-01-21_15-01-11\" \"测试快照\"")
        return None
    
    # 3. 判断是虚拟机名还是ID，并获取vmid
    vmid = None
    if vm_name_or_id.isdigit():
        # 是数字，作为ID处理
        vmid = vm_name_or_id
        print(f"使用虚拟机ID: {vmid}")
    else:
        # 不是数字，作为名称处理，查询ID
        vmid = get_vmid_by_name(vm_name_or_id, credentials)
        if not vmid:
            print(f"❌ 无法找到虚拟机: {vm_name_or_id}")
            return None
    
    if snapname is None and len(sys.argv) > 2:
        snapname = sys.argv[2]
    elif snapname is None:
        # 默认生成时间戳作为快照名称
        from datetime import datetime
        snapname = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"未提供快照名称，使用默认值: {snapname}")
    
    if description is None and len(sys.argv) > 3:
        description = sys.argv[3]
    elif description is None:
        description = ""
        print(f"未提供快照描述，使用默认值: （空）")
    
    # 请求URL
    url = f"https://{HCI_DEVICE_IP}/vapi/json/cluster/vm/{vmid}/snapshot"
    
    # 请求头（使用实时获取的凭证）
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "CSRFPreventionToken": credentials["csrf_token"],
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": f"https://{HCI_DEVICE_IP}",
        "Referer": f"https://{HCI_DEVICE_IP}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cookie": credentials["cookie"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Microsoft Edge\";v=\"144\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    
    # 请求数据（使用用户输入的值）
    data = {
        "snapname": snapname,
        "description": description,
        "vmstate": 0,
        "snaptype": 1
    }
    
    try:
        print("正在发起创建虚拟机快照的请求...")
        print(f"请求URL: {url}")
        
        # 将数据转换为URL编码的表单格式
        import urllib.parse
        form_data = urllib.parse.urlencode(data)
        print(f"请求数据: {form_data}")
        
        # 使用Playwright context发送POST请求
        resp = context.request.post(
            url,
            headers=headers,
            data=form_data,
            timeout=30000
        )
        
        print(f"\n响应状态码: {resp.status}")
        print(f"响应内容: {resp.text()}")
        
        # 尝试解析JSON响应
        try:
            response_json = resp.json()
            print(f"\n响应JSON解析成功:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
             
            return response_json
        except:
            print("\n响应不是有效的JSON格式")
            return {"status": resp.status, "text": resp.text()}
            
    except Exception as e:
        print(f"\n请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # 关闭Playwright实例
        try:
            browser.close()
            playwright_instance.stop()
        except:
            pass


if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("虚拟机快照创建工具")
    print("=" * 80)
    
    # 检查命令行参数数量
    if len(sys.argv) >= 2:
        # 提供了虚拟机ID或名称
        vm_name_or_id = sys.argv[1]
        snapname_arg = sys.argv[2] if len(sys.argv) > 2 else None
        description_arg = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"虚拟机: {vm_name_or_id}")
        print()
        create_vm_snapshot(vm_name_or_id, snapname_arg, description_arg)
    else:
        # 没有提供参数，显示用法提示
        print("参数不足，请提供虚拟机名称或ID")
        print()
        print("用法: python vm_new.py <虚拟机名或ID> [快照名称] [快照描述]")
        print()
        print("示例:")
        print("  python vm_new.py \"XMG5100_2.127_0001\" \"2026-01-21_15-01-11\" \"测试快照\"")
        print("  python vm_new.py 5370079826048 \"2026-01-21_15-01-11\"")
        print("  python vm_new.py \"XMG5100_2.127_0001\"  # 快照名称会自动生成")
        print()
        print("说明:")
        print("  - 虚拟机名或ID: 支持虚拟机名称（如XMG5100_2.127_0001）或虚拟机ID（如5370079826048）")
        print("  - 快照名称: 可选，如果不提供将自动生成时间戳名称")
        print("  - 快照描述: 可选，如果不提供则为空")
    
    print()
