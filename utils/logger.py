#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志管理模块
提供项目统一的日志记录功能，包括用户操作、系统事件、错误处理等
"""

import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from functools import wraps
from flask import request, session

class EmotionLogger:
    """
    情感标注系统专用日志记录器
    提供不同类型的日志记录功能
    """
    
    def __init__(self, log_dir=None):
        """
        初始化日志记录器
        
        Args:
            log_dir (str): 日志目录路径，默认为项目根目录下的logs文件夹
        """
        if log_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(project_root, 'logs')
        
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建不同类型的日志记录器
        self.system_logger = self._create_logger('system', 'system.log')
        self.user_logger = self._create_logger('user_activity', 'user_activity.log')
        self.error_logger = self._create_logger('error', 'error.log')
        self.api_logger = self._create_logger('api', 'api.log')
        self.database_logger = self._create_logger('database', 'database.log')
    
    def _create_logger(self, name, filename):
        """
        创建指定名称和文件的日志记录器
        
        Args:
            name (str): 日志记录器名称
            filename (str): 日志文件名
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建文件处理器
        log_file = os.path.join(self.log_dir, filename)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=20*1024*1024,  # 20MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        
        return logger
    
    def log_system_event(self, event, details=None, level='info'):
        """
        记录系统事件
        
        Args:
            event (str): 事件描述
            details (dict): 事件详细信息
            level (str): 日志级别 ('info', 'warning', 'error')
        """
        message = f"[系统事件] {event}"
        if details:
            message += f" | 详情: {details}"
        
        getattr(self.system_logger, level.lower())(message)
    
    def log_user_activity(self, username, action, details=None, ip_address=None):
        """
        记录用户活动
        
        Args:
            username (str): 用户名
            action (str): 用户操作
            details (dict): 操作详细信息
            ip_address (str): 用户IP地址
        """
        message = f"[用户活动] 用户: {username} | 操作: {action}"
        
        if ip_address:
            message += f" | IP: {ip_address}"
        
        if details:
            message += f" | 详情: {details}"
        
        self.user_logger.info(message)
    
    def log_api_request(self, endpoint, method, username=None, params=None, response_status=None, duration=None):
        """
        记录API请求
        
        Args:
            endpoint (str): API端点
            method (str): HTTP方法
            username (str): 请求用户
            params (dict): 请求参数
            response_status (int): 响应状态码
            duration (float): 请求处理时长（秒）
        """
        message = f"[API请求] {method} {endpoint}"
        
        if username:
            message += f" | 用户: {username}"
        
        if response_status:
            message += f" | 状态: {response_status}"
        
        if duration:
            message += f" | 耗时: {duration:.3f}s"
        
        if params:
            # 过滤敏感信息
            safe_params = {k: v for k, v in params.items() if k not in ['password', 'token', 'secret']}
            message += f" | 参数: {safe_params}"
        
        self.api_logger.info(message)
    
    def log_database_operation(self, operation, table, username=None, details=None, success=True):
        """
        记录数据库操作
        
        Args:
            operation (str): 操作类型 (INSERT, UPDATE, DELETE, SELECT)
            table (str): 表名
            username (str): 操作用户
            details (dict): 操作详情
            success (bool): 操作是否成功
        """
        status = "成功" if success else "失败"
        message = f"[数据库操作] {operation} {table} - {status}"
        
        if username:
            message += f" | 用户: {username}"
        
        if details:
            message += f" | 详情: {details}"
        
        if success:
            self.database_logger.info(message)
        else:
            self.database_logger.error(message)
    
    def log_error(self, error, context=None, username=None, traceback_info=None):
        """
        记录错误信息
        
        Args:
            error (str or Exception): 错误信息或异常对象
            context (str): 错误上下文
            username (str): 相关用户
            traceback_info (str): 堆栈跟踪信息
        """
        if isinstance(error, Exception):
            error_msg = f"{type(error).__name__}: {str(error)}"
        else:
            error_msg = str(error)
        
        message = f"[错误] {error_msg}"
        
        if context:
            message += f" | 上下文: {context}"
        
        if username:
            message += f" | 用户: {username}"
        
        if traceback_info:
            message += f"\n堆栈跟踪:\n{traceback_info}"
        
        self.error_logger.error(message)
    
    def log_annotation_activity(self, username, speaker, audio_file, action, annotation_data=None):
        """
        记录标注相关活动
        
        Args:
            username (str): 用户名
            speaker (str): 说话人
            audio_file (str): 音频文件
            action (str): 操作类型 (save, load, update)
            annotation_data (dict): 标注数据
        """
        details = {
            'speaker': speaker,
            'audio_file': audio_file,
            'action': action
        }
        
        if annotation_data:
            # 记录标注的关键信息
            details.update({
                'v_value': annotation_data.get('v_value'),
                'a_value': annotation_data.get('a_value'),
                'emotion_type': annotation_data.get('emotion_type'),
                'discrete_emotion': annotation_data.get('discrete_emotion')
            })
        
        self.log_user_activity(username, f"标注{action}", details)

# 创建全局日志实例
emotion_logger = EmotionLogger()

def log_api_call(func):
    """
    API调用日志装饰器
    自动记录API请求的详细信息
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        # 获取请求信息
        endpoint = request.endpoint or 'unknown'
        method = request.method
        username = session.get('username', 'anonymous')
        
        # 获取请求参数
        params = {}
        if request.args:
            params.update(request.args.to_dict())
        # 安全地检查JSON数据，避免415错误
        try:
            if request.is_json and request.get_json(silent=True):
                params.update(request.get_json())
        except Exception:
            pass  # 忽略JSON解析错误
        
        try:
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 计算处理时间
            duration = time.time() - start_time
            
            # 获取响应状态
            status = getattr(result, 'status_code', 200)
            
            # 记录成功的API调用
            emotion_logger.log_api_request(
                endpoint=endpoint,
                method=method,
                username=username,
                params=params,
                response_status=status,
                duration=duration
            )
            
            return result
            
        except Exception as e:
            # 计算处理时间
            duration = time.time() - start_time
            
            # 记录失败的API调用
            emotion_logger.log_api_request(
                endpoint=endpoint,
                method=method,
                username=username,
                params=params,
                response_status=500,
                duration=duration
            )
            
            # 记录错误详情
            emotion_logger.log_error(
                error=e,
                context=f"API调用失败: {method} {endpoint}",
                username=username
            )
            
            raise
    
    return wrapper

def get_client_ip():
    """
    获取客户端IP地址
    
    Returns:
        str: 客户端IP地址
    """
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']