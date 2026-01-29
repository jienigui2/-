import requests
import json
import os


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


def load_task_id():
    """
    从KB_compare.json加载task_id
    
    Returns:
        str: task_id字符串，失败时返回None
    """
    compare_file = "KB_compare.json"
    
    # 检查对比结果文件是否存在
    if not os.path.exists(compare_file):
        print(f"✗ 对比结果文件 {compare_file} 不存在，请先运行 KB_compare.py 进行对比")
        return None
    
    try:
        with open(compare_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 获取task_id
        task_id = data.get('task_id')
        if not task_id:
            print("✗ 对比结果文件中未找到task_id字段")
            return None
            
        return task_id
        
    except json.JSONDecodeError as e:
        print(f"✗ 解析对比结果文件JSON失败: {e}")
        return None
    except Exception as e:
        print(f"✗ 读取对比结果文件失败: {e}")
        return None


def kb_compare_state(task_id=None, token=None):
    """
    KB包对比状态查询函数
    
    Args:
        task_id: 任务ID（可选，如果不提供则从KB_compare.json读取）
        token: 认证token（可选，如果不提供则从KB_login_token.json读取）
        
    Returns:
        dict: 对比状态响应数据
        None: 查询失败时返回None
    """
    # 如果没有传入task_id，从对比结果文件读取
    if task_id is None:
        task_id = load_task_id()
        if not task_id:
            return None
    
    # 如果没有传入token，从token文件读取
    if token is None:
        token = load_token()
        if not token:
            return None
    
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
            verify=False  # 对应curl的--insecure参数，禁用SSL证书验证
        )
        
        # 检查响应状态
        if response.status_code == 201:
            result = response.json()
            print(f"✓ KB对比状态查询成功！")
            
            # 保存对比状态结果到KB_compare_state.json
            try:
                state_file = "KB_compare_state.json"
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✓ 对比状态已保存到 {state_file}")
            except Exception as e:
                print(f"⚠ 保存对比状态文件失败: {e}")
            
            return result
        else:
            print(f"✗ KB对比状态查询失败，状态码: {response.status_code}")
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
        print(f"✗ KB对比状态查询失败: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    # 方式1：从文件自动读取task_id和token（推荐）
    print("开始查询KB对比状态（从文件读取）...")
    result = kb_compare_state()
    
    # 方式2：手动传入task_id
    # print("开始查询KB对比状态...")
    # result = kb_compare_state(task_id="1769649917_55115")
    
    if result:
        print("\n对比状态结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))