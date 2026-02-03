# 移除current_kb_package配置项计划

## 任务目标
移除未使用的current_kb_package配置项，包括：
1. 从all.ini文件中删除该配置项
2. 从vm_management_workflow.py文件中移除对它的读取和验证

## 具体步骤

### 步骤1：修改all.ini文件
- 删除第10行的`current_kb_package = Wlan-2025111403`配置项

### 步骤2：修改vm_management_workflow.py文件
- 修改load_ini_config函数，从配置字典中移除kb_packages部分的current字段
- 修改配置验证部分，移除对config['kb_packages']['current']的检查

## 预期结果
- all.ini文件中不再包含current_kb_package配置项
- vm_management_workflow.py文件中不再引用current_kb_package配置项
- 代码仍然能够正常运行，因为这个配置项本来就没有被实际使用