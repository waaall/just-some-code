#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测量数据对比绘图核心模块（通用）

功能：
1. 绘制阶梯图（输入数据）
2. 绘制点图/折线图（输出数据）
3. 鼠标交互（显示双y值）
4. 图表美化与导出
5. 支持任意单位的测量数据（频率/电流/电压等）
6. 模板化标签和格式化字符串
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import math

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.ticker import MultipleLocator

from measure_data_parser import MeasurementDataset, MeasurementDataPoint
from measure_data_alignment import AlignmentReport


@dataclass
class PlotConfig:
    """绘图配置（通用）"""
    # 模板化标签（新增）
    title_template: str = "{data_label} Compare (Input vs Output)"
    input_series_name: str = "Input (Source)"
    output_series_name: str = "Output (Measured)"
    y_axis_label: str = "{data_label} ({data_unit})"
    x_axis_label: str = "Time (s)"
    output_filename_template: str = "{data_label}_comparison_result.png"
    value_format: str = ".3f"  # 值格式化字符串

    # 图表尺寸
    figsize: Tuple[float, float] = (14, 6)  # 宽14英寸，高6英寸

    # 值轴范围（保留freq名称以向后兼容，语义映射为value_min/value_max）
    data_min: Optional[float] = None  # None则自动计算
    data_max: Optional[float] = None

    # 时间轴范围
    time_min: float = 0.0  # 起始时间（秒）
    time_max: Optional[float] = None  # None则自动计算

    # 绘图样式
    output_style: str = 'both'  # 'scatter', 'line', 'both'
    input_color: str = '#1f77b4'  # 蓝色
    output_color: str = '#ff7f0e'  # 橙色
    output_marker_size: float = 4.0  # 散点大小

    # 交互
    enable_cursor: bool = True

    # 导出
    dpi: int = 300
    output_filename: str = 'freq_comparison_result.png'


class DataPlotter:
    """测量数据对比绘图器（通用）"""

    def __init__(self, config: PlotConfig):
        """
        初始化绘图器

        Args:
            config: 绘图配置对象
        """
        self.config = config
        self.fig = None
        self.ax = None
        self.input_data = None
        self.output_data = None
        self.cursor_annotation = None

    def plot(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset,
        alignment_report: AlignmentReport
    ) -> Tuple[Figure, Axes]:
        """
        绘制测量数据对比图（通用版本）

        Args:
            input_data: 输入数据集
            output_data: 输出数据集
            alignment_report: 对齐报告

        Returns:
            (Figure对象, Axes对象)
        """
        # 保存数据引用（用于交互）
        self.input_data = input_data
        self.output_data = output_data

        # 准备模板变量
        template_vars = {
            'data_label': input_data.data_label or "Data",
            'data_unit': input_data.data_unit or ""
        }

        # 创建图表
        self.fig, self.ax = plt.subplots(figsize=self.config.figsize)

        # 绘制输入数据（阶梯图）
        self._plot_input_stepwise(self.ax, input_data)

        # 绘制输出数据（点图/折线图）
        self._plot_output_scatter(self.ax, output_data)

        # 配置坐标轴
        self._setup_time_axis(self.ax, input_data, output_data)
        self._setup_value_axis(self.ax, input_data, output_data)

        # 添加网格
        self.ax.grid(True, which='major', linestyle='-', alpha=0.3, linewidth=0.8)
        self.ax.grid(True, which='minor', linestyle=':', alpha=0.15, linewidth=0.5)

        # 添加图例
        self.ax.legend(loc='best', fontsize=10, framealpha=0.9)

        # 添加标题（应用模板）
        try:
            title = self.config.title_template.format(**template_vars)
        except KeyError:
            title = "Data Compare (Input vs Output)"  # 回退默认值

        if alignment_report.aligned:
            title += f"\nalign: {alignment_report.time_offset_ms}ms"
        self.ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

        # 设置轴标签（应用模板）
        try:
            y_label = self.config.y_axis_label.format(**template_vars)
        except KeyError:
            y_label = "Value"  # 回退默认值
        self.ax.set_ylabel(y_label, fontsize=11, fontweight='bold')

        x_label = self.config.x_axis_label
        self.ax.set_xlabel(x_label, fontsize=11, fontweight='bold')

        # 启用鼠标交互
        if self.config.enable_cursor:
            self._enable_interactive_cursor()

        # 调整布局
        self.fig.tight_layout()

        return self.fig, self.ax

    def _plot_input_stepwise(self, ax: Axes, data: MeasurementDataset):
        """
        绘制阶梯图（输入数据）

        Args:
            ax: 绘图轴
            data: 输入数据集
        """
        # 转换为秒单位
        time_s = [p.timestamp_ms / 1000.0 for p in data.data_points]
        values = [p.value for p in data.data_points]

        # 延伸最后一个阶梯平台（添加虚拟点）
        if len(time_s) > 0:
            # 延伸1秒或5%的时间跨度（取较大值）
            extend_time = max(1.0, (time_s[-1] - time_s[0]) * 0.05)
            time_s.append(time_s[-1] + extend_time)
            values.append(values[-1])

        # 绘制阶梯图
        ax.step(time_s, values, where='post',
                color=self.config.input_color, linewidth=1.5,
                label=self.config.input_series_name, zorder=2)

    def _plot_output_scatter(self, ax: Axes, data: MeasurementDataset):
        """
        绘制输出数据（点图/折线图）

        Args:
            ax: 绘图轴
            data: 输出数据集
        """
        # 转换为秒单位
        time_s = [p.timestamp_ms / 1000.0 for p in data.data_points]
        values = [p.value for p in data.data_points]

        # 根据配置选择绘图样式
        if self.config.output_style == 'line':
            # 仅折线
            ax.plot(time_s, values, color=self.config.output_color,
                    linewidth=1.0, alpha=0.8,
                    label=self.config.output_series_name, zorder=3)

        elif self.config.output_style == 'scatter':
            # 仅散点
            ax.scatter(time_s, values, color=self.config.output_color,
                       s=self.config.output_marker_size, alpha=0.8,
                       label=self.config.output_series_name, zorder=3)

        else:  # 'both'
            # 先绘制折线
            ax.plot(time_s, values, color=self.config.output_color,
                    linewidth=1.0, alpha=0.5, zorder=3)
            # 再叠加散点
            ax.scatter(time_s, values, color=self.config.output_color,
                       s=self.config.output_marker_size, alpha=0.9,
                       label=self.config.output_series_name, zorder=4)

    def _setup_time_axis(self, ax: Axes, input_data: MeasurementDataset,
                         output_data: MeasurementDataset):
        """
        配置时间轴

        Args:
            ax: 绘图轴
            input_data: 输入数据集
            output_data: 输出数据集
        """

        # 计算时间范围（上限以输入末尾为准，保证“截止时间=输入最后时间”）
        input_times_ms = [p.timestamp_ms for p in input_data.data_points]

        if self.config.time_max is None:
            max_time_s = math.ceil(max(input_times_ms) / 1000.0)
        else:
            max_time_s = self.config.time_max

        min_time_s = self.config.time_min

        # 设置时间范围
        ax.set_xlim(min_time_s, max_time_s)

        # 配置刻度
        # 主刻度：1秒（如果范围太大则调整）
        time_span = max_time_s - min_time_s
        if time_span <= 20:
            major_interval = 1.0
        elif time_span <= 60:
            major_interval = 2.0
        else:
            major_interval = 5.0

        ax.xaxis.set_major_locator(MultipleLocator(major_interval))

        # 次刻度：0.1秒（确保100ms可分辨）
        ax.xaxis.set_minor_locator(MultipleLocator(0.1))

        # 刻度标签格式
        ax.tick_params(axis='x', which='major', labelsize=10)
        ax.tick_params(axis='x', which='minor', labelsize=0)  # 隐藏次刻度标签

    def _setup_value_axis(self, ax: Axes, input_data: MeasurementDataset,
                          output_data: MeasurementDataset):
        """
        配置数值轴（通用版本）

        Args:
            ax: 绘图轴
            input_data: 输入数据集
            output_data: 输出数据集
        """
        # 收集所有测量值
        all_values = ([p.value for p in input_data.data_points] +
                      [p.value for p in output_data.data_points])

        # 计算绘图用的值范围（不在配置对象上反写，避免"黏住"）
        if self.config.data_min is None or self.config.data_max is None:
            value_min_data = min(all_values)
            value_max_data = max(all_values)
            value_span = value_max_data - value_min_data

            margin = max(value_span * 0.02, 0.01)  # 至少0.01的边距

            value_min_plot = math.floor((value_min_data - margin) * 100) / 100.0
            value_max_plot = math.ceil((value_max_data + margin) * 100) / 100.0
        else:
            value_min_plot = self.config.data_min
            value_max_plot = self.config.data_max

        # 设置值范围
        ax.set_ylim(value_min_plot, value_max_plot)

        # 配置刻度间隔（根据范围自适应）
        value_span = max(value_max_plot - value_min_plot, 1e-6)
        # 目标刻度数量（含首尾），避免标签过于密集
        target_ticks = 6
        raw_interval = value_span / target_ticks

        exp = math.floor(math.log10(raw_interval))
        base = raw_interval / (10 ** exp)
        for candidate in [1, 2, 2.5, 5, 10]:
            if base <= candidate:
                nice_base = candidate
                break
        else:
            nice_base = 10

        major_interval = nice_base * (10 ** exp)

        ax.yaxis.set_major_locator(MultipleLocator(major_interval))

        # 格式化y轴标签（使用配置的格式字符串）
        value_format = self.config.value_format
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x:{value_format}}'
        ))

        ax.tick_params(axis='y', which='major', labelsize=10)

    def _enable_interactive_cursor(self):
        """启用鼠标交互"""

        def on_mouse_move(event):
            """鼠标移动事件回调"""
            if event.inaxes != self.ax:
                # 鼠标不在绘图区域，隐藏注释
                if self.cursor_annotation is not None:
                    self.cursor_annotation.set_visible(False)
                    self.fig.canvas.draw_idle()
                return

            x_mouse = event.xdata  # 秒
            y_mouse = event.ydata  # 测量值

            # 查找输入数据最近值（阶梯图）
            input_value = self._find_step_value(self.input_data, x_mouse)

            # 查找输出数据最近点
            output_point = self._find_nearest_point(self.output_data, x_mouse, y_mouse)

            # 获取格式字符串和单位
            value_format = self.config.value_format
            data_unit = self.input_data.data_unit or ""
            unit_str = f" {data_unit}" if data_unit else ""

            # 构建注释文本
            text = f"Time: {x_mouse:.3f}s\n"
            if input_value is not None:
                text += f"{self.config.input_series_name}: {input_value:{value_format}}{unit_str}\n"
            if output_point is not None:
                text += f"{self.config.output_series_name}: {output_point.value:{value_format}}{unit_str}"

            # 更新或创建注释框
            if self.cursor_annotation is None:
                self.cursor_annotation = self.ax.annotate(
                    text,
                    xy=(x_mouse, y_mouse),
                    xytext=(15, 15),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow',
                              alpha=0.8, edgecolor='black'),
                    fontsize=9,
                    ha='left'
                )
            else:
                self.cursor_annotation.set_text(text)
                self.cursor_annotation.xy = (x_mouse, y_mouse)
                self.cursor_annotation.set_visible(True)

            self.fig.canvas.draw_idle()

        # 连接鼠标移动事件
        self.fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)

    def _find_step_value(self, data: MeasurementDataset, x_mouse: float) -> Optional[float]:
        """
        在阶梯数据中查找x_mouse所在区间的测量值

        Args:
            data: 数据集
            x_mouse: 鼠标x坐标（秒）

        Returns:
            该区间的测量值，若超出范围则返回None
        """
        if not data.data_points:
            return None

        # 转换时间戳为秒
        for i in range(len(data.data_points) - 1):
            t1 = data.data_points[i].timestamp_ms / 1000.0
            t2 = data.data_points[i + 1].timestamp_ms / 1000.0
            if t1 <= x_mouse < t2:
                return data.data_points[i].value

        # 如果在最后一段
        last_time = data.data_points[-1].timestamp_ms / 1000.0
        if x_mouse >= last_time:
            return data.data_points[-1].value

        # 如果在第一个点之前
        first_time = data.data_points[0].timestamp_ms / 1000.0
        if x_mouse < first_time:
            return None

        return None

    def _find_nearest_point(
        self,
        data: MeasurementDataset,
        x_mouse: float,
        y_mouse: float
    ) -> Optional[MeasurementDataPoint]:
        """
        查找输出数据的最近点

        Args:
            data: 数据集
            x_mouse: 鼠标x坐标（秒）
            y_mouse: 鼠标y坐标（测量值）

        Returns:
            最近的数据点，若距离太远则返回None
        """
        if not data.data_points:
            return None

        # 归一化系数（使x和y距离可比）
        y_limits = self.ax.get_ylim()
        value_span = y_limits[1] - y_limits[0]
        time_span = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]

        if value_span == 0:
            y_scale = 1.0
        else:
            y_scale = time_span / value_span

        # 查找最近点
        min_dist = float('inf')
        nearest_point = None

        for point in data.data_points:
            x_data = point.timestamp_ms / 1000.0
            y_data = point.value

            # 计算归一化距离
            dx = x_data - x_mouse
            dy = (y_data - y_mouse) * y_scale
            dist = math.sqrt(dx**2 + dy**2)

            if dist < min_dist:
                min_dist = dist
                nearest_point = point

        # 距离阈值（0.5秒）
        if min_dist < 0.5:
            return nearest_point
        else:
            return None

    def save(self, output_path: str, dpi: int = None):
        """
        保存图表为文件

        Args:
            output_path: 输出文件路径
            dpi: 分辨率（None则使用配置值）
        """
        if self.fig is None:
            raise RuntimeError("请先调用plot()方法生成图表")

        dpi = dpi or self.config.dpi
        self.fig.savefig(output_path, dpi=dpi, bbox_inches='tight')

    def show(self):
        """显示交互式图表"""
        if self.fig is None:
            raise RuntimeError("请先调用plot()方法生成图表")

        plt.show()


# 测试代码
if __name__ == '__main__':
    import os
    from measure_data_parser import InputDataParser, OutputDataParser
    from measure_data_alignment import DataAlignment

    print("=" * 60)
    print("测试绘图功能")
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

        # 对齐数据
        print("\n2. 对齐数据...")
        aligner = DataAlignment(change_threshold=0.002, threshold_unit="Hz")
        aligned_input, aligned_output, report = aligner.align_datasets(
            input_data, output_data, enable_align=True
        )
        print(f"   {report.message}")

        # 创建绘图配置
        print("\n3. 创建绘图配置...")
        config = PlotConfig(
            figsize=(14, 6),
            data_min=None,  # 自动计算
            data_max=None,
            output_style='both',
            enable_cursor=True,
            dpi=300,
            output_filename='test_freq_comparison.png'
        )

        # 绘图
        print("\n4. 绘制图表...")
        plotter = DataPlotter(config)
        fig, ax = plotter.plot(aligned_input, aligned_output, report)

        # 保存
        print("\n5. 保存图表...")
        plotter.save(config.output_filename)
        print(f"   图表已保存: {config.output_filename}")

        # 显示
        print("\n6. 显示交互式图表...")
        print("   提示: 移动鼠标查看数据点，关闭窗口继续...")
        plotter.show()
