#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIS文件批量处理器 - ClickHouse数据库批量导入工具
==============================================

功能概述:
--------
批量检测指定目录下的所有HIS文件,并自动调用his_to_clickhouse.py
进行逐个文件的数据导入处理。支持单线程/多线程处理、日志记录和详细的进度监控。

使用说明:
--------
    支持的参数:
    --dir/-d: 数据文件目录 (默认: ./his-data)
    --method/-m: 插入方法 (values/csv, 默认: values)
    --host: ClickHouse服务器地址 (默认: 192.168.50.30)
    --port: ClickHouse端口 (默认: 8123)
    --database: 数据库名称 (默认: ezhou)
    --log-dir: 日志文件目录 (默认: ./logs)
    --retry: 失败重试次数 (默认: 1)
    --threads/-t: 文件级并发线程数 (默认: 1, 推荐: 4)
    --point-threads: 数据点级线程数 (默认: 1, 推荐: 2-4)
    --listfiles: 列出所有可用文件并退出
    --files: 指定要处理的文件前缀列表（空格分隔）
    --points: 指定要处理的数据点列表（逗号分隔）

    使用示例:
    1. 批量处理默认目录 (单线程):
       python batch_his_files_to_ck.py

    2. 列出所有可用文件:
       python batch_his_files_to_ck.py --listfiles

    3. 文件级多线程处理:
       python batch_his_files_to_ck.py --threads 4

    4. 数据点级多线程处理:
       python batch_his_files_to_ck.py --point-threads 4

    5. 双重多线程处理 (最佳性能):
       python batch_his_files_to_ck.py --threads 4 --point-threads 4

    6. 处理指定文件:
       python batch_his_files_to_ck.py --files 2025070222 2025070221

    7. 处理指定数据点:
       python batch_his_files_to_ck.py --points "SYS_XCU001_Memory,SYS_XCU101_AN_OFF"

    8. 指定文件+指定数据点+双重多线程:
       python batch_his_files_to_ck.py --files 2025070222 --points "point1,point2" --threads 2 --point-threads 2

作者: zhengxu
版本: 1.0
创建: 2025-07-30
"""

import os
import sys
import time
import glob
import argparse
import io
import contextlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Tuple, Dict
from pathlib import Path

# 导入HisToClickHouseParser类
try:
    from his_to_clickhouse import HisToClickHouseParser
except ImportError:
    print("[ERROR] 无法导入his_to_clickhouse模块")
    sys.exit(1)


class BatchHisProcessor:
    """
    批量HIS文件处理器

    负责:
    1. 文件发现和验证
    2. 批量处理调度
    3. 日志管理
    4. 进度监控
    """

    def __init__(self, data_dir: str = "./his-data", log_dir: str = "./logs",
                 method: str = "values", host: str = "192.168.50.30",
                 port: int = 8123, database: str = "ezhou", retry: int = 1,
                 target_files: List[str] = None, target_points: List[str] = None,
                 max_workers: int = 1, point_threads: int = 1):

        self.data_dir = Path(data_dir).resolve()
        self.log_dir = Path(log_dir).resolve()
        self.method = method
        self.host = host
        self.port = port
        self.database = database
        self.retry = retry
        self.target_files = target_files  # 指定要处理的文件列表
        self.target_points = target_points  # 指定要处理的数据点列表
        if max_workers < 1:
            print("[ERROR] 线程数必须 >= 1, 已设置为1")
            max_workers = 1
        elif max_workers > 4:
            print(f"[WARN] 线程数过高 ({max_workers}), 一设置为4个线程")
            max_workers = 4
        self.max_workers = max_workers

        # 处理单个文件内数据点的线程数
        if point_threads < 1:
            print("[ERROR] 数据点线程数必须 >= 1, 已设置为1")
            point_threads = 1
        elif point_threads > 4:
            print(f"[WARN] 数据点线程数过高 ({point_threads}), 已设置为4个线程")
            point_threads = 4
        self.point_threads = point_threads

        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)

        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"batch_process_{timestamp}.log"

        # 统计信息 - 添加线程安全的锁
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'start_time': None,
            'skipped_files': 0
        }
        self.stats_lock = threading.Lock()  # 统计信息的线程锁

    @contextlib.contextmanager
    def _capture_output_to_log(self, file_prefix: str):
        """
        上下文管理器: 捕获stdout输出并记录到日志文件
        同时保持控制台输出
        """
        # 创建一个StringIO对象来捕获输出
        captured_output = io.StringIO()

        # 保存原始的stdout
        original_stdout = sys.stdout

        class TeeOutput:
            """同时输出到控制台和捕获缓冲区的类"""
            def write(self, text):
                original_stdout.write(text)  # 输出到控制台
                captured_output.write(text)  # 捕获到缓冲区

            def flush(self):
                original_stdout.flush()
                captured_output.flush()

        try:
            # 重定向stdout到TeeOutput
            sys.stdout = TeeOutput()
            yield
        finally:
            # 恢复原始stdout
            sys.stdout = original_stdout

            # 获取捕获的输出并记录到日志
            output_content = captured_output.getvalue()
            if output_content.strip():
                self._log(f"--- {file_prefix} 处理输出 ---")
                self._log(output_content.rstrip())
                self._log(f"--- {file_prefix} 输出结束 ---")

    def discover_his_files(self) -> List[Tuple[str, str]]:
        """
        发现数据目录中的所有HIS文件对

        Returns:
            List[Tuple[str, str]]: (file_prefix, his_file_path) 的列表
        """
        print(f"[SCAN] 扫描目录: {self.data_dir}")
        self._log(f"开始扫描目录: {self.data_dir}")

        # 查找所有.his文件
        his_pattern = str(self.data_dir / "*.his")
        his_files = glob.glob(his_pattern)

        if not his_files:
            print(f"[ERROR] 在目录 {self.data_dir} 中未找到任何.his文件")
            self._log("错误: 未找到.his文件")
            return []

        # 验证每个HIS文件是否有对应的IDX文件
        all_valid_files = []
        for his_file in his_files:
            his_path = Path(his_file)
            file_prefix = his_path.stem  # 文件名(不含扩展名)
            idx_file = his_path.parent / f"{file_prefix}.idx"

            if idx_file.exists():
                all_valid_files.append((file_prefix, str(his_path)))
            else:
                print(f"[WARN] 跳过 {file_prefix}: 缺少对应的.idx文件")
                self._log(f"警告: {file_prefix} 缺少.idx文件,已跳过")
                self.stats['skipped_files'] += 1

        # 如果指定了target_files，则只返回匹配的文件
        if self.target_files:
            filtered_files = []
            found_files = set()

            for file_prefix, his_path in all_valid_files:
                if file_prefix in self.target_files:
                    filtered_files.append((file_prefix, his_path))
                    found_files.add(file_prefix)
                    print(f"[OK] 找到指定文件: {file_prefix}")

            # 检查是否有指定的文件未找到
            missing_files = set(self.target_files) - found_files
            if missing_files:
                print(f"[WARN] 未找到指定文件: {', '.join(missing_files)}")
                self._log(f"警告: 未找到指定文件: {', '.join(missing_files)}")

            valid_files = filtered_files
        else:
            valid_files = all_valid_files
            for file_prefix, _ in valid_files:
                print(f"[OK] 发现有效文件对: {file_prefix}")

        print(f"[STATS] 将处理 {len(valid_files)} 个有效文件对, {self.stats['skipped_files']} 个文件被跳过")
        self._log(f"文件发现完成: {len(valid_files)} 个有效文件对")

        return valid_files

    def list_all_files(self) -> List[str]:
        """
        列出所有可用的HIS文件前缀

        Returns:
            List[str]: 文件前缀列表
        """
        print(f"[SCAN] 扫描目录: {self.data_dir}")

        # 查找所有.his文件
        his_pattern = str(self.data_dir / "*.his")
        his_files = glob.glob(his_pattern)

        if not his_files:
            print(f"[ERROR] 在目录 {self.data_dir} 中未找到任何.his文件")
            return []

        # 验证每个HIS文件是否有对应的IDX文件
        valid_files = []
        missing_idx_files = []

        for his_file in his_files:
            his_path = Path(his_file)
            file_prefix = his_path.stem
            idx_file = his_path.parent / f"{file_prefix}.idx"

            if idx_file.exists():
                valid_files.append(file_prefix)
            else:
                missing_idx_files.append(file_prefix)

        print(f"\n[INFO] 发现 {len(valid_files)} 个有效文件对:")
        print("=" * 60)

        for i, file_prefix in enumerate(sorted(valid_files), 1):
            print(f"  {i:3d}. {file_prefix}")

        if missing_idx_files:
            print(f"\n[WARN] {len(missing_idx_files)} 个文件缺少对应的.idx文件:")
            for file_prefix in sorted(missing_idx_files):
                print(f"     [ERROR] {file_prefix}")

        print("=" * 60)
        print(f"总计: {len(valid_files)} 个有效文件, {len(missing_idx_files)} 个无效文件")

        return valid_files

    def process_single_file(self, file_prefix: str, attempt: int = 1) -> bool:
        """
        处理单个HIS文件

        Args:
            file_prefix: 文件前缀
            attempt: 尝试次数

        Returns:
            bool: 处理是否成功
        """
        print(f"\n[START] 处理文件: {file_prefix} (尝试 {attempt}/{self.retry + 1})")
        self._log(f"开始处理文件: {file_prefix} (尝试 {attempt})")

        try:
            # 创建HisToClickHouseParser实例
            clickhouse_parser = HisToClickHouseParser(
                host=self.host,
                port=self.port,
                database=self.database,
                user='default',
                password='er3HsdSE2dQIS^VI'
            )

            # 执行处理并捕获输出
            start_time = time.time()

            # 使用上下文管理器捕获输出到日志
            with self._capture_output_to_log(file_prefix):
                # 直接调用parse_points_to_clickhouse方法
                success = clickhouse_parser.parse_points_to_clickhouse(
                    directory=str(self.data_dir),
                    file_prefix=file_prefix,
                    point_names=self.target_points,
                    insert_method=self.method,
                    max_workers=self.point_threads
                )

            elapsed = time.time() - start_time

            # 记录处理结果
            if success:
                print(f"[OK] {file_prefix} 处理成功 (耗时: {elapsed:.1f}秒)")
                self._log(f"文件 {file_prefix} 处理成功, 耗时: {elapsed:.1f}秒")
                return True
            else:
                print(f"[ERROR] {file_prefix} 处理失败")
                self._log(f"文件 {file_prefix} 处理失败")
                return False

        except Exception as e:
            print(f"[ERROR] {file_prefix} 处理异常: {e}")
            self._log(f"文件 {file_prefix} 处理异常: {e}")
            return False

    def process_all_files(self) -> bool:
        """
        批量处理所有文件 - 支持单线程和多线程

        Returns:
            bool: 整体处理是否成功
        """
        # 发现文件
        file_pairs = self.discover_his_files()
        if not file_pairs:
            return False

        self.stats['total_files'] = len(file_pairs)
        self.stats['start_time'] = time.time()

        processing_mode = "多线程" if self.max_workers > 1 else "单线程"
        print(f"\n开始批量处理 {len(file_pairs)} 个文件 ({processing_mode})")
        print(f"插入方法: {self.method.upper()}")
        print(f"目标数据库: {self.host}:{self.port}/{self.database}")
        print(f"日志文件: {self.log_file}")

        if self.max_workers > 1:
            print(f"线程数: {self.max_workers}")

        if self.point_threads > 1:
            print(f"数据点线程数: {self.point_threads}")

        if self.target_files:
            print(f"指定文件: {', '.join(self.target_files)}")
        else:
            print("处理模式: 全部文件")

        if self.target_points:
            print(f"指定数据点: {', '.join(self.target_points)}")
        else:
            print("数据点模式: 全部数据点")

        print("=" * 60)

        self._log("=" * 60)
        self._log(f"批量处理开始: {len(file_pairs)} 个文件 ({processing_mode})")
        self._log(f"插入方法: {self.method}")
        self._log(f"目标数据库: {self.host}:{self.port}/{self.database}")
        if self.max_workers > 1:
            self._log(f"线程数: {self.max_workers}")
        if self.point_threads > 1:
            self._log(f"数据点线程数: {self.point_threads}")
        if self.target_files:
            self._log(f"指定文件: {', '.join(self.target_files)}")
        if self.target_points:
            self._log(f"指定数据点: {', '.join(self.target_points)}")
        self._log("=" * 60)

        if self.max_workers == 1:
            # 单线程处理
            return self._process_files_single_thread(file_pairs)
        else:
            # 多线程处理
            return self._process_files_multi_thread(file_pairs)

    def _process_files_single_thread(self, file_pairs: List[Tuple[str, str]]) -> bool:
        """单线程处理文件"""
        for i, (file_prefix, his_path) in enumerate(file_pairs, 1):
            print(f"\n[FOLDER] [{i}/{len(file_pairs)}] 当前处理: {file_prefix}")

            success = False
            for attempt in range(1, self.retry + 2):  # 原始尝试 + 重试次数
                success = self.process_single_file(file_prefix, attempt)
                if success:
                    break
                elif attempt <= self.retry:
                    print(f"[RETRY] 准备重试 {file_prefix} (剩余重试次数: {self.retry + 1 - attempt})")
                    time.sleep(2)  # 重试前等待2秒

            # 更新统计
            self.stats['processed_files'] += 1
            if success:
                self.stats['successful_files'] += 1
            else:
                self.stats['failed_files'] += 1

            # 显示进度
            self._print_progress()

        # 最终统计
        self._print_final_stats()
        return self.stats['failed_files'] == 0

    def _process_files_multi_thread(self, file_pairs: List[Tuple[str, str]]) -> bool:
        """多线程处理文件"""
        print(f"[MULTI-THREAD] 使用 {self.max_workers} 个线程并行处理")

        # 创建线程池
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {}
            for i, (file_prefix, his_path) in enumerate(file_pairs, 1):
                future = executor.submit(self._process_file_with_retry, file_prefix, i, len(file_pairs))
                future_to_file[future] = file_prefix

            # 等待所有任务完成
            completed_count = 0
            for future in as_completed(future_to_file):
                file_prefix = future_to_file[future]
                completed_count += 1

                try:
                    future.result()  # 获取结果以确保异常被捕获
                    # 显示进度 (线程安全)
                    with self.stats_lock:
                        processed = self.stats['processed_files']
                        total = self.stats['total_files']
                        successful = self.stats['successful_files']
                        failed = self.stats['failed_files']
                        percentage = (processed / total) * 100
                        print(f"[MULTI-THREAD] 进度: [{processed}/{total}] {percentage:.1f}% | "
                              f"OK:{successful} ERROR:{failed}")

                except Exception as e:
                    print(f"[MULTI-THREAD] [ERROR] {file_prefix} 处理异常: {e}")
                    self._log(f"线程处理异常: {file_prefix} - {e}")
                    self._update_stats(processed=True, failed=True)

        # 最终统计
        self._print_final_stats()
        return self.stats['failed_files'] == 0

    def _print_progress(self):
        """打印处理进度"""
        processed = self.stats['processed_files']
        total = self.stats['total_files']
        successful = self.stats['successful_files']
        failed = self.stats['failed_files']

        if total > 0:
            percentage = (processed / total) * 100
            print(f"[STATS] 进度: [{processed}/{total}] {percentage:.1f}% | "
                  f"OK:{successful} ERROR:{failed}")

    def _print_final_stats(self):
        """打印最终统计信息"""
        end_time = time.time()
        total_elapsed = end_time - self.stats['start_time']

        print("\n" + "=" * 60)
        print("[SUCCESS] 批量处理完成统计")
        print("=" * 60)
        print(f"[TIME] 总耗时: {total_elapsed:.1f} 秒 ({total_elapsed / 60:.1f} 分钟)")
        print(f"[FILE] 总文件数: {self.stats['total_files']}")
        print(f"[OK] 成功处理: {self.stats['successful_files']}")
        print(f"[ERROR] 失败处理: {self.stats['failed_files']}")
        print(f"[SKIP] 跳过文件: {self.stats['skipped_files']}")
        print(f"[RATE] 成功率: {(self.stats['successful_files'] / max(1, self.stats['total_files']) * 100):.1f}%")
        print(f"[LOG] 详细日志: {self.log_file}")

        if total_elapsed > 0:
            files_per_min = (self.stats['processed_files'] / total_elapsed) * 60
            print(f"[SPEED] 处理速度: {files_per_min:.1f} 文件/分钟")

        print("=" * 60)

        # 记录到日志
        self._log("=" * 60)
        self._log("批量处理完成统计")
        self._log(f"总耗时: {total_elapsed:.1f} 秒")
        self._log(f"总文件数: {self.stats['total_files']}")
        self._log(f"成功处理: {self.stats['successful_files']}")
        self._log(f"失败处理: {self.stats['failed_files']}")
        self._log(f"成功率: {(self.stats['successful_files'] / max(1, self.stats['total_files']) * 100):.1f}%")
        self._log("=" * 60)

    def _log(self, message: str):
        """写入日志文件 - 线程安全版本"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # 使用文件锁确保多线程写入安全
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def _update_stats(self, processed: bool = False, successful: bool = False, failed: bool = False):
        """线程安全的统计信息更新"""
        with self.stats_lock:
            if processed:
                self.stats['processed_files'] += 1
            if successful:
                self.stats['successful_files'] += 1
            if failed:
                self.stats['failed_files'] += 1

    def _process_file_with_retry(self, file_prefix: str, file_index: int, total_files: int) -> bool:
        """
        带重试机制的文件处理方法 - 线程安全版本

        Args:
            file_prefix: 文件前缀
            file_index: 文件在列表中的索引 (从1开始)
            total_files: 总文件数

        Returns:
            bool: 处理是否成功
        """
        thread_id = threading.current_thread().name
        print(f"\n[THREAD-{thread_id}] [{file_index}/{total_files}] 开始处理: {file_prefix}")

        success = False
        for attempt in range(1, self.retry + 2):  # 原始尝试 + 重试次数
            success = self.process_single_file(file_prefix, attempt)
            if success:
                break
            elif attempt <= self.retry:
                print(f"[THREAD-{thread_id}] [RETRY] 准备重试 {file_prefix} (剩余重试次数: {self.retry + 1 - attempt})")
                time.sleep(2)  # 重试前等待2秒

        # 线程安全的统计更新
        self._update_stats(processed=True, successful=success, failed=not success)

        if success:
            print(f"[THREAD-{thread_id}] [OK] {file_prefix} 处理完成")
        else:
            print(f"[THREAD-{thread_id}] [ERROR] {file_prefix} 处理失败")

        return success


def main():
    parser = argparse.ArgumentParser(
        description='HIS文件批量处理器 - ClickHouse数据库批量导入',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                                    # 处理默认目录下所有文件 (单线程)
  %(prog)s --threads 4                        # 使用4个线程并行处理文件
  %(prog)s --point-threads 2                  # 单个文件内用2线程处理数据点
  %(prog)s --threads 4 --point-threads 2      # 4线程处理文件,每文件2线程处理数据点
  %(prog)s --listfiles                        # 列出所有可用文件
  %(prog)s --files 2025070222 2025070221      # 处理指定文件
  %(prog)s --points "point1,point2"           # 处理指定数据点
  %(prog)s --files 2025070222 --points "p1"   # 处理指定文件的指定数据点
  %(prog)s --dir /data/his --method csv       # 指定目录和插入方法
  %(prog)s --host 192.168.1.100 --retry 2    # 指定服务器和重试次数
        """
    )

    parser.add_argument('--dir', '-d', default='./his-data',
                        help='数据文件目录 (默认: ./his-data)')
    parser.add_argument('--method', '-m', choices=['values', 'csv'], default='values',
                        help='插入方法: values(标准SQL) 或 csv(CSV格式) (默认: values)')
    parser.add_argument('--host', default='192.168.50.30',
                        help='ClickHouse服务器地址 (默认: 192.168.50.30)')
    parser.add_argument('--port', type=int, default=8123,
                        help='ClickHouse端口 (默认: 8123)')
    parser.add_argument('--database', default='ezhou',
                        help='数据库名称 (默认: ezhou)')
    parser.add_argument('--log-dir', default='./logs',
                        help='日志文件目录 (默认: ./logs)')
    parser.add_argument('--retry', type=int, default=1,
                        help='失败重试次数 (默认: 1)')
    parser.add_argument('--listfiles', action='store_true',
                        help='列出所有可用文件并退出')
    parser.add_argument('--files', nargs='*',
                        help='指定要处理的文件前缀列表 (例: --files 2025070222 2025070221)')
    parser.add_argument('--threads', '-t', type=int, default=1,
                        help='并发线程数 (默认: 1, 单线程; 推荐多线程值: 4)')
    parser.add_argument('--point-threads', type=int, default=1,
                        help='单个文件内数据点处理线程数 (默认: 1, 推荐: 2-4)')
    parser.add_argument('--points',
                        help='指定数据点列表, 逗号分隔 (例: "point1,point2,point3")')

    args = parser.parse_args()

    try:
        # 检查数据目录是否存在
        if not Path(args.dir).exists():
            print(f"[ERROR] 错误: 数据目录不存在: {args.dir}")
            sys.exit(1)

        # 验证线程数
        if args.threads < 1:
            print(f"[ERROR] 线程数必须 >= 1, 当前值: {args.threads}")
            sys.exit(1)

        if args.threads > 8:
            print(f"[WARN] 线程数过高 ({args.threads}), 建议不超过8个线程")

        # 处理--points参数
        target_points = None
        if args.points:
            target_points = [p.strip() for p in args.points.split(',') if p.strip()]
            print(f"[TARGET] 用户指定了 {len(target_points)} 个数据点")

        # 创建批量处理器
        processor = BatchHisProcessor(
            data_dir=args.dir,
            log_dir=args.log_dir,
            method=args.method,
            host=args.host,
            port=args.port,
            database=args.database,
            retry=args.retry,
            target_files=args.files,
            target_points=target_points,
            max_workers=args.threads,
            point_threads=args.point_threads
        )

        # 如果只是列出文件
        if args.listfiles:
            print("[START] === HIS文件列表 ===")
            processor.list_all_files()
            return        # 开始批量处理
        print("[START] === HIS文件批量处理器 ===")
        success = processor.process_all_files()

        if success:
            print("\n[SUCCESS] 所有文件处理成功！")
            sys.exit(0)
        else:
            print("\n[WARN] 部分文件处理失败，请检查日志文件")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[STOP] 用户中断批量处理")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 批量处理过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
