# -*- coding: utf-8 -*-
"""
管理员服务
提供管理员后台管理功能的业务逻辑
"""

import os
import json
import csv
import sqlite3
import shutil
import glob
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

from config import Config
from .database_service import DatabaseService
from services.audio_service import AudioService
from .group_assignment_service import GroupAssignmentManager

class AdminService:
    """管理员服务类"""
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    def get_users_statistics(self) -> List[Dict[str, Any]]:
        """
        获取所有用户的标注统计信息
        
        Returns:
            List: 包含用户统计信息的列表
        """
        try:
            # 获取用户数据库连接
            with self.db_service.get_users_connection() as users_conn:
                users_cursor = users_conn.cursor()
                
                # 首先获取所有注册用户，包含分组信息
                users_cursor.execute("""
                    SELECT wechat_name, phone_number, created_at, group_id
                    FROM users
                    ORDER BY created_at DESC
                """)
                
                all_users = users_cursor.fetchall()
            
                # 获取标注数据库连接
                with self.db_service.get_connection() as labels_conn:
                    labels_cursor = labels_conn.cursor()
                
                    # 批量获取所有用户的分组分配信息
                    usernames = [user[0] for user in all_users]
                    placeholders = ','.join(['?' for _ in usernames])
                    
                    # 批量获取group_assignments数据
                    labels_cursor.execute(f"""
                        SELECT username, group_id, annotated_count, total_segments
                        FROM group_assignments 
                        WHERE username IN ({placeholders})
                    """, usernames)
                    
                    group_assignments = {}
                    for row in labels_cursor.fetchall():
                        group_assignments[row[0]] = {
                            'group_id': row[1],
                            'annotated_count': row[2] or 0,
                            'total_segments': row[3] or 0
                        }
                    
                    # 批量获取emotion_labels统计数据
                    labels_cursor.execute(f"""
                        SELECT 
                            username,
                            COUNT(*) as total_annotations,
                            SUM(CASE WHEN va_complete = 1 AND discrete_complete = 1 THEN 1 ELSE 0 END) as completed_annotations,

                            AVG(play_count) as avg_play_count
                        FROM emotion_labels 
                        WHERE username IN ({placeholders})
                        GROUP BY username
                    """, usernames)
                    
                    emotion_stats = {}
                    for row in labels_cursor.fetchall():
                        emotion_stats[row[0]] = {
                            'total_annotations': row[1] or 0,
                            'completed_annotations': row[2] or 0,
                            'avg_play_count': row[3] or 0
                        }
                    
                    users_data = []
                    
                    # 处理所有用户数据
                    for user_row in all_users:
                        username = user_row[0]  # wechat_name
                        phone_number = user_row[1]
                        created_at = user_row[2]
                        group_id = user_row[3]  # group_id
                        
                        # 获取分组分配信息
                        group_info = group_assignments.get(username, {
                            'group_id': group_id,
                            'annotated_count': 0,
                            'total_segments': 0
                        })
                        
                        # 获取emotion_labels统计信息
                        emotion_info = emotion_stats.get(username, {
                            'total_annotations': 0,
                            'completed_annotations': 0,

                            'avg_play_count': 0
                        })
                        
                        # 统一使用emotion_labels中真正完成的标注数作为completed_annotations
                        completed_annotations = emotion_info['completed_annotations']
                        
                        # 对于分组用户，使用分组的total_segments；未分组用户使用total_annotations
                        if group_id is None:
                            total_segments = emotion_info['total_annotations']
                        else:
                            total_segments = group_info['total_segments']
                        
                        # 计算完成率
                        completion_rate = (completed_annotations / total_segments * 100) if total_segments > 0 else 0
                        
                        # 确定显示的分组信息
                        display_group = f"第{group_id}组" if group_id else "未分组"
                        
                        users_data.append({
                            "username": username,
                            "phone_number": phone_number,
                            "created_at": created_at,
                            "user_group": display_group,
                            "group_id": group_id,
                            "total_annotations": total_segments,  # 分组数据量
                            "completed_annotations": completed_annotations,  # 完成数
                            "completion_rate": round(completion_rate, 2),
                            "group_total_segments": total_segments,

                            "avg_play_count": round(emotion_info['avg_play_count'], 2) if emotion_info['avg_play_count'] else 0
                        })
                    
                    # 数据库连接将在with语句结束时自动关闭
            
            # 按创建时间降序排列，确保所有用户都能显示
            users_data.sort(key=lambda x: x['created_at'], reverse=True)
            
            return users_data
            
        except Exception as e:
            raise Exception(f"获取用户统计失败: {str(e)}")
    
    def get_user_details(self, username: str) -> Dict[str, Any]:
        """
        获取指定用户的详细标注信息
        
        Args:
            username (str): 用户名
            
        Returns:
            Dict: 用户详细信息
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 用户基本信息
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_annotations,
                        SUM(CASE WHEN va_complete = 1 AND discrete_complete = 1 THEN 1 ELSE 0 END) as completed_annotations,
                        SUM(audio_duration) as total_duration,
                        AVG(play_count) as avg_play_count,
                        MIN(timestamp) as first_annotation
                    FROM emotion_labels 
                    WHERE username = ?
                """, (username,))
                
                user_info = cursor.fetchone()
                

                
                # 最近的标注记录
                cursor.execute("""
                    SELECT audio_file, speaker, va_complete, discrete_complete, timestamp
                    FROM emotion_labels 
                    WHERE username = ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (username,))
                
                recent_annotations = []
                for row in cursor.fetchall():
                    recent_annotations.append({
                        "audio_file": row[0],
                        "speaker": row[1],
                        "va_complete": bool(row[2]),
                        "discrete_complete": bool(row[3]),
                        "timestamp": row[4]
                    })
                
                completion_rate = (user_info[1] / user_info[0] * 100) if user_info[0] > 0 else 0
                
                return {
                    "username": username,
                    "total_annotations": user_info[0],
                    "completed_annotations": user_info[1],
                    "completion_rate": round(completion_rate, 2),
                    "total_duration": round(user_info[2], 2) if user_info[2] else 0,
                    "avg_play_count": round(user_info[3], 2) if user_info[3] else 0,
                    "first_annotation": user_info[4],
                    "recent_annotations": recent_annotations
                }
            
        except Exception as e:
            raise Exception(f"获取用户详细信息失败: {str(e)}")
    

    

    
    @staticmethod
    def get_groups_list() -> List[Dict[str, Any]]:
        """
        获取所有分组列表
        
        Returns:
            List: 分组信息列表
        """
        try:
            from .group_assignment_service import GroupAssignmentManager
            group_manager = GroupAssignmentManager()
            return group_manager.get_all_groups_status()
        except Exception as e:
            raise Exception(f"获取分组列表失败: {str(e)}")
    
    @staticmethod
    def get_group_detailed_statistics(group_id: int) -> Dict[str, Any]:
        """
        获取指定分组的详细统计信息
        
        Args:
            group_id: 分组ID
            
        Returns:
            Dict: 分组详细统计信息
        """
        try:
            from utils.group_data_viewer import GroupDataViewer
            viewer = GroupDataViewer()
            return viewer.get_group_statistics(group_id)
        except Exception as e:
            raise Exception(f"获取分组详细统计失败: {str(e)}")
    

    
    def get_annotation_quality(self, group_id=None) -> Dict[str, Any]:
        """
        获取标注质量分析
        
        Args:
            group_id: 分组ID，如果为None则获取所有数据
        
        Returns:
            Dict: 标注质量分析数据
        """
        try:
            if group_id is not None:
                return self._get_group_annotation_quality(group_id)
            else:
                return self._get_global_annotation_quality()
        except Exception as e:
            raise Exception(f"获取标注质量分析失败: {str(e)}")
    
    def _get_group_annotation_quality(self, group_id) -> Dict[str, Any]:
        """
        获取指定分组的标注质量分析
        """
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
        
            # 获取指定分组的用户A值分布
            cursor.execute("""
            SELECT 
                el.username,
                CASE 
                    WHEN el.a_value >= 1.0 AND el.a_value < 1.5 THEN '1.0'
                    WHEN el.a_value >= 1.5 AND el.a_value < 2.0 THEN '1.5'
                    WHEN el.a_value >= 2.0 AND el.a_value < 2.5 THEN '2.0'
                    WHEN el.a_value >= 2.5 AND el.a_value < 3.0 THEN '2.5'
                    WHEN el.a_value >= 3.0 AND el.a_value < 3.5 THEN '3.0'
                    WHEN el.a_value >= 3.5 AND el.a_value < 4.0 THEN '3.5'
                    WHEN el.a_value >= 4.0 AND el.a_value < 4.5 THEN '4.0'
                    WHEN el.a_value >= 4.5 AND el.a_value <= 5.0 THEN '4.5'
                END as a_range,
                COUNT(*) as count
            FROM emotion_labels el
            INNER JOIN (
                SELECT DISTINCT ga.username
                FROM group_assignments ga
                WHERE ga.group_id = ?
            ) gu ON el.username = gu.username
            WHERE el.a_value IS NOT NULL AND el.va_complete = 1
            GROUP BY el.username, a_range
            ORDER BY el.username, a_range
            """, (group_id,))
            
            a_value_distribution = {}
            for row in cursor.fetchall():
                username = row[0]
                a_range = row[1]
                count = row[2]
                if username not in a_value_distribution:
                    a_value_distribution[username] = {}
                a_value_distribution[username][a_range] = count
            
            # 获取指定分组的用户V值分布
            cursor.execute("""
                SELECT 
                    el.username,
                    CASE 
                        WHEN el.v_value >= -2.0 AND el.v_value < -1.5 THEN '-2.0'
                        WHEN el.v_value >= -1.5 AND el.v_value < -1.0 THEN '-1.5'
                        WHEN el.v_value >= -1.0 AND el.v_value < -0.5 THEN '-1.0'
                        WHEN el.v_value >= -0.5 AND el.v_value < 0.0 THEN '-0.5'
                        WHEN el.v_value >= 0.0 AND el.v_value < 0.5 THEN '0.0'
                        WHEN el.v_value >= 0.5 AND el.v_value < 1.0 THEN '0.5'
                        WHEN el.v_value >= 1.0 AND el.v_value < 1.5 THEN '1.0'
                        WHEN el.v_value >= 1.5 AND el.v_value <= 2.0 THEN '1.5'
                    END as v_range,
                    COUNT(*) as count
                FROM emotion_labels el
                INNER JOIN (
                    SELECT DISTINCT ga.username
                    FROM group_assignments ga
                    WHERE ga.group_id = ?
                ) gu ON el.username = gu.username
                WHERE el.v_value IS NOT NULL AND el.va_complete = 1
                GROUP BY el.username, v_range
                ORDER BY el.username, v_range
            """, (group_id,))
            
            v_value_distribution = {}
            for row in cursor.fetchall():
                username = row[0]
                v_range = row[1]
                count = row[2]
                if username not in v_value_distribution:
                    v_value_distribution[username] = {}
                v_value_distribution[username][v_range] = count
            
            # 获取指定分组的用户离散情感分布
            cursor.execute("""
                SELECT 
                    el.username,
                    el.discrete_emotion,
                    COUNT(*) as count
                FROM emotion_labels el
                INNER JOIN (
                    SELECT DISTINCT ga.username
                    FROM group_assignments ga
                    WHERE ga.group_id = ?
                ) gu ON el.username = gu.username
                WHERE el.discrete_emotion IS NOT NULL AND el.discrete_complete = 1
                GROUP BY el.username, el.discrete_emotion
                ORDER BY el.username, el.discrete_emotion
            """, (group_id,))
            
            discrete_emotion_distribution = {}
            for row in cursor.fetchall():
                username = row[0]
                emotion = row[1]
                count = row[2]
                if username not in discrete_emotion_distribution:
                    discrete_emotion_distribution[username] = {}
                discrete_emotion_distribution[username][emotion] = count
            
            return {
                "group_id": group_id,
                "a_value_distribution": a_value_distribution,
                "v_value_distribution": v_value_distribution,
                "discrete_emotion_distribution": discrete_emotion_distribution
            }
    
    def _get_global_annotation_quality(self) -> Dict[str, Any]:
        """
        获取全局标注质量分析
        """
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取全局A值分布（按用户分组）
            cursor.execute("""
                SELECT 
                    username,
                    CASE 
                        WHEN a_value >= 1.0 AND a_value < 1.5 THEN '1.0'
                        WHEN a_value >= 1.5 AND a_value < 2.0 THEN '1.5'
                        WHEN a_value >= 2.0 AND a_value < 2.5 THEN '2.0'
                        WHEN a_value >= 2.5 AND a_value < 3.0 THEN '2.5'
                        WHEN a_value >= 3.0 AND a_value < 3.5 THEN '3.0'
                        WHEN a_value >= 3.5 AND a_value < 4.0 THEN '3.5'
                        WHEN a_value >= 4.0 AND a_value < 4.5 THEN '4.0'
                        WHEN a_value >= 4.5 AND a_value <= 5.0 THEN '4.5'
                    END as a_range,
                    COUNT(*) as count
                FROM emotion_labels
                WHERE a_value IS NOT NULL AND va_complete = 1
                GROUP BY username, a_range
                ORDER BY username, a_range
            """)
            
            a_value_distribution = {}
            for row in cursor.fetchall():
                username = row[0]
                a_range = row[1]
                count = row[2]
                if a_range:  # 确保范围不为空
                    if username not in a_value_distribution:
                        a_value_distribution[username] = {}
                    a_value_distribution[username][a_range] = count
            
            # 获取全局V值分布（按用户分组）
            cursor.execute("""
                SELECT 
                    username,
                    CASE 
                        WHEN v_value >= -2.0 AND v_value < -1.5 THEN '-2.0'
                        WHEN v_value >= -1.5 AND v_value < -1.0 THEN '-1.5'
                        WHEN v_value >= -1.0 AND v_value < -0.5 THEN '-1.0'
                        WHEN v_value >= -0.5 AND v_value < 0.0 THEN '-0.5'
                        WHEN v_value >= 0.0 AND v_value < 0.5 THEN '0.0'
                        WHEN v_value >= 0.5 AND v_value < 1.0 THEN '0.5'
                        WHEN v_value >= 1.0 AND v_value < 1.5 THEN '1.0'
                        WHEN v_value >= 1.5 AND v_value <= 2.0 THEN '1.5'
                    END as v_range,
                    COUNT(*) as count
                FROM emotion_labels
                WHERE v_value IS NOT NULL AND va_complete = 1
                GROUP BY username, v_range
                ORDER BY username, v_range
            """)
            
            v_value_distribution = {}
            for row in cursor.fetchall():
                username = row[0]
                v_range = row[1]
                count = row[2]
                if v_range:  # 确保范围不为空
                    if username not in v_value_distribution:
                        v_value_distribution[username] = {}
                    v_value_distribution[username][v_range] = count
            
            # 获取所有数据的离散情感分布（按用户分组）
            cursor.execute("""
                SELECT 
                    username,
                    discrete_emotion,
                    COUNT(*) as count
                FROM emotion_labels
                WHERE discrete_emotion IS NOT NULL AND discrete_complete = 1
                GROUP BY username, discrete_emotion
                ORDER BY username, discrete_emotion
            """)
            
            discrete_emotion_distribution = {}
            for row in cursor.fetchall():
                username = row[0]
                emotion = row[1]
                count = row[2]
                if username not in discrete_emotion_distribution:
                    discrete_emotion_distribution[username] = {}
                discrete_emotion_distribution[username][emotion] = count
            
            # 标注时间分析（从创建到完成的时间）
            cursor.execute("""
                SELECT 
                    username,
                    AVG(JULIANDAY(updated_at) - JULIANDAY(timestamp)) * 24 * 60 as avg_annotation_time_minutes
                FROM emotion_labels
                WHERE va_complete = 1 AND discrete_complete = 1
                GROUP BY username
            """)
            
            annotation_time_by_user = []
            for row in cursor.fetchall():
                annotation_time_by_user.append({
                    "username": row[0],
                    "avg_time_minutes": round(row[1], 2) if row[1] else 0
                })
            
            return {
                "a_value_distribution": a_value_distribution,
                "v_value_distribution": v_value_distribution,
                "discrete_emotion_distribution": discrete_emotion_distribution,
                "annotation_time_by_user": annotation_time_by_user
            }
    
    def export_annotation_data(self, format='csv', username=None) -> Dict[str, Any]:
        """
        导出标注数据
        
        Args:
            format (str): 导出格式 ('csv' 或 'json')
            username (str, optional): 指定用户名
            
        Returns:
            Dict: 导出结果信息
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                where_conditions = []
                params = []
                
                if username:
                    where_conditions.append("username = ?")
                    params.append(username)
                

                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # 查询5点量表数据
                query_5point = f"""
                    SELECT 
                        audio_file, speaker, username, v_value, a_value, 
                        emotion_type, discrete_emotion, patient_status,
                        audio_duration, play_count, va_complete, discrete_complete,
                        va_scale, timestamp, updated_at
                    FROM emotion_labels
                    {where_clause}
                """
                
                cursor.execute(query_5point, params)
                data_5point = cursor.fetchall()
                
                # 查询9点量表数据
                query_9point = f"""
                    SELECT 
                        audio_file, speaker, username, v_value, a_value, 
                        emotion_type, discrete_emotion, patient_status,
                        audio_duration, play_count, va_complete, discrete_complete,
                        va_scale, timestamp, updated_at
                    FROM emotion_labels_9point
                    {where_clause}
                """
                
                cursor.execute(query_9point, params)
                data_9point = cursor.fetchall()
                
                # 为5点量表数据添加量表类型标识
                data_5point_with_scale = []
                for row in data_5point:
                    # 将va_scale字段替换为明确的5点量表标识
                    row_list = list(row)
                    row_list[12] = '5点量表'  # va_scale字段位置
                    data_5point_with_scale.append(tuple(row_list))
                
                # 为9点量表数据添加量表类型标识
                data_9point_with_scale = []
                for row in data_9point:
                    # 将va_scale字段替换为明确的9点量表标识
                    row_list = list(row)
                    row_list[12] = '9点量表'  # va_scale字段位置
                    data_9point_with_scale.append(tuple(row_list))
                
                # 合并数据并按时间戳排序
                data = data_5point_with_scale + data_9point_with_scale
                data.sort(key=lambda x: x[13])  # 按timestamp排序
                
                # 生成文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename_parts = ['emotion_labels', timestamp]
                if username:
                    filename_parts.insert(-1, f'user_{username}')

                
                filename = '_'.join(filename_parts)
                
                # 确保导出目录存在
                export_dir = os.path.join(Config.DATABASE_FOLDER, 'exports')
                os.makedirs(export_dir, exist_ok=True)
                
                if format.lower() == 'csv':
                    filepath = os.path.join(export_dir, f'{filename}.csv')
                    
                    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        
                        # 写入表头
                        headers = [
                            '音频文件', '说话人', '用户名', 'V值', 'A值',
                            '情感类型', '离散情感', '患者状态',
                            '音频时长', '播放次数', 'VA完成', '离散完成',
                            '量表类型(5点/9点)', '创建时间', '更新时间'
                        ]
                        writer.writerow(headers)
                        
                        # 写入数据
                        for row in data:
                            writer.writerow(row)
                             
                elif format.lower() == 'json':
                    filepath = os.path.join(export_dir, f'{filename}.json')
                    
                    json_data = []
                    for row in data:
                        json_data.append({
                            'audio_file': row[0],
                            'speaker': row[1],
                            'username': row[2],
                            'v_value': row[3],
                            'a_value': row[4],
                            'emotion_type': row[5],
                            'discrete_emotion': row[6],
                            'patient_status': row[7],
                            'audio_duration': row[8],
                            'play_count': row[9],
                            'va_complete': bool(row[10]),
                            'discrete_complete': bool(row[11]),
                            'scale_type': row[12],  # 量表类型：5点量表 或 9点量表
                            'timestamp': row[13],
                            'updated_at': row[14]
                        })
                    
                    with open(filepath, 'w', encoding='utf-8') as jsonfile:
                        json.dump(json_data, jsonfile, ensure_ascii=False, indent=2)
                         

                
                else:
                    raise ValueError(f"不支持的导出格式: {format}")
                
                return {
                    "success": True,
                    "message": "数据导出成功",
                    "filename": os.path.basename(filepath),
                    "filepath": filepath,
                    "record_count": len(data),
                    "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
        except Exception as e:
            raise Exception(f"导出数据失败: {str(e)}")
    
    def export_users_data(self, format='csv') -> Dict[str, Any]:
        """
        导出用户数据
        
        Args:
            format (str): 导出格式 ('csv' 或 'json')
            
        Returns:
            Dict: 导出结果
        """
        try:
            # 获取用户数据
            users_data = self.get_users_statistics()
            
            # 创建导出目录
            export_dir = os.path.join(Config.DATABASE_FOLDER, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'users_export_{timestamp}.{format}'
            filepath = os.path.join(export_dir, filename)
            
            if format.lower() == 'csv':
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    if users_data:
                        fieldnames = users_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(users_data)
            else:  # JSON
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(users_data, jsonfile, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "用户数据导出成功",
                "filepath": filepath,
                "filename": filename,
                "record_count": len(users_data),
                "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            raise Exception(f"导出用户数据失败: {str(e)}")
    
    def export_admins_data(self, format='csv') -> Dict[str, Any]:
        """
        导出管理员数据
        
        Args:
            format (str): 导出格式 ('csv' 或 'json')
            
        Returns:
            Dict: 导出结果
        """
        try:
            from models.admin_model import AdminModel
            
            admin_model = AdminModel()
            admins_data = admin_model.get_all_admins()
            
            # 创建导出目录
            export_dir = os.path.join(Config.DATABASE_FOLDER, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'admins_export_{timestamp}.{format}'
            filepath = os.path.join(export_dir, filename)
            
            if format.lower() == 'csv':
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    if admins_data:
                        fieldnames = admins_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(admins_data)
            else:  # JSON
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(admins_data, jsonfile, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "管理员数据导出成功",
                "filepath": filepath,
                "filename": filename,
                "record_count": len(admins_data),
                "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            raise Exception(f"导出管理员数据失败: {str(e)}")
    
    def export_groups_data(self, format='csv') -> Dict[str, Any]:
        """
        导出分组数据
        
        Args:
            format (str): 导出格式 ('csv' 或 'json')
            
        Returns:
            Dict: 导出结果
        """
        try:
            groups_data = self.get_groups_list()
            
            # 创建导出目录
            export_dir = os.path.join(Config.DATABASE_FOLDER, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'groups_export_{timestamp}.{format}'
            filepath = os.path.join(export_dir, filename)
            
            if format.lower() == 'csv':
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    if groups_data:
                        fieldnames = groups_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(groups_data)
            else:  # JSON
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(groups_data, jsonfile, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "分组数据导出成功",
                "filepath": filepath,
                "filename": filename,
                "record_count": len(groups_data),
                "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            raise Exception(f"导出分组数据失败: {str(e)}")
    
    def export_user_annotations_data(self, format='csv', username=None) -> Dict[str, Any]:
        """
        导出用户标注数据（包含5点量表和9点量表数据）
        
        Args:
            format (str): 导出格式 ('csv' 或 'json')
            username (str): 指定用户名，为None时导出所有用户
            
        Returns:
            Dict: 导出结果
        """
        try:
            # 获取标注数据（包含5点量表和9点量表）
            if username:
                # 导出指定用户的标注数据
                export_result = self.export_annotation_data(format=format, username=username)
                export_result['message'] = f"用户 {username} 的5点量表和9点量表标注数据导出成功"
                return export_result
            else:
                # 导出所有用户的标注数据
                export_result = self.export_annotation_data(format=format)
                export_result['message'] = "所有用户的5点量表和9点量表标注数据导出成功"
                return export_result
            
        except Exception as e:
            raise Exception(f"导出用户标注数据失败: {str(e)}")
    
    def batch_export_data(self, format='csv') -> Dict[str, Any]:
        """
        批量导出所有数据
        
        Args:
            format (str): 导出格式 ('csv' 或 'json')
            
        Returns:
            Dict: 导出结果
        """
        try:
            # 创建导出目录
            export_dir = os.path.join(Config.DATABASE_FOLDER, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'batch_export_{timestamp}.zip'
            filepath = os.path.join(export_dir, filename)
            
            # 创建临时目录
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # 导出各种数据
                exports = []
                
                # 1. 用户数据
                users_result = self.export_users_data(format)
                if users_result['success']:
                    exports.append(('users', users_result['filepath']))
                
                # 2. 管理员数据
                admins_result = self.export_admins_data(format)
                if admins_result['success']:
                    exports.append(('admins', admins_result['filepath']))
                
                # 3. 分组数据
                groups_result = self.export_groups_data(format)
                if groups_result['success']:
                    exports.append(('groups', groups_result['filepath']))
                
                # 4. 标注数据
                annotations_result = self.export_annotation_data(format)
                if annotations_result['success']:
                    exports.append(('annotations', annotations_result['filepath']))
                
                # 创建ZIP文件
                import zipfile
                with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for name, file_path in exports:
                        zipf.write(file_path, f'{name}_{os.path.basename(file_path)}')
                
                return {
                    "success": True,
                    "message": "批量导出成功",
                    "filepath": filepath,
                    "filename": filename,
                    "export_count": len(exports),
                    "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
        except Exception as e:
            raise Exception(f"批量导出失败: {str(e)}")
    
    @staticmethod
    def reset_user_progress(username: str) -> Dict[str, Any]:
        """
        重置用户标注进度
        
        Args:
            username (str): 用户名
            
        Returns:
            Dict: 重置结果
        """
        from services.database_service import DatabaseService
        
        db_service = DatabaseService()
        
        try:
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取要删除的标注记录数（5分量表）
                cursor.execute("SELECT COUNT(*) FROM emotion_labels WHERE username = ?", (username,))
                emotion_record_count = cursor.fetchone()[0]
                
                # 获取要删除的9分量表标注记录数
                cursor.execute("SELECT COUNT(*) FROM emotion_labels_9point WHERE username = ?", (username,))
                emotion_9point_record_count = cursor.fetchone()[0]
                
                # 获取要删除的第二次一致性测试记录数
                cursor.execute("SELECT COUNT(*) FROM second_consistency_test_results WHERE username = ?", (username,))
                consistency_record_count = cursor.fetchone()[0]
                
                # 删除用户的所有标注记录（5分量表）
                cursor.execute("DELETE FROM emotion_labels WHERE username = ?", (username,))
                
                # 删除用户的所有标注记录（9分量表）
                cursor.execute("DELETE FROM emotion_labels_9point WHERE username = ?", (username,))
                
                # 删除用户的第二次一致性测试记录
                cursor.execute("DELETE FROM second_consistency_test_results WHERE username = ?", (username,))
                
                # 重置用户的第二次一致性测试完成状态（使用同一个连接）
                cursor.execute('''
                    UPDATE group_assignments 
                    SET second_consistency_completed = ?
                    WHERE username = ?
                ''', (False, username))
                
                conn.commit()
                
                total_deleted = emotion_record_count + emotion_9point_record_count + consistency_record_count
                
                return {
                    "success": True,
                    "message": f"已重置用户 {username} 的标注进度和第二次一致性测试数据",
                    "deleted_records": total_deleted,
                    "deleted_emotion_records": emotion_record_count,
                    "deleted_emotion_9point_records": emotion_9point_record_count,
                    "deleted_consistency_records": consistency_record_count
                }
                
        except Exception as e:
            raise Exception(f"重置用户进度失败: {str(e)}")
    
    @staticmethod
    def backup_database() -> Dict[str, Any]:
        """
        备份数据库
        
        Returns:
            Dict: 备份结果
        """
        try:
            # 创建备份目录
            backup_dir = os.path.join(Config.DATABASE_FOLDER, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'emotion_labels_backup_{timestamp}.db'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 复制数据库文件
            source_db = DatabaseService.get_db_path()
            shutil.copy2(source_db, backup_path)
            
            # 获取备份文件大小
            backup_size = os.path.getsize(backup_path)
            
            return {
                "success": True,
                "message": "数据库备份成功",
                "backup_filename": backup_filename,
                "backup_path": backup_path,
                "backup_size": backup_size,
                "backup_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            raise Exception(f"数据库备份失败: {str(e)}")
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            Dict: 系统状态信息
        """
        try:
            # 数据库状态
            db_path = DatabaseService.get_db_path()
            db_exists = os.path.exists(db_path)
            db_size = os.path.getsize(db_path) if db_exists else 0
            
            # 音频文件夹状态
            audio_folder_exists = os.path.exists(Config.AUDIO_FOLDER)
            
            # 数据库连接测试
            try:
                db_service = DatabaseService()
                with db_service.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM emotion_labels")
                    db_accessible = True
                    total_records = cursor.fetchone()[0]
            except:
                db_accessible = False
                total_records = 0
            
            # 磁盘空间检查
            import shutil as disk_util
            total, used, free = disk_util.disk_usage(Config.DATABASE_FOLDER)
            
            return {
                "database": {
                    "exists": db_exists,
                    "accessible": db_accessible,
                    "size_bytes": db_size,
                    "size_mb": round(db_size / 1024 / 1024, 2),
                    "total_records": total_records
                },
                "audio_folder": {
                    "exists": audio_folder_exists,
                    "path": Config.AUDIO_FOLDER
                },
                "disk_space": {
                    "total_gb": round(total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(used / 1024 / 1024 / 1024, 2),
                    "free_gb": round(free / 1024 / 1024 / 1024, 2),
                    "usage_percent": round(used / total * 100, 2)
                },
                "check_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            raise Exception(f"获取系统状态失败: {str(e)}")
    
    def update_user_group(self, username, user_group):
        """
        更新用户分组（管理员手动分配）
        
        Args:
            username (str): 用户名
            user_group (str): 用户分组文本（如"第一组"），可以为None
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 将分组文本转换为group_id数字
            group_id = None
            if user_group and "第" in user_group and "组" in user_group:
                try:
                    import re
                    match = re.search(r'第(\d+)组', user_group)
                    if match:
                        group_id = int(match.group(1))
                except (ValueError, AttributeError):
                    group_id = None
            
            # 如果是分配到具体分组，需要检查分组是否存在且未满员
            if group_id is not None:
                # 检查分组是否存在
                with self.db_service.get_unified_connection() as unified_conn:
                    unified_cursor = unified_conn.cursor()
                    
                    unified_cursor.execute("""
                        SELECT group_id FROM group_status WHERE group_id = ?
                    """, (group_id,))
                    
                    if not unified_cursor.fetchone():
                        return False  # 分组不存在
                    
                    # 检查该分组当前分配人数
                    unified_cursor.execute("""
                        SELECT COUNT(*) FROM group_assignments WHERE group_id = ?
                    """, (group_id,))
                    
                    current_count = unified_cursor.fetchone()[0]
                    
                    # 检查用户是否已经在该分组中
                    unified_cursor.execute("""
                        SELECT username FROM group_assignments WHERE group_id = ? AND username = ?
                    """, (group_id, username))
                    
                    user_in_group = unified_cursor.fetchone()
                    
                    # 移除分组人数限制
                    # if not user_in_group and current_count >= 3:
                    #     return False  # 分组已满员
            
            users_conn = self.db_service.get_users_connection()
            users_cursor = users_conn.cursor()
            
            # 获取用户当前分组
            users_cursor.execute("""
                SELECT group_id FROM users WHERE wechat_name = ?
            """, (username,))
            
            current_group_result = users_cursor.fetchone()
            current_group_id = current_group_result[0] if current_group_result else None
            
            # 更新用户分组（存储group_id数字）
            users_cursor.execute("""
                UPDATE users 
                SET group_id = ?
                WHERE wechat_name = ?
            """, (group_id, username))
            
            users_conn.commit()
            users_conn.close()
            
            # 同步更新group_assignments表
            with self.db_service.get_unified_connection() as unified_conn:
                unified_cursor = unified_conn.cursor()
                
                try:
                    # 如果用户之前有分组，先从旧分组中移除
                    if current_group_id is not None:
                        unified_cursor.execute("""
                            DELETE FROM group_assignments WHERE username = ? AND group_id = ?
                        """, (username, current_group_id))
                        
                        # 更新旧分组的分配计数和状态
                        unified_cursor.execute("""
                            UPDATE group_status 
                            SET assigned_count = assigned_count - 1,
                                status = 'available',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE group_id = ?
                        """, (current_group_id,))
                        
                        # 清除该用户的排序记录（说话人排序和音频排序）
                        unified_cursor.execute('DELETE FROM user_speaker_orders WHERE username = ?', (username,))
                        unified_cursor.execute('DELETE FROM user_audio_orders WHERE username = ?', (username,))
                
                    # 如果分配到新分组，添加到group_assignments
                    if group_id is not None:
                        # 获取分组的总段数
                        unified_cursor.execute("""
                            SELECT total_segments FROM group_status WHERE group_id = ?
                        """, (group_id,))
                        
                        total_segments_result = unified_cursor.fetchone()
                        total_segments = total_segments_result[0] if total_segments_result else 0
                        
                        # 添加用户到新分组
                        unified_cursor.execute("""
                            INSERT OR REPLACE INTO group_assignments 
                            (group_id, username, status, total_segments, assigned_at)
                            VALUES (?, ?, 'assigned', ?, CURRENT_TIMESTAMP)
                        """, (group_id, username, total_segments))
                        
                        # 更新新分组的分配计数和状态
                        unified_cursor.execute("""
                            UPDATE group_status 
                            SET assigned_count = (
                                SELECT COUNT(*) FROM group_assignments WHERE group_id = ?
                            ),
                            status = 'available',
                            updated_at = CURRENT_TIMESTAMP
                            WHERE group_id = ?
                        """, (group_id, group_id))
                        
                        # 为用户预生成排序数据
                        self._generate_user_orders(username, group_id, unified_cursor)
                    
                    unified_conn.commit()
                
                except Exception as e:
                    unified_conn.rollback()
                    raise e
            
            return True
            
        except Exception as e:
            return False
    
    def _generate_user_orders(self, username, group_id, unified_cursor):
        """
        为用户预生成排序数据（说话人排序和音频排序）
        
        Args:
            username (str): 用户名
            group_id (int): 分组ID
            unified_cursor: 数据库游标
        """
        try:
            import random
            import json
            from datetime import datetime
            from .group_assignment_service import GroupAssignmentManager
            
            # 获取分组中的说话人列表
            group_manager = GroupAssignmentManager()
            assigned_speakers = group_manager.get_group_speakers(group_id)
            
            if not assigned_speakers:
                return
            
            # 清除该用户的所有旧排序记录（说话人排序和音频排序）
            unified_cursor.execute('DELETE FROM user_speaker_orders WHERE username = ?', (username,))
            unified_cursor.execute('DELETE FROM user_audio_orders WHERE username = ?', (username,))
            
            # 生成说话人排序
            speaker_list = list(assigned_speakers)
            random.seed(hash(f"{username}_speakers") % (2**32))
            random.shuffle(speaker_list)
            random.seed()
            
            # 保存说话人排序
            unified_cursor.execute('''
                INSERT INTO user_speaker_orders 
                (username, speaker_order, group_id, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (
                username,
                json.dumps(speaker_list, ensure_ascii=False),
                group_id,
                datetime.now().isoformat()
            ))
            
            # 为每个说话人生成音频排序
            from config import Config
            import os
            import re
            
            if os.path.exists(Config.AUDIO_FOLDER):
                # 获取所有音频目录
                all_audio_dirs = [
                    d for d in os.listdir(Config.AUDIO_FOLDER)
                    if os.path.isdir(os.path.join(Config.AUDIO_FOLDER, d))
                ]
                
                for speaker in assigned_speakers:
                    # 找到该说话人对应的音频目录
                    speaker_audio_dirs = []
                    for audio_dir in all_audio_dirs:
                        # 匹配 spkX-Y-Z 格式
                        match = re.match(r'(spk)(\d+)-(\d+)-(\d+)', audio_dir)
                        if match:
                            prefix, spk_id, part, section = match.groups()
                            spk_group = f"spk{spk_id}"
                            if spk_group == speaker:
                                speaker_audio_dirs.append(audio_dir)
                        else:
                            # 直接匹配的说话人
                            if audio_dir == speaker:
                                speaker_audio_dirs.append(audio_dir)
                    
                    if speaker_audio_dirs:
                        # 获取该说话人的所有音频文件
                        audio_files = []
                        for audio_dir in speaker_audio_dirs:
                            audio_dir_path = os.path.join(Config.AUDIO_FOLDER, audio_dir)
                            if os.path.exists(audio_dir_path):
                                files = [
                                    f for f in os.listdir(audio_dir_path)
                                    if f.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))
                                ]
                                audio_files.extend(files)
                        
                        if audio_files:
                            # 生成音频文件排序
                            random.seed(hash(f"{username}_{speaker}_audio") % (2**32))
                            random.shuffle(audio_files)
                            random.seed()
                            
                            # 保存音频排序
                            unified_cursor.execute('''
                                INSERT INTO user_audio_orders 
                                (username, speaker, audio_order, group_id, updated_at)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (
                                username,
                                speaker,
                                json.dumps(audio_files, ensure_ascii=False),
                                group_id,
                                datetime.now().isoformat()
                            ))
            
        except Exception as e:
            print(f"生成用户排序数据失败: {e}")
    
    def update_user_group_with_validation(self, username, user_group):
        """
        更新用户分组（带详细验证和错误信息）
        
        Args:
            username (str): 用户名
            user_group (str): 用户分组文本（如"第一组"），可以为None
            
        Returns:
            tuple: (success: bool, error_message: str)
        """
        try:
            # 将分组文本转换为group_id数字
            group_id = None
            if user_group:
                # 处理前端发送的group1、group2等格式
                if user_group.startswith('group') and user_group[5:].isdigit():
                    group_id = int(user_group[5:])
                # 处理第X组格式
                elif "第" in user_group and "组" in user_group:
                    try:
                        import re
                        match = re.search(r'第(\d+)组', user_group)
                        if match:
                            group_id = int(match.group(1))
                    except (ValueError, AttributeError):
                        return False, "分组格式不正确"
                # 删除了测试组功能
                else:
                    return False, f"不支持的分组格式: {user_group}"
            
            # 如果是分配到具体分组，需要检查分组是否存在且未满员
            if group_id is not None:
                # 检查分组是否存在
                with self.db_service.get_unified_connection() as unified_conn:
                    unified_cursor = unified_conn.cursor()
                    
                    unified_cursor.execute("""
                        SELECT group_id FROM group_status WHERE group_id = ?
                    """, (group_id,))
                    
                    if not unified_cursor.fetchone():
                        return False, f"分组 {user_group} 不存在"
                    
                    # 检查该分组当前分配人数
                    unified_cursor.execute("""
                        SELECT COUNT(*) FROM group_assignments WHERE group_id = ?
                    """, (group_id,))
                    
                    current_count = unified_cursor.fetchone()[0]
                    
                    # 检查用户是否已经在该分组中
                    unified_cursor.execute("""
                        SELECT username FROM group_assignments WHERE group_id = ? AND username = ?
                    """, (group_id, username))
                    
                    user_in_group = unified_cursor.fetchone()
                    
                    # 移除分组人数限制
                    # if not user_in_group and current_count >= 3:
                    #     return False, f"分组 {user_group} 已满员（最多3人），当前已有 {current_count} 人"
            
            # 调用原有的更新方法，传递转换后的group_id对应的文本
            group_text = None
            if group_id is not None:
                group_text = f"第{group_id}组"
            success = self.update_user_group(username, group_text)
            
            if success:
                return True, None
            else:
                return False, "数据库更新失败"
            
        except Exception as e:
            error_msg = str(e)
            if "SQLite3 模块不可用" in error_msg:
                return False, "数据库模块不可用，请联系系统管理员检查Python环境的SQLite3支持"
            elif "no such table" in error_msg.lower():
                return False, "数据库表不存在，请联系系统管理员初始化数据库"
            elif "database is locked" in error_msg.lower():
                return False, "数据库被锁定，请稍后重试"
            else:
                return False, f"更新失败: {error_msg}"
    
    def get_consistency_analysis(self) -> Dict[str, Any]:
        """
        获取一致性分析数据
        
        Returns:
            Dict: 一致性分析数据
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取一致性测试结果统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_comparisons,
                        COUNT(DISTINCT username) as total_users
                    FROM consistency_test_results
                """)
                
                basic_stats = cursor.fetchone()
                total_comparisons = basic_stats[0] if basic_stats else 0
                total_users = basic_stats[1] if basic_stats else 0
                
                # 获取用户一致性详情
                cursor.execute("""
                    SELECT 
                        ctr.username,
                        COUNT(*) as comparison_count,
                        SUM(CASE 
                            WHEN ABS(ctr.v_value - sa.v_value) <= 0.2 
                                 AND ABS(ctr.a_value - sa.a_value) <= 0.2 
                                 AND ctr.discrete_emotion = sa.discrete_emotion 
                            THEN 1 ELSE 0 
                        END) as consistent_count
                    FROM consistency_test_results ctr
                    LEFT JOIN standard_answers sa ON ctr.audio_file = sa.audio_file
                    GROUP BY ctr.username
                    ORDER BY ctr.username
                """)
                
                user_details = []
                total_consistency = 0
                high_consistency_users = 0
                low_consistency_users = 0
                
                for row in cursor.fetchall():
                    username = row[0]
                    comparison_count = row[1]
                    consistent_count = row[2] or 0
                    
                    consistency = (consistent_count / comparison_count * 100) if comparison_count > 0 else 0
                    total_consistency += consistency
                    
                    if consistency >= 80:
                        high_consistency_users += 1
                    elif consistency < 60:
                        low_consistency_users += 1
                    
                    user_details.append({
                        "username": username,
                        "comparison_count": comparison_count,
                        "consistent_count": consistent_count,
                        "consistency": round(consistency, 2)
                    })
                
                avg_consistency = (total_consistency / len(user_details)) if user_details else 0
                
                return {
                    "total_comparisons": total_comparisons,
                    "total_users": total_users,
                    "avg_consistency": round(avg_consistency, 2),
                    "high_consistency_users": high_consistency_users,
                    "low_consistency_users": low_consistency_users,
                    "user_details": user_details
                }
                
        except Exception as e:
            raise Exception(f"获取一致性分析数据失败: {str(e)}")