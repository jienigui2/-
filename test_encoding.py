#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编码处理测试脚本
"""

import sys
import os

print("=== 编码处理测试 ===")
print(f"Python版本: {sys.version}")
print(f"默认编码: {sys.getdefaultencoding()}")
print(f"文件系统编码: {sys.getfilesystemencoding()}")

# 测试中文字符输出
print("\n=== 中文字符输出测试 ===")
try:
    print("测试中文字符: 你好，世界！")
    print("测试保留项设置: 保留项设置")
    print("测试恢复配置: 恢复配置")
    print("[OK] 中文字符输出成功")
except Exception as e:
    print(f"[ERROR] 中文字符输出失败: {e}")

# 测试文件读写编码
print("\n=== 文件读写编码测试 ===")
try:
    test_file = "test_encoding_output.txt"
    # 写入中文字符
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("测试文件内容: 你好，世界！\n")
        f.write("保留项设置测试\n")
        f.write("恢复配置测试\n")
    print(f"[OK] 写入文件成功: {test_file}")
    
    # 读取文件
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"[OK] 读取文件成功")
    print(f"文件内容: {content}")
    
    # 清理测试文件
    os.remove(test_file)
except Exception as e:
    print(f"[ERROR] 文件读写测试失败: {e}")

print("\n=== 编码测试完成 ===")
