# 将KB_scan与kb_scan_report与vm_management绑定实现同步运行

## 实现步骤

### 1. 修改find_and_click_targets方法
- 更新返回值，添加非sign KB包的路径和文件名
- 确保在下载非sign KB包时记录其完整路径和文件名

### 2. 修改upgrade_kb_packages方法
- 在KB包下载完成后，使用多线程启动kb_scan
- 与vm_management程序同步运行kb_scan
- 传递非sign KB包的路径作为kb_scan的file_path参数
- 监控kb_scan的运行状态
- kb_scan运行结束后，等待两分钟
- 然后运行kb_scan_report，传递非sign KB包的名字作为kb_package参数

### 3. 修改kb_scan.py
- 添加命令行参数解析，支持通过命令行指定file_path
- 保持与原有配置文件读取的兼容性

### 4. 修改kb_scan_report.py
- 确保命令行参数解析正确处理kb_package参数
- 保持与原有配置文件读取的兼容性

## 技术实现要点

### 多线程/多进程实现
- 使用Python的threading或multiprocessing模块实现并发执行
- 确保kb_scan与vm_management的升级操作同时进行

### 进程监控
- 实现对kb_scan进程的监控，确保其正常运行和结束
- 在kb_scan结束后触发后续的kb_scan_report执行

### 命令行参数传递
- 为kb_scan和kb_scan_report添加命令行参数支持
- 确保参数传递正确，特别是文件路径和文件名

### 时间控制
- 在kb_scan结束后，使用time.sleep()等待两分钟
- 然后启动kb_scan_report

## 预期效果

- vm_management下载KB包完成后，自动启动kb_scan
- kb_scan与vm_management的升级操作同步运行，提高效率
- kb_scan使用正确的非sign KB包路径
- kb_scan结束后，自动等待两分钟并启动kb_scan_report
- kb_scan_report使用正确的非sign KB包名字
- 整个流程自动化，无需手动干预