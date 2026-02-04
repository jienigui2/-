' 启动Web服务的VBScript脚本
' 此脚本会在后台运行批处理文件，不显示命令行窗口

Set objShell = CreateObject("WScript.Shell")

' 运行批处理文件，隐藏窗口
' 使用相对路径，因为脚本和批处理文件在同一目录
objShell.Run Chr(34) & "start_web_service.bat" & Chr(34), 0, False

' 显示提示信息
Dim msg, title
msg = "配置管理系统已启动！"
msg = msg & vbCrLf
msg = msg & vbCrLf
msg = msg & "访问地址: http://localhost:5000"
title = "启动成功"
MsgBox msg, vbInformation, title
