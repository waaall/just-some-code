#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClickHouse数据库结构检查器
=========================

功能概述:
--------
本工具用于连接ClickHouse数据库，检查数据库结构信息，包括：
1. 数据库列表
2. 表结构信息
3. 字段类型和约束
4. 表大小和记录数
5. 索引信息
6. 分区信息

输出结果会保存为CSV文件，便于分析和后续数据写入格式调整。

作者: zhengxu
版本: 1.0
创建: 2025-07-29
"""

import os
try:
    import requests
    import pandas as pd
    import csv
    import json
    from datetime import datetime
    from typing import List, Dict, Any, Optional
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("错误: requests或pandas未安装。请运行: pip install requests pandas")


class ClickHouseInspector:
    """
    ClickHouse数据库结构检查器
    ========================
    
    功能说明:
    --------
    连接到ClickHouse数据库，检查和分析数据库结构，生成详细的结构报告。
    帮助了解现有数据库结构，为数据写入做准备。
    
    核心功能:
    --------
    1. 数据库连接测试
    2. 获取数据库列表
    3. 获取表列表和基本信息
    4. 获取表字段结构
    5. 获取表统计信息（记录数、大小等）
    6. 获取索引和分区信息
    7. 生成CSV格式的结构报告
    """
    
    def __init__(self, host='192.168.50.30', port=8123, database='default',
                 user='default', password='er3HsdSE2dQIS^VI'):
        """
        初始化数据库检查器
        
        Args:
            host: ClickHouse服务器地址
            port: 端口号（HTTP接口）
            database: 数据库名
            user: 用户名
            password: 密码
        """
        if not CLICKHOUSE_AVAILABLE:
            raise ImportError("requests或pandas未安装，请运行: pip install requests pandas")
        
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.base_url = f"http://{host}:{port}"
        self.auth = (user, password)
        
    def execute_query(self, query: str):
        """
        执行ClickHouse查询（HTTP接口）
        
        Args:
            query: SQL查询语句
            
        Returns:
            查询结果或None（如果失败）
        """
        try:
            response = requests.post(
                self.base_url,
                data=query,
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
            # 测试连接 - 获取版本信息
            version_result = self.execute_query('SELECT version()')
            if version_result is None:
                print("ClickHouse连接失败")
                return False
            
            version = version_result[0][0] if version_result and version_result[0] else "未知版本"
            print("ClickHouse连接成功!")
            print(f"服务器: {self.base_url}")
            print(f"数据库: {self.database}")
            print(f"版本: {version}")
            return True
            
        except Exception as e:
            print(f"ClickHouse连接失败: {e}")
            return False
    
    def get_databases(self) -> List[str]:
        """
        获取所有数据库列表
        
        Returns:
            List[str]: 数据库名列表
        """
        try:
            result = self.execute_query("SHOW DATABASES")
            if result is None:
                return []
            
            databases = [row[0] for row in result]
            print(f"找到 {len(databases)} 个数据库: {databases}")
            return databases
        except Exception as e:
            print(f"获取数据库列表失败: {e}")
            return []
    
    def get_tables(self, database: str = None) -> List[Dict[str, Any]]:
        """
        获取指定数据库中的所有表信息
        
        Args:
            database: 数据库名，默认使用当前连接的数据库
            
        Returns:
            List[Dict]: 表信息列表
        """
        db_name = database or self.database
        
        try:
            # 获取表列表和基本信息
            sql = f"""
            SELECT
                name,
                engine,
                total_rows,
                total_bytes,
                create_table_query
            FROM system.tables
            WHERE database = '{db_name}'
            ORDER BY name
            """
            
            result = self.execute_query(sql)
            if result is None:
                return []
            
            tables = []
            for row in result:
                if len(row) >= 5:
                    name, engine, total_rows, total_bytes, create_query = row[0], row[1], row[2], row[3], row[4]
                    try:
                        total_rows = int(total_rows) if total_rows else 0
                        total_bytes = int(total_bytes) if total_bytes else 0
                        size_mb = round(total_bytes / 1024 / 1024, 2)
                    except:
                        total_rows = 0
                        total_bytes = 0
                        size_mb = 0.0
                    
                    tables.append({
                        'database': db_name,
                        'table_name': name,
                        'engine': engine,
                        'total_rows': total_rows,
                        'total_bytes': total_bytes,
                        'size_mb': size_mb,
                        'create_query': create_query
                    })
            
            print(f"数据库 '{db_name}' 中找到 {len(tables)} 个表")
            return tables
            
        except Exception as e:
            print(f"获取表列表失败: {e}")
            return []
    
    def get_table_columns(self, table_name: str, database: str = None) -> List[Dict[str, Any]]:
        """
        获取指定表的字段结构信息
        
        Args:
            table_name: 表名
            database: 数据库名
            
        Returns:
            List[Dict]: 字段信息列表
        """
        db_name = database or self.database
        
        try:
            sql = f"""
            SELECT
                name,
                type,
                default_kind,
                default_expression,
                comment,
                is_in_partition_key,
                is_in_sorting_key,
                is_in_primary_key,
                is_in_sampling_key
            FROM system.columns
            WHERE database = '{db_name}' AND table = '{table_name}'
            ORDER BY position
            """
            
            result = self.execute_query(sql)
            if result is None:
                return []
            
            columns = []
            for row in result:
                if len(row) >= 9:
                    (name, col_type, default_kind, default_expr, comment,
                     in_partition, in_sorting, in_primary, in_sampling) = row[:9]
                    
                    columns.append({
                        'database': db_name,
                        'table_name': table_name,
                        'column_name': name,
                        'data_type': col_type,
                        'default_kind': default_kind or '',
                        'default_expression': default_expr or '',
                        'comment': comment or '',
                        'is_in_partition_key': bool(int(in_partition)) if in_partition.isdigit() else False,
                        'is_in_sorting_key': bool(int(in_sorting)) if in_sorting.isdigit() else False,
                        'is_in_primary_key': bool(int(in_primary)) if in_primary.isdigit() else False,
                        'is_in_sampling_key': bool(int(in_sampling)) if in_sampling.isdigit() else False
                    })
            
            return columns
            
        except Exception as e:
            print(f"获取表 '{table_name}' 字段信息失败: {e}")
            return []
    
    def get_table_partitions(self, table_name: str, database: str = None) -> List[Dict[str, Any]]:
        """
        获取表的分区信息
        
        Args:
            table_name: 表名
            database: 数据库名
            
        Returns:
            List[Dict]: 分区信息列表
        """
        db_name = database or self.database
        
        try:
            sql = f"""
            SELECT 
                partition,
                name,
                rows,
                bytes_on_disk,
                modification_time
            FROM system.parts 
            WHERE database = '{db_name}' AND table = '{table_name}' AND active = 1
            ORDER BY partition, name
            """
            
            result = self.execute_query(sql)
            if result is None:
                return []
            
            partitions = []
            for row in result:
                if len(row) >= 5:
                    partition, part_name, rows, bytes_disk, mod_time = row[0], row[1], row[2], row[3], row[4]
                    try:
                        rows = int(rows) if rows else 0
                        bytes_disk = int(bytes_disk) if bytes_disk else 0
                        size_mb = round(bytes_disk / 1024 / 1024, 2)
                    except:
                        rows = 0
                        bytes_disk = 0
                        size_mb = 0.0
                    
                    partitions.append({
                        'database': db_name,
                        'table_name': table_name,
                        'partition': partition,
                        'part_name': part_name,
                        'rows': rows,
                        'bytes_on_disk': bytes_disk,
                        'size_mb': size_mb,
                        'modification_time': mod_time
                    })
            
            return partitions
            
        except Exception as e:
            print(f"获取表 '{table_name}' 分区信息失败: {e}")
            return []
    
    def test_sample_data(self, table_name: str, database: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取表的样本数据
        
        Args:
            table_name: 表名
            database: 数据库名
            limit: 样本数量限制
            
        Returns:
            List[Dict]: 样本数据
        """
        db_name = database or self.database
        
        try:
            sql = f"SELECT * FROM {db_name}.{table_name} LIMIT {limit}"
            result = self.execute_query(sql)
            if result is None:
                return []
            
            # 获取列名
            columns_info = self.get_table_columns(table_name, database)
            column_names = [col['column_name'] for col in columns_info]
            
            samples = []
            for i, row in enumerate(result):
                sample = {'database': db_name, 'table_name': table_name, 'sample_row': i + 1}
                for j, value in enumerate(row):
                    if j < len(column_names):
                        sample[column_names[j]] = str(value) if value is not None else 'NULL'
                samples.append(sample)
            
            return samples
            
        except Exception as e:
            print(f"获取表 '{table_name}' 样本数据失败: {e}")
            return []
    
    def generate_full_report(self, output_dir: str = ".") -> bool:
        """
        生成完整的数据库结构报告
        
        Args:
            output_dir: 输出目录
            
        Returns:
            bool: 是否成功生成报告
        """
        if not self.connect():
            return False
        
        print("=== 开始生成ClickHouse数据库结构报告 ===")
        
        # 创建报告目录
        reports_dir = os.path.join(output_dir, "ck-db-analysis-reports")
        os.makedirs(reports_dir, exist_ok=True)
        print(f"报告将保存到: {reports_dir}")
        
        timestamp = datetime.now().strftime("%Y%m%d")
        
        try:
            # 1. 获取数据库列表
            databases = self.get_databases()
            
            # 2. 获取所有表信息
            all_tables = []
            all_columns = []
            all_partitions = []
            all_samples = []
            
            for db_name in databases:
                # 跳过系统数据库（可选）
                if db_name in ['system', 'information_schema', 'INFORMATION_SCHEMA']:
                    continue
                
                print(f"\n检查数据库: {db_name}")
                tables = self.get_tables(db_name)
                all_tables.extend(tables)
                
                for table_info in tables:
                    table_name = table_info['table_name']
                    print(f"  检查表: {table_name}")
                    
                    # 获取字段信息
                    columns = self.get_table_columns(table_name, db_name)
                    all_columns.extend(columns)
                    
                    # 获取分区信息
                    partitions = self.get_table_partitions(table_name, db_name)
                    all_partitions.extend(partitions)
                    
                    # 获取样本数据（如果表不为空）
                    if table_info['total_rows'] > 0:
                        samples = self.test_sample_data(table_name, db_name, limit=3)
                        all_samples.extend(samples)
            
            # 3. 生成CSV报告
            report_files = []
            
            # 数据库概览
            if databases:
                db_overview_file = os.path.join(reports_dir, f"clickhouse_databases_{timestamp}.csv")
                with open(db_overview_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['database_name', 'inspection_time'])
                    for db in databases:
                        writer.writerow([db, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                report_files.append(db_overview_file)
                print(f"数据库概览报告: {db_overview_file}")
            
            # 表信息报告
            if all_tables:
                tables_file = os.path.join(reports_dir, f"clickhouse_tables_{timestamp}.csv")
                df_tables = pd.DataFrame(all_tables)
                df_tables.to_csv(tables_file, index=False, encoding='utf-8')
                report_files.append(tables_file)
                print(f"表信息报告: {tables_file}")
            
            # 字段结构报告
            if all_columns:
                columns_file = os.path.join(reports_dir, f"clickhouse_columns_{timestamp}.csv")
                df_columns = pd.DataFrame(all_columns)
                df_columns.to_csv(columns_file, index=False, encoding='utf-8')
                report_files.append(columns_file)
                print(f"字段结构报告: {columns_file}")
            
            # 分区信息报告
            if all_partitions:
                partitions_file = os.path.join(reports_dir, f"clickhouse_partitions_{timestamp}.csv")
                df_partitions = pd.DataFrame(all_partitions)
                df_partitions.to_csv(partitions_file, index=False, encoding='utf-8')
                report_files.append(partitions_file)
                print(f"分区信息报告: {partitions_file}")
            
            # 样本数据报告
            if all_samples:
                samples_file = os.path.join(reports_dir, f"clickhouse_samples_{timestamp}.csv")
                df_samples = pd.DataFrame(all_samples)
                df_samples.to_csv(samples_file, index=False, encoding='utf-8')
                report_files.append(samples_file)
                print(f"样本数据报告: {samples_file}")
            
            # 生成汇总报告
            summary_file = os.path.join(reports_dir, f"clickhouse_summary_{timestamp}.csv")
            with open(summary_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['项目', '数量', '详细信息'])
                writer.writerow(['检查时间', 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(['服务器地址', 1, f"{self.host}:{self.port}"])
                writer.writerow(['数据库总数', len(databases), ', '.join(databases)])
                writer.writerow(['表总数', len(all_tables), ''])
                writer.writerow(['字段总数', len(all_columns), ''])
                writer.writerow(['分区总数', len(all_partitions), ''])
                writer.writerow(['生成的报告文件', len(report_files), '; '.join(os.path.basename(f) for f in report_files)])
            
            report_files.append(summary_file)
            print(f"汇总报告: {summary_file}")
            
            print("\n=== 报告生成完成 ===")
            print(f"共生成 {len(report_files)} 个报告文件:")
            for file in report_files:
                print(f"  - {os.path.basename(file)}")
            
            return True
            
        except Exception as e:
            print(f"生成报告时出错: {e}")
            return False
        finally:
            # HTTP连接无需手动关闭
            print("数据库检查完成")
    
    def test_connection_and_basic_info(self) -> bool:
        """
        测试连接并显示基本信息
        
        Returns:
            bool: 测试是否成功
        """
        print("=== ClickHouse连接测试 ===")
        
        if not self.connect():
            return False
        
        try:
            # 基本信息测试
            print("\n基本信息:")
            
            # 获取版本信息
            version_result = self.execute_query('SELECT version()')
            if version_result:
                print(f"ClickHouse版本: {version_result[0][0]}")
            
            # 获取当前时间
            time_result = self.execute_query('SELECT now()')
            if time_result:
                print(f"服务器时间: {time_result[0][0]}")
            
            # 获取数据库列表
            databases = self.get_databases()
            print(f"可用数据库: {len(databases)} 个")
            
            # 获取当前数据库的表数量
            tables = self.get_tables()
            print(f"当前数据库表数量: {len(tables)} 个")
            
            if tables:
                print("\n表列表:")
                for table in tables[:5]:  # 只显示前5个
                    print(f"  - {table['table_name']} ({table['engine']}) - " +
                          f"{table['total_rows']} 行, {table['size_mb']} MB")
                if len(tables) > 5:
                    print(f"  ... 还有 {len(tables) - 5} 个表")
            
            print("\n连接测试成功！")
            return True
            
        except Exception as e:
            print(f"测试过程中出错: {e}")
            return False


def main():
    """
    主函数 - 演示用法
    """
    # 创建检查器实例
    inspector = ClickHouseInspector(
        host='192.168.50.30',
        port=8123,
        database='default',
        user='default',
        password='er3HsdSE2dQIS^VI'
    )
    
    print("=== ClickHouse数据库结构检查器 ===")
    
    # 先进行连接测试
    if inspector.test_connection_and_basic_info():
        print("\n是否生成完整的结构报告? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes', '是', '1']:
                inspector.generate_full_report()
            else:
                print("跳过完整报告生成。")
        except KeyboardInterrupt:
            print("\n\n用户取消操作。")
    else:
        print("连接测试失败，请检查数据库连接参数。")


def main_with_args():
    """
    命令行参数主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ClickHouse数据库结构检查器')
    parser.add_argument('--host', default='192.168.50.30', help='ClickHouse主机地址')
    parser.add_argument('--port', type=int, default=8123, help='ClickHouse端口')
    parser.add_argument('--database', default='default', help='数据库名')
    parser.add_argument('--user', default='default', help='用户名')
    parser.add_argument('--password', default='er3HsdSE2dQIS^VI', help='密码')
    parser.add_argument('--output', '-o', default='.', help='输出目录')
    parser.add_argument('--test-only', action='store_true', help='仅执行连接测试')
    
    args = parser.parse_args()
    
    # 创建检查器
    inspector = ClickHouseInspector(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    )
    
    if args.test_only:
        inspector.test_connection_and_basic_info()
    else:
        if inspector.test_connection_and_basic_info():
            inspector.generate_full_report(args.output)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main_with_args()
    else:
        main()
