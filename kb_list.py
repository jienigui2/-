import requests
import json
import ssl

def get_kb_list(filter_text="", start=0, limit=50):
    """获取KB项目列表
    
    Args:
        filter_text: 筛选文本（如：wlan-2025111403）
        start: 起始位置，默认为0
        limit: 返回数量限制，默认为50
        
    Returns:
        dict: 响应数据
    """
    url = "http://10.156.99.96/cgi-bin/kb_project.cgi"
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "http://10.156.99.96",
        "Referer": "http://10.156.99.96/kb.php",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    data = {
        "start": start,
        "limit": limit,
        "opr": "list",
        "filter": filter_text,
        "filterFields": ["name", "description", "creator", "td_id"]
    }
    
    try:
        print(f"正在发送请求到: {url}")
        print(f"请求参数: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None


if __name__ == "__main__":
    # 测试示例
    result = get_kb_list(filter_text="KB-WACAP-20260113-Wlan-2025112002")
    if result:
        print("\n获取KB列表成功！")
    else:
        print("\n获取KB列表失败！")