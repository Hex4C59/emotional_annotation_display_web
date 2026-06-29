import os
import socket
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from utils.logger import emotion_logger

# 加载环境变量
load_dotenv()

# 创建日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
def setup_logging():
    """配置详细的日志记录"""
    # 创建日志文件名（按日期）
    log_file = os.path.join(LOG_DIR, f"emotion_labeling_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # 控制台只显示警告及以上级别
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    # 创建文件处理器（滚动日志，最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)  # 文件记录INFO及以上级别
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 禁用werkzeug默认日志
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.disabled = True
    
    return root_logger

def create_application():
    """创建Flask应用实例"""
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import create_app
    return create_app()

def get_local_ip():
    """获取本机非回环IP地址"""
    try:
        # 创建一个临时套接字来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个外部地址（不会真实发送数据）
        s.connect(("8.8.8.8", 80))
        # 获取本机IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

if __name__ == "__main__":
    # 设置日志
    logger = setup_logging()
    logger.info("正在启动情感标注系统...")
    emotion_logger.log_system_event("系统启动", {"module": "app.py"})
    
    # 创建Flask应用
    app = create_application()
    logger.info("Flask应用创建完成")
    emotion_logger.log_system_event("应用加载完成", {"app_type": "Flask应用"})
    
    # 使用本机IP地址（或使用0.0.0.0监听所有接口）
    ip_address = get_local_ip()  # 或者使用 "0.0.0.0"
    #port = 5000
    #2025年9月7日 端口修改为8000
    port = 5001
    # 显示自定义启动消息
    print("\n" + "=" * 60)
    print("情感标注系统已启动!")
    print(f"请访问: http://{ip_address}:{port}")
    print(f"日志保存在: {LOG_DIR}")
    print("按Ctrl+C停止服务器")
    print("=" * 60 + "\n")
    
    # 记录应用启动信息
    logger.info(f"服务器正在监听: {ip_address}:{port}")
    emotion_logger.log_system_event("服务器启动", {"host": ip_address, "port": port, "debug": True})
    
    try:
        # 运行Flask应用
        app.run(host=ip_address, port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("服务器关闭")
        emotion_logger.log_system_event("服务器关闭", {"reason": "用户中断"})
    except Exception as e:
        # 记录异常
        logger.error(f"服务器错误: {str(e)}", exc_info=True)
        emotion_logger.log_error(e, "服务器启动失败", traceback_info=str(e))
        print(f"\n发生错误: {str(e)}")
    finally:
        # 记录关闭信息
        logger.info("服务器关闭")