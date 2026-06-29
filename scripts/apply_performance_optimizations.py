#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用性能优化脚本

这个脚本会：n1. 删除旧的触发器
2. 创建优化后的触发器
3. 添加缺失的索引
4. 重新计算annotated_count字段
"""

import sqlite3
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 直接定义数据库路径
DATABASE_PATH = project_root / "data" / "emotion_labeling.db"

def apply_optimizations():
    """应用性能优化"""
    print("开始应用性能优化...")
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            print("1. 删除旧的触发器...")
            # 删除旧的触发器
            cursor.execute("DROP TRIGGER IF EXISTS update_annotated_count_on_insert")
            cursor.execute("DROP TRIGGER IF EXISTS update_annotated_count_on_delete")
            cursor.execute("DROP TRIGGER IF EXISTS update_annotated_count_on_update")
            
            print("2. 创建优化后的触发器...")
            # 创建优化的触发器
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
            
            print("3. 添加缺失的索引...")
            # 添加group_assignments表的索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_assignments_username ON group_assignments(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_assignments_group_id ON group_assignments(group_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_assignments_username_group ON group_assignments(username, group_id)')
            
            print("4. 重新计算annotated_count字段...")
            # 重新计算所有用户的annotated_count
            cursor.execute('''
                UPDATE group_assignments 
                SET annotated_count = (
                    SELECT COUNT(*) 
                    FROM emotion_labels 
                    WHERE emotion_labels.username = group_assignments.username 
                    AND va_complete = 1 AND discrete_complete = 1
                )
            ''')
            
            conn.commit()
            print("性能优化应用完成！")
            
            # 显示统计信息
            cursor.execute("SELECT COUNT(*) FROM group_assignments")
            group_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM emotion_labels")
            label_count = cursor.fetchone()[0]
            
            print(f"\n统计信息：")
            print(f"- 分组分配记录数: {group_count}")
            print(f"- 情感标注记录数: {label_count}")
            
    except Exception as e:
        print(f"应用优化时出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if apply_optimizations():
        print("\n✅ 性能优化应用成功！")
    else:
        print("\n❌ 性能优化应用失败！")
        sys.exit(1)