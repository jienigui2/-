#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户配置恢复脚本
"""

import re
import sys
import os
from playwright.sync_api import Playwright, sync_playwright, expect

# 确保标准输出编码正确
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys, 'stdout'):
    # 旧版Python的处理方式
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 确保文件系统编码正确
os.environ['PYTHONIOENCODING'] = 'utf-8'


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
    try:
        # 确保文件路径编码正确
        if config_file_path:
            # 处理文件路径编码
            if isinstance(config_file_path, str):
                # 确保文件路径使用正确的编码
                config_file_path = config_file_path.encode('utf-8').decode('utf-8')
            page.get_by_role("button", name="Choose File").set_input_files(config_file_path)
            print("[DEBUG] 文件路径编码处理完成:", config_file_path)
    except Exception as file_e:
        print(f"[ERROR] 文件上传失败: {file_e}")
        return
    
    # 等待上传完成 - 每隔1秒检查一次
    no_upload_count = 0
    max_no_upload_count = 2  # 连续2次没有"正在上传"字样则认为上传完成
    
    print("文件上传中，检查上传状态...")
    try:
        while True:
            page.wait_for_timeout(1000)  # 等待1秒
            page_content = page.content()
            
            try:
                # 确保页面内容编码正确
                if isinstance(page_content, bytes):
                    page_content = page_content.decode('utf-8')
                
                if "正在上传" in page_content or "上传中" in page_content:
                    print("检测到'正在上传'，继续等待...")
                    no_upload_count = 0
                else:
                    no_upload_count += 1
                    print(f"未检测到上传中 ({no_upload_count}/{max_no_upload_count})")
                    
                    if no_upload_count >= max_no_upload_count:
                        print("文件上传完成")
                        break
            except Exception as content_e:
                print(f"[DEBUG] 页面内容处理失败: {content_e}")
                # 即使内容处理失败，也继续等待
                no_upload_count += 1
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
            # 确保按钮名称编码正确
            button_text = "恢复配置"
            if isinstance(button_text, str):
                button_text = button_text.encode('utf-8').decode('utf-8')
            page.get_by_role("cell", name=button_text).nth(1).click()
            button_name = "恢复配置（第2个）"
            clicked = True
            print(f"[OK] 第1步：点击{button_name}")
        except Exception as e1:
            print(f"[DEBUG] 尝试点击'恢复配置'按钮失败: {e1}")
            # 如果失败，尝试点击第2个"开始恢复"按钮
            try:
                # 确保按钮名称编码正确
                button_text = "开始恢复"
                if isinstance(button_text, str):
                    button_text = button_text.encode('utf-8').decode('utf-8')
                page.get_by_role("cell", name=button_text).nth(1).click()
                button_name = "开始恢复（第2个）"
                clicked = True
                print(f"[OK] 第1步：点击{button_name}")
            except Exception as inner_e:
                print(f"[ERROR] 第1步失败：未找到第2个'恢复配置'或'开始恢复'按钮 - {inner_e}")
                return
        
        if not clicked:
            print("[ERROR] 第1步失败：未找到匹配的按钮")
            return
        
    except Exception as e:
        print(f"[ERROR] 第1步失败: {e}")
        return
    
    page.wait_for_timeout(5000)  # 增加等待时间，确保页面完全加载
    
    try:
        # 添加详细的调试信息
        print("[DEBUG] 当前URL:", page.url)
        print("[DEBUG] 页面标题:", page.title())
        
        # 保存当前页面截图，用于调试
        page.screenshot(path='debug_before_step2.png')
        print("[DEBUG] 已保存步骤2前的截图: debug_before_step2.png")
        
        # 获取页面内容的一部分，检查是否包含关键元素
        page_content = page.content()
        print("[DEBUG] 页面内容长度:", len(page_content))
        
        # 确保页面内容编码正确
        try:
            if isinstance(page_content, bytes):
                page_content = page_content.decode('utf-8')
            print("[DEBUG] 页面是否包含'保留项设置':", "保留项设置" in page_content)
        except Exception as content_e:
            print(f"[DEBUG] 页面内容编码处理失败: {content_e}")
        
        # 尝试多种方式定位"保留项设置"元素
        element_found = False
        
        # 方式0：先检查所有可见元素，获取更多信息
        print("[DEBUG] 尝试获取所有可见的文本元素...")
        try:
            # 确保文本编码正确
            search_text = "保留项设置"
            if isinstance(search_text, str):
                search_text = search_text.encode('utf-8').decode('utf-8')
            
            visible_elements = page.locator("*").filter(has_text=search_text).all()
            print(f"[DEBUG] 找到 {len(visible_elements)} 个包含'保留项设置'的元素")
            for i, elem in enumerate(visible_elements):
                try:
                    bounding_box = elem.bounding_box()
                    if bounding_box:
                        print(f"[DEBUG] 元素 {i} 位置: {bounding_box}")
                except:
                    pass
        except Exception as debug_e:
            print(f"[DEBUG] 获取元素信息失败: {debug_e}")
        
        try:
            # 方式1：通过role和name定位
            print("[DEBUG] 尝试方式1：通过role和name定位")
            element = page.get_by_role("textbox", name="保留项设置")
            count = element.count()
            print(f"[DEBUG] 方式1找到 {count} 个元素")
            if count > 0:
                element.click()
                print("[OK] 第2步：点击保留项设置 (方式1)")
                element_found = True
        except Exception as e1:
            print(f"[DEBUG] 方式1失败: {e1}")
        
        if not element_found:
            try:
                # 方式2：通过文本内容定位
                print("[DEBUG] 尝试方式2：通过文本内容定位")
                element = page.get_by_text("保留项设置")
                count = element.count()
                print(f"[DEBUG] 方式2找到 {count} 个元素")
                if count > 0:
                    element.click()
                    print("[OK] 第2步：点击保留项设置 (方式2)")
                    element_found = True
            except Exception as e2:
                print(f"[DEBUG] 方式2失败: {e2}")
        
        if not element_found:
            try:
                # 方式3：通过CSS选择器定位
                print("[DEBUG] 尝试方式3：通过CSS选择器定位")
                element = page.locator("*:has-text('保留项设置')")
                count = element.count()
                print(f"[DEBUG] 方式3找到 {count} 个元素")
                if count > 0:
                    element.click()
                    print("[OK] 第2步：点击保留项设置 (方式3)")
                    element_found = True
            except Exception as e3:
                print(f"[DEBUG] 方式3失败: {e3}")
        
        if not element_found:
            try:
                # 方式4：通过XPath定位
                print("[DEBUG] 尝试方式4：通过XPath定位")
                element = page.locator("//*[contains(text(), '保留项设置')]")
                count = element.count()
                print(f"[DEBUG] 方式4找到 {count} 个元素")
                if count > 0:
                    element.click()
                    print("[OK] 第2步：点击保留项设置 (方式4)")
                    element_found = True
            except Exception as e4:
                print(f"[DEBUG] 方式4失败: {e4}")
        
        if not element_found:
            try:
                # 方式5：通过clickable定位
                print("[DEBUG] 尝试方式5：通过clickable定位")
                element = page.locator("*").filter(has_text="保留项设置").filter(is_visible=True).filter(is_enabled=True)
                count = element.count()
                print(f"[DEBUG] 方式5找到 {count} 个元素")
                if count > 0:
                    element.click()
                    print("[OK] 第2步：点击保留项设置 (方式5)")
                    element_found = True
            except Exception as e5:
                print(f"[DEBUG] 方式5失败: {e5}")
        
        if not element_found:
            # 方式6：通过坐标点击（最后尝试）
            print("[DEBUG] 尝试方式6：通过坐标点击")
            try:
                # 获取页面中心坐标
                viewport = page.viewport_size
                center_x = viewport["width"] // 2
                center_y = viewport["height"] // 2
                print(f"[DEBUG] 尝试点击页面中心: ({center_x}, {center_y})")
                page.mouse.click(center_x, center_y)
                print("[OK] 第2步：点击页面中心 (方式6)")
                element_found = True
            except Exception as e6:
                print(f"[DEBUG] 方式6失败: {e6}")
        
        if element_found:
            page.wait_for_timeout(2000)  # 增加等待时间
            print("[OK] 第2步：元素点击成功")
        else:
            print("[ERROR] 所有定位方式都失败了")
            raise Exception("无法找到'保留项设置'元素")
            
    except Exception as e:
        print(f"[ERROR] 第2步失败: {e}")
        # 保存失败时的截图，便于调试
        try:
            page.screenshot(path='debug_step2_failed.png')
            print("  调试：已保存失败截图: debug_step2_failed.png")
        except Exception as screenshot_e:
            print(f"  截图失败: {screenshot_e}")
        return
    
    page.wait_for_timeout(2000)
    
    try:
        page.get_by_text("全选").click()
        print("[OK] 第3步：点击全选")
    except Exception as e:
        print(f"[ERROR] 第3步失败: {e}")
        return
    
    page.wait_for_timeout(2000)
    page.get_by_role("textbox", name="保留项设置").click()
    page.wait_for_timeout(2000)

    try:
        # 识别页面中"立即恢复"按钮的位置并点击
        print("[OK] 第4步：识别并点击立即恢复按钮")
        

        
        # 查找所有包含"立即恢复"的元素
        immediate_restore_elements = page.get_by_text("立即恢复").all()
        print(f"  调试：找到 {len(immediate_restore_elements)} 个包含'立即恢复'的元素")
        
        # 点击第一个可点击的"立即恢复"元素
        if immediate_restore_elements:
            immediate_restore_elements[0].click()
            print("[OK] 已点击立即恢复按钮")
            page.wait_for_timeout(500)
        else:
            raise Exception("未找到'立即恢复'元素")
    except Exception as e:
        print(f"[ERROR] 第4步失败: {e}")
        # 保存失败后的截图
        page.screenshot(path='debug_step4_failed.png')
        print("  调试：已保存失败截图: debug_step4_failed.png")
        return
    
    try:
        page.locator('input[name="password"]').click()
        print("[OK] 第5步：点击密码框")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"[ERROR] 第5步失败: {e}")
        return
    page.wait_for_timeout(2000)
    
    try:
        page.locator('input[name="password"]').press("CapsLock")
        page.locator('input[name="password"]').fill("Qwer1234")
        print("[OK] 第6步：输入密码")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"[ERROR] 第6步失败: {e}")
        return
    page.wait_for_timeout(2000)
    try:
        # 尝试多种方式找到提交按钮
        page.wait_for_timeout(1000)                        
        page.get_by_role("button", name="提交").click()
        print("[OK] 第7步：点击提交（方式2）")                            
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"[ERROR] 第7步失败: {e}")
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