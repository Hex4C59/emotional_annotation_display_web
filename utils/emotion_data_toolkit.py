import pandas as pd
import sqlite3
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """数据库管理类"""
    def __init__(self, db_path: str):
        """初始化数据库连接

        Args:
            db_path (str): 数据库文件路径
        """
        self.__db_path = db_path
        self.__connect = None
    
    @property
    def connect(self):
        """建立数据库连接"""
        if self.__connect is None:
            try:
                self.__connect = sqlite3.connect(self.__db_path)
                print(f"成功连接到数据库: {self.__db_path}")
            except sqlite3.Error as e:
                print(f"连接数据库失败: {e}")
                raise
        
        return self.__connect
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.__connect:
            self.__connect.close()
            self.__connect = None
            print("数据库连接已关闭")            
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self,  exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

class TableDataProcessor:
    """表数据处理类"""
    def __init__(self, db_manager: DatabaseManager):
        """初始化数据处理器

        Args:
            db_manager (DatabaseManager): 数据库管理器实例
        """
        self.db_manager = db_manager
    
    def read_table(self, table_name: str) -> pd.DataFrame:
        """读取指定表的数据

        Args:
            table_name (str): 表名称

        Returns:
            pd.DataFrame: 表数据
        """
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, self.db_manager.connect)
            print(f"成功读取表 {table_name} 的数据")
            return df
        except sqlite3.Error as e:
            print(f"读取表 {table_name} 时出错: {e}")
            return pd.DataFrame()
        
def main():
    "使用上下文管理器确保连接正确关闭"
    with DatabaseManager('database/unified_emotion_system.db') as db_manager:
        # 创建数据处理器
        processor = TableDataProcessor(db_manager)
        df = processor.read_table('emotion_labels')
        print(df.head())
        

if __name__ == "__main__":
    main()
    
