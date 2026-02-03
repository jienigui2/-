import re
import json
import os
import configparser
import argparse
import logging
from playwright.sync_api import Playwright, sync_playwright, expect

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_scan_config():
    """
    从all.ini加载KB扫描配置
    
    Returns:
        dict: 包含username、password和file_path的配置，失败时返回None
    """
    config_file = "all.ini"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        logger.error(f"✗ 配置文件 {config_file} 不存在")
        return None
    
    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file, encoding='utf-8')
        
        # 验证配置文件结构
        if 'kb_scan' not in config_parser:
            logger.error("✗ 配置文件中缺少kb_scan部分")
            return None
        
        username = config_parser.get('kb_scan', 'username', fallback='')
        password = config_parser.get('kb_scan', 'password', fallback='')
        file_path = config_parser.get('kb_scan', 'file_path', fallback='')
        
        logger.info(f"✓ 从配置文件加载KB扫描配置成功")
        logger.info(f"  用户名: {username}")
        logger.info(f"  文件路径: {file_path}")
        
        return {
            "username": username,
            "password": password,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"✗ 读取配置文件失败: {e}")
        return None

def parse_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 命令行参数
    """
    parser = argparse.ArgumentParser(description='KB扫描工具')
    parser.add_argument('--file_path', help='KB文件路径')
    parser.add_argument('--username', help='登录用户名')
    parser.add_argument('--password', help='登录密码')
    return parser.parse_args()


def run(playwright: Playwright, config) -> None:
    # 加载配置
    if not config:
        logger.error("✗ 加载配置失败，程序退出")
        return
    
    username = config['username']
    password = config['password']
    file_path = config['file_path']
    
    logger.info(f"✓ 配置加载成功")
    logger.info(f"  用户名: {username}")
    logger.info(f"  文件路径: {file_path}")
    
    logger.info("启动浏览器...")
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    logger.info("导航到扫描页面...")
    page.goto("http://devops.sangfor.com/artifacts/scan/2665/table")
    
    logger.info("点击取消按钮...")
    page.get_by_role("button", name="取消").click()
    
    logger.info("点击用户名密码登录...")
    page.get_by_text("用户名密码登录").click()
    
    logger.info("填写用户名...")
    page.get_by_role("textbox", name="请输入用户名（工号）, 如： w12345").fill(username)
    
    logger.info("填写密码...")
    page.get_by_role("textbox", name="请输入密码").fill(password)
    
    logger.info("点击登录按钮...")
    page.get_by_role("button", name="登录").click()
    
    logger.info("点击创建扫描按钮...")
    page.get_by_role("button", name="plus 创建扫描").click()
    
    logger.info("正在勾选 Virustotal 复选框...")
    # 等待Virustotal复选框出现并勾选
    page.get_by_role("checkbox", name="Virustotal").check()
    logger.info("✓ 已勾选 Virustotal")
    
    logger.info("正在上传文件...")
    # 点击上传按钮
    page.get_by_role("button", name="upload 上传文件").click()
    
    # 等待文件输入框出现（使用attached状态，因为文件输入框通常是隐藏的）
    logger.info("等待文件输入框...")
    page.wait_for_selector('input[type="file"]', timeout=10000, state="attached")
    logger.info("设置上传文件...")
    page.locator('input[type="file"]').set_input_files(file_path)
    
    # 等待上传进度从0/1变为1/1
    logger.info("等待上传完成...")
    
    # 等待上传进度元素出现
    page.get_by_text("上传进度（0/1）").wait_for(timeout=60000)
    logger.info("文件开始上传...")
    
    # 等待上传进度变为1/1
    page.get_by_text("上传进度（1/1）").wait_for(timeout=300000)
    logger.info("✓ 文件上传完成！")
    
    # 点击开始扫描按钮
    logger.info("点击开始扫描按钮...")
    page.get_by_role("button", name="开始扫描").click()
    logger.info("✓ 已点击开始扫描")

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    logger.info("启动KB扫描工具...")
    
    # 解析命令行参数
    logger.info("解析命令行参数...")
    args = parse_args()
    
    # 加载配置文件
    logger.info("加载配置文件...")
    config = load_scan_config()
    if not config:
        config = {}
    
    # 命令行参数优先级高于配置文件
    if args.file_path:
        config['file_path'] = args.file_path
        logger.info(f"从命令行获取文件路径: {args.file_path}")
    if args.username:
        config['username'] = args.username
        logger.info(f"从命令行获取用户名: {args.username}")
    if args.password:
        config['password'] = args.password
        logger.info(f"从命令行获取密码")
    
    # 验证必要参数
    if not all([config.get('username'), config.get('password'), config.get('file_path')]):
        logger.error("✗ 缺少必要参数: username、password或file_path")
        exit(1)
    
    logger.info("开始执行扫描流程...")
    with sync_playwright() as playwright:
        run(playwright, config)
    
    logger.info("KB扫描工具执行完成")
