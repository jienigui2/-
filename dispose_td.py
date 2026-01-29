import json
import re
from API import APIClient

class DisposeTD:
    def __init__(self, json_file):
        """
        初始化DisposeTD实例
        
        Args:
            json_file: defect_result.json文件路径
        """
        self.json_file = json_file
        self.defects = []
        self.api_client = APIClient(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="sk-c46dce9962a44c889f39a7af3ade04a6"
        )
    
    def load_defects(self):
        """
        加载并筛选缺陷
        
        Returns:
            bool: 是否加载成功
        """
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rows = data.get('data', {}).get('rows', [])
            
            # 筛选创建人是许熙铉84333或李进53281的缺陷
            for row in rows:
                creator = row.get('fields', {}).get('creator', {})
                creator_display_name = creator.get('display_name', '')
                
                if creator_display_name in ['许熙铉84333', '李进53281']:
                    self.defects.append(row)
            
            print(f"✓ 成功加载并筛选出 {len(self.defects)} 个缺陷")
            for i, defect in enumerate(self.defects):
                fields = defect.get('fields', {})
                creator = fields.get('creator', {})
                creator_display_name = creator.get('display_name', '')
                summary = fields.get('summary', '')
                print(f"  {i+1}. 创建人: {creator_display_name}, 标题: {summary}")
            
            return True
        except Exception as e:
            print(f"✗ 加载缺陷文件失败: {e}")
            return False
    
    def analyze_defect(self, defect):
        """
        分析单个缺陷，提取KB包全名、版本号和流程阶段
        
        Args:
            defect: 缺陷数据
            
        Returns:
            dict: 分析结果
        """
        try:
            fields = defect.get('fields', {})
            
            # 提取关键信息
            summary = fields.get('summary', '')
            desc = fields.get('desc', '')
            comment = fields.get('comment', '')
            attachments = fields.get('attachment', [])
            status = fields.get('status', {})
            status_name = status.get('name', '')
            discover_stage = fields.get('discover_stage', {})
            stage_name = discover_stage.get('name', '')
            
            # 构建分析请求
            analysis_request = {
                "defect": {
                    "summary": summary,
                    "description": desc,
                    "comment": comment,
                    "attachments": [att.get('file_name', '') for att in attachments],
                    "status": status_name,
                    "stage": stage_name
                },
                "request": '''任务：从下述缺陷信息中高精度提取KB包全名和NMC/NAC版本号，返回严格格式的JSON数据。
核心规则与要求：
1.  KB包全名提取规则：
    a.  提取范围：优先遍历附件中的「file_name」「name」字段，其次遍历缺陷描述、评论中的文本内容
    b.  有效KB包判定：必须以「KB-」开头，包含日期（如20260106）、项目标识（如Wlan-2025120401），可包含后缀.sign/.tgz/.7z/.tar（后缀完整保留）
    c.  处理要求：完整提取，不得截断；多个不同KB包去重后用英文逗号","拼接；无有效KB包则赋值为空字符串""
    d.  排除项：仅文件名包含cov、log、image、png的附件，不视为KB包，无需提取
2.  NMC/NAC版本号提取规则：
    a.  提取范围优先级：「测试环境」描述 > 「定制版本」描述 > 缺陷描述正文 > 评论正文
    b.  有效版本判定：仅识别以「nmc」「NMC」「nac」「NAC」开头的版本信息
    c.  格式转换要求（强制统一）：
        -  原始格式nmc315 → 转换为 NMC 3.15.0
        -  原始格式nmc316 → 转换为 NMC 3.16.0
        -  原始格式nac3.16.0 → 转换为 NAC 3.16.0
        -  原始格式NMC3.15.0 → 转换为 NMC 3.15.0
    d.  无有效NMC/NAC版本信息，赋值为"无"
3.  返回格式要求（强制严格遵守，否则任务失败）：
    a.  仅返回JSON数据，无任何前置、后置文本
    b.  字段名固定为「kb_package」和「version」，不可修改、不可缺失
    c.  字段值均为字符串类型，JSON语法无错误（引号为英文双引号，无多余逗号）
4.  禁止操作：不得添加额外解释、备注、换行符，不得修改字段名，不得返回JSON以外的任何内容。'''
            }
            
            # 调用API进行分析
            payload = {
                "model": "qwen-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": json.dumps(analysis_request, ensure_ascii=False)
                    }
                ],
                "temperature": 0.3
            }
            
            result = self.api_client.call_api("chat/completions", method="POST", payload=payload)
            
            if result:
                # 解析API响应
                response_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 提取JSON部分
                json_match = re.search(r'\{[\s\S]*\}', response_content)
                if json_match:
                    try:
                        analysis_result = json.loads(json_match.group(0))
                        
                        # 标准化字段名
                        normalized_result = {
                            "kb_package": analysis_result.get('kb_package', '') or analysis_result.get('KB包全名', '') or analysis_result.get('name', '') or '',
                            "version": analysis_result.get('version', '') or analysis_result.get('NMC或NAC版本号', '') or analysis_result.get('nmc_or_nac_version', '') or ''
                        }
                        return normalized_result
                    except json.JSONDecodeError:
                        pass
                
                # 如果API返回的不是JSON格式，直接返回None
                return None
            else:
                # API调用失败，直接返回None
                return None
                
        except Exception as e:
            print(f"✗ 分析缺陷失败: {e}")
            return None
    
    def extract_info_manually(self, fields):
        """
        手动提取缺陷信息
        
        Args:
            fields: 缺陷字段
            
        Returns:
            dict: 提取结果
        """
        result = {
            "kb_package": "",
            "version": "",
            "stage": ""
        }
        
        # 提取KB包全名
        attachments = fields.get('attachment', [])
        for attachment in attachments:
            file_name = attachment.get('file_name', '')
            if 'KB-' in file_name:
                result['kb_package'] = file_name
                break
        
        # 提取版本号 - 优先从测试环境获取
        desc = fields.get('desc', '')
        comment = fields.get('comment', '')
        
        # 1. 从测试环境信息中提取版本
        # 从git分支名或测试环境信息中提取
        test_env_match = re.search(r'(NMC|NAC)[0-9]*\.?([0-9]+\.[0-9]+\.[0-9]+)', comment)
        if not test_env_match:
            # 尝试从git分支名中提取版本，如wns3.16.0_Wlan-2025120401
            test_env_match = re.search(r'wns([0-9]+\.[0-9]+\.[0-9]+)', comment)
            if test_env_match:
                # 尝试从描述中查找NMC或NAC前缀
                nmc_nac_match = re.search(r'(NMC|NAC)', desc)
                if nmc_nac_match:
                    result['version'] = f"{nmc_nac_match.group(1)} {test_env_match.group(1)}"
                else:
                    # 默认为NMC
                    result['version'] = f"NMC {test_env_match.group(1)}"
        else:
            result['version'] = f"{test_env_match.group(1)} {test_env_match.group(2)}"
        
        # 如果测试环境中没有找到版本，从描述中提取
        if not result['version']:
            # 2. 从描述中提取版本
            version_match = re.search(r'(NMC|NAC)[0-9]*\.?([0-9]+\.[0-9]+\.[0-9]+)', desc)
            if version_match:
                result['version'] = f"{version_match.group(1)} {version_match.group(2)}"
            else:
                # 3. 尝试其他格式
                version_match = re.search(r'[0-9]+\.[0-9]+\.[0-9]+', desc)
                if version_match:
                    # 尝试从描述中查找NMC或NAC前缀
                    nmc_nac_match = re.search(r'(NMC|NAC)', desc)
                    if nmc_nac_match:
                        result['version'] = f"{nmc_nac_match.group(1)} {version_match.group(0)}"
                    else:
                        result['version'] = version_match.group(0)
        
        # 提取流程阶段
        status = fields.get('status', {})
        result['stage'] = status.get('name', '')
        
        return result
    
    def generate_config(self):
        """
        生成简化格式的输出，只包含需要的字段
        
        Returns:
            dict: 配置数据
        """
        # 简化的输出结构，只包含需要的字段
        simplified_config = []
        
    def split_kb_package(self, kb_package):
        """
        分解KB包为kb_name和kb_id
        
        Args:
            kb_package: KB包全名（可能包含多个KB包，用逗号分隔）
            
        Returns:
            tuple: (kb_name, kb_id)
        """
        if not kb_package:
            return "", ""
        
        # 取第一个KB包
        kb = kb_package.split(',')[0].strip()
        
        # 移除常见扩展名（循环处理，直到没有扩展名可移除）
        extensions = ['.sign', '.tgz', '.7z', '.tar']
        while True:
            removed = False
            for ext in extensions:
                if kb.endswith(ext):
                    kb = kb[:-len(ext)]
                    removed = True
                    break
            if not removed:
                break
        
        # 按连字符分割
        parts = kb.split('-')
        if len(parts) > 1:
            kb_id = parts[-1]
            kb_name = '-'.join(parts[:-1])
        else:
            kb_name = kb
            kb_id = ""
        
        return kb_name, kb_id
    
    def generate_config(self):
        """
        生成简化格式的输出，只包含需要的字段
        
        Returns:
            dict: 配置数据
        """
        # 简化的输出结构，只包含需要的字段
        simplified_config = []
        
        # 分析每个缺陷并添加到配置中
        for defect in self.defects:
            analysis_result = self.analyze_defect(defect)
            fields = defect.get('fields', {})
            creator = fields.get('creator', {})
            desc = fields.get('desc', '')
            
            # 如果AI分析失败，使用手动提取
            if analysis_result is None:
                # 手动提取缺陷信息
                analysis_result = self.extract_info_manually(fields)
            
            # 获取版本并确保包含NMC/NAC前缀（仅当AI未返回前缀时）
            version = analysis_result.get('version', '')
            if version and not (version.startswith('NMC') or version.startswith('NAC')):
                # 从描述中查找NMC或NAC前缀
                nmc_nac_match = re.search(r'(NMC|NAC)', desc)
                if nmc_nac_match:
                    version = f"{nmc_nac_match.group(1)} {version}"
            
            # 分解KB包
            kb_package = analysis_result.get('kb_package', '')
            kb_name, kb_id = self.split_kb_package(kb_package)
            
            # 只包含需要的字段：版本号、KB包、summary、kb_name、kb_id
            defect_info = {
                "version": version,
                "kb_package": kb_package,
                "kb_name": kb_name,
                "kb_id": kb_id,
                "summary": fields.get('summary', '')
            }
            
            simplified_config.append(defect_info)
        
        return simplified_config
    
    def run(self):
        """
        运行完整流程
        
        Returns:
            dict: 生成的配置
        """
        print("="*80)
        print("开始处理缺陷数据")
        print("="*80)
        
        # 加载缺陷
        if not self.load_defects():
            return None
        
        # 生成配置
        config = self.generate_config()
        
        # 保存配置到文件
        output_file = "dispose_td_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*80)
        print(f"处理完成！配置已保存到 {output_file}")
        print("="*80)
        
        # 打印生成的配置
        print("\n生成的配置:")
        print(json.dumps(config, ensure_ascii=False, indent=2))
        
        return config

if __name__ == "__main__":
    # 创建实例并运行
    dispose_td = DisposeTD("defect_result.json")
    dispose_td.run()
