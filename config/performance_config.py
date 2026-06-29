#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化配置
用于调整数据库和应用性能相关参数
"""

class PerformanceConfig:
    """
    性能优化配置类
    """
    
    # 数据库连接优化
    DB_TIMEOUT = 30.0  # 数据库连接超时时间（秒）
    DB_CACHE_SIZE = 10000  # 数据库缓存大小
    DB_MMAP_SIZE = 268435456  # 内存映射大小（256MB）
    
    # 重试机制优化
    MAX_RETRIES = 2  # 最大重试次数
    RETRY_DELAY = 0.05  # 基础重试延迟（秒）
    
    # 事务优化
    USE_DEFERRED_TRANSACTION = True  # 使用延迟事务模式
    BATCH_SIZE = 100  # 批量操作大小
    
    # 并发优化
    ENABLE_WAL_MODE = True  # 启用WAL模式
    ENABLE_SYNCHRONOUS_NORMAL = True  # 使用NORMAL同步模式
    
    # 功能开关
    ENABLE_AUTO_GROUP_PROGRESS_UPDATE = False  # 禁用自动分组进度更新
    ENABLE_DETAILED_LOGGING = False  # 禁用详细日志记录
    
    # 前端优化
    SAVE_DEBOUNCE_DELAY = 300  # 保存防抖延迟（毫秒）
    AUTO_SAVE_INTERVAL = 5000  # 自动保存间隔（毫秒）
    
    @classmethod
    def get_db_pragmas(cls):
        """
        获取数据库PRAGMA设置
        
        Returns:
            list: PRAGMA命令列表
        """
        pragmas = []
        
        if cls.ENABLE_WAL_MODE:
            pragmas.append('PRAGMA journal_mode=WAL;')
        
        if cls.ENABLE_SYNCHRONOUS_NORMAL:
            pragmas.append('PRAGMA synchronous=NORMAL;')
        
        pragmas.extend([
            f'PRAGMA cache_size={cls.DB_CACHE_SIZE};',
            'PRAGMA temp_store=memory;',
            f'PRAGMA mmap_size={cls.DB_MMAP_SIZE};',
            'PRAGMA optimize;'  # 自动优化
        ])
        
        return pragmas
    
    @classmethod
    def get_transaction_mode(cls):
        """
        获取事务模式
        
        Returns:
            str: 事务模式
        """
        return 'BEGIN DEFERRED;' if cls.USE_DEFERRED_TRANSACTION else 'BEGIN IMMEDIATE;'