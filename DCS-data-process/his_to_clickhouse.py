#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIS历史数据到ClickHouse数据库导入器
==================================================

功能概述:
--------
本工具继承自HisDataParser类, 专门用于将解析的HIS历史数据直接写入ClickHouse数据库。


使用说明:
--------
    支持的参数:
    --file/-f: 文件前缀 (默认: 2025070222)
    --dir/-d: 数据目录 (默认: ./his-data)
    --points/-p: 指定数据点列表（逗号分隔）
    --list/-l: 列出所有可用数据点
    --limit: 限制处理的数据点数量（用于测试）

    使用示例:
    1. 处理所有数据点:
       python his_to_clickhouse.py

    2. 处理指定数据点:
       python his_to_clickhouse.py --points "SYS_XCU001_Memory,SYS_XCU001_CPULoad"

    3. 列出可用数据点:
       python his_to_clickhouse.py --list

    4. 测试模式(只处理前10个数据点):
       python his_to_clickhouse.py --limit 10


核心特性:
--------
- 继承原有解析功能:复用HisDataParser的解析能力
- ClickHouse连接管理:支持连接池和自动重连
- 数据类型映射:自动处理Python到ClickHouse的类型转换


数据库设计:使用现有数据库表结构,进行数据插入
----------
table字段:
- point_code: String - 数据点代码
- point_value: Float64 - 数值
- date_time: DateTime - 时间戳
- point_type: Int8 - 数据点类型
- param_code String - 参数代码(一般为空)


作者: zhengxu
版本: 2.2
创建: 2025-07-30
"""

import os
import sys
import time
import struct
import requests
import traceback
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# 导入基础解析器
try:
    from parse_his_data import HisDataParser, PointInfo
except ImportError:
    print("错误: 无法导入parse_his_data模块")
    sys.exit(1)


class HisToClickHouseParser(HisDataParser):
    """
    1. 数据库连接管理:维护ClickHouse连接池
    2. 表结构管理:自动创建和维护数据表
    3. 批量数据写入:批量插入操作
    4. 数据类型转换:Python对象到ClickHouse类型的自动映射
    """

    def __init__(self, host='192.168.50.30', port=8123, database='ezhou',
                 user='default', password='er3HsdSE2dQIS^VI'):

        super().__init__()

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

        self.base_url = f"http://{host}:{port}"
        self.auth = (user, password)

        # 统计信息
        self.stats = {
            'total_points': 0,
            'processed_points': 0,
            'successful_points': 0,
            'failed_points': 0,
            'total_records': 0,
            'start_time': None,
            'idx_parse_time': 0
        }

    def _execute_clickhouse_query(self, query: str, retries: int = 3) -> Optional[str]:
        """执行ClickHouse指令"""
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{self.base_url}/{self.database}",
                    data=query,
                    auth=self.auth,
                    headers={'Content-Type': 'text/plain; charset=utf-8'},
                    timeout=60  # 60秒超时
                )
                response.raise_for_status()
                return response.text.strip()
            except Exception as e:
                if attempt < retries - 1:
                    print(f"⚠️  查询失败 (尝试 {attempt + 1}/{retries}): {e}")
                    time.sleep(2)  # 等待2秒重试
                    continue
                else:
                    print(f"❌ ClickHouse查询最终失败: {e}")
                    return None

    def _test_connection(self) -> bool:
        """测试ClickHouse连接"""
        print("🔗 测试ClickHouse连接...")
        try:
            result = self._execute_clickhouse_query("SELECT 1")
            if result == "1":
                print(f"✅ ClickHouse连接成功: {self.base_url}/{self.database}")
                return True
            else:
                print("❌ ClickHouse连接失败: 返回结果异常")
                return False
        except Exception as e:
            print(f"❌ ClickHouse连接失败: {e}")
            return False

    def _ensure_table_exists(self) -> bool:
        """确保points_data表存在"""
        print("📋 检查数据表...")
        try:
            check_query = "SELECT 1 FROM points_data LIMIT 1"
            result = self._execute_clickhouse_query(check_query)

            if result is not None:
                print("✅ 表points_data已存在, 使用现有表结构")
                return True
            else:
                print("❌ 表points_data不存在")
                return False

        except Exception as e:
            print(f"❌ 检查表结构失败: {e}")
            return False

    def _insert_point_data(self, point_name: str, point_all_data: List) -> bool:
        """
        VALUES格式批量插入：使用标准SQL VALUES语法
        ==========================================

        1. 使用标准SQL VALUES语法，兼容性更好
        2. 批量构建VALUES语句，减少网络往返
        3. 直接使用数据类型，无需字符串格式化
        """
        try:
            if not point_all_data:
                print(f"⚠️  数据点 '{point_name}' 无时序数据, 跳过")
                return False

            total_records = len(point_all_data)
            if total_records > 8000:
                print(f"❌ 数据点 '{point_name}' 记录数过多 ({total_records}), 拒绝处理")
                return False

            # 构建VALUES子句列表
            values_parts = []
            for point in point_all_data:
                # 格式化时间戳为ClickHouse DateTime格式
                timestamp_str = point.date_time.strftime('%Y-%m-%d %H:%M:%S')
                # 构建单个VALUES元组，注意字符串需要引号，param_code使用空字符串
                value_tuple = f"('{point.point_code}', {point.point_value}, '{timestamp_str}', {point.point_type}, '')"
                values_parts.append(value_tuple)

            # 构建完整的INSERT语句
            insert_query = f"""INSERT INTO {self.database}.points_data
(point_code, point_value, date_time, point_type, param_code)
VALUES {','.join(values_parts)}"""

            # 使用统一的执行函数
            result = self._execute_clickhouse_query(insert_query)
            if result is not None:
                self.stats['total_records'] += total_records
                point_type = point_all_data[0].point_type
                print(f"✅ {point_name}: {total_records:,}条记录 (type={point_type}) [VALUES批量]")
                return True
            else:
                print(f"❌ 数据点 '{point_name}' VALUES插入失败")
                return False

        except Exception as e:
            print(f"❌ 数据点 '{point_name}' 处理失败: {e}")
            return False

    def _insert_point_csv_data(self, point_name: str, point_all_data: List) -> bool:
        """
        批量插入:直接使用StructPoint对象, 采用CSV格式批量插入
        ===============================================================

        - 使用CSV格式批量插入, 比VALUES语句更高效
        - 减少HTTP请求次数, 提升网络传输效率
        - ClickHouse对CSV格式有优化的解析器
        """
        try:
            if not point_all_data:
                print(f"⚠️  数据点 '{point_name}' 无时序数据, 跳过")
                return False

            total_records = len(point_all_data)
            if total_records > 3600:
                print(f"warning:  数据点 '{point_name}' 记录数过多 ({total_records})")

            # 构建CSV格式数据
            csv_lines = []
            for point in point_all_data:
                # CSV格式:point_code,point_value,date_time,point_type,param_code
                timestamp_str = point.date_time.strftime('%Y-%m-%d %H:%M:%S')
                csv_line = f"{point.point_code},{point.point_value},{timestamp_str},{point.point_type},"
                csv_lines.append(csv_line)

            # CSV数据
            csv_data = '\n'.join(csv_lines)

            # 使用INSERT FORMAT CSV进行批量插入
            insert_query = ("INSERT INTO points_data "
                            "(point_code, point_value, date_time, point_type, param_code) "
                            "FORMAT CSV")

            # 发送CSV数据
            try:
                response = requests.post(
                    f"{self.base_url}/{self.database}",
                    data=insert_query + '\n' + csv_data,
                    auth=self.auth,
                    headers={'Content-Type': 'text/plain; charset=utf-8'},
                    timeout=120  # CSV批量插入可能需要更长时间
                )
                response.raise_for_status()

                self.stats['total_records'] += total_records
                point_type = point_all_data[0].point_type
                print(f"✅ {point_name}: {total_records:,}条记录 (type={point_type}) [CSV批量]")
                return True

            except Exception as e:
                print(f"❌ CSV批量插入失败: {e}")
                return False

        except Exception as e:
            print(f"❌ 数据点 '{point_name}' 处理失败: {e}")
            return False

    def parse_points_to_clickhouse(self, directory: str, file_prefix: str,
                                   point_names: List[str] = None,
                                   insert_method: str = "values") -> bool:
        """
        数据点上传服务器:支持选择性处理指定数据点
        =============================================

        Args:
            directory: 数据文件目录
            file_prefix: 文件前缀
            point_names: 要处理的数据点列表, None表示处理全部
            insert_method: 插入方法 ("values" 或 "csv")
        """
        print("🚀 === HIS数据到ClickHouse批量导入 ===")
        print(f"📂 目标文件: {file_prefix}")
        print(f"🗄️  目标数据库: {self.database}")
        print(f"🔗 服务器: {self.host}:{self.port}")
        print(f"🔧 插入方法: {insert_method.upper()}")

        if point_names:
            print(f"🎯 指定处理: {len(point_names)} 个数据点")
        else:
            print("🎯 处理模式: 全部数据点")
        print()

        self.stats['start_time'] = time.time()

        try:
            # 1. 测试连接
            if not self._test_connection():
                return False

            # 2. 检查表结构
            if not self._ensure_table_exists():
                return False

            # 3. 解析IDX文件
            idx_filepath = os.path.join(directory, f"{file_prefix}.idx")
            if not self.idx_info_parser(idx_filepath):
                return False

            # 4. 确定要处理的数据点
            if point_names is None:
                # 处理所有数据点
                target_points = list(self._point_info_cache.keys())
                print(f"📋 将处理全部 {len(target_points):,} 个数据点")
            else:
                # 验证指定的数据点
                target_points = []
                invalid_points = []

                for point_name in point_names:
                    if point_name in self._point_info_cache:
                        target_points.append(point_name)
                    else:
                        invalid_points.append(point_name)

                if invalid_points:
                    print(f"⚠️  无效数据点 ({len(invalid_points)}个): {', '.join(invalid_points[:5])}")
                    if len(invalid_points) > 5:
                        print(f"    ... 还有 {len(invalid_points) - 5} 个")

                print(f"📋 将处理 {len(target_points)} 个有效数据点")

                if not target_points:
                    print("❌ 没有有效的数据点可处理")
                    return False

            self.stats['total_points'] = len(target_points)

            # 选择插入方法
            if insert_method.lower() == "values":
                print("🔧 优化策略: 直接StructPoint对象 + VALUES批量插入")
                insert_func = self._insert_point_data
            else:
                print("🔧 优化策略: 直接StructPoint对象 + CSV批量插入")
                insert_func = self._insert_point_csv_data
            print()

            # 5. 逐个处理数据点
            for i, point_name in enumerate(target_points, 1):
                try:
                    # 直接获取StructPoint对象, 无需转换
                    point_all_data = self.read_single_point_all_blocks(directory, file_prefix, point_name)

                    # 使用选定的插入方法
                    if point_all_data:
                        success = insert_func(point_name, point_all_data)
                        if success:
                            self.stats['successful_points'] += 1
                        else:
                            self.stats['failed_points'] += 1
                    else:
                        print(f"⚠️  [{i:,}/{len(target_points):,}] {point_name}: 无数据")
                        self.stats['failed_points'] += 1

                    self.stats['processed_points'] += 1

                    # 每10个点显示一次进度
                    if i % 10 == 0:
                        self._print_progress()

                except Exception as e:
                    print(f"❌ [{i:,}] {point_name} 处理失败: {e}")
                    self.stats['failed_points'] += 1
                    self.stats['processed_points'] += 1

            # 6. 最终统计
            self._print_final_stats()
            return True

        except Exception as e:
            print(f"❌ 批量处理失败: {e}")
            traceback.print_exc()
            return False

    def _print_progress(self):
        """打印详细进度"""
        processed = self.stats['processed_points']
        total = self.stats['total_points']
        successful = self.stats['successful_points']
        failed = self.stats['failed_points']
        records = self.stats['total_records']

        if total > 0:
            percentage = (processed / total) * 100

            # 计算预估剩余时间
            if processed > 0 and self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                avg_time_per_point = elapsed / processed
                remaining_points = total - processed
                eta_seconds = remaining_points * avg_time_per_point
                eta_minutes = eta_seconds / 60

                if eta_minutes > 60:
                    eta_str = f"{eta_minutes / 60:.1f}小时"
                else:
                    eta_str = f"{eta_minutes:.1f}分钟"

                points_per_sec = processed / elapsed if elapsed > 0 else 0

                print(f"📊 [{processed:,}/{total:,}] {percentage:.1f}% | "
                      f"✅{successful:,} ❌{failed:,} | "
                      f"📈{records:,}条记录 | "
                      f"⚡{points_per_sec:.1f}点/秒 | "
                      f"⏱️ 剩余{eta_str}")

    def _print_final_stats(self):
        """打印最终统计信息"""
        end_time = time.time()
        total_elapsed = end_time - self.stats['start_time']

        print("\n" + "=" * 60)
        print(f"⏱️  总耗时: {total_elapsed:.1f} 秒 ({total_elapsed / 60:.1f} 分钟)")
        print(f"📊 IDX解析耗时: {self.stats['idx_parse_time']:.2f} 秒")
        print(f"📊 数据处理耗时: {total_elapsed - self.stats['idx_parse_time']:.1f} 秒")
        print(f"📈 总数据点: {self.stats['total_points']:,}")
        print(f"✅ 成功处理: {self.stats['successful_points']:,}")
        print(f"❌ 失败处理: {self.stats['failed_points']:,}")
        print(f"📈 成功率: {(self.stats['successful_points'] / max(1, self.stats['total_points']) * 100):.1f}%")
        print(f"💾 总记录数: {self.stats['total_records']:,}")

        if total_elapsed > 0:
            points_per_sec = self.stats['processed_points'] / total_elapsed
            records_per_sec = self.stats['total_records'] / total_elapsed
            print(f"⚡ 处理速度: {points_per_sec:.1f} 数据点/秒")
            print(f"⚡ 插入速度: {records_per_sec:.1f} 记录/秒")

        print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='HIS历史数据到ClickHouse批量导入器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                                    # 处理所有数据点(VALUES方式)
  %(prog)s --points "point1,point2"          # 处理指定数据点
  %(prog)s --method csv                       # 使用CSV格式插入
  %(prog)s --method values                    # 使用VALUES格式插入(默认)
  %(prog)s --list                            # 列出所有数据点
  %(prog)s --limit 10                        # 测试模式, 只处理前10个
  %(prog)s --file 2025070223 --dir /data     # 指定文件和目录
        """
    )

    parser.add_argument('--file', '-f', default='2025070222',
                        help='文件前缀 (默认: 2025070222)')
    parser.add_argument('--dir', '-d', default='./his-data',
                        help='数据文件目录 (默认: ./his-data)')
    parser.add_argument('--points', '-p',
                        help='指定数据点列表, 逗号分隔 (例: "point1,point2,point3")')
    parser.add_argument('--list', '-l', action='store_true',
                        help='列出所有可用数据点并退出')
    parser.add_argument('--limit', type=int,
                        help='限制处理的数据点数量（用于测试）')
    parser.add_argument('--method', '-m', choices=['values', 'csv'], default='values',
                        help='插入方法: values(标准SQL) 或 csv(CSV格式) (默认: values)')
    parser.add_argument('--host', default='192.168.50.30',
                        help='ClickHouse服务器地址 (默认: 192.168.50.30)')
    parser.add_argument('--port', type=int, default=8123,
                        help='ClickHouse端口 (默认: 8123)')
    parser.add_argument('--database', default='ezhou',
                        help='数据库名称 (默认: ezhou)')

    args = parser.parse_args()

    try:
        # 创建解析器实例
        clickhouse_parser = HisToClickHouseParser(
            host=args.host,
            port=args.port,
            database=args.database,
            user='default',
            password='er3HsdSE2dQIS^VI'
        )

        # 如果只是列出数据点
        if args.list:
            print("🔍 正在解析IDX文件以获取数据点列表...")
            idx_filepath = os.path.join(args.dir, f"{args.file}.idx")

            if not os.path.exists(idx_filepath):
                print(f"❌ IDX文件不存在: {idx_filepath}")
                return

            if clickhouse_parser.idx_info_parser(idx_filepath):
                all_points = list(clickhouse_parser._point_info_cache.keys())
                print(f"\n📋 发现 {len(all_points)} 个数据点:")
                print("=" * 60)

                for i, point_name in enumerate(all_points, 1):
                    point_info = clickhouse_parser._point_info_cache[point_name]
                    point_type_str = "AX" if point_info.point_type == 0 else "DX"
                    print(f"  {i:4d}. {point_name} [{point_type_str}]")

                print("=" * 60)
                print(f"总计: {len(all_points)} 个数据点")
            else:
                print("❌ 解析IDX文件失败")
            return

        # 确定要处理的数据点
        target_points = None
        if args.points:
            # 解析指定的数据点
            target_points = [p.strip() for p in args.points.split(',') if p.strip()]
            print(f"🎯 用户指定了 {len(target_points)} 个数据点")
        elif args.limit:
            # 限制模式:先解析IDX获取数据点列表
            print(f"🧪 测试模式:限制处理前 {args.limit} 个数据点")
            idx_filepath = os.path.join(args.dir, f"{args.file}.idx")
            if clickhouse_parser.idx_info_parser(idx_filepath):
                all_points = list(clickhouse_parser._point_info_cache.keys())
                target_points = all_points[:args.limit]
                print(f"🎯 将处理前 {len(target_points)} 个数据点")
            else:
                print("❌ 解析IDX文件失败")
                return

        # 执行批量处理
        success = clickhouse_parser.parse_points_to_clickhouse(
            directory=args.dir,
            file_prefix=args.file,
            point_names=target_points,
            insert_method=args.method
        )

        if success:
            print("\n🎉 批量处理成功完成！")
        else:
            print("\n❌ 批量处理失败！")

    except KeyboardInterrupt:
        print("\n⏹️  用户中断处理")
    except Exception as e:
        print(f"\n❌ 处理过程中出错: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
