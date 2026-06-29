#!/usr/bin/env python3
# filepath: /mnt/shareEEx/liuyang/code/emotion_labeling_refactoring/utils/extract_consistency_test_data.py
"""
从标注数据中提取音频文件用于一致性测试
根据优先级条件选择符合要求的音频文件
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

class ConsistencyTestDataExtractor:
    def __init__(self):
        # 定义路径
        self.base_dir = Path("/mnt/shareEEx/liuyang/code/emotion_labeling_refactoring")
        self.json_dir = self.base_dir / "gzx"
        self.source_audio_dir = self.base_dir / "data" / "emotion_annotation"
        self.output_dir = self.base_dir / "data" / "consistency_test"
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 优先级条件
        self.priority_conditions = [
            # 最高优先级：满足所有3个条件
            lambda data: (
                data.get('v_value') != 0 and 
                data.get('a_value') != 3 and 
                data.get('emotion_type') == 'non-neutral'
            ),
            # 次优先级：满足2个条件
            lambda data: sum([
                data.get('v_value') != 0,
                data.get('a_value') != 3,
                data.get('emotion_type') == 'non-neutral'
            ]) == 2,
            # 次次优先级：满足1个条件
            lambda data: sum([
                data.get('v_value') != 0,
                data.get('a_value') != 3,
                data.get('emotion_type') == 'non-neutral'
            ]) == 1,
            # 最低优先级：不满足任何条件
            lambda data: sum([
                data.get('v_value') != 0,
                data.get('a_value') != 3,
                data.get('emotion_type') == 'non-neutral'
            ]) == 0
        ]

    def find_target_json_files(self) -> List[Path]:
        """查找目标JSON文件（以spk2和spk11开头）"""
        json_files = []
        
        if not self.json_dir.exists():
            print(f"错误：JSON目录不存在 - {self.json_dir}")
            return json_files
            
        for file_path in self.json_dir.glob("*.json"):
            filename = file_path.name
            if filename.startswith("spk2") or filename.startswith("spk11"):
                json_files.append(file_path)
                
        print(f"找到 {len(json_files)} 个目标JSON文件")
        return json_files

    def load_json_data(self, json_file: Path) -> List[Dict]:
        """加载JSON文件数据"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 处理不同的JSON结构
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # 如果是字典，尝试获取包含标注数据的键
                for key in ['annotations', 'data', 'labels']:
                    if key in data:
                        return data[key] if isinstance(data[key], list) else [data[key]]
                # 如果没有找到，将整个字典作为单个条目
                return [data]
            else:
                print(f"警告：未知的JSON结构 - {json_file}")
                return []
                
        except json.JSONDecodeError as e:
            print(f"错误：无法解析JSON文件 {json_file} - {e}")
            return []
        except Exception as e:
            print(f"错误：读取文件失败 {json_file} - {e}")
            return []

    def categorize_by_priority(self, annotations: List[Dict]) -> Dict[int, List[Dict]]:
        """根据优先级条件对标注数据进行分类"""
        categories = {0: [], 1: [], 2: [], 3: []}  # 0=最高优先级, 3=最低优先级
        
        for annotation in annotations:
            # 检查是否有audio_file字段
            if 'audio_file' not in annotation:
                continue
                
            # 按优先级检查条件
            categorized = False
            for priority, condition in enumerate(self.priority_conditions):
                try:
                    if condition(annotation):
                        categories[priority].append(annotation)
                        categorized = True
                        break
                except Exception as e:
                    print(f"警告：条件检查失败 - {e}")
                    continue
            
            # 如果没有分类成功，放到最低优先级
            if not categorized:
                categories[3].append(annotation)
        
        return categories

    def find_audio_file(self, audio_filename: str) -> Path:
        """在源音频目录中查找音频文件"""
        # 尝试不同的可能路径
        possible_paths = [
            self.source_audio_dir / audio_filename,
            self.source_audio_dir / f"{audio_filename}.wav",
            # 在子目录中查找
        ]
        
        # 递归查找
        for root, dirs, files in os.walk(self.source_audio_dir):
            if audio_filename in files:
                return Path(root) / audio_filename
            # 尝试添加.wav扩展名
            wav_filename = f"{audio_filename}.wav" if not audio_filename.endswith('.wav') else audio_filename
            if wav_filename in files:
                return Path(root) / wav_filename
        
        return None

    def copy_audio_files(self, categories: Dict[int, List[Dict]], total_target: int = 50) -> Dict[str, int]:
        """复制音频文件到输出目录，总共复制50个文件"""
        stats = {
            'priority_0': 0,  # 满足3个条件
            'priority_1': 0,  # 满足2个条件
            'priority_2': 0,  # 满足1个条件
            'priority_3': 0,  # 满足0个条件
            'not_found': 0,   # 未找到的文件
            'errors': 0       # 复制错误
        }
        
        priority_names = ['priority_0', 'priority_1', 'priority_2', 'priority_3']
        total_copied = 0
        
        print(f"\n开始复制音频文件，目标总数: {total_target}")
        
        for priority in range(4):
            if total_copied >= total_target:
                print(f"已达到目标数量 {total_target}，停止复制")
                break
                
            annotations = categories[priority]
            
            print(f"\n处理优先级 {priority} (满足 {3-priority} 个条件)，共 {len(annotations)} 个文件")
            
            for annotation in annotations:
                if total_copied >= total_target:
                    print(f"已达到目标数量 {total_target}，停止复制")
                    break
                
                audio_filename = annotation['audio_file']
                source_path = self.find_audio_file(audio_filename)
                
                if source_path is None:
                    print(f"未找到音频文件: {audio_filename}")
                    stats['not_found'] += 1
                    continue
                
                # 生成输出文件名（添加优先级前缀和序号）
                base_name = Path(audio_filename).stem
                extension = Path(audio_filename).suffix or '.wav'
                output_filename = f"p{priority}_{total_copied+1:03d}_{base_name}{extension}"
                output_path = self.output_dir / output_filename
                
                try:
                    shutil.copy2(source_path, output_path)
                    stats[priority_names[priority]] += 1
                    total_copied += 1
                    print(f"✓ 复制 ({total_copied}/{total_target}): {audio_filename} -> {output_filename}")
                    
                    # 同时保存对应的标注信息
                    info_file = output_path.with_suffix('.json')
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump(annotation, f, ensure_ascii=False, indent=2)
                        
                except Exception as e:
                    print(f"✗ 复制失败: {audio_filename} - {e}")
                    stats['errors'] += 1
        
        return stats

    def run(self, total_files: int = 50):
        """运行提取流程"""
        print("开始提取一致性测试数据...")
        print(f"源JSON目录: {self.json_dir}")
        print(f"源音频目录: {self.source_audio_dir}")
        print(f"输出目录: {self.output_dir}")
        print(f"目标文件总数: {total_files}")
        
        # 1. 查找目标JSON文件
        json_files = self.find_target_json_files()
        if not json_files:
            print("没有找到目标JSON文件")
            return
        
        # 2. 加载所有标注数据
        all_annotations = []
        for json_file in json_files:
            print(f"处理文件: {json_file.name}")
            annotations = self.load_json_data(json_file)
            all_annotations.extend(annotations)
            print(f"  加载了 {len(annotations)} 条标注")
        
        print(f"\n总共加载了 {len(all_annotations)} 条标注数据")
        
        # 3. 按优先级分类
        categories = self.categorize_by_priority(all_annotations)
        
        print("\n按优先级分类结果:")
        for priority in range(4):
            condition_count = 3 - priority
            print(f"优先级 {priority} (满足 {condition_count} 个条件): {len(categories[priority])} 个文件")
        
        # 4. 复制音频文件
        stats = self.copy_audio_files(categories, total_files)
        
        # 5. 输出统计信息
        total_copied = stats['priority_0'] + stats['priority_1'] + stats['priority_2'] + stats['priority_3']
        print(f"\n提取完成！统计信息:")
        print(f"优先级0 (满足3个条件): {stats['priority_0']} 个文件")
        print(f"优先级1 (满足2个条件): {stats['priority_1']} 个文件") 
        print(f"优先级2 (满足1个条件): {stats['priority_2']} 个文件")
        print(f"优先级3 (满足0个条件): {stats['priority_3']} 个文件")
        print(f"总共复制: {total_copied} 个文件")
        print(f"未找到的文件: {stats['not_found']} 个")
        print(f"复制错误: {stats['errors']} 个")
        print(f"输出目录: {self.output_dir}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='提取一致性测试数据')
    parser.add_argument('--total-files', type=int, default=50,
                       help='总共提取的文件数量 (默认: 50)')
    
    args = parser.parse_args()
    
    extractor = ConsistencyTestDataExtractor()
    extractor.run(total_files=args.total_files)

if __name__ == "__main__":
    main()