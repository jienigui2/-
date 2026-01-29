import asyncio
import json
from playwright.async_api import async_playwright
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def find_and_click_targets(page, download_path, target_number, target_id):
    """
    在页面上查找并点击目标表格行
    
    Args:
        page: Playwright页面实例
        download_path: 下载文件保存路径
        target_number: 目标编号
        target_id: 目标ID
    """
    try:
        # 1. 查找目标编号
        found = False
        
        logger.info(f"查找目标编号: {target_number}")
        
        # 等待表格加载
        await page.wait_for_selector('div.x-grid3-row', timeout=30000)
        logger.info("表格加载完成")
        
        # 获取所有行
        rows = await page.query_selector_all('div.x-grid3-row')
        logger.info(f"找到 {len(rows)} 行数据")
        
        # 遍历每一行
        for index, row in enumerate(rows):
            try:
                # 获取行内所有单元格
                cells = await row.query_selector_all('div.x-grid3-cell-inner')
                
                # 检查每个单元格
                for cell_index, cell in enumerate(cells):
                    try:
                        # 获取单元格内容
                        cell_text = await cell.text_content()
                        
                        # 检查是否是目标编号
                        if cell_text and target_number in cell_text:
                            logger.info(f"找到目标编号: {cell_text.strip()}")
                            # 点击该单元格
                            await cell.click()
                            logger.info("点击目标编号成功")
                            found = True
                            break  # 找到后停止遍历
                    except Exception as e:
                        logger.error(f"处理单元格 {cell_index + 1} 时出错: {e}")
                        continue
                
                if found:
                    break
            except Exception as e:
                logger.error(f"处理行 {index + 1} 时出错: {e}")
                continue
        
        if not found:
            logger.warning(f"未找到目标编号: {target_number}")
        
        # 等待页面加载
        await page.wait_for_load_state("networkidle", timeout=30000)
        
        # 2. 查找目标ID
        id_found = False
        
        logger.info(f"查找目标ID: {target_id}")
        
        # 等待表格加载
        await page.wait_for_selector('div.x-grid3-row', timeout=30000)
        logger.info("第二个表格加载完成")
        
        # 获取所有行
        rows = await page.query_selector_all('div.x-grid3-row')
        logger.info(f"找到 {len(rows)} 行数据")
        
        # 遍历每一行
        for index, row in enumerate(rows):
            try:
                # 获取行内所有单元格
                cells = await row.query_selector_all('div.x-grid3-cell-inner')
                
                # 检查每个单元格
                for cell_index, cell in enumerate(cells):
                    try:
                        # 获取单元格内容
                        cell_text = await cell.text_content()
                        
                        # 检查是否是目标ID
                        if cell_text and cell_text.strip() == target_id:
                            logger.info(f"找到目标ID: {cell_text.strip()}")
                            # 点击该单元格
                            await cell.click()
                            logger.info("点击目标ID成功")
                            
                            # 查找并点击同一行的下载链接
                            try:
                                # 查找同一行的下载KB链接
                                download_kb = await row.query_selector('span.sim-link[actionname="download"]')
                                if download_kb:
                                    logger.info("找到下载KB链接")
                                    # 等待下载完成
                                    async with page.expect_download() as download_info:
                                        await download_kb.click()
                                        logger.info("点击下载KB成功，等待下载完成...")
                                    download = await download_info.value
                                    # 保存到指定目录
                                    save_path = os.path.join(download_path, download.suggested_filename)
                                    await download.save_as(save_path)
                                    logger.info(f"KB文件下载成功: {save_path}")
                                else:
                                    logger.warning("未找到下载KB链接")
                                
                                # 查找同一行的下载KB SIGN链接
                                download_sign = await row.query_selector('span.sim-link[actionname="downloadsign"]')
                                if download_sign:
                                    logger.info("找到下载KB SIGN链接")
                                    # 等待下载完成
                                    async with page.expect_download() as download_info:
                                        await download_sign.click()
                                        logger.info("点击下载KB SIGN成功，等待下载完成...")
                                    download = await download_info.value
                                    # 保存到指定目录
                                    save_path = os.path.join(download_path, download.suggested_filename)
                                    await download.save_as(save_path)
                                    logger.info(f"KB SIGN文件下载成功: {save_path}")
                                else:
                                    logger.warning("未找到下载KB SIGN链接")
                            except Exception as e:
                                logger.error(f"点击下载链接时出错: {e}")
                                import traceback
                                traceback.print_exc()
                            
                            id_found = True
                            break  # 找到后停止遍历
                    except Exception as e:
                        logger.error(f"处理单元格 {cell_index + 1} 时出错: {e}")
                        continue
                
                if id_found:
                    break
            except Exception as e:
                logger.error(f"处理行 {index + 1} 时出错: {e}")
                continue
        
        if not id_found:
            logger.warning(f"未找到目标ID: {target_id}")
        
        return found and id_found
        
    except Exception as e:
        logger.error(f"处理表格时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """
    主函数
    """
    # 从KB_test.json读取配置
    with open('KB_test.json', 'r', encoding='utf-8') as f:
        kb_config = json.load(f)
    
    kb_number = kb_config.get('kb_number')
    target_id = kb_config.get('target_id')
    
    logger.info(f"从配置文件读取: kb_number={kb_number}, target_id={target_id}")
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=['--ignore-certificate-errors', '--disable-web-security']
        )
        
        # 创建下载用的context
        download_path = r"F:\KB"
        # 确保下载目录存在
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            logger.info(f"创建下载目录: {download_path}")
        else:
            logger.info(f"下载目录已存在: {download_path}")
        
        # 打印当前工作目录，用于调试
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"下载路径绝对路径: {os.path.abspath(download_path)}")
        
        # 创建context
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        page.set_default_timeout(60000)  # 增加超时时间
        
        logger.info(f"设置下载路径为: {download_path}")
        
        kb_sign_file = None  # 记录KB SIGN文件路径
        
        try:
            # 访问KB下载页面
            await page.goto('http://10.156.99.96/kb.php#', wait_until='domcontentloaded')
            await page.wait_for_selector('#ext-comp-1016', state='visible')
            
            # 输入KB编号并搜索
            kb_input = page.locator('#ext-comp-1016')
            await kb_input.fill(kb_number)
            await kb_input.press('Enter')
            logger.info(f"搜索KB编号: {kb_number}")
            
            # 等待搜索结果加载
            await page.wait_for_load_state("networkidle", timeout=60000)
            logger.info("搜索结果加载完成")
            
            # 执行表格操作
            success = await find_and_click_targets(page, download_path, kb_number, target_id)
            
            if success:
                logger.info("操作成功完成")
            else:
                logger.error("操作失败")
                
        finally:
            # 关闭浏览器
            await page.close()
            await context.close()
            await browser.close()
            logger.info("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(main())
