#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能监控和优化脚本
用于监控数据库性能并提供优化建议
"""

import os
import sys
import sqlite3
import time
import json
from datetime import datetime
from contextlib import contextmanager

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from config.performance_config import PerformanceConfig

class DatabasePerformanceMonitor:
    """
    数据库性能监控器
    """
    
    def __init__(self):
        self.db_path = os.path.join(Config.DATABASE_FOLDER, 'unified_emotion_system.db')
        self.performance_log = []
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def measure_query_performance(self, query, params=None, description=""):
        """
        测量查询性能
        
        Args:
            query: SQL查询语句
            params: 查询参数
            description: 查询描述
            
        Returns:
            dict: 性能测量结果
        """
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                
            end_time = time.time()
            execution_time = end_time - start_time
            
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'description': description,
                'query': query[:100] + '...' if len(query) > 100 else query,
                'execution_time': execution_time,
                'result_count': len(results),
                'success': True
            }
            
            self.performance_log.append(performance_data)
            return performance_data
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'description': description,
                'query': query[:100] + '...' if len(query) > 100 else query,
                'execution_time': execution_time,
                'error': str(e),
                'success': False
            }
            
            self.performance_log.append(performance_data)
            return performance_data
    
    def analyze_database_performance(self):
        """
        分析数据库性能
        
        Returns:
            dict: 性能分析结果
        """
        analysis = {
            'database_size': self.get_database_size(),
            'table_stats': self.get_table_statistics(),
            'index_usage': self.get_index_usage(),
            'pragma_settings': self.get_pragma_settings(),
            'recommendations': []
        }
        
        # 生成优化建议
        analysis['recommendations'] = self.generate_recommendations(analysis)
        
        return analysis
    
    def get_database_size(self):
        """
        获取数据库大小信息
        
        Returns:
            dict: 数据库大小信息
        """
        try:
            file_size = os.path.getsize(self.db_path)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取页面大小和页面数量
                cursor.execute('PRAGMA page_size;')
                page_size = cursor.fetchone()[0]
                
                cursor.execute('PRAGMA page_count;')
                page_count = cursor.fetchone()[0]
                
                # 获取空闲页面数量
                cursor.execute('PRAGMA freelist_count;')
                freelist_count = cursor.fetchone()[0]
                
            return {
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / 1024 / 1024, 2),
                'page_size': page_size,
                'page_count': page_count,
                'freelist_count': freelist_count,
                'fragmentation_ratio': round(freelist_count / page_count * 100, 2) if page_count > 0 else 0
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_table_statistics(self):
        """
        获取表统计信息
        
        Returns:
            list: 表统计信息列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_stats = []
                
                for table in tables:
                    # 获取表行数
                    cursor.execute(f'SELECT COUNT(*) FROM {table};')
                    row_count = cursor.fetchone()[0]
                    
                    # 获取表大小（近似）
                    cursor.execute(f'PRAGMA table_info({table});')
                    columns = cursor.fetchall()
                    
                    table_stats.append({
                        'table_name': table,
                        'row_count': row_count,
                        'column_count': len(columns)
                    })
                
                return table_stats
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_index_usage(self):
        """
        获取索引使用情况
        
        Returns:
            list: 索引信息列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取所有索引
                cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index';")
                indexes = cursor.fetchall()
                
                index_info = []
                
                for index in indexes:
                    index_name, table_name = index
                    
                    # 跳过自动创建的索引
                    if index_name.startswith('sqlite_autoindex'):
                        continue
                    
                    index_info.append({
                        'index_name': index_name,
                        'table_name': table_name
                    })
                
                return index_info
                
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_pragma_settings(self):
        """
        获取当前PRAGMA设置
        
        Returns:
            dict: PRAGMA设置
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                pragmas = {}
                
                # 重要的PRAGMA设置
                pragma_queries = [
                    'journal_mode',
                    'synchronous',
                    'cache_size',
                    'temp_store',
                    'mmap_size'
                ]
                
                for pragma in pragma_queries:
                    cursor.execute(f'PRAGMA {pragma};')
                    result = cursor.fetchone()
                    pragmas[pragma] = result[0] if result else None
                
                return pragmas
                
        except Exception as e:
            return {'error': str(e)}
    
    def generate_recommendations(self, analysis):
        """
        生成性能优化建议
        
        Args:
            analysis: 性能分析结果
            
        Returns:
            list: 优化建议列表
        """
        recommendations = []
        
        # 检查数据库大小
        if 'database_size' in analysis:
            size_info = analysis['database_size']
            
            if size_info.get('fragmentation_ratio', 0) > 10:
                recommendations.append({
                    'type': 'fragmentation',
                    'priority': 'medium',
                    'message': f'数据库碎片率较高 ({size_info["fragmentation_ratio"]}%)，建议执行VACUUM操作',
                    'action': 'VACUUM'
                })
            
            if size_info.get('file_size_mb', 0) > 100:
                recommendations.append({
                    'type': 'size',
                    'priority': 'low',
                    'message': f'数据库文件较大 ({size_info["file_size_mb"]}MB)，考虑定期清理或归档旧数据',
                    'action': 'archive_old_data'
                })
        
        # 检查PRAGMA设置
        if 'pragma_settings' in analysis:
            pragma_settings = analysis['pragma_settings']
            
            if pragma_settings.get('journal_mode') != 'wal':
                recommendations.append({
                    'type': 'pragma',
                    'priority': 'high',
                    'message': '建议启用WAL模式以提高并发性能',
                    'action': 'PRAGMA journal_mode=WAL'
                })
            
            if pragma_settings.get('synchronous') not in ['NORMAL', 1]:
                recommendations.append({
                    'type': 'pragma',
                    'priority': 'medium',
                    'message': '建议设置synchronous=NORMAL以平衡性能和安全性',
                    'action': 'PRAGMA synchronous=NORMAL'
                })
        
        # 检查表统计
        if 'table_stats' in analysis:
            for table_stat in analysis['table_stats']:
                if table_stat.get('row_count', 0) > 10000:
                    recommendations.append({
                        'type': 'index',
                        'priority': 'medium',
                        'message': f'表 {table_stat["table_name"]} 行数较多 ({table_stat["row_count"]})，确保有适当的索引',
                        'action': f'check_indexes_{table_stat["table_name"]}'
                    })
        
        return recommendations
    
    def optimize_database(self):
        """
        执行数据库优化操作
        
        Returns:
            dict: 优化结果
        """
        optimization_results = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 应用性能配置中的PRAGMA设置
                for pragma in PerformanceConfig.get_db_pragmas():
                    try:
                        cursor.execute(pragma)
                        optimization_results.append({
                            'action': pragma,
                            'success': True
                        })
                    except Exception as e:
                        optimization_results.append({
                            'action': pragma,
                            'success': False,
                            'error': str(e)
                        })
                
                # 执行ANALYZE以更新统计信息
                cursor.execute('ANALYZE;')
                optimization_results.append({
                    'action': 'ANALYZE',
                    'success': True
                })
                
                conn.commit()
                
        except Exception as e:
            optimization_results.append({
                'action': 'general_optimization',
                'success': False,
                'error': str(e)
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'results': optimization_results
        }
    
    def save_performance_report(self, filename=None):
        """
        保存性能报告
        
        Args:
            filename: 报告文件名
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_report_{timestamp}.json'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': self.analyze_database_performance(),
            'performance_log': self.performance_log
        }
        
        report_path = os.path.join(Config.DATABASE_FOLDER, filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"性能报告已保存到: {report_path}")
        return report_path

def main():
    """主函数"""
    monitor = DatabasePerformanceMonitor()
    
    print("=== 数据库性能监控和优化 ===")
    print()
    
    # 分析数据库性能
    print("正在分析数据库性能...")
    analysis = monitor.analyze_database_performance()
    
    # 显示基本信息
    if 'database_size' in analysis:
        size_info = analysis['database_size']
        print(f"数据库大小: {size_info.get('file_size_mb', 0)} MB")
        print(f"碎片率: {size_info.get('fragmentation_ratio', 0)}%")
    
    # 显示优化建议
    if analysis.get('recommendations'):
        print("\n优化建议:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"{i}. [{rec['priority'].upper()}] {rec['message']}")
    else:
        print("\n数据库性能良好，无需优化。")
    
    # 询问是否执行优化
    if analysis.get('recommendations'):
        response = input("\n是否执行数据库优化? (y/n): ")
        if response.lower() == 'y':
            print("\n正在执行优化...")
            optimization_result = monitor.optimize_database()
            
            success_count = sum(1 for r in optimization_result['results'] if r['success'])
            total_count = len(optimization_result['results'])
            
            print(f"优化完成: {success_count}/{total_count} 项成功")
    
    # 保存报告
    report_path = monitor.save_performance_report()
    print(f"\n详细报告已保存到: {report_path}")

if __name__ == '__main__':
    main()