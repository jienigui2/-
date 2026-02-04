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
    
    # 上传文件 - 使用多种定位方式，不检查可见性
    upload_success = False
    upload_errors = []
    
    # 确保文件路径编码正确
    if config_file_path:
        if isinstance(config_file_path, str):
            config_file_path = config_file_path.encode('utf-8').decode('utf-8')
        
        print("[DEBUG] 开始文件上传，尝试多种定位方式...")
        
        # 方式1：通过 input[type="file"] 定位
        try:
            print("[DEBUG] 尝试方式1：通过 input[type='file'] 定位")
            file_input = page.locator('input[type="file"]')
            count = file_input.count()
            print(f"[DEBUG] 方式1找到 {count} 个元素")
            if count > 0:
                file_input.set_input_files(config_file_path)
                print("[OK] 文件上传成功 (方式1: input[type='file'])")
                upload_success = True
            else:
                upload_errors.append("方式1: 未找到 input[type='file'] 元素")
        except Exception as e1:
            error_msg = f"方式1上传失败: {e1}"
            print(f"[DEBUG] {error_msg}")
            upload_errors.append(error_msg)
        
        # 方式2：通过 role 和 name 定位 "Choose File" 按钮
        if not upload_success:
            try:
                print("[DEBUG] 尝试方式2：通过 role 和 name 定位 'Choose File' 按钮")
                choose_btn = page.get_by_role("button", name="Choose File")
                count = choose_btn.count()
                print(f"[DEBUG] 方式2找到 {count} 个元素")
                if count > 0:
                    choose_btn.set_input_files(config_file_path)
                    print("[OK] 文件上传成功 (方式2: role=button name=Choose File)")
                    upload_success = True
                else:
                    upload_errors.append("方式2: 未找到 'Choose File' 按钮")
            except Exception as e2:
                error_msg = f"方式2上传失败: {e2}"
                print(f"[DEBUG] {error_msg}")
                upload_errors.append(error_msg)
        
        # 方式3：通过 role 和 name 定位 "浏览" 按钮
        if not upload_success:
            try:
                print("[DEBUG] 尝试方式3：通过 role 和 name 定位 '浏览' 按钮")
                browse_btn = page.get_by_role("button", name="浏览")
                count = browse_btn.count()
                print(f"[DEBUG] 方式3找到 {count} 个元素")
                if count > 0:
                    browse_btn.set_input_files(config_file_path)
                    print("[OK] 文件上传成功 (方式3: role=button name=浏览)")
                    upload_success = True
                else:
                    upload_errors.append("方式3: 未找到 '浏览' 按钮")
            except Exception as e3:
                error_msg = f"方式3上传失败: {e3}"
                print(f"[DEBUG] {error_msg}")
                upload_errors.append(error_msg)
        
        # 方式4：通过文本内容定位包含"文件"的元素
        if not upload_success:
            try:
                print("[DEBUG] 尝试方式4：通过文本内容定位包含'文件'的元素")
                file_elem = page.get_by_text("文件")
                count = file_elem.count()
                print(f"[DEBUG] 方式4找到 {count} 个元素")
                if count > 0:
                    file_elem.set_input_files(config_file_path)
                    print("[OK] 文件上传成功 (方式4: 文本'文件')")
                    upload_success = True
                else:
                    upload_errors.append("方式4: 未找到包含'文件'的元素")
            except Exception as e4:
                error_msg = f"方式4上传失败: {e4}"
                print(f"[DEBUG] {error_msg}")
                upload_errors.append(error_msg)
        
        # 方式5：通过 CSS 类名定位（ExtJS 常用类名）
        if not upload_success:
            try:
                print("[DEBUG] 尝试方式5：通过 CSS 类名定位 (ExtJS 类名)")
                extjs_selectors = [
                    '.x-form-file-input',
                    '.x-form-field-file',
                    'input.x-form-file-input'
                ]
                for selector in extjs_selectors:
                    file_input = page.locator(selector)
                    count = file_input.count()
                    print(f"[DEBUG] 选择器'{selector}'找到 {count} 个元素")
                    if count > 0:
                        file_input.set_input_files(config_file_path)
                        print(f"[OK] 文件上传成功 (方式5: CSS选择器'{selector}')")
                        upload_success = True
                        break
                if not upload_success:
                    upload_errors.append("方式5: 未找到 ExtJS 类名对应的 input 元素")
            except Exception as e5:
                error_msg = f"方式5上传失败: {e5}"
                print(f"[DEBUG] {error_msg}")
                upload_errors.append(error_msg)
        
        # 方式6：通过 XPath 定位包含 file 相关属性的 input 元素
        if not upload_success:
            try:
                print("[DEBUG] 尝试方式6：通过 XPath 定位 file 相关属性")
                xpath_selectors = [
                    "//input[contains(@type, 'file')]",
                    "//input[contains(@name, 'file')]",
                    "//input[@type='file']",
                    "//input[contains(@class, 'file')]"
                ]
                for xpath in xpath_selectors:
                    file_input = page.locator(f"xpath={xpath}")
                    count = file_input.count()
                    print(f"[DEBUG] XPath'{xpath}'找到 {count} 个元素")
                    if count > 0:
                        file_input.set_input_files(config_file_path)
                        print(f"[OK] 文件上传成功 (方式6: XPath'{xpath}')")
                        upload_success = True
                        break
                if not upload_success:
                    upload_errors.append("方式6: 未找到 XPath 定位的 file input 元素")
            except Exception as e6:
                error_msg = f"方式6上传失败: {e6}"
                print(f"[DEBUG] {error_msg}")
                upload_errors.append(error_msg)
        
        # 方式7：通过 name 属性模糊匹配
        if not upload_success:
            try:
                print("[DEBUG] 尝试方式7：通过 name 属性模糊匹配")
                attr_selectors = [
                    'input[name*="file"]',
                    'input[type="file"][name]',
                    'input[name]'
                ]
                for selector in attr_selectors:
                    file_input = page.locator(selector)
                    count = file_input.count()
                    print(f"[DEBUG] 选择器'{selector}'找到 {count} 个元素")
                    if count > 0:
                        file_input.set_input_files(config_file_path)
                        print(f"[OK] 文件上传成功 (方式7: 选择器'{selector}')")
                        upload_success = True
                        break
                if not upload_success:
                    upload_errors.append("方式7: 未找到 name 属性匹配的 input 元素")
            except Exception as e7:
                error_msg = f"方式7上传失败: {e7}"
                print(f"[DEBUG] {error_msg}")
                upload_errors.append(error_msg)
        
        # 所有上传方式都失败后的处理
        if not upload_success:
            print("[ERROR] 所有文件上传方式都失败！")
            print("\n=== 上传失败详情 ===")
            for i, error in enumerate(upload_errors, 1):
                print(f"  {i}. {error}")
            
            # 保存页面完整 HTML 内容到文件
            try:
                full_html = page.content()
                if isinstance(full_html, bytes):
                    full_html = full_html.decode('utf-8')
                with open('debug_upload_failed.html', 'w', encoding='utf-8') as f:
                    f.write(full_html)
                print("\n[DEBUG] 已保存完整页面 HTML: debug_upload_failed.html")
            except Exception as html_e:
                print(f"[DEBUG] 保存 HTML 文件失败: {html_e}")
            
            # 保存失败时的截图
            try:
                page.screenshot(path='peizhi_upload_failed.png')
                print("[DEBUG] 已保存失败截图: peizhi_upload_failed.png")
            except Exception as screenshot_e:
                print(f"[DEBUG] 保存截图失败: {screenshot_e}")
            
            # 输出页面中所有 input 元素的信息
            print("\n=== 页面中的 input 元素信息 ===")
            try:
                all_inputs = page.locator('input').all()
                print(f"总计找到 {len(all_inputs)} 个 input 元素:")
                for i, inp in enumerate(all_inputs):
                    try:
                        inp_type = inp.get_attribute('type') or '未指定'
                        inp_name = inp.get_attribute('name') or '无'
                        inp_class = inp.get_attribute('class') or '无'
                        inp_id = inp.get_attribute('id') or '无'
                        print(f"  Input {i+1}: type={inp_type}, name={inp_name}, class={inp_class[:50]}, id={inp_id}")
                    except Exception as attr_e:
                        print(f"  Input {i+1}: 无法获取属性 - {attr_e}")
            except Exception as inputs_e:
                print(f"[DEBUG] 获取 input 元素信息失败: {inputs_e}")
            
            return
    else:
        print("[ERROR] 未提供配置文件路径")
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
        # 第2步：点击保留项设置
        print("等待'保留项设置'元素出现...")
        
        # 等待页面稳定
        page.wait_for_timeout(2000)
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # 保存当前页面截图，用于调试
        page.screenshot(path='debug_before_click_dropdown.png')
        print("[DEBUG] 已保存点击下拉框前的截图: debug_before_click_dropdown.png")
        
        # 打印当前页面的URL和标题，用于调试
        print("[DEBUG] 当前URL:", page.url)
        print("[DEBUG] 当前页面标题:", page.title())
        
        # 获取页面内容的一部分，检查是否包含关键元素
        page_content = page.content()
        if isinstance(page_content, bytes):
            page_content = page_content.decode('utf-8')
        print("[DEBUG] 页面内容是否包含'保留项设置':", "保留项设置" in page_content)
        print("[DEBUG] 页面内容是否包含'ext-comp-1040':", "ext-comp-1040" in page_content)
        print("[DEBUG] 页面内容是否包含'reserve_items':", "reserve_items" in page_content)
        
        # 尝试多种方式点击保留项设置下拉框
        dropdown_opened = False
        
        # 方式1：通过ID定位（最精确，根据用户提供的HTML）
        try:
            print("[DEBUG] 尝试方式1：通过ID定位 'ext-comp-1040'")
            reserve_combo = page.locator("#ext-comp-1040")
            count = reserve_combo.count()
            print(f"[DEBUG] 方式1找到 {count} 个元素")
            if count > 0:
                reserve_combo.wait_for(state="visible", timeout=10000)
                reserve_combo.click()
                print("[OK] 第2步：点击保留项设置下拉框（方式1 - ID）")
                dropdown_opened = True
        except Exception as e1:
            print(f"[DEBUG] 方式1失败: {e1}")
        
        # 方式2：通过name定位
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式2：通过name定位 'reserve_items'")
                reserve_input = page.locator("input[name='reserve_items']")
                count = reserve_input.count()
                print(f"[DEBUG] 方式2找到 {count} 个元素")
                if count > 0:
                    reserve_input.wait_for(state="visible", timeout=10000)
                    reserve_input.click()
                    print("[OK] 第2步：点击保留项设置输入框（方式2 - name）")
                    dropdown_opened = True
            except Exception as e2:
                print(f"[DEBUG] 方式2失败: {e2}")
        
        # 方式3：通过class定位
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式3：通过class定位 'x-combo-text'")
                combo_text = page.locator(".x-combo-text.x-form-text.x-form-field.x-trigger-noedit").first
                count = combo_text.count()
                print(f"[DEBUG] 方式3找到 {count} 个元素")
                if count > 0:
                    combo_text.wait_for(state="visible", timeout=10000)
                    combo_text.click()
                    print("[OK] 第2步：点击保留项设置文本框（方式3 - class）")
                    dropdown_opened = True
            except Exception as e3:
                print(f"[DEBUG] 方式3失败: {e3}")
        
        # 方式4：通过文本内容定位
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式4：通过文本内容定位 '保留项设置'")
                reserve_text = page.get_by_text("保留项设置").first
                count = reserve_text.count()
                print(f"[DEBUG] 方式4找到 {count} 个元素")
                if count > 0:
                    reserve_text.wait_for(state="visible", timeout=10000)
                    reserve_text.click()
                    print("[OK] 第2步：点击保留项设置文本（方式4 - text）")
                    dropdown_opened = True
            except Exception as e4:
                print(f"[DEBUG] 方式4失败: {e4}")
        
        # 方式5：通过箭头触发器定位
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式5：通过箭头触发器定位")
                arrow_trigger = page.locator('.x-form-arrow-trigger').first
                count = arrow_trigger.count()
                print(f"[DEBUG] 方式5找到 {count} 个元素")
                if count > 0:
                    arrow_trigger.wait_for(state="visible", timeout=10000)
                    arrow_trigger.click()
                    print("[OK] 第2步：点击保留项设置下拉箭头（方式5 - arrow）")
                    dropdown_opened = True
            except Exception as e5:
                print(f"[DEBUG] 方式5失败: {e5}")
        
        # 方式6：通过role和name定位
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式6：通过role和name定位 '保留项设置' 文本框")
                preserve_settings_input = page.get_by_role("textbox", name="保留项设置")
                count = preserve_settings_input.count()
                print(f"[DEBUG] 方式6找到 {count} 个元素")
                if count > 0:
                    preserve_settings_input.first.wait_for(state="visible", timeout=10000)
                    preserve_settings_input.first.click()
                    print("[OK] 点击保留项设置文本框（方式6）")
                    dropdown_opened = True
            except Exception as e6:
                print(f"[DEBUG] 方式6失败: {e6}")
        
        # 方式7：通过XPath定位
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式7：通过XPath定位 '保留项设置' 相关元素")
                input_element = page.locator("//label[contains(text(), '保留项设置')]/following-sibling::input")
                count = input_element.count()
                print(f"[DEBUG] 方式7找到 {count} 个输入框元素")
                if count > 0:
                    input_element.first.wait_for(state="visible", timeout=10000)
                    input_element.first.click()
                    print("[OK] 点击标签相邻的输入框（方式7）")
                    dropdown_opened = True
            except Exception as e7:
                print(f"[DEBUG] 方式7失败: {e7}")
        
        # 方式8：通过坐标点击（最后尝试）
        if not dropdown_opened:
            try:
                print("[DEBUG] 尝试方式8：通过坐标点击")
                # 获取页面中心坐标
                viewport = page.viewport_size
                center_x = viewport["width"] // 2
                center_y = viewport["height"] // 2
                print(f"[DEBUG] 尝试点击页面中心: ({center_x}, {center_y})")
                page.mouse.click(center_x, center_y)
                print("[OK] 点击页面中心（方式8）")
                dropdown_opened = True
            except Exception as e8:
                print(f"[DEBUG] 方式8失败: {e8}")
        
        if dropdown_opened:
            print("[OK] 成功点击保留项设置下拉框")
            # 等待下拉框完全展开
            print("等待下拉框展开...")
            page.wait_for_timeout(3000)
        else:
            print("[ERROR] 所有定位方式都失败了，无法打开保留项设置下拉框")
            # 保存截图
            try:
                page.screenshot(path='debug_dropdown_failed.png')
                print("已保存下拉框失败截图: debug_dropdown_failed.png")
            except Exception:
                pass
            raise Exception("无法打开保留项设置下拉框")
        
    except Exception as e:
        print(f"[ERROR] 第2步失败: {e}")
        try:
            page.screenshot(path='debug_step2_failed.png')
            print("已保存失败截图: debug_step2_failed.png")
        except Exception:
            pass
        return
    
    # 第3步：点击全选
    try:
        print("等待'全选'按钮出现...")
        
        # 等待下拉框内容加载
        page.wait_for_timeout(2000)
        
        # 保存当前页面截图，用于调试
        page.screenshot(path='debug_before_select_all.png')
        print("[DEBUG] 已保存全选前的截图: debug_before_select_all.png")
        
        # 打印当前页面的URL和标题，用于调试
        print("[DEBUG] 当前URL:", page.url)
        print("[DEBUG] 当前页面标题:", page.title())
        
        # 获取页面内容的一部分，检查是否包含"全选"文本
        page_content = page.content()
        if isinstance(page_content, bytes):
            page_content = page_content.decode('utf-8')
        print("[DEBUG] 页面内容是否包含'全选':", "全选" in page_content)
        
        # 尝试多种定位方式
        clicked = False
        
        # 方式1：通过文本定位（精确匹配）
        try:
            print("[DEBUG] 尝试方式1：通过文本定位 '全选'（精确匹配）")
            select_all = page.get_by_text("全选", exact=True).first
            select_all.wait_for(state="visible", timeout=10000)
            select_all.click()
            print("[OK] 第3步：点击全选（方式1 - 精确文本）")
            clicked = True
        except Exception as e1:
            print(f"[DEBUG] 方式1失败: {e1}")
        
        # 方式2：通过文本定位（非精确匹配）
        if not clicked:
            try:
                print("[DEBUG] 尝试方式2：通过文本定位 '全选'（非精确匹配）")
                select_all = page.get_by_text("全选").first
                select_all.wait_for(state="visible", timeout=8000)
                select_all.click()
                print("[OK] 第3步：点击全选（方式2 - 非精确文本）")
                clicked = True
            except Exception as e2:
                print(f"[DEBUG] 方式2失败: {e2}")
        
        # 方式3：通过XPath定位
        if not clicked:
            try:
                print("[DEBUG] 尝试方式3：通过XPath定位")
                select_all = page.locator("//*[contains(text(), '全选')]").first
                select_all.wait_for(state="visible", timeout=8000)
                select_all.click()
                print("[OK] 第3步：点击全选（方式3 - XPath）")
                clicked = True
            except Exception as e3:
                print(f"[DEBUG] 方式3失败: {e3}")
        
        # 方式4：通过CSS选择器定位
        if not clicked:
            try:
                print("[DEBUG] 尝试方式4：通过CSS选择器定位")
                select_all = page.locator("*").filter(has_text="全选").first
                select_all.wait_for(state="visible", timeout=8000)
                select_all.click()
                print("[OK] 第3步：点击全选（方式4 - CSS）")
                clicked = True
            except Exception as e4:
                print(f"[DEBUG] 方式4失败: {e4}")
        
        # 方式5：通过class定位（常见的ExtJS按钮class）
        if not clicked:
            try:
                print("[DEBUG] 尝试方式5：通过class定位 ExtJS按钮")
                common_classes = [".x-btn", ".btn", ".button", ".x-btn-text"]
                for cls in common_classes:
                    try:
                        select_all = page.locator(cls).filter(has_text="全选").first
                        select_all.wait_for(state="visible", timeout=4000)
                        select_all.click()
                        print(f"[OK] 第3步：点击全选（方式5 - class '{cls}'）")
                        clicked = True
                        break
                    except Exception:
                        continue
            except Exception as e5:
                print(f"[DEBUG] 方式5失败: {e5}")
        
        # 方式6：通过checkbox角色定位
        if not clicked:
            try:
                print("[DEBUG] 尝试方式6：通过checkbox角色定位")
                select_all = page.get_by_role("checkbox", name="全选").first
                select_all.wait_for(state="visible", timeout=8000)
                select_all.check()
                print("[OK] 第3步：点击全选（方式6 - checkbox角色）")
                clicked = True
            except Exception as e6:
                print(f"[DEBUG] 方式6失败: {e6}")
        
        # 方式7：通过坐标点击（最后尝试）
        if not clicked:
            try:
                print("[DEBUG] 尝试方式7：通过坐标点击")
                # 获取页面中心坐标
                viewport = page.viewport_size
                center_x = viewport["width"] // 2
                center_y = viewport["height"] // 2
                print(f"[DEBUG] 尝试点击页面中心: ({center_x}, {center_y})")
                page.mouse.click(center_x, center_y)
                print("[OK] 第3步：点击页面中心（方式7 - 坐标）")
                clicked = True
            except Exception as e7:
                print(f"[DEBUG] 方式7失败: {e7}")
        
        if not clicked:
            # 保存详细的失败截图
            try:
                page.screenshot(path='debug_select_all_failed.png')
                print("已保存全选失败截图: debug_select_all_failed.png")
            except Exception:
                pass
            raise Exception("所有'全选'定位方式都失败")
        
        print("[OK] 第3步：全选操作成功")
        page.wait_for_timeout(1500)
        
    except Exception as e:
        print(f"[ERROR] 第3步失败: {e}")
        try:
            page.screenshot(path='debug_step3_failed.png')
            print("已保存失败截图: debug_step3_failed.png")
        except Exception:
            pass
        return
    
    # 第4步：点击保留项（收起设置面板）
    try:
        print("[OK] 第4步：尝试收起保留项设置面板")
        # 尝试多种方式收起面板
        try:
            preserve_settings = page.get_by_role("textbox", name="保留项设置")
            preserve_settings.wait_for(state="visible", timeout=3000)
            preserve_settings.click()
            page.wait_for_timeout(1000)
            print("[OK] 第4步：成功收起保留项设置面板")
        except Exception as e:
            print(f"[DEBUG] 收起面板失败: {e}")
            # 这一步不是关键步骤，可以继续执行
            print("继续执行后续步骤...")
    except Exception as e:
        print(f"[ERROR] 第4步失败: {e}")
        # 这一步不是关键步骤，可以继续执行
        print("继续执行后续步骤...")

    # 第5步：点击立即恢复按钮
    try:
        # 等待"立即恢复"按钮可用
        immediate_restore = page.get_by_text("立即恢复").first
        immediate_restore.wait_for(state="visible", timeout=5000)
        immediate_restore.click()
        print("[OK] 第5步：点击立即恢复按钮")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"[ERROR] 第5步失败: {e}")
        try:
            page.screenshot(path='debug_step5_failed.png')
            print("已保存失败截图: debug_step5_failed.png")
        except Exception:
            pass
        return
    
    # 第6步：输入密码
    try:
        password_input = page.locator('input[name="password"]')
        password_input.wait_for(state="visible", timeout=5000)
        password_input.click()
        page.wait_for_timeout(200)
        password_input.fill("Qwer1234")
        print("[OK] 第6步：输入密码")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"[ERROR] 第6步失败: {e}")
        return
    
    # 第7步：点击提交按钮
    try:
        submit_button = page.get_by_role("button", name="提交")
        submit_button.wait_for(state="visible", timeout=5000)
        submit_button.click()
        print("[OK] 第7步：点击提交按钮")
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
