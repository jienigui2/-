## 问题分析

在日志中出现了curl命令的进度输出被当作错误信息记录的情况，具体表现为：
```
启动错误信息:   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current 
 Dload  Upload   Total   Spent    Left  Speed 
 0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0 
 100    71  100    71    0     0    290      0 --:--:-- --:--:-- --:--:--   290 
```

### 根本原因
1. curl命令在默认情况下会将进度信息输出到标准错误（stderr）
2. 代码在执行curl命令时捕获了stderr，并将其作为错误信息记录
3. 这导致curl的正常进度信息被误当作错误信息

## 修复方案

### 1. 修改vm_management_workflow.py
- 在所有curl命令中添加 `-s` 或 `--silent` 参数，禁用进度输出
- 同时添加 `-S` 或 `--show-error` 参数，确保真正的错误信息仍能显示

### 2. 修改vm/test_start_simple.py
- 同样在curl命令中添加 `-s` 参数

### 3. 修改vm/vm_group.py
- 在curl命令中添加 `-s` 参数

## 具体修改点

1. **vm_management_workflow.py**：
   - 第625行：在curl命令参数中添加 `-s`
   - 第569行：在curl命令字符串中添加 `-s`
   - 第1976行：在curl命令字符串中添加 `-s`
   - 第2028行：在curl命令字符串中添加 `-s`
   - 第2089行：在curl命令字符串中添加 `-s`

2. **vm/test_start_simple.py**：
   - 在curl命令中添加 `-s` 参数

3. **vm/vm_group.py**：
   - 第136行：在curl命令字符串中添加 `-s`

## 修复效果

修复后，curl命令的进度信息将不再被当作错误信息记录，日志会更加干净，同时真正的错误信息仍然会被正确捕获和记录。