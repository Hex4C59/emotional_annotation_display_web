#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准答案管理路由
提供标准答案的增删改查API接口
"""

import os
import sys
from flask import Blueprint, request, jsonify

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.standard_answers_service import StandardAnswersService


# 创建蓝图
standard_answers_bp = Blueprint('standard_answers', __name__)

@standard_answers_bp.route('/api/standard-answers', methods=['GET'])
def get_all_standard_answers():
    """
    获取所有标准答案
    
    Returns:
        JSON响应，包含标准答案列表
    """
    try:
        standard_answers = StandardAnswersService.get_all_standard_answers()
        return jsonify({
            'success': True,
            'data': standard_answers,
            'count': len(standard_answers)
        })
    except Exception as e:
        if 'SQLite3 模块不可用' in str(e):
            return jsonify({
                'success': False,
                'error': 'SQLite3 模块不可用',
                'details': '数据库连接失败，无法访问一致性测试数据',
                'solution': '请联系系统管理员检查 SQLite3 模块安装'
            }), 500
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers/<audio_file>', methods=['GET'])
def get_standard_answer(audio_file):
    """
    获取指定音频文件的标准答案
    
    Args:
        audio_file (str): 音频文件名
        
    Returns:
        JSON响应，包含标准答案数据
    """
    try:
        standard_answer = StandardAnswersService.get_standard_answer(audio_file)
        if standard_answer:
            return jsonify({
                'success': True,
                'data': standard_answer
            })
        else:
            return jsonify({
                'success': False,
                'error': '未找到该音频文件的标准答案'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers', methods=['POST'])
def add_standard_answer():
    """
    添加新的标准答案
    
    Returns:
        JSON响应，表示操作结果
    """
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data or 'audio_file' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需的audio_file字段'
            }), 400
        
        # 添加创建者信息
        data['created_by'] = '管理员添加'
        
        success = StandardAnswersService.add_or_update_standard_answer(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '标准答案添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '添加标准答案失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers/<audio_file>', methods=['PUT'])
def update_standard_answer(audio_file):
    """
    更新标准答案
    
    Args:
        audio_file (str): 音频文件名
        
    Returns:
        JSON响应，表示操作结果
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        # 确保audio_file字段正确
        data['audio_file'] = audio_file
        data['created_by'] = '管理员更新'
        
        success = StandardAnswersService.add_or_update_standard_answer(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '标准答案更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '更新标准答案失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers/<audio_file>', methods=['DELETE'])
def delete_standard_answer(audio_file):
    """
    删除标准答案
    
    Args:
        audio_file (str): 音频文件名
        
    Returns:
        JSON响应，表示操作结果
    """
    try:
        success = StandardAnswersService.delete_standard_answer(audio_file)
        
        if success:
            return jsonify({
                'success': True,
                'message': '标准答案删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除标准答案失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers/statistics', methods=['GET'])
def get_standard_answers_statistics():
    """
    获取标准答案统计信息
    
    Returns:
        JSON响应，包含统计信息
    """
    try:
        stats = StandardAnswersService.get_statistics()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers/batch-import', methods=['POST'])
def batch_import_standard_answers():
    """
    批量导入标准答案
    
    Returns:
        JSON响应，表示导入结果
    """
    try:
        data = request.get_json()
        
        if not data or 'answers' not in data:
            return jsonify({
                'success': False,
                'error': '请求数据格式错误，需要answers字段'
            }), 400
        
        answers = data['answers']
        if not isinstance(answers, list):
            return jsonify({
                'success': False,
                'error': 'answers字段必须是数组'
            }), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        for answer in answers:
            if 'audio_file' not in answer:
                error_count += 1
                errors.append(f"缺少audio_file字段: {answer}")
                continue
            
            answer['created_by'] = '批量导入'
            success = StandardAnswersService.add_or_update_standard_answer(answer)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"导入失败: {answer['audio_file']}")
        
        return jsonify({
            'success': True,
            'message': f'批量导入完成，成功: {success_count}, 失败: {error_count}',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@standard_answers_bp.route('/api/standard-answers/consistency/<username>', methods=['GET'])
def calculate_user_consistency_with_standard(username):
    """
    计算指定用户与标准答案的一致性
    
    Args:
        username (str): 用户名
        
    Returns:
        JSON响应，包含一致性分析结果
    """
    try:
        import sqlite3
        from services.database_service import DatabaseService
        
        # 获取用户的一致性测试结果
        db_service = DatabaseService()
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT audio_file, v_value, a_value, emotion_type, discrete_emotion, patient_status
                FROM consistency_test_results 
                WHERE username = ?
            ''', (username,))
            
            user_results = cursor.fetchall()
        
        if not user_results:
            return jsonify({
                'success': False,
                'error': '该用户没有一致性测试数据'
            }), 404
        
        # 将用户结果转换为字典列表格式
        user_results_list = []
        for result in user_results:
            user_results_list.append({
                'audio_file': result[0],
                'v_value': result[1],
                'a_value': result[2],
                'emotion_type': result[3],
                'discrete_emotion': result[4],
                'patient_status': result[5]
            })
        
        # 使用标准答案服务计算一致性
        consistency_result = StandardAnswersService.calculate_consistency_with_standard(user_results_list)
        
        return jsonify({
            'success': True,
            'username': username,
            'consistency_analysis': consistency_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500