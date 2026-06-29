#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分组数据查看器
用于查看和分析unified_emotion_system.db中的分组数据和标注情况
"""

import sqlite3
import os
from datetime import datetime
from collections import defaultdict

class GroupDataViewer:
    def __init__(self, db_path=None):
        """
        初始化分组数据查看器
        
        Args:
            db_path (str): 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            self.db_path = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/database/unified_emotion_system.db'
        else:
            self.db_path = db_path
    
    def get_database_schema(self):
        """
        获取数据库表结构
        
        Returns:
            dict: 包含所有表结构的字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schema = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                schema[table_name] = columns
            
            return schema
        finally:
            conn.close()
    
    def get_all_groups(self):
        """
        获取所有分组信息
        
        Returns:
            list: 分组信息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT group_id, total_duration, total_segments, 
                       assigned_count, completed_count, status
                FROM group_status 
                ORDER BY group_id
            """)
            
            groups = cursor.fetchall()
            return [{
                'group_id': group[0],
                'total_duration': group[1],
                'total_segments': group[2],
                'assigned_count': group[3],
                'completed_count': group[4],
                'status': group[5]
            } for group in groups]
        finally:
            conn.close()
    
    def get_group_speakers(self, group_id):
        """
        获取指定分组的说话人信息
        
        Args:
            group_id (int): 分组ID
            
        Returns:
            list: 说话人信息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT speaker_id, duration, segment_count
                FROM speaker_groups 
                WHERE group_id = ?
                ORDER BY duration DESC
            """, (group_id,))
            
            speakers = cursor.fetchall()
            return [{
                'speaker_id': speaker[0],
                'duration': speaker[1],
                'segment_count': speaker[2]
            } for speaker in speakers]
        finally:
            conn.close()
    
    def get_group_assignments(self, group_id=None):
        """
        获取分组分配信息
        
        Args:
            group_id (int, optional): 分组ID，如果为None则获取所有分组
            
        Returns:
            list: 分配信息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if group_id is None:
                cursor.execute("""
                    SELECT group_id, username, assigned_at, status, 
                           progress_count, total_segments, completed_at
                    FROM group_assignments 
                    ORDER BY group_id, username
                """)
            else:
                cursor.execute("""
                    SELECT group_id, username, assigned_at, status, 
                           progress_count, total_segments, completed_at
                    FROM group_assignments 
                    WHERE group_id = ?
                    ORDER BY username
                """, (group_id,))
            
            assignments = cursor.fetchall()
            return [{
                'group_id': assignment[0],
                'username': assignment[1],
                'assigned_at': assignment[2],
                'status': assignment[3],
                'progress_count': assignment[4],
                'total_segments': assignment[5],
                'completed_at': assignment[6],
                'completion_rate': round((assignment[4] / assignment[5] * 100) if assignment[5] > 0 else 0, 2)
            } for assignment in assignments]
        finally:
            conn.close()
    
    def get_user_annotation_progress(self, group_id=None, username=None):
        """
        获取用户标注进度详情
        
        Args:
            group_id (int, optional): 分组ID
            username (str, optional): 用户名
            
        Returns:
            list: 标注进度详情列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT username, group_id, speaker_id, audio_file, 
                       annotation_status, annotated_at, va_value, a_value, emotion
                FROM user_annotation_progress 
                WHERE 1=1
            """
            params = []
            
            if group_id is not None:
                query += " AND group_id = ?"
                params.append(group_id)
            
            if username is not None:
                query += " AND username = ?"
                params.append(username)
            
            query += " ORDER BY group_id, username, speaker_id, audio_file"
            
            cursor.execute(query, params)
            
            progress = cursor.fetchall()
            return [{
                'username': p[0],
                'group_id': p[1],
                'speaker_id': p[2],
                'audio_file': p[3],
                'annotation_status': p[4],
                'annotated_at': p[5],
                'va_value': p[6],
                'a_value': p[7],
                'emotion': p[8]
            } for p in progress]
        finally:
            conn.close()
    
    def get_group_statistics(self, group_id):
        """
        获取指定分组的详细统计信息
        
        Args:
            group_id (int): 分组ID
            
        Returns:
            dict: 分组统计信息
        """
        # 获取分组基本信息
        groups = self.get_all_groups()
        group_info = next((g for g in groups if g['group_id'] == group_id), None)
        
        if not group_info:
            return None
        
        # 获取分组分配信息
        assignments = self.get_group_assignments(group_id)
        
        # 获取说话人信息
        speakers = self.get_group_speakers(group_id)
        
        # 获取标注进度详情
        progress_details = self.get_user_annotation_progress(group_id)
        
        # 计算统计信息
        total_users = len(assignments)
        completed_users = len([a for a in assignments if a['status'] == 'completed'])
        in_progress_users = len([a for a in assignments if a['status'] == 'in_progress'])
        
        # 按说话人统计标注情况
        speaker_stats = defaultdict(lambda: {
            'total_segments': 0,
            'completed_segments': 0,
            'users_working': set(),
            'completion_rate': 0
        })
        
        for speaker in speakers:
            speaker_id = speaker['speaker_id']
            speaker_stats[speaker_id]['total_segments'] = speaker['segment_count']
        
        for progress in progress_details:
            speaker_id = progress['speaker_id']
            if progress['annotation_status'] == 'completed':
                speaker_stats[speaker_id]['completed_segments'] += 1
            speaker_stats[speaker_id]['users_working'].add(progress['username'])
        
        # 计算完成率
        for speaker_id in speaker_stats:
            total = speaker_stats[speaker_id]['total_segments']
            completed = speaker_stats[speaker_id]['completed_segments']
            speaker_stats[speaker_id]['completion_rate'] = round((completed / total * 100) if total > 0 else 0, 2)
            speaker_stats[speaker_id]['users_working'] = list(speaker_stats[speaker_id]['users_working'])
        
        # 计算整体完成率
        total_assigned_segments = sum(a['total_segments'] for a in assignments)
        total_completed_segments = sum(a['progress_count'] for a in assignments)
        overall_completion_rate = round((total_completed_segments / total_assigned_segments * 100) if total_assigned_segments > 0 else 0, 2)
        
        return {
            'group_info': group_info,
            'assignments': assignments,
            'speakers': speakers,
            'speaker_statistics': dict(speaker_stats),
            'summary': {
                'total_users': total_users,
                'completed_users': completed_users,
                'in_progress_users': in_progress_users,
                'total_speakers': len(speakers),
                'total_segments': group_info['total_segments'],
                'total_assigned_segments': total_assigned_segments,
                'total_completed_segments': total_completed_segments,
                'overall_completion_rate': overall_completion_rate
            }
        }
    
    def print_group_summary(self, group_id):
        """
        打印分组摘要信息
        
        Args:
            group_id (int): 分组ID
        """
        stats = self.get_group_statistics(group_id)
        
        if not stats:
            print(f"分组 {group_id} 不存在")
            return
        
        print(f"\n=== 分组 {group_id} 统计信息 ===")
        print(f"总时长: {stats['group_info']['total_duration']:.2f} 小时")
        print(f"总段数: {stats['group_info']['total_segments']}")
        print(f"分配用户数: {stats['summary']['total_users']}")
        print(f"完成用户数: {stats['summary']['completed_users']}")
        print(f"进行中用户数: {stats['summary']['in_progress_users']}")
        print(f"总体完成率: {stats['summary']['overall_completion_rate']}%")
        
        print(f"\n--- 用户分配情况 ---")
        for assignment in stats['assignments']:
            print(f"用户: {assignment['username']}, 状态: {assignment['status']}, "
                  f"进度: {assignment['progress_count']}/{assignment['total_segments']} "
                  f"({assignment['completion_rate']}%)")
        
        print(f"\n--- 说话人标注情况 ---")
        for speaker in stats['speakers'][:10]:  # 只显示前10个说话人
            speaker_id = speaker['speaker_id']
            speaker_stat = stats['speaker_statistics'].get(speaker_id, {})
            print(f"说话人: {speaker_id}, 总段数: {speaker['segment_count']}, "
                  f"已完成: {speaker_stat.get('completed_segments', 0)}, "
                  f"完成率: {speaker_stat.get('completion_rate', 0)}%, "
                  f"参与用户: {len(speaker_stat.get('users_working', []))}")
        
        if len(stats['speakers']) > 10:
            print(f"... 还有 {len(stats['speakers']) - 10} 个说话人")

def main():
    """
    主函数，用于测试和演示
    """
    viewer = GroupDataViewer()
    
    print("=== 数据库表结构 ===")
    schema = viewer.get_database_schema()
    for table_name, columns in schema.items():
        print(f"\n表: {table_name}")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    print("\n=== 所有分组信息 ===")
    groups = viewer.get_all_groups()
    for group in groups:
        print(f"分组 {group['group_id']}: {group['total_segments']} 段, "
              f"{group['assigned_count']} 用户, 状态: {group['status']}")
    
    # 显示每个分组的详细统计
    for group in groups:
        viewer.print_group_summary(group['group_id'])

if __name__ == '__main__':
    main()