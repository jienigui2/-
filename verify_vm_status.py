import subprocess
import json
import time

def verify_vm_status():
    """验证虚拟机状态是否为运行中"""
    # 配置信息
    ip = "10.156.1.50"  # HCI设备IP
    vmid = "7908819340268"  # 虚拟机ID
    csrf_token = "6972E7EB:LkxobR5yjUy9YdaC4cGB8wFs6yo"  # 从之前的请求中获取
    cookie = "LoginAuthCookie=Login:YWRtaW4=:6972CFFB::kwF196DU9JE+LC0wX5kveC4tMv9PAtELOUMjiXeMMyEl2xzVXlfWveV/PhWlfRP/CNJEmk1zncvAo6gks4j3kk6ZUUuwwrljLC72QBbhxPe+PqRLggEai6s6W8bnvYGOAm6p2uhPFTdxVJpVqPwxRxxJFT1ccSUxiKEdCKKY7dbyywoylMS41f3YJYLt62Mcr13IriMw1s5wzbOXqCITbT4VrEvMFDO1sZ5ocTAjnF/eZApflSzBw+DCul10qRHI2Y7VuwLJYJu9ng2ye04OWQanbfoE4PqwID0OkB0WR7xfZPIW4rP7VE81qQqSBaM9nsgxRKOJUixJZNsAoVHDlQ==; cluster=single_cluster; needAnalytic=need_analytic; vnc-keyboard=en-us; global.timeout.task=1769138766826"  # 从之前的请求中获取
    
    max_checks = 10  # 最大检查次数
    check_interval = 5  # 检查间隔（秒）
    
    print("开始验证虚拟机状态...")
    print(f"HCI设备IP: {ip}")
    print(f"虚拟机ID: {vmid}")
    
    for check in range(max_checks):
        try:
            print(f"\n第 {check + 1} 次检查...")
            
            # 构建curl命令获取虚拟机列表，从中查找目标虚拟机的状态
            curl_command = f"""
curl ^"https://{ip}/vapi/json/cluster/vms^" ^
-X ^"GET^" ^
-H ^"Accept: */*^" ^
-H ^"CSRFPreventionToken: {csrf_token}^" ^
-H ^"Cookie: {cookie}^" ^
-H ^"X-Requested-With: XMLHttpRequest^" ^
--insecure
"""
            
            # 执行curl命令
            process = subprocess.Popen(
                curl_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="E:\\1"
            )
            
            # 获取输出和错误
            stdout, stderr = process.communicate(timeout=60)  # 60秒超时
            
            # 打印结果
            print(f"命令退出码: {process.returncode}")
            print(f"响应内容前100字符: {stdout[:100]}...")
            if stderr:
                print(f"错误信息: {stderr}")
            
            if process.returncode == 0:
                try:
                    # 解析JSON响应
                    response_data = json.loads(stdout)
                    vms = response_data.get('data', [])
                    
                    print(f"共获取到 {len(vms)} 个虚拟机")
                    
                    # 查找目标虚拟机
                    target_vm = None
                    for vm in vms:
                        if str(vm.get('vmid')) == str(vmid):
                            target_vm = vm
                            break
                    
                    if target_vm:
                        print(f"找到目标虚拟机: {target_vm.get('name')}")
                        # 检查虚拟机状态字段（根据实际返回数据调整字段名）
                        status = target_vm.get('status')
                        power_state = target_vm.get('power_state')
                        
                        print(f"虚拟机状态: {status}")
                        print(f"电源状态: {power_state}")
                        
                        # 检查状态是否为运行中
                        if status in [1, "running", "RUNNING", "1"] or power_state in [1, "running", "RUNNING", "1"]:
                            print("✓ 虚拟机已成功启动，当前状态为运行中！")
                            return True
                        elif status in [0, "stopped", "STOPPED", "0"] or power_state in [0, "stopped", "STOPPED", "0"]:
                            print("✗ 虚拟机当前状态为停止，等待再次检查...")
                        else:
                            print(f"⚠ 虚拟机当前状态为 status={status}, power_state={power_state}，等待再次检查...")
                    else:
                        print(f"✗ 未找到ID为 {vmid} 的虚拟机")
                        
                except json.JSONDecodeError as e:
                    print(f"解析响应JSON失败: {e}")
                    print(f"实际响应内容: {stdout}")
            else:
                print(f"✗ 获取虚拟机列表失败，退出码: {process.returncode}")
            
            # 等待一段时间后再次检查
            if check < max_checks - 1:
                print(f"等待 {check_interval} 秒后再次检查...")
                time.sleep(check_interval)
            
        except Exception as e:
            print(f"✗ 验证虚拟机状态失败: {e}")
            import traceback
            traceback.print_exc()
            if check < max_checks - 1:
                print(f"等待 {check_interval} 秒后再次检查...")
                time.sleep(check_interval)
            
    print("\n✗ 多次检查后仍未检测到虚拟机运行状态")
    return False

if __name__ == "__main__":
    verify_vm_status()