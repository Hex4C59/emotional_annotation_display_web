#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排序服务
处理用户的说话人和音频文件排序逻辑
"""

import os
import json
import random
from datetime import datetime
from .database_service import DatabaseService

class OrderService:
    """排序服务类"""
    
    def __init__(self):
        """初始化排序服务"""
        self.db_service = DatabaseService()
    
    def get_user_speaker_order(self, username, speaker_groups):
        """
        获取用户专属的说话人排序
        简化版本：直接返回固定排序，不依赖数据库
        
        Args:
            username (str): 用户名
            speaker_groups (dict): 说话人分组字典
            
        Returns:
            list: 排序后的说话人列表
        """
        try:
            # 简化版本：使用固定的随机种子确保排序一致性
            speaker_group_list = list(speaker_groups.keys())
            
            # 使用固定的随机种子确保排序一致性
            random.seed(hash(f"{username}_speakers") % (2**32))
            random.shuffle(speaker_group_list)
            random.seed()  # 重置随机种子
            
            return speaker_group_list
            
        except Exception as e:
            print(f"获取用户说话人排序失败: {e}")
            # 降级处理：返回原始排序
            return list(speaker_groups.keys())
    
    def _save_user_speaker_order(self, username, speaker_order):
        """
        保存用户的说话人排序到数据库
        简化版本：不执行任何操作，不依赖数据库
        
        Args:
            username (str): 用户名
            speaker_order (list): 说话人排序列表
        """
        # 简化版本：不保存到数据库
        pass
    
    def get_user_audio_order(self, speaker, username, audio_files):
        """
        获取用户专属的音频文件排序
        简化版本：直接返回固定排序，不依赖数据库
        
        Args:
            speaker (str): 说话人
            username (str): 用户名
            audio_files (list): 音频文件列表
            
        Returns:
            list: 排序后的音频文件列表
        """
        try:
            # 简化版本：使用固定的随机种子确保排序一致性
            audio_files_copy = audio_files.copy()
            
            # 使用固定的随机种子确保排序一致性
            seed_string = f"{username}_{speaker}_audio"
            random.seed(hash(seed_string) % (2**32))
            random.shuffle(audio_files_copy)
            random.seed()  # 重置随机种子
            
            return audio_files_copy
            
        except Exception as e:
            print(f"获取用户音频排序失败: {e}")
            # 降级处理：返回原始排序
            return audio_files
    
    def _save_user_audio_order(self, username, speaker, audio_order):
        """
        保存用户的音频文件排序到数据库
        简化版本：不执行任何操作，不依赖数据库
        
        Args:
            username (str): 用户名
            speaker (str): 说话人
            audio_order (list): 音频文件排序列表
        """
        # 简化版本：不保存到数据库
        pass
    
    def delete_user_orders(self, username):
        """
        删除用户的所有排序数据
        简化版本：不执行任何操作，不依赖数据库
        
        Args:
            username (str): 用户名
        """
        # 简化版本：不操作数据库
        pass
    
    def get_user_order_statistics(self, username):
        """
        获取用户排序统计信息
        简化版本：返回固定值，不依赖数据库
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 统计信息
        """
        # 简化版本：返回固定统计信息
        return {
            'speaker_orders': 1,
            'audio_orders': 1
        }