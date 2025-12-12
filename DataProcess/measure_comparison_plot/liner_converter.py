#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4-20mA 数据转换模块

功能：
1. mA 与频率的线性映射转换
2. 频率输入 CSV → mA 输入 CSV
3. 解析特殊格式 mA 输出 CSV
4. mA 输出 CSV → 标准格式 CSV
"""

import argparse
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Iterable, List, Sequence, Tuple


class DataLinerMapping:
    """线性映射配置（in → out）"""

    def __init__(
        self,
        in_min: float = 4.0,
        in_max: float = 20.0,
        out_min: float = 49.8,
        out_max: float = 50.2,
        in_precision: float = 0.01,
        out_precision: float = None
    ):
        self.in_min = in_min
        self.in_max = in_max
        self.out_min = out_min
        self.out_max = out_max
        self.in_precision = in_precision
        self.out_precision = out_precision

    @staticmethod
    def _round_to_precision(value: float, precision: float) -> float:
        """按指定精度四舍五入到最近的步进"""
        if precision is None or precision <= 0:
            return value
        d_value = Decimal(str(value))
        d_precision = Decimal(str(precision))
        quantized = (d_value / d_precision).to_integral_value(rounding=ROUND_HALF_UP) * d_precision
        return float(quantized)

    @staticmethod
    def _precision_decimals(precision: float, fallback: int) -> int:
        """根据步进精度推导小数位数, 用于格式化输出"""
        if precision is None or precision <= 0:
            return fallback
        exp = Decimal(str(precision)).normalize().as_tuple().exponent
        return max(0, -exp)

    def map_in_to_out(self, in_value: float, out_precision: float = None) -> float:
        """
        (线性映射: in → out)
        公式: out = out_min + (in - in_min) / (in_max - in_min) * (out_max - out_min)
        Args:
            in_value
            out_precision: 输出精度步进，默认使用 self.out_precision
        Returns:
            out_value (按 out_precision 四舍五入)
        """
        if out_precision is None:
            out_precision = self.out_precision
        ratio = (in_value - self.in_min) / (self.in_max - self.in_min)
        out_value = self.out_min + ratio * (self.out_max - self.out_min)
        return self._round_to_precision(out_value, out_precision)

    def reverse(self) -> "DataLinerMapping":
        """返回反向映射(out → in)的配置对象"""
        return DataLinerMapping(
            in_min=self.out_min,
            in_max=self.out_max,
            out_min=self.in_min,
            out_max=self.in_max,
            in_precision=self.out_precision,
            out_precision=self.in_precision
        )

    def csv_linemap(self, input_csv: str, output_csv: str) -> int:
        """
        将输入 CSV 的第4列数值按 in → out 线性映射

        输入格式: 2025-12-9,16:00:05,000,49.916
                 (日期,时间,毫秒,in_value)
        输出格式: 2025-12-9,16:00:05,000,12.32
                 (日期,时间,毫秒,out_value)

        Returns:
            转换的行数
        """
        decimals = DataLinerMapping._precision_decimals(self.out_precision, 2)

        count = 0
        with open(input_csv, 'r', encoding='utf-8-sig') as fin, \
             open(output_csv, 'w', encoding='utf-8', newline='') as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout)

            for row in reader:
                if not row or len(row) < 4:
                    continue

                try:
                    date_str = row[0].strip()
                    time_str = row[1].strip()
                    ms_str = row[2].strip()
                    in_value = float(row[3].strip())

                    # 转换
                    out_value = self.map_in_to_out(in_value)

                    # 写入 输出 CSV(格式相同, 只是值变了)
                    writer.writerow([date_str, time_str, ms_str, f"{out_value:.{decimals}f}"])
                    count += 1

                except (ValueError, IndexError) as e:
                    print(f"警告: 跳过无效行: {e}")
                    continue

        return count


class TimeSeriesAggregator:
    """时间采样数据 CSV 聚合器(按固定毫秒窗口求均值)"""

    @staticmethod
    def _parse_raw_rows(rows: Iterable[Sequence[str]]) -> List[Tuple[datetime, float]]:
        """
        行格式: ["2025-12-11 10:22:26.419200", "19.99777"]

        Args:
            rows: CSV reader 或其他行迭代器

        Returns:
            原始采样点列表 (datetime, ma_value)
        """
        samples: List[Tuple[datetime, float]] = []
        for row in rows:
            if not row or len(row) < 2:
                continue
            try:
                datetime_str = str(row[0]).strip()
                ma_value = float(str(row[1]).strip())
                dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
                samples.append((dt, ma_value))
            except (ValueError, IndexError) as e:
                print(f"警告: 跳过无效行: {e}")
                continue

        return samples

    @staticmethod
    def raw_csv_to_time_series(input_csv: str) -> List[Tuple[datetime, float]]:
        """读取原始 mA 输出 CSV 并解析为采样点列表"""
        with open(input_csv, 'r', encoding='utf-8-sig') as fin:
            reader = csv.reader(fin)
            return TimeSeriesAggregator._parse_raw_rows(reader)

    @staticmethod
    def _aggregate_time_series(
        samples: Iterable[Tuple[datetime, float]],
        aggregate_ms: int = 1
    ) -> List[Tuple[datetime, float]]:
        """
        将时间序列按固定毫秒窗口聚合为均值点

        Args:
            samples: 原始采样点 (datetime, value)
            aggregate_ms: 聚合窗口大小(毫秒), 默认 1ms

        Returns:
            按时间排序的聚合结果 (bucket_datetime, avg_value)
        """
        if aggregate_ms <= 0:
            raise ValueError("aggregate_ms 必须大于 0")

        epoch = datetime(1970, 1, 1)
        bucket_sum_count: dict[int, Tuple[float, int]] = {}

        for dt, value in samples:
            delta = dt - epoch
            total_ms = (
                (delta.days * 86400 + delta.seconds) * 1000 +
                delta.microseconds // 1000
            )
            bucket_total_ms = (total_ms // aggregate_ms) * aggregate_ms
            prev_sum, prev_count = bucket_sum_count.get(bucket_total_ms, (0.0, 0))
            bucket_sum_count[bucket_total_ms] = (prev_sum + value, prev_count + 1)

        aggregated: List[Tuple[datetime, float]] = []
        for bucket_total_ms in sorted(bucket_sum_count.keys()):
            value_sum, value_count = bucket_sum_count[bucket_total_ms]
            avg_value = value_sum / value_count
            dt_bucket = epoch + timedelta(milliseconds=bucket_total_ms)
            aggregated.append((dt_bucket, avg_value))

        return aggregated

    @staticmethod
    def _format_standard_timestamp(dt_bucket: datetime) -> str:
        """格式化标准输出时间戳: YYYY/MM/DD HH:MM:SS::mmm"""
        dt_no_micro = dt_bucket.replace(microsecond=0)
        ms = dt_bucket.microsecond // 1000
        date_part = dt_no_micro.strftime("%Y/%m/%d %H:%M:%S")
        return f"{date_part}::{ms:03d}"

    @staticmethod
    def aggregate_round_time_series(
        samples: Iterable[Tuple[datetime, float]],
        aggregate_ms: int = 1,
        precision: float = 0.01
    ) -> List[Tuple[str, float]]:
        """
        将原始采样点聚合并转换为标准格式数据

        Args:
            samples: 原始采样点 (datetime, value)
            aggregate_ms: 聚合时间精度(毫秒), 默认 1ms
            precision: 步进精度(默认 0.01)

        Returns:
            标准格式行列表 (standard_datetime_str, value_rounded)
        """
        aggregated = TimeSeriesAggregator._aggregate_time_series(samples, aggregate_ms=aggregate_ms)

        value_decimals = DataLinerMapping._precision_decimals(precision, 2)
        standard_rows: List[Tuple[str, float]] = []
        for dt_bucket, avg_value in aggregated:
            value_rounded = DataLinerMapping._round_to_precision(avg_value, precision)
            standard_datetime = TimeSeriesAggregator._format_standard_timestamp(dt_bucket)
            standard_rows.append((standard_datetime, float(f"{value_rounded:.{value_decimals}f}")))

        return standard_rows

    @staticmethod
    def csv_to_aggregated_csv(
        input_csv: str,
        output_standard_csv: str,
        mapping: DataLinerMapping = None,
        aggregate_ms: int = 1
    ) -> int:
        """
        解析 高精度时间序列的 csv 输出 毫秒级 CSV, 转换为标准 DataFormatParser 格式

        输入格式: 2025-12-11 10:22:26.419200,19.99777
                 (YYYY-MM-DD HH:MM:SS.微秒, mA值)

        输出格式: 2025/12/09 10:05:28::805,18.90
                 (YYYY/MM/DD HH:MM:SS::毫秒, mA值四舍五入, 每毫秒一个采样点)

        Args:
            input_csv: 输入 mA 输出 CSV 路径
            output_standard_csv: 输出标准格式 CSV 路径
            mapping: mA-频率映射配置(未使用, 保留接口一致性)
            aggregate_ms: 聚合后的时间精度(毫秒), 默认 1ms

        Returns:
            转换的行数(输出的毫秒采样点数)
        """
        if mapping is None:
            mapping = DataLinerMapping()
        input_precision = mapping.in_precision if mapping.in_precision is not None else 0.01

        samples = TimeSeriesAggregator.raw_csv_to_time_series(input_csv)
        standard_rows = TimeSeriesAggregator.aggregate_round_time_series(
            samples,
            aggregate_ms=aggregate_ms,
            precision=input_precision
        )

        value_decimals = DataLinerMapping._precision_decimals(input_precision, 2)
        with open(output_standard_csv, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.writer(fout)
            for datetime_str, value in standard_rows:
                writer.writerow([datetime_str, f"{value:.{value_decimals}f}"])

        return len(standard_rows)


class LinearConvertAggregator:
    """通用线性映射 + 时间序列 CSV 转换器

    - 读取/写入两列标准 CSV: (timestamp_str, value)
    - 标准 CSV 之间的 in → out 线性映射
    - 原始高精度时间序列 CSV 按毫秒窗口聚合为标准 CSV
    """

    def __init__(self, mapping: DataLinerMapping):
        self.mapping = mapping

    @staticmethod
    def read_standard_csv(input_csv: str) -> List[Tuple[str, float]]:
        """读取两列标准 CSV 为行列表 (timestamp_str, value)"""
        rows: List[Tuple[str, float]] = []
        with open(input_csv, 'r', encoding='utf-8-sig') as fin:
            reader = csv.reader(fin)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                try:
                    timestamp_str = row[0].strip()
                    value = float(row[1].strip())
                    rows.append((timestamp_str, value))
                except (ValueError, IndexError) as e:
                    print(f"警告: 跳过无效行: {e}")
                    continue
        return rows

    @staticmethod
    def write_standard_csv(
        output_csv: str,
        rows: Iterable[Tuple[str, float]],
        precision: float = None
    ) -> int:
        """写入两列标准 CSV, 可选按 precision 格式化数值"""
        decimals = DataLinerMapping._precision_decimals(precision, 3)
        count = 0
        with open(output_csv, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.writer(fout)
            for timestamp_str, value in rows:
                writer.writerow([timestamp_str, f"{value:.{decimals}f}"])
                count += 1
        return count

    def _map_rows(
        self,
        rows: Iterable[Tuple[str, float]],
        output_precision: float = None
    ) -> List[Tuple[str, float]]:
        """
        对标准行的 value 做线性映射

        Args:
            rows: (timestamp_str, value)
            output_precision: 输出步进精度, 默认使用映射配置的 out_precision
        """
        if output_precision is None:
            output_precision = self.mapping.out_precision

        decimals = DataLinerMapping._precision_decimals(output_precision, 3)
        mapped_rows: List[Tuple[str, float]] = []
        for timestamp_str, value in rows:
            mapped_value = self.mapping.map_in_to_out(value, out_precision=output_precision)
            mapped_rows.append(
                (timestamp_str, float(f"{mapped_value:.{decimals}f}"))
            )

        return mapped_rows

    def aggregate_and_map_csv(
        self,
        input_raw_csv: str,
        output_mapped_csv: str,
        aggregate_ms: int = 1,
        source_precision: float = None,
        output_precision: float = None
    ) -> int:
        """原始高精度 CSV 先聚合再线性映射并保存"""
        if source_precision is None:
            source_precision = (
                self.mapping.in_precision if self.mapping.in_precision is not None else 0.01
            )

        samples = TimeSeriesAggregator.raw_csv_to_time_series(input_raw_csv)
        standard_rows = TimeSeriesAggregator.aggregate_round_time_series(
            samples,
            aggregate_ms=aggregate_ms,
            precision=source_precision
        )
        mapped_rows = self._map_rows(
            standard_rows,
            output_precision=output_precision
        )

        precision_out = output_precision
        if precision_out is None:
            precision_out = self.mapping.out_precision

        return LinearConvertAggregator.write_standard_csv(
            output_mapped_csv,
            mapped_rows,
            precision=precision_out
        )


def _load_mapping_from_config(config: dict) -> DataLinerMapping:
    """
    Args:
        config: 配置字典
    Returns:
        DataLinerMapping 对象 (in=ma, out=freq)
    """
    mapping_cfg = config.get('ma_freq_mapping', {})
    return DataLinerMapping(
        in_min=mapping_cfg.get('ma_min', 4.0),
        in_max=mapping_cfg.get('ma_max', 20.0),
        out_min=mapping_cfg.get('freq_min', 49.8),
        out_max=mapping_cfg.get('freq_max', 50.2),
        in_precision=mapping_cfg.get('ma_precision', 0.01),
        out_precision=mapping_cfg.get('freq_precision', None)
    )


def _print_conversion_result(count, input_path, output_path, details):
    """打印转换结果"""
    print(f"成功转换 {count} 行数据")
    print(f"   输入: {input_path}")
    print(f"   输出: {output_path}")

    if isinstance(details, dict):
        for key, value in details.items():
            print(f"   {key}: {value}")
    elif isinstance(details, (list, tuple)):
        for detail in details:
            print(f"   {detail}")


def convert_input_command(config: dict):
    """处理 convert-input 命令"""
    mapping_ma_to_freq = _load_mapping_from_config(config)
    mapping_freq_to_ma = mapping_ma_to_freq.reverse()
    cmd_cfg = config.get('convert_input', {})

    input_file = cmd_cfg.get('input', 'input_freq.csv')
    output_file = cmd_cfg.get('output', 'output_ma.csv')

    count = mapping_freq_to_ma.csv_linemap(input_file, output_file)

    _print_conversion_result(count, input_file, output_file, {
        '映射': f"{mapping_freq_to_ma.in_min}-{mapping_freq_to_ma.in_max} Hz → "
        f"{mapping_freq_to_ma.out_min}-{mapping_freq_to_ma.out_max} mA"
    })


def convert_output_command(config: dict):
    """处理 convert-output 命令"""
    mapping = _load_mapping_from_config(config)
    cmd_cfg = config.get('convert_output', {})

    input_file = cmd_cfg.get('input', 'input_ma_output.csv')
    output_file = cmd_cfg.get('output', 'output_standard_ma.csv')
    aggregate_ms = cmd_cfg.get('aggregate_ms', 1)

    converter = LinearConvertAggregator(mapping)
    count = converter.aggregate_raw_csv(
        input_file,
        output_file,
        aggregate_ms=aggregate_ms
    )

    _print_conversion_result(count, input_file, output_file, {
        '格式': f"YYYY-MM-DD HH:MM:SS.微秒 → YYYY/MM/DD HH:MM:SS::毫秒 (每 {aggregate_ms}ms 均值)"
    })


def convert_output_freq_command(config: dict):
    """处理 convert-output-freq 命令"""
    mapping = _load_mapping_from_config(config)
    cmd_cfg = config.get('convert_output_freq', {})

    input_file = cmd_cfg.get('input', 'input_standard_ma.csv')
    output_file = cmd_cfg.get('output', 'output_freq.csv')

    converter = LinearConvertAggregator(mapping)
    count = converter.aggregate_and_map_csv(input_file, output_file)
    _print_conversion_result(count, input_file, output_file, {
        '映射': f"{mapping.in_min}-{mapping.in_max} mA → {mapping.out_min}-{mapping.out_max} Hz",
        '频率精度': f"{mapping.out_precision} Hz"
    })


def main():
    parser = argparse.ArgumentParser(
        description="4-20mA 数据处理工具(配置文件驱动)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置文件 (ma_converter_config.json)
  python liner_converter.py convert-input

  python liner_converter.py -c config.json convert-output
  python liner_converter.py -c config.json convert-output-freq

配置文件格式参考: ma_converter_config.json
        """
    )
    # 全局参数：配置文件路径(默认使用 ma_converter_config.json)
    parser.add_argument(
        '-c', '--config',
        default='ma_converter_config.json',
        help='配置文件路径(JSON 格式, 默认: ma_converter_config.json)'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser(
        'convert-input',
        help='将频率输入 CSV 转换为 mA 输入 CSV'
    )
    subparsers.add_parser(
        'convert-output',
        help='将 mA 输出 CSV 转换为标准格式(按毫秒求均值)'
    )
    subparsers.add_parser(
        'convert-output-freq',
        help='将标准格式 mA 输出 CSV 转换为频率 CSV'
    )
    args = parser.parse_args()

    config = json.load(open(args.config, 'r', encoding='utf-8'))

    if args.command == 'convert-input':
        convert_input_command(config)
    elif args.command == 'convert-output':
        convert_output_command(config)
    elif args.command == 'convert-output-freq':
        convert_output_freq_command(config)


if __name__ == '__main__':
    main()
