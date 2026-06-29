#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为用户表添加量表顺序字段
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def add_scale_order_field():
    """
    为用户表添加量表顺序字段
    """
    database_folder = Config.DATABASE_FOLDER
    db_path = os.path.join(database_folder, 'unified_emotion_system.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'scale_order' not in columns:
            print("添加 scale_order 字段到 users 表...")
            # 添加量表顺序字段，默认值为 '5_point_first'（先5分量表后9分量表）
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN scale_order TEXT DEFAULT '5_point_first'
            ''')
            
            print("scale_order 字段添加成功")
        else:
            print("scale_order 字段已存在")
        
        conn.commit()
        conn.close()
        
        print("用户表量表顺序字段添加完成")
        return True
        
    except Exception as e:
        print(f"添加量表顺序字段时出错: {e}")
        return False

if __name__ == '__main__':
    add_scale_order_field()