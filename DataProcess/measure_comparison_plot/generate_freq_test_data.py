#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成频率动态测试数据, 支持线性扫频、三角波、正弦波三种模式。
支持命令行配置和时间累计误差校准输出。

用法示例:

1. 线性扫频(默认模式):
  python generate_freq_test_data.py --start-freq 49.9 --end-freq 50.1 --freq-step 0.01 --interval-ms 200
  # 生成: test_49.9_50.1_200ms.csv

2. 三角波模式:
  python generate_freq_test_data.py --waveform-type triangle \
    --start-freq 49.9 --end-freq 50.1 \
    --waveform-period-s 5.0 --num-periods 2 --interval-ms 200
  # 生成: test_triangle_49.9_50.1_5s_2p_200ms.csv
  # 频率在5秒内从49.9Hz上升到50.1Hz, 再下降回49.9Hz, 重复2个周期

3. 正弦波模式:
  python generate_freq_test_data.py --waveform-type sine \
    --start-freq 49.9 --end-freq 50.1 \
    --waveform-period-s 10.0 --num-periods 1 --interval-ms 100
  # 生成: test_sine_49.9_50.1_10s_1p_100ms.csv
  # 频率以正弦波形式在49.9-50.1Hz之间变化, 从中间值(50.0Hz)开始向上

4. 生成校准文件(含时间累计误差):
  python generate_freq_test_data.py --waveform-type sine \
    --start-freq 49.9 --end-freq 50.1 \
    --waveform-period-s 5.0 --num-periods 1 \
    --interval-ms 200 --cal-error-ms 4.5
  # 同时生成主文件和校准文件(每步累计4.5ms误差)

参数说明:
  --waveform-type       波形类型: linear(默认)/triangle/sine
  --start-freq          起始频率/最小频率 (Hz), 默认49.9
  --end-freq            结束频率/最大频率 (Hz), 默认50.1
  --interval-ms         时间间隔 (ms), 默认200

  线性模式专用:
    --freq-step         频率步进 (Hz), 默认0.004

  波形模式专用:
    --waveform-period-s 波形周期 (秒), 必需
    --num-periods       生成周期数, 默认1.0(可以是小数, 如1.5表示1个半周期)

  校准输出:
    --generate-cal      生成校准文件
    --cal-error-ms      每步累计误差 (ms), 默认4.0; 指定此参数自动开启校准输出
"""

import argparse
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class SweepConfig:
    output: Optional[Path]
    interval_ms: float
    freq_step: float
    start_freq: float
    end_freq: float
    start_datetime: datetime
    generate_cal: bool
    cal_error_ms: float
    # 新增：波形类型相关字段
    waveform_type: str = "linear"  # "linear"/"triangle"/"sine"
    waveform_period_s: Optional[float] = None  # 波形周期(秒)
    num_periods: float = 1.0  # 生成周期数


class FrequencyTestDataGenerator:
    def __init__(self, config: SweepConfig) -> None:
        self.config = config
        self._ensure_output_name()
        self._validate_config()

    def generate(self) -> None:
        """生成测试数据文件"""
        self._write_csv(self.config.output, self.config.interval_ms)

        cal_path = None
        if self.config.generate_cal:
            cal_path = default_cal_path(self.config.output)
            cal_interval_ms = self.config.interval_ms + self.config.cal_error_ms
            self._write_csv(cal_path, cal_interval_ms)

        total_time_ms = (self._num_points() - 1) * self.config.interval_ms
        total_time_s = total_time_ms / 1000.0

        print(f"已生成: {self.config.output}")
        if cal_path:
            print(f"已生成校准文件: {cal_path} (每步误差 {self.config.cal_error_ms}ms)")
        print(f"  波形类型: {self.config.waveform_type}")
        print(f"  数据点数: {self._num_points()}")
        print(f"  时间间隔: {self.config.interval_ms}ms")
        print(f"  频率范围: {self.config.start_freq:.3f} - {self.config.end_freq:.3f} Hz")

        if self.config.waveform_type == "linear":
            print(f"  频率步进: {self.config.freq_step} Hz")
        else:
            print(f"  波形周期: {self.config.waveform_period_s}s")
            print(f"  周期数量: {self.config.num_periods}")
            actual_periods = total_time_s / self.config.waveform_period_s
            print(f"  实际周期: {actual_periods:.2f} (含首尾点)")

        print(f"  总时长: {total_time_s:.1f}秒 ({total_time_ms}ms)")

    def _write_csv(self, path: Path, step_ms: float) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            for row in self._iter_rows(step_ms):
                file.write(row)

    def _iter_rows(self, step_ms: float) -> Iterable[str]:
        """生成每行CSV数据"""
        for index in range(self._num_points()):
            # 计算时间戳
            elapsed_ms = int(round(step_ms * index))
            current_time = self.config.start_datetime + timedelta(milliseconds=elapsed_ms)

            # 根据波形类型计算频率
            current_freq = self._calculate_frequency(index, step_ms)

            # 格式化输出
            date_str = f"{current_time.year}-{current_time.month}-{current_time.day}"
            time_str = current_time.strftime("%H:%M:%S")
            ms_str = f"{current_time.microsecond // 1000:03d}"
            freq_str = f"{current_freq:.3f}"
            yield f"{date_str},{time_str},{ms_str},{freq_str}\n"

    def _num_points(self) -> int:
        """计算总数据点数"""
        if self.config.waveform_type == "linear":
            # 线性模式：基于频率步进计算
            return int((self.config.end_freq - self.config.start_freq) / self.config.freq_step) + 1
        else:
            # 三角波/正弦波模式：基于时间周期计算
            if self.config.waveform_period_s is None:
                raise ValueError(f"{self.config.waveform_type} 模式需要指定 --waveform-period-s")

            # 总时长 = 单个周期时长 * 周期数
            total_duration_ms = self.config.waveform_period_s * 1000 * self.config.num_periods

            # 数据点数 = 总时长 / 时间间隔 + 1(包含起点)
            return int(total_duration_ms / self.config.interval_ms) + 1

    def _calculate_frequency(self, index: int, step_ms: float) -> float:
        """根据波形类型计算当前频率"""
        if self.config.waveform_type == "linear":
            # 线性扫频(现有逻辑)
            return self.config.start_freq + index * self.config.freq_step

        elif self.config.waveform_type == "triangle":
            # 三角波
            return self._triangle_wave_freq(index, step_ms)

        elif self.config.waveform_type == "sine":
            # 正弦波
            return self._sine_wave_freq(index, step_ms)

        else:
            raise ValueError(f"不支持的波形类型: {self.config.waveform_type}")

    def _triangle_wave_freq(self, index: int, step_ms: float) -> float:
        """计算三角波频率"""
        # 当前时间点 (毫秒)
        t_ms = index * step_ms
        # 周期时长 (毫秒)
        T_ms = self.config.waveform_period_s * 1000

        # 计算周期内相位 (0 到 1)
        phase = (t_ms % T_ms) / T_ms

        f_min = self.config.start_freq
        f_max = self.config.end_freq
        f_range = f_max - f_min

        if phase < 0.5:
            # 上升段: 0 → 0.5 映射到 f_min → f_max
            freq = f_min + 2 * f_range * phase
        else:
            # 下降段: 0.5 → 1.0 映射到 f_max → f_min
            freq = f_max - 2 * f_range * (phase - 0.5)

        return freq

    def _sine_wave_freq(self, index: int, step_ms: float) -> float:
        """计算正弦波频率"""
        # 当前时间点 (毫秒)
        t_ms = index * step_ms
        # 周期时长 (毫秒)
        T_ms = self.config.waveform_period_s * 1000

        # 计算周期内相位 (0 到 1)
        phase = (t_ms % T_ms) / T_ms

        f_min = self.config.start_freq
        f_max = self.config.end_freq
        f_center = (f_min + f_max) / 2
        amplitude = (f_max - f_min) / 2

        # 正弦波公式：从中间值开始向上
        freq = f_center + amplitude * math.sin(2 * math.pi * phase)

        return freq

    def _validate_config(self) -> None:
        """验证配置参数"""
        # 通用验证
        if self.config.interval_ms <= 0:
            raise ValueError("时间间隔必须大于0")
        if self.config.end_freq < self.config.start_freq:
            raise ValueError("结束频率必须大于或等于起始频率")

        # 模式特定验证
        if self.config.waveform_type == "linear":
            if self.config.freq_step <= 0:
                raise ValueError("频率步进必须大于0")
        else:  # triangle 或 sine
            if self.config.waveform_period_s is None:
                raise ValueError(f"{self.config.waveform_type} 模式需要指定 --waveform-period-s")
            if self.config.waveform_period_s <= 0:
                raise ValueError("波形周期必须大于0")
            if self.config.num_periods <= 0:
                raise ValueError("周期数必须大于0")

            # 警告：周期时间应该远大于采样间隔
            min_samples_per_period = 10  # 每个周期至少10个采样点
            period_ms = self.config.waveform_period_s * 1000
            if period_ms / self.config.interval_ms < min_samples_per_period:
                import warnings
                warnings.warn(
                    f"警告：每个周期采样点过少 "
                    f"({period_ms / self.config.interval_ms:.1f}点), "
                    f"建议至少{min_samples_per_period}点以上",
                    UserWarning
                )

    def _ensure_output_name(self) -> None:
        """自动生成输出文件名"""
        if self.config.output is None:
            if self.config.waveform_type == "linear":
                # 线性模式：使用现有命名
                self.config.output = Path(
                    default_output_name(
                        self.config.start_freq,
                        self.config.end_freq,
                        self.config.interval_ms,
                    )
                )
            else:
                # 波形模式：新命名规则
                self.config.output = Path(
                    waveform_output_name(
                        self.config.waveform_type,
                        self.config.start_freq,
                        self.config.end_freq,
                        self.config.waveform_period_s,
                        self.config.num_periods,
                        self.config.interval_ms,
                    )
                )


def parse_args() -> SweepConfig:
    parser = argparse.ArgumentParser(description="生成频率动态测试数据")
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件名, 默认根据参数自动生成 test_{start}_{end}_{interval}ms.csv",
    )
    parser.add_argument("--interval-ms", type=float, default=200.0, help="时间间隔 (ms)")
    parser.add_argument("--freq-step", type=float, default=0.004, help="频率步进 (Hz), 仅用于线性模式")
    parser.add_argument("--start-freq", type=float, default=49.9, help="起始频率/最小频率 (Hz)")
    parser.add_argument("--end-freq", type=float, default=50.1, help="结束频率/最大频率 (Hz)")

    # 新增：波形类型参数
    parser.add_argument(
        "--waveform-type",
        type=str,
        default="linear",
        choices=["linear", "triangle", "sine"],
        help="波形类型: linear(线性扫频), triangle(三角波), sine(正弦波)",
    )

    # 新增：波形周期参数
    parser.add_argument(
        "--waveform-period-s",
        type=float,
        default=None,
        help="波形周期 (秒), 用于 triangle 和 sine 模式, 例如 5.0 表示5秒完成一个周期",
    )

    # 新增：周期数参数
    parser.add_argument(
        "--num-periods",
        type=float,
        default=1.0,
        help="生成多少个完整波形周期, 可以是小数, 例如 2.5 表示2个半周期",
    )
    parser.add_argument(
        "--start-date",
        type=_parse_date,
        default=None,
        help="起始日期 (YYYY-MM-DD), 默认今天",
    )
    parser.add_argument(
        "--start-time",
        type=_parse_time,
        default=time(hour=10, minute=0, second=0),
        help="起始时间 (HH:MM:SS), 默认 10:00:00",
    )
    parser.add_argument(
        "--generate-cal",
        action="store_true",
        help="同时生成 {name}-cal.csv, 用于叠加每步时间误差",
    )
    parser.add_argument(
        "--cal-error-ms",
        type=float,
        default=None,
        help="每次频率修改的累计误差 (ms), 默认 4.0; 传入该参数将自动开启校准输出",
    )

    args = parser.parse_args()

    # 参数验证
    if args.waveform_type in ["triangle", "sine"]:
        if args.waveform_period_s is None:
            parser.error(f"--waveform-type={args.waveform_type} 需要指定 --waveform-period-s")
        if args.waveform_period_s <= 0:
            parser.error("--waveform-period-s 必须大于 0")
        if args.num_periods <= 0:
            parser.error("--num-periods 必须大于 0")

    start_dt = datetime.combine(args.start_date or date.today(), args.start_time)
    cal_error_ms = args.cal_error_ms if args.cal_error_ms is not None else 4.0
    generate_cal = args.generate_cal or args.cal_error_ms is not None
    output_path = Path(args.output) if args.output else None

    return SweepConfig(
        output=output_path,
        interval_ms=args.interval_ms,
        freq_step=args.freq_step,
        start_freq=args.start_freq,
        end_freq=args.end_freq,
        start_datetime=start_dt,
        generate_cal=bool(generate_cal),
        cal_error_ms=cal_error_ms,
        # 新增字段
        waveform_type=args.waveform_type,
        waveform_period_s=args.waveform_period_s,
        num_periods=args.num_periods,
    )


def default_cal_path(output: Path) -> Path:
    if output.suffix:
        return output.with_name(f"{output.stem}-cal{output.suffix}")
    return output.with_name(f"{output.name}-cal.csv")


def default_output_name(start_freq: float, end_freq: float, interval_ms: float) -> str:
    start_str = _format_number(start_freq)
    end_str = _format_number(end_freq)
    interval_str = _format_number(interval_ms)
    return f"test_{start_str}_{end_str}_{interval_str}ms.csv"


def waveform_output_name(
    waveform_type: str,
    freq_min: float,
    freq_max: float,
    period_s: float,
    num_periods: float,
    interval_ms: float,
) -> str:
    """生成波形模式的默认文件名

    示例：test_triangle_49.9_50.1_5s_2p_200ms.csv
          (三角波, 49.9-50.1Hz, 5秒周期, 2个周期, 200ms间隔)
    """
    min_str = _format_number(freq_min)
    max_str = _format_number(freq_max)
    period_str = _format_number(period_s)
    periods_str = _format_number(num_periods)
    interval_str = _format_number(interval_ms)

    return (
        f"test_{waveform_type}_{min_str}_{max_str}_"
        f"{period_str}s_{periods_str}p_{interval_str}ms.csv"
    )


def _format_number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期格式应为 YYYY-MM-DD") from exc


def _parse_time(value: str) -> time:
    if isinstance(value, time):
        return value
    try:
        hours, minutes, seconds = value.split(":")
        return time(hour=int(hours), minute=int(minutes), second=int(seconds))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("时间格式应为 HH:MM:SS") from exc


def main() -> None:
    config = parse_args()
    generator = FrequencyTestDataGenerator(config)
    generator.generate()


if __name__ == "__main__":
    main()
