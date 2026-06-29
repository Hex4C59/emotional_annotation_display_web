#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新group_assignments表，添加annotated_count字段并初始化数据
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.unified_db_manager import UnifiedDatabaseManager
from config import Config

def check_column_exists(db_path: str, table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        conn.close()
        return column_name in columns
        
    except Exception as e:
        print(f"检查列是否存在时出错: {e}")
        return False

def add_annotated_count_column(db_path: str) -> bool:
    """添加annotated_count列到group_assignments表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 添加annotated_count列
        cursor.execute('''
            ALTER TABLE group_assignments 
            ADD COLUMN annotated_count INTEGER DEFAULT 0
        ''')
        
        conn.commit()
        conn.close()
        print("成功添加annotated_count列")
        return True
        
    except Exception as e:
        print(f"添加annotated_count列失败: {e}")
        return False

def create_triggers(db_path: str) -> bool:
    """创建自动更新annotated_count的触发器"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 删除可能存在的旧触发器
        cursor.execute('DROP TRIGGER IF EXISTS update_annotated_count_on_insert')
        cursor.execute('DROP TRIGGER IF EXISTS update_annotated_count_on_delete')
        
        # 创建插入触发器
        cursor.execute('''
            CREATE TRIGGER update_annotated_count_on_insert
            AFTER INSERT ON emotion_labels
            FOR EACH ROW
            BEGIN
                UPDATE group_assignments 
                SET annotated_count = (
                    SELECT COUNT(*) FROM emotion_labels 
                    WHERE username = NEW.username
                )
                WHERE username = NEW.username;
            END
        ''')
        
        # 创建删除触发器
        cursor.execute('''
            CREATE TRIGGER update_annotated_count_on_delete
            AFTER DELETE ON emotion_labels
            FOR EACH ROW
            BEGIN
                UPDATE group_assignments 
                SET annotated_count = (
                    SELECT COUNT(*) FROM emotion_labels 
                    WHERE username = OLD.username
                )
                WHERE username = OLD.username;
            END
        ''')
        
        conn.commit()
        conn.close()
        print("成功创建触发器")
        return True
        
    except Exception as e:
        print(f"创建触发器失败: {e}")
        return False

def main():
    """主函数"""
    print("开始更新group_assignments表...")
    
    # 获取数据库路径
    db_manager = UnifiedDatabaseManager()
    db_path = db_manager.db_path
    
    print(f"数据库路径: {db_path}")
    
    # 检查annotated_count列是否已存在
    if check_column_exists(db_path, 'group_assignments', 'annotated_count'):
        print("annotated_count列已存在")
    else:
        print("添加annotated_count列...")
        if not add_annotated_count_column(db_path):
            print("添加列失败，退出")
            return
    
    # 创建触发器
    print("创建触发器...")
    if not create_triggers(db_path):
        print("创建触发器失败，退出")
        return
    
    # 更新现有数据的annotated_count
    print("更新现有用户的annotated_count...")
    if db_manager.update_all_annotated_counts():
        print("成功更新所有用户的标注统计")
    else:
        print("更新标注统计失败")
        return
    
    # 显示更新结果
    print("\n=== 更新结果 ===")
    stats = db_manager.get_all_users_annotation_stats()
    
    if not stats:
        print("没有找到用户数据")
        return
    
    print(f"{'用户名':<15} {'分组ID':<8} {'标注数量':<10} {'实际数量':<10} {'匹配':<6}")
    print("-" * 60)
    
    for stat in stats:
        match_status = "✓" if stat['count_match'] else "✗"
        print(f"{stat['username']:<15} {stat['group_id']:<8} {stat['annotated_count']:<10} {stat['actual_count']:<10} {match_status:<6}")
    
    print(f"\n总计: {len(stats)} 个用户")
    matched_count = sum(1 for stat in stats if stat['count_match'])
    print(f"数据匹配: {matched_count}/{len(stats)} 个用户")
    
    print("\n更新完成！")

if __name__ == '__main__':
    main()