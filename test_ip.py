"""
测试IP地址配置和静态路由配置的调试脚本
"""
from playwright.sync_api import sync_playwright
import json
import time


def test_ip_configuration():
    """测试IP地址配置和静态路由配置"""
    
    # 从config.json读取配置
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 提取配置信息
    device_ip = config.get('network_config', {}).get('ip_address', '').split('/')[0]
    ip_address = config.get('network_config', {}).get('ip_address', '')
    default_gateway = config.get('network_config', {}).get('default_gateway', '')
    login_username = config.get('login_credentials', {}).get('username')
    login_password = config.get('login_credentials', {}).get('password')
    
    print(f"设备IP: {device_ip}")
    print(f"待配置IP地址: {ip_address}")
    print(f"默认网关: {default_gateway}")
    print(f"登录用户名: {login_username}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_default_timeout(30000)
        
        try:
            # ==================== 登录部分 ====================
            print("\n" + "="*50)
            print("步骤1: 登录设备")
            print("="*50)
            
            page.goto(f'https://{device_ip}')
            
            # 处理证书警告
            try:
                page.get_by_role('button', name='高级').click(timeout=3000)
                page.get_by_role('link', name=f'继续前往{device_ip}（不安全）').click(timeout=3000)
            except:
                pass
            
            # 输入用户名
            page.wait_for_selector('#login_user', state='visible')
            page.locator('#login_user').click()
            page.locator('#login_user').fill('')
            for char in login_username:
                page.keyboard.type(char)
            print(f"已输入用户名: {login_username}")
            
            # 输入密码
            page.wait_for_selector('#login_password', state='visible')
            page.locator('#login_password').click()
            page.locator('#login_password').fill('')
            for char in login_password:
                page.keyboard.type(char)
            print("已输入密码")
            
            # 勾选协议并登录
            page.get_by_role('checkbox', name='我已认真阅读并同意').check()
            page.get_by_text('登录', exact=True).click()
            
            page.wait_for_load_state('networkidle')
            print("✓ 登录成功\n")
            
            # ==================== 配置端口 ====================
            print("="*50)
            print("步骤2: 配置端口")
            print("="*50)
            
            page.goto(f"https://{device_ip}/WLAN/index.php#/system/Port")
            time.sleep(3)
            print(f"已跳转到端口配置页面")
            
            page.locator("span.sim-link[actionname='modify']").filter(has_text="eth0(管理口)").click()
            print("已点击eth0(管理口)修改按钮")
            
            time.sleep(2)
            page.get_by_role("textbox", name="IP地址：").fill(f"{ip_address}")
            print(f"已填入IP地址: {ip_address}")
            
            page.get_by_role("button", name="确定").click()
            print("✓ 已点击确定按钮")
            time.sleep(2)
            
            # ==================== 配置静态路由 ====================
            print("\n" + "="*50)
            print("步骤3: 配置静态路由")
            print("="*50)
            
            page.goto(f"https://{device_ip}/WLAN/index.php#/system/StaticRoute")
            time.sleep(3)
            print(f"已跳转到静态路由配置页面")
            
            page.get_by_role("button", name=" 新增").click()
            print("已点击新增按钮")
            
            page.get_by_role("link", name="新增IPv4静态路由").click()
            print("已点击新增IPv4静态路由")
            
            time.sleep(2)
            page.get_by_role("textbox", name="目标地址：").fill("0.0.0.0")
            print("已填入目标地址: 0.0.0.0")
            
            page.get_by_role("textbox", name="网络掩码：").fill("0.0.0.0")
            print("已填入网络掩码: 0.0.0.0")
            
            page.get_by_role("textbox", name="下一跳地址：").fill(default_gateway)
            print(f"已填入下一跳地址: {default_gateway}")
            
            page.get_by_role("button", name="提交").click()
            print("✓ 已点击提交按钮")
            time.sleep(2)
            
            # ==================== 完成 ====================
            print("\n" + "="*50)
            print("✓ IP地址和静态路由配置测试完成！")
            print("="*50)
            
            # 等待用户确认
            input("\n按Enter键关闭浏览器...")
            
        except Exception as e:
            print(f"\n✗ 测试过程出错: {e}")
            import traceback
            traceback.print_exc()
            input("\n按Enter键关闭浏览器...")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    test_ip_configuration()