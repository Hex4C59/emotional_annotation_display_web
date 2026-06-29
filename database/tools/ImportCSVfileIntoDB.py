import sqlite3
import csv
from datetime import datetime

#2025年9月10日
#bcd：这是一个用于导入csv文件到数据库中的脚本
#如果表不为空，可能需要先清空表，可以使用以下SQL命令：
#DELETE FROM standard_answers;
#删除standard_answers表中的所有数据
#DELETE FROM sqlite_sequence WHERE name='standard_answers';
#重置standard_answers表的自增主键


# 数据库和 CSV 文件路径
db_file = 'unified_emotion_system.db'
csv_file = 'standard_answers2.csv'

# 1. 连接数据库
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 2. 创建表（如果不存在）
cursor.execute("""
CREATE TABLE IF NOT EXISTS standard_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audio_file TEXT NOT NULL UNIQUE,
    v_value REAL,
    a_value REAL,
    emotion_type TEXT,
    discrete_emotion TEXT,
    patient_status TEXT,
    audio_duration REAL,
    created_by TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 3. 读取 CSV 文件
with open(csv_file, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    data = []
    for row in reader:
        try:
            v_value = float(row['v_value'])
            a_value = float(row['a_value'])
            audio_duration = float(row['audio_duration'])
        except ValueError:
            print(f"⚠️ 跳过无效数据行: {row}")
            continue

        # 如果 CSV 中有 timestamp，则使用 CSV 的值，否则使用默认
        timestamp_value = row.get('timestamp', None)
        data.append((
            row['audio_file'],
            v_value,
            a_value,
            row['emotion_type'],
            row['discrete_emotion'],
            row['patient_status'],
            audio_duration,
            row['created_by'],
            timestamp_value
        ))

# 4. 批量插入数据，重复 audio_file 自动忽略
cursor.executemany("""
INSERT OR IGNORE INTO standard_answers (
    audio_file, v_value, a_value, emotion_type, discrete_emotion, patient_status, audio_duration, created_by, timestamp
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", data)

# 5. 提交事务并关闭数据库
conn.commit()
conn.close()

print("✅ CSV 数据已成功导入数据库！")
