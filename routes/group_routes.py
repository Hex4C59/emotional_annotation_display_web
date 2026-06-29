#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分组管理相关路由
"""

from flask import Blueprint, jsonify, request, session
from services.group_assignment_service import GroupAssignmentManager
from utils.logger import emotion_logger, get_client_ip


group_bp = Blueprint('group', __name__, url_prefix='/api/group')
group_manager = GroupAssignmentManager()

@group_bp.route('/user-assignment')
def get_user_assignment():
    """
    获取当前用户的分组分配信息
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        assignment_info = group_manager.get_user_assignment_info(username)
        
        if assignment_info:
            emotion_logger.log_user_activity(
                username=username,
                action="查看分组分配信息",
                details={"group_id": assignment_info['group_id']},
                ip_address=get_client_ip()
            )
            return jsonify({
                'success': True,
                'assignment': assignment_info
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户暂未分配分组'
            })
            
    except Exception as e:
        emotion_logger.log_error(e, "获取用户分组分配信息失败", username)
        return jsonify({'error': str(e)}), 500

@group_bp.route('/progress')
def get_user_progress():
    """
    获取用户标注进度
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        assignment_info = group_manager.get_user_assignment_info(username)
        
        if assignment_info:
            progress_percentage = 0
            if assignment_info['total_segments'] > 0:
                progress_percentage = (assignment_info['progress_count'] / assignment_info['total_segments']) * 100
            
            return jsonify({
                'success': True,
                'progress': {
                    'group_id': assignment_info['group_id'],
                    'progress_count': assignment_info['progress_count'],
                    'total_segments': assignment_info['total_segments'],
                    'progress_percentage': round(progress_percentage, 2),
                    'status': assignment_info['status']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户暂未分配分组'
            })
            
    except Exception as e:
        emotion_logger.log_error(e, "获取用户进度失败", username)
        return jsonify({'error': str(e)}), 500

@group_bp.route('/update-progress', methods=['POST'])
def update_progress():
    """
    更新用户标注进度
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        data = request.get_json()
        progress_count = data.get('progress_count', 0)
        
        assignment_info = group_manager.get_user_assignment_info(username)
        if not assignment_info:
            return jsonify({
                'success': False,
                'message': '用户暂未分配分组'
            }), 400
        
        group_id = assignment_info['group_id']
        success = group_manager.update_user_progress(username, group_id, progress_count)
        
        if success:
            emotion_logger.log_user_activity(
                username=username,
                action="更新标注进度",
                details={
                    "group_id": group_id,
                    "progress_count": progress_count,
                    "total_segments": assignment_info['total_segments']
                },
                ip_address=get_client_ip()
            )
            return jsonify({
                'success': True,
                'message': '进度更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '进度更新失败'
            }), 500
            
    except Exception as e:
        emotion_logger.log_error(e, "更新用户进度失败", username)
        return jsonify({'error': str(e)}), 500

@group_bp.route('/all-groups-status')
def get_all_groups_status():
    """
    获取所有分组状态（管理员功能）
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        # 这里可以添加管理员权限检查
        # if not is_admin(username):
        #     return jsonify({'error': '权限不足'}), 403
        
        groups_status = group_manager.get_all_groups_status()
        
        emotion_logger.log_user_activity(
            username=username,
            action="查看所有分组状态",
            details={"groups_count": len(groups_status)},
            ip_address=get_client_ip()
        )
        
        return jsonify({
            'success': True,
            'groups': groups_status
        })
        
    except Exception as e:
        emotion_logger.log_error(e, "获取分组状态失败", username)
        return jsonify({'error': str(e)}), 500

@group_bp.route('/group-info/<int:group_id>')
def get_group_info(group_id):
    """
    获取指定分组的详细信息
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        group_info = group_manager.get_group_info(group_id)
        
        if group_info:
            return jsonify({
                'success': True,
                'group_info': group_info
            })
        else:
            return jsonify({
                'success': False,
                'message': '分组不存在'
            }), 404
            
    except Exception as e:
        emotion_logger.log_error(e, f"获取分组{group_id}信息失败", username)
        return jsonify({'error': str(e)}), 500

@group_bp.route('/second-consistency-status', methods=['GET'])
def get_second_consistency_status():
    """
    获取当前用户的第二次一致性测试完成状态
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        assignment_info = group_manager.get_user_assignment_info(username)
        if not assignment_info:
            return jsonify({
                'success': False,
                'message': '用户暂未分配分组'
            }), 400
        
        group_id = assignment_info['group_id']
        status = group_manager.get_second_consistency_status(username, group_id)
        
        return jsonify({
            'success': True,
            'second_consistency_completed': status,
            'group_id': group_id
        })
        
    except Exception as e:
        emotion_logger.log_error(e, "获取第二次一致性测试状态失败", username)
        return jsonify({'error': str(e)}), 500

@group_bp.route('/second-consistency-status', methods=['POST'])
def update_second_consistency_status():
    """
    更新当前用户的第二次一致性测试完成状态
    """
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        data = request.get_json()
        completed = data.get('completed', True)
        
        assignment_info = group_manager.get_user_assignment_info(username)
        if not assignment_info:
            return jsonify({
                'success': False,
                'message': '用户暂未分配分组'
            }), 400
        
        group_id = assignment_info['group_id']
        success = group_manager.update_second_consistency_status(username, group_id, completed)
        
        if success:
            emotion_logger.log_user_activity(
                username=username,
                action="更新第二次一致性测试状态",
                details={
                    "group_id": group_id,
                    "completed": completed
                },
                ip_address=get_client_ip()
            )
            return jsonify({
                'success': True,
                'message': '第二次一致性测试状态更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '第二次一致性测试状态更新失败'
            }), 500
            
    except Exception as e:
        emotion_logger.log_error(e, "更新第二次一致性测试状态失败", username)
        return jsonify({'error': str(e)}), 500