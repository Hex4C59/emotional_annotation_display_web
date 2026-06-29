import os
from .database_service import DatabaseService

class LabelService:
    """标注相关服务"""
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    def get_labeled_files(self, username, speaker, va_scale="5_point"):
        """获取已标注的文件列表"""
        return self.db_service.get_labeled_files(username, speaker, va_scale)
    
    def save_label(self, label_data, speaker, audio_file_path):
        """保存标注数据到数据库"""
        return self.db_service.save_label(label_data, speaker, audio_file_path)
    
    def get_label(self, username, speaker, filename, va_scale="5_point"):
        """获取标注数据"""
        return self.db_service.get_label(username, speaker, filename, va_scale)
    
    def save_play_count(self, username, speaker, filename, va_scale="5_point"):
        """保存音频播放次数"""
        return self.db_service.update_play_count(username, speaker, filename, va_scale)
    
    def get_play_count(self, username, speaker, filename, va_scale="5_point"):
        """获取音频播放次数"""
        return self.db_service.get_play_count(username, speaker, filename, va_scale)