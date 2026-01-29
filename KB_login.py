import requests
import json
import os


def load_config():
    """
    从配置文件加载KB登录凭证
    
    Returns:
        dict: 包含username和password的配置，失败时返回None
    """
    config_file = "KB_login.json"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"✗ 配置文件 {config_file} 不存在")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 验证配置文件结构
        kb_credentials = config.get('kb_credentials', {})
        username = kb_credentials.get('username')
        password = kb_credentials.get('password')
        
        if not all([username, password]):
            print("✗ 配置文件中缺少username或password")
            return None
            
        return kb_credentials
        
    except json.JSONDecodeError as e:
        print(f"✗ 解析配置文件JSON失败: {e}")
        return None
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


# 使用示例
if __name__ == "__main__":
    # 测试登录（从配置文件读取）
    result = kb_login()
    if result:
        print("登录响应数据:")
        print(json.dumps(result, indent=2, ensure_ascii=False))