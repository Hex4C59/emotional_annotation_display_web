# models/emotion_model.py
# models/emotion_model.py
from datetime import datetime

class EmotionLabel:
    """情感标注数据模型"""
    
    def __init__(self, audio_file, v_value=None, a_value=None, emotion_type=None, 
                 discrete_emotion=None, username=None, patient_status=None, 
                 audio_duration=0, va_complete=False, discrete_complete=False, play_count=0):
        self.audio_file = audio_file
        self.v_value = v_value
        self.a_value = a_value
        self.emotion_type = emotion_type
        self.discrete_emotion = discrete_emotion
        self.username = username
        self.patient_status = patient_status
        self.audio_duration = audio_duration
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.play_count = play_count  # 播放次数
        
        # 这两个字段现在由下面的方法自动管理
        self.va_complete = va_complete
        self.discrete_complete = discrete_complete

        # [新增] 初始化时即更新一次完整性状态
        self.update_completeness()
    
    def update_completeness(self):
        """
        [新增] 根据当前属性值，更新VA和离散情感的完成状态。
        这个方法将完成状态的计算逻辑封装在模型内部。
        """
        # 1. 更新VA完成状态 - 只有当用户实际设置了值时才认为完成
        hasV = self.v_value is not None
        hasA = self.a_value is not None 
        if hasV and hasA:
            self.va_complete = True
        else:
            self.va_complete = False
            
        # 2. 更新离散情感完成状态 - 只有当用户实际设置了值时才认为完成
        has_patient_status = self.patient_status is not None
        has_emotion_type = self.emotion_type is not None
        has_discrete_sub_emotion = False
        
        if self.emotion_type == 'neutral' and self.va_complete:
            has_discrete_sub_emotion = True  # 中性情感不需要选择具体子情感
        elif self.emotion_type == 'non-neutral' and self.discrete_emotion is not None and self.va_complete:
            has_discrete_sub_emotion = True
        
        if has_patient_status and has_emotion_type and has_discrete_sub_emotion:
            self.discrete_complete = True
        else:
            self.discrete_complete = False

    def to_dict(self):
        """转换为字典"""
        return {
            "audio_file": self.audio_file,
            "v_value": self.v_value,
            "a_value": self.a_value,
            "emotion_type": self.emotion_type,
            "discrete_emotion": self.discrete_emotion,
            "username": self.username,
            "patient_status": self.patient_status,
            "audio_duration": self.audio_duration,
            "timestamp": self.timestamp,
            "va_complete": self.va_complete,
            "discrete_complete": self.discrete_complete,
            "play_count": self.play_count,
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        # [修改] 移除对 va_complete 和 discrete_complete 的直接赋值
        label = cls(
            data.get("audio_file"),
            data.get("v_value"),
            data.get("a_value"),
            data.get("emotion_type"),
            data.get("discrete_emotion"),
            data.get("username"),
            data.get("patient_status"),
            data.get("audio_duration", 0),
            # va_complete 和 discrete_complete 将由 update_completeness 自动计算，
            # 无需从字典中读取旧的状态，保证了状态的实时正确性。
            play_count=data.get("play_count", 0),
        )
        if "timestamp" in data:
            label.timestamp = data["timestamp"]
        
        # [修改] 在创建实例后，调用更新方法。
        # 这样可以兼容旧数据（没有这两个flag），并自动生成正确的状态。
        label.update_completeness()
        
        return label

def calculate_annotation_completeness(label_dict):
    """计算标注的完整性状态
    
    现在这个函数直接读取字典中的 'va_complete' 和 'discrete_complete' 标志。
    """
    # --- 1. 直接从字典中获取已经计算好的状态 ---
    va_complete = label_dict.get('va_complete', False)
    discrete_complete = label_dict.get('discrete_complete', False)

    # --- 2. 构建结果列表 ---
    completeness_status = []
    if va_complete:
        completeness_status.append('va_complete')
    if discrete_complete:
        completeness_status.append('discrete_complete')

    # --- 3. 根据结果列表决定最终返回 ---
    # 如果列表不为空，说明至少有一项是完整的，直接返回列表
    if completeness_status:
        return completeness_status
        
    # 如果以上都不是，则为完全未标注
    return ['none']