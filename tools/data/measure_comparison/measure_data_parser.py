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
from abc import ABC, abstractmethod
import csv
import re


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


# ============================================================================
# 格式规范基类和具体实现
# ============================================================================

class FormatSpec(ABC):
    """数据格式规范基类（抽象接口）"""

    @property
    @abstractmethod
    def default_value_index(self) -> int:
        """默认值列索引"""
        pass

    @abstractmethod
    def detect(self, row: List[str]) -> bool:
        """
        检测该行是否匹配此格式

        Args:
            row: CSV 行数据

        Returns:
            True 如果匹配，False 否则
        """
        pass

    @abstractmethod
    def parse_timestamp(self, row: List[str]) -> datetime:
        """
        从行中解析时间戳

        Args:
            row: CSV 行数据

        Returns:
            datetime 对象（精确到毫秒）
        """
        pass


class Format1Spec(FormatSpec):
    """
    格式一规范：4列格式

    示例：2025-12-9,10:00:00,000,49.900
    结构：日期,时间,毫秒,测量值
    """

    @property
    def default_value_index(self) -> int:
        return 3

    def detect(self, row: List[str]) -> bool:
        """
        检测条件：
        - len(row) >= 4
        - row[0] 匹配 YYYY-M-D 或 YYYY-MM-DD（含 -）
        - row[1] 匹配 HH:MM:SS
        - row[2] 为 1-3 位数字毫秒
        """
        if len(row) < 4:
            return False

        try:
            # 检查 row[0]: YYYY-M-D 或 YYYY-MM-DD
            date_pattern = r'^\d{4}-\d{1,2}-\d{1,2}$'
            if not re.match(date_pattern, row[0].strip()):
                return False

            # 检查 row[1]: HH:MM:SS
            time_pattern = r'^\d{1,2}:\d{2}:\d{2}$'
            if not re.match(time_pattern, row[1].strip()):
                return False

            # 检查 row[2]: 1-3 位数字
            ms_pattern = r'^\d{1,3}$'
            if not re.match(ms_pattern, row[2].strip()):
                return False

            return True
        except (IndexError, AttributeError):
            return False

    def parse_timestamp(self, row: List[str]) -> datetime:
        """解析格式一的时间戳"""
        date_str = row[0].strip()
        time_str = row[1].strip()
        ms_str = row[2].strip()

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


class Format2Spec(FormatSpec):
    """
    格式二规范：2列格式

    示例：2025/12/09 10:01:37::608,50.000
    结构：日期时间::毫秒,测量值
    """

    @property
    def default_value_index(self) -> int:
        return 1

    def detect(self, row: List[str]) -> bool:
        """
        检测条件：
        - len(row) >= 2
        - row[0] 含 ::
        - 拆分后主串匹配 YYYY/MM/DD HH:MM:SS 或 YYYY/M/D HH:MM:SS
        - 毫秒段为数字
        """
        if len(row) < 2:
            return False

        try:
            datetime_str = row[0].strip()

            # 检查是否包含 ::
            if '::' not in datetime_str:
                return False

            # 拆分
            main_part, ms_part = datetime_str.split('::')

            # 检查主串格式：YYYY/MM/DD HH:MM:SS（支持单/双位数月日）
            main_pattern = r'^\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}:\d{2}$'
            if not re.match(main_pattern, main_part.strip()):
                return False

            # 检查毫秒段：纯数字
            if not ms_part.strip().isdigit():
                return False

            return True
        except (IndexError, AttributeError, ValueError):
            return False

    def parse_timestamp(self, row: List[str]) -> datetime:
        """解析格式二的时间戳"""
        datetime_str = row[0].strip()

        # 分割日期时间和毫秒部分
        if '::' not in datetime_str:
            raise ValueError(f"输出时间格式错误（缺少::）: {datetime_str}")

        main_part, ms_part = datetime_str.split('::')

        # 解析主日期时间部分
        dt = datetime.strptime(main_part, "%Y/%m/%d %H:%M:%S")

        # 添加毫秒
        milliseconds = int(ms_part)
        dt = dt + timedelta(milliseconds=milliseconds)

        return dt


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


def _detect_format_from_sample(
    rows: List[List[str]],
    specs: List[FormatSpec],
    sample_size: int = 10,
    threshold: float = 0.8
) -> FormatSpec:
    """
    从样本行中检测数据格式

    策略：抽样前 N 行，统计每个 spec 的命中率，选择命中率最高且超过阈值的 spec

    Args:
        rows: 数据行列表（已过滤 header 和空行）
        specs: 格式规范列表
        sample_size: 抽样大小（默认 10 行）
        threshold: 命中率阈值（默认 0.8，即 80%）

    Returns:
        检测到的格式规范

    Raises:
        ValueError: 格式不一致或未知
    """
    # 限制样本大小
    sample_rows = rows[:min(sample_size, len(rows))]

    if not sample_rows:
        raise ValueError("没有可用的数据行进行格式检测")

    # 统计每个 spec 的命中次数
    spec_hits = {spec: 0 for spec in specs}

    for row in sample_rows:
        for spec in specs:
            if spec.detect(row):
                spec_hits[spec] += 1

    # 找到命中率最高的 spec
    best_spec = max(spec_hits, key=spec_hits.get)
    best_hits = spec_hits[best_spec]
    hit_rate = best_hits / len(sample_rows)

    # 检查命中率
    if hit_rate < threshold:
        raise ValueError(
            f"格式检测失败：最高命中率为 {hit_rate:.1%}（阈值 {threshold:.0%}），"
            f"可能是未知格式或混合格式"
        )

    # 打印检测结果
    spec_name = best_spec.__class__.__name__
    print(f"✓ 检测到格式: {spec_name} (命中率 {hit_rate:.1%})")

    return best_spec


class DataFormatParser:
    """输入数据解析器（支持多种格式自动识别）"""

    # 支持的格式规范列表
    SUPPORTED_FORMATS = [Format1Spec(), Format2Spec()]

    @staticmethod
    def parse_csv(
        csv_path: str,
        value_column_name: Optional[str] = None,    # 列名（优先）
        value_column_index: Optional[int] = None,   # 列索引（如果不指定，使用格式默认值）
        value_scale_factor: float = 1.0,            # 值缩放系数
        data_label: str = "",                       # 数据标签
        data_unit: str = "",                        # 数据单位
        format_specs: Optional[List[FormatSpec]] = None,  # 自定义格式规范列表（默认使用 SUPPORTED_FORMATS）
        data_type: str = 'input'                    # 数据模式标记（与时间戳格式独立）
    ) -> MeasurementDataset:
        """
        解析CSV文件（自动识别格式）

        支持时间戳格式：
        - 格式一: 2025-12-9,10:00:00,000,49.900
        - 格式二: 2025/12/09 10:01:37::608,50.000

        列选择策略:
        1. 自动检测数据格式（Format1Spec 或 Format2Spec）
        2. 如果未指定 value_column_index，使用格式默认值（格式一=3，格式二=1）
        3. 如果指定 value_column_name 且 CSV 有 header，尝试匹配列名
        4. 打印清晰的日志提示

        Args:
            csv_path: CSV文件路径
            value_column_name: 值列名称（优先匹配）
            value_column_index: 值列索引（如果不指定，使用格式默认值）
            value_scale_factor: 值缩放系数
            data_label: 数据标签（如 "Frequency", "Current"）
            data_unit: 数据单位（如 "Hz", "mA"）
            format_specs: 自定义格式规范列表（默认使用 SUPPORTED_FORMATS）

        Returns:
            MeasurementDataset对象
        """
        # 使用默认格式规范列表（如果未提供）
        if format_specs is None:
            format_specs = DataFormatParser.SUPPORTED_FORMATS

        data_points = []
        start_time = None

        # 打开文件，处理可能的BOM
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)

            # 读取首行，检测 header
            try:
                first_row = next(reader)
            except StopIteration:
                raise ValueError(f"CSV文件为空: {csv_path}")

            has_header = _detect_header(first_row)

            # 收集数据行用于格式检测
            rows_to_process = [] if has_header else [first_row]
            rows_to_process.extend(reader)

            # 过滤空行
            non_empty_rows = [row for row in rows_to_process if row and any(cell.strip() for cell in row)]

            if not non_empty_rows:
                raise ValueError(f"CSV文件无有效数据: {csv_path}")

            # 格式检测
            detected_spec = _detect_format_from_sample(non_empty_rows, format_specs)

            # 确定值列索引：显式指定优先，否则使用格式默认值
            explicit_index_provided = value_column_index is not None
            value_idx = value_column_index if explicit_index_provided else detected_spec.default_value_index
            value_idx_from_name = False

            # 如果有 header 且指定了列名，尝试匹配
            if has_header and value_column_name:
                try:
                    value_idx = first_row.index(value_column_name)
                    value_idx_from_name = True
                    print(f"✓ 使用列名匹配: '{value_column_name}' (索引 {value_idx})")
                except ValueError:
                    print(f"⚠ 列名 '{value_column_name}' 未找到，使用索引 {value_idx}")
            else:
                print(f"✓ 使用列索引: {value_idx}")

            # 若用户显式指定的索引对多数样本行无效，则回退到格式默认索引
            if explicit_index_provided and not value_idx_from_name:
                sample_n = min(10, len(non_empty_rows))
                valid_n = sum(1 for r in non_empty_rows[:sample_n] if len(r) > value_idx)
                if sample_n > 0 and (valid_n / sample_n) < 0.5:
                    fallback_idx = detected_spec.default_value_index
                    if fallback_idx != value_idx:
                        print(
                            f"⚠ 值列索引 {value_idx} 对多数样本行无效，"
                            f"回退到格式默认索引 {fallback_idx}"
                        )
                        value_idx = fallback_idx

            # 解析数据行
            for line_num, row in enumerate(non_empty_rows, start=1 if has_header else 0):
                # 检查列数
                if len(row) <= value_idx:
                    print(f"警告: 第{line_num}行列数不足，跳过")
                    continue

                try:
                    # 使用检测到的格式解析时间戳
                    dt = detected_spec.parse_timestamp(row)

                    # 解析值并应用缩放系数
                    value_str = row[value_idx].strip()
                    value = float(value_str) * value_scale_factor

                    # 记录起始时间
                    if start_time is None:
                        start_time = dt

                    # 计算相对时间戳（毫秒）
                    delta_ms = int((dt - start_time).total_seconds() * 1000)

                    # 创建数据点（raw_datetime 根据格式选择）
                    if isinstance(detected_spec, Format2Spec):
                        raw_datetime = row[0]
                    else:  # Format1Spec
                        raw_datetime = f"{row[0]} {row[1]}.{row[2]}"

                    point = MeasurementDataPoint(
                        timestamp_ms=delta_ms,
                        value=value,
                        raw_datetime=raw_datetime
                    )
                    data_points.append(point)

                except (ValueError, IndexError) as e:
                    print(f"警告: 第{line_num}行解析失败: {e}")
                    continue

        if not data_points:
            raise ValueError(f"CSV文件无有效数据: {csv_path}")

        return MeasurementDataset(
            data_points=data_points,
            data_type=data_type,  # 使用参数指定的 data_type
            start_time_abs=start_time,
            data_label=data_label,
            data_unit=data_unit
        )


# 测试代码
if __name__ == '__main__':
    import os

    # 测试输入数据解析
    print("=" * 60)
    print("测试输入数据解析")
    print("=" * 60)

    input_file = "../251209test200ms.csv"
    if os.path.exists(input_file):
        input_data = DataFormatParser.parse_csv(input_file)
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
