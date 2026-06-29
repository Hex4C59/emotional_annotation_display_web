from flask import Blueprint, render_template, send_from_directory, request, session, jsonify
from utils.logger import emotion_logger, get_client_ip

main_bp = Blueprint('main', __name__)



@main_bp.route("/test-second-consistency")
def test_second_consistency():
    """测试第二次一致性测试页面"""
    return render_template("test_second_consistency.html")





@main_bp.route("/")
def index():
    """主页"""
    return render_template("index.html")

@main_bp.route("/main")
def main_page():
    """主页面"""
    return render_template("index.html")

@main_bp.route('/volume-test')
def volume_test_page():
    """音量测试页面"""
    return render_template('volume_test.html')

@main_bp.route('/volume-test-confirmation')
def volume_test_confirmation_page():
    """音量测试完成确认页面"""
    return render_template('volume_test_confirmation.html')

@main_bp.route('/test')
def test_page():
    """测试页面"""
    return render_template('test.html')

@main_bp.route('/5point')
def five_point_page():
    """5点量表页面"""
    return render_template("index.html")

@main_bp.route('/9point')
def nine_point_page():
    """9点量表页面"""
    return render_template("index_9point.html")