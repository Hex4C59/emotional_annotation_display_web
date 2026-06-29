#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全配置检查脚本
用于检查系统的安全配置是否正确
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

from config import Config

def check_secret_key():
    """检查SECRET_KEY配置"""
    print("检查 SECRET_KEY 配置...")
    
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        print("❌ SECRET_KEY 环境变量未设置")
        print("   请设置 SECRET_KEY 环境变量")
        return False
    
    if len(secret_key) < 32:
        print(f"❌ SECRET_KEY 长度不足 (当前: {len(secret_key)}, 要求: 至少32)")
        print("   请使用更长的密钥")
        return False
    
    if secret_key == 'emotion_labeling_secret_key_2024':
        print("❌ SECRET_KEY 使用默认值")
        print("   请更改为随机生成的密钥")
        return False
    
    print("✅ SECRET_KEY 配置正确")
    return True

def check_flask_env():
    """检查Flask环境配置"""
    print("\n检查 Flask 环境配置...")
    
    flask_env = os.getenv('FLASK_ENV', 'development')
    flask_debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    if flask_env == 'production':
        if flask_debug:
            print("❌ 生产环境不应启用调试模式")
            print("   请设置 FLASK_DEBUG=False")
            return False
        print("✅ 生产环境配置正确")
    else:
        print(f"ℹ️  当前环境: {flask_env} (开发环境)")
        if flask_debug:
            print("⚠️  调试模式已启用 (仅开发环境使用)")
    
    return True

def check_file_permissions():
    """检查关键文件权限"""
    print("\n检查文件权限...")
    
    # 检查数据库文件权限
    db_folder = Config.DATABASE_FOLDER
    if os.path.exists(db_folder):
        for db_file in ['admins.db', 'users.db', 'emotion_labels.db']:
            db_path = os.path.join(db_folder, db_file)
            if os.path.exists(db_path):
                stat = os.stat(db_path)
                mode = oct(stat.st_mode)[-3:]
                if mode not in ['600', '640', '644']:
                    print(f"⚠️  {db_file} 权限可能过于宽松: {mode}")
                    print(f"   建议设置为 600: chmod 600 {db_path}")
                else:
                    print(f"✅ {db_file} 权限正确: {mode}")
    
    # 检查密码文件
    password_file = os.path.join(db_folder, 'initial_admin_password.txt')
    if os.path.exists(password_file):
        stat = os.stat(password_file)
        mode = oct(stat.st_mode)[-3:]
        if mode != '600':
            print(f"❌ 初始密码文件权限不安全: {mode}")
            print(f"   请设置为 600: chmod 600 {password_file}")
            return False
        else:
            print("⚠️  初始密码文件仍然存在")
            print("   建议登录后立即删除此文件")
    
    return True

def check_default_passwords():
    """检查是否存在默认密码"""
    print("\n检查默认密码...")
    
    # 检查代码中是否还有硬编码密码
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    dangerous_patterns = [
        'Admin@123456',
        'TempAdmin@123456',
        'admin.*123456',
        'password.*123456'
    ]
    
    found_issues = False
    
    # 简单的文件扫描
    current_script = os.path.abspath(__file__)
    for root, dirs, files in os.walk(project_root):
        # 跳过某些目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith(('.py', '.js', '.html', '.txt')):
                file_path = os.path.join(root, file)
                # 跳过安全检查脚本自身
                if os.path.abspath(file_path) == current_script:
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in dangerous_patterns:
                            if pattern.replace('.*', '') in content:
                                print(f"⚠️  在 {file_path} 中发现可能的硬编码密码")
                                found_issues = True
                                break
                except:
                    continue
    
    if not found_issues:
        print("✅ 未发现硬编码密码")
    
    return not found_issues

def generate_secure_key():
    """生成安全的SECRET_KEY"""
    import secrets
    return secrets.token_urlsafe(32)

def main():
    """主函数"""
    print("="*60)
    print("安全配置检查")
    print("="*60)
    
    checks = [
        check_secret_key,
        check_flask_env,
        check_file_permissions,
        check_default_passwords
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有安全检查通过！")
    else:
        print("❌ 发现安全问题，请根据上述提示进行修复")
        
        print("\n建议的修复步骤:")
        print("1. 设置强随机的 SECRET_KEY:")
        print(f"   export SECRET_KEY='{generate_secure_key()}'")
        print("2. 在生产环境中设置:")
        print("   export FLASK_ENV=production")
        print("   export FLASK_DEBUG=False")
        print("3. 检查并修复文件权限")
        print("4. 删除初始密码文件（登录后）")
    
    print("="*60)
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)