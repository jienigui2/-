import requests
import json
import os

class APIClient:
    def __init__(self, base_url=None, api_key=None):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
        """
        # 默认配置，用户需要填写
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 请填写API基础URL
        self.api_key = api_key or "sk-c46dce9962a44c889f39a7af3ade04a6"  # 请填写API密钥
        
        # 固定配置
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = 30
    
    def call_api(self, endpoint, method="GET", payload=None):
        """
        调用API
        
        Args:
            endpoint: API端点
            method: 请求方法 (GET, POST)
            payload: 请求数据
            
        Returns:
            dict: API响应结果
        """
        try:
            # 构建完整URL
            url = f"{self.base_url}/{endpoint}"
            print(f"[API调用] URL: {url}")
            print(f"[API调用] 方法: {method}")
            if payload:
                print(f"[API调用] 数据: {json.dumps(payload, indent=2)}")
            
            # 发送请求
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            else:
                print(f"[错误] 不支持的请求方法: {method}")
                return None
            
            # 处理响应
            print(f"[API响应] 状态码: {response.status_code}")
            print(f"[API响应] 内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("[错误] API响应不是有效的JSON格式")
                    return {"raw_response": response.text}
            else:
                print(f"[错误] API调用失败，状态码: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"[错误] API调用异常: {e}")
            return None
        except Exception as e:
            print(f"[错误] 未知错误: {e}")
            return None
    
    def test_connection(self):
        """
        测试API连接是否成功
        
        Returns:
            bool: 连接是否成功
        """
        print("\n" + "="*60)
        print("测试API连接")
        print("="*60)
        
        # 尝试调用一个简单的端点（通常是health或ping）
        test_endpoints = ["health", "ping", "status"]
        
        for endpoint in test_endpoints:
            print(f"\n测试端点: {endpoint}")
            result = self.call_api(endpoint)
            
            if result:
                print("✓ API连接成功！")
                return True
        
        # 如果测试端点都失败，尝试调用根路径
        print("\n测试端点: 根路径")
        result = self.call_api("")
        
        if result:
            print("✓ API连接成功！")
            return True
        else:
            print("✗ API连接失败，请检查配置是否正确")
            return False
    
    def test_post_request(self, test_endpoint="test", test_data=None):
        """
        测试POST请求
        
        Args:
            test_endpoint: 测试用的POST端点
            test_data: 测试数据
            
        Returns:
            bool: POST请求是否成功
        """
        print("\n" + "="*60)
        print("测试POST请求")
        print("="*60)
        
        # 默认测试数据
        if test_data is None:
            test_data = {
                "test_key": "test_value",
                "test_number": 123,
                "test_bool": True
            }
        
        print(f"测试端点: {test_endpoint}")
        print(f"测试数据: {json.dumps(test_data, indent=2)}")
        
        result = self.call_api(test_endpoint, method="POST", payload=test_data)
        
        if result:
            print("✓ POST请求成功！")
            return True
        else:
            print("✗ POST请求失败")
            return False

if __name__ == "__main__":
    """
    测试程序
    """
    print("="*80)
    print("API调用测试程序")
    print("="*80)
    
    # 创建API客户端实例，使用阿里云DashScope API
    api_client = APIClient(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云DashScope兼容模式API地址
        api_key="sk-c46dce9962a44c889f39a7af3ade04a6"  # 阿里云DashScope API Key
    )
    
    # 测试连接 - 修改为测试具体的大模型API端点
    print("\n" + "="*60)
    print("测试大模型API连接")
    print("="*60)
    
    # 测试ChatGPT兼容API - 使用阿里云DashScope支持的模型名称
    chat_payload = {
        "model": "qwen-turbo",  # 阿里云通义千问模型
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.7
    }
    
    print("测试端点: chat/completions")
    print(f"测试数据: {json.dumps(chat_payload, indent=2)}")
    
    result = api_client.call_api("chat/completions", method="POST", payload=chat_payload)
    
    if result:
        print("✓ 大模型API连接成功！")
        print("\nAPI响应结果:")
        print(json.dumps(result, indent=2))
    else:
        print("✗ 大模型API连接失败，请检查配置是否正确")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
