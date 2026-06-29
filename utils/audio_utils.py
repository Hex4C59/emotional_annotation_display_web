import os
import wave

def get_audio_duration(file_path):
    """获取音频文件的时长（秒）"""
    try:
        if os.path.splitext(file_path)[1].lower() == ".wav":
            with wave.open(file_path, "rb") as audio:
                frame_rate = audio.getframerate()
                frame_count = audio.getnframes()
                if frame_rate <= 0:
                    return 0.0
                return frame_count / float(frame_rate)

        from pydub import AudioSegment
        import pydub.exceptions

        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # 毫秒转换为秒
    except (wave.Error, EOFError):
        print(f"无法读取 WAV 音频文件: {file_path}")
        return 0.0
    except Exception as e:
        print(f"获取音频时长时出错: {e}")
        return 0.0
