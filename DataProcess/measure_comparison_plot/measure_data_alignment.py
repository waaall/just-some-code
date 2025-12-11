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

from measure_data_parser import MeasurementDataset


@dataclass
class AlignmentReport:
    """对齐结果报告"""
    input_change_index: Optional[int]      # 输入变化点索引
    output_change_index: Optional[int]     # 输出变化点索引
    input_change_time_ms: Optional[int]    # 输入变化点时间戳(ms)
    output_change_time_ms: Optional[int]   # 输出变化点时间戳(ms)
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

    def align_datasets(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset,
        enable_align: bool = True,
        manual_time_offset_ms: Optional[int] = None
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

        Returns:
            (对齐后的输入数据, 对齐后的输出数据, 对齐报告)

        Raises:
            ValueError: 如果输入输出数据单位不匹配
        """
        # 单位一致性检查
        if input_data.data_unit and output_data.data_unit:
            if input_data.data_unit != output_data.data_unit:
                raise ValueError(
                    f"输入数据单位 '{input_data.data_unit}' 与输出数据单位 '{output_data.data_unit}' 不匹配"
                )

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

        # 手动偏移量模式：直接应用指定的时间偏移
        if manual_time_offset_ms is not None:
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


# 测试代码
if __name__ == '__main__':
    import os
    from measure_data_parser import InputDataParser, OutputDataParser

    print("=" * 60)
    print("测试时间对齐功能")
    print("=" * 60)

    # 加载测试数据
    input_file = "../251209test200ms.csv"
    output_file = "../251209test200ms-result.csv"

    if not os.path.exists(input_file) or not os.path.exists(output_file):
        print("测试文件不存在，跳过测试")
    else:
        # 解析数据
        print("\n1. 解析数据...")
        input_data = InputDataParser.parse_csv(input_file)
        output_data = OutputDataParser.parse_csv(output_file)
        print(f"   输入数据: {len(input_data.data_points)} 点")
        print(f"   输出数据: {len(output_data.data_points)} 点")

        # 创建对齐器
        print("\n2. 创建对齐器(阈值: 0.002Hz)...")
        aligner = DataAlignment(change_threshold=0.002, threshold_unit="Hz")

        # 查找变化点
        print("\n3. 查找变化点...")
        input_change_idx = aligner.find_first_change_point(input_data)
        output_change_idx = aligner.find_first_change_point(output_data)

        if input_change_idx is not None:
            point = input_data.data_points[input_change_idx]
            print(f"   输入变化点: 索引{input_change_idx}, "
                  f"时间{point.timestamp_ms}ms, 值{point.value:.3f}")
        else:
            print("   输入数据无变化点")

        if output_change_idx is not None:
            point = output_data.data_points[output_change_idx]
            print(f"   输出变化点: 索引{output_change_idx}, "
                  f"时间{point.timestamp_ms}ms, 值{point.value:.3f}")
        else:
            print("   输出数据无变化点")

        # 执行对齐
        print("\n4. 执行对齐...")
        aligned_input, aligned_output, report = aligner.align_datasets(
            input_data, output_data, enable_align=True
        )

        # 打印对齐报告
        print("\n5. 对齐报告:")
        print(f"   状态: {report.message}")
        print(f"   是否对齐: {report.aligned}")
        print(f"   时间偏移: {report.time_offset_ms}ms")

        if report.aligned:
            print("\n6. 对齐后的时间戳:")
            print(f"   输入变化点: {report.input_change_time_ms}ms")
            print(f"   输出变化点(对齐后): "
                  f"{aligned_output.data_points[report.output_change_index].timestamp_ms}ms")

            # 验证对齐
            diff = (aligned_output.data_points[report.output_change_index].timestamp_ms -
                    report.input_change_time_ms)
            print(f"   对齐误差: {diff}ms (应该接近0)")
