#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIS历史数据到ClickHouse数据库导入器
=====================================

功能概述:
--------
本工具继承自HisDataParser类，专门用于将解析的HIS历史数据直接写入ClickHouse数据库。
相比Excel导出，数据库存储具有更好的查询性能、并发访问和数据压缩能力。

核心特性:
--------
1. 继承原有解析功能：完全复用HisDataParser的解析能力
2. ClickHouse连接管理：支持连接池和自动重连
3. 批量写入优化：使用批量插入提升写入性能
4. 数据类型映射：自动处理Python到ClickHouse的类型转换
5. 错误处理：完善的异常处理和重试机制
6. 表结构管理：自动创建和管理数据表结构

数据库设计:
----------
表名：his_timeseries_data
字段：
- timestamp: DateTime64(3) - 时间戳（毫秒精度）
- point_code: String - 数据点代码
- point_name: String - 数据点名称
- value: Float64 - 数值
- quality: UInt8 - 数据质量
- xh: UInt32 - 数据点序号
- file_source: String - 源文件名
- created_at: DateTime - 创建时间

使用方法:
--------
命令行模式:
  python his_to_clickhouse.py --file 2025070222 --point "20MCS-UNITMW" --dir ./his-data

编程模式:
  parser = HisToClickHouseParser()
  success = parser.parse_and_save_to_clickhouse(directory, "2025070222", "20MCS-UNITMW")

依赖要求:
--------
- clickhouse-driver: ClickHouse数据库连接驱动
- pandas: 数据处理
- numpy: 数值计算

作者: zhengxu
版本: 1.0
创建: 2025-07-29
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

# 导入父类
from parse_his_data import HisDataParser, StructAxPoint

try:
    import requests
    import json
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("警告: requests未安装。请运行: pip install requests")


class HisToClickHouseParser(HisDataParser):
    """
    HIS数据到ClickHouse导入器
    ========================
    
    功能说明:
    --------
    继承HisDataParser类，扩展数据库写入功能。保留原有的所有解析能力，
    增加ClickHouse数据库连接、表管理和批量数据写入功能。
    
    核心功能:
    --------
    1. 数据库连接管理：维护ClickHouse连接池
    2. 表结构管理：自动创建和维护数据表
    3. 批量数据写入：优化的批量插入操作
    4. 数据类型转换：Python对象到ClickHouse类型的自动映射
    5. 事务处理：确保数据一致性
    6. 错误恢复：连接断开重连和失败重试
    
    性能优化:
    --------
    - 批量插入：每次写入1000-5000条记录
    - 连接复用：维护长连接避免频繁建连
    - 数据压缩：利用ClickHouse列式存储压缩
    - 索引优化：基于时间戳和数据点的复合索引
    """
    
    def __init__(self, host='192.168.50.30', port=8123, database='default',
                 user='default', password='er3HsdSE2dQIS^VI', batch_size=2000):
        """
        初始化ClickHouse解析器
        
        Args:
            host: ClickHouse服务器地址
            port: 端口号（HTTP接口）
            database: 数据库名
            user: 用户名
            password: 密码
            batch_size: 批量写入大小
        """
        super().__init__()
        
        if not CLICKHOUSE_AVAILABLE:
            raise ImportError("requests未安装，请运行: pip install requests")
        
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.batch_size = batch_size
        self.base_url = f"http://{host}:{port}"
        self.auth = (user, password)
        self.table_name = 'his_timeseries_data'
        
    def execute_query(self, query: str, data: list = None):
        """
        执行ClickHouse查询（HTTP接口）
        
        Args:
            query: SQL查询语句
            data: 插入数据（可选）
            
        Returns:
            查询结果或None（如果失败）
        """
        try:
            if data:
                # 批量插入数据
                query_with_data = query
                for row in data:
                    values = []
                    for key in ['timestamp', 'point_code', 'point_name', 'value', 'quality', 'xh', 'file_source', 'created_at']:
                        value = row.get(key, '')
                        if isinstance(value, str):
                            values.append(f"'{value}'")
                        elif isinstance(value, datetime):
                            values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}'")
                        else:
                            values.append(str(value))
                    query_with_data += f"\n({', '.join(values)})"
                    if row != data[-1]:
                        query_with_data += ","
                
                full_query = query_with_data
            else:
                full_query = query
            
            response = requests.post(
                self.base_url,
                data=full_query,
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()
            
            # 解析响应
            result_text = response.text.strip()
            if not result_text:
                return []
            
            # 按行分割结果
            lines = result_text.split('\n')
            results = []
            for line in lines:
                if line.strip():
                    # 按制表符分割字段
                    fields = line.split('\t')
                    results.append(fields)
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"HTTP请求失败: {e}")
            return None
        except Exception as e:
            print(f"查询执行失败: {e}")
            return None
        
    def connect(self) -> bool:
        """
        测试ClickHouse数据库连接（HTTP接口）
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 测试连接
            result = self.execute_query('SELECT 1')
            if result is not None:
                print(f"ClickHouse连接成功: {self.base_url}/{self.database}")
                return True
            else:
                print(f"ClickHouse连接失败: {self.base_url}")
                return False
            
        except Exception as e:
            print(f"ClickHouse连接失败: {e}")
            return False
    
    def create_table_if_not_exists(self) -> bool:
        """
        创建数据表（如果不存在）
        
        Returns:
            bool: 创建是否成功
        """
        try:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                timestamp DateTime64(3),
                point_code String,
                point_name String,
                value Float64,
                quality UInt8,
                xh UInt32,
                file_source String,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY (point_code, timestamp)
            PARTITION BY toYYYYMM(timestamp)
            """
            
            result = self.execute_query(create_sql)
            if result is not None:
                print(f"数据表 {self.table_name} 创建/验证成功")
                return True
            else:
                print(f"创建数据表失败")
                return False
            
        except Exception as e:
            print(f"创建数据表失败: {e}")
            return False
    
    def insert_data_points_batch(self, data_points: List[StructAxPoint],
                                 file_source: str) -> bool:
        """
        批量插入数据点到ClickHouse
        
        Args:
            data_points: 数据点列表
            file_source: 源文件名
            
        Returns:
            bool: 插入是否成功
        """
        if not data_points:
            return False
        
        try:
            # 准备批量插入数据
            batch_data = []
            for point in data_points:
                batch_data.append({
                    'timestamp': point.TimeStamp,
                    'point_code': point.PointCode,
                    'point_name': point.PointName,
                    'value': float(point.Value) if not pd.isna(point.Value) else 0.0,
                    'quality': int(point.Quality),
                    'xh': int(point.XH),
                    'file_source': file_source,
                    'created_at': datetime.now()
                })
            
            # 分批插入
            total_inserted = 0
            for i in range(0, len(batch_data), self.batch_size):
                batch = batch_data[i:i + self.batch_size]
                
                insert_sql = f"""
                INSERT INTO {self.table_name}
                (timestamp, point_code, point_name, value, quality, xh, file_source, created_at)
                VALUES
                """
                
                result = self.execute_query(insert_sql, batch)
                if result is not None:
                    total_inserted += len(batch)
                    print(f"已插入 {total_inserted}/{len(batch_data)} 条记录")
                else:
                    print(f"批次插入失败")
                    return False
            
            print(f"数据插入完成，共 {total_inserted} 条记录")
            return True
            
        except Exception as e:
            print(f"批量插入数据失败: {e}")
            return False
    
    def parse_and_save_to_clickhouse(self, directory: str, file_title: str,
                                   point_name: str) -> bool:
        """
        解析HIS数据并保存到ClickHouse数据库
        
        Args:
            directory: 文件目录
            file_title: 文件名标题
            point_name: 数据点名称
            
        Returns:
            bool: 处理是否成功
        """
        print(f"=== 开始处理数据点 '{point_name}' 到ClickHouse数据库 ===")
        
        # 建立数据库连接
        if not self.connect():
            return False
        
        # 创建数据表
        if not self.create_table_if_not_exists():
            return False
        
        try:
            # 解析数据（调用父类方法）
            data_points = self.read_single_point_all_blocks(directory, file_title, point_name)
            
            if not data_points:
                print("没有解析到任何数据")
                return False
            
            print(f"成功解析 {len(data_points)} 个数据点")
            
            # 插入数据库
            success = self.insert_data_points_batch(data_points, file_title)
            
            if success:
                # 查询验证
                self.verify_insertion(point_name, file_title)
                print(f"数据点 '{point_name}' 成功保存到ClickHouse数据库")
                return True
            else:
                print("数据保存失败")
                return False
                
        except Exception as e:
            print(f"处理过程中出错: {e}")
            return False
        finally:
            # HTTP连接无需手动关闭
            print("处理完成")
    
    def verify_insertion(self, point_name: str, file_source: str):
        """
        验证数据插入结果
        
        Args:
            point_name: 数据点名称
            file_source: 源文件名
        """
        try:
            # 查询插入的记录数
            count_sql = f"""
            SELECT count(*) as cnt 
            FROM {self.table_name} 
            WHERE point_code = %(point_code)s AND file_source = %(file_source)s
            """
            
            result = self.client.execute(
                count_sql, 
                {'point_code': point_name, 'file_source': file_source}
            )
            record_count = result[0][0] if result else 0
            
            # 查询时间范围
            range_sql = f"""
            SELECT 
                min(timestamp) as min_time,
                max(timestamp) as max_time,
                avg(value) as avg_value
            FROM {self.table_name} 
            WHERE point_code = %(point_code)s AND file_source = %(file_source)s
            """
            
            range_result = self.client.execute(
                range_sql,
                {'point_code': point_name, 'file_source': file_source}
            )
            
            if range_result:
                min_time, max_time, avg_value = range_result[0]
                print(f"验证结果:")
                print(f"  - 插入记录数: {record_count}")
                print(f"  - 时间范围: {min_time} 到 {max_time}")
                print(f"  - 平均值: {avg_value:.4f}")
            
        except Exception as e:
            print(f"验证插入结果时出错: {e}")
    
    def query_data(self, point_name: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        查询数据库中的数据
        
        Args:
            point_name: 数据点名称
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制返回记录数
            
        Returns:
            List[Dict]: 查询结果
        """
        if not self.client:
            if not self.connect():
                return []
        
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE point_code = %(point_code)s"
            params = {'point_code': point_name}
            
            if start_time:
                sql += " AND timestamp >= %(start_time)s"
                params['start_time'] = start_time
            
            if end_time:
                sql += " AND timestamp <= %(end_time)s"
                params['end_time'] = end_time

            sql += " ORDER BY timestamp"
            
            if limit > 0:
                sql += f" LIMIT {limit}"
            
            results = self.client.execute(sql, params)
            
            # 转换为字典格式
            columns = ['timestamp', 'point_code', 'point_name', 'value', 
                      'quality', 'xh', 'file_source', 'created_at']
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            print(f"查询数据时出错: {e}")
            return []
    
    def get_available_points(self) -> List[str]:
        """
        获取数据库中所有可用的数据点
        
        Returns:
            List[str]: 数据点列表
        """
        if not self.client:
            if not self.connect():
                return []
        
        try:
            sql = f"SELECT DISTINCT point_code FROM {self.table_name} ORDER BY point_code"
            results = self.client.execute(sql)
            return [row[0] for row in results]
            
        except Exception as e:
            print(f"获取数据点列表时出错: {e}")
            return []


def main():
    """
    演示函数
    """
    # 设置数据目录
    data_dir = "/Users/zx_ll/Desktop/some_code/just-some-code/DCS-data-process/his-data"

    # 创建解析器
    parser = HisToClickHouseParser(
        host='192.168.50.30',
        port=8123,
        database='default',
        user='default',
        password='er3HsdSE2dQIS^VI',
        batch_size=1000
    )

    # 解析指定文件
    filename_base = "2025070222"

    print("=== HIS数据到ClickHouse导入器 ===")
    print(f"目标文件: {filename_base}")
    print(f"ClickHouse: 192.168.50.30:8123")
    print()

    # 首先获取可用的数据点列表
    temp_parser = HisDataParser()
    temp_parser.get_point_code_and_xh(os.path.join(data_dir, f"{filename_base}.idx"))

    if temp_parser.m_codeToXh:
        available_points = list(temp_parser.m_codeToXh.keys())[:10]
        print(f"可用数据点(前10个): {available_points}")

        # 选择一个数据点进行解析
        if "20MCS-UNITMW" in temp_parser.m_codeToXh:
            target_point = "20MCS-UNITMW"
        else:
            target_point = available_points[0] if available_points else None

        if target_point:
            print(f"选择数据点: {target_point}")
            success = parser.parse_and_save_to_clickhouse(data_dir, filename_base, target_point)

            if success:
                print(f"数据点 '{target_point}' 成功保存到ClickHouse数据库")

                # 演示查询功能
                print("\n=== 查询验证 ===")
                query_results = parser.query_data(target_point, limit=5)
                if query_results:
                    print("查询结果(前5条):")
                    for i, record in enumerate(query_results):
                        print(f"  {i+1}. {record['timestamp']} - {record['value']}")
            else:
                print("数据保存失败")
        else:
            print("未找到可用的数据点")
    else:
        print("无法获取数据点列表")
    
    print("\n=== 处理完成 ===")


def main_with_args():
    """
    命令行参数主函数
    """
    import argparse
    
    parser_cmd = argparse.ArgumentParser(description='HIS数据到ClickHouse导入器')
    parser_cmd.add_argument('--file', '-f', required=True, help='文件名(不含扩展名), 如 2025070222')
    parser_cmd.add_argument('--point', '-p', help='数据点名称(如不指定则显示可用数据点列表)')
    parser_cmd.add_argument('--dir', '-d',
                            default="./his-data",
                            help='数据文件目录')
    parser_cmd.add_argument('--host', default='192.168.50.30', help='ClickHouse主机地址')
    parser_cmd.add_argument('--port', type=int, default=8123, help='ClickHouse端口')
    parser_cmd.add_argument('--database', default='default', help='数据库名')
    parser_cmd.add_argument('--user', default='default', help='用户名')
    parser_cmd.add_argument('--password', default='er3HsdSE2dQIS^VI', help='密码')
    parser_cmd.add_argument('--batch-size', type=int, default=2000, help='批量插入大小')
    
    args = parser_cmd.parse_args()
    
    # 创建解析器
    parser = HisToClickHouseParser(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
        batch_size=args.batch_size
    )
    
    print("=== HIS数据到ClickHouse导入器 ===")
    print(f"目标文件: {args.file}")
    print(f"数据目录: {args.dir}")
    print(f"ClickHouse: {args.host}:{args.port}/{args.database}")
    
    if not args.point:
        # 如果没有指定数据点，先显示可用的数据点
        temp_parser = HisDataParser()
        temp_parser.get_point_code_and_xh(os.path.join(args.dir, f"{args.file}.idx"))
        if temp_parser.m_codeToXh:
            available_points = list(temp_parser.m_codeToXh.keys())[:20]
            print("可用数据点(前20个):")
            for i, point in enumerate(available_points):
                print(f"  {i+1}. {point}")
            print("\n请使用 --point 参数指定数据点名称")
        else:
            print("无法获取数据点列表")
        return
    
    print(f"数据点: {args.point}")
    success = parser.parse_and_save_to_clickhouse(args.dir, args.file, args.point)
    
    if success:
        print(f"数据点 '{args.point}' 成功保存到ClickHouse数据库")
    else:
        print("数据处理失败")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main_with_args()
    else:
        main()
