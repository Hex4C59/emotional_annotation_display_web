#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准答案服务
用于处理标准答案数据的数据库操作
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from .database_service import DatabaseService
from utils.logger import emotion_logger

class StandardAnswersService:
    """标准答案服务类"""
    
    def __init__(self):
        """初始化标准答案服务"""
        self.db_service = DatabaseService()
    
    def get_standard_answer(self, audio_file):
        """
        获取指定音频文件的标准答案
        
        Args:
            audio_file (str): 音频文件名
            
        Returns:
            dict: 标准答案数据，如果不存在返回None
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT audio_file, v_value, a_value, emotion_type, 
                           discrete_emotion, patient_status, audio_duration,
                           created_by, timestamp, updated_at
                    FROM standard_answers 
                    WHERE audio_file = ?
                ''', (audio_file,))
                
                result = cursor.fetchone()
            
            if result:
                return {
                    'audio_file': result[0],
                    'v_value': result[1],
                    'a_value': result[2],
                    'emotion_type': result[3],
                    'discrete_emotion': result[4],
                    'patient_status': result[5],
                    'audio_duration': result[6],
                    'created_by': result[7],
                    'timestamp': result[8],
                    'updated_at': result[9]
                }
            return None
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="SELECT",
                table="standard_answers",
                username="system",
                details={"audio_file": audio_file, "error": str(e)},
                success=False
            )
            print(f"获取标准答案时出错: {e}")
            return None
    
    def get_all_standard_answers(self):
        """
        获取所有标准答案
        
        Returns:
            list: 标准答案列表
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT audio_file, v_value, a_value, emotion_type, 
                           discrete_emotion, patient_status, audio_duration,
                           created_by, timestamp, updated_at
                    FROM standard_answers 
                    ORDER BY audio_file
                ''')
                
                results = cursor.fetchall()
            
            standard_answers = []
            for result in results:
                standard_answers.append({
                    'audio_file': result[0],
                    'v_value': result[1],
                    'a_value': result[2],
                    'emotion_type': result[3],
                    'discrete_emotion': result[4],
                    'patient_status': result[5],
                    'audio_duration': result[6],
                    'created_by': result[7],
                    'timestamp': result[8],
                    'updated_at': result[9]
                })
            
            return standard_answers
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="SELECT ALL",
                table="standard_answers",
                username="system",
                details={"error": str(e)},
                success=False
            )
            print(f"获取所有标准答案时出错: {e}")
            return []
    
    def add_or_update_standard_answer(self, answer_data):
        """
        添加或更新标准答案
        
        Args:
            answer_data (dict): 标准答案数据
            
        Returns:
            bool: 操作是否成功
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查记录是否已存在
                cursor.execute('SELECT id FROM standard_answers WHERE audio_file = ?', 
                             (answer_data['audio_file'],))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE standard_answers 
                        SET v_value = ?, a_value = ?, emotion_type = ?, 
                            discrete_emotion = ?, patient_status = ?, 
                            audio_duration = ?, created_by = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE audio_file = ?
                    ''', (
                        answer_data.get('v_value'),
                        answer_data.get('a_value'),
                        answer_data.get('emotion_type'),
                        answer_data.get('discrete_emotion'),
                        answer_data.get('patient_status'),
                        answer_data.get('audio_duration'),
                        answer_data.get('created_by', '手动添加'),
                        answer_data['audio_file']
                    ))
                    operation = "UPDATE"
                else:
                    # 插入新记录
                    cursor.execute('''
                        INSERT INTO standard_answers 
                        (audio_file, v_value, a_value, emotion_type, discrete_emotion, 
                         patient_status, audio_duration, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        answer_data['audio_file'],
                        answer_data.get('v_value'),
                        answer_data.get('a_value'),
                        answer_data.get('emotion_type'),
                        answer_data.get('discrete_emotion'),
                        answer_data.get('patient_status'),
                        answer_data.get('audio_duration'),
                        answer_data.get('created_by', '手动添加')
                    ))
                    operation = "INSERT"
                
                conn.commit()
            
            emotion_logger.log_database_operation(
                operation=operation,
                table="standard_answers",
                username="system",
                details={
                    "audio_file": answer_data['audio_file'],
                    "emotion_type": answer_data.get('emotion_type'),
                    "discrete_emotion": answer_data.get('discrete_emotion')
                },
                success=True
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="INSERT/UPDATE",
                table="standard_answers",
                username="system",
                details={"audio_file": answer_data.get('audio_file'), "error": str(e)},
                success=False
            )
            print(f"添加或更新标准答案时出错: {e}")
            return False
    
    def delete_standard_answer(self, audio_file):
        """
        删除标准答案
        
        Args:
            audio_file (str): 音频文件名
            
        Returns:
            bool: 删除是否成功
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM standard_answers WHERE audio_file = ?', (audio_file,))
                
                conn.commit()
            
            emotion_logger.log_database_operation(
                operation="DELETE",
                table="standard_answers",
                username="system",
                details={"audio_file": audio_file},
                success=True
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="DELETE",
                table="standard_answers",
                username="system",
                details={"audio_file": audio_file, "error": str(e)},
                success=False
            )
            print(f"删除标准答案时出错: {e}")
            return False
    
    def get_statistics(self):
        """
        获取标准答案统计信息
        
        Returns:
            dict: 统计信息
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute('SELECT COUNT(*) FROM standard_answers')
                total_count = cursor.fetchone()[0]
                
                # 按情感类型统计
                cursor.execute('''
                    SELECT emotion_type, COUNT(*) 
                    FROM standard_answers 
                    GROUP BY emotion_type
                    ORDER BY COUNT(*) DESC
                ''')
                emotion_stats = cursor.fetchall()
                
                # 按离散情感统计
                cursor.execute('''
                    SELECT discrete_emotion, COUNT(*) 
                    FROM standard_answers 
                    GROUP BY discrete_emotion
                    ORDER BY COUNT(*) DESC
                ''')
                discrete_stats = cursor.fetchall()
                
                # 按患者状态统计
                cursor.execute('''
                    SELECT patient_status, COUNT(*) 
                    FROM standard_answers 
                    GROUP BY patient_status
                    ORDER BY COUNT(*) DESC
                ''')
                status_stats = cursor.fetchall()
            
            return {
                'total_count': total_count,
                'emotion_type_stats': dict(emotion_stats),
                'discrete_emotion_stats': dict(discrete_stats),
                'patient_status_stats': dict(status_stats)
            }
            
        except Exception as e:
            emotion_logger.log_database_operation(
                operation="STATISTICS",
                table="standard_answers",
                username="system",
                details={"error": str(e)},
                success=False
            )
            print(f"获取统计信息时出错: {e}")
            return {
                'total_count': 0,
                'emotion_type_stats': {},
                'discrete_emotion_stats': {},
                'patient_status_stats': {}
            }
    
    @staticmethod
    def calculate_consistency_with_standard(user_results):
        """
        计算用户结果与标准答案的一致性
        
        Args:
            user_results (list): 用户标注结果列表
            
        Returns:
            dict: 一致性分析结果
        """
        try:
            # 获取所有标准答案
            standard_answers = {}
            service = StandardAnswersService()
            all_standards = service.get_all_standard_answers()
            for standard in all_standards:
                standard_answers[standard['audio_file']] = standard
            
            total_samples = len(user_results)
            if total_samples == 0:
                return {
                    'total_samples': 0,
                    'matched_samples': 0,
                    'v_consistency': 0,
                    'a_consistency': 0,
                    'discrete_consistency': 0,
                    'overall_consistency': 0,
                    'detailed_results': []
                }
            
            matched_samples = 0
            total_v_score = 0
            total_a_score = 0
            total_discrete_score = 0
            detailed_results = []
            
            for result in user_results:
                audio_file = result.get('audio_file')
                if not audio_file:
                    continue
                
                standard = standard_answers.get(audio_file)
                if not standard:
                    continue
                
                matched_samples += 1
                
                # 计算V值一致性
                user_v = result.get('v_value', 0)
                user_a = result.get('a_value', 0)
                standard_v = standard.get('v_value', 0)
                standard_a = standard.get('a_value', 0)
                
                if user_v is not None and user_a is not None and standard_v is not None and standard_a is not None:
                    # V值计算：完全相同=100%，差0.5=50%，其他=0%
                    v_diff = abs(user_v - standard_v)
                    if v_diff == 0:
                        v_score = 1.0  # 100%正确率
                    elif v_diff == 0.5:
                        v_score = 0.5  # 50%正确率
                    else:
                        v_score = 0.0  # 0%正确率
                    
                    # A值计算：完全相同=100%，差0.5=50%，其他=0%
                    a_diff = abs(user_a - standard_a)
                    if a_diff == 0:
                        a_score = 1.0  # 100%正确率
                    elif a_diff == 0.5:
                        a_score = 0.5  # 50%正确率
                    else:
                        a_score = 0.0  # 0%正确率
                    
                    total_v_score += v_score
                    total_a_score += a_score
                else:
                    v_score = 0
                    a_score = 0
                
                # 计算离散情感一致性
                user_discrete = result.get('discrete_emotion')
                standard_discrete = standard.get('discrete_emotion')
                standard_emotion_type = standard.get('emotion_type')
                
                # 处理标准答案中neutral类型的特殊情况
                # 如果标准答案的emotion_type是neutral但discrete_emotion是NULL，
                # 则将其视为neutral进行比较
                if (standard_emotion_type == 'neutral' and 
                    (standard_discrete is None or standard_discrete == '')):
                    standard_discrete = 'neutral'
                
                discrete_score = 1 if user_discrete == standard_discrete else 0
                total_discrete_score += discrete_score
                
                detailed_results.append({
                    'audio_file': audio_file,
                    'user_v': user_v,
                    'user_a': user_a,
                    'standard_v': standard_v,
                    'standard_a': standard_a,
                    'user_discrete': user_discrete,
                    'standard_discrete': standard_discrete,  # 这里已经是修正后的值
                    'standard_emotion_type': standard_emotion_type,  # 添加emotion_type用于调试
                    'v_score': v_score,
                    'a_score': a_score,
                    'discrete_score': discrete_score,
                    'v_consistent': v_score == 1.0,  # 添加布尔值字段
                    'a_consistent': a_score == 1.0,  # 添加布尔值字段
                    'discrete_consistent': discrete_score == 1  # 添加布尔值字段
                })
            
            if matched_samples == 0:
                return {
                    'total_samples': total_samples,
                    'matched_samples': 0,
                    'v_consistency': 0,
                    'a_consistency': 0,
                    'discrete_consistency': 0,
                    'overall_consistency': 0,
                    'detailed_results': []
                }
            
            # 计算平均一致性
            v_consistency = total_v_score / matched_samples
            a_consistency = total_a_score / matched_samples
            discrete_consistency = total_discrete_score / matched_samples
            overall_consistency = (v_consistency + a_consistency + discrete_consistency) / 3
            
            return {
                'total_samples': total_samples,
                'matched_samples': matched_samples,
                'v_consistency': round(v_consistency, 4),
                'a_consistency': round(a_consistency, 4),
                'discrete_consistency': round(discrete_consistency, 4),
                'overall_consistency': round(overall_consistency, 4),
                'detailed_results': detailed_results
            }
            
        except Exception as e:
            print(f"计算一致性时出错: {e}")
            return {
                'total_samples': 0,
                'matched_samples': 0,
                'v_consistency': 0,
                'a_consistency': 0,
                'discrete_consistency': 0,
                'overall_consistency': 0,
                'detailed_results': [],
                'error': str(e)
            }