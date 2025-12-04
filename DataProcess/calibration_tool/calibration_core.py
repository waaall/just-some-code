#!/usr/bin/env python3
"""
核心模块:数据结构与校准算法

包含:
- CalibrationConfig / CalibrationData / CalibrationCoefficients / MeasurementPoint
- 线性校准与两点校准(LinearCalibrator)
- 校准质量评估(CalibrationAnalyzer)
"""

import csv
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple

import numpy as np
from scipy.optimize import minimize


# ===================== 数据结构 =====================

@dataclass
class CalibrationCoefficients:
    """校准系数数据类(对应 C 侧 Calib_t)"""
    zero_offset: int = 0      # 零点偏移(码值)
    span_offset: int = 0      # 满量程偏移(码值)
    gain_10k: int = 10000     # 增益(万分比，10000 = 1.0 倍)

    def to_c_code(self, var_name: str = "calib") -> str:
        """生成 C 语言结构体初始化代码"""
        return f"""static const Calib_t {var_name} = {{
  .zero_offset = {self.zero_offset},
  .span_offset = {self.span_offset},
  .gain_10k = {self.gain_10k}
}};"""

    @classmethod
    def from_json(cls, json_path: str) -> "CalibrationCoefficients":
        """从 JSON 文件读取校准系数字段(zero_offset/span_offset/gain_10k)"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = {"zero_offset", "span_offset", "gain_10k"}
        missing = required - data.keys()
        if missing:
            raise KeyError(f"系数文件缺少字段: {', '.join(sorted(missing))}")
        return cls(
            zero_offset=int(data["zero_offset"]),
            span_offset=int(data["span_offset"]),
            gain_10k=int(data["gain_10k"]),
        )


@dataclass
class MeasurementPoint:
    """单个测量数据点"""
    input_value: float      # 输入值(如频率 Hz)
    expected_output: float  # 期望输出(如电流 mA，可由配置推导)
    measured_output: float  # 实际测量输出(如电流 mA)


@dataclass
class CalibrationConfig:
    """
    校准配置参数

    注意:
    - code_min / code_max 必须与 C 侧 ma_output.h 中的
      MA_OUT_DAC_4MA / MA_OUT_DAC_20MA 完全一致
    """
    input_min: float            # 输入最小值
    input_max: float            # 输入最大值
    output_min: float           # 输出最小值
    output_max: float           # 输出最大值
    code_min: int               # 最小码值(对应 output_min)
    code_max: int               # 最大码值(对应 output_max)
    max_avg_error: float        # 允许的最大平均绝对误差(单位同输出，如 mA)
    offset_limit: int = 2000    # 允许的偏移量范围(码值)
    gain_min: int = 5000        # 最小增益(0.5 倍)
    gain_max: int = 15000       # 最大增益(1.5 倍)

    @classmethod
    def from_json(cls, json_path: str) -> "CalibrationConfig":
        """从 JSON 文件加载配置"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_json(self, json_path: str) -> None:
        """保存配置到 JSON 文件"""
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)


class CalibrationData:
    """校准数据管理类"""

    def __init__(self, config: CalibrationConfig) -> None:
        self.config = config
        self.measurements: List[MeasurementPoint] = []

    def load_from_csv(self, csv_path: str) -> None:
        """
        从 CSV 文件加载测量数据

        CSV 支持两种格式:
        1) input_value, measured_output(按配置推导期望值)
        2) input_value, expected_output, measured_output(显式提供期望值)
        """
        self.measurements.clear()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV 文件缺少表头")

            field_set = set(reader.fieldnames)
            required = {"input_value", "measured_output"}
            missing = required - field_set
            if missing:
                raise ValueError(f"CSV 缺少必要列: {', '.join(sorted(missing))}")

            has_expected = "expected_output" in field_set

            for row in reader:
                input_value = float(row["input_value"])
                measured_output = float(row["measured_output"])

                exp_raw = row.get("expected_output") if has_expected else None
                if exp_raw is not None and str(exp_raw).strip() != "":
                    expected_output = float(exp_raw)
                else:
                    expected_output = self.expected_output_from_input(input_value)

                self.measurements.append(
                    MeasurementPoint(
                        input_value=input_value,
                        expected_output=expected_output,
                        measured_output=measured_output,
                    )
                )

    def get_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """返回 numpy 数组格式的数据 (inputs, expected, measured)"""
        inputs = np.array([m.input_value for m in self.measurements], dtype=float)
        expected = np.array([m.expected_output for m in self.measurements], dtype=float)
        measured = np.array([m.measured_output for m in self.measurements], dtype=float)
        return inputs, expected, measured

    def input_to_raw_code(self, input_value: float) -> int:
        """输入值映射到理论 DAC 码值(线性插值 + 饱和)"""
        cfg = self.config
        if input_value <= cfg.input_min:
            return cfg.code_min
        if input_value >= cfg.input_max:
            return cfg.code_max

        progress = (input_value - cfg.input_min) / (cfg.input_max - cfg.input_min)
        raw = cfg.code_min + progress * (cfg.code_max - cfg.code_min)
        return int(round(raw))

    def get_raw_codes(self) -> np.ndarray:
        """将所有输入值映射为对应的理论原始码值数组"""
        inputs, _, _ = self.get_arrays()
        return np.array([self.input_to_raw_code(v) for v in inputs], dtype=float)

    def fit_code_to_measured_model(self) -> Tuple[float, float]:
        """
        拟合“码值 -> 实测输出”的线性模型:

            I_meas(code) ≈ a_m * code + b_m
        """
        codes = self.get_raw_codes()
        _, _, measured = self.get_arrays()

        if len(codes) < 2 or np.allclose(codes, codes[0]):
            # 极端情况下回退到理论斜率
            span_y = self.config.output_max - self.config.output_min
            span_code = self.config.code_max - self.config.code_min
            a = span_y / span_code
            b = self.config.output_min - a * self.config.code_min
            return a, b

        a, b = np.polyfit(codes, measured, 1)
        return float(a), float(b)

    def code_to_output_theoretical(self, code: float) -> float:
        """理论上 code -> 输出值 的线性关系(仅由配置决定)"""
        cfg = self.config
        if code <= cfg.code_min:
            return cfg.output_min
        if code >= cfg.code_max:
            return cfg.output_max
        progress = (code - cfg.code_min) / (cfg.code_max - cfg.code_min)
        return cfg.output_min + progress * (cfg.output_max - cfg.output_min)

    def expected_output_from_input(self, input_value: float) -> float:
        """根据配置推导给定输入值对应的理论期望输出"""
        raw_code = self.input_to_raw_code(input_value)
        return self.code_to_output_theoretical(raw_code)


# ===================== 校准核心算法 =====================

class LinearCalibrator:
    """线性校准器"""

    def __init__(self, data: CalibrationData) -> None:
        self.data = data
        self.config = data.config
        # 拟合得到 I_meas(code) = a_m * code + b_m
        self._code_to_measured = data.fit_code_to_measured_model()

    # ---- MCU 侧应保持一致的校准公式 ----
    def apply_calibration(self, raw_code: int, coef: CalibrationCoefficients) -> int:
        """
        应用校准系数，模拟 MCU 侧的线性校准算法。

        建议 C 侧实现完全一致的函数，例如:

            static int ma_out_apply_calibration(int code, const Calib_t *c)
            {
                long tmp = (long)(code + c->span_offset) * c->gain_10k + 5000;
                tmp /= 10000;
                tmp += c->zero_offset;
                if (tmp < 0) tmp = 0;
                if (tmp > 32767) tmp = 32767;
                return (int)tmp;
            }

        这里 Python 侧以相同公式进行模拟。
        """
        if raw_code <= 0:
            return 0

        zero = int(coef.zero_offset)
        span = int(coef.span_offset)
        gain = int(coef.gain_10k)

        tmp = (int(raw_code) + span) * gain + 5000  # 四舍五入
        tmp //= 10000
        tmp += zero

        if tmp < 0:
            tmp = 0
        max_code = max(self.config.code_min, self.config.code_max, 32767)
        if tmp > max_code:
            tmp = max_code

        return int(tmp)

    def _predict_output_from_code(self, code: int) -> float:
        """使用实测拟合模型预测给定码值的输出"""
        a_m, b_m = self._code_to_measured
        y = a_m * code + b_m
        # 裁剪到量程内
        y = float(np.clip(y, self.config.output_min, self.config.output_max))
        return y

    def calculate_linear_calibration(self) -> CalibrationCoefficients:
        """
        计算线性校准系数(只调整 zero_offset 和 gain_10k)

        思路:
        - 实测模型:I_meas = a_m * code + b_m
        - 理论模型:I_exp  = a_t * code + b_t
        - 希望存在线性变换 code_cal = α * code + β，使得

              I_meas(code_cal) = I_exp(code)  对任意 code 成立

          即:

              a_m*(α*code + β) + b_m = a_t*code + b_t

          对比系数得到解析解:

              α = a_t / a_m
              β = (b_t - b_m) / a_m

        然后映射到:

            gain_10k ≈ α * 10000
            zero_offset ≈ β
        """
        cfg = self.config
        a_m, b_m = self._code_to_measured

        # 理论模型:code -> 期望输出
        code_span = cfg.code_max - cfg.code_min
        if code_span == 0:
            raise ValueError("配置错误: code_max 不可等于 code_min")

        out_span = cfg.output_max - cfg.output_min
        a_t = out_span / code_span
        b_t = cfg.output_min - a_t * cfg.code_min

        if abs(a_m) < 1e-12:
            # 极端情况:实测斜率几乎为 0，退化为不调增益
            alpha = 1.0
            beta = 0.0
        else:
            alpha = a_t / a_m
            beta = (b_t - b_m) / a_m

        gain_10k = int(round(alpha * 10000.0))
        gain_10k = int(np.clip(gain_10k, cfg.gain_min, cfg.gain_max))

        zero_offset = int(round(beta))
        zero_offset = int(np.clip(zero_offset, -cfg.offset_limit, cfg.offset_limit))

        return CalibrationCoefficients(
            zero_offset=zero_offset,
            span_offset=0,
            gain_10k=gain_10k,
        )

    def _calculate_avg_error(self, coef: CalibrationCoefficients) -> float:
        """
        根据当前系数计算“校准后平均绝对误差”

        使用 I_meas(code_cal) 作为“校准后输出”，与 expected_output 对比。
        """
        inputs, expected, _ = self.data.get_arrays()
        errors: List[float] = []

        for i, inp in enumerate(inputs):
            raw_code = self.data.input_to_raw_code(inp)
            cal_code = self.apply_calibration(raw_code, coef)
            cal_out = self._predict_output_from_code(cal_code)
            errors.append(abs(cal_out - expected[i]))

        return float(np.mean(errors))

    def calculate_twopoint_calibration(self) -> CalibrationCoefficients:
        """
        计算两点校准系数(调整 zero_offset、span_offset 和 gain_10k)

        仍然使用数值优化(scipy.optimize.minimize)最小化
        “校准后平均绝对误差”，但初始值可以参考线性解析解。
        """
        inputs, expected, measured = self.data.get_arrays()
        cfg = self.config

        # 先用解析线性解作为初值的基础
        linear_coef = self.calculate_linear_calibration()
        init_zero = linear_coef.zero_offset
        init_gain = linear_coef.gain_10k
        init_span = 0

        def objective(params: np.ndarray) -> float:
            zero_offset, span_offset, gain_10k = params
            coef = CalibrationCoefficients(
                zero_offset=int(zero_offset),
                span_offset=int(span_offset),
                gain_10k=int(gain_10k),
            )

            err_sum = 0.0
            for i, inp in enumerate(inputs):
                raw_code = self.data.input_to_raw_code(inp)
                cal_code = self.apply_calibration(raw_code, coef)
                cal_out = self._predict_output_from_code(cal_code)
                err_sum += abs(cal_out - expected[i])
            return err_sum / len(inputs)

        result = minimize(
            objective,
            x0=[init_zero, init_span, init_gain],
            method="L-BFGS-B",
            bounds=[
                (-cfg.offset_limit, cfg.offset_limit),   # zero_offset
                (-cfg.offset_limit, cfg.offset_limit),   # span_offset
                (cfg.gain_min, cfg.gain_max),            # gain_10k
            ],
        )

        zero_offset = int(result.x[0])
        span_offset = int(result.x[1])
        gain_10k = int(result.x[2])

        return CalibrationCoefficients(
            zero_offset=zero_offset,
            span_offset=span_offset,
            gain_10k=gain_10k,
        )

    def auto_calibrate(self) -> Tuple[CalibrationCoefficients, bool]:
        """
        自动校准:
        1. 先尝试线性解析校准(zero + gain)
        2. 若平均误差 <= max_avg_error，则采用线性校准
        3. 否则使用两点校准(zero + span + gain)

        返回:
            (校准系数, 是否使用线性校准)
        """
        # 线性解析校准
        linear_coef = self.calculate_linear_calibration()
        linear_err = self._calculate_avg_error(linear_coef)

        if linear_err <= self.config.max_avg_error:
            return linear_coef, True

        # 线性不满足要求，使用两点校准
        twopoint_coef = self.calculate_twopoint_calibration()
        return twopoint_coef, False


# ===================== 分析与评估 =====================

class CalibrationAnalyzer:
    """校准分析器:线性度、误差、R² 等"""

    @staticmethod
    def calculate_linearity(x: np.ndarray, y: np.ndarray) -> float:
        """
        计算线性度(非线性最大偏差占量程百分比)

        返回:
            线性度百分比(0~100%，越小越好)
        """
        if len(x) < 2:
            return 0.0

        coeffs = np.polyfit(x, y, 1)
        y_fit = np.polyval(coeffs, x)
        nonlin = y - y_fit

        fs = np.max(y) - np.min(y)
        if fs == 0:
            return 0.0

        return float(np.max(np.abs(nonlin)) / fs * 100.0)

    @staticmethod
    def calculate_avg_error(expected: np.ndarray, actual: np.ndarray) -> float:
        return float(np.mean(np.abs(actual - expected)))

    @staticmethod
    def calculate_max_error(expected: np.ndarray, actual: np.ndarray) -> float:
        return float(np.max(np.abs(actual - expected)))

    @staticmethod
    def calculate_r_squared(x: np.ndarray, y: np.ndarray) -> float:
        if len(x) < 2:
            return 1.0
        coeffs = np.polyfit(x, y, 1)
        y_fit = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1.0 - ss_res / ss_tot)

