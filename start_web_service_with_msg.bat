@echo off

REM 启动Web服务（配置管理系统）
echo 正在启动配置管理系统...

REM 使用完整路径运行Python脚本
"C:\Program Files\Python312\python.exe" "%~dp0config_web.py"

REM 显示中文提示信息
msg * /time:5 "配置管理系统已启动！

访问地址: http://localhost:5000"

REM 暂停以查看输出
pause
