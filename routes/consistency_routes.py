import os
import json
import glob
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from config import Config
from services.database_service import DatabaseService

consistency_bp = Blueprint('consistency', __name__)

@consistency_bp.route('/consistency-test')
def consistency_test_page():
    """一致性测试页面"""
    return render_template('consistency_test.html')

@consistency_bp.route('/api/consistency/questions')
def get_consistency_questions():
    """获取一致性测试题目"""
    try:
        # 检查是否为第二次测试
        is_second_test = request.args.get('second_test', 'false').lower() == 'true'
        
        # 根据测试类型选择不同的数据目录
        if is_second_test:
            consistency_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/second_consistency_test'
        else:
            consistency_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/consistency_test'
        
        if not os.path.exists(consistency_dir):
            return jsonify({
                'success': False,
                'error': '一致性测试数据目录不存在'
            }), 404
        
        questions = []
        
        # 获取所有音频文件
        audio_files = glob.glob(os.path.join(consistency_dir, '*.wav'))
        
        for audio_file in audio_files:
            filename = os.path.basename(audio_file)
            # 移除扩展名获取基础文件名
            base_name = os.path.splitext(filename)[0]
            
            questions.append({
                'filename': filename,
                'base_name': base_name,
                'type': 'consistency'
            })
        
        # 按文件名排序
        questions.sort(key=lambda x: x['filename'])
        
        # 根据配置限制音频数量
        max_count = Config.CONSISTENCY_TEST_AUDIO_COUNT
        
        # 根据测试类型处理数据集
        if is_second_test:
            # 第二次测试使用所有second_consistency_test目录下的数据
            if len(questions) > max_count:
                questions = questions[:max_count]
        else:
            # 第一次测试使用前半部分数据
            if len(questions) > max_count:
                questions = questions[:max_count]
        
        return jsonify({
            'success': True,
            'questions': questions,
            'total_count': len(questions),
            'is_second_test': is_second_test
        })
        
    except Exception as e:
        print(f"获取一致性测试题目失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/audio/<filename>')
def get_consistency_audio(filename):
    """获取一致性测试音频文件"""
    try:
        # 检查是否为第二次测试
        is_second_test = request.args.get('second_test', 'false').lower() == 'true'
        
        # 根据测试类型选择不同的数据目录
        if is_second_test:
            consistency_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/second_consistency_test'
        else:
            consistency_dir = '/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/data/consistency_test'
        
        file_path = os.path.join(consistency_dir, filename)
        
        if os.path.exists(file_path):
            return send_from_directory(consistency_dir, filename)
        
        return jsonify({'error': '音频文件不存在'}), 404
        
    except Exception as e:
        print(f"获取一致性测试音频失败: {e}")
        return jsonify({'error': str(e)}), 500

@consistency_bp.route('/api/consistency/submit', methods=['POST'])
def submit_consistency_result():
    """提交一致性测试结果"""
    try:
        data = request.json
        username = data.get('username')
        results = data.get('results', [])
        is_second_test = data.get('is_second_test', False)
        
        if not username:
            return jsonify({'error': '缺少用户名'}), 400
        
        if not results:
            return jsonify({'error': '缺少测试结果'}), 400
        
        # 根据测试类型保存到不同的表
        if is_second_test:
            # 保存到第二次一致性测试专用表
            success = DatabaseService.save_second_consistency_test_results(username, results)
            if not success:
                return jsonify({
                    'success': False,
                    'error': '保存第二次一致性测试结果失败'
                }), 500
        else:
            # 保存到原有的一致性测试结果表
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建一致性测试结果表（如果不存在）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS consistency_test_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        audio_file TEXT NOT NULL,
                        v_value REAL,
                        a_value REAL,
                        emotion_type TEXT,
                        discrete_emotion TEXT,
                        patient_status TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(username, audio_file)
                    )
                ''')
                
                # 保存每个结果
                for result in results:
                    cursor.execute('''
                        INSERT OR REPLACE INTO consistency_test_results (
                            username, audio_file, v_value, a_value, emotion_type, 
                            discrete_emotion, patient_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        username,
                        result.get('filename'),
                        result.get('v_value'),
                        result.get('a_value'),
                        result.get('emotion_type'),
                        result.get('discrete_emotion'),
                        result.get('patient_status')
                    ))
                
                conn.commit()
        
        # 如果是第二次一致性测试，标记为已完成并计算一致性得分
        if is_second_test:
            from models.user_model import UserModel
            user_model = UserModel()
            user_model.mark_second_consistency_test_completed(username)
            
            # 计算一致性得分
            consistency_score = DatabaseService.calculate_second_consistency_score(username)
            
            return jsonify({
                'success': True,
                'message': f'成功保存 {len(results)} 条一致性测试结果',
                'consistency_score': consistency_score
            })
        
        return jsonify({
            'success': True,
            'message': f'成功保存 {len(results)} 条一致性测试结果'
        })
        
    except Exception as e:
        print(f"提交一致性测试结果失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/history/<username>')
def get_consistency_history(username):
    """获取用户的一致性测试历史"""
    try:
        # 检查是否为第二次测试
        is_second_test = request.args.get('second_test', 'false').lower() == 'true'
        
        if is_second_test:
            # 获取第二次一致性测试历史
            results = DatabaseService.get_second_consistency_test_results(username)
            history = []
            for result in results:
                history.append({
                    'audio_file': result['audio_file'],
                    'v_value': result['v_value'],
                    'a_value': result['a_value'],
                    'emotion_type': result['emotion_type'],
                    'discrete_emotion': result['discrete_emotion'],
                    'patient_status': result['patient_status'],
                    'timestamp': result['timestamp']
                })
        else:
            # 获取第一次一致性测试历史
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM consistency_test_results 
                    WHERE username = ? 
                    ORDER BY timestamp DESC
                ''', (username,))
                
                results = cursor.fetchall()
            
            history = []
            for row in results:
                history.append({
                    'id': row['id'],
                    'audio_file': row['audio_file'],
                    'v_value': row['v_value'],
                    'a_value': row['a_value'],
                    'emotion_type': row['emotion_type'],
                    'discrete_emotion': row['discrete_emotion'],
                    'patient_status': row['patient_status'],
                    'timestamp': row['timestamp']
                })
        
        return jsonify({
            'success': True,
            'history': history,
            'is_second_test': is_second_test
        })
        
    except Exception as e:
        print(f"获取一致性测试历史失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/second-test-score/<username>')
def get_second_consistency_score(username):
    """获取用户第二次一致性测试得分"""
    try:
        consistency_score = DatabaseService.calculate_second_consistency_score(username)
        
        return jsonify({
            'success': True,
            'score': consistency_score
        })
        
    except Exception as e:
        print(f"获取第二次一致性测试得分失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@consistency_bp.route('/api/consistency/import-second-test-answers', methods=['POST'])
def import_second_test_answers():
    """导入第二次一致性测试标准答案"""
    try:
        success = DatabaseService.import_second_consistency_standard_answers()
        
        if success:
            return jsonify({
                'success': True,
                'message': '第二次一致性测试标准答案导入成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '导入失败'
            }), 500
            
    except Exception as e:
        print(f"导入第二次一致性测试标准答案失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500