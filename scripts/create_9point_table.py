#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建9分量表专用数据表
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import Config

def create_9point_emotion_labels_table():
    """创建9分量表专用的emotion_labels_9point表"""
    db_path = os.path.join(Config.DATABASE_FOLDER, 'unified_emotion_system.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='emotion_labels_9point'
        """)
        
        if cursor.fetchone():
            print("emotion_labels_9point表已存在")
            return True
        
        # 创建9分量表专用表
        cursor.execute('''
            CREATE TABLE emotion_labels_9point (
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
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_9point_audio_speaker_user 
            ON emotion_labels_9point(audio_file, speaker, username)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_9point_username 
            ON emotion_labels_9point(username)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_9point_speaker 
            ON emotion_labels_9point(speaker)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_9point_va_scale 
            ON emotion_labels_9point(va_scale)
        ''')
        
        # 创建触发器用于更新 updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_emotion_labels_9point_timestamp 
            AFTER UPDATE ON emotion_labels_9point
            BEGIN
                UPDATE emotion_labels_9point SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        conn.commit()
        print("emotion_labels_9point表创建成功")
        
        # 迁移现有的9分量表数据
        migrate_9point_data(cursor)
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"创建9分量表表时出错: {e}")
        return False
    finally:
        if conn:
            conn.close()

def migrate_9point_data(cursor):
    """迁移现有的9分量表数据到新表"""
    try:
        # 查询现有的9分量表数据
        cursor.execute("""
            SELECT * FROM emotion_labels WHERE va_scale = '9_point'
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("没有找到9分量表数据需要迁移")
            return
        
        # 获取列名
        cursor.execute("PRAGMA table_info(emotion_labels)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 插入数据到新表
        placeholders = ','.join(['?' for _ in columns])
        insert_sql = f"INSERT OR REPLACE INTO emotion_labels_9point ({','.join(columns)}) VALUES ({placeholders})"
        
        cursor.executemany(insert_sql, rows)
        
        # 从原表中删除9分量表数据
        cursor.execute("DELETE FROM emotion_labels WHERE va_scale = '9_point'")
        
        print(f"成功迁移 {len(rows)} 条9分量表数据")
        
    except Exception as e:
        print(f"迁移9分量表数据时出错: {e}")
        raise

if __name__ == "__main__":
    create_9point_emotion_labels_table()