    def recover_vm_snapshot(self, vmid, snapshot_id):
        """恢复虚拟机快照"""
        if not self.hci_credentials:
            print("✗ HCI登录凭证未获取")
            return False
        
        try:
            ip = self.hci_credentials.get('ip')
            csrf_token = self.hci_credentials.get('csrf_token')
            cookie = self.hci_credentials.get('cookie')
            
            print(f"正在恢复虚拟机 {vmid} 到快照 {snapshot_id}...")
            
            # 尝试使用curl命令恢复虚拟机快照
            import subprocess
            import time
            
            # 构建完整的Cookie字符串
            timestamp = int(time.time() * 1000)
            full_cookie = f"cluster=single_cluster; needAnalytic=need_analytic; vnc-keyboard=en-us; {cookie}; global.timeout.task={timestamp}"
            
            # 构建curl命令
            curl_command = f"curl ^\"https://{ip}/vapi/extjs/cluster/vm/{vmid}/recovery^\" ^
-X ^\"POST^\" ^
-H ^\"Accept: */*\" ^
-H ^\"Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6^\" ^
-H ^\"CSRFPreventionToken: {csrf_token}^\" ^
-H ^\"Connection: keep-alive^\" ^
-H ^\"Content-Type: application/x-www-form-urlencoded; charset=UTF-8^\" ^
-H ^\"Cookie: {full_cookie}^\" ^
-H ^\"Origin: https://{ip}^\" ^
-H ^\"Referer: https://{ip}/^\" ^
-H ^\"Sec-Fetch-Dest: empty^\" ^
-H ^\"Sec-Fetch-Mode: cors^\" ^
-H ^\"Sec-Fetch-Site: same-origin^\" ^
-H ^\"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0^\" ^
-H ^\"X-Requested-With: XMLHttpRequest^\" ^
-H ^\"sec-ch-ua: ^\\\"Not(A:Brand^\\\";v=^\\\\\"8^\\\", ^\\\\\"Chromium^\\\";v=^\\\\\"144^\\\", ^\\\\\"Microsoft Edge^\\\";v=^\\\\\"144^\\\\\"^\" ^
-H ^\"sec-ch-ua-mobile: ?0^\" ^
-H ^\"sec-ch-ua-platform: ^\\\"Windows^\"^\" ^
-d ^\"rtype=raw&snapid={snapshot_id}&backup=0^\" ^
--insecure"
            
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
            print(f"恢复快照命令退出码: {process.returncode}")
            if stdout:
                print(f"恢复快照响应内容: {stdout}")
            if stderr:
                print(f"恢复快照命令错误: {stderr}")
            
            if process.returncode == 0:
                print("✓ 快照恢复成功")
                
                # 恢复快照后等待10秒再启动虚拟机
                print("\n等待10秒后启动虚拟机...")
                time.sleep(10)
                print("✓ 等待完成，正在启动虚拟机...")
                self.start_vm(vmid)
                
                return True
            else:
                print("✗ 快照恢复失败")
                return False
                
        except Exception as e:
            print(f"✗ 恢复快照失败: {e}")
            import traceback
            traceback.print_exc()
            return False