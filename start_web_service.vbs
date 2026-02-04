' Start Web Service VBScript
Set objShell = CreateObject("WScript.Shell")

' Run batch file
objShell.Run "start_web_service.bat", 0, False

' Show message
MsgBox "Service started", vbInformation, "Success"
