#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分组分配管理器
简化版本：不依赖missing database tables
"""

import sqlite3
import os
import sys
from datetime import datetime

# 添加父目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

class GroupAssignmentManager:
    def __init__(self):
        self.db_path = os.path.join(Config.DATABASE_FOLDER, 'unified_emotion_system.db')
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """确保数据库存在"""
        if not os.path.exists(self.db_path):
            print(f"分组分配数据库不存在，请先运行初始化脚本")
            return False
        return True
    
    def get_available_group_for_user(self, username):
        """
        获取用户已分配的分组（简化版本：返回None）
        返回: (group_id, group_info) 或 None
        """
        # 简化版本：不使用数据库
        return None, None
    
    def get_user_annotation_stats(self, username):
        """
        获取用户的标注统计信息（简化版本：返回None）
        """
        # 简化版本：不使用数据库
        return None
    
    def update_annotated_count_for_user(self, username):
        """
        更新指定用户的annotated_count字段（简化版本：返回True）
        """
        # 简化版本：不使用数据库
        return True
    
    def update_second_consistency_completed(self, username, completed=True):
        """
        更新用户的第二次一致性测试完成状态（简化版本：不执行任何操作）
        
        Args:
            username: 用户名
            completed: 是否完成，默认为True
        """
        # 简化版本：不使用数据库
        pass

    def get_group_info(self, group_id):
        """
        获取分组信息（简化版本：返回空字典）
        """
        # 简化版本：不使用数据库
        return {}

    def get_user_assignment_info(self, username):
        """
        获取用户分配信息（简化版本：返回None）
        """
        # 简化版本：不使用数据库
        return None