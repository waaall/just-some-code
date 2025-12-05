#!/usr/bin/env python3
"""
核心模块:数据结构与校准算法

包含:
- 数据结构
    - CalibrationConfig
    - CalibrationData
    - CalibrationCoefficients
    - MeasurementPoint
- 线性校准类(LinearCalibrator): 注意校准的过程和系数的约定
- 校准质量评估类(CalibrationAnalyzer)
"""

import csv
import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

import numpy as np


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
    input_value: Optional[float]      # 输入值(如频率 Hz)，若直接提供码值则为 None
    expected_output: float            # 期望输出(如电流 mA，可由配置推导)
    measured_output: float            # 实际测量输出(如电流 mA)
    raw_code: Optional[int] = None    # 若 CSV 直接提供码值则使用该字段


@dataclass
class CalibrationConfig:
    """
    校准配置参数
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
    code_saturation_min: int = 0       # 码值饱和下限(校准后饱和下限)
    code_saturation_max: int = 32767   # 码值饱和上限(校准后饱和上限)

    @classmethod
    def from_json(cls, json_path: str) -> "CalibrationConfig":
        """从 JSON 文件加载配置"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 兼容旧字段名 dac_code_min/dac_code_max
        if "code_saturation_min" not in data and "dac_code_min" in data:
            data["code_saturation_min"] = data.pop("dac_code_min")
        if "code_saturation_max" not in data and "dac_code_max" in data:
            data["code_saturation_max"] = data.pop("dac_code_max")
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
        self.measurement_resolution: float = 0.0  # 测试分辨率
        self.flex_zone: float = 0.0               # 分辨率的一半，用于误差容忍
        self.data_mode: str = "input"             # 'input' 或 'code'

    def load_from_csv(self, csv_path: str) -> None:
        """
        从 CSV 文件加载测量数据

        CSV 支持三种格式:
        1) input_value, measured_output(按配置推导期望值)
        2) input_value, expected_output, measured_output(显式提供期望值)
        3) code/raw_code, measured_output(可选 expected_output)，直接使用码值
        """
        self.measurements.clear()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV 文件缺少表头")

            field_set = set(reader.fieldnames)
            if "measured_output" not in field_set:
                raise ValueError("CSV 缺少必要列: measured_output")

            has_input = "input_value" in field_set
            code_field = None
            if "code" in field_set:
                code_field = "code"
            elif "raw_code" in field_set:
                code_field = "raw_code"

            if not has_input and code_field is None:
                raise ValueError("CSV 缺少必要列: input_value 或 code/raw_code")

            has_expected = "expected_output" in field_set
            self.data_mode = "code" if code_field else "input"
            measured_raw_list: List[str] = []

            for row in reader:
                measured_raw = row["measured_output"]
                measured_output = float(measured_raw)
                measured_raw_list.append(str(measured_raw))

                exp_raw = row.get("expected_output") if has_expected else None
                raw_code: Optional[int] = None
                input_value: Optional[float] = None

                if code_field:
                    raw_txt = row.get(code_field, "").strip()
                    if raw_txt == "":
                        raise ValueError("CSV 行缺少 code/raw_code 值")
                    raw_code = int(round(float(raw_txt)))

                    if has_input:
                        inp_txt = row.get("input_value", "").strip()
                        input_value = float(inp_txt) if inp_txt != "" else None

                    if exp_raw is not None and str(exp_raw).strip() != "":
                        expected_output = float(exp_raw)
                    else:
                        expected_output = self.expected_output_from_code(raw_code)
                else:
                    input_txt = row.get("input_value", "").strip()
                    if input_txt == "":
                        raise ValueError("CSV 行缺少 input_value 值")
                    input_value = float(input_txt)
                    raw_code = self.input_to_raw_code(input_value)

                    if exp_raw is not None and str(exp_raw).strip() != "":
                        expected_output = float(exp_raw)
                    else:
                        expected_output = self.expected_output_from_input(input_value)

                self.measurements.append(
                    MeasurementPoint(
                        input_value=input_value,
                        expected_output=expected_output,
                        measured_output=measured_output,
                        raw_code=raw_code,
                    )
                )

        # 根据测量值文本推断分辨率（例: 3.8 → 0.1mA），flex_zone = 分辨率 / 2
        self.measurement_resolution = self._infer_measurement_resolution(measured_raw_list)
        self.flex_zone = self.measurement_resolution * 0.5

    def get_arrays(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """返回 numpy 数组格式的数据 (inputs, expected, measured)"""
        inputs: List[float] = []
        expected: List[float] = []
        measured: List[float] = []

        for m in self.measurements:
            if self.data_mode == "code":
                if m.raw_code is not None:
                    inputs.append(float(m.raw_code))
                elif m.input_value is not None:
                    inputs.append(float(m.input_value))
                else:
                    raise ValueError("测量数据缺少 input_value/raw_code")
            else:
                if m.input_value is not None:
                    inputs.append(float(m.input_value))
                elif m.raw_code is not None:
                    inputs.append(float(m.raw_code))
                else:
                    raise ValueError("测量数据缺少 input_value/raw_code")

            expected.append(float(m.expected_output))
            measured.append(float(m.measured_output))

        return (
            np.array(inputs, dtype=float),
            np.array(expected, dtype=float),
            np.array(measured, dtype=float),
        )

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
        codes: List[float] = []
        for m in self.measurements:
            if m.raw_code is not None:
                codes.append(float(m.raw_code))
            elif m.input_value is not None:
                codes.append(float(self.input_to_raw_code(m.input_value)))
            else:
                raise ValueError("测量数据缺少 input_value/raw_code")

        return np.array(codes, dtype=float)

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

    def expected_output_from_code(self, code: float) -> float:
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
        return self.expected_output_from_code(raw_code)

    @staticmethod
    def _infer_measurement_resolution(raw_values: List[str]) -> float:
        """
        从测量值文本推断最小分辨率:
        - 找到小数点后最后一个非零数字所在位数，得到分辨率(例: '3.8' → 1位 → 0.1)
        - 若全为整数则返回 1.0
        """
        min_res = None
        # 遍历所有测量值文本，分析小数位数以推断仪表分辨率
        for raw in raw_values:
            txt = str(raw).strip()
            if not txt:
                continue
            # 判断是否有小数点
            if "." in txt:
                # 提取小数部分（例: "3.8" → "8", "12.450" → "450"）
                _, right = txt.split(".", 1)
                # 去除尾部的0（"450" → "45"），得到有效小数位
                right_no_trailing = right.rstrip("0")
                if right_no_trailing == "":
                    decimals = 0  # "4.0" → 整数
                else:
                    decimals = len(right_no_trailing)  # "3.8" → 1位, "12.45" → 2位
            else:
                decimals = 0  # 无小数点，为整数

            # 根据小数位数计算分辨率（1位 → 0.1, 2位 → 0.01）
            res = 10.0 ** (-decimals) if decimals > 0 else 1.0
            # 取所有值的最小分辨率（以最精细的为准）
            min_res = res if min_res is None else min(min_res, res)

        return min_res if min_res is not None else 0.1


# ===================== 校准核心算法 =====================

class LinearCalibrator:
    """线性校准器"""

    def __init__(self, data: CalibrationData) -> None:
        self.data = data
        self.config = data.config
        # 拟合得到 I_meas(code) = a_m * code + b_m
        self._code_to_measured = data.fit_code_to_measured_model()
        self._flex_zone = data.flex_zone

    # ---- MCU 侧应保持一致的校准公式 ----
    def apply_calibration(self, raw_code: int, coef: CalibrationCoefficients) -> int:
        """
        按 MCU 侧 ma_out_apply_calibration 的两点校准流程模拟：
        1) 以 code_min/code_max 基准做零/满偏移
        2) 再乘万分比增益
        3) 按配置的码值饱和范围裁剪
        """
        sat_min = int(self.config.code_saturation_min)
        sat_max = int(self.config.code_saturation_max)
        if raw_code <= sat_min:
            return sat_min

        # 提取配置参数：4mA 和 20mA 对应的 DAC 码值
        code_min = int(self.config.code_min)    # 4mA 参考点
        code_max = int(self.config.code_max)   # 20mA 参考点
        span_code = code_max - code_min              # 原始量程
        if span_code == 0:
            return raw_code

        # 提取校准系数
        zero = int(coef.zero_offset)  # 零点偏移（码值）
        span = int(coef.span_offset)  # 满量程偏移（码值，通常为0）
        gain = int(coef.gain_10k)     # 增益（万分比，10000 = 1.0倍）

        # Python // 对负数向下取整，C 的 / 向零截断；保持一致用 trunc
        def _div_trunc(numer: int, denom: int) -> int:
            return int(numer / denom)

        # 步骤1: 两点校准 - 计算校准后的量程
        # span_full = (校准后max点) - (校准后min点)
        span_full = (code_max + span) - (code_min + zero)

        # 步骤2: 线性缩放 - 按校准后量程重新映射码值
        # scaled = (raw - code_min) * span_full / span_code
        numerator = (int(raw_code) - code_min) * span_full
        scaled = _div_trunc(numerator, span_code)
        calibrated = scaled + (code_min + zero)  # 加上校准后的零点

        # 步骤3: 增益调整
        calibrated = _div_trunc(calibrated * gain, 10000)

        # 步骤4: 饱和保护
        if calibrated < sat_min:
            calibrated = sat_min
        if calibrated > sat_max:
            calibrated = sat_max

        return int(calibrated)

    def _predict_output_from_code(self, code: int) -> float:
        """使用实测拟合模型预测给定码值的输出"""
        a_m, b_m = self._code_to_measured
        y = a_m * code + b_m
        # 裁剪到量程内
        y = float(np.clip(y, self.config.output_min, self.config.output_max))
        return y

    def calculate_linear_calibration(self) -> CalibrationCoefficients:
        """
        计算线性校准系数(只调整 zero_offset 和 gain_10k)，解析解直接对应
        MCU 的两点校准公式(固定 span_offset=0)。

        推导:
          I_meas(code) = a_m*code + b_m
          I_exp(code)  = a_t*code + b_t
          code_cal = G * [ (code-code_min)*(1 - z/S) + code_min + z ], 其中 z=zero_offset, G=gain

          系数匹配得到:
            a_m * G * (1 - z/S) = a_t
            a_m * G * z * (1 + code_min/S) + b_m = b_t

          解:
            z = (b_t - b_m) / [ a_t*(1 + code_min/S) + (b_t - b_m)/S ]
            G = a_t / (a_m * (1 - z/S))
        """
        cfg = self.config
        # 获取实测拟合模型: I_meas(code) = a_m * code + b_m
        a_m, b_m = self._code_to_measured

        # 建立理论模型: I_exp(code) = a_t * code + b_t
        code_span = cfg.code_max - cfg.code_min
        if code_span == 0:
            raise ValueError("配置错误: code_max 不可等于 code_min")

        # 计算理论模型的斜率和截距
        out_span = cfg.output_max - cfg.output_min
        a_t = out_span / code_span      # 理论斜率
        b_t = cfg.output_min - a_t * cfg.code_min  # 理论截距

        # 准备解析解所需的参数
        code_min = float(cfg.code_min)  # 4mA 参考点
        S = float(code_span)      # 码值量程

        # 极端情况处理: 实测斜率接近0（测量无响应）
        if abs(a_m) < 1e-12:
            # 退化为默认系数（无校准）
            gain_10k = 10000
            zero_offset = 0
        else:
            # 解析求解零点偏移 z = (b_t - b_m) / [ a_t*(1 + code_min/S) + (b_t - b_m)/S ]
            denom_z = a_t * (1.0 + code_min / S) + (b_t - b_m) / S
            if abs(denom_z) < 1e-12:
                zero = 0.0  # 分母为0时零点设为0
            else:
                zero = (b_t - b_m) / denom_z  # 零点偏移（浮点数）

            # 解析求解增益 G = a_t / (a_m * (1 - z/S))
            if abs(1.0 - zero / S) < 1e-12:
                gain = 1.0  # 分母为0时增益设为1
            else:
                gain = a_t / (a_m * (1.0 - zero / S))  # 增益（浮点数）

            # 转换为整数（万分比）
            gain_10k = int(round(gain * 10000.0))  # 转为万分比整数
            zero_offset = int(round(zero))         # 转为整数码值

            # 约束限制（防止极端值）
            gain_10k = int(np.clip(gain_10k, cfg.gain_min, cfg.gain_max))  # [5000, 15000]
            zero_offset = int(np.clip(zero_offset, -cfg.offset_limit, cfg.offset_limit))  # [-2000, 2000]

        # 返回校准系数（span_offset 固定为0）
        return CalibrationCoefficients(
            zero_offset=zero_offset,
            span_offset=0,
            gain_10k=gain_10k,
        )


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
