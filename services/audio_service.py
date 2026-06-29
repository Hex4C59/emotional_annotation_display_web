# services/audio_service.py
import os
import glob
import re
import random
from config import Config
from services.order_service import OrderService
from .group_assignment_service import GroupAssignmentManager

class AudioService:
    """音频文件相关服务"""
    
    @staticmethod
    def get_speakers_list(username="default"):
        """获取说话人列表（直接返回所有可用说话人，不进行分组过滤）"""
        print(f"DEBUG: Config.AUDIO_FOLDER = {Config.AUDIO_FOLDER}")
        if not os.path.exists(Config.AUDIO_FOLDER):
            raise FileNotFoundError(f"音频文件夹不存在: {Config.AUDIO_FOLDER}")

        # 检查是否是文件夹结构（如emotion_annotation）还是文件结构（如gzx_data）
        all_items = os.listdir(Config.AUDIO_FOLDER)
        
        # 如果有子文件夹，使用原来的逻辑
        all_speakers = [d for d in all_items if os.path.isdir(os.path.join(Config.AUDIO_FOLDER, d))]
        
        if all_speakers:
            # 按spk编号分组，包含所有说话人
            speaker_groups = {}
            for speaker in all_speakers:
                match = re.match(r'(spk)(\d+)-(\d+)-(\d+)', speaker)
                if match:
                    prefix, spk_id, part, section = match.groups()
                    spk_group = f"spk{spk_id}"
                    if spk_group not in speaker_groups:
                        speaker_groups[spk_group] = []
                    speaker_groups[spk_group].append(speaker)
                else:
                    # 直接匹配的说话人
                    speaker_groups[speaker] = [speaker]
        else:
            # 如果没有子文件夹，从音频文件名中提取说话人信息
            audio_files = [f for f in all_items if f.endswith('.wav')]
            speaker_groups = {}
            
            for audio_file in audio_files:
                # 从文件名中提取说话人信息，格式如：spk16-2-1-108.wav
                match = re.match(r'(spk)(\d+)-(\d+)-(\d+)-', audio_file)
                if match:
                    prefix, spk_id, part, section = match.groups()
                    spk_group = f"spk{spk_id}"
                    if spk_group not in speaker_groups:
                        speaker_groups[spk_group] = [spk_group]
        
        # 获取或创建用户专属排序
        return AudioService._get_user_speaker_order(username, speaker_groups)
    
    @staticmethod
    def _get_user_speaker_order(username, speaker_groups):
        """获取用户专属的说话人排序"""
        order_service = OrderService()
        return order_service.get_user_speaker_order(username, speaker_groups)
    
    @staticmethod
    def get_audio_files_list(speaker, username=""):
        """获取指定说话人的音频文件列表"""
        # 检查是否是简单的spk格式（如spk1），如果audio文件夹下有对应的子文件夹，就直接使用单说话人方式
        all_items = os.listdir(Config.AUDIO_FOLDER)
        has_subdirs = any(os.path.isdir(os.path.join(Config.AUDIO_FOLDER, item)) for item in all_items)
        
        if has_subdirs and speaker in all_items:
            # 如果有子文件夹且存在对应的说话人文件夹，使用单说话人方式
            audio_files = AudioService._get_single_speaker_files(speaker)
        elif re.match(r'spk\d+$', speaker):
            # 否则尝试分组说话人方式
            audio_files = AudioService._get_grouped_speaker_files(speaker)
        else:
            # 最后尝试单说话人方式
            audio_files = AudioService._get_single_speaker_files(speaker)
        
        # 获取用户专属的文件排序
        if username:
            audio_files = AudioService._get_user_audio_order(speaker, username, audio_files)
        else:
            random.shuffle(audio_files)
        
        return audio_files
    
    @staticmethod
    def _get_grouped_speaker_files(speaker):
        """获取分组说话人的音频文件"""
        # 检查是否有子文件夹结构
        all_items = os.listdir(Config.AUDIO_FOLDER)
        has_subdirs = any(os.path.isdir(os.path.join(Config.AUDIO_FOLDER, item)) for item in all_items)
        
        if has_subdirs:
            # 有子文件夹的情况
            all_speakers = [
                d for d in all_items
                if os.path.isdir(os.path.join(Config.AUDIO_FOLDER, d)) 
                and d.startswith(speaker + '-')
            ]
            
            audio_files = []
            for sub_speaker in all_speakers:
                speaker_folder = os.path.join(Config.AUDIO_FOLDER, sub_speaker)
                files = glob.glob(os.path.join(speaker_folder, "*.wav"))
                audio_files.extend(files)
        else:
            # 所有文件在同一个文件夹下的情况
            audio_files = []
            for item in all_items:
                if item.endswith('.wav') and item.startswith(speaker + '-'):
                    audio_files.append(os.path.join(Config.AUDIO_FOLDER, item))
        
        return audio_files
    
    @staticmethod
    def _get_single_speaker_files(speaker):
        """获取单个说话人的音频文件"""
        # 检查是否有子文件夹结构
        all_items = os.listdir(Config.AUDIO_FOLDER)
        has_subdirs = any(os.path.isdir(os.path.join(Config.AUDIO_FOLDER, item)) for item in all_items)
        
        if has_subdirs:
            # 有子文件夹的情况
            speaker_folder = os.path.join(Config.AUDIO_FOLDER, speaker)
            if not os.path.exists(speaker_folder):
                raise FileNotFoundError(f"找不到说话人 {speaker} 的文件夹")
            return glob.glob(os.path.join(speaker_folder, "*.wav"))
        else:
            # 所有文件在同一个文件夹下的情况
            audio_files = []
            for item in all_items:
                if item.endswith('.wav') and item.startswith(speaker + '-'):
                    audio_files.append(os.path.join(Config.AUDIO_FOLDER, item))
            return audio_files
    
    @staticmethod
    def _get_user_audio_order(speaker, username, audio_files):
        """获取用户专属的音频文件排序"""
        order_service = OrderService()
        return order_service.get_user_audio_order(speaker, username, audio_files)
    
    @staticmethod
    def get_all_audio_files(username=""):
        """获取所有音频文件列表（不按说话人分组）"""
        if not os.path.exists(Config.AUDIO_FOLDER):
            raise FileNotFoundError(f"音频文件夹不存在: {Config.AUDIO_FOLDER}")
        
        all_items = os.listdir(Config.AUDIO_FOLDER)
        has_subdirs = any(os.path.isdir(os.path.join(Config.AUDIO_FOLDER, item)) for item in all_items)
        
        audio_files = []
        
        if has_subdirs:
            # 有子文件夹的情况，遍历所有子文件夹
            for item in all_items:
                item_path = os.path.join(Config.AUDIO_FOLDER, item)
                if os.path.isdir(item_path):
                    files = glob.glob(os.path.join(item_path, "*.wav"))
                    audio_files.extend(files)
        else:
            # 所有文件在同一个文件夹下的情况
            files = glob.glob(os.path.join(Config.AUDIO_FOLDER, "*.wav"))
            audio_files.extend(files)
        
        # 如果有用户名，可以进行用户专属排序
        if username:
            # 这里可以添加用户专属的排序逻辑
            pass
        else:
            # 默认按文件名排序
            audio_files.sort()
        
        return audio_files
    
    @staticmethod
    def find_audio_file(speaker, filename):
        """查找音频文件的完整路径"""
        # 检查是否有子文件夹结构
        all_items = os.listdir(Config.AUDIO_FOLDER)
        has_subdirs = any(os.path.isdir(os.path.join(Config.AUDIO_FOLDER, item)) for item in all_items)
        
        if re.match(r'spk\d+$', speaker):
            # 分组说话人
            if has_subdirs:
                # 有子文件夹的情况
                all_speakers = [
                    d for d in all_items
                    if os.path.isdir(os.path.join(Config.AUDIO_FOLDER, d)) 
                    and d.startswith(speaker + '-')
                ]
                
                for sub_speaker in all_speakers:
                    # 首先尝试直接查找文件名
                    file_path = os.path.join(Config.AUDIO_FOLDER, sub_speaker, filename)
                    if os.path.exists(file_path):
                        return file_path, sub_speaker
                    
                    # 如果文件名包含说话人前缀，尝试提取实际文件名
                    if filename.startswith(sub_speaker + '-'):
                        # 提取去掉说话人前缀的文件名部分
                        actual_filename = filename[len(sub_speaker + '-'):]
                        file_path = os.path.join(Config.AUDIO_FOLDER, sub_speaker, actual_filename)
                        if os.path.exists(file_path):
                            return file_path, sub_speaker
            else:
                # 所有文件在同一个文件夹下的情况
                file_path = os.path.join(Config.AUDIO_FOLDER, filename)
                if os.path.exists(file_path):
                    return file_path, speaker
            return None, None
        else:
            # 单个说话人
            if has_subdirs:
                file_path = os.path.join(Config.AUDIO_FOLDER, speaker, filename)
                if os.path.exists(file_path):
                    return file_path, speaker
            else:
                # 所有文件在同一个文件夹下的情况
                file_path = os.path.join(Config.AUDIO_FOLDER, filename)
                if os.path.exists(file_path):
                    return file_path, speaker
            return None, None