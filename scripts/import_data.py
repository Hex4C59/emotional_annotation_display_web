#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入第二次一致性测试标准答案数据
使用纯Python实现，不依赖sqlite3模块
"""

import os
import json
import glob
import subprocess
import tempfile
from pathlib import Path

def escape_sql_string(value):
    """转义SQL字符串"""
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)

def import_data():
    """
    导入第二次一致性测试标准答案数据
    """
    try:
        print("开始导入第二次一致性测试标准答案...")
        
        data_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/second_consistency_test'
        db_path = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/database/unified_emotion_system.db'
        
        if not os.path.exists(data_dir):
            print(f"数据目录不存在: {data_dir}")
            return False
        
        if not os.path.exists(db_path):
            print(f"数据库文件不存在: {db_path}")
            return False
        
        # 获取所有JSON文件
        json_files = glob.glob(os.path.join(data_dir, '*.json'))
        print(f"找到 {len(json_files)} 个JSON文件")
        
        if not json_files:
            print("没有找到JSON文件")
            return False
        
        # 生成SQL插入语句
        sql_statements = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                audio_file = data.get('audio_file')
                if not audio_file:
                    print(f"跳过文件 {json_file}: 缺少audio_file字段")
                    continue
                
                # 构建INSERT语句
                sql = f"""INSERT OR IGNORE INTO second_consistency_standard_answers (
                    audio_file, v_value, a_value, emotion_type, 
                    discrete_emotion, patient_status, audio_duration, username
                ) VALUES (
                    {escape_sql_string(audio_file)},
                    {escape_sql_string(data.get('v_value'))},
                    {escape_sql_string(data.get('a_value'))},
                    {escape_sql_string(data.get('emotion_type'))},
                    {escape_sql_string(data.get('discrete_emotion'))},
                    {escape_sql_string(data.get('patient_status'))},
                    {escape_sql_string(data.get('audio_duration'))},
                    {escape_sql_string(data.get('username'))}
                );"""
                
                sql_statements.append(sql)
                
            except Exception as e:
                print(f"处理文件 {json_file} 时出错: {e}")
                continue
        
        if not sql_statements:
            print("没有有效的数据可以导入")
            return False
        
        print(f"准备导入 {len(sql_statements)} 条记录")
        
        # 创建临时SQL文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            temp_file.write('BEGIN TRANSACTION;\n')
            for sql in sql_statements:
                temp_file.write(sql + '\n')
            temp_file.write('COMMIT;\n')
            temp_file.write('SELECT COUNT(*) as count FROM second_consistency_standard_answers;\n')
            temp_sql_path = temp_file.name
        
        try:
            # 执行SQL文件
            result = subprocess.run(
                ['sqlite3', db_path],
                input=open(temp_sql_path, 'r').read(),
                text=True,
                capture_output=True
            )
            
            if result.returncode == 0:
                print(f"导入成功!")
                print(f"输出: {result.stdout.strip()}")
                
                # 显示一些示例记录
                sample_sql = """SELECT audio_file, v_value, a_value, emotion_type, discrete_emotion, username
                FROM second_consistency_standard_answers 
                LIMIT 5;"""
                
                sample_result = subprocess.run(
                    ['sqlite3', db_path, '-header', '-column'],
                    input=sample_sql,
                    text=True,
                    capture_output=True
                )
                
                if sample_result.returncode == 0:
                    print("\n前5条记录:")
                    print(sample_result.stdout)
                
                return True
            else:
                print(f"导入失败: {result.stderr}")
                return False
                
        finally:
            # 清理临时文件
            os.unlink(temp_sql_path)
        
    except Exception as e:
        print(f"导入过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始导入第二次一致性测试标准答案数据...")
    
    success = import_data()
    
    if success:
        print("\n✅ 数据导入完成!")
        print("现在可以正常计算第二次一致性测试得分了。")
    else:
        print("\n❌ 数据导入失败!")
        exit(1)