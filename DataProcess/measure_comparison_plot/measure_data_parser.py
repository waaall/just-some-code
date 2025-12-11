#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测量数据解析模块（通用）

功能：
1. 解析输入CSV格式（阶梯变化数据）: 2025-12-9,10:00:00,000,49.900
2. 解析输出CSV格式（连续记录数据）: 2025/12/09 10:01:37::608,50.000
3. 统一时间戳为相对毫秒数
4. 支持任意单位的测量数据（频率/电流/电压等）
5. 支持列名匹配（优先）和列索引（回退）两种方式
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import csv


@dataclass
class MeasurementDataPoint:
    """单个测量数据点（通用）"""
    timestamp_ms: int      # 相对时间戳（从第一个点开始的毫秒数）
    value: float           # 测量值（通用，如频率/电流/电压等）
    raw_datetime: str      # 原始时间字符串（调试用）


@dataclass
class MeasurementDataset:
    """测量数据集（通用）"""
    data_points: List[MeasurementDataPoint]
    data_type: str                    # 'input' 或 'output'
    start_time_abs: datetime          # 绝对起始时间
    data_label: str = ""              # 数据标签（如 "Frequency", "Current"）
    data_unit: str = ""               # 数据单位（如 "Hz", "mA"）


def _detect_header(first_row: List[str]) -> bool:
    """
    检测首行是否为 header

    策略：如果首行包含非数字字段（如 "Date", "Time", "频率"），判定为 header

    Args:
        first_row: CSV 首行数据

    Returns:
        True 如果是 header，False 否则
    """
    for cell in first_row:
        try:
            float(cell.strip())
        except ValueError:
            # 非数字，检查是否包含常见 header 关键词
            cell_lower = cell.lower()
            if any(keyword in cell_lower for keyword in
                   ['date', 'time', 'freq', '频率', 'ma', '电流', 'current', 'volt', '电压']):
                return True
    return False


class InputDataParser:
    """输入数据解析器（阶梯变化格式）"""

    @staticmethod
    def parse_csv(
        csv_path: str,
        value_column_name: Optional[str] = None,    # 列名（优先）
        value_column_index: int = 3,                # 列索引（回退）
        value_scale_factor: float = 1.0,            # 值缩放系数
        data_label: str = "",                       # 数据标签
        data_unit: str = ""                         # 数据单位
    ) -> MeasurementDataset:
        """
        解析输入CSV文件（通用版本）

        格式: 2025-12-9,10:00:00,000,49.900
              日期,时间,毫秒,测量值

        列选择策略:
        1. 如果指定 value_column_name 且 CSV 有 header，尝试匹配列名
        2. 如果匹配失败或无 header，使用 value_column_index
        3. 打印清晰的日志提示

        Args:
            csv_path: CSV文件路径
            value_column_name: 值列名称（优先匹配）
            value_column_index: 值列索引（回退）
            value_scale_factor: 值缩放系数
            data_label: 数据标签（如 "Frequency", "Current"）
            data_unit: 数据单位（如 "Hz", "mA"）

        Returns:
            MeasurementDataset对象
        """
        data_points = []
        start_time = None

        # 打开文件，处理可能的BOM
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)

            # 读取首行，检测 header 并确定值列索引
            try:
                first_row = next(reader)
            except StopIteration:
                raise ValueError(f"输入CSV文件为空: {csv_path}")

            has_header = _detect_header(first_row)

            # 确定值列索引
            value_idx = value_column_index  # 默认使用索引
            if has_header and value_column_name:
                try:
                    value_idx = first_row.index(value_column_name)
                    print(f"✓ 使用列名匹配: '{value_column_name}' (索引 {value_idx})")
                except ValueError:
                    value_idx = value_column_index
                    print(f"⚠ 列名 '{value_column_name}' 未找到，回退至索引 {value_column_index}")
            else:
                print(f"✓ 使用列索引: {value_column_index}")

            # 处理数据行（如果有 header 则跳过首行）
            start_line = 1 if has_header else 0
            rows_to_process = [first_row] if not has_header else []
            rows_to_process.extend(reader)

            for line_num, row in enumerate(rows_to_process, start=start_line + 1):
                # 跳过空行
                if not row or len(row) <= max(value_idx, 2):  # 确保有足够的列
                    continue

                try:
                    date_str = row[0].strip()
                    time_str = row[1].strip()
                    ms_str = row[2].strip()
                    value_str = row[value_idx].strip()

                    # 解析时间戳
                    dt = InputDataParser._parse_input_timestamp(
                        date_str, time_str, ms_str
                    )

                    # 解析值并应用缩放系数
                    value = float(value_str) * value_scale_factor

                    # 记录起始时间
                    if start_time is None:
                        start_time = dt

                    # 计算相对时间戳（毫秒）
                    delta_ms = int((dt - start_time).total_seconds() * 1000)

                    # 创建数据点
                    raw_datetime_str = f"{date_str} {time_str}.{ms_str}"
                    point = MeasurementDataPoint(
                        timestamp_ms=delta_ms,
                        value=value,
                        raw_datetime=raw_datetime_str
                    )
                    data_points.append(point)

                except (ValueError, IndexError) as e:
                    print(f"警告: 输入CSV第{line_num}行解析失败: {e}")
                    continue

        if not data_points:
            raise ValueError(f"输入CSV文件为空或无有效数据: {csv_path}")

        return MeasurementDataset(
            data_points=data_points,
            data_type='input',
            start_time_abs=start_time,
            data_label=data_label,
            data_unit=data_unit
        )

    @staticmethod
    def _parse_input_timestamp(date_str: str, time_str: str, ms_str: str) -> datetime:
        """
        解析输入时间格式

        输入格式: "2025-12-9", "10:00:00", "000"
        返回: datetime对象（精确到毫秒）
        """
        # 组合时间字符串（毫秒作为微秒的前三位）
        datetime_str = f"{date_str} {time_str}.{ms_str.zfill(3)}"

        # 解析datetime（自动处理单/双位数的月日）
        try:
            # 尝试标准格式
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            # 如果失败，尝试手动解析以支持单位数日期
            parts = date_str.split('-')
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])

            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            second = int(time_parts[2])

            millisecond = int(ms_str)

            return datetime(year, month, day, hour, minute, second, millisecond * 1000)


class OutputDataParser:
    """输出数据解析器（连续记录格式）"""

    @staticmethod
    def parse_csv(
        csv_path: str,
        value_column_name: Optional[str] = None,    # 列名（优先）
        value_column_index: int = 1,                # 列索引（回退）
        value_scale_factor: float = 1.0,            # 值缩放系数
        data_label: str = "",                       # 数据标签
        data_unit: str = ""                         # 数据单位
    ) -> MeasurementDataset:
        """
        解析输出CSV文件（通用版本）

        格式: 2025/12/09 10:01:37::608,50.000
              日期时间::毫秒,测量值

        Header: RX Date/Time,组/A_Freq

        列选择策略:
        1. 如果指定 value_column_name 且 CSV 有 header，尝试匹配列名
        2. 如果匹配失败或无 header，使用 value_column_index
        3. 打印清晰的日志提示

        Args:
            csv_path: CSV文件路径
            value_column_name: 值列名称（优先匹配）
            value_column_index: 值列索引（回退）
            value_scale_factor: 值缩放系数
            data_label: 数据标签（如 "Frequency", "Current"）
            data_unit: 数据单位（如 "Hz", "mA"）

        Returns:
            MeasurementDataset对象
        """
        data_points = []
        start_time = None

        # 打开文件，处理可能的BOM
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)

            # 读取首行，检测 header 并确定值列索引
            try:
                first_row = next(reader)
            except StopIteration:
                raise ValueError(f"输出CSV文件为空: {csv_path}")

            has_header = _detect_header(first_row)

            # 确定值列索引
            value_idx = value_column_index  # 默认使用索引
            if has_header and value_column_name:
                try:
                    value_idx = first_row.index(value_column_name)
                    print(f"✓ 使用列名匹配: '{value_column_name}' (索引 {value_idx})")
                except ValueError:
                    value_idx = value_column_index
                    print(f"⚠ 列名 '{value_column_name}' 未找到，回退至索引 {value_column_index}")
            else:
                print(f"✓ 使用列索引: {value_column_index}")

            # 处理数据行（如果有 header 则跳过首行）
            start_line = 1 if has_header else 0
            rows_to_process = [first_row] if not has_header else []
            rows_to_process.extend(reader)

            for line_num, row in enumerate(rows_to_process, start=start_line + 1):
                # 跳过空行
                if not row or len(row) <= max(value_idx, 0):  # 确保有足够的列
                    continue

                try:
                    datetime_str = row[0].strip()
                    value_str = row[value_idx].strip()

                    # 解析时间戳
                    dt = OutputDataParser._parse_output_timestamp(datetime_str)

                    # 解析值并应用缩放系数
                    value = float(value_str) * value_scale_factor

                    # 记录起始时间
                    if start_time is None:
                        start_time = dt

                    # 计算相对时间戳（毫秒）
                    delta_ms = int((dt - start_time).total_seconds() * 1000)

                    # 创建数据点
                    point = MeasurementDataPoint(
                        timestamp_ms=delta_ms,
                        value=value,
                        raw_datetime=datetime_str
                    )
                    data_points.append(point)

                except (ValueError, IndexError) as e:
                    print(f"警告: 输出CSV第{line_num}行解析失败: {e}")
                    continue

        if not data_points:
            raise ValueError(f"输出CSV文件为空或无有效数据: {csv_path}")

        return MeasurementDataset(
            data_points=data_points,
            data_type='output',
            start_time_abs=start_time,
            data_label=data_label,
            data_unit=data_unit
        )

    @staticmethod
    def _parse_output_timestamp(datetime_str: str) -> datetime:
        """
        解析输出时间格式

        输入格式: "2025/12/09 10:01:37::608"
        返回: datetime对象（精确到毫秒）
        """
        # 分割日期时间和毫秒部分
        if '::' in datetime_str:
            main_part, ms_part = datetime_str.split('::')
        else:
            raise ValueError(f"输出时间格式错误（缺少::）: {datetime_str}")

        # 解析主日期时间部分
        dt = datetime.strptime(main_part, "%Y/%m/%d %H:%M:%S")

        # 添加毫秒
        milliseconds = int(ms_part)
        dt = dt + timedelta(milliseconds=milliseconds)

        return dt


# 测试代码
if __name__ == '__main__':
    import os

    # 测试输入数据解析
    print("=" * 60)
    print("测试输入数据解析")
    print("=" * 60)

    input_file = "../251209test200ms.csv"
    if os.path.exists(input_file):
        input_data = InputDataParser.parse_csv(input_file)
        print(f"数据类型: {input_data.data_type}")
        print(f"起始时间: {input_data.start_time_abs}")
        print(f"数据点数: {len(input_data.data_points)}")
        print("\n前5个数据点:")
        for i, point in enumerate(input_data.data_points[:5]):
            print(f"  [{i}] {point.timestamp_ms:6d}ms -> {point.value:.3f}")
        print("\n后5个数据点:")
        for i, point in enumerate(input_data.data_points[-5:]):
            idx = len(input_data.data_points) - 5 + i
            print(f"  [{idx}] {point.timestamp_ms:6d}ms -> {point.value:.3f}")
    else:
        print(f"文件不存在: {input_file}")

    # 测试输出数据解析
    print("\n" + "=" * 60)
    print("测试输出数据解析")
    print("=" * 60)

    output_file = "../251209test200ms-result.csv"
    if os.path.exists(output_file):
        output_data = OutputDataParser.parse_csv(output_file)
        print(f"数据类型: {output_data.data_type}")
        print(f"起始时间: {output_data.start_time_abs}")
        print(f"数据点数: {len(output_data.data_points)}")
        print("\n前5个数据点:")
        for i, point in enumerate(output_data.data_points[:5]):
            print(f"  [{i}] {point.timestamp_ms:6d}ms -> {point.value:.3f}")
        print("\n后5个数据点:")
        for i, point in enumerate(output_data.data_points[-5:]):
            idx = len(output_data.data_points) - 5 + i
            print(f"  [{idx}] {point.timestamp_ms:6d}ms -> {point.value:.3f}")
    else:
        print(f"文件不存在: {output_file}")
