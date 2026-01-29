import requests
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def search_defects(summary_keyword, page_no=1, page_size=25):
    """
    搜索缺陷数据
    
    Args:
        summary_keyword (str): summary关键词
        page_no (int): 页码，从1开始
        page_size (int): 每页数量
    
    Returns:
        dict: 返回的JSON数据或错误信息
    """
    # API URL（动态生成时间戳）
    import time
    url = f"https://td.sangfor.com/api/v1/defect/es/es_search_by_fields?_t={int(time.time() * 1000)}"
    
    # Cookie字符串
    cookie_str = "ep_jwt_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjU5MjcyIiwiZGlzcGxheV9uYW1lIjoiXHU4YzJkXHU0ZmNhXHU2NzcwNTkyNzIiLCJhY2Nlc3NfaXAiOiIxMC43Mi4xMC41MSIsImlhdCI6MTc2ODg1NDYxNiwiZXhwIjoxNzY5NDU5NDE2LCJpc19hZG1pbiI6ZmFsc2UsImVtYWlsIjoiNTkyNzJAc2FuZ2Zvci5jb20ifQ.vYh4Db97BRQ-NnIJ0DFRkcX3uHWWhWwKG3R0EZ1tJW8"
    
    # 请求头
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": cookie_str,
        "Origin": "https://td.sangfor.com",
        "PRODUCT-ID": "10083",
        "Referer": "https://td.sangfor.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }
    
    # 构建查询条件
    query_conditions = {
        "and": {"fields": {}},
        "or": {"fields": {"summary": summary_keyword}},
        "not": {"fields": {}}
    }
    
    # 构建请求数据
    data = {
        "product_id": 10083,
        "origin_product_id": None,
        "is_cross_product": None,
        "page_no": page_no,
        "page_size": page_size,
        "sort_by": {"assigner": "asc"},
        "query_conditions": query_conditions,
        "cycle_analysis": {},
        "handle_by_self": False
    }
    
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return None
            
    except Exception as e:
        return None


def save_defect_data(summary_keyword, filename='defect_result.json'):
    """
    根据summary关键词搜索缺陷并保存全部报文到文件
    
    Args:
        summary_keyword (str): summary关键词
        filename (str): 保存文件名
        
    Returns:
        bool: 保存是否成功
    """
    # 调用搜索函数
    result = search_defects(summary_keyword)
    
    if not result:
        print("搜索失败，未获取到数据")
        return False
    
    # 保存全部报文到文件
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ 全部报文已成功保存到 {filename}")
        return True
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        return False


# 主函数
if __name__ == "__main__":
    # 获取用户输入的关键词
    summary_keyword = input("请输入summary关键词: ")
    
    # 保存缺陷数据
    save_defect_data(summary_keyword)