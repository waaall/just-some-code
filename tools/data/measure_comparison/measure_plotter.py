#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测量数据对比绘图工具 - 主程序（通用）

功能：
1. 加载配置文件（支持向后兼容）
2. 协调各模块工作流（解析、对齐、绘图）
3. 提供命令行接口
4. 日志输出
5. 支持任意单位的测量数据（频率/电流/电压等）
"""

import json
import os
import argparse
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from measure_data_parser import DataFormatParser, MeasurementDataset
from measure_data_alignment import DataAlignment, AlignmentReport
from measure_plotter_core import DataPlotter, PlotConfig


@dataclass
class AppConfig:
    """
    应用配置（支持向后兼容）

    路径解析规则：
    - 配置文件中的相对路径：相对于配置文件所在目录（config_dir）
    - 命令行指定的相对路径：相对于当前工作目录（Path.cwd()）
    - 绝对路径：按原样使用
    """
    # 文件路径（可被命令行覆盖）
    input_csv_path: str = ""
    output_csv_path: str = ""
    # 配置文件所在目录（用于解析配置文件中的相对路径）
    config_dir: Path = field(default_factory=lambda: Path.cwd())

    # 数据配置（新增）
    data_config: dict = field(default_factory=lambda: {
        'data_label': 'Frequency',
        'data_unit': 'Hz',
        'value_format': '.3f',
        'input_column': {'name': None, 'index': 3, 'scale_factor': 1.0},
        'output_column': {'name': None, 'index': 1, 'scale_factor': 1.0}
    })

    # 对齐配置（新增）
    alignment_config: dict = field(default_factory=lambda: {
        'change_threshold': 0.002,
        'threshold_unit': 'Hz',
        'manual_time_offset_ms': None  # 手动指定时间偏移量(ms)，None表示使用自动检测
    })
    enable_alignment: bool = True

    # 绘图参数
    plot_config: PlotConfig = field(default_factory=PlotConfig)

    # 输出
    save_static: bool = True
    show_interactive: bool = True
    aligned_output_csv_path: str = "out_aligned.csv"

    @classmethod
    def from_json(cls, json_path: str) -> "AppConfig":
        """
        从JSON文件加载配置（支持向后兼容）

        Args:
            json_path: JSON配置文件路径

        Returns:
            AppConfig对象
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 向后兼容：检测旧配置格式
        if 'data_config' not in data:
            # 自动迁移为频率模式
            data_config = {
                'data_label': 'Frequency',
                'data_unit': 'Hz',
                'value_format': '.3f',
                'input_column': {'name': None, 'index': 3, 'scale_factor': 1.0},
                'output_column': {'name': None, 'index': 1, 'scale_factor': 1.0}
            }
            print("⚠ 检测到旧配置格式，自动使用频率默认值")
        else:
            data_config = data['data_config']

        # 对齐配置
        alignment_config = data.get('alignment_config', {
            'change_threshold': 0.002,
            'threshold_unit': data_config.get('data_unit', 'Hz'),
            'manual_time_offset_ms': None
        })

        # 解析绘图配置
        plot_config_data = data.get('plot_config', {})
        plot_config = PlotConfig(
            # 新增模板字段
            title_template=plot_config_data.get('title_template', '{data_label} Compare (Input vs Output)'),
            input_series_name=plot_config_data.get('input_series_name', 'Input (Source)'),
            output_series_name=plot_config_data.get('output_series_name', 'Output (Measured)'),
            y_axis_label=plot_config_data.get('y_axis_label', '{data_label} ({data_unit})'),
            x_axis_label=plot_config_data.get('x_axis_label', 'Time (s)'),
            output_filename_template=plot_config_data.get('output_filename_template', '{data_label}_comp_result.png'),
            value_format=plot_config_data.get('value_format', data_config.get('value_format', '.3f')),

            # 原有字段
            figsize=tuple(plot_config_data.get('figsize', [14, 6])),
            data_min=plot_config_data.get('data_min'),
            data_max=plot_config_data.get('data_max'),
            time_min=plot_config_data.get('time_min', 0.0),
            time_max=plot_config_data.get('time_max'),
            output_style=plot_config_data.get('output_style', 'both'),
            input_color=plot_config_data.get('input_color', '#1f77b4'),
            output_color=plot_config_data.get('output_color', '#ff7f0e'),
            output_marker_size=plot_config_data.get('output_marker_size', 10.0),
            enable_cursor=plot_config_data.get('enable_cursor', True),
            dpi=plot_config_data.get('dpi', 300),
            output_filename=plot_config_data.get('output_filename',
                                                 'freq_comparison_result.png')
        )

        # 创建配置对象
        config = cls(
            input_csv_path=data.get('input_csv_path', ''),
            output_csv_path=data.get('output_csv_path', ''),
            data_config=data_config,
            alignment_config=alignment_config,
            enable_alignment=data.get('enable_alignment', True),
            plot_config=plot_config,
            save_static=data.get('save_static', True),
            show_interactive=data.get('show_interactive', True),
            aligned_output_csv_path=data.get('aligned_output_csv_path', ''),
            config_dir=Path(json_path).resolve().parent
        )

        return config

    def to_json(self, json_path: str):
        """
        保存配置到JSON文件

        Args:
            json_path: JSON配置文件路径
        """
        # 转换为字典
        data = {
            'input_csv_path': self.input_csv_path,
            'output_csv_path': self.output_csv_path,
            'data_config': self.data_config,
            'alignment_config': self.alignment_config,
            'enable_alignment': self.enable_alignment,
            'plot_config': {
                'title_template': self.plot_config.title_template,
                'input_series_name': self.plot_config.input_series_name,
                'output_series_name': self.plot_config.output_series_name,
                'y_axis_label': self.plot_config.y_axis_label,
                'x_axis_label': self.plot_config.x_axis_label,
                'output_filename_template': self.plot_config.output_filename_template,
                'value_format': self.plot_config.value_format,
                'figsize': list(self.plot_config.figsize),
                'data_min': self.plot_config.data_min,
                'data_max': self.plot_config.data_max,
                'time_min': self.plot_config.time_min,
                'time_max': self.plot_config.time_max,
                'output_style': self.plot_config.output_style,
                'input_color': self.plot_config.input_color,
                'output_color': self.plot_config.output_color,
                'output_marker_size': self.plot_config.output_marker_size,
                'enable_cursor': self.plot_config.enable_cursor,
                'dpi': self.plot_config.dpi,
                'output_filename': self.plot_config.output_filename
            },
            'save_static': self.save_static,
            'show_interactive': self.show_interactive,
            'aligned_output_csv_path': self.aligned_output_csv_path
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class DataPlotterApp:
    """测量数据绘图应用主类（通用）"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化应用

        Args:
            config_path: 配置文件路径
        """
        # 基准目录：脚本所在目录
        script_dir = Path(__file__).resolve().parent
        default_config_path = script_dir / "measure_compare_plot.json"

        # 解析配置文件路径（CLI传入或默认）
        config_path = Path(config_path).expanduser() if config_path else default_config_path
        config_path = config_path.resolve()

        # 加载配置
        if config_path.exists():
            self.config = AppConfig.from_json(str(config_path))
            print(f"已加载配置文件: {config_path}")
            self.config_dir = config_path.parent
        else:
            # 使用默认配置
            self.config = AppConfig(config_dir=default_config_path.parent)
            self.config_dir = default_config_path.parent
            print(f"配置文件不存在，使用默认配置: {default_config_path}")

    def run(self, input_csv: Optional[str] = None,
            output_csv: Optional[str] = None,
            aligned_output_csv: Optional[str] = None,
            **kwargs):
        """
        主流程

        Args:
            input_csv: 输入CSV路径（覆盖配置文件）
            output_csv: 输出CSV路径（覆盖配置文件）
            **kwargs: 其他参数（data_min, data_max, etc.）
        """
        print("\n" + "=" * 60)
        print("频率对比绘图工具")
        print("=" * 60)

        # 1. 确定文件路径（命令行优先；相对路径基于对应来源）
        input_path_raw = input_csv if input_csv is not None else self.config.input_csv_path
        output_path_raw = output_csv if output_csv is not None else self.config.output_csv_path
        aligned_output_raw = (aligned_output_csv if aligned_output_csv is not None
                              else self.config.aligned_output_csv_path)

        input_path = self._resolve_data_path(input_path_raw, from_cli=input_csv is not None)
        output_path = self._resolve_data_path(output_path_raw, from_cli=output_csv is not None)
        aligned_from_cli = aligned_output_csv is not None

        if not input_path or not output_path:
            raise ValueError("请指定输入和输出CSV文件路径")

        # 检查文件是否存在
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"输出文件不存在: {output_path}")

        # 2. 解析数据（使用data_config配置）
        print("\n[步骤1] 解析数据")
        data_cfg = self.config.data_config

        print(f"  输入文件: {input_path}")
        input_data = DataFormatParser.parse_csv(
            input_path,
            value_column_name=data_cfg['input_column'].get('name'),
            value_column_index=data_cfg['input_column'].get('index', 3),
            value_scale_factor=data_cfg['input_column'].get('scale_factor', 1.0),
            data_label=data_cfg.get('data_label', ''),
            data_unit=data_cfg.get('data_unit', ''),
            data_type='input'
        )
        print(f"    - 数据点数: {len(input_data.data_points)}")
        print(f"    - 起始时间: {input_data.start_time_abs}")

        print(f"  输出文件: {output_path}")
        output_data = DataFormatParser.parse_csv(
            output_path,
            value_column_name=data_cfg['output_column'].get('name'),
            value_column_index=data_cfg['output_column'].get('index', 1),
            value_scale_factor=data_cfg['output_column'].get('scale_factor', 1.0),
            data_label=data_cfg.get('data_label', ''),
            data_unit=data_cfg.get('data_unit', ''),
            data_type='output'
        )
        print(f"    - 数据点数: {len(output_data.data_points)}")
        print(f"    - 起始时间: {output_data.start_time_abs}")

        # 3. 时间对齐（使用alignment_config配置）
        print("\n[步骤2] 时间对齐")
        if self.config.enable_alignment:
            align_cfg = self.config.alignment_config
            threshold = align_cfg.get('change_threshold', 0.002)
            threshold_unit = align_cfg.get('threshold_unit', 'Hz')
            manual_offset = align_cfg.get('manual_time_offset_ms')

            if manual_offset is not None:
                print(f"  使用手动时间偏移: {manual_offset}ms")
            else:
                print(f"  变化检测阈值: {threshold} {threshold_unit}")

            aligned_csv_path = None
            if aligned_output_raw:
                aligned_csv_path = self._resolve_data_path(
                    aligned_output_raw, from_cli=aligned_from_cli
                )

            aligner = DataAlignment(threshold, threshold_unit=threshold_unit)
            aligned_input, aligned_output, report = aligner.align_datasets(
                input_data, output_data, enable_align=True,
                manual_time_offset_ms=manual_offset,
                aligned_csv_path=aligned_csv_path
            )
            self._print_alignment_report(report)
        else:
            print("  对齐功能已禁用")
            aligned_input = input_data
            aligned_output = output_data
            report = AlignmentReport(
                input_change_index=None,
                output_change_index=None,
                input_change_time_ms=None,
                output_change_time_ms=None,
                time_offset_ms=0,
                aligned=False,
                message="对齐功能已禁用"
            )

        # 4. 应用命令行覆盖的参数
        plot_config = self.config.plot_config
        if 'data_min' in kwargs and kwargs['data_min'] is not None:
            plot_config.data_min = kwargs['data_min']
            print(f"\n[参数覆盖] data_min = {kwargs['data_min']} Hz")
        if 'data_max' in kwargs and kwargs['data_max'] is not None:
            plot_config.data_max = kwargs['data_max']
            print(f"[参数覆盖] data_max = {kwargs['data_max']} Hz")

        # 5. 绘图
        print("\n[步骤3] 生成对比图")
        plotter = DataPlotter(plot_config)
        fig, ax = plotter.plot(aligned_input, aligned_output, report)
        print("  图表生成完成")

        # 6. 打印数据摘要
        self._print_summary(aligned_input, aligned_output)

        # 7. 保存和显示
        print("\n[步骤4] 输出图表")
        if self.config.save_static:
            # 注意：配置文件中的相对路径基于配置文件所在目录，而非当前工作目录
            template_vars = {
                'data_label': (data_cfg.get('data_label') or aligned_input.data_label or "Data"),
                'data_unit': (data_cfg.get('data_unit') or aligned_input.data_unit or "").strip()
            }

            # 优先使用模板（除非用户显式提供非默认文件名）
            legacy_default = 'freq_comparison_result.png'
            output_override = plot_config.output_filename
            if output_override and output_override != legacy_default:
                output_file_raw = output_override
            elif plot_config.output_filename_template:
                output_file_raw = plot_config.output_filename_template
            else:
                output_file_raw = output_override or legacy_default

            try:
                output_file_formatted = output_file_raw.format(**template_vars)
            except (KeyError, ValueError):
                output_file_formatted = output_file_raw

            if not os.path.isabs(output_file_formatted):
                output_file_formatted = str(self.config_dir / output_file_formatted)

            plotter.save(output_file_formatted, dpi=plot_config.dpi)
            print(f"  静态图已保存: {output_file_formatted} (DPI: {plot_config.dpi})")

        if self.config.show_interactive:
            print("  交互式图表已准备就绪")
            print("  提示: 移动鼠标查看数据点，关闭窗口退出")
            plotter.show()
        else:
            print("  交互式显示已禁用")

        print("\n" + "=" * 60)
        print("处理完成！")
        print("=" * 60 + "\n")

    def _print_alignment_report(self, report: AlignmentReport):
        """
        打印对齐报告

        Args:
            report: 对齐报告对象
        """
        print(f"  状态: {report.message}")

        if report.aligned:
            print("  输入变化点:")
            if report.input_change_index is not None and report.input_change_time_ms is not None:
                print(f"    - 索引: {report.input_change_index}")
                print(f"    - 时间: {report.input_change_time_ms}ms "
                      f"({report.input_change_time_ms / 1000.0:.3f}s)")
            else:
                print("    - 未检测/手动指定")

            print("  输出变化点:")
            if report.output_change_index is not None and report.output_change_time_ms is not None:
                print(f"    - 索引: {report.output_change_index}")
                print(f"    - 原始时间: {report.output_change_time_ms}ms "
                      f"({report.output_change_time_ms / 1000.0:.3f}s)")
            else:
                print("    - 未检测/手动指定")

            print(f"  时间偏移: {report.time_offset_ms}ms "
                  f"({report.time_offset_ms / 1000.0:.3f}s)")

    def _print_summary(
        self,
        input_data: MeasurementDataset,
        output_data: MeasurementDataset
    ):
        """
        打印数据摘要

        Args:
            input_data: 输入数据集
            output_data: 输出数据集
        """
        # 输入数据统计
        input_values = [p.value for p in input_data.data_points]
        input_times = [p.timestamp_ms for p in input_data.data_points]

        # 输出数据统计
        output_values = [p.value for p in output_data.data_points]
        output_times = [p.timestamp_ms for p in output_data.data_points]

        # 获取数据单位
        data_unit = input_data.data_unit or ""
        unit_str = f" {data_unit}" if data_unit else ""

        print("\n[数据摘要]")
        print("  输入数据:")
        print(f"    - 值范围: {min(input_values):.3f} ~ {max(input_values):.3f}{unit_str}")
        print(f"    - 时间跨度: {min(input_times)/1000.0:.3f} ~ "
              f"{max(input_times)/1000.0:.3f}s")

        print("  输出数据:")
        print(f"    - 值范围: {min(output_values):.3f} ~ {max(output_values):.3f}{unit_str}")
        print(f"    - 时间跨度: {min(output_times)/1000.0:.3f} ~ "
              f"{max(output_times)/1000.0:.3f}s")

    def _resolve_data_path(self, path: str, from_cli: bool) -> str:
        """
        解析数据文件路径

        路径解析规则：
        - 命令行指定的相对路径：相对于当前工作目录（执行命令的目录）
        - 配置文件中的相对路径：相对于配置文件所在目录（代码所在目录）
        - 绝对路径：按原样使用

        Args:
            path: 原始路径字符串
            from_cli: 是否来自命令行（True=基于当前工作目录；False=基于配置文件所在目录）

        Returns:
            绝对路径字符串（可能为空字符串）
        """
        if not path:
            return ""

        base_dir = Path.cwd() if from_cli else self.config_dir
        p = Path(path)
        if not p.is_absolute():
            p = base_dir / p
        return str(p)


def main():
    """命令行入口"""
    script_dir = Path(__file__).resolve().parent
    default_config_path = script_dir / "measure_compare_plot.json"

    parser = argparse.ArgumentParser(
        description='频率对比绘图工具 - 绘制输入输出频率对比图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用配置文件
  python measure_plotter.py

  # 指定输入输出文件
  python measure_plotter.py -i input.csv -o output.csv

  # 自定义y轴范围
  python measure_plotter.py -i input.csv -o output.csv --ymin 49.8 --ymax 50.2

  # 禁用时间对齐
  python measure_plotter.py -i input.csv -o output.csv --no-align

  # 使用自定义配置文件
  python measure_plotter.py -c my_config.json -i input.csv -o output.csv
    """
    )

    parser.add_argument('-c', '--config', default=str(default_config_path),
                        help=f'配置文件路径（默认: {default_config_path}）')
    parser.add_argument('-i', '--input', help='输入CSV文件路径')
    parser.add_argument('-o', '--output', help='输出CSV文件路径')
    parser.add_argument('--ymin', type=float, help='频率轴最小值 (Hz)')
    parser.add_argument('--ymax', type=float, help='频率轴最大值 (Hz)')
    parser.add_argument('--no-align', action='store_true', help='禁用时间对齐')
    parser.add_argument('--threshold', type=float,
                        help='变化检测阈值（与阈值单位一致，覆盖配置文件）')
    parser.add_argument('--manual-offset', type=int,
                        help='手动指定时间偏移量(ms)，跳过自动检测（正值表示output相对input延迟）')
    parser.add_argument('--no-show', action='store_true',
                        help='禁用交互式显示（仅保存图片）')
    parser.add_argument('--aligned-output', help='输出对齐后CSV路径（保存对齐后的输入/输出数据）')

    args = parser.parse_args()

    try:
        # 创建应用
        app = DataPlotterApp(args.config)

        # 覆盖配置
        if args.no_align:
            app.config.enable_alignment = False
        if args.threshold is not None:
            app.config.alignment_config['change_threshold'] = args.threshold
        if args.manual_offset is not None:
            app.config.alignment_config['manual_time_offset_ms'] = args.manual_offset
        if args.no_show:
            app.config.show_interactive = False
        if args.aligned_output:
            app.config.aligned_output_csv_path = args.aligned_output

        # 运行
        app.run(
            input_csv=args.input,
            output_csv=args.output,
            aligned_output_csv=args.aligned_output,
            data_min=args.ymin,
            data_max=args.ymax
        )

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
