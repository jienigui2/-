import asyncio
from playwright.async_api import async_playwright
import logging
import argparse
import configparser
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 读取配置文件
def read_config(config_file='config.ini'):
    """
    读取配置文件
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        dict: 配置信息
    """
    config = {}
    if os.path.exists(config_file):
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file, encoding='utf-8')
            if 'devops' in config_parser:
                config['username'] = config_parser.get('devops', 'username', fallback='')
                config['password'] = config_parser.get('devops', 'password', fallback='')
                config['kb_package'] = config_parser.get('devops', 'kb_package', fallback='')
            logger.info(f"读取配置文件成功: {config_file}")
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
    return config

class KBScanReport:
    def __init__(self, username, password, target_package_name, headless=False):
        """
        初始化KBScanReport实例
        
        Args:
            username: 登录用户名
            password: 登录密码
            target_package_name: 目标KB包名称
            headless: 是否使用无头模式
        """
        self.username = username
        self.password = password
        self.target_package_name = target_package_name
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        """
        进入上下文管理器
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器，关闭浏览器
        """
        await self.close()
    
    async def close(self):
        """
        关闭所有资源
        """
        try:
            # 按照正确的顺序关闭资源
            if self.page:
                try:
                    await self.page.close()
                    logger.info("页面关闭成功")
                except Exception as e:
                    logger.error(f"关闭页面时出错: {e}")
            
            if self.context:
                try:
                    await self.context.close()
                    logger.info("上下文关闭成功")
                except Exception as e:
                    logger.error(f"关闭上下文时出错: {e}")
            
            if self.browser:
                try:
                    await self.browser.close()
                    logger.info("浏览器关闭成功")
                except Exception as e:
                    logger.error(f"关闭浏览器时出错: {e}")
            
            if self.playwright:
                try:
                    await self.playwright.stop()
                    logger.info("Playwright实例关闭成功")
                except Exception as e:
                    logger.error(f"关闭Playwright实例时出错: {e}")
            
            logger.info("所有资源关闭完成")
        except Exception as e:
            logger.error(f"关闭资源时出错: {e}")
    
    async def launch_browser(self):
        """
        启动浏览器
        """
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            logger.info("浏览器启动成功")
            return True
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            # 确保在失败时清理资源
            await self.close()
            return False
    
    async def login(self):
        """
        登录DevOps平台
        """
        try:
            # 导航到登录页面
            await self.page.goto("http://devops.sangfor.com/artifacts/scan/2665/table", timeout=60000)
            logger.info("导航到登录页面成功")
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            
            # 处理服务异常提示弹窗（如果存在）
            try:
                # 查找并关闭服务异常提示弹窗
                error_popup_close = self.page.get_by_role("button", name="×").or_(self.page.locator("button[aria-label='Close']"))
                if await error_popup_close.is_visible(timeout=5000):
                    await error_popup_close.click()
                    logger.info("关闭服务异常提示弹窗")
                    await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception as e:
                logger.warning(f"关闭服务异常弹窗失败: {e}")
            
            # 处理版本更新提示框的取消按钮
            try:
                # 使用更精确的选择器查找取消按钮
                cancel_button = self.page.get_by_role("button", name="取消").or_(self.page.locator("button").filter(has_text="取消"))
                if await cancel_button.is_visible(timeout=10000):
                    await cancel_button.click()
                    logger.info("点击取消按钮")
                    await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                else:
                    # 尝试查找其他可能的取消按钮
                    alt_cancel_buttons = self.page.locator("button").filter(has_text="取消")
                    count = await alt_cancel_buttons.count()
                    if count > 0:
                        await alt_cancel_buttons.first.click()
                        logger.info("点击备选取消按钮")
                        await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception as e:
                logger.warning(f"取消按钮操作失败: {e}")
                
                # 打印页面上所有按钮，便于调试
                try:
                    all_buttons = self.page.locator("button").all()
                    if all_buttons:
                        logger.info("页面上的按钮:")
                        for i, btn in enumerate(all_buttons):
                            try:
                                btn_text = await btn.text_content()
                                logger.info(f"按钮 {i+1}: {btn_text}")
                            except Exception:
                                pass
                except Exception:
                    pass
            
            # 点击用户名密码登录
            try:
                login_button = self.page.get_by_text("用户名密码登录")
                if await login_button.is_visible(timeout=10000):
                    await login_button.click()
                    logger.info("点击用户名密码登录")
                    await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception as e:
                logger.warning(f"用户名密码登录按钮操作失败: {e}")
            
            # 填写用户名和密码
            try:
                username_input = self.page.get_by_role("textbox", name="请输入用户名（工号）, 如： w12345")
                await username_input.wait_for(state="visible", timeout=10000)
                await username_input.fill(self.username)
                logger.info("填写用户名成功")
                
                password_input = self.page.get_by_role("textbox", name="请输入密码")
                await password_input.wait_for(state="visible", timeout=10000)
                await password_input.fill(self.password)
                logger.info("填写密码成功")
            except Exception as e:
                logger.error(f"填写登录信息失败: {e}")
                return False
            
            # 点击登录按钮
            try:
                submit_button = self.page.get_by_role("button", name="登录")
                await submit_button.wait_for(state="visible", timeout=10000)
                await submit_button.click()
                logger.info("提交登录信息")
            except Exception as e:
                logger.error(f"点击登录按钮失败: {e}")
                return False
            
            # 等待登录完成
            await self.page.wait_for_load_state("networkidle", timeout=60000)
            
            # 检查登录是否成功（通过检查是否还在登录页面）
            current_url = self.page.url
            if "login" in current_url.lower() or "auth" in current_url.lower():
                logger.error("登录失败，可能是用户名或密码错误")
                return False
            
            logger.info("登录成功")
            return True
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    async def find_and_open_report(self):
        """
        查找目标KB包并打开报告
        """
        try:
            # 等待表格加载
            logger.info("等待表格加载...")
            await self.page.wait_for_selector('tr.ix-table-row', timeout=60000)
            logger.info("表格加载完成")
            
            # 等待网络空闲
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            
            # 获取所有表格行
            rows = await self.page.locator('tr.ix-table-row').all()
            logger.info(f"找到 {len(rows)} 行数据")
            
            # 遍历行查找目标KB包
            found = False
            for index, row in enumerate(rows):
                try:
                    # 获取行中的所有单元格
                    cells = await row.locator('td').all()
                    
                    # 遍历单元格查找包含KB包名称的单元格
                    for cell_index, cell in enumerate(cells):
                        try:
                            cell_text = await cell.text_content()
                            if cell_text and "KB-WACAP-" in cell_text:
                                package_name = cell_text.strip()
                                logger.info(f"检查第 {index + 1} 行, 第 {cell_index + 1} 列: {package_name}")
                                
                                # 检查是否匹配目标KB包
                                if self.target_package_name in package_name:
                                    logger.info(f"找到目标KB包: {package_name}")
                                    found = True
                                    
                                    # 查找并点击报告按钮
                                    try:
                                        # 使用更精确的选择器查找报告按钮
                                        report_button = row.locator('button').filter(has_text="报告")
                                        if await report_button.is_visible(timeout=10000):
                                            logger.info("找到报告按钮")
                                            await report_button.click()
                                            logger.info("点击报告按钮成功")
                                            
                                            # 等待页面加载完毕
                                            logger.info("等待报告页面加载...")
                                            await self.page.wait_for_load_state("networkidle", timeout=60000)
                                            await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                                            
                                            # 创建KB_photo文件夹
                                            import os
                                            screenshot_dir = "KB_photo"
                                            if not os.path.exists(screenshot_dir):
                                                os.makedirs(screenshot_dir)
                                                logger.info(f"创建文件夹: {screenshot_dir}")
                                            
                                            # 生成截图文件名
                                            import time
                                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                                            screenshot_name = f"{screenshot_dir}\\{self.target_package_name}_{timestamp}.png"
                                            
                                            # 截图并保存
                                            await self.page.screenshot(path=screenshot_name, full_page=True)
                                            logger.info(f"截图保存成功: {screenshot_name}")
                                            
                                            return True
                                        else:
                                            logger.warning("报告按钮不可见")
                                    except Exception as e:
                                        logger.error(f"点击报告按钮失败: {e}")
                                        # 尝试查找所有按钮
                                        buttons = await row.locator('button').all()
                                        logger.info(f"行中有 {len(buttons)} 个按钮")
                                        for btn_index, btn in enumerate(buttons):
                                            btn_text = await btn.text_content()
                                            logger.info(f"按钮 {btn_index + 1}: {btn_text}")
                            
                        except Exception as e:
                            logger.error(f"处理单元格时出错: {e}")
                            continue
                except Exception as e:
                    logger.error(f"处理第 {index + 1} 行时出错: {e}")
                    continue
            
            if found:
                logger.warning("找到目标KB包但无法点击报告按钮")
            else:
                logger.warning(f"未找到目标KB包: {self.target_package_name}")
                
                # 尝试打印前几行的内容，以便调试
                logger.info("打印前5行数据以供调试:")
                for i, row in enumerate(rows[:5]):
                    try:
                        cells = await row.locator('td').all()
                        row_data = []
                        for cell in cells[:3]:  # 只打印前3列
                            cell_text = await cell.text_content()
                            if cell_text:
                                row_data.append(cell_text.strip()[:50])  # 限制长度
                        logger.info(f"第 {i + 1} 行: {', '.join(row_data)}")
                    except Exception as e:
                        logger.error(f"打印第 {i + 1} 行时出错: {e}")
            
            return False
        except Exception as e:
            logger.error(f"查找KB包时出错: {e}")
            return False

async def main(username, password, target_package_name, headless=False):
    """
    主函数
    
    Args:
        username: 登录用户名
        password: 登录密码
        target_package_name: 目标KB包名称
        headless: 是否使用无头模式
    """
    async with KBScanReport(username, password, target_package_name, headless) as kb_scanner:
        # 启动浏览器
        if not await kb_scanner.launch_browser():
            return False
        
        # 登录
        if not await kb_scanner.login():
            return False
        
        # 查找并打开报告
        return await kb_scanner.find_and_open_report()

def parse_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 命令行参数
    """
    parser = argparse.ArgumentParser(description='KB包扫描报告工具')
    parser.add_argument('-t', '--target', help='目标KB包名称')
    parser.add_argument('-u', '--username', help='登录用户名')
    parser.add_argument('-p', '--password', help='登录密码')
    parser.add_argument('-c', '--config', default='config.ini', help='配置文件路径')
    parser.add_argument('-H', '--headless', action='store_true', help='使用无头模式')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 读取配置文件
    config = read_config(args.config)
    
    # 优先级：命令行参数 > 配置文件
    username = args.username or config.get('username', '')
    password = args.password or config.get('password', '')
    target_package = args.target or config.get('kb_package', '')
    headless = args.headless
    
    # 验证必要参数
    if not username:
        logger.error("请提供用户名")
        exit(1)
    if not password:
        logger.error("请提供密码")
        exit(1)
    if not target_package:
        logger.error("请提供目标KB包名称")
        exit(1)
    
    logger.info(f"开始查找KB包报告: {target_package}")
    logger.info(f"使用无头模式: {headless}")
    
    # 运行主函数
    result = asyncio.run(main(username, password, target_package, headless))
    
    if result:
        logger.info("操作成功完成")
    else:
        logger.error("操作失败")
