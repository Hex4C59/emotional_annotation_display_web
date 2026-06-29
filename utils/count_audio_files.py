#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计音频文件数量脚本
用于统计 emotion_annotation 文件夹下所有音频文件的数量
"""

import os
import sys
import glob
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def count_audio_files_in_folder(folder_path, verbose=False):
    """
    统计指定文件夹下所有音频文件的数量
    
    Args:
        folder_path (str): 文件夹路径
        verbose (bool): 是否显示详细信息
        
    Returns:
        int: 音频文件总数
    """
    if not os.path.exists(folder_path):
        if verbose:
            print(f"警告: 文件夹 {folder_path} 不存在")
        return 0
    
    total_count = 0
    folder_stats = []
    
    # 遍历所有子文件夹
    for root, dirs, files in os.walk(folder_path):
        # 统计当前文件夹中的音频文件
        audio_files = glob.glob(os.path.join(root, "*.wav"))
        audio_files.extend(glob.glob(os.path.join(root, "*.mp3")))
        audio_files.extend(glob.glob(os.path.join(root, "*.flac")))
        audio_files.extend(glob.glob(os.path.join(root, "*.m4a")))
        
        folder_count = len(audio_files)
        total_count += folder_count
        
        if folder_count > 0:
            relative_path = os.path.relpath(root, folder_path)
            folder_stats.append((relative_path, folder_count))
    
    # 只在verbose模式下显示详细信息
    if verbose:
        for relative_path, count in folder_stats:
            print(f"文件夹 {relative_path}: {count} 个音频文件")
    
    return total_count

def update_audio_count_in_system(verbose=False):
    """
    更新系统中的音频文件总数统计
    这个函数可以在系统启动时调用，或者定期调用来更新统计信息
    
    Args:
        verbose (bool): 是否显示详细信息
    """
    try:
        # 统计 emotion_annotation 文件夹中的音频文件
        emotion_annotation_path = Config.AUDIO_FOLDER
        total_files = count_audio_files_in_folder(emotion_annotation_path, verbose=verbose)
        
        if verbose:
            print(f"\n=== 音频文件统计结果 ===")
            print(f"emotion_annotation 文件夹路径: {emotion_annotation_path}")
            print(f"音频文件总数: {total_files}")
        
        # 可以在这里添加将统计结果保存到数据库或配置文件的逻辑
        # 例如：保存到一个专门的统计表中
        
        return total_files
        
    except Exception as e:
        if verbose:
            print(f"统计音频文件时发生错误: {e}")
        return 0

def main():
    """
    主函数
    """
    print("开始统计音频文件数量...")
    
    # 统计并更新音频文件数量（详细模式）
    total_count = update_audio_count_in_system(verbose=True)
    
    print(f"\n统计完成，共找到 {total_count} 个音频文件")
    
    return total_count

if __name__ == "__main__":
    main()