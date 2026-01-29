import os
import ssl
from ftplib import FTP_TLS

class FTP_TLS_SSLReuse(FTP_TLS):
    """
    支持SSL会话重用的FTP_TLS子类
    解决"522 SSL connection failed; session reuse required"错误
    """
    def __init__(self, *args, **kwargs):
        # 创建SSL上下文
        self.ssl_context = ssl.create_default_context()
        # 禁用证书验证（由于服务器使用弱证书）
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        # 传递上下文给父类
        kwargs['context'] = self.ssl_context
        super().__init__(*args, **kwargs)
        self._ssl_session = None
    
    def auth(self):
        """启动TLS会话并保存会话以便重用"""
        # 调用父类auth方法
        super().auth()
        # 获取SSL会话
        if hasattr(self.sock, '_sslobj'):
            self._ssl_session = self.sock._sslobj.session
        return self.sock
    
    def ntransfercmd(self, cmd, rest=None):
        """重写ntransfercmd以在数据连接中重用SSL会话"""
        # 保存当前会话
        session = self._ssl_session
        
        # 调用FTP类的ntransfercmd方法（绕过FTP_TLS的实现）
        conn, size = super(FTP_TLS, self).ntransfercmd(cmd, rest)
        
        # 如果有保存的会话，手动进行SSL包装
        if session:
            try:
                # 使用保存的会话创建新的SSL连接
                ssl_conn = self.ssl_context.wrap_socket(
                    conn,
                    server_hostname=self.host,
                    session=session
                )
                # 替换原始连接
                conn = ssl_conn
                # 保存新的会话
                if hasattr(conn, '_sslobj'):
                    self._ssl_session = conn._sslobj.session
            except Exception as e:
                print(f"设置SSL会话时出错: {e}")
                # 如果失败，关闭连接
                conn.close()
                raise
        
        return conn, size

def ftp_download_specific_file(remote_file_path=None, local_file_path=None):
    """
    连接FTP服务器并下载指定文件
    使用显式SSL连接 (FTP over TLS)
    与FlashFXP中使用完全相同的配置
    
    参数:
    remote_file_path (str): 远程文件路径（可选）
    local_file_path (str): 本地保存路径（可选）
    """
    # FTP服务器配置
    ftp_server = "200.200.0.16"
    ftp_port = 21
    ftp_user = "10000"
    ftp_pass = "BFHJFl1nhE"
    
    # 下载配置（与FlashFXP中完全相同）
    # 从FlashFXP截图中获取的路径和文件名
    local_dir = "D:/版本"  # 本地保存目录（与FlashFXP中相同）
    
    # 创建本地下载目录
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        print(f"创建本地下载目录: {local_dir}")
    
    ftp = None
    download_success = False
    
    try:
        print(f"正在连接FTP服务器: {ftp_server}:{ftp_port}")
        
        # 创建支持SSL会话重用的FTP_TLS实例
        ftp = FTP_TLS_SSLReuse()
        ftp.set_debuglevel(0)  # 禁用调试信息，使输出更清晰
        
        # 连接服务器
        ftp.connect(ftp_server, ftp_port)
        print("成功连接到FTP服务器")
        
        # 启动TLS
        ftp.auth()
        print("TLS会话已启动")
        
        # 登录
        ftp.login(ftp_user, ftp_pass)
        print("登录成功")
        
        # 设置为被动模式
        ftp.set_pasv(True)
        print("设置为被动模式")
        
        # 设置数据连接为TLS
        ftp.prot_p()
        print("已启用数据连接TLS保护")
        
        # 如果没有指定远程文件路径，尝试导航到默认目录
        if not remote_file_path:
            # 尝试导航到正式版本目录
            print("\n尝试导航到正式版本目录:")
            try:
                ftp.cwd("正式版本")
                print("成功切换到 正式版本")
                
                # 尝试导航到NMC目录
                print("\n尝试导航到NMC目录:")
                try:
                    ftp.cwd("NMC")
                    print("成功切换到 NMC")
                    
                    # 尝试导航到NMC3.12.0目录
                    print("\n尝试导航到NMC3.12.0目录:")
                    try:
                        ftp.cwd("NMC3.12.0")
                        print("成功切换到 NMC3.12.0")
                        
                        # 尝试导航到02-虚拟机vNMC目录
                        print("\n尝试导航到02-虚拟机vNMC目录:")
                        try:
                            ftp.cwd("02-虚拟机vNMC")
                            print("成功切换到 02-虚拟机vNMC")
                            
                            # 尝试导航到01-客户端升级包目录
                            print("\n尝试导航到01-客户端升级包目录:")
                            try:
                                ftp.cwd("01-客户端升级包")
                                print("成功切换到 01-客户端升级包")
                                
                                # 列出目录内容
                                print("\n目录内容:")
                                try:
                                    stat_info = ftp.sendcmd('STAT .')
                                    print(f"STAT命令结果: {stat_info}")
                                except Exception as e:
                                    print(f"获取目录信息失败: {e}")
                                    
                            except Exception as e:
                                print(f"导航到01-客户端升级包目录失败: {e}")
                                
                        except Exception as e:
                            print(f"导航到02-虚拟机vNMC目录失败: {e}")
                            
                    except Exception as e:
                        print(f"导航到NMC3.12.0目录失败: {e}")
                        
                except Exception as e:
                    print(f"导航到NMC目录失败: {e}")
                    
            except Exception as e:
                print(f"导航目录失败: {e}")
        
        # 解析远程文件路径
        if remote_file_path:
            # 分离目录和文件名
            remote_dir = os.path.dirname(remote_file_path)
            remote_file = os.path.basename(remote_file_path)
            
            # 如果有目录部分，导航到该目录
            if remote_dir and remote_dir != '.':
                print(f"\n尝试导航到目录: {remote_dir}")
                try:
                    ftp.cwd(remote_dir)
                    print(f"成功切换到 {remote_dir}")
                except Exception as e:
                    print(f"导航到目录失败: {e}")
                    return
        else:
            # 默认下载Temporary Files.lnk文件
            remote_file = "Temporary Files.lnk"
        
        # 确定本地保存路径
        if local_file_path:
            # 如果指定了完整路径，使用它
            save_path = local_file_path
        else:
            # 否则，使用默认目录和远程文件名
            save_path = os.path.join(local_dir, remote_file)
        
        # 确保本地目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # 尝试下载文件
        print(f"\n尝试下载文件: {remote_file}")
        print(f"保存到: {save_path}")
        
        try:
            # 尝试下载
            print(f"尝试使用命令: RETR {remote_file}")
            
            with open(save_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_file}', f.write)
            
            # 检查文件是否下载成功
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                file_size = os.path.getsize(save_path)
                file_size_mb = file_size / (1024 * 1024)
                print(f"\n✓ 下载成功! 文件大小: {file_size_mb:.2f} MB")
                print(f"文件已保存到: {save_path}")
                download_success = True
            else:
                print(f"\n✗ 下载失败! 文件未找到或为空")
                # 删除空文件
                if os.path.exists(save_path):
                    os.remove(save_path)
        except Exception as e:
            print(f"\n✗ 下载过程中发生错误: {e}")
            # 清理可能创建的空文件
            if os.path.exists(save_path):
                os.remove(save_path)
        
        if not download_success:
            print("\n下载失败")
            print("请检查以下内容:")
            print("1. 文件是否存在于FTP服务器上")
            print("2. 文件名格式是否正确")
            print("3. 您是否有足够的权限访问该文件")
        
        # 退出
        ftp.quit()
        print("\nFTP连接已关闭")
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ftp:
            try:
                ftp.quit()
            except:
                pass

def list_ftp_directory(remote_dir="."):
    """
    列出FTP服务器上指定目录的内容
    
    参数:
    remote_dir (str): 远程目录路径
    """
    # FTP服务器配置
    ftp_server = "200.200.0.16"
    ftp_port = 21
    ftp_user = "10000"
    ftp_pass = "BFHJFl1nhE"
    
    ftp = None
    
    try:
        print(f"正在连接FTP服务器: {ftp_server}:{ftp_port}")
        
        # 创建支持SSL会话重用的FTP_TLS实例
        ftp = FTP_TLS_SSLReuse()
        ftp.set_debuglevel(0)  # 禁用调试信息
        
        # 连接服务器
        ftp.connect(ftp_server, ftp_port)
        print("成功连接到FTP服务器")
        
        # 启动TLS
        ftp.auth()
        print("TLS会话已启动")
        
        # 登录
        ftp.login(ftp_user, ftp_pass)
        print("登录成功")
        
        # 设置为被动模式
        ftp.set_pasv(True)
        print("设置为被动模式")
        
        # 设置数据连接为TLS
        ftp.prot_p()
        print("已启用数据连接TLS保护")
        
        # 导航到指定目录
        if remote_dir and remote_dir != '.':
            print(f"\n尝试导航到目录: {remote_dir}")
            try:
                ftp.cwd(remote_dir)
                print(f"成功切换到 {remote_dir}")
            except Exception as e:
                print(f"导航到目录失败: {e}")
                return
        
        # 列出目录内容
        print(f"\n目录内容 ({remote_dir}):")
        try:
            stat_info = ftp.sendcmd('STAT .')
            print(stat_info)
            
            # 解析STAT结果，提取文件和目录信息
            lines = stat_info.split('\n')
            files = []
            dirs = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('d'):
                    # 目录
                    parts = line.split()
                    if parts:
                        dirs.append(parts[-1])
                elif line.startswith('-'):
                    # 文件
                    parts = line.split()
                    if parts:
                        files.append((parts[-1], parts[4]))  # 文件名和大小
            
            if dirs:
                print("\n目录:")
                for d in dirs:
                    print(f"  - {d}")
            
            if files:
                print("\n文件:")
                for f, size in files:
                    print(f"  - {f} (大小: {size} 字节)")
        
        except Exception as e:
            print(f"获取目录信息失败: {e}")
        
        # 退出
        ftp.quit()
        print("\nFTP连接已关闭")
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ftp:
            try:
                ftp.quit()
            except:
                pass

if __name__ == "__main__":
    print("FTP文件下载工具")
    print("=" * 60)
    
    # 显示菜单
    print("\n请选择操作:")
    print("1. 列出FTP服务器上的文件和目录")
    print("2. 下载指定文件")
    print("3. 使用默认配置下载文件")
    
    choice = input("\n输入选项编号: ")
    
    if choice == '1':
        # 列出目录
        remote_dir = input("请输入要列出的远程目录路径 (默认为根目录): ")
        if not remote_dir:
            remote_dir = "."
        list_ftp_directory(remote_dir)
    elif choice == '2':
        # 下载指定文件
        remote_file = input("请输入远程文件路径: ")
        local_file = input("请输入本地保存路径 (可选): ")
        if not local_file:
            local_file = None
        ftp_download_specific_file(remote_file, local_file)
    elif choice == '3':
        # 使用默认配置
        print("\n使用默认配置下载文件...")
        ftp_download_specific_file()
    else:
        print("无效的选项")
    
    print("=" * 60)
    print("操作完成")