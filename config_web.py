from flask import Flask, render_template_string, request, jsonify, send_from_directory
import configparser
import os
import subprocess
import threading
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 清理超过指定天数的文件
def cleanup_old_files(days=7):
    """
    清理超过指定天数的文件
    
    Args:
        days: 保留天数，默认为7天
    """
    import datetime
    
    # 需要清理的目录和文件类型
    cleanup_dirs = [
        {'path': 'info', 'extensions': ['.log']},
        {'path': 'KB_photo', 'extensions': ['.png']},
        {'path': 'KB_compare_photo', 'extensions': ['.png']}
    ]
    
    # 计算截止时间
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_timestamp = cutoff_time.timestamp()
    
    logger.info(f"开始清理超过 {days} 天的文件，截止时间: {cutoff_time}")
    
    for cleanup_item in cleanup_dirs:
        dir_path = cleanup_item['path']
        extensions = cleanup_item['extensions']
        
        if not os.path.exists(dir_path):
            logger.info(f"目录 {dir_path} 不存在，跳过清理")
            continue
        
        try:
            deleted_count = 0
            
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                
                # 检查是否是文件
                if not os.path.isfile(file_path):
                    continue
                
                # 检查文件扩展名
                if not any(filename.endswith(ext) for ext in extensions):
                    continue
                
                # 检查文件修改时间
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_timestamp:
                    # 删除文件
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"删除文件: {file_path} (修改时间: {datetime.datetime.fromtimestamp(file_mtime)})")
            
            logger.info(f"目录 {dir_path} 清理完成，删除了 {deleted_count} 个文件")
            
        except Exception as e:
            logger.error(f"清理目录 {dir_path} 时出错: {e}")
    
    logger.info("文件清理完成")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

# 全局变量
running_process = None
process_output = []
process_status = 'idle'  # idle, running, completed, error

# 上一次运行信息
last_run_info = {
    'start_time': None,
    'end_time': None,
    'screenshots': []
}

# 读取配置文件
def read_config():
    """读取all.ini配置文件"""
    config = configparser.ConfigParser()
    config_file = 'all.ini'
    
    if not os.path.exists(config_file):
        logger.error(f"配置文件 {config_file} 不存在")
        return {}
    
    try:
        config.read(config_file, encoding='utf-8')
        
        # 转换为字典格式
        config_dict = {}
        for section in config.sections():
            config_dict[section] = {}
            for option in config.options(section):
                config_dict[section][option] = config.get(section, option)
        
        return config_dict
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return {}

# 保存配置文件
def save_config(config_dict):
    """保存配置到all.ini文件"""
    config = configparser.ConfigParser()
    config_file = 'all.ini'
    
    try:
        # 读取现有配置，保留注释
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 构建新的配置内容
        new_lines = []
        current_section = None
        
        for line in lines:
            stripped_line = line.strip()
            
            # 处理section
            if stripped_line.startswith('[') and stripped_line.endswith(']'):
                current_section = stripped_line[1:-1]
                new_lines.append(line)
            # 处理注释
            elif stripped_line.startswith('#'):
                new_lines.append(line)
            # 处理空行
            elif not stripped_line:
                new_lines.append(line)
            # 处理配置项
            elif current_section and '=' in line:
                key = line.split('=', 1)[0].strip()
                if current_section in config_dict and key in config_dict[current_section]:
                    # 更新配置值
                    value = config_dict[current_section][key]
                    new_line = f"{key} = {value}\n"
                    new_lines.append(new_line)
                else:
                    # 保留原有配置
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 写入新配置
        with open(config_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.info("配置文件保存成功")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False

# 运行vm_management程序
def run_vm_management():
    """运行vm_management_workflow.py程序"""
    global running_process, process_output, process_status
    
    # 初始化日志文件路径
    log_file_path = None
    
    try:
        # 更新运行开始时间
        update_last_run_time()
        
        process_output = []
        process_status = 'running'
        
        # 创建info文件夹
        info_dir = 'info'
        if not os.path.exists(info_dir):
            os.makedirs(info_dir)
            logger.info(f"创建info文件夹: {info_dir}")
        
        # 生成日志文件名（使用北京时间）
        start_time = last_run_info.get('start_time')
        if start_time:
            # 使用datetime模块处理北京时间（UTC+8）
            import datetime
            # 北京时间比UTC早8小时
            beijing_time = datetime.datetime.fromtimestamp(start_time) + datetime.timedelta(hours=8)
            log_filename = f"run_{beijing_time.strftime('%Y%m%d_%H%M%S')}.log"
            log_file_path = os.path.join(info_dir, log_filename)
            logger.info(f"创建日志文件: {log_file_path}")
        
        # 启动进程
        cmd = ['python', 'vm_management_workflow.py']
        logger.info(f"启动命令: {cmd}")
        
        # 启动进程，不使用text模式，直接处理字节流
        running_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,  # 不使用text模式，直接获取字节流
            bufsize=1,
            universal_newlines=False
        )
        
        # 实时读取输出
        while True:
            try:
                # 读取一行字节
                line_bytes = running_process.stdout.readline()
                if not line_bytes:
                    break
                
                # 尝试使用多种编码解码，提高可靠性
                encoding_attempts = ['utf-8', 'gbk', 'utf-16', 'latin-1']
                line = None
                
                for encoding in encoding_attempts:
                    try:
                        line = line_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                # 如果所有编码都失败，使用replace模式
                if line is None:
                    line = line_bytes.decode('utf-8', errors='replace')
            except Exception as decode_e:
                # 处理解码过程中的其他错误
                logger.error(f"解码输出失败: {decode_e}")
                line = str(line_bytes)
            
            stripped_line = line.strip()
            process_output.append(stripped_line)
            logger.info(f"程序输出: {stripped_line}")
            
            # 实时保存到日志文件
            if log_file_path:
                try:
                    with open(log_file_path, 'a', encoding='utf-8') as f:
                        f.write(f"{stripped_line}\n")
                except Exception as e:
                    logger.error(f"保存日志失败: {e}")
                    # 尝试使用其他编码保存
                    try:
                        with open(log_file_path, 'a', encoding='gbk') as f:
                            f.write(f"{stripped_line}\n")
                    except Exception as e2:
                        logger.error(f"使用gbk编码保存日志也失败: {e2}")
        
        # 等待进程结束
        running_process.wait()
        
        if running_process.returncode == 0:
            process_status = 'completed'
            logger.info("程序运行成功")
        else:
            process_status = 'error'
            logger.error(f"程序运行失败，退出码: {running_process.returncode}")
            
    except Exception as e:
        error_msg = f"运行出错: {e}"
        process_status = 'error'
        process_output.append(error_msg)
        logger.error(f"运行程序失败: {e}")
        
        # 保存错误信息到日志文件
        if log_file_path:
            try:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{error_msg}\n")
            except Exception as e:
                logger.error(f"保存错误日志失败: {e}")
    finally:
        # 完成运行记录
        finish_last_run()
        running_process = None

# 更新上一次运行时间
def update_last_run_time():
    """更新上一次运行的开始时间"""
    global last_run_info
    last_run_info['start_time'] = time.time()
    last_run_info['end_time'] = None
    last_run_info['screenshots'] = []
    logger.info(f"更新运行开始时间: {last_run_info['start_time']}")

# 完成上一次运行
def finish_last_run():
    """完成上一次运行，记录结束时间并扫描截图"""
    global last_run_info
    last_run_info['end_time'] = time.time()
    last_run_info['screenshots'] = scan_last_run_screenshots()
    logger.info(f"更新运行结束时间: {last_run_info['end_time']}")
    logger.info(f"上一次运行产生 {len(last_run_info['screenshots'])} 个截图")

# 扫描上一次运行的截图
def scan_last_run_screenshots():
    """扫描上一次运行产生的截图"""
    screenshots = []
    screenshot_dirs = ['KB_photo', 'KB_compare_photo']
    start_time = last_run_info.get('start_time')
    end_time = last_run_info.get('end_time', time.time())
    
    if not start_time:
        logger.warning("未记录运行开始时间，无法扫描截图")
        return screenshots
    
    for dir_name in screenshot_dirs:
        if os.path.exists(dir_name):
            for filename in os.listdir(dir_name):
                if filename.endswith('.png'):
                    file_path = os.path.join(dir_name, filename)
                    if os.path.isfile(file_path):
                        try:
                            file_mtime = os.path.getmtime(file_path)
                            # 检查是否在上一次运行时间范围内
                            if start_time <= file_mtime <= end_time:
                                screenshots.append({
                                    'filename': filename,
                                    'path': file_path,
                                    'size': os.path.getsize(file_path),
                                    'mtime': file_mtime,
                                    'folder': dir_name
                                })
                        except Exception as e:
                            logger.error(f"获取文件信息失败: {e}")
    
    # 按修改时间排序，最新的在前
    screenshots.sort(key=lambda x: x['mtime'], reverse=True)
    return screenshots

# 停止运行中的程序
def stop_vm_management():
    """停止运行中的vm_management程序"""
    global running_process, process_output, process_status
    
    if running_process:
        try:
            running_process.terminate()
            running_process.wait(timeout=5)
            process_status = 'stopped'
            process_output.append("程序已手动停止")
            logger.info("程序已手动停止")
            # 完成运行记录
            finish_last_run()
        except Exception as e:
            logger.error(f"停止程序失败: {e}")
    
    return process_status

# 主页面
@app.route('/', methods=['GET', 'POST'])
def index():
    """主页面，显示配置和处理表单提交"""
    if request.method == 'POST':
        # 处理配置保存
        if request.form.get('action') == 'save':
            # 构建配置字典
            config_dict = {}
            
            # 读取所有表单数据
            for key, value in request.form.items():
                if '.' in key:
                    section, option = key.split('.', 1)
                    if section not in config_dict:
                        config_dict[section] = {}
                    # 处理history_packages的多个输入字段
                    if section == 'kb_compare' and option.startswith('history_packages') and not option.endswith('count'):
                        # 跳过单个输入字段，稍后统一处理
                        continue
                    config_dict[section][option] = value
            
            # 处理kb_compare的history_packages多个输入字段
            if 'kb_compare' in config_dict:
                # 收集所有history_packages输入字段
                packages = []
                count = int(request.form.get('kb_compare.history_packages.count', 0))
                for i in range(count):
                    pkg_value = request.form.get(f'kb_compare.history_packages.{i}', '').strip()
                    if pkg_value:
                        packages.append(pkg_value)
                # 将多个包用逗号连接
                if packages:
                    config_dict['kb_compare']['history_packages'] = ','.join(packages)
                else:
                    config_dict['kb_compare']['history_packages'] = ''
            
            # 保存配置
            if save_config(config_dict):
                message = '配置保存成功！'
                message_type = 'success'
            else:
                message = '配置保存失败，请查看日志。'
                message_type = 'error'
            
            # 重新读取配置
            config_data = read_config()
            return render_template_string(index_template, 
                                        config_data=config_data, 
                                        message=message, 
                                        message_type=message_type, 
                                        process_status=process_status, 
                                        process_output=process_output)
        
        # 处理程序运行
        elif request.form.get('action') == 'run':
            # 检查是否已有程序在运行
            if process_status == 'running':
                message = '程序正在运行中，请先停止当前运行的程序。'
                message_type = 'warning'
            else:
                # 启动新线程运行程序
                thread = threading.Thread(target=run_vm_management)
                thread.daemon = True
                thread.start()
                message = '程序已开始运行，请查看下方运行状态。'
                message_type = 'info'
            
            config_data = read_config()
            return render_template_string(index_template, 
                                        config_data=config_data, 
                                        message=message, 
                                        message_type=message_type, 
                                        process_status=process_status, 
                                        process_output=process_output)
        
        # 处理程序停止
        elif request.form.get('action') == 'stop':
            status = stop_vm_management()
            message = f'程序已停止，状态: {status}'
            message_type = 'info'
            
            config_data = read_config()
            return render_template_string(index_template, 
                                        config_data=config_data, 
                                        message=message, 
                                        message_type=message_type, 
                                        process_status=process_status, 
                                        process_output=process_output)
        
        # 处理模块操作
        elif request.form.get('action').startswith('module_'):
            module_action = request.form.get('action')[7:]  # 去除 'module_' 前缀
            
            # 检查是否已有程序在运行
            if process_status == 'running':
                message = '程序正在运行中，请先停止当前运行的程序。'
                message_type = 'warning'
            else:
                # 启动新线程运行模块
                def run_module():
                    global process_output, process_status, running_process
                    
                    # 清空日志（只在模块开始时清空，运行结束后不清空）
                    process_output = []
                    process_status = 'running'
                    
                    # 初始化日志文件路径
                    log_file_path = None
                    
                    try:
                        # 更新运行开始时间
                        update_last_run_time()
                        
                        # 创建info文件夹
                        info_dir = 'info'
                        if not os.path.exists(info_dir):
                            os.makedirs(info_dir)
                            logger.info(f"创建info文件夹: {info_dir}")
                        
                        # 生成日志文件名（使用北京时间）
                        start_time = last_run_info.get('start_time')
                        if start_time:
                            # 使用datetime模块处理北京时间（UTC+8）
                            import datetime
                            # 北京时间比UTC早8小时
                            beijing_time = datetime.datetime.fromtimestamp(start_time) + datetime.timedelta(hours=8)
                            log_filename = f"module_{module_action}_{beijing_time.strftime('%Y%m%d_%H%M%S')}.log"
                            log_file_path = os.path.join(info_dir, log_filename)
                            logger.info(f"创建模块日志文件: {log_file_path}")
                        
                        # 执行指定模块
                        cmd = ['python', 'vm_management_workflow.py', '--module', module_action]
                        logger.info(f"启动模块命令: {cmd}")
                        
                        # 启动进程
                        running_process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=False,
                            bufsize=1,
                            universal_newlines=False
                        )
                        
                        # 实时读取输出
                        while True:
                            try:
                                # 读取一行字节
                                line_bytes = running_process.stdout.readline()
                                if not line_bytes:
                                    break
                                
                                # 尝试使用多种编码解码
                                encoding_attempts = ['utf-8', 'gbk', 'utf-16', 'latin-1']
                                line = None
                                
                                for encoding in encoding_attempts:
                                    try:
                                        line = line_bytes.decode(encoding)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                
                                # 如果所有编码都失败，使用replace模式
                                if line is None:
                                    line = line_bytes.decode('utf-8', errors='replace')
                                
                                stripped_line = line.strip()
                                process_output.append(stripped_line)
                                logger.info(f"模块输出: {stripped_line}")
                                
                                # 实时保存到日志文件
                                if log_file_path:
                                    try:
                                        with open(log_file_path, 'a', encoding='utf-8') as f:
                                            f.write(f"{stripped_line}\n")
                                    except Exception as e:
                                        logger.error(f"保存日志失败: {e}")
                                        # 尝试使用其他编码保存
                                        try:
                                            with open(log_file_path, 'a', encoding='gbk') as f:
                                                f.write(f"{stripped_line}\n")
                                        except Exception as e2:
                                            logger.error(f"使用gbk编码保存日志也失败: {e2}")
                            except Exception as e:
                                logger.error(f"读取进程输出时出错: {e}")
                                # 继续处理下一行
                                continue
                        
                        # 等待进程结束
                        running_process.wait()
                        
                        if running_process.returncode == 0:
                            process_status = 'completed'
                            logger.info("模块运行成功")
                        else:
                            process_status = 'error'
                            logger.error(f"模块运行失败，退出码: {running_process.returncode}")
                    except Exception as e:
                        error_msg = f"运行模块出错: {e}"
                        process_status = 'error'
                        process_output.append(error_msg)
                        logger.error(f"运行模块失败: {e}")
                        
                        # 保存错误信息到日志文件
                        if log_file_path:
                            try:
                                with open(log_file_path, 'a', encoding='utf-8') as f:
                                    f.write(f"{error_msg}\n")
                            except Exception as e:
                                logger.error(f"保存错误日志失败: {e}")
                    finally:
                        # 完成运行记录
                        finish_last_run()
                        running_process = None
                
                # 启动线程
                thread = threading.Thread(target=run_module)
                thread.daemon = True
                thread.start()
                message = f'模块 {module_action} 已开始运行，请查看下方运行状态。'
                message_type = 'info'
            
            config_data = read_config()
            return render_template_string(index_template, 
                                        config_data=config_data, 
                                        message=message, 
                                        message_type=message_type, 
                                        process_status=process_status, 
                                        process_output=process_output)
        
        # 处理刷新
        elif request.form.get('action') == 'refresh':
            config_data = read_config()
            return render_template_string(index_template, 
                                        config_data=config_data, 
                                        message='', 
                                        message_type='', 
                                        process_status=process_status, 
                                        process_output=process_output)
    
    # GET请求，显示配置
    config_data = read_config()
    return render_template_string(index_template, 
                                config_data=config_data, 
                                message='', 
                                message_type='', 
                                process_status=process_status, 
                                process_output=process_output)

# 获取程序运行状态
@app.route('/status')
def get_status():
    """获取程序运行状态"""
    global process_status, process_output
    
    return jsonify({
        'status': process_status,
        'output': process_output
    })

# 获取上一次运行的截图信息
@app.route('/last_run_screenshots')
def get_last_run_screenshots():
    """获取上一次运行的截图信息"""
    global last_run_info
    
    # 格式化截图信息
    formatted_screenshots = []
    for screenshot in last_run_info['screenshots']:
        formatted_screenshots.append({
            'filename': screenshot['filename'],
            'path': screenshot['path'],
            'size': screenshot['size'],
            'mtime': screenshot['mtime'],
            'folder': screenshot['folder']
        })
    
    return jsonify({
        'screenshots': formatted_screenshots,
        'start_time': last_run_info['start_time'],
        'end_time': last_run_info['end_time']
    })

# 刷新上一次运行的截图
@app.route('/refresh_last_run_screenshots')
def refresh_last_run_screenshots():
    """刷新上一次运行的截图列表"""
    global last_run_info
    last_run_info['screenshots'] = scan_last_run_screenshots()
    
    return jsonify({
        'screenshots': last_run_info['screenshots'],
        'count': len(last_run_info['screenshots'])
    })

# 提供截图文件访问
@app.route('/screenshot/<path:filename>')
def serve_screenshot(filename):
    """提供截图文件访问"""
    # 安全检查，防止路径遍历
    if '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    # 构建完整路径
    for dir_name in ['KB_photo', 'KB_compare_photo']:
        file_path = os.path.join(dir_name, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
    
    return jsonify({'error': 'Screenshot not found'}), 404

# 前端模板
index_template = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>配置管理系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .subtitle {
            text-align: center;
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .message {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            font-weight: 500;
        }
        
        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .message.warning {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .message.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            flex: 1;
            min-width: 120px;
        }
        
        .btn-primary {
            background-color: #4CAF50;
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #45a049;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background-color: #2196F3;
            color: white;
        }
        
        .btn-success:hover {
            background-color: #0b7dda;
            transform: translateY(-2px);
        }
        
        .btn-danger {
            background-color: #f44336;
            color: white;
        }
        
        .btn-danger:hover {
            background-color: #da190b;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background-color: #9e9e9e;
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #757575;
            transform: translateY(-2px);
        }
        
        .btn-info {
            background-color: #00bcd4;
            color: white;
        }
        
        .btn-info:hover {
            background-color: #00acc1;
            transform: translateY(-2px);
        }
        
        .config-sections {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .section-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .section-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .section-title {
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #444;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .config-item {
            margin-bottom: 15px;
        }
        
        .item-label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        
        .item-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        .item-input:focus {
            outline: none;
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }
        
        .item-input.password {
            font-family: 'Courier New', monospace;
        }
        
        .status-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .status-title {
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #444;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .status-indicator {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .status-idle {
            background-color: #e0e0e0;
            color: #666;
        }
        
        .status-running {
            background-color: #2196F3;
            color: white;
            animation: pulse 1.5s infinite;
        }
        
        .status-completed {
            background-color: #4CAF50;
            color: white;
        }
        
        .status-error {
            background-color: #f44336;
            color: white;
        }
        
        .status-stopped {
            background-color: #ff9800;
            color: white;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .output-container {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .output-line {
            margin-bottom: 5px;
            white-space: pre-wrap;
        }
        
        footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .config-sections {
                grid-template-columns: 1fr;
            }
            
            .actions {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
            }
            
            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>配置管理系统</h1>
            <p class="subtitle">统一管理 all.ini 配置文件</p>
        </header>
        
        {% if message %}
        <div class="message {{ message_type }}">
            {{ message }}
        </div>
        {% endif %}
        
        <form method="post">
            <div class="actions">
                <button type="submit" name="action" value="save" class="btn btn-primary">
                    保存配置
                </button>
                <button type="submit" name="action" value="run" class="btn btn-success">
                    运行程序
                </button>
                <button type="submit" name="action" value="stop" class="btn btn-danger">
                    停止程序
                </button>
                <button type="button" id="showScreenshotsBtn" class="btn btn-info">
                    截图展示
                </button>
                <button type="submit" name="action" value="refresh" class="btn btn-secondary">
                    刷新
                </button>
            </div>
            
            <h2 class="section-title">模块操作</h2>
            <div class="actions" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr); gap: 10px;">
                <button type="submit" name="action" value="module_prepare" class="btn btn-primary">
                    1. 准备
                </button>
                <button type="submit" name="action" value="module_download_kb" class="btn btn-primary">
                    2. 下载KB包
                </button>
                <button type="submit" name="action" value="module_kb_conflict" class="btn btn-primary">
                    3. KB冲突检测
                </button>
                <button type="submit" name="action" value="module_recover_snapshot" class="btn btn-primary">
                    4. 恢复快照与启动
                </button>
                <button type="submit" name="action" value="module_modify_ip" class="btn btn-primary">
                    5. 修改IP
                </button>
                <button type="submit" name="action" value="module_recover_customer_config" class="btn btn-primary">
                    6. 恢复客户配置
                </button>
                <button type="submit" name="action" value="module_check_reboot" class="btn btn-primary">
                    7. 检测重启
                </button>
                <button type="submit" name="action" value="module_upgrade_kb" class="btn btn-primary">
                    8. 升级KB包
                </button>
                <button type="submit" name="action" value="module_kb_scan" class="btn btn-primary">
                    9. KB扫描与报告
                </button>
            </div>
            
            <div class="config-sections">
                {% for section, options in config_data.items() %}
                {% if section != 'kb_scan_report' %}
                <div class="section-card">
                    <h2 class="section-title">{{ section }}</h2>
                    {% for key, value in options.items() %}
                    {% if section == 'kb_compare' and key == 'history_packages' %}
                    <div class="config-item">
                        <label class="item-label">{{ key }}</label>
                        <div id="historyPackagesContainer">
                            {% set packages = value.split(',') if value else [] %}
                            {% for pkg in packages %}
                            <div class="package-input-group" style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                <input 
                                    type="text" 
                                    name="{{ section }}.{{ key }}.{{ loop.index0 }}" 
                                    value="{{ pkg.strip() }}" 
                                    class="item-input" 
                                    style="flex: 1;"
                                >
                                <button type="button" class="btn btn-danger" onclick="removePackageInput(this)" style="padding: 6px 12px; font-size: 14px;">
                                    删除
                                </button>
                            </div>
                            {% endfor %}
                            {% if packages|length == 0 %}
                            <div class="package-input-group" style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                <input 
                                    type="text" 
                                    name="{{ section }}.{{ key }}.0" 
                                    value="" 
                                    class="item-input" 
                                    style="flex: 1;"
                                >
                                <button type="button" class="btn btn-danger" onclick="removePackageInput(this)" style="padding: 6px 12px; font-size: 14px;">
                                    删除
                                </button>
                            </div>
                            {% endif %}
                        </div>
                        <button type="button" class="btn btn-primary" onclick="addPackageInput()" style="margin-top: 10px; padding: 8px 16px;">
                            添加KB包
                        </button>
                        <input type="hidden" name="{{ section }}.{{ key }}.count" value="{{ packages|length if packages else 1 }}">
                    </div>
                    {% else %}
                    <div class="config-item">
                        <label class="item-label" for="{{ section }}.{{ key }}">{{ key }}</label>
                        <input 
                            type="text" 
                            id="{{ section }}.{{ key }}" 
                            name="{{ section }}.{{ key }}" 
                            value="{{ value }}" 
                            class="item-input"
                        >
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
                {% endif %}
                {% endfor %}
            </div>
        </form>
        
        <div class="status-section">
            <h2 class="status-title">程序运行状态</h2>
            <div class="output-container" style="max-height: 400px; overflow-y: auto;">
                {% for line in process_output %}
                <div class="output-line">{{ line }}</div>
                {% else %}
                <div class="output-line">暂无输出</div>
                {% endfor %}
            </div>
        </div>
        
        <footer>
            <p>© 2026 配置管理系统</p>
        </footer>
    </div>
    
    <!-- 截图展示模态框 -->
    <div id="screenshotsModal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.9);">
        <div class="modal-content" style="background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 90%; max-width: 1200px; border-radius: 10px;">
            <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; font-size: 1.5em;">上一次运行截图展示</h2>
                <span class="close" style="color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer;">&times;</span>
            </div>
            <div class="modal-body">
                <div id="screenshotsContainer" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">
                    <!-- 截图将通过JavaScript动态添加 -->
                    <div style="grid-column: 1 / -1; text-align: center; padding: 50px; color: #666;">
                        加载中...
                    </div>
                </div>
            </div>
            <div class="modal-footer" style="display: flex; justify-content: flex-end; margin-top: 20px; gap: 10px;">
                <button id="refreshScreenshotsBtn" class="btn btn-secondary" style="padding: 8px 16px;">
                    刷新截图
                </button>
                <button id="closeScreenshotsBtn" class="btn btn-primary" style="padding: 8px 16px;">
                    关闭
                </button>
            </div>
        </div>
    </div>

    <!-- 图片预览模态框 -->
    <div id="imagePreviewModal" class="modal" style="display: none; position: fixed; z-index: 1100; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.9);">
        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <span class="close" style="position: absolute; top: 20px; right: 30px; color: white; font-size: 40px; font-weight: bold; cursor: pointer;">&times;</span>
            <img id="previewImage" src="" style="max-width: 90%; max-height: 90%; object-fit: contain; border: 2px solid white; border-radius: 5px;">
        </div>
    </div>

    <script>
        // 动态添加和删除history_packages输入字段
        function addPackageInput() {
            const container = document.getElementById('historyPackagesContainer');
            const inputGroups = container.querySelectorAll('.package-input-group');
            const newIndex = inputGroups.length;
            
            const newInputGroup = document.createElement('div');
            newInputGroup.className = 'package-input-group';
            newInputGroup.style = 'display: flex; align-items: center; gap: 10px; margin-bottom: 10px;';
            
            newInputGroup.innerHTML = `
                <input 
                    type="text" 
                    name="kb_compare.history_packages.${newIndex}" 
                    value="" 
                    class="item-input" 
                    style="flex: 1;"
                >
                <button type="button" class="btn btn-danger" onclick="removePackageInput(this)" style="padding: 6px 12px; font-size: 14px;">
                    删除
                </button>
            `;
            
            container.appendChild(newInputGroup);
            
            // 更新计数器
            const countInput = document.querySelector('input[name="kb_compare.history_packages.count"]');
            if (countInput) {
                countInput.value = newIndex + 1;
            }
        }
        
        function removePackageInput(button) {
            const inputGroup = button.closest('.package-input-group');
            if (inputGroup) {
                inputGroup.remove();
                
                // 更新剩余输入字段的索引
                const container = document.getElementById('historyPackagesContainer');
                const inputGroups = container.querySelectorAll('.package-input-group');
                
                inputGroups.forEach((group, index) => {
                    const input = group.querySelector('input');
                    if (input) {
                        input.name = `kb_compare.history_packages.${index}`;
                    }
                });
                
                // 更新计数器
                const countInput = document.querySelector('input[name="kb_compare.history_packages.count"]');
                if (countInput) {
                    countInput.value = inputGroups.length;
                }
            }
        }

        // 自动刷新输出
        setInterval(function() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    // 检查状态变化，更新现有条幅内容
                    if (data.status === 'completed' || data.status === 'error') {
                        // 查找现有的消息条幅
                        const existingMessageDiv = document.querySelector('.message');
                        if (existingMessageDiv) {
                            // 更新现有条幅内容
                            existingMessageDiv.className = 'message info';
                            existingMessageDiv.textContent = '已结束';
                        }
                    }
                    
                    // 更新输出
                    const outputContainer = document.querySelector('.output-container');
                    if (outputContainer) {
                        // 记录当前滚动位置和高度
                        const wasAtBottom = outputContainer.scrollTop >= outputContainer.scrollHeight - outputContainer.clientHeight - 10;
                        
                        outputContainer.innerHTML = '';
                        data.output.forEach(line => {
                            const lineElement = document.createElement('div');
                            lineElement.className = 'output-line';
                            lineElement.textContent = line;
                            outputContainer.appendChild(lineElement);
                        });
                        
                        // 只有当用户接近底部时才自动滚动
                        if (wasAtBottom) {
                            outputContainer.scrollTop = outputContainer.scrollHeight;
                        }
                    }
                });
        }, 1000); // 每1秒刷新一次

        // 截图展示功能
        document.addEventListener('DOMContentLoaded', function() {
            // 获取模态框元素
            const screenshotsModal = document.getElementById('screenshotsModal');
            const imagePreviewModal = document.getElementById('imagePreviewModal');
            const screenshotsContainer = document.getElementById('screenshotsContainer');
            const previewImage = document.getElementById('previewImage');
            
            // 获取按钮元素
            const showScreenshotsBtn = document.getElementById('showScreenshotsBtn');
            const closeScreenshotsBtn = document.getElementById('closeScreenshotsBtn');
            const refreshScreenshotsBtn = document.getElementById('refreshScreenshotsBtn');
            
            // 获取关闭按钮
            const closeButtons = document.querySelectorAll('.modal .close');
            
            // 打开截图展示模态框
            showScreenshotsBtn.addEventListener('click', function() {
                screenshotsModal.style.display = 'block';
                loadScreenshots();
            });
            
            // 关闭截图展示模态框
            closeScreenshotsBtn.addEventListener('click', function() {
                screenshotsModal.style.display = 'none';
            });
            
            // 关闭模态框
            closeButtons.forEach(function(button) {
                button.addEventListener('click', function() {
                    screenshotsModal.style.display = 'none';
                    imagePreviewModal.style.display = 'none';
                });
            });
            
            // 刷新截图
            refreshScreenshotsBtn.addEventListener('click', function() {
                loadScreenshots();
            });
            
            // 点击模态框外部关闭
            window.addEventListener('click', function(event) {
                if (event.target == screenshotsModal) {
                    screenshotsModal.style.display = 'none';
                }
                if (event.target == imagePreviewModal) {
                    imagePreviewModal.style.display = 'none';
                }
            });
            
            // 加载截图
            function loadScreenshots() {
                screenshotsContainer.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 50px; color: #666;">加载中...</div>';
                
                fetch('/last_run_screenshots')
                    .then(response => response.json())
                    .then(data => {
                        if (data.screenshots && data.screenshots.length > 0) {
                            screenshotsContainer.innerHTML = '';
                            
                            data.screenshots.forEach(function(screenshot) {
                                // 创建截图卡片
                                const screenshotCard = document.createElement('div');
                                screenshotCard.style.cssText = `
                                    border: 1px solid #ddd;
                                    border-radius: 5px;
                                    padding: 10px;
                                    text-align: center;
                                    background: #f9f9f9;
                                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                                `;
                                
                                // 添加悬停效果
                                screenshotCard.addEventListener('mouseenter', function() {
                                    screenshotCard.style.transform = 'translateY(-5px)';
                                    screenshotCard.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
                                });
                                
                                screenshotCard.addEventListener('mouseleave', function() {
                                    screenshotCard.style.transform = 'translateY(0)';
                                    screenshotCard.style.boxShadow = 'none';
                                });
                                
                                // 创建缩略图
                                const thumbnail = document.createElement('div');
                                thumbnail.style.cssText = `
                                    width: 100%;
                                    height: 150px;
                                    background: #f0f0f0;
                                    border-radius: 3px;
                                    overflow: hidden;
                                    margin-bottom: 10px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    cursor: pointer;
                                `;
                                
                                // 创建图片元素
                                const img = document.createElement('img');
                                img.src = `/screenshot/${screenshot.filename}`;
                                img.alt = screenshot.filename;
                                img.style.cssText = `
                                    max-width: 100%;
                                    max-height: 100%;
                                    object-fit: contain;
                                `;
                                
                                // 图片加载错误处理
                                img.onerror = function() {
                                    thumbnail.innerHTML = '<div style="color: #666; font-size: 14px;">图片加载失败</div>';
                                };
                                
                                // 点击图片预览
                                img.addEventListener('click', function() {
                                    previewImage.src = `/screenshot/${screenshot.filename}`;
                                    imagePreviewModal.style.display = 'block';
                                });
                                
                                thumbnail.appendChild(img);
                                
                                // 创建文件名
                                const filename = document.createElement('div');
                                filename.textContent = screenshot.filename;
                                filename.style.cssText = `
                                    font-size: 12px;
                                    margin-bottom: 5px;
                                    word-break: break-all;
                                    color: #333;
                                `;
                                
                                // 创建文件信息
                                const fileInfo = document.createElement('div');
                                const size = (screenshot.size / 1024).toFixed(2);
                                const date = new Date(screenshot.mtime * 1000).toLocaleString();
                                fileInfo.innerHTML = `
                                    <div style="font-size: 10px; color: #666; margin-bottom: 2px;">${size} KB</div>
                                    <div style="font-size: 10px; color: #666;">${date}</div>
                                `;
                                
                                // 创建下载链接
                                const downloadLink = document.createElement('a');
                                downloadLink.href = `/screenshot/${screenshot.filename}`;
                                downloadLink.download = screenshot.filename;
                                downloadLink.textContent = '下载';
                                downloadLink.style.cssText = `
                                    display: inline-block;
                                    margin-top: 10px;
                                    padding: 4px 8px;
                                    background: #4CAF50;
                                    color: white;
                                    text-decoration: none;
                                    border-radius: 3px;
                                    font-size: 12px;
                                    transition: background 0.3s ease;
                                `;
                                
                                downloadLink.addEventListener('mouseenter', function() {
                                    downloadLink.style.background = '#45a049';
                                });
                                
                                downloadLink.addEventListener('mouseleave', function() {
                                    downloadLink.style.background = '#4CAF50';
                                });
                                
                                // 组装卡片
                                screenshotCard.appendChild(thumbnail);
                                screenshotCard.appendChild(filename);
                                screenshotCard.appendChild(fileInfo);
                                screenshotCard.appendChild(downloadLink);
                                
                                // 添加到容器
                                screenshotsContainer.appendChild(screenshotCard);
                            });
                        } else {
                            screenshotsContainer.innerHTML = `
                                <div style="grid-column: 1 / -1; text-align: center; padding: 50px; color: #666;">
                                    <p>上一次运行未产生截图</p>
                                    <p style="font-size: 14px; margin-top: 10px;">请先运行程序生成截图</p>
                                </div>
                            `;
                        }
                    })
                    .catch(function(error) {
                        console.error('加载截图失败:', error);
                        screenshotsContainer.innerHTML = `
                            <div style="grid-column: 1 / -1; text-align: center; padding: 50px; color: #f44336;">
                                加载截图失败，请重试
                            </div>
                        `;
                    });
            }
            

        });
    </script>
</body>
</html>
'''

# 定时清理任务
import threading
import datetime

def schedule_cleanup():
    """定时执行清理任务，每天24:00执行"""
    while True:
        try:
            # 获取当前时间
            now = datetime.datetime.now()
            
            # 计算到今天24:00的时间差
            next_cleanup = now.replace(hour=24, minute=0, second=0, microsecond=0)
            if now.hour >= 24:
                # 如果当前时间已经过了24:00，设置为明天24:00
                next_cleanup += datetime.timedelta(days=1)
            
            # 计算等待时间（秒）
            wait_seconds = (next_cleanup - now).total_seconds()
            logger.info(f"下次清理时间: {next_cleanup}, 等待 {wait_seconds} 秒")
            
            # 等待到指定时间
            time.sleep(wait_seconds)
            
            # 执行清理
            logger.info("开始执行定时清理任务")
            cleanup_old_files()
            logger.info("定时清理任务执行完成")
            
        except Exception as e:
            logger.error(f"定时清理任务出错: {e}")
            # 出错后等待1小时再尝试
            time.sleep(3600)

if __name__ == '__main__':
    # 启动定时清理线程
    cleanup_thread = threading.Thread(target=schedule_cleanup, daemon=True)
    cleanup_thread.start()
    logger.info("定时清理线程已启动")
    
    # 启动Flask应用
    logger.info("启动配置管理系统")
    logger.info("访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)