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


def setup_logging():
    """配置详细的日志记录"""
    log_file = os.path.join(LOG_DIR, f"emotion_labeling_{datetime.now().strftime('%Y%m%d')}.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)

    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.disabled = True

    return root_logger


def create_application():
    """创建Flask应用实例"""
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import create_app
    return create_app()


def get_local_ip():
    """获取本机非回环IP地址，仅用于显示外部访问地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    logger = setup_logging()
    logger.info("正在启动情感标注系统（本地反代模式）...")
    emotion_logger.log_system_event("系统启动", {"module": "start_server_local.py"})

    app = create_application()
    logger.info("Flask应用创建完成")
    emotion_logger.log_system_event("应用加载完成", {"app_type": "Flask应用"})

    public_ip = get_local_ip()
    host = "127.0.0.1"
    port = 5001

    print("\n" + "=" * 60)
    print("情感标注系统已启动（本地反代模式）!")
    print(f"Flask 监听: http://{host}:{port}")
    print(f"对外访问: http://{public_ip}:5000")
    print(f"日志保存在: {LOG_DIR}")
    print("按Ctrl+C停止服务器")
    print("=" * 60 + "\n")

    logger.info(f"服务器正在监听: {host}:{port}")
    emotion_logger.log_system_event("服务器启动", {"host": host, "port": port, "debug": True})

    try:
        app.run(host=host, port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("服务器关闭")
        emotion_logger.log_system_event("服务器关闭", {"reason": "用户中断"})
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}", exc_info=True)
        emotion_logger.log_error(e, "服务器启动失败", traceback_info=str(e))
        print(f"\n发生错误: {str(e)}")
    finally:
        logger.info("服务器关闭")
