#!/usr/bin/env python3
"""
线性输入输出校准工具
用于自动生成校准系数（零点偏移 + 增益）

基本流程:
1. 从 JSON 读取通道配置(输入/输出量程、DAC 码值范围等)
2. 从 CSV 读取测试数据:
   - input_value + measured_output(可选 expected_output，默认按配置推导)
   - 或 code/raw_code + measured_output(可选 expected_output，直接使用码值)
3. 拟合“码值 → 实测输出”的线性模型:I_meas = a_m * code + b_m
4. 根据配置计算理论模型:I_exp = a_t * code + b_t
5. 解析求出线性变换 code_cal = α * code + β，并映射为 zero_offset / gain_10k
6. 输出校准系数、C 代码初始化、误差/线性度指标，并绘图保存

使用示例:
python calibration_tool.py \
  --config calibration_config.json \
  --data calibration_data.csv \
  --output calibration_result.png \
  --log calibration_result.log \
  --compare-coefs prev_calib.json \
  --comparison-csv comparison_output.csv

注意:
- 若测试数据csv文件中同时提供 `input_value` 与 `code/raw_code`
- 会优先使用code/码值列；`input_value` 仅作为参考。
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt
import numpy as np

from calibration_core import (
    CalibrationAnalyzer,
    CalibrationCoefficients,
    CalibrationConfig,
    CalibrationData,
    LinearCalibrator,
)


# ===================== 可视化与报告 =====================

class CalibrationVisualizer:
    """校准结果可视化与报告"""

    def __init__(self, data: CalibrationData, calibrator: LinearCalibrator) -> None:
        self.data = data
        self.calibrator = calibrator
        self.logger = logging.getLogger(__name__)

        # 尝试设置中文字体(不保证所有环境都有)
        plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

    def _axis_label(self) -> str:
        return "输入值" if self.data.data_mode == "input" else "码值"

    def _calibrate_outputs(
        self, coef: CalibrationCoefficients
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """返回输入、期望、实测与当前系数下的校准输出"""
        inputs, expected, measured = self.data.get_arrays()
        raw_codes = self.data.get_raw_codes()

        calibrated = []
        for raw_code in raw_codes:
            cal_code = self.calibrator.apply_calibration(int(round(raw_code)), coef)
            cal_out = self.calibrator._predict_output_from_code(cal_code)
            calibrated.append(cal_out)

        return inputs, expected, measured, np.array(calibrated, dtype=float)

    def _metrics_for_coef(self, coef: CalibrationCoefficients) -> dict:
        """计算指定校准系数下的误差与线性度指标"""
        inputs, expected, _, calibrated = self._calibrate_outputs(coef)
        analyzer = CalibrationAnalyzer()
        return {
            "avg_err": analyzer.calculate_avg_error(expected, calibrated),
            "max_err": analyzer.calculate_max_error(expected, calibrated),
            "linearity": analyzer.calculate_linearity(inputs, calibrated),
            "r2": analyzer.calculate_r_squared(inputs, calibrated),
        }

    def plot_calibration_curves(
        self,
        coef: CalibrationCoefficients,
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> None:
        """绘制校准前后曲线和误差对比"""

        inputs, expected, measured, calibrated = self._calibrate_outputs(coef)
        axis_label = self._axis_label()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 左图:曲线
        ax1.plot(inputs, expected, "k-o", label="理论曲线", linewidth=2)
        ax1.plot(inputs, measured, "r--s", label="实测曲线", linewidth=1.5)
        ax1.plot(inputs, calibrated, "g-.^", label="校准后曲线", linewidth=1.5)

        ax1.set_xlabel(axis_label, fontsize=12)
        ax1.set_ylabel("输出值", fontsize=12)
        ax1.set_title("校准曲线对比", fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)

        # 添加鼠标悬停显示功能
        annot = ax1.annotate("", xy=(0, 0), xytext=(20, 20),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="yellow", alpha=0.8),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def on_hover(event):
            """鼠标移动事件处理:显示理论曲线和校准后曲线的y值"""
            if event.inaxes == ax1:
                x = event.xdata
                if x is not None and len(inputs) > 1:
                    # 使用线性插值计算对应的y值
                    y_expected = np.interp(x, inputs, expected)
                    y_calibrated = np.interp(x, inputs, calibrated)

                    # 更新注释内容
                    text = f"{axis_label}: {x:.3f}\n理论: {y_expected:.3f}\n校准: {y_calibrated:.3f}"
                    annot.xy = (x, y_calibrated)
                    annot.set_text(text)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
            else:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

        # 连接鼠标移动事件
        fig.canvas.mpl_connect("motion_notify_event", on_hover)

        # 右图:误差柱状图
        err_before = measured - expected
        err_after = calibrated - expected
        x_pos = np.arange(len(inputs))
        width = 0.35

        ax2.bar(x_pos - width / 2, err_before, width, label="校准前误差")
        ax2.bar(x_pos + width / 2, err_after, width, label="校准后误差")

        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([f"{v:.3f}" for v in inputs], rotation=45, ha="right")
        ax2.set_xlabel("测试点", fontsize=12)
        ax2.set_ylabel("误差(同输出单位)", fontsize=12)
        ax2.set_title("校准前后误差对比", fontsize=14)
        ax2.grid(True, axis="y", alpha=0.3)
        ax2.axhline(0, color="k", linewidth=0.5)
        ax2.legend(fontsize=10)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            self.logger.info(f"图表已保存到: {save_path}")

        if show:
            plt.show()
        else:
            plt.close(fig)

    def print_analysis_report(self, coef: CalibrationCoefficients) -> None:
        """打印详细分析报告(使用 logger 输出)"""

        inputs, expected, measured, calibrated = self._calibrate_outputs(coef)

        analyzer = CalibrationAnalyzer()

        lin_before = analyzer.calculate_linearity(inputs, measured)
        lin_after = analyzer.calculate_linearity(inputs, calibrated)

        avg_err_before = analyzer.calculate_avg_error(expected, measured)
        max_err_before = analyzer.calculate_max_error(expected, measured)
        avg_err_after = analyzer.calculate_avg_error(expected, calibrated)
        max_err_after = analyzer.calculate_max_error(expected, calibrated)

        r2_before = analyzer.calculate_r_squared(inputs, measured)
        r2_after = analyzer.calculate_r_squared(inputs, calibrated)

        self.logger.info("\n" + "=" * 60)
        self.logger.info("校准分析报告")
        self.logger.info("=" * 60)

        self.logger.info(f"\n校准模式: 线性校准(zero + gain)")

        self.logger.info("\n建议 C 代码(示例变量名 calib):")
        self.logger.info(coef.to_c_code("calib"))

        self.logger.info("\n线性度指标(越小越好):")
        self.logger.info(f"  测量数据线性度:    {lin_before:.4f} %")
        self.logger.info(f"  校准后数据线性度:  {lin_after:.4f} %")

        self.logger.info("\n误差指标:")
        self.logger.info(f"  校准前平均误差: {avg_err_before:.4f}")
        self.logger.info(f"  校准前最大误差: {max_err_before:.4f}")
        self.logger.info(f"  校准后平均误差: {avg_err_after:.4f}")
        self.logger.info(f"  校准后最大误差: {max_err_after:.4f}")
        self.logger.info(f"  配置限定平均误差: {self.data.config.max_avg_error:.4f}")

        self.logger.info("\n拟合优度 R²(越接近 1 越好):")
        self.logger.info(f"  测量数据 R²:   {r2_before:.5f}")
        self.logger.info(f"  校准后数据 R²: {r2_after:.5f}")

        # 调用统一的详细数据对比函数
        self._print_detailed_comparison(None, coef)

    def print_coefficient_comparison(
        self,
        base_label: str,
        base_coef: CalibrationCoefficients,
        others: List[Tuple[str, CalibrationCoefficients]],
        save_csv: Optional[str] = None,
    ) -> None:
        """对比不同校准系数的参数与误差差异(使用 logger 输出)"""
        # 保存对比预测数据到 CSV (即使没有额外系数也可以保存)
        if save_csv:
            self._save_comparison_csv(save_csv, base_label, base_coef, others)

        # 如果没有额外系数，不打印对比表格
        if not others:
            return

        # 只为手动导入的配置打印详细数据对比
        for name, coef in others:
            self.logger.info(f"\n手动导入 {name} 校准系数:")
            self.logger.info(f"  zero_offset = {coef.zero_offset}")
            self.logger.info(f"  span_offset = {coef.span_offset}")
            self.logger.info(f"  gain_10k    = {coef.gain_10k}\n")
            self._print_detailed_comparison(name, coef)

        base_metrics = self._metrics_for_coef(base_coef)

        header = (
            f"{'Name':<12} {'zero':>8} {'span':>8} {'gain':>10} "
            f"{'avg_err':>12} {'max_err':>12} {'lin(%)':>10} {'R2':>9}"
        )
        self.logger.info("\n校准系数对比(基准: " + base_label + ")")
        self.logger.info(header)
        self.logger.info("-" * len(header))

        # 跟 header 长度一致
        def print_row(name: str, coef: CalibrationCoefficients, metrics: dict) -> None:
            self.logger.info(
                f"{name:<12} "
                f"{coef.zero_offset:8d} {coef.span_offset:8d} {coef.gain_10k:10d} "
                f"{metrics['avg_err']:12.4f} {metrics['max_err']:12.4f} "
                f"{metrics['linearity']:10.4f} {metrics['r2']:9.5f}"
            )

        print_row(base_label, base_coef, base_metrics)

        for name, coef in others:
            metrics = self._metrics_for_coef(coef)
            print_row(name, coef, metrics)
        self.logger.info("-" * len(header) + "\n")


    def _print_detailed_comparison(
        self, label: Optional[str], coef: CalibrationCoefficients
    ) -> None:
        """打印指定系数配置的详细数据对比:"""
        inputs, expected, measured, calibrated = self._calibrate_outputs(coef)

        # 根据label参数决定标题格式
        title = "\n详细数据对比:" if label is None else f"\n详细数据对比 - {label}:"
        self.logger.info(title)

        axis_label = "Input" if self.data.data_mode == "input" else "Code"
        header = f"{axis_label:>10} {'Expected':>10} {'Measured':>10} {'Calibrated':>12} {'Err_Before':>12} {'Err_After':>12}"
        self.logger.info(header)
        self.logger.info("-" * len(header))
        for i in range(len(inputs)):
            eb = measured[i] - expected[i]
            ea = calibrated[i] - expected[i]
            self.logger.info(
                f"{inputs[i]:10.3f} {expected[i]:10.3f} {measured[i]:10.3f} "
                f"{calibrated[i]:12.3f} {eb:12.4f} {ea:12.4f}"
            )
        self.logger.info("-" * len(header))

    def _infer_input_precision(self) -> float:
        """从测量数据中推断 input 的精度"""
        inputs, _, _ = self.data.get_arrays()
        if len(inputs) == 0:
            return 0.001  # 默认精度

        # 将 float 数组转换为字符串列表，复用 CalibrationData 的精度推断方法
        input_str_list = [f"{inp:.10f}".rstrip('0').rstrip('.') for inp in inputs]
        return CalibrationData._infer_measurement_resolution(input_str_list)

    def _save_comparison_csv(
        self,
        csv_path: str,
        base_label: str,
        base_coef: CalibrationCoefficients,
        others: List[Tuple[str, CalibrationCoefficients]],
    ) -> None:
        """保存对比预测数据到 CSV 文件(最多300行，按头中尾采样)"""
        import csv

        # 推断 input 的精度
        input_precision = self._infer_input_precision()

        # 生成完整的 input 序列
        cfg = self.data.config
        input_min = cfg.input_min
        input_max = cfg.input_max

        # 计算总行数
        total_rows = int((input_max - input_min) / input_precision) + 1

        # 生成采样点
        if total_rows <= 300:
            # 全部输出
            input_values = np.arange(input_min, input_max + input_precision/2, input_precision)
        else:
            # 头100 + 中100 + 尾100
            head = np.arange(input_min, input_min + 100 * input_precision, input_precision)
            mid_start = input_min + (input_max - input_min) / 2 - 50 * input_precision
            mid = np.arange(mid_start, mid_start + 100 * input_precision, input_precision)
            tail = np.arange(input_max - 99 * input_precision, input_max + input_precision/2, input_precision)
            input_values = np.concatenate([head, mid, tail])

        # 准备 CSV 数据
        rows = []
        for inp in input_values:
            row = {"Input": f"{inp:.3f}"}

            # 计算期望输出
            expected = self.data.expected_output_from_input(inp)
            row["Expected"] = f"{expected:.3f}"

            # 计算 base_coef 的输出
            raw_code = self.data.input_to_raw_code(inp)
            cal_code = self.calibrator.apply_calibration(raw_code, base_coef)
            cal_out = self.calibrator._predict_output_from_code(cal_code)
            row[base_label] = f"{cal_out:.3f}"

            # 计算其他系数的输出
            for name, coef in others:
                cal_code = self.calibrator.apply_calibration(raw_code, coef)
                cal_out = self.calibrator._predict_output_from_code(cal_code)
                row[name] = f"{cal_out:.3f}"

            rows.append(row)

        # 写入 CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["Input", "Expected", base_label] + [name for name, _ in others]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.logger.info(f"对比预测数据已保存到: {csv_path}")


# ===================== 命令行入口 =====================

def main() -> None:
    parser = argparse.ArgumentParser(description="线性输入输出校准工具")
    base = Path(__file__).resolve().parent

    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=base / "calibration_config.json",
        help="配置文件路径(默认: 同目录 calibration_config.json)",
    )
    parser.add_argument(
        "-d", "--data",
        type=Path,
        default=base / "calibration_data.csv",
        help="测量数据 CSV 路径(默认: 同目录 calibration_data.csv)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=base / "calibration_result.png",
        help="校准曲线图保存路径",
    )
    parser.add_argument(
        "-l", "--log",
        type=Path,
        default=base / "calibration_result.log",
        help="日志文件保存路径(默认: 同目录 calibration_result.log)",
    )
    parser.add_argument(
        "--compare-coefs",
        nargs="+",
        type=Path,
        help="额外校准系数 JSON 文件列表(字段 zero_offset/span_offset/gain_10k)，与本次计算结果对比",
    )
    parser.add_argument(
        "--comparison-csv",
        type=Path,
        help="保存系数对比预测数据的 CSV 文件路径(最多300行，按头中尾采样)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="仅保存图像，不弹出窗口(适合无头环境)",
    )

    args = parser.parse_args()

    # 配置 logging:同时输出到终端和文件
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建格式器
    formatter = logging.Formatter('%(message)s')

    # 终端 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler
    file_handler = logging.FileHandler(args.log, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"日志将保存到: {args.log}")

    # 若配置不存在，自动创建一份默认配置(使用正确的 code_min / code_max)
    if not args.config.exists():
        default_cfg = CalibrationConfig(
            input_min=49.8,
            input_max=50.2,
            output_min=4.0,
            output_max=20.0,
            code_min=0x147A,   # 5242，对应 4mA
            code_max=0x6665,   # 26213，对应 20mA
            max_avg_error=0.3,
            code_saturation_min=0,
            code_saturation_max=32767,
        )
        default_cfg.to_json(str(args.config))
        logger.info(f"已创建默认配置文件: {args.config}")

    config = CalibrationConfig.from_json(str(args.config))

    if not args.data.exists():
        raise FileNotFoundError(
            f"未找到测量数据文件: {args.data}\n"
            f"请提供包含列 input_value,measured_output(可选 expected_output)或 "
            f"code/raw_code,measured_output(可选 expected_output)的 CSV 文件。"
        )

    data = CalibrationData(config)
    data.load_from_csv(str(args.data))

    calibrator = LinearCalibrator(data)
    coef = calibrator.calculate_linear_calibration()
    extra_coefs: List[Tuple[str, CalibrationCoefficients]] = []
    if args.compare_coefs:
        for path in args.compare_coefs:
            if not path.exists():
                raise FileNotFoundError(f"未找到系数文件: {path}")
            loaded = CalibrationCoefficients.from_json(str(path))
            extra_coefs.append((path.stem, loaded))

    visualizer = CalibrationVisualizer(data, calibrator)
    visualizer.print_analysis_report(coef)

    # 准备对比预测 CSV 路径
    comparison_csv_path = str(args.comparison_csv) if args.comparison_csv else None
    visualizer.print_coefficient_comparison("auto", coef, extra_coefs, save_csv=comparison_csv_path)

    visualizer.plot_calibration_curves(
        coef,
        save_path=str(args.output),
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
