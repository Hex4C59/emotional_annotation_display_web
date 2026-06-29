import os
import re
import os
from flask import Blueprint, jsonify, request, session, send_from_directory
from services.audio_service import AudioService
from services.label_service import LabelService
from services.database_service import DatabaseService

from utils.logger import emotion_logger, log_api_call, get_client_ip
import traceback

api_bp = Blueprint('api', __name__, url_prefix='/api')

# 创建服务实例
label_service = LabelService()

@api_bp.route("/speakers")
@log_api_call
def get_speakers():
    """获取所有说话人列表"""
    try:
        speakers = AudioService.get_speakers_list('default')
        
        emotion_logger.log_user_activity(
            username='system',
            action="获取说话人列表",
            details={"speaker_count": len(speakers)},
            ip_address=get_client_ip()
        )
        
        return jsonify(speakers)
    except Exception as e:
        emotion_logger.log_error(e, "获取说话人列表失败", 'system')
        return jsonify({"error": str(e)}), 500



@api_bp.route("/audio_list/<speaker>")
@log_api_call
def get_audio_list(speaker):
    """获取指定说话人的音频文件列表"""
    try:
        va_scale = request.args.get('va_scale', '5_point')
        audio_files = AudioService.get_audio_files_list(speaker, '')
        labeled_files, annotation_completeness = label_service.get_labeled_files('system', speaker, va_scale)
        
        result = []
        for audio_file in audio_files:
            file_name = os.path.basename(audio_file)
            result.append({
                "file_name": file_name,
                "path": f"/api/audio/{speaker}/{file_name}",
                "labeled": file_name in labeled_files,
                "annotation_completeness": annotation_completeness.get(file_name, ['none']),
            })
        
        emotion_logger.log_user_activity(
            username='system',
            action="获取音频列表",
            details={"speaker": speaker, "audio_count": len(result)},
            ip_address=get_client_ip()
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/all_audio_list")
@log_api_call
def get_all_audio_list():
    """获取所有音频文件列表（不按说话人分组）"""
    try:
        va_scale = request.args.get('va_scale', '5_point')
        
        # 获取所有说话人
        speakers = AudioService.get_speakers_list('default')
        
        all_audio_files = []
        for speaker in speakers:
            audio_files = AudioService.get_audio_files_list(speaker, '')
            labeled_files, annotation_completeness = label_service.get_labeled_files('system', speaker, va_scale)
            
            for audio_file in audio_files:
                file_name = os.path.basename(audio_file)
                all_audio_files.append({
                    "file_name": file_name,
                    "speaker": speaker,
                    "path": f"/api/audio/{speaker}/{file_name}",
                    "labeled": file_name in labeled_files,
                    "annotation_completeness": annotation_completeness.get(file_name, ['none']),
                })
        
        emotion_logger.log_user_activity(
            username='system',
            action="获取所有音频列表",
            details={"total_audio_count": len(all_audio_files)},
            ip_address=get_client_ip()
        )
        
        return jsonify(all_audio_files)
    except Exception as e:
        emotion_logger.log_error(e, "获取所有音频列表失败", 'system')
        return jsonify({"error": str(e)}), 500





@api_bp.route("/audio/<speaker>/<filename>")
@log_api_call
def get_audio(speaker, filename):
    """提供音频文件下载"""
    try:
        username = session.get('username', 'anonymous')
        file_path, actual_speaker = AudioService.find_audio_file(speaker, filename)
        if file_path:
            directory = os.path.dirname(file_path)
            
            emotion_logger.log_user_activity(
                username=username,
                action="获取音频文件",
                details={"speaker": speaker, "audio_file": filename},
                ip_address=get_client_ip()
            )
            
            # 明确设置WAV文件的MIME类型
            return send_from_directory(directory, filename, mimetype='audio/wav')
        else:
            emotion_logger.log_error(f"找不到音频文件 {filename}", "获取音频文件", username)
            return jsonify({"error": f"找不到音频文件 {filename}"}), 404
    except Exception as e:
        emotion_logger.log_error(e, f"获取音频文件失败 - speaker: {speaker}, file: {filename}", session.get('username'))
        return jsonify({"error": str(e)}), 500

@api_bp.route("/save_label", methods=["POST"])
@log_api_call
def save_label():
    """保存情感标注结果（优化版本）"""
    username = None  # 初始化username变量
    try:
        # 检查请求内容类型
        if not request.is_json:
            return jsonify({"error": "请求必须是JSON格式"}), 400
        
        # 安全地获取JSON数据
        try:
            data = request.get_json(silent=True)
        except Exception as json_error:
            return jsonify({"error": "JSON数据解析失败"}), 400
        
        if not data or not isinstance(data, dict):
            return jsonify({"error": "请求数据为空或格式错误"}), 400
            
        speaker = data.get("speaker")
        audio_file = data.get("audio_file")
        username = data.get("username")
        
        if not all([speaker, audio_file, username]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 查找音频文件
        file_path, actual_speaker = AudioService.find_audio_file(speaker, audio_file)
        if not file_path:
            return jsonify({"error": f"找不到音频文件 {audio_file}"}), 404
        
        # 保存标注
        #2025年9月8日 保存标注到数据库，todo:改为本地临时保存
        success = label_service.save_label(data, actual_speaker, file_path)
        if success:
            # 优化：减少日志记录，只在出错时记录详细信息
            return jsonify({"success": True})
        else:
            return jsonify({"error": "保存失败"}), 500
            
    except Exception as e:
        # 确保username变量已定义，如果未定义则使用默认值
        if username is None:
            username = session.get('username', 'unknown')
        # 只在出错时记录详细日志
        emotion_logger.log_error(e, "保存标注失败", username, traceback.format_exc())
        return jsonify({"error": str(e)}), 500





# 添加播放计数相关的API端点
@api_bp.route("/save_play_count", methods=["POST"])
@log_api_call
def save_play_count():
    """保存音频播放计数"""
    username = None  # 初始化username变量
    try:
        # 安全地获取JSON数据
        try:
            data = request.get_json(silent=True)
        except Exception as json_error:
            emotion_logger.log_error(f"JSON解析失败: {json_error}", "保存播放次数", None)
            return jsonify({"error": "JSON数据解析失败"}), 400
        
        if not data or not isinstance(data, dict):
            emotion_logger.log_error("请求数据为空或格式错误", "保存播放次数", None)
            return jsonify({"error": "请求数据为空或格式错误"}), 400
        
        username = data.get("username")
        speaker = data.get("speaker") 
        audio_file = data.get("audio_file")
        va_scale = data.get("va_scale", "5_point")
        
        if not all([username, speaker, audio_file]):
            emotion_logger.log_error("缺少必要参数", "保存播放次数", username)
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 使用标签服务保存播放次数
        play_count = label_service.save_play_count(username, speaker, audio_file, va_scale)
        
        emotion_logger.log_user_activity(
            username=username,
            action="更新播放次数",
            details={
                "speaker": speaker,
                "audio_file": audio_file,
                "play_count": play_count,
                "va_scale": va_scale
            },
            ip_address=get_client_ip()
        )
        
        return jsonify({
            "success": True,
            "play_count": play_count
        })
        
    except Exception as e:
        # 确保username变量已定义，如果未定义则使用默认值
        if username is None:
            username = session.get('username', 'unknown')
        emotion_logger.log_error(e, "保存播放次数失败", username)
        return jsonify({"error": str(e)}), 500













@api_bp.route('/config/rest-reminder-interval', methods=['GET'])
def get_rest_reminder_interval():
    """获取休息提醒间隔配置"""
    try:
        from config import Config
        return jsonify({
            'success': True,
            'interval_minutes': Config.REST_REMINDER_INTERVAL
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500

@api_bp.route('/config/test-pass-threshold', methods=['GET'])
def get_test_pass_threshold():
    """获取测试通过阈值配置"""
    try:
        from config import Config
        return jsonify({
            'success': True,
            'threshold': Config.TEST_PASS_THRESHOLD
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500

@api_bp.route('/config/scale-switch-button-min-annotations', methods=['GET'])
def get_scale_switch_button_min_annotations():
    """获取切换量表按钮显示所需的最小标注数量配置"""
    try:
        from config import Config
        return jsonify({
            'success': True,
            'min_annotations': Config.SCALE_SWITCH_BUTTON_MIN_ANNOTATIONS
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500

@api_bp.route('/standard_answer/<audio_file>', methods=['GET'])
@log_api_call
def get_standard_answer(audio_file):
    """获取指定音频文件的标准答案"""
    try:
        db_service = DatabaseService()
        answer = db_service.get_standard_answer(audio_file)
        
        if answer:
            emotion_logger.log_user_activity(
                username='system',
                action="获取标准答案",
                details={"audio_file": audio_file},
                ip_address=get_client_ip()
            )
            return jsonify({
                'success': True,
                'answer': answer
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No standard answer found for this audio file'
            }), 404
            
    except Exception as e:
        emotion_logger.log_error(e, f"获取标准答案失败 - audio_file: {audio_file}", 'system')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500