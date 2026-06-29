#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加va_scale字段
用于区分5点量表和9点量表的VA值标注
"""

import os
import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def add_va_scale_field():
    """为emotion_labels表添加va_scale字段"""
    db_path = os.path.join(Config.DATABASE_FOLDER, 'unified_emotion_system.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(emotion_labels)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'va_scale' in columns:
            print("va_scale字段已存在，无需添加")
            return True
        
        # 添加va_scale字段
        cursor.execute("""
            ALTER TABLE emotion_labels 
            ADD COLUMN va_scale TEXT DEFAULT '5_point'
        """)
        
        # 为现有数据设置默认值
        cursor.execute("""
            UPDATE emotion_labels 
            SET va_scale = '5_point' 
            WHERE va_scale IS NULL
        """)
        
        conn.commit()
        print("成功添加va_scale字段到emotion_labels表")
        
        # 验证字段添加成功
        cursor.execute("PRAGMA table_info(emotion_labels)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'va_scale' in columns:
            print("字段添加验证成功")
        else:
            print("字段添加验证失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"添加字段时发生错误: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("开始添加va_scale字段...")
    success = add_va_scale_field()
    if success:
        print("数据库迁移完成")
    else:
        print("数据库迁移失败")
        sys.exit(1)