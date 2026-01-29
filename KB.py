import os
import sys
import time
from playwright.sync_api import sync_playwright
from pathlib import Path


def main():
    # 获取KB编号 and 网段（从命令行参数）
    if len(sys.argv) < 3:
        print('用法: python KB.py <KB编号> <网段地址>')
        print('例如: python KB.py KB12345 10.156.2.113')
        return
    
    kb_number = sys.argv[1]
    network_address = sys.argv[2]
    
    kb_number = kb_number.strip()
    download_dir = os.path.join('F:\\KB', kb_number)
    os.makedirs(download_dir, exist_ok=True)
    print(f'下载目录: {download_dir}\n')
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=False,
            args=['--ignore-certificate-errors', '--disable-web-security']
        )
        
        # 创建下载用的context
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(30000)
        
        kb_sign_file = None  # 记录KB SIGN文件路径
        
        try:
            # 访问KB下载页面
            page.goto('http://10.156.99.96/kb.php#', wait_until='domcontentloaded')
            page.wait_for_selector('#ext-comp-1016', state='visible')
            
            kb_input = page.locator('#ext-comp-1016')
            kb_input.fill(kb_number)
            kb_input.press('Enter')
            time.sleep(3)
            
            # # 点击包含KB编号的元素
            # page.get_by_text(kb_number).click()
            
            # 下载KB SIGN和KB两个文件
            print('正在下载KB文件...\n')
            
            for file_type in ['下载KB SIGN', '下载KB']:
                try:
                    # 设置下载处理器
                    with page.expect_download(timeout=30000) as download_info:
                        page.get_by_text(file_type, exact=file_type == '下载KB').click(timeout=10000)
                    
                    download = download_info.value
                    save_path = os.path.join(download_dir, download.suggested_filename)
                    download.save_as(save_path)
                    print(f'✓ {file_type}: {download.suggested_filename}')
                    
                    # 记录KB SIGN文件路径
                    if file_type == '下载KB SIGN':
                        kb_sign_file = save_path
                    
                    time.sleep(1)
                except Exception as e:
                    print(f'❌ {file_type} 下载失败: {e}')
            
            print(f'\n✓ 下载完成！文件已保存到 {download_dir}')
            
            # 关闭下载页面的context（清理状态，避免污染登录页面）
            context.close()
            print('已关闭下载页面的浏览器上下文')
            
            # 下载完成后，执行KB更新逻辑
            if kb_sign_file:
                print('\n' + '=' * 50)
                print('开始执行KB更新操作...\n')
                
                # 创建全新的context和page用于登录和更新（避免状态污染）
                update_context = browser.new_context(ignore_https_errors=True)
                update_page = update_context.new_page()
                update_page.set_default_timeout(30000)
                print('已创建新的浏览器上下文')
                
                try:
                    # 切换到更新页面
                    update_page.goto(f'https://{network_address}')
                    time.sleep(2)
                    
                    # 处理证书警告（如果存在）
                    try:
                        update_page.get_by_role('button', name='高级').click(timeout=3000)
                        update_page.get_by_role('link', name=f'继续前往{network_address}（不安全）').click(timeout=3000)
                        time.sleep(2)
                    except Exception:
                        # 无证书警告，继续
                        pass
                    
                    # 输入登录信息
                    print('正在输入账号密码...')
                    update_page.wait_for_selector('#login_user', state='visible', timeout=10000)
                    login_user = update_page.locator('#login_user')
                    login_user.click()
                    login_user.fill('')
                    login_user.fill('admin')
                    print('账号已输入')
                    
                    update_page.wait_for_selector('#login_password', state='visible', timeout=10000)
                    login_password = update_page.locator('#login_password')
                    login_password.click()
                    login_password.fill('')
                    login_password.fill('Qwer1234')
                    print('密码已输入')
                    
                    # 勾选协议并登录
                    update_page.get_by_role('checkbox', name='我已认真阅读并同意').check()
                    print('已勾选同意条款')
                    
                    update_page.get_by_text('登录', exact=True).click()
                    print('已点击登录按钮，等待页面加载...')
                    
                    # 额外等待2秒，让页面的JavaScript逻辑（路由、权限验证等）有足够时间完成
                    print('等待页面JavaScript处理完成...')
                    time.sleep(2)
                    print('✓ 页面处理完成')
                    
                    print('继续跳转到升级页面...')
                    
                    # 跳转到固件升级页面（使用正确的URL路径）
                    update_page.goto(f'https://{network_address}/WLAN/index.php#/maintain/DeviceUpdate',
                                    wait_until='domcontentloaded',
                                    timeout=30000)
                    print('✓ 已跳转到升级页面')
                    
                    # 等待升级页面加载
                    time.sleep(5)
                    print('✓ 升级页面已加载')
                    
                    # 勾选"补丁包升级"单选框
                    print('正在勾选"补丁包升级"...')
                    update_page.get_by_role('radio', name='补丁包升级').check()
                    print('✓ 已勾选"补丁包升级"')
                    time.sleep(3)
                    
                    # 点击上传按钮
                    print('正在点击上传按钮...')
                    update_page.locator('#ext-gen111').click()
                    print('✓ 已点击上传按钮')
                    time.sleep(3)
                    
                    # 点击选择文件输入框
                    print('正在选择文件...')
                    update_page.get_by_role('textbox', name='请选择本地补丁包文件(.tgz)').click()
                    print('✓ 已点击文件选择框')
                    time.sleep(2)
                    
                    # 上传KB SIGN文件
                    print('正在上传补丁包...')
                    file_input = update_page.locator('input[type="file"]').first
                    if file_input.is_visible():
                        file_input.set_input_files(kb_sign_file)
                        print(f'✓ 已上传补丁包: {os.path.basename(kb_sign_file)}')
                        time.sleep(5)  # 等待上传完成
                    else:
                        print('❌ 未找到文件上传输入框')
                    
                    # 点击"开始升级"按钮
                    print('正在点击"开始升级"按钮...')
                    update_page.get_by_role('button', name='开始升级').click()
                    print('✓ 已点击"开始升级"按钮')
                    time.sleep(3)
                    
                    # 点击"确定"按钮
                    print('正在点击"确定"按钮...')
                    update_page.get_by_role('button', name='确定').click()
                    print('✓ 已点击"确定"按钮')
                    
                    # 停5秒确认更新
                    print('等待5秒确认更新...')
                    time.sleep(5)
                    
                    # 刷新页面
                    print('刷新页面...')
                    update_page.reload(wait_until='domcontentloaded')
                    print('✓ 页面已刷新')
                    
                    print('\n✓ KB更新操作完成！')
                    print('浏览器保持打开状态，按Ctrl+C退出...')
                    
                    # 保持浏览器打开，等待用户手动退出
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print('\n用户中断，退出程序')
                finally:
                    # 关闭更新用的context
                    update_context.close()
                    print('已关闭更新操作的浏览器上下文')
            else:
                print('❌ 未找到KB SIGN文件，跳过更新操作')
                
        except Exception as error:
            print(f'❌ 错误: {error}')
        finally:
            # 关闭浏览器
            try:
                context.close()
            except:
                pass
            browser.close()


if __name__ == "__main__":
    main()