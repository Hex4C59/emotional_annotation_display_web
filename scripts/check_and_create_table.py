#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库状态并创建second_consistency_standard_answers表
"""

import os
import sys
import json
import glob
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('SECRET_KEY', 'temp_key_for_init_only_' + 'x' * 32)

def check_and_create_table():
    """
    检查数据库状态并创建second_consistency_standard_answers表
    """
    try:
        print("正在检查数据库状态...")
        
        # 导入并初始化数据库管理器
        from scripts.unified_db_manager import UnifiedDatabaseManager
        
        db_manager = UnifiedDatabaseManager()
        print(f"数据库路径: {db_manager.db_path}")
        
        # 获取数据库连接
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查所有表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
                ORDER BY name
            """)
            
            tables = [row['name'] for row in cursor.fetchall()]
            print(f"\n数据库中现有的表 ({len(tables)} 个):")
            for table in tables:
                print(f"  - {table}")
            
            # 检查second_consistency_standard_answers表是否存在
            if 'second_consistency_standard_answers' in tables:
                print("\n✅ second_consistency_standard_answers 表已存在")
            else:
                print("\n❌ second_consistency_standard_answers 表不存在，正在创建...")
                
                # 手动创建表
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
                
                conn.commit()
                print("✅ second_consistency_standard_answers 表创建成功")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(second_consistency_standard_answers)")
            columns = cursor.fetchall()
            print(f"\nsecond_consistency_standard_answers 表结构:")
            for col in columns:
                print(f"  {col['name']}: {col['type']} {'NOT NULL' if col['notnull'] else 'NULL'} {'PRIMARY KEY' if col['pk'] else ''}")
            
            # 检查表中的记录数
            cursor.execute('SELECT COUNT(*) as count FROM second_consistency_standard_answers')
            count = cursor.fetchone()['count']
            print(f"\n表中现有记录数: {count}")
            
            # 如果表为空，导入数据
            if count == 0:
                print("\n开始导入第二次一致性测试标准答案...")
                
                data_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/second_consistency_test'
                
                if not os.path.exists(data_dir):
                    print(f"数据目录不存在: {data_dir}")
                    return False
                
                # 获取所有JSON文件
                json_files = glob.glob(os.path.join(data_dir, '*.json'))
                print(f"找到 {len(json_files)} 个JSON文件")
                
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
                
                print(f"\n导入完成:")
                print(f"- 导入: {imported_count} 条")
                print(f"- 跳过: {skipped_count} 条")
                
                # 再次检查记录数
                cursor.execute('SELECT COUNT(*) as count FROM second_consistency_standard_answers')
                final_count = cursor.fetchone()['count']
                print(f"- 表中总计: {final_count} 条记录")
                
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
            else:
                print(f"\n表中已有 {count} 条记录，跳过导入")
        return True
        
    except Exception as e:
        print(f"检查和创建表过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始检查数据库状态并创建表...")
    
    success = check_and_create_table()
    
    if success:
        print("\n✅ 检查和创建完成!")
        print("现在可以正常计算第二次一致性测试得分了。")
    else:
        print("\n❌ 检查和创建失败!")
        sys.exit(1)