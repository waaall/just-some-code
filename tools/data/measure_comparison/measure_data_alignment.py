#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测量数据时间对齐模块（通用）

功能：
1. 检测数据集的首个显著变化点
2. 对齐输入输出数据集的时间轴
3. 生成对齐报告
4. 支持任意单位的测量数据（频率/电流/电压等）
5. 验证阈值单位与数据单位一致性
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import copy
from pathlib import Path

from measure_data_parser import MeasurementDataset


@dataclass
class AlignmentReport:
    """对齐结果报告"""
    input_change_index: Optional[int]      # 输入变化点索引
    output_change_index: Optional[int]     # 输出变化点索引
    input_change_time_ms: Optional[int]    # 输入变化点时间戳(ms)，自动对齐有效；手动对齐为None
    output_change_time_ms: Optional[int]   # 输出变化/参考点时间戳(ms)，手动对齐为对齐起点的原始输出时间
    time_offset_ms: int                    # 应用的时间偏移量(ms)
    aligned: bool                          # 是否成功对齐
    message: str                           # 对齐状态说明


class DataAlignment:
    """测量数据对齐器（通用）"""

    def __init__(self, change_threshold: float = 0.002, threshold_unit: str = "Hz"):
        """
        初始化对齐器

        Args:
            change_threshold: 变化阈值（数值），默认0.002
            threshold_unit: 阈值单位（如 "Hz", "mA", "V"），默认"Hz"
        """
        self.change_threshold = change_threshold
        self.threshold_unit = threshold_unit

    def _save_aligned_csv(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset,
        aligned_csv_path: str,
        input_base_ms: int = 0
    ) -> None:
        """
        内部方法：将对齐后的输入/输出数据导出为CSV，便于对比。

        输出格式：
            aligned_ms,input_value,output_value,raw_datetime

        aligned_ms 为对齐后的输出时间戳（ms），input_value 为对应时刻的输入阶梯值，
        output_value 为对齐后的输出测量值，raw_datetime 来自输出数据原始时间字符串。

        输入值查找策略（阶梯保持）：
        - 对每个输出时间点，查找输入数据中最近的前一个点（或等于该时间点）
        - 边界情况：如果查找时间超出输入数据范围，使用首/末点的值
        - 适用于阶梯变化的输入信号（如频率设定值）

        Args:
            input_data: 输入数据集（未裁剪）
            output_data: 对齐且裁剪后的输出数据集
            aligned_csv_path: 输出CSV文件路径
            input_base_ms: 输入时间基准（对齐后输出0ms对应的输入时间ms）
        """
        if not aligned_csv_path:
            return

        out_file = Path(aligned_csv_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        input_points = input_data.data_points
        input_index = 0
        current_input_value = input_points[0].value if input_points else None

        with out_file.open('w', encoding='utf-8', newline='') as f:
            f.write("aligned_ms,input_value,output_value,raw_datetime\n")
            for out_point in output_data.data_points:
                target_input_time_ms = out_point.timestamp_ms + input_base_ms

                if input_points:
                    while (input_index + 1 < len(input_points) and
                           input_points[input_index + 1].timestamp_ms <= target_input_time_ms):
                        input_index += 1
                    current_input_value = input_points[input_index].value

                    input_value_str = f"{current_input_value:.6f}"
                else:
                    input_value_str = ""

                f.write(
                    f"{out_point.timestamp_ms},"
                    f"{input_value_str},"
                    f"{out_point.value:.6f},"
                    f"{out_point.raw_datetime}\n"
                )

        print(f"已导出对齐CSV: {out_file}")

    def find_first_change_point(self, dataset: MeasurementDataset) -> Optional[int]:
        """
        查找首个显著变化点的索引（通用版本）

        算法:
        1. 验证数据单位与阈值单位一致
        2. 取第一个点作为参考值 value_ref
        3. 遍历数据点，计算 |value - value_ref|
        4. 当变化量 >= change_threshold 时返回该索引
        5. 若无变化点则返回 None

        Args:
            dataset: 测量数据集

        Returns:
            首个变化点的索引，若无则返回None

        Raises:
            ValueError: 如果阈值单位与数据单位不匹配
        """
        # 单位一致性检查
        if dataset.data_unit and dataset.data_unit != self.threshold_unit:
            raise ValueError(
                f"阈值单位 '{self.threshold_unit}' 与数据单位 '{dataset.data_unit}' 不匹配"
            )

        if not dataset.data_points:
            return None

        # 取第一个点作为参考值
        value_ref = dataset.data_points[0].value

        # 遍历查找首个变化点
        for i, point in enumerate(dataset.data_points):
            change = abs(point.value - value_ref)
            if change >= self.change_threshold:
                return i

        # 无变化点
        return None

    def _validate_units(self, input_data: MeasurementDataset, output_data: MeasurementDataset) -> None:
        """验证输入输出数据单位一致性。"""
        if input_data.data_unit and output_data.data_unit:
            if input_data.data_unit != output_data.data_unit:
                raise ValueError(
                    f"输入数据单位 '{input_data.data_unit}' 与输出数据单位 '{output_data.data_unit}' 不匹配"
                )

    def _align_with_manual_offset(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset,
        manual_time_offset_ms: int
    ) -> Tuple[MeasurementDataset, MeasurementDataset, AlignmentReport]:
        """手动时间偏移量对齐实现。"""
        # 创建对齐后的输出数据(深拷贝)
        aligned_output_data = copy.deepcopy(output_data)

        # 对所有时间戳应用手动偏移量
        for point in aligned_output_data.data_points:
            point.timestamp_ms = point.timestamp_ms - manual_time_offset_ms

        # 找到对齐后的起点（首个时间戳>=0）
        start_idx = next(
            (i for i, point in enumerate(aligned_output_data.data_points)
             if point.timestamp_ms >= 0),
            None
        )

        # 如果偏移量超出范围，返回未对齐报告
        if start_idx is None:
            report = AlignmentReport(
                input_change_index=None,
                output_change_index=None,
                input_change_time_ms=None,
                output_change_time_ms=None,
                time_offset_ms=manual_time_offset_ms,
                aligned=False,
                message="手动偏移量导致输出数据全部在参考点之前，无法对齐"
            )
            return input_data, output_data, report

        # 裁剪起点并重基准化到参考点
        base_time_shifted = aligned_output_data.data_points[start_idx].timestamp_ms
        base_time_original = base_time_shifted + manual_time_offset_ms
        aligned_output_data.data_points = aligned_output_data.data_points[start_idx:]
        for point in aligned_output_data.data_points:
            point.timestamp_ms = point.timestamp_ms - base_time_shifted

        # 生成对齐报告
        report = AlignmentReport(
            input_change_index=None,
            output_change_index=0,
            input_change_time_ms=None,
            output_change_time_ms=base_time_original,
            time_offset_ms=manual_time_offset_ms,
            aligned=True,
            message=f"使用手动偏移量对齐: {manual_time_offset_ms}ms"
        )

        return input_data, aligned_output_data, report

    def _align_with_auto_detection(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset
    ) -> Tuple[MeasurementDataset, MeasurementDataset, AlignmentReport]:
        """自动变化点检测对齐实现。"""
        # 查找输入数据的首个变化点
        input_change_idx = self.find_first_change_point(input_data)

        # 查找输出数据的首个变化点
        output_change_idx = self.find_first_change_point(output_data)

        unit_suffix = f" {self.threshold_unit}" if self.threshold_unit else ""

        # 检查是否找到变化点
        if input_change_idx is None:
            report = AlignmentReport(
                input_change_index=None,
                output_change_index=output_change_idx,
                input_change_time_ms=None,
                output_change_time_ms=(
                    output_data.data_points[output_change_idx].timestamp_ms
                    if output_change_idx is not None else None
                ),
                time_offset_ms=0,
                aligned=False,
                message=f"输入数据无显著变化(阈值: {self.change_threshold}{unit_suffix})"
            )
            return input_data, output_data, report

        if output_change_idx is None:
            report = AlignmentReport(
                input_change_index=input_change_idx,
                output_change_index=None,
                input_change_time_ms=input_data.data_points[input_change_idx].timestamp_ms,
                output_change_time_ms=None,
                time_offset_ms=0,
                aligned=False,
                message=f"输出数据无显著变化(阈值: {self.change_threshold}{unit_suffix})"
            )
            return input_data, output_data, report

        # 获取变化点的时间戳
        input_change_time = input_data.data_points[input_change_idx].timestamp_ms
        output_change_time = output_data.data_points[output_change_idx].timestamp_ms

        # 计算时间偏移(输出相对输入的延迟)
        time_offset_ms = output_change_time - input_change_time

        # 创建对齐后的输出数据(深拷贝，避免修改原数据)，同时裁掉变化前的数据
        aligned_output_data = copy.deepcopy(output_data)
        aligned_output_data.data_points = aligned_output_data.data_points[output_change_idx:]

        # 以输出变化点为“起点”，时间基准对齐到该点（ms级），其余点减去首变点的时间偏移
        base_time = aligned_output_data.data_points[0].timestamp_ms
        for point in aligned_output_data.data_points:
            point.timestamp_ms = point.timestamp_ms - base_time

        # 生成对齐报告
        report = AlignmentReport(
            input_change_index=input_change_idx,
            output_change_index=0,  # 已裁剪，变化点位于索引0
            input_change_time_ms=input_change_time,
            output_change_time_ms=output_change_time,
            time_offset_ms=time_offset_ms,
            aligned=True,
            message=f"对齐成功，时间偏移: {time_offset_ms}ms"
        )

        # 输入数据保持不变
        return input_data, aligned_output_data, report

    def align_datasets(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset,
        enable_align: bool = True,
        manual_time_offset_ms: Optional[int] = None,
        aligned_csv_path: Optional[str] = None
    ) -> Tuple[MeasurementDataset, MeasurementDataset, AlignmentReport]:
        """
        对齐输入输出数据集（通用版本）

        算法:
        1. 验证输入输出数据单位一致
        2. 如果提供了manual_time_offset_ms，使用手动偏移量模式
        3. 否则，查找输入数据的首个变化点 t_input_change
        4. 查找输出数据的首个变化点 t_output_change
        5. 计算时间差 delta_t = t_output_change - t_input_change
        6. 将输出数据的所有时间戳减去 delta_t（或手动偏移量）
        7. 生成对齐报告

        Args:
            input_data: 输入数据集
            output_data: 输出数据集
            enable_align: 是否启用对齐，False则直接返回原始数据
            manual_time_offset_ms: 手动指定的时间偏移量(ms)，如果提供则跳过自动检测
            aligned_csv_path: 若提供，则在对齐后保存CSV（aligned_ms,input_value,output_value,raw_datetime）

        Returns:
            (对齐后的输入数据, 对齐后的输出数据, 对齐报告)

        Raises:
            ValueError: 如果输入输出数据单位不匹配
        """
        self._validate_units(input_data, output_data)

        # 如果禁用对齐，直接返回
        if not enable_align:
            report = AlignmentReport(
                input_change_index=None,
                output_change_index=None,
                input_change_time_ms=None,
                output_change_time_ms=None,
                time_offset_ms=0,
                aligned=False,
                message="对齐功能已禁用"
            )
            return input_data, output_data, report

        if manual_time_offset_ms is not None:
            aligned_input, aligned_output, report = self._align_with_manual_offset(
                input_data, output_data, manual_time_offset_ms
            )
            input_base_ms = 0
            if report.aligned and report.output_change_time_ms is not None:
                input_base_ms = report.output_change_time_ms - report.time_offset_ms
        else:
            aligned_input, aligned_output, report = self._align_with_auto_detection(
                input_data, output_data
            )
            input_base_ms = 0
            if report.aligned and report.input_change_time_ms is not None:
                input_base_ms = report.input_change_time_ms

        if aligned_csv_path:
            self._save_aligned_csv(aligned_input, aligned_output, aligned_csv_path, input_base_ms)

        return aligned_input, aligned_output, report


# 测试代码
if __name__ == '__main__':
    import os
    from measure_data_parser import DataFormatParser

    print("=" * 60)
    print("测试时间对齐功能")
    print("=" * 60)

    input_file = "../251209test200ms.csv"
    output_file = "../251209test200ms-result.csv"

    if not os.path.exists(input_file) or not os.path.exists(output_file):
        print("\n测试文件不存在，跳过测试")
    else:
        # 解析数据并创建对齐器
        input_data = DataFormatParser.parse_csv(input_file, data_type='input')
        output_data = DataFormatParser.parse_csv(output_file, data_type='output')
        aligner = DataAlignment(change_threshold=0.002, threshold_unit="Hz")

        print(f"\n数据点数: 输入{len(input_data.data_points)}, 输出{len(output_data.data_points)}")

        # 执行对齐（自动检测变化点）并导出CSV
        aligned_input, aligned_output, report = aligner.align_datasets(
            input_data, output_data,
            enable_align=True,
            aligned_csv_path="../test_aligned.csv"
        )

        # 打印对齐结果
        print(f"\n对齐结果: {report.message}")
        if report.aligned:
            print(f"  时间偏移: {report.time_offset_ms}ms")
            print(f"  输入变化点: 索引{report.input_change_index}, {report.input_change_time_ms}ms")
            print(f"  输出变化点: 对齐后索引0, 原始时间{report.output_change_time_ms}ms")
        else:
            print(f"  未能对齐: {report.message}")
