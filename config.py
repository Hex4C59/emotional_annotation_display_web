import os

class Config:
    """应用配置"""
    print(f"DEBUG: os.getenv('AUDIO_FOLDER') = {os.getenv('AUDIO_FOLDER')}")
    AUDIO_FOLDER = os.getenv(
        "AUDIO_FOLDER", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "gzx_data")
    )
    print(f"DEBUG: Final AUDIO_FOLDER = {AUDIO_FOLDER}")
    DATABASE_FOLDER = os.getenv(
        "DATABASE_FOLDER", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
    )
    TEST_AUDIO_FOLDER = os.getenv(
        "TEST_AUDIO_FOLDER",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_examples")
    )
    
    # Flask配置
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = "10.10.16.135"
    PORT = 5000
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV', 'development') == 'production'
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600 * 24  # 24小时
    
    @classmethod
    def validate_config(cls):
        """验证关键配置项"""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY环境变量必须设置！请设置一个强随机密钥。")
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY长度至少需要32个字符！")

    # 测试配置
    TEST_QUESTION_LIMIT = 34  # 测试题目数量限制
    TEST_PASS_THRESHOLD = 85  # 测试通过阈值（百分比）
    CONSISTENCY_TEST_AUDIO_COUNT = 50  # 一致性测试音频数量
    SECOND_CONSISTENCY_TEST_THRESHOLD = 8000  # 第二次一致性测试的标注数量阈值
    
    # 切换量表按钮显示配置
    SCALE_SWITCH_BUTTON_MIN_ANNOTATIONS = 2  # 显示切换量表按钮所需的最小标注数量
    
    # 计时器配置
    REST_REMINDER_INTERVAL = 30  # 休息提醒间隔（分钟）
    
    # 管理员密码配置
    ADMIN_PASSWORD_MIN_LENGTH = 8  # 管理员密码最小长度
    ADMIN_PASSWORD_MAX_LENGTH = 128  # 管理员密码最大长度
    ADMIN_PASSWORD_REQUIRE_UPPERCASE = True  # 是否要求包含大写字母
    ADMIN_PASSWORD_REQUIRE_LOWERCASE = True  # 是否要求包含小写字母
    ADMIN_PASSWORD_REQUIRE_DIGIT = True  # 是否要求包含数字
    ADMIN_PASSWORD_REQUIRE_SPECIAL = True  # 是否要求包含特殊字符
    ADMIN_PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"  # 允许的特殊字符
    ADMIN_PASSWORD_CHANGE_INTERVAL = 90  # 密码修改间隔天数（0表示不限制）
    ADMIN_PASSWORD_MAX_ATTEMPTS = 5  # 密码错误最大尝试次数
    ADMIN_PASSWORD_LOCKOUT_TIME = 300  # 账户锁定时间（秒）
    
    # 确保必要目录存在
    @classmethod
    def init_directories(cls):
        os.makedirs(cls.DATABASE_FOLDER, exist_ok=True)
        # os.makedirs(cls.ORDER_LIST_FOLDER, exist_ok=True)  # 已迁移到数据库
    
    @classmethod
    def validate_admin_password(cls, password: str) -> tuple[bool, str]:
        """
        验证管理员密码是否符合复杂度要求
        
        Args:
            password (str): 待验证的密码
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        import re
        
        if not password:
            return False, "密码不能为空"
            
        if len(password) < cls.ADMIN_PASSWORD_MIN_LENGTH:
            return False, f"密码长度不能少于{cls.ADMIN_PASSWORD_MIN_LENGTH}位"
            
        if len(password) > cls.ADMIN_PASSWORD_MAX_LENGTH:
            return False, f"密码长度不能超过{cls.ADMIN_PASSWORD_MAX_LENGTH}位"
            
        if cls.ADMIN_PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "密码必须包含至少一个大写字母"
            
        if cls.ADMIN_PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "密码必须包含至少一个小写字母"
            
        if cls.ADMIN_PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "密码必须包含至少一个数字"
            
        if cls.ADMIN_PASSWORD_REQUIRE_SPECIAL:
            special_chars_pattern = f"[{re.escape(cls.ADMIN_PASSWORD_SPECIAL_CHARS)}]"
            if not re.search(special_chars_pattern, password):
                return False, f"密码必须包含至少一个特殊字符：{cls.ADMIN_PASSWORD_SPECIAL_CHARS}"
                
        return True, "密码符合要求"