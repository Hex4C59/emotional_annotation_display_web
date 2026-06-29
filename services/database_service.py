#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务
用于处理情感标注数据的数据库操作
"""

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    print("警告: SQLite3 模块不可用，数据库功能将被禁用")
    print("请检查Python环境是否正确安装了SQLite3支持")

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from models.emotion_model import EmotionLabel
from utils.audio_utils import get_audio_duration
from utils.logger import emotion_logger
from config import Config
from scripts.unified_db_manager import get_unified_db_manager

class DatabaseService:
    """数据库服务类"""
    
    def __init__(self):
        """初始化数据库服务"""
        self.db_manager = get_unified_db_manager()
    
    @staticmethod
    def get_db_path():
        """获取数据库文件路径（保持兼容性）"""
        return os.path.join(Config.DATABASE_FOLDER, 'unified_emotion_system.db')
    
    def get_connection(self):
        """获取数据库连接"""
        if not SQLITE_AVAILABLE:
            raise Exception("SQLite3 模块不可用")
        
        return self.db_manager.get_connection()
    
    def get_users_connection(self):
        """获取用户数据库连接"""
        if not SQLITE_AVAILABLE:
            raise Exception("SQLite3 模块不可用")
        
        return self.db_manager.get_users_connection()
    
    def get_unified_connection(self):
        """获取统一数据库连接（与get_connection相同）"""
        if not SQLITE_AVAILABLE:
            raise Exception("SQLite3 模块不可用")
        
        return self.db_manager.get_connection()
    
    def save_emotion_label(self, audio_file: str, speaker: str, username: str,
                          v_value=None, a_value=None, emotion_type=None,
                          discrete_emotion=None, patient_status=None,
                          va_complete=False, discrete_complete=False) -> bool:
        """
        保存情感标注数据
        
        Args:
            audio_file: 音频文件名
            speaker: 说话人
            username: 用户名
            v_value: V值
            a_value: A值
            emotion_type: 情感类型
            discrete_emotion: 离散情感
            patient_status: 患者状态
            va_complete: VA标注是否完成
            discrete_complete: 离散情感标注是否完成
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        return self.db_manager.save_emotion_label(
            audio_file, speaker, username, v_value, a_value,
            emotion_type, discrete_emotion, patient_status,
            va_complete, discrete_complete
        )
    
    @staticmethod
    def _ensure_tables_exist(conn):
        """确保数据库表存在，如果不存在则创建"""
        cursor = conn.cursor()
        
        # 检查emotion_labels表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='emotion_labels'
        """)
        
        if not cursor.fetchone():
            # 创建表
            cursor.execute('''
                CREATE TABLE emotion_labels (
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
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(audio_file, speaker, username)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audio_speaker_user 
                ON emotion_labels(audio_file, speaker, username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_username 
                ON emotion_labels(username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_speaker 
                ON emotion_labels(speaker)
            ''')
            
            # 创建触发器用于更新 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_emotion_labels_timestamp 
                AFTER UPDATE ON emotion_labels
                BEGIN
                    UPDATE emotion_labels SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            print("emotion_labels表创建成功")
        
        # 检查standard_answers表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='standard_answers'
        """)
        
        if not cursor.fetchone():
            # 创建标准答案表
            cursor.execute('''
                CREATE TABLE standard_answers (
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
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_standard_audio_file 
                ON standard_answers(audio_file)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_standard_emotion_type 
                ON standard_answers(emotion_type)
            ''')
            
            # 创建触发器用于更新 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_standard_answers_timestamp 
                AFTER UPDATE ON standard_answers
                BEGIN
                    UPDATE standard_answers SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            print("standard_answers表创建成功")
        
        # 检查test_answers表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='test_answers'
        """)
        
        if not cursor.fetchone():
            # 创建测试答案表
            cursor.execute('''
                CREATE TABLE test_answers (
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
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_test_audio_file 
                ON test_answers(audio_file)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_test_emotion_type 
                ON test_answers(emotion_type)
            ''')
            
            # 创建触发器用于更新 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_test_answers_timestamp 
                AFTER UPDATE ON test_answers
                BEGIN
                    UPDATE test_answers SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            print("test_answers表创建成功")
        
        # 检查second_consistency_test_results表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='second_consistency_test_results'
        """)
        
        if not cursor.fetchone():
            # 创建第二次一致性测试结果表
            cursor.execute('''
                CREATE TABLE second_consistency_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    audio_file TEXT NOT NULL,
                    v_value REAL,
                    a_value REAL,
                    emotion_type TEXT,
                    discrete_emotion TEXT,
                    patient_status TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, audio_file)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_second_consistency_username 
                ON second_consistency_test_results(username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_second_consistency_audio_file 
                ON second_consistency_test_results(audio_file)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_second_consistency_username_audio 
                ON second_consistency_test_results(username, audio_file)
            ''')
            
            # 创建触发器用于更新 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_second_consistency_test_results_timestamp 
                AFTER UPDATE ON second_consistency_test_results
                BEGIN
                    UPDATE second_consistency_test_results SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            print("second_consistency_test_results表创建成功")
        
        # 检查second_consistency_standard_answers表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='second_consistency_standard_answers'
        """)
        
        if not cursor.fetchone():
            # 创建第二次一致性测试标准答案表
            cursor.execute('''
                CREATE TABLE second_consistency_standard_answers (
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
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_second_consistency_audio_file 
                ON second_consistency_standard_answers(audio_file)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_second_consistency_emotion_type 
                ON second_consistency_standard_answers(emotion_type)
            ''')
            
            # 创建触发器用于更新 updated_at
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_second_consistency_standard_answers_timestamp 
                AFTER UPDATE ON second_consistency_standard_answers
                BEGIN
                    UPDATE second_consistency_standard_answers SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            print("standard_answers表创建成功")
    
    @staticmethod
    def save_label(label_data, speaker, audio_file_path):
        """
        保存标注数据到数据库（优化版本）
        
        Args:
            label_data: 标注数据字典
            speaker: 说话人
            audio_file_path: 音频文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 创建DatabaseService实例来获取连接
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 根据va_scale决定使用哪个表
                va_scale = label_data.get("va_scale", "5_point")
                table_name = "emotion_labels_9point" if va_scale == "9_point" else "emotion_labels"
                
                # 优化：使用更高效的查询，只获取必要的字段
                cursor.execute(f'''
                    SELECT audio_duration, play_count FROM {table_name} 
                    WHERE audio_file = ? AND speaker = ? AND username = ?
                ''', (label_data.get("audio_file"), speaker, label_data.get("username")))
                
                existing_record = cursor.fetchone()
                
                # 优化：减少音频时长计算，优先使用缓存值
                if existing_record and existing_record['audio_duration'] and existing_record['audio_duration'] > 0:
                    audio_duration = existing_record['audio_duration']
                    play_count = existing_record['play_count'] or 0
                else:
                    # 只在首次保存时计算音频时长
                    try:
                        from utils.audio_utils import get_audio_duration
                        audio_duration = get_audio_duration(audio_file_path)
                    except Exception as e:
                        # 如果计算失败，使用默认值，不阻塞保存流程
                        print(f"音频时长计算失败，使用默认值: {e}")
                        audio_duration = 0
                    play_count = existing_record['play_count'] if existing_record else 0
            
                # 创建标注对象
                label = EmotionLabel(
                    audio_file=label_data.get("audio_file"),
                    v_value=label_data.get("v_value"),
                    a_value=label_data.get("a_value"),
                    emotion_type=label_data.get("emotion_type"),
                    discrete_emotion=label_data.get("discrete_emotion"),
                    username=label_data.get("username"),
                    patient_status=label_data.get("patient_status"),
                    audio_duration=audio_duration
                )
                
                # 插入或更新数据，使用完整的speaker保持与get_label方法一致
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} (
                        audio_file, speaker, username, v_value, a_value,
                        emotion_type, discrete_emotion, patient_status,
                        audio_duration, play_count, va_complete, discrete_complete, va_scale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    label.audio_file,
                    speaker,           # 使用完整的speaker
                    label.username,
                    label.v_value,
                    label.a_value,
                    label.emotion_type,
                    label.discrete_emotion,
                    label.patient_status,
                    label.audio_duration,
                    play_count,        # 使用已获取的播放次数
                    int(label.va_complete),    # 转换布尔值为整数
                    int(label.discrete_complete),  # 转换布尔值为整数
                    va_scale  # 使用实际的va_scale值
                ))
                
                emotion_logger.log_database_operation(
                    operation="INSERT OR REPLACE",
                    table=table_name,
                    username=label.username,
                    details={
                        "audio_file": label.audio_file,
                        "speaker": speaker,
                        "v_value": label.v_value,
                        "a_value": label.a_value,
                        "emotion_type": label.emotion_type,
                        "discrete_emotion": label.discrete_emotion,
                        "va_scale": va_scale
                    },
                    success=True
                )
                
                # 移除自动分组进度更新以提升性能
                # 分组进度可通过定时任务或手动触发更新
                
                conn.commit()
                return True
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="INSERT OR REPLACE",
                table="emotion_labels",
                username=label_data.get("username", "unknown"),
                details={"audio_file": label_data.get("audio_file"), "error": str(e)},
                success=False
            )
            print(f"保存标注数据时出错: {e}")
            return False
    
    def get_label(self, username, speaker, filename, va_scale="5_point"):
        """
        获取标注数据
        
        Args:
            username: 用户名
            speaker: 说话人
            filename: 文件名
            va_scale: VA量表类型，"5_point"或"9_point"
            
        Returns:
            dict: 标注数据字典，如果不存在则返回None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 根据va_scale决定使用哪个表
                table_name = "emotion_labels_9point" if va_scale == "9_point" else "emotion_labels"
                
                # 处理分组说话人逻辑
                import re
                
                # 首先尝试精确匹配传入的speaker
                cursor.execute(f'''
                    SELECT * FROM {table_name} 
                    WHERE username = ? AND speaker = ? AND audio_file = ?
                ''', (username, speaker, filename))
                
                row = cursor.fetchone()
                
                # 如果精确匹配没有找到，且speaker不包含分组后缀，则尝试模糊匹配
                if not row and not re.match(r'spk\d+-.+-.+$', speaker):
                    # 查询所有以speaker开头的记录
                    cursor.execute(f'''
                        SELECT * FROM {table_name} 
                        WHERE username = ? AND speaker LIKE ? AND audio_file = ?
                        ORDER BY speaker LIMIT 1
                    ''', (username, f"{speaker}-%", filename))
                    row = cursor.fetchone()
                
                if row:
                    # 将数据库行转换为字典
                    label_dict = dict(row)
                    
                    # 计算标注完整性
                    from models.emotion_model import calculate_annotation_completeness
                    completeness = calculate_annotation_completeness(label_dict)
                    label_dict['annotation_completeness'] = completeness
                    
                    emotion_logger.log_database_operation(
                        operation="SELECT",
                        table=table_name,
                        username=username,
                        details={"audio_file": filename, "speaker": speaker, "found": True, "actual_speaker": label_dict.get('speaker'), "va_scale": va_scale},
                        success=True
                    )
                    
                    return label_dict
                
                emotion_logger.log_database_operation(
                    operation="SELECT",
                    table=table_name,
                    username=username,
                    details={"audio_file": filename, "speaker": speaker, "found": False, "va_scale": va_scale},
                    success=True
                )
                
                return None
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="SELECT",
                table=f"{table_name} (va_scale: {va_scale})",
                username=username,
                details={"audio_file": filename, "speaker": speaker, "error": str(e), "va_scale": va_scale},
                success=False
            )
            print(f"获取标注数据时出错: {e}")
            return None
    
    def get_labeled_files(self, username, speaker, va_scale="5_point"):
        """
        获取已标注的文件列表
        
        Args:
            username: 用户名
            speaker: 说话人
            va_scale: VA量表类型，"5_point"或"9_point"
            
        Returns:
            tuple: (已标注文件集合, 标注完整性字典)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 根据va_scale决定使用哪个表
                table_name = "emotion_labels_9point" if va_scale == "9_point" else "emotion_labels"
                
                # 处理分组说话人逻辑
                import re
                
                # 对于分组说话人（如spk189），需要查询所有相关记录
                # 包括精确匹配（spk189）和模糊匹配（spk189-x-x）
                if re.match(r'spk\d+$', speaker):
                    # 分组说话人：查询精确匹配和模糊匹配的所有记录
                    cursor.execute(f'''
                        SELECT audio_file, v_value, a_value, emotion_type, 
                               discrete_emotion, patient_status, va_complete, discrete_complete
                        FROM {table_name} 
                        WHERE username = ? AND (speaker = ? OR speaker LIKE ?)
                    ''', (username, speaker, f"{speaker}-%"))
                else:
                    # 非分组说话人：只进行精确匹配
                    cursor.execute(f'''
                        SELECT audio_file, v_value, a_value, emotion_type, 
                               discrete_emotion, patient_status, va_complete, discrete_complete
                        FROM {table_name} 
                        WHERE username = ? AND speaker = ?
                    ''', (username, speaker))
                
                rows = cursor.fetchall()
                
                labeled_files = set()
                annotation_completeness = {}
                
                for row in rows:
                    filename = row['audio_file']
                    labeled_files.add(filename)
                    
                    # 计算标注完整性
                    label_dict = dict(row)
                    from models.emotion_model import calculate_annotation_completeness
                    completeness = calculate_annotation_completeness(label_dict)
                    annotation_completeness[filename] = completeness
                
                return labeled_files, annotation_completeness
            
        except Exception as e:
            print(f"获取已标注文件列表时出错: {e}")
            return set(), {}
    
    def update_play_count(self, username, speaker, filename, va_scale="5_point"):
        """
        更新音频播放次数（优化版本）
        
        Args:
            username: 用户名
            speaker: 说话人
            filename: 文件名
            va_scale: VA量表类型，"5_point"或"9_point"
            
        Returns:
            int: 更新后的播放次数
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 根据va_scale决定使用哪个表
                table_name = "emotion_labels_9point" if va_scale == "9_point" else "emotion_labels"
                
                # 优化方案：先检查记录是否存在
                # 使用完整的speaker，与save_label和get_label方法保持一致
                cursor.execute(f'''
                    SELECT id, play_count FROM {table_name} 
                    WHERE audio_file = ? AND speaker = ? AND username = ?
                ''', (filename, speaker, username))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # 记录存在，直接更新播放次数
                    new_play_count = existing_record['play_count'] + 1
                    cursor.execute(f'''
                        UPDATE {table_name} 
                        SET play_count = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (new_play_count, existing_record['id']))
                    
                    conn.commit()
                    return new_play_count
                else:
                    # 记录不存在，使用INSERT OR REPLACE避免唯一约束冲突
                    cursor.execute(f'''
                        INSERT OR REPLACE INTO {table_name} (
                            audio_file, speaker, username, 
                            v_value, a_value, emotion_type, discrete_emotion, patient_status,
                            audio_duration, play_count, va_complete, discrete_complete, va_scale,
                            timestamp, updated_at
                        ) VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL, 0, 1, 0, 0, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (filename, speaker, username, va_scale))
                    
                    conn.commit()
                    return 1
            
        except Exception as e:
            print(f"更新播放次数时出错: {e}")
            return 0
    
    def get_play_count(self, username, speaker, filename, va_scale="5_point"):
        """
        获取音频播放次数
        
        Args:
            username: 用户名
            speaker: 说话人
            filename: 文件名
            va_scale: VA量表类型，"5_point"或"9_point"
            
        Returns:
            int: 播放次数
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 根据va_scale决定使用哪个表
                table_name = "emotion_labels_9point" if va_scale == "9_point" else "emotion_labels"
                
                # 查询播放次数
                # 使用完整的speaker，与其他方法保持一致
                cursor.execute(f'''
                    SELECT play_count FROM {table_name} 
                    WHERE username = ? AND speaker = ? AND audio_file = ?
                ''', (username, speaker, filename))
                
                row = cursor.fetchone()
                
                return row['play_count'] if row else 0
            
        except Exception as e:
            print(f"获取播放次数时出错: {e}")
            return 0
    
    @staticmethod
    def _update_group_progress(cursor, username, speaker):
        """
        自动更新用户的分组进度（简化版本：不执行任何操作）
        
        Args:
            cursor: 数据库游标
            username: 用户名
            speaker: 说话人
        """
        # 简化版本：不使用数据库表
        pass
    
    @staticmethod
    def get_user_statistics(username):
        """
        获取用户标注统计信息
        
        Args:
            username: 用户名
            
        Returns:
            dict: 统计信息
        """
        try:
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 总标注数量
                cursor.execute('''
                    SELECT COUNT(*) as total_count FROM emotion_labels 
                    WHERE username = ?
                ''', (username,))
                total_count = cursor.fetchone()['total_count']
                
                # VA完整标注数量
                cursor.execute('''
                    SELECT COUNT(*) as va_complete_count FROM emotion_labels 
                    WHERE username = ? AND va_complete = 1
                ''', (username,))
                va_complete_count = cursor.fetchone()['va_complete_count']
                
                # 离散情感完整标注数量
                cursor.execute('''
                    SELECT COUNT(*) as discrete_complete_count FROM emotion_labels 
                    WHERE username = ? AND discrete_complete = 1
                ''', (username,))
                discrete_complete_count = cursor.fetchone()['discrete_complete_count']
                
                # 按说话人统计
                cursor.execute('''
                    SELECT speaker, COUNT(*) as count FROM emotion_labels 
                    WHERE username = ? 
                    GROUP BY speaker
                    ORDER BY count DESC
                ''', (username,))
                speaker_stats = cursor.fetchall()
              
                return {
                        'total_count': total_count,
                        'va_complete_count': va_complete_count,
                        'discrete_complete_count': discrete_complete_count,
                        'speaker_stats': [dict(row) for row in speaker_stats]
                    }
            
        except Exception as e:
            print(f"获取用户统计信息时出错: {e}")
            return {
                'total_count': 0,
                'va_complete_count': 0,
                'discrete_complete_count': 0,
                'speaker_stats': []
            }
     

    
    @staticmethod
    def import_second_consistency_standard_answers():
        """
        从文件夹导入第二次一致性测试的标准答案到数据库
        """
        try:
            import glob
            
            data_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/second_consistency_test'
            
            if not os.path.exists(data_dir):
                print(f"数据目录不存在: {data_dir}")
                return False
            
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取所有JSON文件
                json_files = glob.glob(os.path.join(data_dir, '*.json'))
                
                imported_count = 0
                skipped_count = 0
                
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        audio_file = data.get('audio_file')
                        if not audio_file:
                            print(f"跳过文件 {json_file}: 缺少audio_file字段")
                            skipped_count += 1
                            continue
                        
                        # 检查是否已存在
                        cursor.execute('''
                            SELECT id FROM second_consistency_standard_answers 
                            WHERE audio_file = ?
                        ''', (audio_file,))
                        
                        if cursor.fetchone():
                            print(f"跳过已存在的文件: {audio_file}")
                            skipped_count += 1
                            continue
                        
                        # 插入标准答案
                        cursor.execute('''
                            INSERT INTO second_consistency_standard_answers (
                                audio_file, v_value, a_value, emotion_type, 
                                discrete_emotion, patient_status, audio_duration, username
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            audio_file,
                            data.get('v_value'),
                            data.get('a_value'),
                            data.get('emotion_type'),
                            data.get('discrete_emotion'),
                            data.get('patient_status'),
                            data.get('audio_duration'),
                            data.get('username')
                        ))
                        
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"处理文件 {json_file} 时出错: {e}")
                        skipped_count += 1
                        continue
                
                conn.commit()
                
                print(f"第二次一致性测试标准答案导入完成: 导入 {imported_count} 条，跳过 {skipped_count} 条")
                return True
            
        except Exception as e:
            print(f"导入第二次一致性测试标准答案时出错: {e}")
            return False
    
    @staticmethod
    def save_second_consistency_test_results(username, results):
        """
        保存第二次一致性测试结果到专用表
        
        Args:
            username: 用户名
            results: 测试结果列表
            
        Returns:
            bool: 保存是否成功
        """
        try:
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 保存每个结果到专用表
                for result in results:
                    cursor.execute('''
                        INSERT OR REPLACE INTO second_consistency_test_results (
                            username, audio_file, v_value, a_value, emotion_type, 
                            discrete_emotion, patient_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        username,
                        result.get('filename'),
                        result.get('v_value'),
                        result.get('a_value'),
                        result.get('emotion_type'),
                        result.get('discrete_emotion'),
                        result.get('patient_status')
                    ))
                
                conn.commit()
            
            # 更新用户的第二次一致性测试完成状态
            from services.group_assignment_service import GroupAssignmentManager
            group_manager = GroupAssignmentManager()
            group_manager.update_second_consistency_completed(username, True)
            
            emotion_logger.log_database_operation(
                operation="INSERT OR REPLACE",
                table="second_consistency_test_results",
                username=username,
                details={"results_count": len(results)},
                success=True
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="INSERT OR REPLACE",
                table="second_consistency_test_results",
                username=username,
                details={"error": str(e)},
                success=False
            )
            print(f"保存第二次一致性测试结果时出错: {e}")
            return False
    
    @staticmethod
    def get_second_consistency_test_results(username):
        """
        获取用户的第二次一致性测试结果
        
        Args:
            username: 用户名
            
        Returns:
            list: 测试结果列表
        """
        try:
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT audio_file, v_value, a_value, emotion_type, 
                           discrete_emotion, patient_status, timestamp
                    FROM second_consistency_test_results 
                    WHERE username = ?
                    ORDER BY timestamp DESC
                ''', (username,))
                
                results = [dict(row) for row in cursor.fetchall()]
                
                return results
            
        except Exception as e:
            print(f"获取第二次一致性测试结果时出错: {e}")
            return []
    
    @staticmethod
    def has_completed_second_consistency_test(username):
        """
        检查用户是否已完成第二次一致性测试
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否已完成
        """
        try:
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) as count
                    FROM second_consistency_test_results 
                    WHERE username = ?
                ''', (username,))
                
                result = cursor.fetchone()
                
                return result['count'] > 0
            
        except Exception as e:
            print(f"检查第二次一致性测试完成状态时出错: {e}")
            return False
    
    @staticmethod
    def calculate_second_consistency_score(username):
        """
        计算用户第二次一致性测试的得分
        使用与第一次一致性测试相同的算法
        
        Args:
            username: 用户名
            
        Returns:
            dict: 包含一致性得分的详细信息
        """
        try:
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取用户的第二次一致性测试结果
                cursor.execute('''
                    SELECT audio_file, v_value, a_value, emotion_type, 
                           discrete_emotion, patient_status
                    FROM second_consistency_test_results 
                    WHERE username = ?
                ''', (username,))
                
                user_results_raw = cursor.fetchall()
                
                # 获取标准答案
                cursor.execute('''
                    SELECT audio_file, v_value, a_value, emotion_type, 
                           discrete_emotion, patient_status
                    FROM second_consistency_standard_answers
                ''')
                
                standard_answers_raw = cursor.fetchall()
            
            if not user_results_raw:
                return None
            
            # 将用户结果转换为字典列表格式，与第一次一致性测试保持一致
            user_results_list = []
            for result in user_results_raw:
                user_results_list.append({
                    'audio_file': result[0],
                    'v_value': result[1],
                    'a_value': result[2],
                    'emotion_type': result[3],
                    'discrete_emotion': result[4],
                    'patient_status': result[5]
                })
            
            # 将标准答案转换为字典格式
            standard_answers = {}
            for standard in standard_answers_raw:
                standard_answers[standard[0]] = {
                    'audio_file': standard[0],
                    'v_value': standard[1],
                    'a_value': standard[2],
                    'emotion_type': standard[3],
                    'discrete_emotion': standard[4],
                    'patient_status': standard[5]
                }
            
            # 使用与第一次一致性测试相同的算法
            total_samples = len(user_results_list)
            if total_samples == 0:
                return {
                    'total_samples': 0,
                    'matched_samples': 0,
                    'v_consistency': 0,
                    'a_consistency': 0,
                    'discrete_consistency': 0,
                    'overall_consistency': 0,
                    'detailed_results': []
                }
            
            matched_samples = 0
            total_v_score = 0
            total_a_score = 0
            total_discrete_score = 0
            detailed_results = []
            
            for result in user_results_list:
                audio_file = result.get('audio_file')
                if not audio_file:
                    continue
                
                standard = standard_answers.get(audio_file)
                if not standard:
                    continue
                
                matched_samples += 1
                
                # 计算V值一致性
                user_v = result.get('v_value', 0)
                user_a = result.get('a_value', 0)
                standard_v = standard.get('v_value', 0)
                standard_a = standard.get('a_value', 0)
                
                if user_v is not None and user_a is not None and standard_v is not None and standard_a is not None:
                    # V值计算：完全相同=100%，差0.5=50%，其他=0%
                    v_diff = abs(user_v - standard_v)
                    if v_diff == 0:
                        v_score = 1.0  # 100%正确率
                    elif v_diff == 0.5:
                        v_score = 0.5  # 50%正确率
                    else:
                        v_score = 0.0  # 0%正确率
                    
                    # A值计算：完全相同=100%，差0.5=50%，其他=0%
                    a_diff = abs(user_a - standard_a)
                    if a_diff == 0:
                        a_score = 1.0  # 100%正确率
                    elif a_diff == 0.5:
                        a_score = 0.5  # 50%正确率
                    else:
                        a_score = 0.0  # 0%正确率
                    
                    total_v_score += v_score
                    total_a_score += a_score
                else:
                    v_score = 0
                    a_score = 0
                
                # 计算离散情感一致性
                user_discrete = result.get('discrete_emotion')
                standard_discrete = standard.get('discrete_emotion')
                standard_emotion_type = standard.get('emotion_type')
                
                # 处理标准答案中neutral类型的特殊情况
                # 如果标准答案的emotion_type是neutral但discrete_emotion是NULL，
                # 则将其视为neutral进行比较
                if (standard_emotion_type == 'neutral' and 
                    (standard_discrete is None or standard_discrete == '')):
                    standard_discrete = 'neutral'
                
                discrete_score = 1 if user_discrete == standard_discrete else 0
                total_discrete_score += discrete_score
                
                detailed_results.append({
                    'audio_file': audio_file,
                    'user_v': user_v,
                    'user_a': user_a,
                    'standard_v': standard_v,
                    'standard_a': standard_a,
                    'user_discrete': user_discrete,
                    'standard_discrete': standard_discrete,  # 这里已经是修正后的值
                    'standard_emotion_type': standard_emotion_type,  # 添加emotion_type用于调试
                    'v_score': v_score,
                    'a_score': a_score,
                    'discrete_score': discrete_score,
                    'v_consistent': v_score == 1.0,  # 添加布尔值字段
                    'a_consistent': a_score == 1.0,  # 添加布尔值字段
                    'discrete_consistent': discrete_score == 1  # 添加布尔值字段
                })
            
            if matched_samples == 0:
                return {
                    'total_samples': total_samples,
                    'matched_samples': 0,
                    'v_consistency': 0,
                    'a_consistency': 0,
                    'discrete_consistency': 0,
                    'overall_consistency': 0,
                    'detailed_results': []
                }
            
            # 计算平均一致性
            v_consistency = total_v_score / matched_samples
            a_consistency = total_a_score / matched_samples
            discrete_consistency = total_discrete_score / matched_samples
            overall_consistency = (v_consistency + a_consistency + discrete_consistency) / 3
            
            return {
                'total_samples': total_samples,
                'matched_samples': matched_samples,
                'v_consistency': round(v_consistency, 4),
                'a_consistency': round(a_consistency, 4),
                'discrete_consistency': round(discrete_consistency, 4),
                'overall_consistency': round(overall_consistency, 4),
                'detailed_results': detailed_results
            }
            
        except Exception as e:
            print(f"计算第二次一致性测试得分时出错: {e}")
            return None
    
    @staticmethod
    def check_second_consistency_test_needed(username):
        """
        检查用户是否需要进行第二次一致性测试
        基于group_assignments表中的annotated_count字段
        
        Args:
            username: 用户名
            
        Returns:
            dict: 包含是否需要测试和相关信息的字典
        """
        try:
            # 从配置文件读取阈值
            from config import Config
            threshold = Config.SECOND_CONSISTENCY_TEST_THRESHOLD
            
            # 获取用户的分组分配信息，包含annotated_count
            from services.group_assignment_service import GroupAssignmentManager
            group_manager = GroupAssignmentManager()
            assignment = group_manager.get_user_assignment_info(username)
            
            if not assignment:
                return {
                    'annotated_count': 0,
                    'needs_second_test': False,
                    'second_test_completed': False
                }
            
            annotated_count = assignment.get('annotated_count', 0)
            
            # 检查用户是否已经完成过第二次一致性测试
            # 从group_assignments表中获取second_consistency_completed字段
            second_test_completed = assignment.get('second_consistency_completed', False)
            
            return {
                'annotated_count': annotated_count,
                'needs_second_test': annotated_count >= threshold and not second_test_completed,
                'second_test_completed': second_test_completed
            }
            
        except Exception as e:
            print(f"检查第二次一致性测试需求时出错: {e}")
            return {
                'annotated_count': 0,
                'needs_second_test': False,
                'second_test_completed': False
            }
    
    @staticmethod
    def ensure_test_answers_table_exists():
        """
        确保test_answers表存在
        """
        db_service = DatabaseService()
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查test_answers表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='test_answers'
            """)
            
            if not cursor.fetchone():
                # 创建测试答案表
                cursor.execute('''
                    CREATE TABLE test_answers (
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
                
                # 创建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_test_audio_file 
                    ON test_answers(audio_file)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_test_emotion_type 
                    ON test_answers(emotion_type)
                ''')
                
                # 创建触发器用于更新 updated_at
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_test_answers_timestamp 
                    AFTER UPDATE ON test_answers
                    BEGIN
                        UPDATE test_answers SET updated_at = CURRENT_TIMESTAMP 
                        WHERE id = NEW.id;
                    END
                ''')
                
                conn.commit()
                print("test_answers表创建成功")
    
    @staticmethod
    def insert_test_answer(audio_file, v_value=None, a_value=None, emotion_type=None, 
                          discrete_emotion=None, patient_status=None, audio_duration=None, 
                          created_by='测试答案导入', timestamp=None):
        """
        插入测试答案
        
        Args:
            audio_file: 音频文件名
            v_value: V值
            a_value: A值
            emotion_type: 情感类型
            discrete_emotion: 离散情感
            patient_status: 患者状态
            audio_duration: 音频时长
            created_by: 创建者
            timestamp: 时间戳
        """
        db_service = DatabaseService()
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            if timestamp is None:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT OR REPLACE INTO test_answers 
                (audio_file, v_value, a_value, emotion_type, discrete_emotion, 
                 patient_status, audio_duration, created_by, timestamp, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audio_file, v_value, a_value, emotion_type, discrete_emotion,
                patient_status, audio_duration, created_by, timestamp, timestamp
            ))
            
            conn.commit()
    
    @staticmethod
    def get_test_answer_by_audio_file(audio_file):
        """
        根据音频文件名获取测试答案
        
        Args:
            audio_file: 音频文件名
            
        Returns:
            dict: 测试答案数据，如果不存在返回None
        """
        db_service = DatabaseService()
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, audio_file, v_value, a_value, emotion_type, discrete_emotion, 
                       patient_status, audio_duration, created_by, timestamp, updated_at
                FROM test_answers 
                WHERE audio_file = ?
            """, (audio_file,))
            
            result = cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'audio_file': result[1],
                'v_value': result[2],
                'a_value': result[3],
                'emotion_type': result[4],
                'discrete_emotion': result[5],
                'patient_status': result[6],
                'audio_duration': result[7],
                'created_by': result[8],
                'timestamp': result[9],
                'updated_at': result[10]
            }
        return None
    
    @staticmethod
    def get_all_test_answers():
        """
        获取所有测试答案
        
        Returns:
            list: 测试答案列表
        """
        db_service = DatabaseService()
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, audio_file, v_value, a_value, emotion_type, discrete_emotion, 
                       patient_status, audio_duration, created_by, timestamp, updated_at
                FROM test_answers 
                ORDER BY emotion_type, audio_file
            """)
            
            results = cursor.fetchall()
        
        answers = []
        for result in results:
            answers.append({
                'id': result[0],
                'audio_file': result[1],
                'v_value': result[2],
                'a_value': result[3],
                'emotion_type': result[4],
                'discrete_emotion': result[5],
                'patient_status': result[6],
                'audio_duration': result[7],
                'created_by': result[8],
                'timestamp': result[9],
                'updated_at': result[10]
            })
        
        return answers
    
    def get_standard_answer(self, audio_file):
        """
        获取指定音频文件的标准答案
        
        Args:
            audio_file (str): 音频文件名
            
        Returns:
            dict: 标准答案数据，如果不存在返回None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT audio_file, v_value, a_value, emotion_type, 
                           discrete_emotion, patient_status, audio_duration,
                           created_by, timestamp, updated_at
                    FROM standard_answers 
                    WHERE audio_file = ?
                ''', (audio_file,))
                
                result = cursor.fetchone()
            
            if result:
                return {
                    'audio_file': result[0],
                    'v_value': result[1],
                    'a_value': result[2],
                    'emotion_type': result[3],
                    'discrete_emotion': result[4],
                    'patient_status': result[5],
                    'audio_duration': result[6],
                    'created_by': result[7],
                    'timestamp': result[8],
                    'updated_at': result[9]
                }
            else:
                return None
                
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="SELECT",
                table="standard_answers",
                username="system",
                details={"audio_file": audio_file, "error": str(e)},
                success=False
            )
            print(f"获取标准答案时出错: {e}")
            return None
    
    @staticmethod
    def clear_table(table_name, condition=None):
        """
        清空指定表的数据
        
        Args:
            table_name: 表名
            condition: 删除条件，如果为None则删除所有数据
        """
        db_service = DatabaseService()
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            if condition:
                cursor.execute(f"DELETE FROM {table_name} WHERE {condition}")
            else:
                cursor.execute(f"DELETE FROM {table_name}")
            conn.commit()