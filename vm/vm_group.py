import subprocess
import json
import time
from playwright.sync_api import sync_playwright

class VMGroupManager:
    """虚拟机组管理器，用于获取和管理虚拟机组信息"""
    
    def __init__(self, hci_ip, hci_username, hci_password, http_port='443'):
        """初始化VMGroupManager
        
        Args:
            hci_ip: HCI设备IP地址
            hci_username: HCI设备登录用户名
            hci_password: HCI设备登录密码
            http_port: HTTP端口，默认为443
        """
        self.hci_ip = hci_ip
        self.hci_username = hci_username
        self.hci_password = hci_password
        self.http_port = http_port
        self.hci_credentials = None
    
    def get_hci_credentials(self):
        """获取HCI设备登录凭证，包括CSRF token和cookie"""
        try:
            print(f"正在登录 HCI 设备 {self.hci_ip}...")
            
            # 使用Playwright完成登录
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                
                # 获取公钥
                print("正在获取公钥...")
                public_key_url = f"https://{self.hci_ip}:{self.http_port}/vapi/json/public_key"
                resp = page.request.get(public_key_url, timeout=30000)
                
                if resp.status != 200:
                    print(f"✗ 获取公钥失败，状态码: {resp.status}")
                    browser.close()
                    return False
                
                public_key_data = resp.json()
                public_key = public_key_data.get('data')
                
                if not public_key:
                    print("✗ 响应中没有找到公钥")
                    browser.close()
                    return False
                
                print("✓ 已获取公钥")
                
                # RSA加密密码
                print("正在加密密码...")
                import rsa
                import binascii
                key = rsa.PublicKey(int(public_key, 16), int("10001", 16))
                password_temp = rsa.encrypt(bytes(self.hci_password, encoding="utf-8"), key)
                password_rsa = str(binascii.b2a_hex(password_temp), encoding="utf-8")
                print("✓ 密码加密完成")
                
                # 发送登录请求
                print("正在登录...")
                login_url = f"https://{self.hci_ip}:{self.http_port}/vapi/json/access/ticket"
                
                login_headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest"
                }
                
                form_data = f"username={self.hci_username}&password={password_rsa}"
                
                resp = page.request.post(
                    login_url,
                    data=form_data,
                    headers=login_headers,
                    timeout=30000
                )
                
                if resp.status != 200:
                    print(f"✗ 登录失败，状态码: {resp.status}")
                    browser.close()
                    return False
                
                login_data = resp.json()
                csrf_token = login_data.get("data", {}).get("CSRFPreventionToken")
                ticket = login_data.get("data", {}).get("ticket")
                
                if not csrf_token or not ticket:
                    print("✗ 响应中没有找到CSRFPreventionToken或ticket")
                    browser.close()
                    return False
                
                # 获取完整的cookie
                cookies = context.cookies()
                cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
                
                self.hci_credentials = {
                    "csrf_token": csrf_token,
                    "cookie": cookie_string,
                    "ticket": ticket,
                    "ip": self.hci_ip,
                    "http_port": self.http_port,
                    "username": self.hci_username,
                    "password": self.hci_password
                }
                
                browser.close()
                print("✓ 成功获取HCI登录凭证")
                return True
                
        except Exception as e:
            print(f"✗ 获取HCI登录凭证失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_vm_groups(self):
        """获取虚拟机组列表"""
        if not self.hci_credentials:
            print("✗ HCI登录凭证未获取，正在尝试获取...")
            if not self.get_hci_credentials():
                print("✗ 获取HCI登录凭证失败，无法继续")
                return None
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            print(f"正在获取虚拟机组列表...")
            
            # 构建curl命令
            curl_command = f"curl -k -s \"https://{ip}/vapi/extjs/cluster/vms?group_type=group&sort_type=&desc=1&scene=resources_used\" -H \"Accept: */*\" -H \"Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6\" -H \"CSRFPreventionToken: {csrf_token}\" -H \"Connection: keep-alive\" -H \"Cookie: {cookie}\" -H \"Referer: https://{ip}/\" -H \"Sec-Fetch-Dest: empty\" -H \"Sec-Fetch-Mode: cors\" -H \"Sec-Fetch-Site: same-origin\" -H \"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\" -H \"X-Requested-With: XMLHttpRequest\""
            
            # 执行curl命令
            print(f"执行命令: {curl_command[:100]}...")
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            print(f"响应状态: 完成")
            
            # 解析响应
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                    
                    if response_data.get("success") == 1:
                        groups = response_data.get("data", [])
                        print(f"✓ 获取到 {len(groups)} 个虚拟机组")
                        return groups
                    else:
                        print(f"✗ 获取虚拟机组失败")
                        print(f"响应: {result.stdout[:200]}")
                        return None
                except json.JSONDecodeError:
                    print(f"✗ 无法解析响应JSON")
                    print(f"响应内容: {result.stdout[:200]}")
                    return None
            else:
                print(f"✗ curl命令没有返回响应")
                if result.stderr:
                    print(f"错误信息: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"✗ 获取虚拟机组失败: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    # 测试代码
    HCI_DEVICE_IP = "10.156.1.50"
    HCI_USERNAME = "admin"
    HCI_PASSWORD = "Msgt@202601"
    
    manager = VMGroupManager(HCI_DEVICE_IP, HCI_USERNAME, HCI_PASSWORD)
    groups = manager.get_vm_groups()
    
    if groups:
        print("\n虚拟机组及虚拟机列表:")
        print("=" * 100)
        for group in groups:
            group_name = group.get('name', '未命名')
            vms = group.get('data', [])
            
            print(f"\n📁 组名: {group_name} (共 {len(vms)} 个虚拟机)")
            print("-" * 100)
            
            for vm in vms:
                vm_name = vm.get('name', '未命名')
                vmid = vm.get('vmid', '未知')
                vm_status = vm.get('status', '未知')
                
                # 状态中文映射
                status_map = {
                    'running': '运行中',
                    'stopped': '已停止',
                    'paused': '已暂停'
                }
                status_cn = status_map.get(vm_status, vm_status)
                
                print(f"   虚拟机: {vm_name}")
                print(f"      VMID: {vmid}")
                print(f"      状态: {status_cn}")
                print()
            
            print("=" * 100)
    else:
        print("未获取到虚拟机组")