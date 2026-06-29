#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据库管理器
管理合并后的统一数据库的所有操作
"""

import os
import sys
import sqlite3
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
from threading import Lock, RLock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

class UnifiedDatabaseManager:
    """
    统一数据库管理器
    管理所有数据库操作的统一接口
    """
    
    def __init__(self):
        """初始化统一数据库管理器"""
        self.database_folder = Config.DATABASE_FOLDER
        self.db_path = os.path.join(self.database_folder, 'unified_emotion_system.db')
        
        # 使用RLock支持重入锁
        self.write_lock = RLock()
        self.read_lock = RLock()
        
        # 重试配置（优化性能）
        self.max_retries = 2  # 减少重试次数
        self.retry_delay = 0.05  # 减少重试延迟
        
        # 确保数据库文件夹存在
        os.makedirs(self.database_folder, exist_ok=True)
        
        # 初始化数据库
        self.init_database()
    

    def _create_connection(self) -> sqlite3.Connection:
        """创建数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # 启用WAL模式以提高并发性
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('PRAGMA cache_size=10000;')
        conn.execute('PRAGMA temp_store=memory;')
        conn.execute('PRAGMA mmap_size=268435456;')  # 256MB
        return conn
    
    @contextmanager
    def get_connection(self, timeout=10.0):
        """获取数据库连接（上下文管理器）"""
        # 直接创建新连接，避免连接池共享导致的并发问题
        conn = self._create_connection()
        
        try:
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def get_connection_legacy(self) -> sqlite3.Connection:
        """获取数据库连接（兼容旧代码）"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        return conn
    
    def get_users_connection(self) -> sqlite3.Connection:
        """获取用户数据库连接（统一数据库中的用户表）"""
        return self.get_connection_legacy()
    
    def init_database(self):
        """初始化数据库，创建所有必要的表"""
        if not os.path.exists(self.db_path):
            print(f"创建统一数据库: {self.db_path}")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建所有表
                self._create_all_tables(cursor)
                
                conn.commit()
    
    def _create_all_tables(self, cursor):
        """创建所有数据库表"""
        # 情感标注相关表
        self._create_emotion_labels_tables(cursor)
        
        # 创建索引和触发器
        self._create_indexes_and_triggers(cursor)
    
    def _create_emotion_labels_tables(self, cursor):
        """创建情感标注相关表"""
        # 主要标注数据表（5分量表）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT NOT NULL,
                speaker TEXT NOT NULL,
                username TEXT NOT NULL,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                audio_duration REAL DEFAULT 0,
                play_count INTEGER DEFAULT 0,
                va_complete BOOLEAN DEFAULT FALSE,
                discrete_complete BOOLEAN DEFAULT FALSE,
                va_scale TEXT DEFAULT '5_point',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(audio_file, speaker, username)
            )
        ''')
        
        # 9分量表专用数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_labels_9point (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT NOT NULL,
                speaker TEXT NOT NULL,
                username TEXT NOT NULL,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                audio_duration REAL DEFAULT 0,
                play_count INTEGER DEFAULT 0,
                va_complete BOOLEAN DEFAULT FALSE,
                discrete_complete BOOLEAN DEFAULT FALSE,
                va_scale TEXT DEFAULT '9_point',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(audio_file, speaker, username)
            )
        ''')
        
        # 一致性测试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consistency_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                audio_file TEXT NOT NULL,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, audio_file)
            )
        ''')
        
        # 第二次一致性测试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS second_consistency_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                audio_file TEXT NOT NULL,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, audio_file)
            )
        ''')
        
        # 标准答案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS standard_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT NOT NULL UNIQUE,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                audio_duration REAL,
                created_by TEXT DEFAULT '系统导入',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 第二次一致性测试标准答案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS second_consistency_standard_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT NOT NULL UNIQUE,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                audio_duration REAL,
                username TEXT,
                created_by TEXT DEFAULT '系统导入',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 测试答案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT NOT NULL UNIQUE,
                v_value REAL,
                a_value REAL,
                emotion_type TEXT,
                discrete_emotion TEXT,
                patient_status TEXT,
                audio_duration REAL,
                created_by TEXT DEFAULT '测试答案导入',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用户排序表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_speaker_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                speaker_order TEXT NOT NULL,
                group_id INTEGER DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username),
                FOREIGN KEY (group_id) REFERENCES group_status(group_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_audio_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                speaker TEXT NOT NULL,
                audio_order TEXT NOT NULL,
                group_id INTEGER DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, speaker),
                FOREIGN KEY (group_id) REFERENCES group_status(group_id)
            )
        ''')
    

    

    

    
    def _create_indexes_and_triggers(self, cursor):
        """创建索引和触发器"""
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audio_speaker_user ON emotion_labels(audio_file, speaker, username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_username_speaker ON emotion_labels(username, speaker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON emotion_labels(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_standard_audio_file ON standard_answers(audio_file)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_audio_file ON test_answers(audio_file)')

        
        # 创建触发器
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_emotion_labels_timestamp 
            AFTER UPDATE ON emotion_labels
            FOR EACH ROW
            BEGIN
                UPDATE emotion_labels SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_standard_answers_timestamp 
            AFTER UPDATE ON standard_answers
            BEGIN
                UPDATE standard_answers SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_test_answers_timestamp 
            AFTER UPDATE ON test_answers
            BEGIN
                UPDATE test_answers SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_user_speaker_orders_timestamp 
            AFTER UPDATE ON user_speaker_orders
            BEGIN
                UPDATE user_speaker_orders SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_user_audio_orders_timestamp 
            AFTER UPDATE ON user_audio_orders
            BEGIN
                UPDATE user_audio_orders SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        # 优化的触发器：当emotion_labels表插入新记录时，增量更新group_assignments表的annotated_count
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_annotated_count_on_insert
            AFTER INSERT ON emotion_labels
            FOR EACH ROW
            WHEN NEW.va_complete = 1 AND NEW.discrete_complete = 1
            BEGIN
                UPDATE group_assignments 
                SET annotated_count = COALESCE(annotated_count, 0) + 1
                WHERE username = NEW.username;
            END
        ''')
        
        # 优化的触发器：当emotion_labels表删除记录时，减量更新group_assignments表的annotated_count
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_annotated_count_on_delete
            AFTER DELETE ON emotion_labels
            FOR EACH ROW
            WHEN OLD.va_complete = 1 AND OLD.discrete_complete = 1
            BEGIN
                UPDATE group_assignments 
                SET annotated_count = MAX(0, COALESCE(annotated_count, 0) - 1)
                WHERE username = OLD.username;
            END
        ''')
        
        # 优化的触发器：当emotion_labels表更新记录时，根据完成状态变化调整annotated_count
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_annotated_count_on_update
            AFTER UPDATE ON emotion_labels
            FOR EACH ROW
            WHEN (OLD.va_complete != NEW.va_complete OR OLD.discrete_complete != NEW.discrete_complete)
            BEGIN
                UPDATE group_assignments 
                SET annotated_count = CASE
                    WHEN OLD.va_complete = 1 AND OLD.discrete_complete = 1 AND 
                         (NEW.va_complete != 1 OR NEW.discrete_complete != 1) THEN
                        MAX(0, COALESCE(annotated_count, 0) - 1)
                    WHEN (OLD.va_complete != 1 OR OLD.discrete_complete != 1) AND 
                         NEW.va_complete = 1 AND NEW.discrete_complete = 1 THEN
                        COALESCE(annotated_count, 0) + 1
                    ELSE annotated_count
                END
                WHERE username = NEW.username;
            END
        ''')
    
    # ==================== 情感标注相关方法 ====================
    
    def _execute_with_retry(self, operation, *args, **kwargs):
        """带重试机制的数据库操作执行器（优化版本）"""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < self.max_retries - 1:
                    # 数据库锁定，使用更短的等待时间
                    delay = self.retry_delay * (1.5 ** attempt) + random.uniform(0, 0.02)
                    time.sleep(delay)
                    continue
                else:
                    raise
            except Exception as e:
                # 对于非锁定错误，只重试一次
                if attempt == 0:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise
        
    def save_emotion_label(self, audio_file: str, speaker: str, 
                          v_value: Optional[float] = None, a_value: Optional[float] = None,
                          emotion_type: Optional[str] = None, discrete_emotion: Optional[str] = None,
                          patient_status: Optional[str] = None, audio_duration: float = 0,
                          play_count: int = 0) -> bool:
        """保存情感标注数据（优化版本）"""
        def _save_operation():
            with self.write_lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 使用更轻量的事务模式
                    conn.execute('BEGIN DEFERRED;')
                    
                    try:
                        # 判断完成状态（提前计算，避免重复逻辑）
                        va_complete = v_value is not None and a_value is not None
                        
                        # 简化的离散情感完成状态判断
                        discrete_complete = (
                            patient_status is not None and 
                            emotion_type is not None and 
                            (emotion_type == 'neutral' or 
                             (emotion_type == 'non-neutral' and discrete_emotion is not None))
                        ) and va_complete
                        
                        # 使用INSERT OR REPLACE简化逻辑，减少数据库查询
                        cursor.execute('''
                            INSERT OR REPLACE INTO emotion_labels (
                                audio_file, speaker, v_value, a_value, emotion_type,
                                discrete_emotion, patient_status, audio_duration, play_count,
                                va_complete, discrete_complete, timestamp, updated_at
                            ) VALUES (
                                ?, ?, ?, ?, ?, ?, ?, ?, 
                                COALESCE((SELECT play_count FROM emotion_labels 
                                         WHERE audio_file = ? AND speaker = ?), ?),
                                ?, ?, 
                                COALESCE((SELECT timestamp FROM emotion_labels 
                                         WHERE audio_file = ? AND speaker = ?), CURRENT_TIMESTAMP),
                                CURRENT_TIMESTAMP
                            )
                        ''', (
                            audio_file, speaker, v_value, a_value, emotion_type,
                            discrete_emotion, patient_status, audio_duration, 
                            audio_file, speaker, play_count,  # 保留原播放次数
                            int(va_complete), int(discrete_complete),
                            audio_file, speaker  # 保留原时间戳
                        ))
                        
                        conn.commit()
                        return True
                        
                    except Exception as e:
                        conn.rollback()
                        raise e
        
        try:
            return self._execute_with_retry(_save_operation)
        except Exception as e:
            print(f"保存情感标注数据失败: {e}")
            return False
    
    def get_emotion_labels(self, speaker: Optional[str] = None,
                          audio_file: Optional[str] = None) -> List[Dict]:
        """获取情感标注数据"""
        def _get_operation():
            with self.read_lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    sql = "SELECT * FROM emotion_labels WHERE 1=1"
                    params = []
                    
                    if speaker:
                        sql += " AND speaker = ?"
                        params.append(speaker)
                    if audio_file:
                        sql += " AND audio_file = ?"
                        params.append(audio_file)
                    
                    sql += " ORDER BY timestamp DESC"
                    
                    cursor.execute(sql, params)
                    return [dict(row) for row in cursor.fetchall()]
        
        try:
            return self._execute_with_retry(_get_operation)
        except Exception as e:
            print(f"获取情感标注数据失败: {e}")
            return []
    

    
    # ==================== 用户相关方法 ====================
    

    

    

    

    
    # ==================== 管理员相关方法 ====================
    

    

    

    
    # ==================== 通用方法 ====================
    
    def execute_query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """执行查询语句"""
        def _execute_query_operation():
            with self.read_lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute(sql, params)
                    return [dict(row) for row in cursor.fetchall()]
        
        try:
            return self._execute_with_retry(_execute_query_operation)
        except Exception as e:
            print(f"执行查询失败: {e}")
            return []
    
    def execute_update(self, sql: str, params: Tuple = ()) -> bool:
        """执行更新语句"""
        def _execute_update_operation():
            with self.write_lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    conn.execute('BEGIN IMMEDIATE;')
                    try:
                        cursor.execute(sql, params)
                        conn.commit()
                        return True
                    except Exception as e:
                        conn.rollback()
                        raise e
        
        try:
            return self._execute_with_retry(_execute_update_operation)
        except Exception as e:
            print(f"执行更新失败: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        def _backup_operation():
            with self.read_lock:
                # 确保所有写操作完成后再备份
                with self.get_connection() as conn:
                    # 执行VACUUM以优化数据库并确保数据完整性
                    conn.execute('VACUUM;')
                    conn.commit()
                
                # 使用文件系统级别的复制
                import shutil
                shutil.copy2(self.db_path, backup_path)
                return True
        
        try:
            return self._execute_with_retry(_backup_operation)
        except Exception as e:
            print(f"备份数据库失败: {e}")
            return False
    

    
    def get_database_info(self) -> Dict:
        """获取数据库信息"""
        def _get_db_info_operation():
            with self.read_lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 获取所有表名和记录数
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    table_info = {}
                    total_records = 0
                    
                    for table in tables:
                        if table == 'sqlite_sequence':
                            continue
                            
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_info[table] = count
                        total_records += count
                    
                    # 获取数据库文件大小
                    db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                    
                    return {
                        'database_path': self.db_path,
                        'database_size': db_size,
                        'total_tables': len(table_info),
                        'total_records': total_records,
                        'table_info': table_info
                    }
        
        try:
            return self._execute_with_retry(_get_db_info_operation)
        except Exception as e:
            print(f"获取数据库信息失败: {e}")
            return {}
    
    # ==================== 标注统计相关方法 ====================
    

    

    


# 全局实例将按需创建
unified_db_manager = None

def get_unified_db_manager():
    """获取统一数据库管理器实例（单例模式）"""
    global unified_db_manager
    if unified_db_manager is None:
        unified_db_manager = UnifiedDatabaseManager()
    return unified_db_manager