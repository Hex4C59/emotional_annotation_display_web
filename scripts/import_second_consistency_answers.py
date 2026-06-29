#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入第二次一致性测试标准答案的脚本
"""

import os
import sys
import json
import glob
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_second_consistency_standard_answers_table(cursor):
    """创建第二次一致性测试标准答案表"""
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
    print("已创建 second_consistency_standard_answers 表")

def import_second_consistency_standard_answers():
    """
    从文件夹导入第二次一致性测试的标准答案到数据库
    """
    try:
        # 数据目录
        data_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/second_consistency_test'
        
        if not os.path.exists(data_dir):
            print(f"数据目录不存在: {data_dir}")
            return False
        
        # 连接数据库
        db_path = os.path.join(project_root, 'data', 'emotion_labels.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 创建表
        create_second_consistency_standard_answers_table(cursor)
        
        # 获取所有JSON文件
        json_files = glob.glob(os.path.join(data_dir, '*.json'))
        
        imported_count = 0
        skipped_count = 0
        
        print(f"找到 {len(json_files)} 个JSON文件")
        
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
                print(f"导入: {audio_file}")
                
            except Exception as e:
                print(f"处理文件 {json_file} 时出错: {e}")
                skipped_count += 1
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n第二次一致性测试标准答案导入完成:")
        print(f"- 导入: {imported_count} 条")
        print(f"- 跳过: {skipped_count} 条")
        print(f"- 总计: {len(json_files)} 个文件")
        return True
        
    except Exception as e:
        print(f"导入第二次一致性测试标准答案时出错: {e}")
        return False

def verify_import():
    """验证导入结果"""
    try:
        db_path = os.path.join(project_root, 'data', 'emotion_labels.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='second_consistency_standard_answers'
        ''')
        
        if not cursor.fetchone():
            print("错误: second_consistency_standard_answers 表不存在")
            return False
        
        # 统计记录数
        cursor.execute('SELECT COUNT(*) as count FROM second_consistency_standard_answers')
        count = cursor.fetchone()['count']
        
        print(f"\n验证结果:")
        print(f"- second_consistency_standard_answers 表存在")
        print(f"- 记录数: {count}")
        
        # 显示前几条记录
        cursor.execute('''
            SELECT audio_file, v_value, a_value, emotion_type, discrete_emotion, username
            FROM second_consistency_standard_answers 
            LIMIT 5
        ''')
        
        records = cursor.fetchall()
        if records:
            print(f"\n前5条记录:")
            for record in records:
                print(f"  {record['audio_file']}: v={record['v_value']}, a={record['a_value']}, type={record['emotion_type']}, discrete={record['discrete_emotion']}, user={record['username']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"验证导入结果时出错: {e}")
        return False

if __name__ == '__main__':
    print("开始导入第二次一致性测试标准答案...")
    
    # 导入数据
    success = import_second_consistency_standard_answers()
    
    if success:
        # 验证导入结果
        verify_import()
        print("\n导入完成!")
    else:
        print("\n导入失败!")
        sys.exit(1)