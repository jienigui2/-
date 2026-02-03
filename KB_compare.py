import requests
import json
import os
import time
import configparser


def load_config():
    """
    从all.ini加载KB登录凭证
    
    Returns:
        dict: 包含username和password的配置，失败时返回None
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
        
        username = config_parser.get('kb_compare', 'kb_username', fallback='')
        password = config_parser.get('kb_compare', 'kb_password', fallback='')
        
        if not all([username, password]):
            print("✗ 配置文件中缺少kb_username或kb_password")
            return None
            
        return {
            'username': username,
            'password': password
        }
        
    except Exception as e:
        print(f"✗ 读取配置文件失败: {e}")
        return None


def kb_login(username=None, password=None):
    """
    KB系统登录函数
    
    Args:
        username: 用户名（可选，如果不提供则从配置文件读取）
        password: 密码（可选，如果不提供则从配置文件读取）
        
    Returns:
        dict: 登录响应数据，包含token等信息
        None: 登录失败时返回None
    """
    # 如果没有传入参数，从配置文件读取
    if username is None or password is None:
        credentials = load_config()
        if credentials:
            username = credentials.get('username')
            password = credentials.get('password')
        else:
            return None
    url = "http://kb.sundray.work/api/users/login"
    
    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "http://kb.sundray.work",
        "Referer": "http://kb.sundray.work/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
    }
    
    # 请求体数据
    data = {
        "username": username,
        "password": password
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
            timeout=30,
            verify=False  # 对应curl的--insecure参数，禁用SSL证书验证
        )
        
        # 检查响应状态
        if response.status_code == 201:
            result = response.json()
            print(f"✓ 登录成功！")
            
            # 保存登录响应到KB_login_token.json
            try:
                token_file = "KB_login_token.json"
                with open(token_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✓ 登录响应已保存到 {token_file}")
            except Exception as e:
                print(f"⚠ 保存token文件失败: {e}")
            
            return result
        else:
            print(f"✗ 登录失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"✗ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"✗ 连接错误，请检查网络或服务器地址")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ 解析响应JSON失败: {e}")
        print(f"响应内容: {response.text}")
        return None
    except Exception as e:
        print(f"✗ 登录请求失败: {e}")
        return None


def load_token():
    """
    从KB_login_token.json加载token
    
    Returns:
        str: token字符串，失败时返回None
    """
    token_file = "KB_login_token.json"
    
    # 检查token文件是否存在
    if not os.path.exists(token_file):
        print(f"✗ Token文件 {token_file} 不存在，请先运行 KB_login.py 登录")
        return None
    
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 获取token
        token = data.get('token')
        if not token:
            print("✗ Token文件中未找到token字段")
            return None
            
        return token
        
    except json.JSONDecodeError as e:
        print(f"✗ 解析token文件JSON失败: {e}")
        return None
    except Exception as e:
        print(f"✗ 读取token文件失败: {e}")
        return None


def load_compare_config():
    """
    从all.ini加载KB包对比配置
    
    Returns:
        dict: 包含history_packages和pending_packages的配置，失败时返回None
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
        
        # 读取并解析历史包列表（支持逗号分隔的多个包）
        history_packages_str = config_parser.get('kb_compare', 'history_packages', fallback='')
        history_packages = []
        if history_packages_str:
            for package in history_packages_str.split(','):
                package = package.strip()
                if package:
                    history_packages.append({"name": package})
        
        # 读取并解析待对比包列表（支持逗号分隔的多个包）
        pending_packages_str = config_parser.get('kb_compare', 'pending_packages', fallback='')
        pending_packages = []
        if pending_packages_str:
            for package in pending_packages_str.split(','):
                package = package.strip()
                if package:
                    pending_packages.append({"name": package})
        
        if not history_packages or not pending_packages:
            print("✗ 配置文件中缺少有效的history_packages或pending_packages")
            return None
            
        return {
            "history_packages": history_packages,
            "pending_packages": pending_packages
        }
        
    except Exception as e:
        print(f"✗ 读取配置文件失败: {e}")
        return None


def kb_compare(history_packages=None, pending_packages=None, token=None):
    """
    KB包对比函数
    
    Args:
        history_packages: 历史包列表，格式为 [{"name": "包名1"}, {"name": "包名2"}]
                        （可选，如果不提供则从KB_login.json读取）
        pending_packages: 待对比包列表，格式同上
                        （可选，如果不提供则从KB_login.json读取）
        token: 认证token（可选，如果不提供则从KB_login_token.json读取，若不存在或过期则自动登录）
        
    Returns:
        dict: 对比结果响应数据
        None: 对比失败时返回None
    """
    # 如果没有传入token，从token文件读取
    if token is None:
        token = load_token()
        # 无论token是否存在，都尝试自动登录获取新token
        # 这样可以避免token过期的问题
        print("尝试自动登录获取新token...")
        login_result = kb_login()
        if login_result:
            token = login_result.get('token')
            if not token:
                print("✗ 登录成功但未获取到token")
                return None
            print("✓ 登录成功并获取到新token")
        else:
            return None
    
    # 如果没有传入包列表，从配置文件读取
    if history_packages is None or pending_packages is None:
        compare_config = load_compare_config()
        if compare_config:
            if history_packages is None:
                history_packages = compare_config.get('history_packages')
            if pending_packages is None:
                pending_packages = compare_config.get('pending_packages')
        else:
            return None
    
    url = "http://kb.sundray.work/api/kb_services/kb_compare"
    
    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": f"vue_admin_template_token={token}; sidebarStatus=0",
        "Origin": "http://kb.sundray.work",
        "Referer": "http://kb.sundray.work/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "X-Token": token
    }
    
    # 请求体数据
    data = {
        "historyPackages": history_packages or [],
        "pendingPackages": pending_packages or []
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
            timeout=30,
            verify=False  # 对应curl的--insecure参数，禁用SSL证书验证
        )
        
        # 检查响应状态
        if response.status_code == 201:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✓ KB对比成功！获取到task_id: {task_id}")
            
            # 保存对比结果到KB_compare.json
            try:
                compare_result_file = "KB_compare.json"
                with open(compare_result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✓ 对比结果已保存到 {compare_result_file}")
            except Exception as e:
                print(f"⚠ 保存对比结果文件失败: {e}")
            
            # 等待5秒后开始查询状态
            print(f"\n等待5秒后查询对比状态...")
            time.sleep(5)
            
            # 轮询查询对比状态直到完成
            max_polls = 120  # 最多轮询120次 (120 * 5秒 = 10分钟)
            poll_count = 0
            
            while poll_count < max_polls:
                poll_count += 1
                print(f"\n第 {poll_count} 次查询对比状态...")
                
                # 查询对比状态
                state_result = query_compare_state(task_id, token)
                
                if not state_result:
                    print(f"✗ 查询对比状态失败")
                    break
                
                # 检查状态
                state = state_result.get('state')
                print(f"当前状态: {state}")
                
                # 保存查询结果
                try:
                    state_file = "KB_compare_state.json"
                    with open(state_file, 'w', encoding='utf-8') as f:
                        json.dump(state_result, f, indent=2, ensure_ascii=False)
                    print(f"✓ 对比状态已保存到 {state_file}")
                except Exception as e:
                    print(f"⚠ 保存对比状态文件失败: {e}")
                
                # 判断是否完成
                if state == "已完成":
                    print(f"\n✓ KB对比任务已完成！")
                    return state_result
                else:
                    print(f"对比任务未完成，等待5秒后继续查询...")
                    time.sleep(5)
            
            if poll_count >= max_polls:
                print(f"\n⚠ 已达到最大轮询次数（{max_polls}次），退出轮询")
            
            return state_result
        else:
            print(f"✗ KB对比失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"✗ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"✗ 连接错误，请检查网络或服务器地址")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ 解析响应JSON失败: {e}")
        print(f"响应内容: {response.text}")
        return None
    except Exception as e:
        print(f"✗ KB对比请求失败: {e}")
        return None


def query_compare_state(task_id, token):
    """
    查询KB对比状态
    
    Args:
        task_id: 任务ID
        token: 认证token
        
    Returns:
        dict: 对比状态响应数据
        None: 查询失败时返回None
    """
    url = "http://kb.sundray.work/api/kb_services/kb_compare_state"
    
    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": f"vue_admin_template_token={token}; sidebarStatus=0",
        "Origin": "http://kb.sundray.work",
        "Referer": "http://kb.sundray.work/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "X-Token": token
    }
    
    # 请求体数据
    data = {
        "id": task_id
    }
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
            timeout=30,
            verify=False
        )
        
        # 检查响应状态
        if response.status_code == 201:
            result = response.json()
            print(f"✓ 状态查询成功！")
            return result
        else:
            print(f"✗ 状态查询失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"✗ 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"✗ 连接错误，请检查网络或服务器地址")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ 解析响应JSON失败: {e}")
        print(f"响应内容: {response.text}")
        return None
    except Exception as e:
        print(f"✗ 状态查询失败: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    # 方式1：从配置文件自动读取（推荐）
    print("开始KB包对比（从配置文件读取）...")
    result = kb_compare()
    
    # 方式2：手动传入包列表
    # print("开始KB包对比...")
    # history_packages = [{"name": "KB-WACAP-20260116-Wlan-2025111403-001"}]
    # pending_packages = [{"name": "KB-WACAP-20260116-Wlan-2025111403-001"}]
    # result = kb_compare(history_packages, pending_packages)
    
    if result:
        print("\n对比结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))