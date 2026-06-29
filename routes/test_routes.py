import os
import json
import random
import glob
from flask import Blueprint, jsonify, request, send_from_directory
from config import Config
from services.database_service import DatabaseService


# 测试音频文件夹配置从Config类获取
TEST_AUDIO_FOLDER = Config.TEST_AUDIO_FOLDER

test_bp = Blueprint('test', __name__)

@test_bp.route('/test')
def test_page():
    """测试页面"""
    from flask import render_template
    return render_template('test.html')

@test_bp.route('/api/test/questions')
def get_test_questions():
    """获取测试题目"""
    try:
        questions = []
        
        # 优先从数据库获取测试答案
        try:
            db_service = DatabaseService()
            with db_service.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT audio_file, v_value, a_value, emotion_type, discrete_emotion
                    FROM test_answers 
                    WHERE created_by = '测试答案导入'
                    ORDER BY audio_file
                """)
                
                db_answers = cursor.fetchall()
            
            if db_answers:
                print(f"从数据库获取到 {len(db_answers)} 个测试答案")
                
                for row in db_answers:
                    filename, v_value, a_value, emotion_type, discrete_emotion = row
                    
                    # 确定文件夹和正确答案
                    if emotion_type == 'discrete':
                        folder = 'discrete_emotions'
                        correct_answer = discrete_emotion
                        question_type = 'discrete'
                    elif emotion_type == 'potency':
                        folder = 'potency'
                        correct_answer = v_value
                        question_type = 'potency'
                    elif emotion_type == 'arousal':
                        folder = 'wake_up'
                        correct_answer = a_value
                        question_type = 'arousal'
                    else:
                        continue  # 跳过未知类型
                    
                    questions.append({
                        'filename': filename,
                        'type': question_type,
                        'correct_answer': correct_answer,
                        'folder': folder
                    })
                
                # 随机打乱题目顺序
                random.shuffle(questions)
                
                # 限制题目数量
                questions = questions[:Config.TEST_QUESTION_LIMIT]
                
                return jsonify({
                    'success': True,
                    'questions': questions,
                    'source': 'database'
                })
                
        except Exception as db_error:
            print(f"从数据库获取测试答案失败，回退到文件名解析: {db_error}")
        
        # 回退到原有的文件名解析方式
        print("使用文件名解析方式获取测试答案")
        test_examples_dir = os.path.abspath(TEST_AUDIO_FOLDER)
        
        # 处理离散情感测试题目
        discrete_dir = os.path.join(test_examples_dir, 'discrete_emotions')
        if os.path.exists(discrete_dir):
            for filename in os.listdir(discrete_dir):
                if filename.endswith('.wav') or filename.endswith('.MP3'):
                    # 从文件名提取正确答案 (例如: 愤怒-2.wav -> 愤怒)
                    correct_answer = filename.split('-')[0]
                    questions.append({
                        'filename': filename,
                        'type': 'discrete',
                        'correct_answer': correct_answer,
                        'folder': 'discrete_emotions'
                    })
        
        # 处理效价测试题目（V值标注）
        potency_dir = os.path.join(test_examples_dir, 'potency')
        if os.path.exists(potency_dir):
            for filename in os.listdir(potency_dir):
                if filename.endswith('.wav'):
                    # 从文件名提取正确答案 (例如: V0-2.wav -> V0, V负1-2.wav -> V负1)
                    label_part = filename.split('-')[0]
                    if label_part.startswith('V'):
                        # 处理V负数格式
                        if '负' in label_part:
                            v_value = -float(label_part.replace('V负', ''))  # V负1 -> -1
                        else:
                            v_value = float(label_part[1:])  # V0 -> 0, V1 -> 1, etc.
                        questions.append({
                            'filename': filename,
                            'type': 'potency',  # 专门的效价测试类型
                            'correct_answer': v_value,  # 只需要V值
                            'folder': 'potency'
                        })
        
        # 处理唤醒测试题目（A值标注）
        wake_up_dir = os.path.join(test_examples_dir, 'wake_up')
        if os.path.exists(wake_up_dir):
            for filename in os.listdir(wake_up_dir):
                if filename.endswith('.wav'):
                    # 从文件名提取正确答案 (例如: A2-1.wav -> A2)
                    label_part = filename.split('-')[0]
                    if label_part.startswith('A'):
                        a_value = float(label_part[1:])  # A2 -> 2, A1 -> 1, etc.
                        questions.append({
                            'filename': filename,
                            'type': 'arousal',  # 专门的唤醒测试类型
                            'correct_answer': a_value,  # 只需要A值
                            'folder': 'wake_up'
                        })
        
        # 随机打乱题目顺序
        random.shuffle(questions)
        
        # 限制题目数量
        questions = questions[:Config.TEST_QUESTION_LIMIT]
        
        return jsonify({
            'success': True,
            'questions': questions,
            'source': 'filename_parsing'
        })
        
    except Exception as e:
        print(f"获取测试题目失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@test_bp.route('/api/test/audio/<filename>')
def get_test_audio(filename):
    """获取测试音频文件"""
    try:
        test_examples_dir = os.path.abspath(TEST_AUDIO_FOLDER)
        
        # 在各个子目录中查找文件
        for subfolder in ['discrete_emotions', 'potency', 'wake_up']:
            file_path = os.path.join(test_examples_dir, subfolder, filename)
            if os.path.exists(file_path):
                return send_from_directory(os.path.dirname(file_path), filename)
            # 也尝试查找.MP3文件
            if filename.endswith('.wav'):
                mp3_filename = filename.replace('.wav', '.MP3')
                mp3_file_path = os.path.join(test_examples_dir, subfolder, mp3_filename)
                if os.path.exists(mp3_file_path):
                    return send_from_directory(os.path.dirname(mp3_file_path), mp3_filename)
        
        return jsonify({'error': '音频文件不存在'}), 404
        
    except Exception as e:
        print(f"获取测试音频失败: {e}")
        return jsonify({'error': str(e)}), 500

# 添加额外的测试相关功能
@test_bp.route('/api/test/submit', methods=['POST'])
def submit_test_result():
    """提交测试结果"""
    try:
        data = request.json
        username = data.get('username')
        test_results = data.get('results', [])
        
        if not username:
            return jsonify({'error': '缺少用户名'}), 400
        
        # 计算测试分数
        total_questions = len(test_results)
        correct_count = 0
        
        for result in test_results:
            user_answer = result.get('user_answer')
            correct_answer = result.get('correct_answer')
            question_type = result.get('type')
            
            if question_type == 'discrete':
                # 离散情感完全匹配
                if user_answer == correct_answer:
                    correct_count += 1
            elif question_type in ['potency', 'arousal']:
                # 连续值允许一定误差（例如±0.5）
                if abs(float(user_answer) - float(correct_answer)) <= 0.5:
                    correct_count += 1
        
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # 保存测试结果
        test_results_dir = os.path.join(Config.LABEL_FOLDER, 'test_results')
        os.makedirs(test_results_dir, exist_ok=True)
        
        result_file = os.path.join(test_results_dir, f"{username}_test_results.json")
        
        # 读取现有结果
        existing_results = []
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
            except json.JSONDecodeError:
                existing_results = []
        
        # 添加新结果
        from datetime import datetime
        new_result = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_questions': total_questions,
            'correct_count': correct_count,
            'score': round(score, 2),
            'details': test_results
        }
        existing_results.append(new_result)
        
        # 保存结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'score': round(score, 2),
            'correct_count': correct_count,
            'total_questions': total_questions
        })
        
    except Exception as e:
        print(f"提交测试结果失败: {e}")
        return jsonify({'error': str(e)}), 500

@test_bp.route('/api/test/history/<username>')
def get_test_history(username):
    """获取用户测试历史"""
    try:
        test_results_dir = os.path.join(Config.LABEL_FOLDER, 'test_results')
        result_file = os.path.join(test_results_dir, f"{username}_test_results.json")
        
        if not os.path.exists(result_file):
            return jsonify({
                'success': True,
                'history': []
            })
        
        with open(result_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 只返回摘要信息，不包含详细答案
        summary_history = []
        for result in history:
            summary_history.append({
                'timestamp': result.get('timestamp'),
                'score': result.get('score'),
                'correct_count': result.get('correct_count'),
                'total_questions': result.get('total_questions')
            })
        
        return jsonify({
            'success': True,
            'history': summary_history
        })
        
    except Exception as e:
        print(f"获取测试历史失败: {e}")
        return jsonify({'error': str(e)}), 500