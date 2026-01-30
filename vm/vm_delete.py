import json
from playwright.sync_api import sync_playwright
import rsa
import binascii
import urllib.parse

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


def get_snapshot_id_by_name(vmid, snapshot_name, credentials):
    """
    通过 HCI API 获取虚拟机的快照列表，根据快照名称查找快照ID
    
    Args:
        vmid: 虚拟机ID
        snapshot_name: 快照名称
        credentials: HCI登录凭证
    
    Returns:
        str: 快照ID，如果未找到则返回 None
    """
    print(f"正在查询虚拟机 {vmid} 的快照列表...")
    
    context = credentials["context"]
    
    # 请求 URL：获取虚拟机快照列表
    url = f"https://{HCI_DEVICE_IP}/vapi/json/cluster/vm/{vmid}/snapshot"
    
    headers = {
        "Accept": "*/*",
        "CSRFPreventionToken": credentials["csrf_token"],
        "Cookie": credentials["cookie"],
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        resp = context.request.get(url, headers=headers, timeout=30000)
        
        if resp.status != 200:
            print(f"❌ 获取快照列表失败，状态码: {resp.status}")
            return None
        
        response_data = resp.json()
        
        if response_data.get("success") != 1:
            print(f"❌ 获取快照列表失败")
            print(f"响应: {response_data}")
            return None
        
        # 解析快照列表
        snapshots = response_data.get("data", [])
        
        if not snapshots:
            print(f"❌ 虚拟机 {vmid} 没有任何快照")
            return None
        
        print(f"✅ 获取到 {len(snapshots)} 个快照")
        
        # 调试：输出第一个快照的所有字段
        if snapshots:
            print("第一个快照的字段:")
            for key, value in snapshots[0].items():
                print(f"  {key}: {value}")
        
        # 查找匹配的快照名称
        for snapshot in snapshots:
            snap_name = snapshot.get("name")
            # 尝试多种可能的快照ID字段
            snap_id = (snapshot.get("snapname") or
                      snapshot.get("snapid") or
                      snapshot.get("snapshot_id") or
                      snapshot.get("id") or
                      snapshot.get("name"))
            
            if snap_name == snapshot_name:
                print(f"✅ 找到快照: {snap_name}, ID: {snap_id}")
                return snap_id
        
        print(f"❌ 未找到快照名称: {snapshot_name}")
        print(f"可用的快照:")
        for snapshot in snapshots:
            print(f"   - {snapshot.get('name')} (描述: {snapshot.get('description', '无')})")
        
        return None
        
    except Exception as e:
        print(f"❌ 查询快照列表失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_vmid_by_name(vm_name, credentials=None):
    """
    根据虚拟机名获取虚拟机ID
    通过查询 HCI API 实现
    
    Args:
        vm_name: 虚拟机名
        credentials: HCI登录凭证（可选，如果不提供则创建新的）
    
    Returns:
        str: 虚拟机ID，如果未找到则返回 None
    """
    print(f"正在查找虚拟机: {vm_name}")
    
    # 如果没有提供凭证，创建新的
    if credentials is None:
        credentials = get_hci_credentials_with_context()
        if not credentials:
            return None
    
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


def delete_snapshot(vm_name, snapshot_name):
    """
    发起删除虚拟机快照的请求
    基于提供的curl命令实现
    
    Args:
        vm_name: 虚拟机名称或ID（用于查找虚拟机ID）
        snapshot_name: 要删除的快照名称
    """
    # 1. 实时获取登录凭证和Playwright context
    credentials = get_hci_credentials_with_context()
    if not credentials:
        print("无法获取登录凭证，终止执行")
        return None
    
    # 提取 context, browser, playwright_instance
    context = credentials["context"]
    playwright_instance = credentials["playwright"]
    browser = credentials["browser"]
    
    print(f"虚拟机: {vm_name}")
    print(f"快照名称: {snapshot_name}")
    
    # 2. 判断是虚拟机名还是ID，并获取vmid
    vmid = None
    if vm_name.isdigit():
        # 是数字，作为ID处理
        vmid = vm_name
        print(f"使用虚拟机ID: {vmid}")
    else:
        # 不是数字，作为名称处理，查询ID
        vmid = get_vmid_by_name(vm_name, credentials)
        if not vmid:
            return None
    
    # 3. 直接从API获取快照ID
    print("正在查找快照ID...")
    snapshot_id = get_snapshot_id_by_name(vmid, snapshot_name, credentials)
    
    if not snapshot_id:
        return None
    
    # 4. 请求URL
    url = f"https://{HCI_DEVICE_IP}/vapi/extjs/cluster/vm/{vmid}/snapshot/{snapshot_id}"
    
    print(f"虚拟机ID: {vmid}")
    print(f"快照ID: {snapshot_id}")
    
    # 请求头（使用实时获取的凭证）
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "CSRFPreventionToken": credentials["csrf_token"],
        "Connection": "keep-alive",
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
    
    try:
        print("正在发起删除虚拟机快照的请求...")
        print(f"请求URL: {url}")
        print(f"请求方法: DELETE")
        
        # 使用Playwright context发送DELETE请求
        resp = context.request.delete(
            url,
            headers=headers,
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
    print("虚拟机快照删除工具")
    print("=" * 80)
    
    # 检查命令行参数数量
    if len(sys.argv) >= 3:
        # 提供了参数，执行删除快照操作
        vm_name_arg = sys.argv[1]
        snapshot_name = sys.argv[2]
        
        print("执行删除快照操作...")
        print(f"虚拟机: {vm_name_arg}")
        print(f"快照名称: {snapshot_name}")
        print()
        
        delete_snapshot(vm_name_arg, snapshot_name)
    else:
        # 没有提供参数，显示用法提示
        print("参数不足，请提供虚拟机名或ID和快照名称")
        print()
        print("用法: python vm_delete.py <虚拟机名或ID> <快照名称>")
        print()
        print("示例:")
        print("  python vm_delete.py \"XMG5100_2.127_0001\" \"test_snapshot_20260121\"")
        print("  python vm_delete.py 5370079826048 \"test_snapshot_20260121\"")
        print()
        print("说明:")
        print("  - 虚拟机名或ID: 要删除快照的虚拟机名称或ID")
        print("  - 快照名称: 要删除的快照名称")
    
    print()


    
