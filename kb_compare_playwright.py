import json
import configparser
import os
from playwright.sync_api import Playwright, sync_playwright, expect


def load_config():
    """
    从all.ini加载配置
    
    Returns:
        dict: 配置信息，失败时返回None
    """
    config_file = "all.ini"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"✗ 配置文件 {config_file} 不存在")
        return None
    
    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file, encoding='utf-8')
        
        # 验证配置文件结构
        if 'kb_compare' not in config_parser:
            print("✗ 配置文件中缺少kb_compare部分")
            return None
        
        if 'kb_test' not in config_parser:
            print("✗ 配置文件中缺少kb_test部分")
            return None
        
        username = config_parser.get('kb_compare', 'kb_username', fallback='')
        password = config_parser.get('kb_compare', 'kb_password', fallback='')
        history_packages = config_parser.get('kb_compare', 'history_packages', fallback='')
        kb_number = config_parser.get('kb_test', 'kb_number', fallback='')
        target_id = config_parser.get('kb_test', 'target_id', fallback='')
        
        # 处理历史包，支持逗号分隔的多个包
        history_package_list = [pkg.strip() for pkg in history_packages.split(',') if pkg.strip()]
        history_package_text = '\n'.join(history_package_list)
        
        # 构建待测包名：kb_number-target_id
        pending_package = f"{kb_number}-{target_id}"
        
        return {
            "username": username,
            "password": password,
            "pending_package": pending_package,
            "history_package_text": history_package_text,
            "history_package_list": history_package_list
        }
        
    except Exception as e:
        print(f"✗ 读取配置文件失败: {e}")
        return None


def run(playwright: Playwright) -> None:
    # 从all.ini读取配置
    config = load_config()
    if not config:
        print("✗ 加载配置失败，程序退出")
        return
    
    # 获取配置
    username = config['username']
    password = config['password']
    pending_package = config['pending_package']
    history_package_text = config['history_package_text']
    history_package_list = config['history_package_list']
    
    print(f"登录用户: {username}")
    print(f"待测包: {pending_package}")
    print(f"历史包数量: {len(history_package_list)}")
    for idx, pkg in enumerate(history_package_list, 1):
        print(f"  历史包{idx}: {pkg}")
    
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://kb.sundray.work/#/login?redirect=%2Ftree%2Findex")

    page.get_by_role("textbox", name="Username").fill(username)

    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Login").click()

    page.get_by_role("textbox", name="请输入完整的KB包名，如KB-WACAP-20160918").fill(pending_package)

    page.get_by_role("textbox", name="请输入完整的KB包名，每行一个，最多30").fill(history_package_text)
    page.get_by_role("button", name="开始冲突检测").click()
    
    # 监测加载遮罩层，如果存在则等待消失
    try:
        loading_mask = page.locator('div.el-loading-mask.is-fullscreen')
        if loading_mask.is_visible(timeout=10000):
            print("检测到加载遮罩层，等待处理完成...")
            loading_mask.wait_for(state='hidden', timeout=120000)
            print("加载遮罩层已消失，继续执行")
        else:
            print("未检测到加载遮罩层，继续执行")
    except Exception as e:
        print(f"等待加载遮罩层时出现异常: {e}，继续执行")
    
    # 等待页面加载完成
    page.wait_for_load_state("networkidle", timeout=30000)
    
    # 滚动到页面底部
    # print("滚动到页面底部...")
    # page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    # page.wait_for_timeout(2000)
    
    # 创建截图保存目录
    import os
    screenshot_dir = "KB_compare_photo"
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
        print(f"创建截图目录: {screenshot_dir}")
    
    # 生成截图文件名（包含时间戳）
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"KB_compare_{timestamp}.png")
    
    # 截图保存
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"截图已保存: {screenshot_path}")


    context.close()
    browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)