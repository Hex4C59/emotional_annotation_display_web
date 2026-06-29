from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
from utils.logger import emotion_logger
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from routes.test_routes import test_bp
from routes.consistency_routes import consistency_bp

from routes.group_routes import group_bp
from routes.standard_answers_routes import standard_answers_bp
from routes.lansys_proxy import lansys_proxy_bp
from routes.manager_proxy import manager_proxy_bp
from utils.count_audio_files import update_audio_count_in_system

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 验证关键配置
    try:
        Config.validate_config()
    except ValueError as e:
        emotion_logger.log_error(e, "配置验证失败")
        print(f"配置错误: {e}")
        print("请设置必要的环境变量后重新启动应用。")
        exit(1)
    
    # 配置安全的session（配置已在Config类中设置）
    from datetime import timedelta
    app.permanent_session_lifetime = timedelta(seconds=Config.PERMANENT_SESSION_LIFETIME)
    
    # 初始化配置
    Config.init_directories()
    
    # 添加favicon路由
    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.ico')
    
    # 注册蓝图（Lansys 反向代理须优先，避免与其它规则冲突）
    app.register_blueprint(lansys_proxy_bp)
    app.register_blueprint(manager_proxy_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(test_bp)  # 移除url_prefix，因为test_routes.py中已经包含了完整路径
    app.register_blueprint(consistency_bp)  # 注册一致性测试路由

    app.register_blueprint(group_bp)  # 注册分组管理路由
    app.register_blueprint(standard_answers_bp)  # 注册标准答案管理路由
    
    return app

# 为了兼容现有的启动脚本
app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
