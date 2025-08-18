# -*- coding: utf-8 -*-
"""
HIS文件批量CSV导出
===========================================

功能概述:
--------
批量检测指定目录下的HIS文件, 按天分批处理，支持多线程处理；
时间范围限制（最多一个月）、数据点限制（最多20个点）依赖配置文件 his_config.json。

配置文件自动化:
--------------
程序启动时会自动检查 his_config.json 配置文件：
- 如果文件不存在, 自动生成配置文件模板并提示用户编辑
- 如果文件存在但格式错误, 给出错误提示并退出
- 如果配置有效, 自动加载参数并开始处理

使用说明:
--------
1. 首次运行：
   python batch_his_files_to_csv.py
   (会自动生成配置文件模板并退出)

2. 编辑配置文件：
   修改 his_config.json 中的参数

3. 再次运行：
   python batch_his_files_to_csv.py
   (自动读取配置并开始处理)

作者: zhengxu
版本: 2.0
创建: 2025-08-16
更新: 简化为纯配置文件驱动的自动化版本
"""

import os
import sys
import time
import glob
import csv
import threading
import logging
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from pathlib import Path
from collections import defaultdict

# 导入HisDataParser类
try:
    from parse_his_data import HisDataParser, PointDataStruct
except ImportError as e:
    print(f"错误: 无法导入parse_his_data模块: {e}")
    sys.exit(1)


class BatchHisToCsv:
    def __init__(self, config_file: str = "his_config.json"):
        """
        Args:
            config_file: 配置文件路径
        """
        print(f"[INIT] 初始化HIS数据批量CSV导出...")
        
        # 自动处理配置文件
        config = self._load_and_validate_config(config_file)
        
        # 从配置文件读取参数
        data_dir = config.get('data_dir', './his-data')
        output_dir = config.get('output_dir', './csv-output')
        target_points = config.get('target_points', [])
        days = config.get('days', 1)
        start_date = config.get('start_date', None)
        max_workers = config.get('max_workers', 4)
        point_threads = config.get('point_threads', 4)
        csv_format = config.get('csv_format', 'detailed')
        save_individual_points = config.get('save_individual_points', False)
        
        # 参数验证和设置
        self.data_dir = Path(data_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建日志目录
        self.log_dir = Path("./logs").resolve()
        self.log_dir.mkdir(exist_ok=True)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"HisToCsv_{timestamp}.log"
        
        # 设置高性能日志系统
        self._setup_logger()
        
        # 验证和限制数据点数量
        if target_points and len(target_points) > 20:
            self.logger.warning(f"数据点数量超过限制 ({len(target_points)}), 只处理前20个")
            target_points = target_points[:20]
        self.target_points = target_points
        
        # 验证和限制天数
        if days < 1 or days > 31:
            self.logger.error(f"天数必须在1-31之间, 当前值: {days}")
            days = max(1, min(31, days))
        self.days = days
        
        # 解析开始日期
        self.start_date = self._parse_start_date(start_date)
        
        # 线程数限制
        self.max_workers = max(1, min(4, max_workers))
        self.point_threads = max(1, min(4, point_threads))
        
        self.csv_format = csv_format
        self.save_individual_points = save_individual_points
        
        # 数据缓存池 - 内存中存储所有数据点的数据
        # 结构: {point_name: {file_prefix: [PointDataStruct, ...]}}
        self.data_cache = defaultdict(dict)
        self.cache_lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'total_days': 0,
            'processed_days': 0,
            'total_files': 0,
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'start_time': None
        }
        self.stats_lock = threading.Lock()
        
        # HIS解析器实例（每个线程独立）
        self._parser_cache = {}
        self._parser_lock = threading.Lock()
        
        # 初始化日志
        self.logger.info(f"HIS数据批量CSV导出初始化完成")
        self.logger.info(f"数据目录: {self.data_dir}")
        self.logger.info(f"输出目录: {self.output_dir}")
        self.logger.info(f"目标数据点: {target_points}")
        self.logger.info(f"处理天数: {self.days}")
        self.logger.info(f"开始日期: {self.start_date.strftime('%Y-%m-%d')}")
        self.logger.info(f"CSV格式: {self.csv_format}")
        self.logger.info(f"保存单个数据点文件: {self.save_individual_points}")
        self.logger.info(f"线程配置: 文件级{self.max_workers}, 数据点级{self.point_threads}")
        
        # 验证配置
        self._validate_configuration()
    
    @staticmethod
    def save_config_template(config_file: str = "his_config.json") -> None:
        """
        保存完整的配置文件模板
        
        Args:
            config_file: 配置文件路径
        """
        template_config = {
            "data_dir": "./his-data",
            "output_dir": "./csv-output",
            "target_points": [
                "SYS_XCU001_Memory",
                "20MCS-UNITMW"
            ],
            "days": 1,
            "start_date": "20250702",
            "max_workers": 4,
            "point_threads": 4,
            "csv_format": "detailed",
            "save_individual_points": False,
            "description": "HIS文件批量CSV导出配置文件",
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(template_config, f, ensure_ascii=False, indent=4)
            print(f"[SUCCESS] 配置文件模板已保存: {config_file}")
        except Exception as e:
            print(f"[ERROR] 保存配置文件模板失败: {e}")
    
    def _load_and_validate_config(self, config_file: str) -> dict:
        """
        加载和验证配置文件, 如果不存在则自动创建模板
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            dict: 配置字典
        """
        config_path = Path(config_file)
        
        # 如果配置文件不存在, 创建模板并提示用户
        if not config_path.exists():
            print(f"[INFO] 配置文件 {config_file} 不存在")
            print(f"[INFO] 正在创建默认配置文件模板...")
            
            self.save_config_template(config_file)
            
            print(f"[NOTICE] ==========================================")
            print(f"[NOTICE] 已自动生成配置文件: {config_file}")
            print(f"[NOTICE] 请编辑该文件设置您的参数:")
            print(f"[NOTICE] - data_dir: HIS数据文件目录")
            print(f"[NOTICE] - target_points: 要导出的数据点列表") 
            print(f"[NOTICE] - days: 处理天数 (1-31)")
            print(f"[NOTICE] 编辑完成后重新运行程序")
            print(f"[NOTICE] ==========================================")
            sys.exit(0)
        
        # 加载配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read().strip()
                if not config_content:
                    print(f"[ERROR] 配置文件 {config_file} 为空")
                    sys.exit(1)
                
                config = json.loads(config_content)
                print(f"[CONFIG] 已加载配置文件: {config_file}")
                return config
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] 配置文件 {config_file} 格式错误: {e}")
            print(f"[HINT] 请检查JSON格式是否正确")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] 读取配置文件 {config_file} 失败: {e}")
            sys.exit(1)
    
    def _validate_configuration(self):
        """验证配置的有效性"""
        # 检查数据目录
        if not self.data_dir.exists():
            self.logger.error(f"数据目录不存在: {self.data_dir}")
            print(f"[ERROR] 数据目录不存在: {self.data_dir}")
            print(f"[HINT] 请在配置文件中设置正确的 data_dir 路径")
            sys.exit(1)
        
        # 检查数据点
        if not self.target_points:
            self.logger.error("未配置数据点")
            print(f"[ERROR] 未配置数据点")
            print(f"[HINT] 请在配置文件的 target_points 中设置要导出的数据点列表")
            sys.exit(1)
        
        print(f"[CONFIG] 配置验证通过")
    
    def _setup_logger(self):
        """设置高性能日志系统"""
        self.logger = logging.getLogger('HisToCsv')
        self.logger.setLevel(logging.INFO)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 创建文件处理器, 使用缓冲模式提高性能
        file_handler = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        file_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 禁用传播到根logger
        self.logger.propagate = False
    
    def _parse_start_date(self, start_date_str: str) -> datetime:
        """解析开始日期"""
        if not start_date_str:
            # 默认使用今天
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            return datetime.strptime(start_date_str, "%Y%m%d")
        except ValueError:
            error_msg = f"日期格式错误: {start_date_str}, 使用格式: YYYYMMDD"
            self.logger.error(error_msg)
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _get_parser(self) -> HisDataParser:
        """获取线程安全的解析器实例"""
        thread_id = threading.current_thread().ident
        
        with self._parser_lock:
            if thread_id not in self._parser_cache:
                self._parser_cache[thread_id] = HisDataParser()
        
        return self._parser_cache[thread_id]
    
    def discover_daily_batches(self) -> List[Tuple[datetime, List[Tuple[str, str]]]]:
        """
        按天发现和组织HIS文件
        Returns:
            List[Tuple[datetime, List[Tuple[str, str]]]]: (日期, [(file_prefix, his_path)])
        """
        self.logger.info(f"扫描目录: {self.data_dir}")
        self.logger.info(f"日期范围: {self.start_date.strftime('%Y-%m-%d')} 开始, {self.days} 天")
        
        # 查找所有.his文件
        his_pattern = str(self.data_dir / "*.his")
        his_files = glob.glob(his_pattern)
        
        if not his_files:
            self.logger.error(f"在目录 {self.data_dir} 中未找到任何.his文件")
            return []
        
        # 按日期组织文件
        daily_files = defaultdict(list)
        
        for his_file in his_files:
            his_path = Path(his_file)
            file_prefix = his_path.stem
            
            # 检查IDX文件
            idx_file = his_path.parent / f"{file_prefix}.idx"
            if not idx_file.exists():
                self.logger.warning(f"跳过 {file_prefix}: 缺少对应的.idx文件")
                continue
            
            # 解析文件日期和小时 (格式: YYYYMMDDHH)
            if len(file_prefix) >= 10:
                try:
                    file_date_str = file_prefix[:8]  # YYYYMMDD
                    file_hour = int(file_prefix[8:10])  # HH
                    file_date = datetime.strptime(file_date_str, "%Y%m%d")
                    
                    # 检查是否在目标日期范围内
                    if self.start_date <= file_date < self.start_date + timedelta(days=self.days):
                        daily_files[file_date].append((file_prefix, str(his_path)))
                        
                except ValueError:
                    self.logger.warning(f"无法解析文件日期: {file_prefix}")
                    continue
        
        # 转换为有序列表
        daily_batches = []
        for day_offset in range(self.days):
            current_date = self.start_date + timedelta(days=day_offset)
            if current_date in daily_files:
                files = daily_files[current_date]
                files.sort(key=lambda x: x[0])  # 按文件名排序
                daily_batches.append((current_date, files))
                self.logger.info(f"{current_date.strftime('%Y-%m-%d')}: 找到 {len(files)} 个文件")
            else:
                self.logger.warning(f"{current_date.strftime('%Y-%m-%d')}: 未找到文件")
        
        self.stats['total_days'] = len(daily_batches)
        total_files = sum(len(files) for _, files in daily_batches)
        self.stats['total_files'] = total_files
        
        result_msg = f"总计: {len(daily_batches)} 天, {total_files} 个文件"
        self.logger.info(f"统计信息: {result_msg}")
        self.logger.info(f"文件发现完成: {result_msg}")
        return daily_batches
    
    def list_all_files(self) -> None:
        """列出所有可用的HIS文件"""
        daily_batches = self.discover_daily_batches()
        
        if not daily_batches:
            self.logger.error("未找到任何有效文件")
            return
        
        self.logger.info(f"\n在指定日期范围内发现 {len(daily_batches)} 天的数据:")
        self.logger.info("=" * 80)
        
        for date, files in daily_batches:
            self.logger.info(f"\n{date.strftime('%Y-%m-%d')} ({len(files)} 个文件):")
            for i, (file_prefix, _) in enumerate(files, 1):
                hour = file_prefix[8:10] if len(file_prefix) >= 10 else "??"
                self.logger.info(f"  {i:2d}. {file_prefix} (时间: {hour}:00)")
        
        self.logger.info("=" * 80)
        self.logger.info(f"总计: {sum(len(files) for _, files in daily_batches)} 个文件")
    
    def list_available_points(self, sample_date: datetime = None) -> List[str]:
        """
        列出指定日期的所有可用数据点
        Args:
            sample_date: 采样日期, None则使用开始日期
        """
        if sample_date is None:
            sample_date = self.start_date
        
        # 找到该日期的第一个文件
        daily_batches = self.discover_daily_batches()
        sample_files = None
        
        for date, files in daily_batches:
            if date.date() == sample_date.date():
                sample_files = files
                break
        
        if not sample_files:
            self.logger.error(f"在 {sample_date.strftime('%Y-%m-%d')} 未找到文件")
            return []
        
        # 使用第一个文件解析数据点
        file_prefix, his_path = sample_files[0]
        parser = self._get_parser()
        
        try:
            idx_filepath = str(self.data_dir / f"{file_prefix}.idx")
            if parser.idx_info_parser(idx_filepath):
                point_names = list(parser._point_info_cache.keys())
                
                self.logger.info(f"\n{sample_date.strftime('%Y-%m-%d')} 可用数据点 ({len(point_names)} 个):")
                self.logger.info("=" * 60)
                
                for i, point_name in enumerate(sorted(point_names), 1):
                    point_info = parser._point_info_cache[point_name]
                    self.logger.info(f"  {i:3d}. {point_name} (索引: {point_info.point_index}, 类型: {point_info.point_type})")
                
                self.logger.info("=" * 60)
                self.logger.info(f"总计: {len(point_names)} 个数据点")
                return point_names
            else:
                self.logger.error(f"无法解析IDX文件: {idx_filepath}")
                return []
                
        except Exception as e:
            self.logger.error(f"列出数据点失败: {e}")
            return []
    
    def process_single_file(self, file_prefix: str, points_to_process: List[str]) -> Tuple[bool, int]:
        """
        处理单个HIS文件 - 只负责数据读取和缓存, 不写入文件
        Args:
            file_prefix: 文件前缀
            points_to_process: 要处理的数据点列表
        Returns:
            Tuple[bool, int]: (是否成功, 记录数量)
        """
        thread_id = threading.current_thread().name
        parser = self._get_parser()
        
        try:
            self.logger.info(f"[THREAD-{thread_id}] 读取文件: {file_prefix}")
            # Log thread start
            
            # 解析IDX文件
            idx_filepath = str(self.data_dir / f"{file_prefix}.idx")
            if not parser.idx_info_parser(idx_filepath):
                error_msg = f"无法解析IDX文件: {file_prefix}"
                self.logger.error(f"{error_msg}")
                # Error already logged above
                return False, 0
            
            # 验证数据点
            available_points = set(parser._point_info_cache.keys())
            valid_points = [p for p in points_to_process if p in available_points]
            
            if not valid_points:
                warning_msg = f"{file_prefix}: 无有效数据点"
                self.logger.warning(f"{warning_msg}")
                # Warning already logged above
                return True, 0  # 不算失败
            
            total_records = 0
            
            # 处理每个数据点 - 读取数据并存入缓存
            if self.point_threads == 1:
                # 单线程处理数据点
                for point_name in valid_points:
                    records = self._read_and_cache_point_data(parser, file_prefix, point_name)
                    total_records += records
            else:
                # 多线程处理数据点
                with ThreadPoolExecutor(max_workers=self.point_threads) as executor:
                    futures = [
                        executor.submit(self._read_and_cache_point_data, parser, file_prefix, point_name)
                        for point_name in valid_points
                    ]
                    
                    for future in as_completed(futures):
                        records = future.result()
                        total_records += records
            
            self.logger.info(f"[THREAD-{thread_id}] {file_prefix} 读取完成: {total_records} 条记录缓存")
            # File read completion already logged above
            return True, total_records
            
        except Exception as e:
            error_msg = f"{file_prefix} 处理失败: {e}"
            self.logger.error(f"{error_msg}")
            return False, 0
    
    def _read_and_cache_point_data(self, parser: HisDataParser, file_prefix: str, point_name: str) -> int:
        """
        读取单个数据点数据并存入缓存
        Args:
            parser: HIS数据解析器
            file_prefix: 文件前缀
            point_name: 数据点名称 
        Returns:
            int: 读取的记录数
        """
        try:
            # 读取数据点所有数据块
            point_data = parser.read_single_point_all_blocks(
                str(self.data_dir), file_prefix, point_name
            )
            
            if not point_data:
                return 0
            
            # 将数据存入缓存 (线程安全)
            with self.cache_lock:
                self.data_cache[point_name][file_prefix] = point_data
            
            return len(point_data)
            
        except Exception as e:
            error_msg = f"读取数据点 {point_name} 失败: {e}"
            self.logger.error(f"{error_msg}")
            return 0
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的特殊字符，并控制长度
        Args:
            filename: 原始文件名
        Returns:
            str: 清理后的安全文件名
        """
        # 替换特殊字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ', '.']
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 移除连续的下划线
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        
        # 移除开头和结尾的下划线
        sanitized = sanitized.strip('_')
        
        # 如果为空，使用默认名称
        if not sanitized:
            sanitized = 'unnamed_point'
        
        return sanitized
    
    def _write_csv_file(self, filepath: Path, data_points: List[PointDataStruct], point_name: str) -> None:
        """
        写入CSV文件
        Args:
            filepath: CSV文件路径
            data_points: 数据点列表
            point_name: 数据点名称
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if self.csv_format == "detailed":
                fieldnames = ['timestamp', 'value', 'point_code', 'point_index', 'point_type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for point in data_points:
                    writer.writerow({
                        'timestamp': point.date_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'value': point.point_value,
                        'point_code': point.point_code,
                        'point_index': point.point_index,
                        'point_type': point.point_type
                    })
            else:
                # 简单格式：只有时间和数值
                fieldnames = ['timestamp', 'value']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for point in data_points:
                    writer.writerow({
                        'timestamp': point.date_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'value': point.point_value
                    })
    
    def _write_merged_csv_file(self, date: datetime, all_points_data: Dict[str, List[PointDataStruct]]) -> int:
        """
        写入合并所有数据点的CSV文件
        Args:
            date: 日期
            all_points_data: 所有数据点的数据字典 {point_name: [PointDataStruct, ...]}
        Returns:
            int: 写入的记录数
        """
        # 生成合并文件名 - 避免文件名过长的问题
        points_str = "_".join([self._sanitize_filename(p) for p in self.target_points])
        
        # 检查文件名长度，如果太长则使用简化策略
        max_filename_length = 200  # 预留一些空间给日期和扩展名
        if len(points_str) > max_filename_length:
            # 策略1：只使用前几个点名 + 点数量
            num_points = len(self.target_points)
            if num_points <= 3:
                # 如果点数少，截断每个点名
                truncated_points = [self._sanitize_filename(p)[:20] for p in self.target_points[:3]]
                points_str = "_".join(truncated_points)
            else:
                # 如果点数多，使用前2个点名 + 总数
                first_two = [self._sanitize_filename(p)[:15] for p in self.target_points[:2]]
                points_str = "_".join(first_two) + f"_and_{num_points-2}_more"
        
        merged_filename = f"{date.strftime('%Y%m%d')}_{points_str}.csv"
        
        # 最终检查：如果还是太长，使用最简方案
        if len(merged_filename) > 220:
            merged_filename = f"{date.strftime('%Y%m%d')}_merged_{len(self.target_points)}_points.csv"
        
        merged_filepath = self.output_dir / merged_filename
        
        # 收集所有时间戳
        all_timestamps = set()
        for point_data_list in all_points_data.values():
            for point_data in point_data_list:
                all_timestamps.add(point_data.date_time)
        
        # 按时间排序
        sorted_timestamps = sorted(all_timestamps)
        
        # 为每个数据点创建时间戳到值的映射
        point_value_maps = {}
        for point_name, point_data_list in all_points_data.items():
            point_value_maps[point_name] = {
                point_data.date_time: point_data.point_value 
                for point_data in point_data_list
            }
        
        # 写入合并的CSV文件
        with open(merged_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # 创建列名：timestamp + 各个数据点名
            fieldnames = ['timestamp'] + self.target_points
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            written_records = 0
            for timestamp in sorted_timestamps:
                row = {'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                
                # 为每个数据点添加对应时间的值，如果没有则为空
                for point_name in self.target_points:
                    if point_name in point_value_maps and timestamp in point_value_maps[point_name]:
                        row[point_name] = point_value_maps[point_name][timestamp]
                    else:
                        row[point_name] = ''  # 如果该时间点没有数据则为空
                
                writer.writerow(row)
                written_records += 1
        
        self.logger.info(f"合并文件: {written_records:,} 条记录 -> {merged_filename}")
        return written_records
    
    def _write_daily_csv_files(self, date: datetime, file_prefixes: List[str]) -> int:
        """
        将缓存中的数据写入CSV文件 - 每个数据点一个文件包含一天所有数据，同时生成合并文件
        
        Args:
            date: 日期
            file_prefixes: 该天所有文件前缀列表
            
        Returns:
            int: 写入的总记录数
        """
        self.logger.info(f"开始写入 {date.strftime('%Y-%m-%d')} 的CSV文件...")
        # CSV write start already logged above
        
        total_written = 0
        all_points_data = {}  # 存储所有数据点的数据，用于合并文件
        
        # 为每个数据点创建一个CSV文件, 包含该天所有小时的数据
        for point_name in self.target_points:
            # 收集该数据点在该天的所有数据
            all_point_data = []
    
            with self.cache_lock:
                if point_name in self.data_cache:
                    for file_prefix in sorted(file_prefixes):  # 按时间顺序
                        if file_prefix in self.data_cache[point_name]:
                            all_point_data.extend(self.data_cache[point_name][file_prefix])

            if all_point_data:
                # 根据配置决定是否写入单个数据点的CSV文件
                if self.save_individual_points:
                    safe_point_name = self._sanitize_filename(point_name)
                    csv_filename = f"{date.strftime('%Y%m%d')}_{safe_point_name}.csv"
                    csv_filepath = self.output_dir / csv_filename
                    # 按时间排序（仅在需要生成单个文件时排序）
                    all_point_data.sort(key=lambda x: x.date_time)
                    self._write_csv_file(csv_filepath, all_point_data, point_name)

                self.logger.info(f"{point_name}: {len(all_point_data):,} 条记录")
                total_written += len(all_point_data)

                # 存储数据用于合并文件（合并文件生成时会统一排序）
                all_points_data[point_name] = all_point_data
            else:
                self.logger.info(f"{point_name}: 无数据")

        # 生成合并所有数据点的CSV文件
        if all_points_data:
            merged_records = self._write_merged_csv_file(date, all_points_data)
            self.logger.info(f"合并文件: {merged_records:,} 条记录")

        # 清理已写入的缓存数据以释放内存
        self._clear_daily_cache(date, file_prefixes)
        
        self.logger.info(f"{date.strftime('%Y-%m-%d')} CSV写入完成: {total_written:,} 条记录")
        # CSV completion already logged above
        return total_written
    
    def _clear_daily_cache(self, date: datetime, file_prefixes: List[str]) -> None:
        """
        清理指定日期的缓存数据以释放内存
        
        Args:
            date: 日期
            file_prefixes: 要清理的文件前缀列表
        """
        with self.cache_lock:
            for point_name in list(self.data_cache.keys()):
                for file_prefix in file_prefixes:
                    if file_prefix in self.data_cache[point_name]:
                        del self.data_cache[point_name][file_prefix]
                
                # 如果该数据点没有任何缓存数据了, 删除整个键
                if not self.data_cache[point_name]:
                    del self.data_cache[point_name]
        
        self.logger.info(f"{date.strftime('%Y-%m-%d')} 缓存已清理")
        # Cache cleanup already logged above
    
    def process_daily_batch(self, date: datetime, files: List[Tuple[str, str]]) -> bool:
        """
        处理一天的文件批次 - 先读取数据到缓存, 再统一写入CSV
        Args:
            date: 日期
            files: 文件列表
        Returns:
            bool: 是否成功
        """
        self.logger.info(f"\n=== 处理 {date.strftime('%Y-%m-%d')} ===")
        self.logger.info(f"文件数量: {len(files)}")
        self.logger.info(f"数据点: {', '.join(self.target_points) if self.target_points else '未指定'}")
        self.logger.info(f"线程数: {self.max_workers}")
        
        if not self.target_points:
            error_msg = "未指定数据点, 跳过此批次"
            self.logger.error(f"{error_msg}")
            return False
        
        batch_start_time = time.time()
        successful_files = 0
        total_records = 0
        
        # Batch start already logged above
        
        # 第一阶段：多线程读取数据到缓存
        self.logger.info(f"阶段1: 读取数据到缓存...")
        
        if self.max_workers == 1:
            # 单线程处理
            for i, (file_prefix, his_path) in enumerate(files, 1):
                self.logger.info(f"[{i}/{len(files)}] 读取: {file_prefix}")
                success, records = self.process_single_file(file_prefix, self.target_points)
                
                with self.stats_lock:
                    self.stats['processed_files'] += 1
                    if success:
                        self.stats['successful_files'] += 1
                        successful_files += 1
                    else:
                        self.stats['failed_files'] += 1
                    self.stats['total_records'] += records
                    total_records += records
        else:
            # 多线程处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self.process_single_file, file_prefix, self.target_points)
                    for file_prefix, his_path in files
                ]
                
                for future in as_completed(futures):
                    success, records = future.result()
                    
                    with self.stats_lock:
                        self.stats['processed_files'] += 1
                        if success:
                            self.stats['successful_files'] += 1
                            successful_files += 1
                        else:
                            self.stats['failed_files'] += 1
                        self.stats['total_records'] += records
                        total_records += records
        
        # 第二阶段：统一写入CSV文件
        self.logger.info(f"阶段2: 写入CSV文件...")
        file_prefixes = [file_prefix for file_prefix, _ in files]
        csv_records = self._write_daily_csv_files(date, file_prefixes)
        
        batch_elapsed = time.time() - batch_start_time
        self.logger.info(f"{date.strftime('%Y-%m-%d')} 完成: {successful_files}/{len(files)} 文件成功")
        self.logger.info(f"缓存记录: {total_records:,} 条, CSV记录: {csv_records:,} 条")
        self.logger.info(f"耗时: {batch_elapsed:.1f} 秒")
        
        batch_result = f"{date.strftime('%Y-%m-%d')} 批次完成: {successful_files}/{len(files)} 文件成功, {total_records:,} 条缓存记录, {csv_records:,} 条CSV记录, 耗时: {batch_elapsed:.1f} 秒"
        # Batch completion already logged above
        
        with self.stats_lock:
            self.stats['processed_days'] += 1
        
        return successful_files > 0
    
    def process_all_batches(self) -> bool:
        """
        处理所有批次
        
        Returns:
            bool: 整体是否成功
        """
        daily_batches = self.discover_daily_batches()
        
        if not daily_batches:
            error_msg = "未找到任何文件批次"
            self.logger.error(f"{error_msg}")
            return False
        
        if not self.target_points:
            error_msg = "未指定数据点, 无法处理"
            self.logger.error(f"{error_msg}")
            return False
        
        self.stats['start_time'] = time.time()
        
        start_info = f"开始批量CSV导出: {len(daily_batches)} 天, {sum(len(files) for _, files in daily_batches)} 个文件"
        self.logger.info(start_info)
        self.logger.info(f"数据点: {', '.join(self.target_points)}")
        self.logger.info(f"CSV格式: {self.csv_format}")
        self.logger.info(f"保存单个数据点文件: {self.save_individual_points}")
        self.logger.info(f"线程配置: 文件级{self.max_workers}, 数据点级{self.point_threads}")
        
        # 按天顺序处理
        overall_success = True
        for i, (date, files) in enumerate(daily_batches, 1):
            self.logger.info(f"\n[PROGRESS] 批次 {i}/{len(daily_batches)}")
            batch_success = self.process_daily_batch(date, files)
            if not batch_success:
                overall_success = False
        
        # 最终统计
        end_time = time.time()
        total_elapsed = end_time - self.stats['start_time']
        self.logger.info("[RESULT] 批量CSV导出完成统计")
        self.logger.info("=" * 60)
        self.logger.info(f"[TIME] 总耗时: {total_elapsed:.1f} 秒 ({total_elapsed / 60:.1f} 分钟)")
        self.logger.info(f"[BATCH] 处理天数: {self.stats['processed_days']}/{self.stats['total_days']}")
        self.logger.info(f"[FILE] 处理文件: {self.stats['processed_files']}/{self.stats['total_files']}")
        self.logger.info(f"[SUCCESS] 成功文件: {self.stats['successful_files']}")
        self.logger.info(f"[ERROR] 失败文件: {self.stats['failed_files']}")
        self.logger.info(f"[RECORDS] 导出记录: {self.stats['total_records']:,} 条")
        self.logger.info(f"[OUTPUT] 输出目录: {self.output_dir}")
        self.logger.info(f"[LOG] 日志文件: {self.log_file}")
        
        final_result = f"批量处理完成: 成功率 {(self.stats['successful_files'] / max(1, self.stats['total_files']) * 100):.1f}%"
        self.logger.info(final_result)
        
        if total_elapsed > 0:
            files_per_min = (self.stats['processed_files'] / total_elapsed) * 60
            records_per_sec = self.stats['total_records'] / total_elapsed
            self.logger.info(f"[SPEED] 处理速度: {files_per_min:.1f} 文件/分钟, {records_per_sec:.1f} 记录/秒")

        return overall_success


def main():
    # 解析命令行参数（只保留必要的选项）
    parser = argparse.ArgumentParser(
        description='HIS文件批量CSV导出 (配置文件驱动)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用说明:
  %(prog)s                           # 使用配置文件运行
  %(prog)s --save-config-template    # 生成配置文件模板
  %(prog)s --config custom.json     # 使用自定义配置文件
        """
    )
    
    parser.add_argument('--save-config-template', action='store_true',
                        help='生成配置文件模板并退出')
    parser.add_argument('--config', default='his_config.json',
                        help='配置文件路径 (默认: his_config.json)')
    
    args = parser.parse_args()
    
    # 处理生成配置文件模板命令
    if args.save_config_template:
        print("=" * 60)
        print("生成HIS文件批量CSV导出配置文件模板")
        print("=" * 60)
        BatchHisToCsv.save_config_template(args.config)
        print(f"[INFO] 请编辑 {args.config} 文件设置您的参数, 然后运行:")
        print(f"[INFO] python batch_his_files_to_csv.py")
        return
    
    print("=" * 60)
    print("HIS文件批量CSV导出")
    print("=" * 60)
    
    try:
        # 创建批处理器（会自动处理配置文件）
        processor = BatchHisToCsv(args.config)
        
        # 开始批量导出
        print("[START] === HIS数据批量CSV导出 ===")
        success = processor.process_all_batches()
        
        if success:
            print("\n[SUCCESS] CSV导出完成！")
            sys.exit(0)
        else:
            print("\n[WARN] 部分文件导出失败")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[STOP] 用户中断导出过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 导出过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
