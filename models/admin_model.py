#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员数据模型
提供管理员用户的数据库操作功能，支持超级管理员和普通管理员的分层管理
"""

import os
import sys
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import Config
from utils.logger import emotion_logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.unified_db_manager import unified_db_manager

class AdminModel:
    """管理员数据模型类"""
    
    # 管理员角色常量
    ROLE_SUPER_ADMIN = 'super_admin'  # 超级管理员
    ROLE_ADMIN = 'admin'              # 普通管理员
    
    def __init__(self):
        """
        初始化管理员模型
        """
        # 使用统一数据库管理器
        self.db_manager = unified_db_manager
        self.init_database()
    
    def init_database(self):
        """
        初始化管理员数据库（已由统一数据库管理器处理）
        """
        try:
            # 数据库表创建已由统一数据库管理器处理
            # 这里只需要确保超级管理员存在
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否存在超级管理员，如果不存在则创建默认的
                self._ensure_super_admin_exists(cursor)
                
                conn.commit()
            
            emotion_logger.log_system_event("管理员数据库初始化完成")
            
        except Exception as e:
            emotion_logger.log_error(e, "管理员数据库初始化失败")
            raise
    
    def _ensure_super_admin_exists(self, cursor):
        """
        确保存在至少一个超级管理员
        
        Args:
            cursor: 数据库游标
        """
        cursor.execute('SELECT COUNT(*) FROM admins WHERE role = ?', (self.ROLE_SUPER_ADMIN,))
        super_admin_count = cursor.fetchone()[0]
        
        if super_admin_count == 0:
            # 创建默认超级管理员，使用随机生成的强密码
            default_password = self._generate_secure_password()
            password_hash, salt = self._hash_password(default_password)
            
            cursor.execute('''
                INSERT INTO admins (username, password_hash, salt, role, description, force_password_change)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'admin',
                password_hash,
                salt,
                self.ROLE_SUPER_ADMIN,
                '系统默认超级管理员',
                True  # 强制首次登录修改密码
            ))
            
            # 将密码写入安全文件
            self._save_initial_password('admin', default_password)
            
            emotion_logger.log_system_event(
                "创建默认超级管理员",
                {"username": "admin", "role": self.ROLE_SUPER_ADMIN, "password_saved_to_file": True}
            )
    
    def _generate_salt(self) -> str:
        """
        生成随机盐值
        
        Returns:
            str: 随机盐值
        """
        return secrets.token_hex(32)
    
    def _generate_secure_password(self) -> str:
        """
        生成符合复杂度要求的安全密码
        
        Returns:
            str: 安全密码
        """
        import string
        import random
        
        # 确保密码包含所有必需的字符类型
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        special = random.choice(Config.ADMIN_PASSWORD_SPECIAL_CHARS)
        
        # 生成剩余字符
        all_chars = string.ascii_letters + string.digits + Config.ADMIN_PASSWORD_SPECIAL_CHARS
        remaining_length = max(12, Config.ADMIN_PASSWORD_MIN_LENGTH) - 4
        remaining = ''.join(random.choice(all_chars) for _ in range(remaining_length))
        
        # 组合并打乱
        password_chars = list(uppercase + lowercase + digit + special + remaining)
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    def _save_initial_password(self, username: str, password: str):
        """
        将初始密码保存到安全文件
        
        Args:
            username (str): 用户名
            password (str): 密码
        """
        try:
            password_file = os.path.join(Config.DATABASE_FOLDER, 'initial_admin_password.txt')
            with open(password_file, 'w', encoding='utf-8') as f:
                f.write(f"初始管理员账户信息\n")
                f.write(f"创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"用户名: {username}\n")
                f.write(f"初始密码: {password}\n")
                f.write(f"\n重要提醒:\n")
                f.write(f"1. 请立即登录并修改密码\n")
                f.write(f"2. 修改密码后请删除此文件\n")
                f.write(f"3. 此密码仅在首次登录时有效\n")
            
            # 设置文件权限为仅所有者可读写
            os.chmod(password_file, 0o600)
            
            print(f"\n⚠️  重要提醒: 初始管理员密码已保存到文件: {password_file}")
            print(f"   请立即查看该文件获取密码，登录后修改密码并删除该文件！")
            
        except Exception as e:
            emotion_logger.log_error(e, "保存初始密码失败")
            print(f"\n❌ 保存初始密码失败: {e}")
            print(f"   初始密码: {password}")
            print(f"   请记录此密码并立即登录修改！")
    
    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """
        对密码进行哈希加密（使用PBKDF2算法）
        
        Args:
            password (str): 原始密码
            salt (str): 盐值，如果为None则生成新的
            
        Returns:
            tuple[str, str]: (密码哈希, 盐值)
        """
        if salt is None:
            salt = self._generate_salt()
        
        # 使用PBKDF2算法，迭代100000次
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    def verify_admin(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证管理员登录信息
        
        Args:
            username (str): 用户名
            password (str): 密码
            
        Returns:
            Optional[Dict]: 验证成功返回管理员信息，失败返回None
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 首先检查用户是否存在且活跃
                cursor.execute('''
                    SELECT id, username, password_hash, salt, role, created_by, created_at, last_login, description,
                           failed_login_attempts, locked_until, force_password_change
                    FROM admins 
                    WHERE username = ? AND is_active = 1
                ''', (username,))
                
                admin = cursor.fetchone()
                 
                if not admin:
                    emotion_logger.log_user_activity(
                        username=username,
                        action="管理员登录失败",
                        details={"reason": "用户不存在或已禁用"}
                    )
                    return None
                 
                admin_id, admin_username, stored_hash, salt, role, created_by, created_at, last_login, description, failed_attempts, locked_until, force_change = admin
                 
                 # 检查账户是否被锁定
                if locked_until:
                    locked_until_dt = datetime.fromisoformat(locked_until)
                    if datetime.now() < locked_until_dt:
                        remaining_time = int((locked_until_dt - datetime.now()).total_seconds())
                        emotion_logger.log_user_activity(
                            username=username,
                            action="管理员登录失败",
                            details={"reason": f"账户已锁定，剩余时间{remaining_time}秒"}
                        )
                        return None
                    else:
                         # 锁定时间已过，重置失败次数和锁定状态
                        cursor.execute(
                            'UPDATE admins SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?',
                            (admin_id,)
                        )
                        conn.commit()
                 
                # 验证密码
                password_hash, _ = self._hash_password(password, salt)
                 
                if password_hash == stored_hash:
                     # 密码正确，重置失败次数，更新最后登录时间
                    cursor.execute('''
                        UPDATE admins SET 
                            last_login = ?, 
                            failed_login_attempts = 0, 
                            locked_until = NULL 
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), admin_id))
                    conn.commit()
                     
                    admin_info = {
                        'id': admin_id,
                        'username': admin_username,
                        'role': role,
                        'created_by': created_by,
                        'created_at': created_at,
                        'last_login': last_login,
                        'description': description,
                        'force_password_change': bool(force_change)
                    }
                     
                    emotion_logger.log_user_activity(
                        username=username,
                        action="管理员登录成功",
                        details={"role": role}
                    )
                     
                    return admin_info
                else:
                    # 密码错误，增加失败次数
                    new_failed_attempts = failed_attempts + 1
                     
                    if new_failed_attempts >= Config.ADMIN_PASSWORD_MAX_ATTEMPTS:
                        # 达到最大失败次数，锁定账户
                        locked_until = (datetime.now() + timedelta(seconds=Config.ADMIN_PASSWORD_LOCKOUT_TIME)).isoformat()
                        cursor.execute(
                            'UPDATE admins SET failed_login_attempts = ?, locked_until = ? WHERE id = ?',
                            (new_failed_attempts, locked_until, admin_id)
                        )
                        emotion_logger.log_user_activity(
                            username=username,
                            action="管理员账户被锁定",
                            details={"reason": f"连续{new_failed_attempts}次登录失败"}
                        )
                    else:
                        # 更新失败次数
                        cursor.execute(
                            'UPDATE admins SET failed_login_attempts = ? WHERE id = ?',
                            (new_failed_attempts, admin_id)
                        )
                     
                    conn.commit()
                     
                    emotion_logger.log_user_activity(
                        username=username,
                        action="管理员登录失败",
                        details={"reason": "密码错误", "failed_attempts": new_failed_attempts}
                    )
                     
                    return None
                
        except Exception as e:
            emotion_logger.log_error(e, "管理员验证失败", username)
            return None
    
    def get_admin(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取管理员信息
        
        Args:
            username (str): 用户名
            
        Returns:
            Optional[Dict]: 管理员信息，不存在返回None
        """
        return self.db_manager.get_admin(username)
    
    def create_admin(self, username: str, password: str, role: str, created_by: str, description: str = None) -> bool:
        """
        创建新管理员
        
        Args:
            username (str): 用户名
            password (str): 密码
            role (str): 角色 (admin 或 super_admin)
            created_by (str): 创建者用户名
            description (str): 描述信息
            
        Returns:
            bool: 创建成功返回True，失败返回False
        """
        try:
            # 验证密码复杂度
            is_valid, error_message = Config.validate_admin_password(password)
            if not is_valid:
                emotion_logger.log_error(f"密码不符合要求: {error_message}", "创建管理员", created_by)
                return False
            
            # 验证角色
            if role not in [self.ROLE_ADMIN, self.ROLE_SUPER_ADMIN]:
                emotion_logger.log_error(f"无效的管理员角色: {role}", "创建管理员", created_by)
                return False
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查用户名是否已存在
                cursor.execute('SELECT COUNT(*) FROM admins WHERE username = ?', (username,))
                if cursor.fetchone()[0] > 0:
                    emotion_logger.log_error(f"管理员用户名已存在: {username}", "创建管理员", created_by)
                    return False
                
                password_hash, salt = self._hash_password(password)
                
                cursor.execute('''
                    INSERT INTO admins (username, password_hash, salt, role, created_by, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, password_hash, salt, role, created_by, description))
                
                conn.commit()
            
            emotion_logger.log_user_activity(
                username=created_by,
                action="创建管理员",
                details={
                    "new_admin_username": username,
                    "new_admin_role": role,
                    "description": description
                }
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_error(e, "创建管理员失败", created_by)
            return False
    
    def get_all_admins(self) -> List[Dict[str, Any]]:
        """
        获取所有管理员列表
        
        Returns:
            List[Dict]: 管理员信息列表
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, role, created_by, created_at, last_login, is_active, description
                    FROM admins 
                    ORDER BY created_at DESC
                ''')
                
                admins = cursor.fetchall()
            
            return [{
                'id': admin[0],
                'username': admin[1],
                'role': admin[2],
                'created_by': admin[3],
                'created_at': admin[4],
                'last_login': admin[5],
                'is_active': bool(admin[6]),
                'description': admin[7]
            } for admin in admins]
            
        except Exception as e:
            emotion_logger.log_error(e, "获取管理员列表失败")
            return []
    
    def update_admin_status(self, admin_id: int, is_active: bool, operator: str) -> bool:
        """
        更新管理员状态（启用/禁用）
        
        Args:
            admin_id (int): 管理员ID
            is_active (bool): 是否启用
            operator (str): 操作者用户名
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取管理员信息
                cursor.execute('SELECT username, role FROM admins WHERE id = ?', (admin_id,))
                admin_info = cursor.fetchone()
                
                if not admin_info:
                    emotion_logger.log_error(f"管理员不存在: ID {admin_id}", "更新管理员状态", operator)
                    return False
                
                # 不能禁用超级管理员
                if admin_info[1] == self.ROLE_SUPER_ADMIN and not is_active:
                    emotion_logger.log_error("不能禁用超级管理员", "更新管理员状态", operator)
                    return False
                
                cursor.execute(
                    'UPDATE admins SET is_active = ? WHERE id = ?',
                    (is_active, admin_id)
                )
                
                conn.commit()
            
            emotion_logger.log_user_activity(
                username=operator,
                action="更新管理员状态",
                details={
                    "target_admin": admin_info[0],
                    "new_status": "启用" if is_active else "禁用"
                }
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_error(e, "更新管理员状态失败", operator)
            return False
    
    def delete_admin(self, admin_id: int, operator: str) -> bool:
        """
        删除管理员
        
        Args:
            admin_id (int): 管理员ID
            operator (str): 操作者用户名
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取管理员信息
                cursor.execute('SELECT username, role FROM admins WHERE id = ?', (admin_id,))
                admin_info = cursor.fetchone()
                
                if not admin_info:
                    emotion_logger.log_error(f"管理员不存在: ID {admin_id}", "删除管理员", operator)
                    return False
                
                # 不能删除超级管理员
                if admin_info[1] == self.ROLE_SUPER_ADMIN:
                    emotion_logger.log_error("不能删除超级管理员", "删除管理员", operator)
                    return False
                
                cursor.execute('DELETE FROM admins WHERE id = ?', (admin_id,))
                
                conn.commit()
            
            emotion_logger.log_user_activity(
                username=operator,
                action="删除管理员",
                details={"deleted_admin": admin_info[0]}
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_error(e, "删除管理员失败", operator)
            return False
    
    def change_password(self, admin_id: int, new_password: str, operator: str) -> bool:
        """
        修改管理员密码
        
        Args:
            admin_id (int): 管理员ID
            new_password (str): 新密码
            operator (str): 操作者用户名
            
        Returns:
            bool: 修改成功返回True，失败返回False
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取管理员信息
                cursor.execute('SELECT username FROM admins WHERE id = ?', (admin_id,))
                admin_info = cursor.fetchone()
                
                if not admin_info:
                    emotion_logger.log_error(f"管理员不存在: ID {admin_id}", "修改密码", operator)
                    return False
                
                # 验证密码复杂度
                is_valid, error_message = Config.validate_admin_password(new_password)
                if not is_valid:
                    emotion_logger.log_error(f"密码不符合要求: {error_message}", "修改密码", operator)
                    return False
                
                password_hash, salt = self._hash_password(new_password)
                
                cursor.execute(
                    'UPDATE admins SET password_hash = ?, salt = ?, password_changed_at = ?, force_password_change = ? WHERE id = ?',
                    (password_hash, salt, datetime.now().isoformat(), False, admin_id)
                )
                
                conn.commit()
            
            emotion_logger.log_user_activity(
                username=operator,
                action="修改管理员密码",
                details={"target_admin": admin_info[0]}
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_error(e, "修改管理员密码失败", operator)
            return False
    
    def change_password_by_username(self, username: str, new_password: str, operator: str = None) -> bool:
        """
        根据用户名修改管理员密码
        
        Args:
            username (str): 管理员用户名
            new_password (str): 新密码
            operator (str): 操作者用户名，默认为当前用户
            
        Returns:
            bool: 修改成功返回True，失败返回False
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取管理员信息
                cursor.execute('SELECT id, username FROM admins WHERE username = ? AND is_active = 1', (username,))
                admin_info = cursor.fetchone()
                
                if not admin_info:
                    emotion_logger.log_error(f"管理员不存在或已禁用: {username}", "修改密码", operator or username)
                    return False
                
                admin_id = admin_info[0]
                
                # 验证密码复杂度
                is_valid, error_message = Config.validate_admin_password(new_password)
                if not is_valid:
                    emotion_logger.log_error(f"密码不符合要求: {error_message}", "修改密码", operator or username)
                    return False
                
                password_hash, salt = self._hash_password(new_password)
                
                cursor.execute(
                    'UPDATE admins SET password_hash = ?, salt = ?, password_changed_at = ?, force_password_change = ? WHERE id = ?',
                    (password_hash, salt, datetime.now().isoformat(), False, admin_id)
                )
                
                conn.commit()
            
            emotion_logger.log_user_activity(
                username=operator or username,
                action="修改管理员密码",
                details={"target_admin": username}
            )
            
            return True
            
        except Exception as e:
            emotion_logger.log_error(e, "修改管理员密码失败", operator or username)
            return False
    
    def is_super_admin(self, username: str) -> bool:
        """
        检查用户是否为超级管理员
        
        Args:
            username (str): 用户名
            
        Returns:
            bool: 是超级管理员返回True，否则返回False
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT role FROM admins WHERE username = ? AND is_active = 1',
                    (username,)
                )
                
                result = cursor.fetchone()
                
                return result and result[0] == self.ROLE_SUPER_ADMIN
                
        except Exception as e:
            emotion_logger.log_error(e, "检查超级管理员权限失败", username)
            return False