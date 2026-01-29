import re
import json
import urllib.parse
import cv2
import numpy as np
import requests
from playwright.sync_api import Playwright, sync_playwright, expect
try:
    from pyzbar import pyzbar
    pyzbar_available = True
except ImportError:
    print("pyzbar库未安装，将只使用OpenCV检测")
    pyzbar_available = False

# ============ HCI 设备登录配置 ============
HCI_DEVICE_IP = "10.156.1.50"
HCI_USERNAME = "admin"
HCI_PASSWORD = "Msgt@202601"
HCI_HTTP_PORT = "443"
# =========================================


def get_hci_credentials():
    """使用Playwright实时获取 HCI 设备的登录凭证"""
    try:
        print(f"正在登录 HCI 设备 {HCI_DEVICE_IP}...")
        
        # 使用Playwright完成登录（可以处理SSL问题）
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # 1. 获取公钥
            print("正在获取公钥...")
            public_key_url = f"https://{HCI_DEVICE_IP}:{HCI_HTTP_PORT}/vapi/json/public_key"
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
                import rsa
                import binascii
                
                key = rsa.PublicKey(int(public_key, 16), int("10001", 16))
                password_temp = rsa.encrypt(bytes(HCI_PASSWORD, encoding="utf-8"), key)
                password_rsa = str(binascii.b2a_hex(password_temp), encoding="utf-8")
                print(f"✅ 密码加密完成")
            except Exception as e:
                print(f"❌ 密码加密失败: {e}")
                browser.close()
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
                browser.close()
                return None
            
            try:
                login_data = resp.json()
            except Exception as e:
                print(f"❌ 登录响应解析失败: {e}")
                print(f"响应内容: {resp.text()}")
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
            
            credentials = {
                "cookie": f"LoginAuthCookie={ticket}",
                "csrf_token": csrf_token,
                "context": context  # 保留context用于后续请求
            }
            
            browser.close()
            
            print(f"✅ 成功获取登录凭证")
            print(f"   Cookie: {credentials['cookie'][:50]}...")
            print(f"   CSRFPreventionToken: {csrf_token}")
            
            return credentials
            
    except Exception as e:
        print(f"❌ 获取 HCI 登录凭证失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def send_api_request():
    """发送API请求获取虚拟机信息（实时获取登录凭证）"""
    target_vmid = None
    encoded_name = None
    
    # 实时获取 HCI 登录凭证
    credentials = get_hci_credentials()
    if not credentials:
        print("无法获取登录凭证，终止执行")
        return None, None
    
    hci_instance = credentials.get("hci_instance")
    
    # 使用 Playwright 发送请求
    with sync_playwright() as p:
        # 创建忽略SSL错误的浏览器上下文
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # 设置必要的请求头（使用实时获取的凭证）
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "CSRFPreventionToken": credentials["csrf_token"],
            "Connection": "keep-alive",
            "Cookie": credentials["cookie"],
            "Host": HCI_DEVICE_IP,
            "Referer": f"https://{HCI_DEVICE_IP}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
        
        try:
            # 构建URL参数
            params = {
                "group_type": "group",
                "sort_type": "",
                "desc": "1",
                "scene": "resources_used"
            }
            
            # 访问URL（使用配置的设备IP）
            base_url = f"https://{HCI_DEVICE_IP}/vapi/extjs/cluster/vms"
            url_with_params = base_url
            if params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url_with_params = f"{base_url}?{query_string}"
            
            # 使用context.request.get直接发送API请求
            response = context.request.get(
                base_url,
                params=params,
                headers=headers,
                timeout=30000
            )
            
            if response.status == 200:
                try:
                    data = response.json()
                    
                    # 筛选出名称为 "XMG5100丛雨2.112" 的虚拟机
                    target_vm_name = "XMG5100_不要关_2.127_0001"
                    
                    if "data" in data:
                        for group in data["data"]:
                            if "data" in group:
                                for vm in group["data"]:
                                    if vm.get("name") == target_vm_name:
                                        target_vmid = vm.get("vmid")
                                        encoded_name = urllib.parse.quote(target_vm_name)
                                        break
                    
                    if target_vmid:
                        print(f"{target_vm_name} {target_vmid} {encoded_name}")
                        return target_vmid, encoded_name
                    else:
                        print(f"未找到虚拟机: {target_vm_name}")
                        return None, None
                
                except Exception as e:
                    print(f"JSON解析失败: {e}")
                    return None, None
            
            print(f"请求失败: HTTP {response.status}")
            browser.close()
            return None, None
        
        except Exception as e:
            print(f"请求失败: {e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return None, None


def run(playwright: Playwright, vmid: str, vmname: str) -> None:
    """运行浏览器自动化"""
    # 声明全局变量，用于存储提取到的二维码数据
    global qrcode_data
    qrcode_data = None  # 初始化qrcode_data变量

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(f"https://{HCI_DEVICE_IP}/#/mod-computer/index?id=&name=&stype=&status=&active_grp_path=&group_type=&tab=hci")
    
    
    # 输入用户名
    page.get_by_role("textbox", name="请输入您的用户名").click(timeout=10000)
    page.get_by_role("textbox", name="请输入您的用户名").fill(HCI_USERNAME)
    
    # 输入密码
    page.get_by_role("textbox", name="请输入您的密码").click()
    page.get_by_role("textbox", name="请输入您的密码").fill(HCI_PASSWORD)
    
    # 点击登录按钮
    page.get_by_role("button", name="立即登录").click()
    
    # 停5秒
    print("等待5秒...")
    page.wait_for_timeout(5000)
    print("✓ 停5秒完成")
    page.goto(f"https://{HCI_DEVICE_IP}/#/mod-console/index?n-hfs&vmid={vmid}&vmname={vmname}")
    
    # 跳转完成后等待10秒
    print("跳转完成后等待7秒...")
    page.wait_for_timeout(7000)
    print("✓ 等待7秒完成")
    
    page.mouse.click(page.viewport_size["width"] // 2, page.viewport_size["height"] // 2)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    # 逐字符输入，避免输入被截断
    for char in "aadmin":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    # 逐字符输入密码，避免输入被截断
    password = "Qwer1234sunwns"
    for char in password:
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)  # 等待密码验证完成
    page.wait_for_timeout(5000)  # 暂停两秒
    
    # 使用OpenCV检测二维码
    print("检测二维码...")
    # 尝试多次检测，提高成功率
    max_attempts = 3
    qr_detected = False
    
    for attempt in range(max_attempts):
        print(f"第 {attempt + 1} 次检测...")
        screenshot_bytes = page.screenshot()
        
        # 保存截图到文件，便于调试
        with open(f"qrcode_screenshot_{attempt + 1}.png", "wb") as f:
            f.write(screenshot_bytes)
        print(f"截图已保存为 qrcode_screenshot_{attempt + 1}.png")
        
        # 转换为OpenCV格式
        img_array = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # 方法1：基于二维码特征的简单检测
        print("方法1：基于二维码特征的简单检测...")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测二维码的三个定位图案（角落的正方形）
        # 使用边缘检测
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 统计正方形轮廓的数量（二维码的定位图案）
        square_count = 0
        for contour in contours:
            # 近似轮廓
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 检查是否为四边形
            if len(approx) == 4:
                # 检查是否为正方形（长宽比接近1）
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.9 < aspect_ratio < 1.1:
                    square_count += 1
                    # 绘制轮廓（仅用于调试）
                    cv2.drawContours(img, [approx], 0, (0, 255, 0), 2)
        
        # 保存带有轮廓的图像
        cv2.imwrite(f"qrcode_contours_{attempt + 1}.png", img)
        print(f"带有轮廓的图像已保存为 qrcode_contours_{attempt + 1}.png")
        
        # 如果检测到3个或更多正方形，认为可能存在二维码
        if square_count >= 3:
            print(f"检测到 {square_count} 个正方形轮廓，可能存在二维码，停止执行")
            qr_detected = True
            break
        
        # 方法2：简单的亮度分析（检测屏幕中央的高对比度区域）
        print("方法2：简单的亮度分析...")
        # 获取屏幕中央区域
        h, w = gray.shape
        center_region = gray[h//3:2*h//3, w//3:2*w//3]
        
        # 计算亮度标准差（二维码区域通常有高对比度）
        std_dev = np.std(center_region)
        print(f"中央区域亮度标准差: {std_dev}")
        
        # 如果标准差高于阈值，认为可能存在二维码
        if std_dev > 80:
            print(f"中央区域对比度高（标准差: {std_dev}），可能存在二维码，停止执行")
            qr_detected = True
            break
        
        print(f"第 {attempt + 1} 次检测未找到二维码")
        # 等待一段时间后再次尝试
        page.wait_for_timeout(3000)
    
    if qr_detected:
        print("检测到二维码，准备使用PyAutoGUI截图并复制到剪贴板...")
        
        # 导入必要的库
        try:
            import pyautogui
            from PIL import ImageGrab
            import win32clipboard
            from io import BytesIO
            
            def screenshot_to_clipboard():
                # 截取全屏
                print("正在截取屏幕...")
                img = pyautogui.screenshot()
                
                # 将图片转为二进制流
                print("正在处理图片...")
                output = BytesIO()
                img.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # 去掉 BMP 文件头
                output.close()
                
                # 写入剪贴板
                print("正在复制到剪贴板...")
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                
                print("✅ 截图已复制到剪贴板！")
                return True
            
            # 执行截图并复制到剪贴板
            success = screenshot_to_clipboard()
            if success:
                print("操作完成：已使用PyAutoGUI截图并复制到剪贴板")
                
                # 打开新的浏览器窗口，访问指定网站并粘贴图片
                print("打开网站并粘贴图片...")
                try:
                    # 在同一个浏览器上下文中打开新页面
                    new_page = context.new_page()
                    
                    # 访问指定网站
                    new_page.goto("http://200.200.92.147/hyc/qrcode_get.html", timeout=60000)
                    
                    # 等待页面加载完毕
                    new_page.wait_for_load_state("networkidle", timeout=60000)
                    print("网站加载完毕")
                    
                    # 等待一段时间，确保页面完全就绪
                    new_page.wait_for_timeout(2000)
                    
                    # 点击页面，确保获得焦点
                    new_page.mouse.click(new_page.viewport_size["width"] // 2, new_page.viewport_size["height"] // 2)
                    print("已点击页面，确保获得焦点")
                    
                    # 模拟键盘操作 Ctrl+V 粘贴图片
                    new_page.keyboard.down("Control")
                    new_page.keyboard.press("V")
                    new_page.keyboard.up("Control")
                    print("图片已粘贴到页面")
                    
                    # 等待一段时间，让用户查看结果
                    new_page.wait_for_timeout(5000)
                    
                    # 提示用户操作完成
                    print("操作完成：二维码已复制并粘贴到网站")
                    
                    # 发送请求获取响应
                    print("发送请求获取响应...")
                    try:
                        import requests
                        
                        # 请求URL
                        url = "http://200.200.92.147/hyc/device_login/qrcode_get.php?qr=VUZYM2xWZVhESUJtS0FmeWtoVGQrMmN2cllXMWtqbHVzeGIrbzJuOXR4WT0="
                        
                        # 请求头
                        headers = {
                            "Accept": "application/json, text/javascript, */*; q=0.01",
                            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                            "Connection": "keep-alive",
                            "Referer": "http://200.200.92.147/hyc/qrcode_get.html",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
                            "X-Requested-With": "XMLHttpRequest"
                        }
                        
                        # 发送请求
                        response = requests.get(url, headers=headers, timeout=30, verify=False)
                        
                        # 处理响应
                        if response.status_code == 200:
                            try:
                                response_data = response.json()
                                print(f"请求成功，响应: {response_data}")
                                
                                # 提取data值
                                if "data" in response_data:
                                    extracted_data = response_data["data"]
                                    print(f"提取到的data值: {extracted_data}")
                                    # 将值赋给外部变量
                                    qrcode_data = extracted_data
                                else:
                                    print("响应中未找到data字段")
                            except Exception as json_error:
                                print(f"响应解析失败: {json_error}")
                                print(f"原始响应: {response.text}")
                        else:
                            print(f"请求失败，状态码: {response.status_code}")
                            print(f"响应内容: {response.text}")
                            
                    except Exception as req_error:
                        print(f"发送请求失败: {req_error}")
                    
                    # 关闭当前页面，返回上一网页
                    print("关闭当前页面，返回上一网页...")
                    try:
                        # 关闭qrcode_get.html页面
                        new_page.close()
                        print("已关闭qrcode_get.html页面")
                        
                        # 返回上一网页（虚拟机控制台页面）
                        print("返回虚拟机控制台页面继续操作...")
                    except Exception as close_error:
                        print(f"关闭页面失败: {close_error}")
                except Exception as e:
                    print(f"打开网站失败: {e}")
            else:
                print("操作失败：截图并复制到剪贴板失败")
        
        except Exception as e:
            print(f"使用PyAutoGUI失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 继续执行后续操作，不直接返回
    else:
        print("多次检测后仍未检测到二维码，继续执行配置")

    page.mouse.click(page.viewport_size["width"] // 2, page.viewport_size["height"] // 2)
    # 使用提取到的qrcode_data值作为输入
    input_value = qrcode_data if qrcode_data else ""
    print(f"使用输入值: {input_value}")
    # 逐字符输入，避免输入被截断
    for char in input_value:
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    # 逐字符输入，避免输入被截断
    for char in "cli":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.wait_for_timeout(2000)
    page.keyboard.press("Enter")
    # 逐字符输入，避免输入被截断
    for char in "config terminal":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.wait_for_timeout(2000)
    page.keyboard.press("Enter")
    # 逐字符输入，避免输入被截断
    for char in "in eth0":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.wait_for_timeout(2000)
    page.keyboard.press("Enter")
    # 逐字符输入，避免输入被截断
    for char in "ip addr 10.156.2.127/15":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.wait_for_timeout(2000)
    page.keyboard.press("Enter")
    # 逐字符输入，避免输入被截断
    for char in "exit":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.wait_for_timeout(2000)
    page.keyboard.press("Enter")
    # 逐字符输入，避免输入被截断
    for char in "ip route 0.0.0.0/0 10.157.255.254":
        page.keyboard.type(char)
        page.wait_for_timeout(50)
    page.wait_for_timeout(2000)
    page.keyboard.press("Enter")

    page.goto("https://10.156.2.127")
    page.locator("#login_user").fill("admin")
    page.locator("#login_password").fill("Qwer1234")
    page.get_by_role("checkbox", name="我已认真阅读并同意").check()
    page.get_by_text("登录", exact=True).click() 
    page.goto("https://10.156.2.127/WLAN/index.php#/system/Port")
    page.locator("span.sim-link[actionname='modify']").filter(has_text="eth0(管理口)").click()
    page.get_by_role("textbox", name="IP地址：").fill("10.156.2.127/15")
    page.locator("button.x-btn-text").filter(has_text="提交").click()
    page.goto("https://10.156.2.127/WLAN/index.php#/system/StaticRoute")
    page.get_by_role("button", name=" 新增").click()
    page.get_by_role("link", name="新增IPv4静态路由").click()
    page.get_by_role("textbox", name="目标地址：").click()
    page.get_by_role("textbox", name="目标地址：").fill("0.0.0.0")
    page.get_by_role("textbox", name="网络掩码：").click()
    page.get_by_role("textbox", name="网络掩码：").fill("0.0.0.0")
    page.get_by_role("textbox", name="下一跳地址：").click()
    page.get_by_role("textbox", name="下一跳地址：").fill("10.157.255.254")
    page.locator("button.x-btn-text").filter(has_text="提交").click()

    # ---------------------
    context.close()
    browser.close()


# 在程序启动时发送API请求并运行浏览器自动化
if __name__ == "__main__":
    vmid, vmname = send_api_request()
    if vmid and vmname:
        with sync_playwright() as playwright:
            run(playwright, vmid, vmname)