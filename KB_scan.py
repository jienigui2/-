import re
import json
import os
from playwright.sync_api import Playwright, sync_playwright, expect


def load_scan_config():
    """
    从KB_scan.json加载KB扫描配置
    
    Returns:
        dict: 包含username、password和file_path的配置，失败时返回None
    """
    config_file = "KB_scan.json"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"✗ 配置文件 {config_file} 不存在")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 验证配置文件结构
        scan_credentials = config.get('scan_credentials', {})
        scan_config = config.get('scan_config', {})
        
        username = scan_credentials.get('username')
        password = scan_credentials.get('password')
        file_path = scan_config.get('file_path')
        
        if not all([username, password, file_path]):
            print("✗ 配置文件中缺少username、password或file_path")
            return None
            
        return {
            "username": username,
            "password": password,
            "file_path": file_path
        }
        
    except json.JSONDecodeError as e:
        print(f"✗ 解析配置文件JSON失败: {e}")
        return None
    except Exception as e:
        print(f"✗ 读取配置文件失败: {e}")
        return None


def run(playwright: Playwright) -> None:
    # 加载配置
    config = load_scan_config()
    if not config:
        print("✗ 加载配置失败，程序退出")
        return
    
    username = config['username']
    password = config['password']
    file_path = config['file_path']
    
    print(f"✓ 配置加载成功")
    print(f"  用户名: {username}")
    print(f"  文件路径: {file_path}")
    
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://devops.sangfor.com/artifacts/scan/2665/table")
    page.get_by_role("button", name="取消").click()
    page.get_by_text("用户名密码登录").click()
    # page.get_by_role("textbox", name="请输入用户名（工号）, 如： w12345").click()
    page.get_by_role("textbox", name="请输入用户名（工号）, 如： w12345").fill(username)
    # page.get_by_role("textbox", name="请输入密码").click()
    page.get_by_role("textbox", name="请输入密码").fill(password)
    page.get_by_role("button", name="登录").click()
    page.get_by_role("button", name="plus 创建扫描").click()
    print("正在勾选 Virustotal 复选框...")
    
    # 等待Virustotal复选框出现并勾选
    page.get_by_role("checkbox", name="Virustotal").check()
    print("✓ 已勾选 Virustotal")
    
    print("正在上传文件...")
    
    # 点击上传按钮
    page.get_by_role("button", name="upload 上传文件").click()
    
    # 等待文件输入框出现（使用attached状态，因为文件输入框通常是隐藏的）
    print("等待文件输入框...")
    page.wait_for_selector('input[type="file"]', timeout=10000, state="attached")
    print("设置上传文件...")
    page.locator('input[type="file"]').set_input_files(file_path)
    
    # 等待上传进度从0/1变为1/1
    print("等待上传完成...")
    
    # 等待上传进度元素出现
    page.get_by_text("上传进度（0/1）").wait_for(timeout=60000)
    print("文件开始上传...")
    
    # 等待上传进度变为1/1
    page.get_by_text("上传进度（1/1）").wait_for(timeout=300000)
    print("✓ 文件上传完成！")
    
    # 点击开始扫描按钮
    page.get_by_role("button", name="开始扫描").click()
    print("✓ 已点击开始扫描")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
