"""
测试确认按钮定位的调试脚本
"""
from playwright.sync_api import sync_playwright
import time

def test_confirm_button_detection(device_ip, login_username, login_password):
    """测试确认按钮的多种定位方式"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--ignore-certificate-errors'])
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_default_timeout(30000)
        
        try:
            # 1. 登录
            print("步骤1: 登录设备...")
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
            
            # 输入密码
            page.wait_for_selector('#login_password', state='visible')
            page.locator('#login_password').click()
            page.locator('#login_password').fill('')
            for char in login_password:
                page.keyboard.type(char)
            
            # 勾选协议并登录
            page.get_by_role('checkbox', name='我已认真阅读并同意').check()
            page.get_by_text('登录', exact=True).click()
            
            page.wait_for_load_state('networkidle')
            print("✓ 登录成功")
            
            # 2. 跳转到升级页面
            print("\n步骤2: 跳转到升级页面...")
            page.goto(f'https://{device_ip}/WLAN/index.php#/maintain/DeviceUpdate')
            time.sleep(5)
            print("✓ 已跳转到升级页面")
            
            # 3. 勾选补丁包升级
            print("\n步骤3: 勾选'补丁包升级'...")
            page.get_by_role('radio', name='补丁包升级').check()
            time.sleep(3)
            print("✓ 已勾选'补丁包升级'")
            
            # 4. 点击"开始升级"按钮
            print("\n步骤4: 点击'开始升级'按钮...")
            page.get_by_role('button', name='开始升级').click()
            print("✓ 已点击'开始升级'按钮")
            
            # 5. 等待并调试确认按钮
            print("\n步骤5: 等待确认按钮出现并调试...")
            time.sleep(5)
            
            # 保存当前页面截图
            page.screenshot(path='debug_after_start_upgrade.png')
            print("✓ 已保存截图: debug_after_start_upgrade.png")
            
            # 查找所有按钮
            print("\n调试信息: 页面上所有按钮...")
            buttons = page.locator('button').all()
            print(f"共找到 {len(buttons)} 个按钮")
            for idx, btn in enumerate(buttons):
                try:
                    btn_text = btn.inner_text(timeout=1000)
                    is_visible = btn.is_visible()
                    is_enabled = btn.is_enabled()
                    print(f"  按钮{idx}: '{btn_text}' (可见:{is_visible}, 可用:{is_enabled})")
                except Exception as e:
                    print(f"  按钮{idx}: 无法获取信息 - {e}")
            
            # 查找包含"确认"或"确定"的元素
            print("\n调试信息: 查找包含'确认'或'确定'的元素...")
            
            # 方法1: 直接文本查找
            try:
                confirm_by_text = page.get_by_text('确认', exact=False).all()
                print(f"包含'确认'的元素: {len(confirm_by_text)} 个")
                for idx, elem in enumerate(confirm_by_text[:5]):  # 只显示前5个
                    try:
                        tag = elem.evaluate('el => el.tagName')
                        print(f"  元素{idx}: <{tag}> - {elem.inner_text(timeout=500)[:30]}")
                    except:
                        pass
            except Exception as e:
                print(f"查找'确认'失败: {e}")
            
            # 方法2: 查找所有包含"确定"的元素
            try:
                determine_by_text = page.get_by_text('确定', exact=False).all()
                print(f"包含'确定'的元素: {len(determine_by_text)} 个")
                for idx, elem in enumerate(determine_by_text[:5]):
                    try:
                        tag = elem.evaluate('el => el.tagName')
                        print(f"  元素{idx}: <{tag}> - {elem.inner_text(timeout=500)[:30]}")
                    except:
                        pass
            except Exception as e:
                print(f"查找'确定'失败: {e}")
            
            # 方法3: 查找所有可点击元素
            print("\n调试信息: 查找所有可点击元素（button, input[type=button], a）...")
            clickable = page.locator('button, input[type="button"], input[type="submit"], a').all()
            print(f"共找到 {len(clickable)} 个可点击元素")
            for idx, elem in enumerate(clickable[:10]):  # 只显示前10个
                try:
                    tag = elem.evaluate('el => el.tagName')
                    text = elem.inner_text(timeout=500).strip()
                    if text:
                        print(f"  元素{idx}: <{tag}> - '{text}'")
                except:
                    pass
            
            # 方法4: 使用XPath查找所有包含确认/确定文本的元素
            print("\n调试信息: 使用XPath查找所有确认/确定元素...")
            xpath_result = page.locator('//*[contains(text(), "确认") or contains(text(), "确定")]').all()
            print(f"共找到 {len(xpath_result)} 个元素")
            for idx, elem in enumerate(xpath_result[:5]):
                try:
                    tag = elem.evaluate('el => el.tagName')
                    text = elem.inner_text(timeout=500).strip()
                    print(f"  元素{idx}: <{tag}> - '{text}'")
                except:
                    pass
            
            # 保存页面的HTML结构
            print("\n保存页面HTML结构...")
            html_content = page.content()
            with open('debug_page_structure.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("✓ 已保存: debug_page_structure.html")
            
            print("\n" + "="*50)
            print("调试完成！请检查以下文件：")
            print("1. debug_after_start_upgrade.png - 页面截图")
            print("2. debug_page_structure.html - 页面HTML结构")
            print("="*50)
            
            # 等待用户手动操作
            input("\n按Enter键关闭浏览器...")
            
        except Exception as e:
            print(f"\n✗ 测试过程出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    # 从config.json读取配置
    import json
    
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    device_ip = config.get('network_config', {}).get('ip_address', '').split('/')[0]
    login_username = config.get('login_credentials', {}).get('username')
    login_password = config.get('login_credentials', {}).get('password')
    
    print(f"设备IP: {device_ip}")
    print(f"用户名: {login_username}")
    
    test_confirm_button_detection(device_ip, login_username, login_password)