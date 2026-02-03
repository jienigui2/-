import re

def extract_text_from_html(html_content):
    """从HTML内容中提取文本"""
    # 提取x-grid3-cell-inner标签中的文本
    pattern = r'<div class="x-grid3-cell-inner x-grid3-col-1"[^>]*>([^<]+)</div>'
    matches = re.findall(pattern, html_content)
    
    # 去除空白字符并去重
    versions = [match.strip() for match in matches if match.strip()]
    
    # 去重（保持顺序）
    seen = set()
    unique_versions = []
    for version in versions:
        if version not in seen:
            seen.add(version)
            unique_versions.append(version)
    
    return unique_versions

# 读取version.ini文件
with open('version.ini', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 提取文本
versions = extract_text_from_html(html_content)

# 输出结果
print(f"\n从version.ini中提取的版本号（共{len(versions)}个）：")
print("=" * 60)
for idx, version in enumerate(versions, 1):
    print(f"{idx:3d}. {version}")

# 保存到文件
with open('version_list.txt', 'w', encoding='utf-8') as f:
    for version in versions:
        f.write(f"{version}\n")

print(f"\n版本列表已保存到 version_list.txt")