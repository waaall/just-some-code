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
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MAFreqMapping:
    """mA 与频率的线性映射配置"""
    ma_min: float = 4.0      # mA 最小值（默认 4mA）
    ma_max: float = 20.0     # mA 最大值（默认 20mA）
    freq_min: float = 49.8   # 对应频率最小值（默认 49.8Hz）
    freq_max: float = 50.2   # 对应频率最大值（默认 50.2Hz）

    def freq_to_ma(self, freq: float) -> float:
        """
        频率转 mA（线性映射）

        公式: mA = ma_min + (freq - freq_min) / (freq_max - freq_min) * (ma_max - ma_min)

        Args:
            freq: 频率值 (Hz)

        Returns:
            对应的 mA 值（四舍五入到 0.01mA）
        """
        ratio = (freq - self.freq_min) / (self.freq_max - self.freq_min)
        ma = self.ma_min + ratio * (self.ma_max - self.ma_min)
        return round(ma, 2)  # 四舍五入到 0.01mA

    def ma_to_freq(self, ma: float) -> float:
        """
        mA 转频率（反向映射）

        公式: freq = freq_min + (ma - ma_min) / (ma_max - ma_min) * (freq_max - freq_min)

        Args:
            ma: mA 值

        Returns:
            对应的频率值 (Hz)
        """
        ratio = (ma - self.ma_min) / (self.ma_max - self.ma_min)
        freq = self.freq_min + ratio * (self.freq_max - self.freq_min)
        return freq


class MAInputConverter:
    """频率输入 CSV → mA 输入 CSV 转换器"""

    @staticmethod
    def convert_freq_to_ma_csv(
        input_freq_csv: str,
        output_ma_csv: str,
        mapping: MAFreqMapping = None
    ) -> int:
        """
        将频率输入 CSV 转换为 mA 输入 CSV

        输入格式: 2025-12-9,16:00:05,000,49.916
                 (日期,时间,毫秒,频率)

        输出格式: 2025-12-9,16:00:05,000,12.32
                 (日期,时间,毫秒,mA值)

        Args:
            input_freq_csv: 输入频率 CSV 路径
            output_ma_csv: 输出 mA CSV 路径
            mapping: mA-频率映射配置（默认 4-20mA → 49.8-50.2Hz）

        Returns:
            转换的行数
        """
        if mapping is None:
            mapping = MAFreqMapping()

        count = 0
        with open(input_freq_csv, 'r', encoding='utf-8-sig') as fin, \
             open(output_ma_csv, 'w', encoding='utf-8', newline='') as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout)

            for row in reader:
                if not row or len(row) < 4:
                    continue

                try:
                    date_str = row[0].strip()
                    time_str = row[1].strip()
                    ms_str = row[2].strip()
                    freq = float(row[3].strip())

                    # 转换为 mA
                    ma = mapping.freq_to_ma(freq)

                    # 写入 mA CSV（格式相同，只是值变了）
                    writer.writerow([date_str, time_str, ms_str, f"{ma:.2f}"])
                    count += 1

                except (ValueError, IndexError) as e:
                    print(f"警告: 跳过无效行: {e}")
                    continue

        return count


class MAOutputParser:
    """mA 输出 CSV 解析器（特殊格式）"""

    @staticmethod
    def parse_and_convert_to_standard(
        input_ma_output_csv: str,
        output_standard_csv: str,
        mapping: MAFreqMapping = None
    ) -> int:
        """
        解析特殊格式 mA 输出 CSV，转换为标准 OutputDataParser 格式

        输入格式: 2025-12-11 10:22:26.419200,19.99777
                 (YYYY-MM-DD HH:MM:SS.微秒, mA值)

        输出格式: 2025/12/09 10:05:28::805,18.90
                 (YYYY/MM/DD HH:MM:SS::毫秒, mA值四舍五入，每毫秒一个采样点)

        功能：将0.1ms级采样数据聚合为1ms级采样数据（每毫秒计算平均值）

        Args:
            input_ma_output_csv: 输入 mA 输出 CSV 路径
            output_standard_csv: 输出标准格式 CSV 路径
            mapping: mA-频率映射配置（未使用，保留接口一致性）

        Returns:
            转换的行数（输出的毫秒采样点数）
        """
        # 用于存储每毫秒的所有采样值: {(datetime, ms): [values]}
        ms_data = defaultdict(list)

        # 第一遍读取：收集所有数据并按毫秒分组
        with open(input_ma_output_csv, 'r', encoding='utf-8-sig') as fin:
            reader = csv.reader(fin)

            for row in reader:
                if not row or len(row) < 2:
                    continue

                try:
                    datetime_str = row[0].strip()
                    ma_value = float(row[1].strip())

                    # 解析时间戳: "2025-12-11 10:22:26.419200"
                    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")

                    # 计算毫秒
                    ms = dt.microsecond // 1000

                    # 创建键：(去除微秒的datetime, 毫秒)
                    dt_no_micro = dt.replace(microsecond=0)
                    key = (dt_no_micro, ms)

                    # 收集该毫秒的所有采样值
                    ms_data[key].append(ma_value)

                except (ValueError, IndexError) as e:
                    print(f"警告: 跳过无效行: {e}")
                    continue

        # 第二遍：计算每毫秒的平均值并写入
        count = 0
        with open(output_standard_csv, 'w', encoding='utf-8', newline='') as fout:
            writer = csv.writer(fout)

            # 按时间顺序排序
            for (dt_no_micro, ms) in sorted(ms_data.keys()):
                # 计算该毫秒的平均值
                avg_ma = sum(ms_data[(dt_no_micro, ms)]) / len(ms_data[(dt_no_micro, ms)])

                # 四舍五入到 0.01mA
                ma_rounded = round(avg_ma, 2)

                # 格式化输出
                date_part = dt_no_micro.strftime("%Y/%m/%d %H:%M:%S")
                standard_datetime = f"{date_part}::{ms:03d}"
                writer.writerow([standard_datetime, f"{ma_rounded:.2f}"])
                count += 1

        return count


def load_mapping_from_config(config_path: str) -> MAFreqMapping:
    """
    从配置文件加载 mA-频率映射

    Args:
        config_path: 配置文件路径（JSON 格式）

    Returns:
        MAFreqMapping 对象
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    mapping_cfg = config.get('ma_freq_mapping', {})
    return MAFreqMapping(
        ma_min=mapping_cfg.get('ma_min', 4.0),
        ma_max=mapping_cfg.get('ma_max', 20.0),
        freq_min=mapping_cfg.get('freq_min', 49.8),
        freq_max=mapping_cfg.get('freq_max', 50.2)
    )


def convert_input_command(args):
    """处理 convert-input 命令"""
    if hasattr(args, 'config') and args.config:
        mapping = load_mapping_from_config(args.config)
        print(f"📋 从配置文件加载映射参数: {args.config}")
    else:
        mapping = MAFreqMapping(
            ma_min=args.ma_min,
            ma_max=args.ma_max,
            freq_min=args.freq_min,
            freq_max=args.freq_max
        )

    print("🔄 开始转换频率输入为 mA 输入...")
    count = MAInputConverter.convert_freq_to_ma_csv(
        args.input,
        args.output,
        mapping
    )

    print(f"✅ 成功转换 {count} 行数据")
    print(f"   输入: {args.input}")
    print(f"   输出: {args.output}")
    print(f"   映射: {mapping.freq_min}-{mapping.freq_max} Hz → {mapping.ma_min}-{mapping.ma_max} mA")


def convert_output_command(args):
    """处理 convert-output 命令"""
    print("🔄 开始转换 mA 输出为标准格式（每毫秒均值）...")
    count = MAOutputParser.parse_and_convert_to_standard(
        args.input,
        args.output
    )

    print(f"✅ 成功转换 {count} 行数据")
    print(f"   输入: {args.input}")
    print(f"   输出: {args.output}")
    print("   格式: YYYY-MM-DD HH:MM:SS.微秒 → YYYY/MM/DD HH:MM:SS::毫秒 (每毫秒均值)")


def main():
    parser = argparse.ArgumentParser(
        description="4-20mA 数据处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用默认映射转换频率输入
python Scripts/measure_comparison_plot/ma_data_converter.py convert-input -i \\
       Tests/4-20mA测试/DEWE高精度测试/251209test_dynamic.csv -o dynamic_4-20ma_input.csv

  # 使用配置文件中的映射参数
  python ma_data_converter.py convert-input -c config.json -i input.csv -o output.csv

  # 自定义映射范围
  python ma_data_converter.py convert-input -i input.csv -o output.csv \\
         --ma-min 4 --ma-max 20 --freq-min 49.5 --freq-max 50.5

  # 转换 mA 输出为标准格式（按毫秒求均值）
python Scripts/measure_comparison_plot/ma_data_converter.py convert-output -i \\
       Tests/4-20mA测试/DEWE高精度测试/dynamic_4-20ma_20251211_1113.csv \\
       -o dynamic_4-20ma_output.csv
        """
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    input_parser = subparsers.add_parser(
        'convert-input',
        help='将频率输入 CSV 转换为 mA 输入 CSV'
    )
    input_parser.add_argument('-i', '--input', required=True, help='输入频率 CSV 路径')
    input_parser.add_argument('-o', '--output', required=True, help='输出 mA CSV 路径')
    input_parser.add_argument('-c', '--config', help='配置文件路径（可选，用于加载 ma_freq_mapping）')
    input_parser.add_argument('--ma-min', type=float, default=4.0, help='mA 最小值（默认 4）')
    input_parser.add_argument('--ma-max', type=float, default=20.0, help='mA 最大值（默认 20）')
    input_parser.add_argument('--freq-min', type=float, default=49.8, help='频率最小值（默认 49.8）')
    input_parser.add_argument('--freq-max', type=float, default=50.2, help='频率最大值（默认 50.2）')

    output_parser = subparsers.add_parser(
        'convert-output',
        help='将 mA 输出 CSV 转换为标准格式（按毫秒求均值）'
    )
    output_parser.add_argument('-i', '--input', required=True, help='输入 mA 输出 CSV 路径')
    output_parser.add_argument('-o', '--output', required=True, help='输出标准格式 CSV 路径')

    args = parser.parse_args()

    if args.command == 'convert-input':
        convert_input_command(args)
    elif args.command == 'convert-output':
        convert_output_command(args)


if __name__ == '__main__':
    main()
