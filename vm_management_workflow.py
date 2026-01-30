import os
import sys
import json
import argparse
import time
import traceback
import ssl
import subprocess
from playwright.sync_api import sync_playwright
import rsa
import binascii
import requests
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入peizhi.py中的功能
import peizhi

class HTTPHelper:
    """HTTP请求助手类，用于统一处理HTTP请求和错误"""
    
    @staticmethod
    def create_ssl_context():
        """创建自定义SSL上下文，解决SSL握手失败问题"""
        context = ssl.create_default_context()
        # 禁用SSL版本检查和证书验证
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # 允许所有SSL/TLS版本，包括旧版本
        context.min_version = ssl.TLSVersion.TLSv1
        context.max_version = ssl.TLSVersion.TLSv1_3
        # 设置宽松的SSL选项
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1_1
        # 允许所有密码套件
        context.set_ciphers('ALL:!aNULL:!eNULL:!LOW:!EXPORT:!SSLv2')
        return context
    
    @staticmethod
    def send_request(method, url, headers=None, data=None, params=None, max_retries=3, retry_interval=5):
        """发送HTTP请求，支持重试机制
        
        Args:
            method: 请求方法，GET或POST
            url: 请求URL
            headers: 请求头
            data: 请求数据
            params: 请求参数
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            
        Returns:
            dict: 响应内容
        """
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0,  # 自定义重试机制
            pool_block=False
        ))
        
        # 创建自定义SSL上下文
        ssl_context = HTTPHelper.create_ssl_context()
        session.verify = False  # 禁用SSL验证
        session.ssl_context = ssl_context
        
        for retry in range(max_retries):
            try:
                logger.info(f"发送{method}请求到: {url}")
                if headers:
                    # 只记录关键请求头，避免记录完整请求头
                    logger.debug(f"请求头: {headers}")
                if data:
                    # 只记录数据存在性，避免记录完整数据
                    logger.debug(f"请求数据: 存在")
                if params:
                    logger.debug(f"请求参数: {params}")
                
                if method == 'GET':
                    resp = session.get(url, headers=headers, params=params, timeout=30)
                elif method == 'POST':
                    resp = session.post(url, headers=headers, data=data, params=params, timeout=30)
                else:
                    logger.error(f"不支持的请求方法: {method}")
                    return None
                
                logger.info(f"响应状态码: {resp.status_code}")
                if resp.status_code != 200:
                    # 只在响应失败时记录响应内容
                    logger.debug(f"响应内容: {resp.text}")
                
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except json.JSONDecodeError:
                        logger.error(f"响应内容不是有效的JSON格式: {resp.text}")
                        return {"success": 0, "msg": "响应内容不是有效的JSON格式", "data": None}
                else:
                    logger.error(f"请求失败，状态码: {resp.status_code}")
                    if retry < max_retries - 1:
                        logger.info(f"等待 {retry_interval} 秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        logger.error(f"多次尝试后仍失败，状态码: {resp.status_code}")
                        return {"success": 0, "msg": f"请求失败，状态码: {resp.status_code}", "data": None}
            
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {e}")
                if retry < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                    continue
                else:
                    logger.error(f"多次尝试后仍失败: {e}")
                    return {"success": 0, "msg": f"请求异常: {e}", "data": None}
        
        return {"success": 0, "msg": "请求超时", "data": None}

class VMManagementWorkflow:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = None
        self.selected_config = None
        self.hci_credentials = None
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"成功: 配置文件加载成功: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"错误: 加载配置文件失败: {e}")
            return False
    
    def validate_config(self):
        """验证配置完整性"""
        if not self.config:
            logger.error("错误: 配置未加载")
            return False
        
        # 验证HCI设备配置
        hci_device = self.config.get('hci_device', {})
        if not all([hci_device.get('ip'), hci_device.get('username'), hci_device.get('password')]):
            logger.error("错误: HCI设备登录信息不完整")
            return False
        
        # 验证目标虚拟机配置
        target_vm = self.config.get('target_vm', {})
        if not all([target_vm.get('name'), target_vm.get('snapshot')]):
            logger.error("错误: 目标虚拟机信息不完整")
            return False
        
        # 验证网络配置
        network_config = self.config.get('network_config', {})
        if not all([network_config.get('ip_address'), network_config.get('default_gateway')]):
            logger.error("错误: 网络配置不完整")
            return False
        
        # 验证KB包配置
        kb_packages = self.config.get('kb_packages', {})
        if not kb_packages.get('current'):
            logger.error("错误: 本次KB包信息未配置")
            return False
        
        # 验证客户配置
        customer_config = self.config.get('customer_config')
        if not customer_config:
            logger.error("错误: 客户配置信息未配置")
            return False
        
        # 验证登录凭证
        login_credentials = self.config.get('login_credentials', {})
        if not all([login_credentials.get('username'), login_credentials.get('password')]):
            logger.error("错误: 登录凭证信息不完整")
            return False
        
        logger.info("成功: 配置验证通过")
        return True
    
    def select_config(self):
        """根据关键词选择配置"""
        # 由于新的配置文件只包含一个目标虚拟机，直接使用配置
        self.selected_config = self.config
        logger.info("成功: 使用配置文件中的目标虚拟机")
        return True
    
    def get_hci_credentials(self):
        """获取HCI设备登录凭证"""
        try:
            hci_device = self.selected_config.get('hci_device', {})
            ip = hci_device.get('ip')
            username = hci_device.get('username')
            password = hci_device.get('password')
            http_port = hci_device.get('http_port', '443')
            
            logger.info(f"正在登录 HCI 设备 {ip}...")
            
            # 使用Playwright完成登录
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                
                # 获取公钥
                logger.info("正在获取公钥...")
                public_key_url = f"https://{ip}:{http_port}/vapi/json/public_key"
                resp = page.request.get(public_key_url, timeout=30000)
                
                if resp.status != 200:
                    logger.error(f"错误: 获取公钥失败，状态码: {resp.status}")
                    browser.close()
                    return False
                
                public_key_data = resp.json()
                public_key = public_key_data.get('data')
                
                if not public_key:
                    logger.error("错误: 响应中没有找到公钥")
                    browser.close()
                    return False
                
                logger.info("成功: 已获取公钥")
                
                # RSA加密密码
                logger.info("正在加密密码...")
                key = rsa.PublicKey(int(public_key, 16), int("10001", 16))
                password_temp = rsa.encrypt(bytes(password, encoding="utf-8"), key)
                password_rsa = str(binascii.b2a_hex(password_temp), encoding="utf-8")
                logger.info("成功: 密码加密完成")
                
                # 发送登录请求
                logger.info("正在登录...")
                login_url = f"https://{ip}:{http_port}/vapi/json/access/ticket"
                
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
                
                if resp.status != 200:
                    logger.error(f"错误: 登录失败，状态码: {resp.status}")
                    browser.close()
                    return False
                
                login_data = resp.json()
                csrf_token = login_data.get("data", {}).get("CSRFPreventionToken")
                ticket = login_data.get("data", {}).get("ticket")
                
                if not csrf_token or not ticket:
                    logger.error("错误: 响应中没有找到CSRFPreventionToken或ticket")
                    browser.close()
                    return False
                
                self.hci_credentials = {
                    "csrf_token": csrf_token,
                    "cookie": f"LoginAuthCookie={ticket}",
                    "ip": ip,
                    "http_port": http_port,
                    "username": username,
                    "password": password
                }
                
                browser.close()
                logger.info("成功: 成功获取HCI登录凭证")
                return True
                
        except Exception as e:
            logger.error(f"错误: 获取HCI登录凭证失败: {e}")
            traceback.print_exc()
            return False
    
    def get_clean_ip(self, ip_address_with_cidr):
        """从CIDR格式提取纯IP地址"""
        if '/' in ip_address_with_cidr:
            return ip_address_with_cidr.split('/')[0]
        return ip_address_with_cidr
    
    def get_vm_id(self, vm_name):
        """根据虚拟机名称获取虚拟机ID"""
        if not self.hci_credentials:
            logger.error("✗ HCI登录凭证未获取")
            return None
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            logger.info(f"正在查找虚拟机 {vm_name}...")
            
            # 尝试使用curl命令获取虚拟机列表
            import subprocess
            
            curl_command = f"""
curl ^"https://{ip}/vapi/json/cluster/vms?group_type=group&sort_type=&desc=1&scene=resources_used^" ^
-H ^"Accept: */*^" ^
-H ^"CSRFPreventionToken: {csrf_token}^" ^
-H ^"Cookie: {cookie}^" ^
-H ^"X-Requested-With: XMLHttpRequest^" ^
--insecure
"""
            
            # 执行curl命令
            process = subprocess.Popen(
                curl_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="E:\\1"
            )
            
            # 获取输出和错误
            stdout, stderr = process.communicate(timeout=60)  # 60秒超时
            
            if process.returncode == 0 and stdout:
                try:
                    # 解析JSON响应
                    response_data = json.loads(stdout)
                    
                    if response_data.get("success") == 1:
                        # 解析虚拟机列表（数据是分组的）
                        groups = response_data.get("data", [])
                        
                        # 在所有组中查找虚拟机
                        for group in groups:
                            vms = group.get("data", [])
                            for vm in vms:
                                if vm.get("name") == vm_name:
                                    vmid = vm.get("vmid")
                                    logger.info(f"✓ 找到虚拟机: {vm_name}, ID: {vmid}")
                                    return vmid
                except json.JSONDecodeError as e:
                    logger.error(f"解析响应JSON失败: {e}")
                    logger.error(f"响应内容: {stdout}")
            
            logger.error(f"✗ 未找到虚拟机: {vm_name}")
            return None
            
        except Exception as e:
            logger.error(f"✗ 获取虚拟机ID失败: {e}")
            traceback.print_exc()
            return None
    
    def get_vm_snapshots(self, vmid):
        """获取虚拟机快照列表"""
        if not self.hci_credentials:
            logger.error("✗ HCI登录凭证未获取")
            return None
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            logger.info(f"正在查询虚拟机 {vmid} 的快照列表...")
            
            # 尝试使用curl命令获取快照列表
            import subprocess
            
            curl_command = f"""
curl ^"https://{ip}/vapi/json/cluster/vm/{vmid}/snapshot^" ^
-H ^"Accept: */*^" ^
-H ^"CSRFPreventionToken: {csrf_token}^" ^
-H ^"Cookie: {cookie}^" ^
-H ^"X-Requested-With: XMLHttpRequest^" ^
--insecure
"""
            
            # 执行curl命令
            process = subprocess.Popen(
                curl_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="E:\\1"
            )
            
            # 获取输出和错误
            stdout, stderr = process.communicate(timeout=60)  # 60秒超时
            
            if process.returncode == 0 and stdout:
                try:
                    # 解析JSON响应
                    response_data = json.loads(stdout)
                    
                    if response_data.get("success") == 1:
                        snapshots = response_data.get("data", [])
                        
                        if snapshots:
                            logger.info(f"✓ 获取到 {len(snapshots)} 个快照")
                            for snapshot in snapshots:
                                logger.info(f"  - {snapshot.get('name')} (ID: {snapshot.get('snapid')})")
                            return snapshots
                        else:
                            logger.error(f"✗ 虚拟机 {vmid} 没有任何快照")
                    else:
                        logger.error(f"✗ 响应success字段不为1: {response_data.get('success')}")
                except json.JSONDecodeError as e:
                    logger.error(f"解析响应JSON失败: {e}")
                    logger.error(f"响应内容: {stdout}")
            else:
                logger.error(f"✗ 获取快照列表失败，退出码: {process.returncode}")
                if stderr:
                    logger.error(f"错误信息: {stderr}")
            
            return None
            
        except Exception as e:
            logger.error(f"✗ 获取快照列表失败: {e}")
            traceback.print_exc()
            return None
    
    def recover_vm_snapshot(self, vmid, snapshot_id):
        """恢复虚拟机快照"""
        if not self.hci_credentials:
            logger.error("✗ HCI登录凭证未获取")
            return False
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            logger.info(f"正在恢复虚拟机 {vmid} 到快照 {snapshot_id}...")
            
            # 使用curl命令恢复虚拟机快照
            # 构建完整的Cookie字符串
            timestamp = int(time.time() * 1000)
            full_cookie = f"cluster=single_cluster; needAnalytic=need_analytic; vnc-keyboard=en-us; {cookie}; global.timeout.task={timestamp}"
            
            # 构建curl命令（参考vm_recover.py的成功实现，添加rtype和backup参数）
            curl_command = f"curl -k -X POST \"https://{ip}/vapi/extjs/cluster/vm/{vmid}/recovery\" -H \"Accept: */*\" -H \"CSRFPreventionToken: {csrf_token}\" -H \"Cookie: {full_cookie}\" -H \"Content-Type: application/x-www-form-urlencoded; charset=UTF-8\" -H \"X-Requested-With: XMLHttpRequest\" --data-urlencode \"rtype=raw\" --data-urlencode \"snapid={snapshot_id}\" --data-urlencode \"backup=0\""
            
            # 执行curl命令
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            # 解析响应
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                    
                    if response_data.get("success") == 1:
                        logger.info(f"✓ 虚拟机 {vmid} 快照恢复请求已发送成功")
                        
                        # 等待10秒后再返回，给快照恢复一些时间
                        logger.info("等待10秒，让快照恢复过程进行中...")
                        time.sleep(10)
                        return True
                    else:
                        logger.error(f"✗ 虚拟机 {vmid} 快照恢复失败: {response_data.get('msg') if response_data else '请求失败'}")
                        logger.error(f"响应: {result.stdout[:200]}")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"✗ 解析响应JSON失败: {e}")
                    logger.error(f"响应内容: {result.stdout[:200]}")
                    return False
            else:
                logger.error(f"✗ 恢复虚拟机快照失败: 响应为空")
                if result.stderr:
                    logger.error(f"错误信息: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"✗ 恢复虚拟机快照失败: {e}")
            traceback.print_exc()
            return False
        
    def start_vm(self, vmid):
        """启动虚拟机"""
        if not self.hci_credentials:
            logger.error("✗ HCI登录凭证未获取")
            return False
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            logger.info(f"正在启动虚拟机 {vmid}...")
            
            # 构建完整的Cookie字符串（参考完整的curl请求）
            timestamp = int(time.time() * 1000)
            full_cookie = f"cluster=single_cluster; needAnalytic=need_analytic; vnc-keyboard=en-us; {cookie}; global.timeout.task={timestamp}"
            
            # 使用单行curl命令（避免Windows CMD的多行引号问题）
            url = f"https://{ip}/vapi/extjs/cluster/vm/{vmid}/status/start"
            curl_command = [
                'curl',
                '-k',
                '-X', 'POST',
                '-H', 'Accept: */*',
                '-H', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                f'-H', f'CSRFPreventionToken: {csrf_token}',
                '-H', 'Connection: keep-alive',
                '-H', 'Content-Length: 0',
                '-b', full_cookie,
                f'-H', f'Origin: https://{ip}',
                f'-H', f'Referer: https://{ip}/',
                '-H', 'Sec-Fetch-Dest: empty',
                '-H', 'Sec-Fetch-Mode: cors',
                '-H', 'Sec-Fetch-Site: same-origin',
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0',
                '-H', 'X-Requested-With: XMLHttpRequest',
                '-H', 'sec-ch-ua: "Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
                '-H', 'sec-ch-ua-mobile: ?0',
                '-H', 'sec-ch-ua-platform: "Windows"',
                url
            ]
            
            # 执行curl命令（使用列表参数避免shell解析问题）
            result = subprocess.run(curl_command, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            # 打印调试信息
            logger.info(f"启动命令退出码: {result.returncode}")
            logger.info(f"启动响应内容: {result.stdout}")
            if result.stderr:
                logger.error(f"启动错误信息: {result.stderr}")
            
            # 解析响应
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                    
                    if response_data.get("success") == 1:
                        logger.info(f"✓ 虚拟机 {vmid} 启动请求已发送成功")
                        return True
                    else:
                        logger.error(f"✗ 虚拟机 {vmid} 启动失败: {response_data.get('msg') if response_data else '请求失败'}")
                        logger.error(f"响应: {result.stdout[:200]}")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"✗ 解析响应JSON失败: {e}")
                    logger.error(f"响应内容: {result.stdout[:200]}")
                    return False
            else:
                logger.error(f"✗ 启动虚拟机失败: 响应为空")
                if result.stderr:
                    logger.error(f"错误信息: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"✗ 启动虚拟机失败: {e}")
            traceback.print_exc()
            return False
    def modify_vm_ip(self, vm_name, network_config):
        """修改虚拟机IP地址（参考vm.py的run方法）"""
        logger.info(f"正在修改虚拟机 {vm_name} 的IP地址...")
        
        try:
            # 获取HCI设备配置
            hci_ip = self.hci_credentials.get('ip')
            hci_username = self.hci_credentials.get('username')
            hci_password = self.hci_credentials.get('password')
            
            # 获取虚拟机IP地址和信息
            device_ip_with_cidr = network_config.get('ip_address')
            device_ip = self.get_clean_ip(device_ip_with_cidr)
            vmid = self.get_vm_id(vm_name)
            
            if not vmid:
                logger.error("✗ 无法获取虚拟机ID")
                return False
            
            # URL编码虚拟机名称
            import urllib.parse
            encoded_vm_name = urllib.parse.quote(vm_name)
            
            # 配置IP和网关
            ip_address = device_ip_with_cidr  # 保持完整的CIDR格式（包含子网掩码后缀）
            default_gateway = network_config.get('default_gateway')
            
            # 获取设备登录凭证
            login_username = self.config.get('login_credentials', {}).get('username')
            login_password = self.config.get('login_credentials', {}).get('password')
            
            # 创建浏览器实例
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                
                # 访问HCI平台登录页
                page.goto(f"https://{hci_ip}/#/mod-computer/index?id=&name=&stype=&status=&active_grp_path=&group_type=&tab=hci")
                
                # 输入用户名
                page.get_by_role("textbox", name="请输入您的用户名").click(timeout=10000)
                page.get_by_role("textbox", name="请输入您的用户名").fill(hci_username)
                
                # 输入密码
                page.get_by_role("textbox", name="请输入您的密码").click()
                page.get_by_role("textbox", name="请输入您的密码").fill(hci_password)
                
                # 点击登录按钮
                page.get_by_role("button", name="立即登录").click()
                
                # 停5秒
                logger.info("等待5秒...")
                page.wait_for_timeout(5000)
                logger.info("✓ 停5秒完成")
                
                # 跳转到虚拟机控制台
                page.goto(f"https://{hci_ip}/#/mod-console/index?n-hfs&vmid={vmid}&vmname={encoded_vm_name}")
                
                # 跳转完成后等待7秒
                logger.info("跳转完成后等待7秒...")
                page.wait_for_timeout(7000)
                logger.info("✓ 等待7秒完成")
                
                # 点击屏幕中央并按Enter
                page.mouse.click(page.viewport_size["width"] // 2, page.viewport_size["height"] // 2)
                page.wait_for_timeout(2000)
                
                # 逐字符输入用户名
                for char in "aadmin":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)
                
                # 逐字符输入密码
                password = login_password + "sunwns"
                for char in password:
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.keyboard.press("Enter")
                page.wait_for_timeout(1000)
                page.wait_for_timeout(5000)
                
                # 使用OpenCV检测二维码
                logger.info("检测二维码...")
                max_attempts = 3
                qr_detected = False
                qrcode_data = None
                
                for attempt in range(max_attempts):
                    logger.info(f"第 {attempt + 1} 次检测...")
                    screenshot_bytes = page.screenshot()
                    
                    # 保存截图到文件
                    with open(f"qrcode_screenshot_{attempt + 1}.png", "wb") as f:
                        f.write(screenshot_bytes)
                    logger.info(f"截图已保存为 qrcode_screenshot_{attempt + 1}.png")
                    
                    # 转换为OpenCV格式
                    img_array = np.frombuffer(screenshot_bytes, np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    # 方法1：基于二维码特征的简单检测
                    logger.info("方法1：基于二维码特征的简单检测...")
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # 使用边缘检测
                    edges = cv2.Canny(gray, 50, 150)
                    
                    # 查找轮廓
                    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # 统计正方形轮廓的数量
                    square_count = 0
                    for contour in contours:
                        epsilon = 0.04 * cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        
                        if len(approx) == 4:
                            x, y, w, h = cv2.boundingRect(approx)
                            aspect_ratio = float(w) / h
                            if 0.9 < aspect_ratio < 1.1:
                                square_count += 1
                                cv2.drawContours(img, [approx], 0, (0, 255, 0), 2)
                    
                    # 保存带有轮廓的图像
                    cv2.imwrite(f"qrcode_contours_{attempt + 1}.png", img)
                    logger.info(f"带有轮廓的图像已保存为 qrcode_contours_{attempt + 1}.png")
                    
                    if square_count >= 3:
                        logger.info(f"检测到 {square_count} 个正方形轮廓，可能存在二维码，停止执行")
                        qr_detected = True
                        break
                    
                    # 方法2：简单的亮度分析
                    logger.info("方法2：简单的亮度分析...")
                    h, w = gray.shape
                    center_region = gray[h//3:2*h//3, w//3:2*w//3]
                    std_dev = np.std(center_region)
                    logger.info(f"中央区域亮度标准差: {std_dev}")
                    
                    if std_dev > 80:
                        logger.info(f"中央区域对比度高（标准差: {std_dev}），可能存在二维码，停止执行")
                        qr_detected = True
                        break
                    
                    logger.info(f"第 {attempt + 1} 次检测未找到二维码")
                    page.wait_for_timeout(3000)
                
                if qr_detected:
                    logger.info("检测到二维码，准备截取 noVNC_Wrapper 元素并复制到剪贴板...")
                    
                    try:
                        import win32clipboard
                        from io import BytesIO
                        from PIL import Image as PILImage
                        
                        # 定位并截取 noVNC_Wrapper 元素
                        logger.info("正在截取 noVNC_Wrapper 元素...")
                        vnc_wrapper = page.locator('div.noVNC_Wrapper')
                        screenshot_bytes = vnc_wrapper.screenshot()
                        
                        # 将字节转换为PIL Image
                        img = PILImage.open(BytesIO(screenshot_bytes))
                        
                        logger.info("正在处理图片...")
                        output = BytesIO()
                        img.convert("RGB").save(output, "BMP")
                        data = output.getvalue()[14:]
                        output.close()
                        
                        logger.info("正在复制到剪贴板...")
                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                        win32clipboard.CloseClipboard()
                        
                        logger.info("✅ noVNC_Wrapper 元素截图已复制到剪贴板！")
                        success = True
                        if success:
                            logger.info("操作完成：已截取 noVNC_Wrapper 元素并复制到剪贴板")
                            
                            try:
                                new_page = context.new_page()
                                new_page.goto("http://200.200.92.147/hyc/qrcode_get.html", timeout=60000)
                                new_page.wait_for_load_state("networkidle", timeout=60000)
                                logger.info("网站加载完毕")
                                new_page.wait_for_timeout(2000)
                                
                                new_page.mouse.click(new_page.viewport_size["width"] // 2, new_page.viewport_size["height"] // 2)
                                logger.info("已点击页面，确保获得焦点")
                                
                                new_page.keyboard.down("Control")
                                new_page.keyboard.press("V")
                                new_page.keyboard.up("Control")
                                logger.info("图片已粘贴到页面")
                                new_page.wait_for_timeout(5000)
                                
                                logger.info("从页面获取验证码...")
                                try:
                                    # 等待验证码元素出现
                                    new_page.wait_for_selector('xpath=/html/body/div/div[2]/p', state='visible', timeout=10000)
                                    
                                    # 获取验证码文本
                                    verification_code_element = new_page.locator('xpath=/html/body/div/div[2]/p')
                                    qrcode_data = verification_code_element.inner_text()
                                    logger.info(f"提取到的验证码: {qrcode_data}")
                                except Exception as get_code_error:
                                    logger.error(f"获取验证码失败: {get_code_error}")
                                    qrcode_data = ""
                                
                                try:
                                    new_page.close()
                                    logger.info("已关闭qrcode_get.html页面")
                                except Exception as close_error:
                                    logger.error(f"关闭页面失败: {close_error}")
                            except Exception as e:
                                logger.error(f"打开网站失败: {e}")
                        else:
                            logger.error("操作失败：截图并复制到剪贴板失败")
                    except Exception as e:
                        logger.error(f"使用PyAutoGUI失败: {e}")
                        traceback.print_exc()
                else:
                    logger.info("多次检测后仍未检测到二维码，继续执行配置")
                
                # 继续执行配置命令
                page.mouse.click(page.viewport_size["width"] // 2, page.viewport_size["height"] // 2)
                input_value = qrcode_data if qrcode_data else ""
                logger.info(f"使用输入值: {input_value}")
                
                for char in input_value:
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)
                
                for char in "cli":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                
                for char in "config terminal":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                
                for char in "in eth0":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                
                # 配置IP地址
                for char in f"ip addr {ip_address}":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                
                for char in "exit":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                
                # 配置默认网关
                for char in f"ip route 0.0.0.0/0 {default_gateway}":
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                page.wait_for_timeout(2000)
                page.keyboard.press("Enter")
                
                # 等待网络配置生效
                logger.info("等待网络配置生效...")
                page.wait_for_timeout(10000)
                
                # 访问设备页面
                logger.info(f"正在访问设备页面: https://{device_ip}")
                page.goto(f"https://{device_ip}")
                
                # 逐字输入用户名
                page.locator("#login_user").click()
                for char in login_username:
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                
                # 逐字输入密码
                page.locator("#login_password").click()
                for char in login_password:
                    page.keyboard.type(char)
                    page.wait_for_timeout(50)
                
                page.wait_for_timeout(2000)
                page.get_by_role("checkbox", name="我已认真阅读并同意").check()
                page.get_by_text("登录", exact=True).click()
                

                logger.info("登录成功")
                page.wait_for_timeout(2000)

                # 配置端口
                logger.info(f"配置端口: {ip_address}")
                page.goto(f"https://{device_ip}/WLAN/index.php#/system/Port")
                time.sleep(3)
                
                page.locator("span.sim-link[actionname='modify']").filter(has_text="eth0(管理口)").click()
                time.sleep(2)
                
                page.get_by_role("textbox", name="IP地址：").fill(f"{ip_address}")
                page.get_by_role("button", name="确定").click()
                time.sleep(2)
                
                # 配置静态路由
                logger.info(f"配置静态路由: 下一跳 {default_gateway}")
                page.goto(f"https://{device_ip}/WLAN/index.php#/system/StaticRoute")
                time.sleep(3)
                
                page.get_by_role("button", name=" 新增").click()
                page.get_by_role("link", name="新增IPv4静态路由").click()
                time.sleep(2)
                

                page.get_by_role("textbox", name="目标地址：").fill("0.0.0.0")

                page.get_by_role("textbox", name="网络掩码：").fill("0.0.0.0")
      
                page.get_by_role("textbox", name="下一跳地址：").fill(default_gateway)
                page.get_by_role("button", name="提交").click()
                time.sleep(2)
                
                # 关闭浏览器
                context.close()
                browser.close()
                
                logger.info(f"✓ 虚拟机 {vm_name} IP地址修改成功")
                return True
            
        except Exception as e:
            logger.error(f"✗ 修改虚拟机 {vm_name} IP地址失败: {e}")
            traceback.print_exc()
            return False
        
    def is_debug_shell_ready(self, page):
        """使用模板匹配判断是否进入 Debug Shell 界面"""
        try:
            # 1. 定位 VNC 控制台元素
            vnc_wrapper = page.locator('.noVNC_Wrapper')
            
            # 2. 截取 VNC 控制台元素
            screenshot_bytes = vnc_wrapper.screenshot()
            
            # 3. 将字节转换为 PIL Image
            from PIL import Image
            from io import BytesIO
            screenshot = Image.open(BytesIO(screenshot_bytes))
            
            # 4. 读取模板图片
            template_path = 'pht/vnc_screenshot_20260126_142250.png'
            template = cv2.imread(template_path)
            
            if template is None:
                logger.error(f"✗ 无法读取模板图片: {template_path}")
                return False
            
            # 6. 将当前截图转换为OpenCV格式
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 7. 执行模板匹配
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 8. 设置匹配阈值
            threshold = 0.95  # 匹配度阈值，可以根据实际情况调整
            
            logger.info(f"模板匹配度: {max_val:.4f} (阈值: {threshold})")
            
            is_ready = max_val >= threshold
            
            if is_ready:
                logger.info("✓ 模板匹配检测到已成功进入 Debug Shell 界面！")
            else:
                logger.info("✗ 模板匹配未检测到目标界面")
            
            return is_ready
            
        except Exception as e:
            logger.error(f"✗ 模板匹配检测失败: {e}")
            traceback.print_exc()
            return False
    
    def check_vm_reboot_completed(self, vm_name, network_config, vmid):
        """检测虚拟机是否重启完毕（独立创建浏览器）"""
        logger.info(f"正在检测虚拟机 {vm_name} 是否重启完毕...")
        
        # 获取HCI设备IP和登录信息
        hci_ip = self.hci_credentials.get('ip')
        hci_username = self.hci_credentials.get('username')
        hci_password = self.hci_credentials.get('password')
        
        # URL编码虚拟机名称
        import urllib.parse
        encoded_vm_name = urllib.parse.quote(vm_name)
        
        # 构建URL
        login_url = f"https://{hci_ip}/#/mod-computer/index?id=&name=&stype=&status=&active_grp_path=&group_type=&tab=hci"
        console_url = f"https://{hci_ip}/#/mod-console/index?n-hfs&vmid={vmid}&vmname={encoded_vm_name}"
        
        success_count = 0
        max_attempts = 240  # 最多尝试240次，每次5秒，总共20分
        check_interval = 5  # 每5秒检查一次
        required_successes = 3  # 连续3次成功才算重启完成
        
        # 创建独立的浏览器实例用于检测
        browser = None
        context = None
        page = None
        
        try:
            p = sync_playwright().start()
            browser = p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # 步骤1: 登录并跳转到虚拟机控制台
            # 访问登录页面
            logger.info(f"正在访问超融合管理平台: {login_url}")
            page.goto(login_url, timeout=30000)
            
            # 输入用户名
            logger.info("正在输入用户名...")
            page.get_by_role("textbox", name="请输入您的用户名").click(timeout=10000)
            page.get_by_role("textbox", name="请输入您的用户名").fill(hci_username)
            
            # 输入密码
            logger.info("正在输入密码...")
            page.get_by_role("textbox", name="请输入您的密码").click()
            page.get_by_role("textbox", name="请输入您的密码").fill(hci_password)
            
            # 点击登录按钮
            logger.info("正在登录...")
            page.get_by_role("button", name="立即登录").click()
            
            # 等待登录完成
            logger.info("等待5秒...")
            page.wait_for_timeout(5000)
            logger.info("✓ 登录完成")
            
            # 跳转到虚拟机控制台
            logger.info(f"正在跳转到虚拟机控制台: {console_url}")
            page.goto(console_url, timeout=30000)
            logger.info("✓ 已跳转到虚拟机控制台页面")
            
            # 等待VNC控制台iframe和关键元素加载完成
            logger.info("正在等待VNC控制台加载...")
            try:
                # 等待 noVNC_Wrapper 元素出现（最多等待15秒）
                page.wait_for_selector('.noVNC_Wrapper', timeout=15000)
                logger.info("✓ VNC控制台元素已加载")
            except Exception as e:
                logger.warning(f"⚠ 等待VNC控制台元素超时: {e}，继续尝试...")
            
            # 额外等待5秒确保VNC画面完全渲染
            page.wait_for_timeout(5000)
            logger.info("✓ 控制台页面加载完成，开始检测...")
            
            # 删除补丁服务提示元素（如果存在）
            try:
                patch_alert = page.locator('.v-tip.patch-alert-tip')
                if patch_alert.count() > 0:
                    logger.info("检测到补丁服务提示元素，正在删除...")
                    page.evaluate('''
                        const patchAlert = document.querySelector('.v-tip.patch-alert-tip');
                        if (patchAlert) {
                            patchAlert.remove();
                        }
                    ''')
                    logger.info("✓ 补丁服务提示元素已删除")
                else:
                    logger.info("未检测到补丁服务提示元素")
            except Exception as e:
                logger.warning(f"删除补丁提示元素时出错（可忽略）: {e}")
            
            # 删除客户回访弹窗（如果存在）
            try:
                # 点击"暂不参与"按钮关闭弹窗
                delay_button = page.locator('button[action="delay"]').filter(has_text="暂不参与")
                if delay_button.count() > 0:
                    logger.info("检测到客户回访弹窗，点击'暂不参与'...")
                    delay_button.first.click()
                    logger.info("✓ 已点击'暂不参与'，客户回访弹窗已关闭")
                    time.sleep(1)  # 等待弹窗关闭动画完成
                else:
                    logger.info("未检测到客户回访弹窗")
            except Exception as e:
                logger.warning(f"关闭客户回访弹窗时出错（可忽略）: {e}")
                # 如果点击失败，尝试直接删除元素
                try:
                    page.evaluate('''
                        const feedbackWindows = document.querySelectorAll('.sfis-window');
                        feedbackWindows.forEach(window => {
                            const title = window.querySelector('.title');
                            if (title && title.textContent.includes('客户回访')) {
                                window.remove();
                            }
                        });
                    ''')
                    logger.info("✓ 客户回访弹窗已手动删除")
                except:
                    pass
            
            # 步骤2: 循环检测（只做模板匹配判断）
            for attempt in range(max_attempts):
                access_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                try:
                    # 使用模板匹配方式判断页面（传入page对象用于截取元素）
                    if self.is_debug_shell_ready(page):
                        success_count += 1
                        logger.info(f"✓ [{access_time}] 模板匹配检测到重启完成标志，连续成功次数: {success_count}/{required_successes}")
                    else:
                        success_count = 0
                        logger.warning(f"✗ [{access_time}] 模板匹配未检测到重启完成标志，第 {attempt+1}/{max_attempts} 次尝试")
                    
                    # 如果连续3次成功，关闭浏览器并返回True
                    if success_count >= required_successes:
                        logger.info(f"✓ 虚拟机 {vm_name} 重启完成")
                        browser.close()
                        p.stop()
                        return True
                    
                    # 等待下次检查
                    time.sleep(check_interval)
                    
                except Exception as match_error:
                    success_count = 0
                    logger.error(f"✗ [{access_time}] 模板匹配检测出错: {match_error}，第 {attempt+1}/{max_attempts} 次尝试")
                    time.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"✗ 检测过程中出错: {e}")
            traceback.print_exc()
            if browser:
                browser.close()
            if 'p' in locals():
                p.stop()
            return False
        
        # 超时后关闭浏览器
        if browser:
            browser.close()
        if 'p' in locals():
            p.stop()
        logger.error(f"✗ 虚拟机 {vm_name} 重启检测超时")
        return False
        
    def upgrade_kb_packages(self, vm_name, network_config, kb_packages):
        """升级KB包（完整实现KB.py的下载和升级功能）"""
        logger.info(f"正在为虚拟机 {vm_name} 升级KB包...")
        
        device_ip = self.get_clean_ip(network_config.get('ip_address'))
        login_username = self.config.get('login_credentials', {}).get('username')
        login_password = self.config.get('login_credentials', {}).get('password')
        kb_number = kb_packages.get('current')
        
        kb_number = kb_number.strip()
        download_dir = os.path.join('F:\\KB', kb_number)
        os.makedirs(download_dir, exist_ok=True)
        
        logger.info(f"设备IP: {device_ip}")
        logger.info(f"KB编号: {kb_number}")
        logger.info(f"下载目录: {download_dir}\n")
        
        kb_sign_file = None  # 记录KB SIGN文件路径
        
        with sync_playwright() as p:
            # ========== 第一部分：下载KB包 ==========
            browser = p.chromium.launch(
                headless=False,
                args=['--ignore-certificate-errors', '--disable-web-security']
            )
            
            # 创建下载用的context
            download_context = browser.new_context(accept_downloads=True)
            download_page = download_context.new_page()
            download_page.set_default_timeout(30000)
            
            try:
                # 访问KB下载页面
                logger.info("正在访问KB下载页面...")
                download_page.goto('http://10.156.99.96/kb.php#', wait_until='domcontentloaded')
                download_page.wait_for_selector('#ext-comp-1016', state='visible')
                
                kb_input = download_page.locator('#ext-comp-1016')
                kb_input.fill(kb_number)
                kb_input.press('Enter')
                time.sleep(10)
                
                # 下载KB SIGN和KB两个文件
                logger.info('正在下载KB文件...\n')
                
                for file_type in ['下载KB SIGN', '下载KB']:
                    try:
                        # 设置下载处理器
                        with download_page.expect_download(timeout=30000) as download_info:
                            download_page.get_by_text(file_type, exact=file_type == '下载KB').click(timeout=10000)
                        
                        download = download_info.value
                        save_path = os.path.join(download_dir, download.suggested_filename)
                        download.save_as(save_path)
                        logger.info(f'✓ {file_type}: {download.suggested_filename}')
                        
                        # 记录KB SIGN文件路径
                        if file_type == '下载KB SIGN':
                            kb_sign_file = save_path
                        
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f'❌ {file_type} 下载失败: {e}')
                
                logger.info(f'\n✓ 下载完成！文件已保存到 {download_dir}')
                
            except Exception as download_error:
                logger.error(f'❌ KB下载失败: {download_error}')
                download_context.close()
                browser.close()
                return False
            
            # 关闭下载页面的context（清理状态，避免污染登录页面）
            download_context.close()
            logger.info('已关闭下载页面的浏览器上下文')
            
            # ========== 第二部分：升级KB包 ==========
            if kb_sign_file:
                logger.info('\n' + '=' * 50)
                logger.info('开始执行KB更新操作...\n')
                
                # 创建全新的context和page用于登录和更新（避免状态污染）
                update_context = browser.new_context(ignore_https_errors=True)
                update_page = update_context.new_page()
                update_page.set_default_timeout(30000)
                logger.info('已创建新的浏览器上下文')
                
                try:
                    # 切换到更新页面（添加重试机制）
                    max_retries = 5
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            logger.info(f'尝试访问设备 {device_ip} (第 {retry_count + 1}/{max_retries} 次)...')
                            update_page.goto(f'https://{device_ip}', timeout=30000)
                            time.sleep(5)
                            logger.info(f'✓ 成功访问设备 {device_ip}')
                            break
                        except Exception as goto_error:
                            retry_count += 1
                            if retry_count < max_retries:
                                logger.warning(f'⚠ 访问设备失败: {goto_error}')
                                wait_time = retry_count * 5  # 递增等待时间：5s, 10s, 15s, 20s
                                logger.info(f'等待 {wait_time} 秒后重试...')
                                time.sleep(wait_time)
                            else:
                                raise Exception(f'访问设备 {device_ip} 失败，已重试 {max_retries} 次')
                    
                    # 处理证书警告（如果存在）
                    try:
                        update_page.get_by_role('button', name='高级').click(timeout=3000)
                        update_page.get_by_role('link', name=f'继续前往{device_ip}（不安全）').click(timeout=3000)
                        time.sleep(2)
                    except Exception:
                        # 无证书警告，继续
                        pass
                    logger.info("无证书警告或已处理，继续...")
                    
                    # 输入登录信息
                    logger.info("正在输入账号密码...")
                    update_page.wait_for_selector('#login_user', state='visible', timeout=10000)
                    login_user = update_page.locator('#login_user')
                    login_user.click()
                    login_user.fill('')
                    
                    # 逐字输入用户名
                    for char in login_username:
                        update_page.keyboard.type(char)
                        update_page.wait_for_timeout(50)
                    logger.info('账号已输入')
                    
                    update_page.wait_for_selector('#login_password', state='visible', timeout=10000)
                    login_password_loc = update_page.locator('#login_password')
                    login_password_loc.click()
                    login_password_loc.fill('')
                    
                    # 逐字输入密码
                    for char in login_password:
                        update_page.keyboard.type(char)
                        update_page.wait_for_timeout(50)
                    logger.info(f'密码已输入')
                    
                    # 勾选协议并登录
                    update_page.get_by_role('checkbox', name='我已认真阅读并同意').check()
                    logger.info('已勾选同意条款')
                    
                    update_page.get_by_text('登录', exact=True).click()
                    logger.info('已点击登录按钮，等待页面加载...')
                    
                    # 额外等待2秒
                    time.sleep(8)
              
                    # 跳转到固件升级页面
                    logger.info('正在跳转到升级页面...')
                    update_page.goto(f'https://{device_ip}/WLAN/index.php#/maintain/DeviceUpdate',
                             wait_until='domcontentloaded',
                             timeout=30000)
                    logger.info('✓ 已跳转到升级页面')
                    
                    # 等待升级页面加载
                    time.sleep(5)
                    logger.info('✓ 升级页面已加载')
                    
                    # 勾选"补丁包升级"单选框
                    logger.info('正在勾选"补丁包升级"...')
                    update_page.get_by_role('radio', name='补丁包升级').check()
                    logger.info('✓ 已勾选"补丁包升级"')
                    time.sleep(3)

                    
                    # 上传KB SIGN文件
                    logger.info('正在上传补丁包...')
                    file_input = update_page.locator('input[type="file"]').first
                    if file_input.is_visible():
                        file_input.set_input_files(kb_sign_file)
                        logger.info(f'✓ 已上传补丁包: {os.path.basename(kb_sign_file)}')
                        time.sleep(5)  # 等待上传完成
                    else:
                        logger.error('❌ 未找到文件上传输入框')
                        browser.close()
                        return False
                    
                    # 点击"开始升级"按钮
                    logger.info('正在点击"开始升级"按钮...')
                    update_page.get_by_role('button', name='开始升级').click()
                    logger.info('✓ 已点击"开始升级"按钮')
                    time.sleep(3)
                    
                    # 点击"确定"按钮
                    logger.info('正在点击"确定"按钮...')
                    # 1. 先定位包含"确认"文本的弹窗容器（缩小上下文，避免匹配其他按钮）
                    dialog_container = update_page.locator("div", has_text="确认")
                    # 2. 在弹窗容器内定位"确定"按钮并点击（优先匹配带 x-btn-text 类的按钮，更精准）
                    dialog_container.locator(".x-btn-text", has_text="确定").click()
                    logger.info('✓ 已点击"确定"按钮')
                    
                    # 停20秒确认更新
                    logger.info('等待20秒确认更新...')
                    time.sleep(20)
                    
                    # 等待页面自动刷新
                    logger.info('等待页面自动刷新...')
                    update_page.wait_for_load_state('networkidle', timeout=30000)
                    logger.info('✓ 页面已自动刷新完成')
                
                    logger.info(f'\n✓ 虚拟机 {vm_name} KB包升级成功！')
                    logger.info('='*50)
         
                except Exception as update_error:
                    logger.error(f"✗ KB更新失败: {update_error}")
                    traceback.print_exc()
                    update_context.close()
                    return False
                finally:
                    # 关闭更新用的context
                    update_context.close()
                    logger.info('已关闭更新操作的浏览器上下文')
            else:
                logger.error('❌ 未找到KB SIGN文件，跳过更新操作')
                browser.close()
                return False
        
        # with sync_playwright() 会自动关闭browser
        return True
    
    def run_workflow(self):
        """运行完整的虚拟机管理工作流"""
        logger.info("="*50)
        logger.info("开始执行虚拟机管理工作流")
        logger.info("="*50)
        
        try:
            # 1. 加载配置
            if not self.load_config():
                return False
            
            # 2. 验证配置
            if not self.validate_config():
                return False
            
            # 3. 选择配置
            if not self.select_config():
                return False
            
            # 4. 获取HCI登录凭证
            if not self.get_hci_credentials():
                return False
            
            # 5. 获取目标虚拟机信息
            target_vm = self.selected_config.get('target_vm', {})
            vm_name = target_vm.get('name')
            snapshot_name = target_vm.get('snapshot')
            
            # 6. 获取虚拟机ID
            vmid = self.get_vm_id(vm_name)
            if not vmid:
                return False
            
            # 7. 获取快照列表
            snapshots = self.get_vm_snapshots(vmid)
            if not snapshots:
                return False
            
            # 8. 查找指定快照ID
            snapshot_id = None
            for snapshot in snapshots:
                if snapshot.get('name') == snapshot_name:
                    snapshot_id = snapshot.get('snapid')
                    break
            
            if not snapshot_id:
                logger.error(f"✗ 未找到快照: {snapshot_name}")
                return False
            
            # 9. 恢复虚拟机快照
            if not self.recover_vm_snapshot(vmid, snapshot_id):
                return False
            
            # 10. 等待10秒后启动虚拟机
            logger.info("等待10秒后启动虚拟机...")
            time.sleep(10)
            
            # 11. 启动虚拟机
            if not self.start_vm(vmid):
                return False
            
            # 12. 检测虚拟机是否重启完毕
            network_config = self.config.get('network_config', {})
            if not self.check_vm_reboot_completed(vm_name, network_config, vmid):
                return False
            
            # 13. 修改虚拟机IP地址（独立创建浏览器）
            if not self.modify_vm_ip(vm_name, network_config):
                return False
            
            #14. 恢复客户配置
            logger.info("正在恢复客户配置...")
            customer_config = self.config.get('customer_config')
            
            # 处理两种情况：customer_config可能是字符串或包含file_path的对象
            if isinstance(customer_config, dict):
                config_file_path = customer_config.get('file_path')
            else:
                config_file_path = customer_config
            
            if config_file_path:
                with sync_playwright() as p:
                    peizhi.run(
                        p,
                        config_file_path=config_file_path,
                        device_ip=self.get_clean_ip(network_config.get('ip_address')),
                        login_username=self.config.get('login_credentials', {}).get('username'),
                        login_password=self.config.get('login_credentials', {}).get('password')
                    )
                logger.info("成功: 客户配置恢复完成")
            else:
                logger.error("错误: 客户配置文件路径未配置")
                return False
            
            # 16. 检查虚拟机是否重启完毕
            logger.info("正在检测虚拟机重启状态...")
            if not self.check_vm_reboot_completed(vm_name, network_config, vmid):
                logger.error("错误: 虚拟机重启检测失败")
                return False
            logger.info("成功: 虚拟机重启检测完成")

             # 13. 修改虚拟机IP地址（独立创建浏览器）
            if not self.modify_vm_ip(vm_name, network_config):
                return False
            
            # 17. 升级KB包
            kb_packages = self.config.get('kb_packages', {})
            if not self.upgrade_kb_packages(vm_name, network_config, kb_packages):
                return False
            
            logger.info("="*50)
            logger.info("虚拟机管理工作流执行完成")
            logger.info("="*50)
            return True
            
        except Exception as e:
            logger.error(f"错误: 工作流执行失败: {e}")
            traceback.print_exc()
            return False
        
    def get_vm_snapshots(self, vmid):
        """获取虚拟机快照列表"""
        if not self.hci_credentials:
            logger.error("错误: HCI登录凭证未获取")
            return None
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            logger.info(f"正在查询虚拟机 {vmid} 的快照列表...")
            
            # 使用curl命令获取快照列表
            curl_command = f"curl -k \"https://{ip}/vapi/extjs/cluster/vm/{vmid}/snapshot\" -H \"Accept: */*\" -H \"CSRFPreventionToken: {csrf_token}\" -H \"Cookie: {cookie}\" -H \"X-Requested-With: XMLHttpRequest\""
            
            # 执行curl命令
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            # 解析响应
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                    
                    if response_data.get("success") == 1:
                        snapshots = response_data.get("data", [])
                        
                        if snapshots:
                            logger.info(f"成功: 获取到 {len(snapshots)} 个快照")
                            for snapshot in snapshots:
                                logger.info(f"  - {snapshot.get('name')} (ID: {snapshot.get('snapid')})")
                            return snapshots
                        else:
                            logger.error(f"错误: 虚拟机 {vmid} 没有任何快照")
                    else:
                        logger.error(f"错误: 获取快照列表失败: success不为1")
                        logger.error(f"响应: {result.stdout[:200]}")
                except json.JSONDecodeError as e:
                    logger.error(f"错误: 解析响应JSON失败: {e}")
                    logger.error(f"响应内容: {result.stdout[:200]}")
            else:
                logger.error(f"错误: 获取快照列表失败: 响应为空")
                if result.stderr:
                    logger.error(f"错误信息: {result.stderr}")
            
            return None
            
        except Exception as e:
            logger.error(f"错误: 获取快照列表失败: {e}")
            traceback.print_exc()
            return None
        
    def get_vm_id(self, vm_name):
        """根据虚拟机名称获取虚拟机ID"""
        if not self.hci_credentials:
            logger.error("错误: HCI登录凭证未获取")
            return None
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            logger.info(f"正在查找虚拟机 {vm_name}...")
            
            # 使用curl命令获取虚拟机列表（参考vm_group.py的成功实现）
            curl_command = f"curl -k \"https://{ip}/vapi/extjs/cluster/vms?group_type=group&sort_type=&desc=1&scene=resources_used\" -H \"Accept: */*\" -H \"CSRFPreventionToken: {csrf_token}\" -H \"Cookie: {cookie}\" -H \"X-Requested-With: XMLHttpRequest\""
            
            # 执行curl命令
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            logger.info(f"curl响应状态: 完成")
            
            # 解析响应
            if result.stdout:
                try:
                    response_data = json.loads(result.stdout)
                    
                    if response_data.get("success") == 1:
                        # 解析虚拟机列表（数据是分组的）
                        groups = response_data.get("data", [])
                        
                        # 在所有组中查找虚拟机
                        for group in groups:
                            vms = group.get("data", [])
                            for vm in vms:
                                if vm.get("name") == vm_name:
                                    vmid = vm.get("vmid")
                                    logger.info(f"成功: 找到虚拟机: {vm_name}, ID: {vmid}")
                                    return vmid
                        
                        # 打印所有虚拟机名称，帮助调试
                        logger.info("未找到虚拟机，所有可用虚拟机名称:")
                        for group in groups:
                            vms = group.get("data", [])
                            for vm in vms:
                                logger.info(f"  - {vm.get('name')}")
                    else:
                        logger.error(f"错误: 获取虚拟机列表失败: success不为1")
                        logger.error(f"响应: {result.stdout[:200]}")
                except json.JSONDecodeError as e:
                    logger.error(f"错误: 解析响应JSON失败: {e}")
                    logger.error(f"响应内容: {result.stdout[:200]}")
            else:
                logger.error(f"错误: 获取虚拟机列表失败: 响应为空")
                if result.stderr:
                    logger.error(f"错误信息: {result.stderr}")
            
            logger.error(f"错误: 未找到虚拟机: {vm_name}")
            return None
            
        except Exception as e:
            logger.error(f"错误: 获取虚拟机ID失败: {e}")
            traceback.print_exc()
            return None
        

if __name__ == "__main__":
    # 创建工作流实例
    workflow = VMManagementWorkflow()
    
    # 运行完整工作流
    success = workflow.run_workflow()
    
    if success:
        logger.info("工作流执行成功！")
        sys.exit(0)
    else:
        logger.error("工作流执行失败！")
        sys.exit(1)
