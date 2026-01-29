import requests
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_defect_by_key(defect_key):
    """
    根据缺陷编号获取缺陷详细信息
    
    Args:
        defect_key (str): 缺陷编号
    
    Returns:
        dict: 返回的JSON数据或错误信息
    """
    # API URL（动态生成时间戳）
    import time
    url = f"https://td.sangfor.com/api/v1/defect/by_key/{defect_key}?_t={int(time.time() * 1000)}"
    
    # Cookie字符串
    cookie_str = "ep_jwt_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjU5MjcyIiwiZGlzcGxheV9uYW1lIjoiXHU4YzJkXHU0ZmNhXHU2NzcwNTkyNzIiLCJhY2Nlc3NfaXAiOiIxMC43Mi4xMC41MSIsImlhdCI6MTc2ODg5OTk0MywiZXhwIjoxNzY5NTA0NzQzLCJpc19hZG1pbiI6ZmFsc2UsImVtYWlsIjoiNTkyNzJAc2FuZ2Zvci5jb20ifQ.eUWE6J2MmBtcYancc24nvIPoMdaiUiDismz8xq_W1mc"
    
    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "PRODUCT-ID": "10083",
        "Referer": "https://td.sangfor.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TD-AREA": "null",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }
    
    try:
        # 发送GET请求
        response = requests.get(url, headers=headers, cookies={"ep_jwt_token": cookie_str}, verify=False, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"发生错误: {e}")
        return None


def save_defect_detail(defect_key, filename=None):
    """
    根据缺陷编号获取缺陷详细信息并保存到文件
    
    Args:
        defect_key (str): 缺陷编号
        filename (str): 保存文件名，默认为 defect_{defect_key}.json
        
    Returns:
        bool: 保存是否成功
    """
    # 如果未指定文件名，使用默认文件名
    if not filename:
        filename = f"defect_{defect_key}.json"
    
    # 获取缺陷详细信息
    result = get_defect_by_key(defect_key)
    
    if not result:
        print("获取缺陷信息失败，无法保存")
        return False
    
    # 保存到文件
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ 缺陷详细信息已成功保存到 {filename}")
        return True
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        return False


# 主函数
if __name__ == "__main__":
    # 获取用户输入的缺陷编号
    defect_key = input("请输入缺陷编号: ")
    
    # 保存缺陷详细信息
    save_defect_detail(defect_key)