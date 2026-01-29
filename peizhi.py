import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright, config_file_path=None, device_ip=None, login_username=None, login_password=None) -> None:
    # 如果没有提供参数，使用默认值
    if device_ip is None:
        device_ip = "10.156.2.112"
    if config_file_path is None:
        config_file_path = r"D:\Users\SXF-Admin\Desktop\Wlan-2026010802 江苏移动\01-客户配置\2026_01_14_105715.bcf"
    if login_username is None:
        login_username = "admin"
    if login_password is None:
        login_password = "Qwer1234"
    
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(f"https://{device_ip}")
    page.locator("#login_user").click()
    page.locator("#login_user").fill(login_username)
    page.locator("#login_password").fill(login_password)
    page.get_by_role("checkbox", name="我已认真阅读并同意").check()
    page.get_by_text("登录", exact=True).click()
    page.goto(f"https://{device_ip}/WLAN/index.php#/maintain/Backup")
    page.wait_for_timeout(2000)
    
    # 上传文件
    page.get_by_role("button", name="Choose File").set_input_files(config_file_path)
    
    # 等待上传完成 - 每隔1秒检查一次
    no_upload_count = 0
    max_no_upload_count = 2  # 连续2次没有"正在上传"字样则认为上传完成
    
    print("文件上传中，检查上传状态...")
    try:
        while True:
            page.wait_for_timeout(1000)  # 等待1秒
            page_content = page.content()
            
            if "正在上传" in page_content or "上传中" in page_content:
                print("检测到'正在上传'，继续等待...")
                no_upload_count = 0
            else:
                no_upload_count += 1
                print(f"未检测到上传中 ({no_upload_count}/{max_no_upload_count})")
                
                if no_upload_count >= max_no_upload_count:
                    print("文件上传完成")
                    break
    except Exception as e:
        print(f"上传检查过程中出错: {e}")
        return
    
    # 点击恢复配置
    print("准备点击各个步骤...")


    try:
        # 等待页面刷新
        page.wait_for_timeout(3000)
        
        # 尝试点击第2个"恢复配置"或"开始恢复"按钮
        clicked = False
        button_name = ""
        
        # 优先尝试点击第2个"恢复配置"按钮
        try:
            page.get_by_role("cell", name="恢复配置").nth(1).click()
            button_name = "恢复配置（第2个）"
            clicked = True
            print(f"✓ 第1步：点击{button_name}")
        except:
            # 如果失败，尝试点击第2个"开始恢复"按钮
            try:
                page.get_by_role("cell", name="开始恢复").nth(1).click()
                button_name = "开始恢复（第2个）"
                clicked = True
                print(f"✓ 第1步：点击{button_name}")
            except Exception as inner_e:
                print(f"✗ 第1步失败：未找到第2个'恢复配置'或'开始恢复'按钮 - {inner_e}")
                return
        
        if not clicked:
            print("✗ 第1步失败：未找到匹配的按钮")
            return
        
    except Exception as e:
        print(f"✗ 第1步失败: {e}")
        return
    
    page.wait_for_timeout(2000)
    
    try:
        page.get_by_role("textbox", name="保留项设置").click()
        print("✓ 第2步：点击保留项设置")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"✗ 第2步失败: {e}")
        return
    
    page.wait_for_timeout(2000)
    
    try:
        page.get_by_text("全选").click()
        print("✓ 第3步：点击全选")
    except Exception as e:
        print(f"✗ 第3步失败: {e}")
        return
    
    page.wait_for_timeout(2000)
    page.get_by_role("textbox", name="保留项设置").click()
    page.wait_for_timeout(2000)

    try:
        # 识别页面中"立即恢复"按钮的位置并点击
        print("✓ 第4步：识别并点击立即恢复按钮")
        
        # 保存当前页面截图用于调试
        page.screenshot(path='debug_step4_before_click.png')
        print("  调试：已保存当前页面截图: debug_step4_before_click.png")
        
        # 查找所有包含"立即恢复"的元素
        immediate_restore_elements = page.get_by_text("立即恢复").all()
        print(f"  调试：找到 {len(immediate_restore_elements)} 个包含'立即恢复'的元素")
        
        # 点击第一个可点击的"立即恢复"元素
        if immediate_restore_elements:
            immediate_restore_elements[0].click()
            print("✓ 已点击立即恢复按钮")
            page.wait_for_timeout(500)
        else:
            raise Exception("未找到'立即恢复'元素")
    except Exception as e:
        print(f"✗ 第4步失败: {e}")
        # 保存失败后的截图
        page.screenshot(path='debug_step4_failed.png')
        print("  调试：已保存失败截图: debug_step4_failed.png")
        return
    
    try:
        page.locator('input[name="password"]').click()
        print("✓ 第5步：点击密码框")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"✗ 第5步失败: {e}")
        return
    page.wait_for_timeout(2000)
    
    try:
        page.locator('input[name="password"]').press("CapsLock")
        page.locator('input[name="password"]').fill("Qwer1234")
        print("✓ 第6步：输入密码")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"✗ 第6步失败: {e}")
        return
    page.wait_for_timeout(2000)
    try:
        # 尝试多种方式找到提交按钮
        page.wait_for_timeout(1000)                        
        page.get_by_role("button", name="提交").click()
        print("✓ 第7步：点击提交（方式2）")                            
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"✗ 第7步失败: {e}")
        return
    
    
    # ---------------------
    print("配置恢复完成")
    page.wait_for_timeout(8000)
    
    # 等待5秒后检查页面是否正常加载
    print("等待20秒后检查页面是否正常加载...")
    page.wait_for_timeout(20000)
    
    
    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)