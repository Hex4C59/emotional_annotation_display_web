import os
import json
import shutil

def safe_json_load(file_path, default=None):
    """安全地加载JSON文件"""
    if not os.path.exists(file_path):
        return default or []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default or []

def safe_json_save(file_path, data):
    """安全地保存JSON文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def move_user_directory(old_path, new_path):
    """移动用户目录"""
    if os.path.exists(old_path):
        os.makedirs(new_path, exist_ok=True)
        for item in os.listdir(old_path):
            shutil.move(os.path.join(old_path, item), os.path.join(new_path, item))
        shutil.rmtree(old_path)
        return True
    return False