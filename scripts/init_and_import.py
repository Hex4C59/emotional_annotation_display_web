#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化数据库并导入第二次一致性测试标准答案
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

def init_database_and_import():
    """
    初始化数据库并导入第二次一致性测试标准答案
    """
    try:
        print("正在初始化数据库...")
        
        # 导入并初始化数据库管理器
        from scripts.unified_db_manager import UnifiedDatabaseManager
        
        db_manager = UnifiedDatabaseManager()
        print(f"数据库已初始化: {db_manager.db_path}")
        
        # 检查数据库文件是否存在
        if os.path.exists(db_manager.db_path):
            print("数据库文件已创建")
        else:
            print("错误: 数据库文件未创建")
            return False
        
        # 获取数据库连接
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查second_consistency_standard_answers表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='second_consistency_standard_answers'
            """)
            
            if cursor.fetchone():
                print("second_consistency_standard_answers 表已存在")
            else:
                print("错误: second_consistency_standard_answers 表不存在")
                return False
            
            # 导入第二次一致性测试标准答案
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
            
            # 验证导入结果
            cursor.execute('SELECT COUNT(*) as count FROM second_consistency_standard_answers')
            total_count = cursor.fetchone()['count']
            
            print(f"\n导入完成:")
            print(f"- 新导入: {imported_count} 条")
            print(f"- 跳过: {skipped_count} 条")
            print(f"- 表中总计: {total_count} 条记录")
            
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
        return True
        
    except Exception as e:
        print(f"初始化和导入过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始初始化数据库并导入第二次一致性测试标准答案...")
    
    success = init_database_and_import()
    
    if success:
        print("\n✅ 初始化和导入完成!")
        print("现在可以正常计算第二次一致性测试得分了。")
    else:
        print("\n❌ 初始化和导入失败!")
        sys.exit(1)