# 线性输入输出校准工具 (Linear I/O Calibration Tool)

## 目录

- [项目概述](#项目概述)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [使用方法](#使用方法)
- [设计思路](#设计思路)
- [数据格式说明](#数据格式说明)
- [校准算法原理](#校准算法原理)
- [示例](#示例)

---

## 项目概述

本工具用于自动生成**线性输入输出系统**的校准系数，适用于需要精确输出控制的嵌入式系统（如 DAC 输出、电流环路等）。

### 主要功能

1. **自动计算校准系数**：从测试数据自动求解 `zero_offset`（零点偏移）和 `gain_10k`（增益万分比）
2. **多种数据输入模式**：支持输入值（如频率）或直接提供码值（如 DAC 码值）
3. **校准效果分析**：计算平均误差、最大误差、线性度、R² 等指标
4. **可视化对比**：绘制校准前后曲线和误差柱状图
5. **C 代码生成**：直接输出可用于嵌入式系统的 C 结构体初始化代码
6. **多系数对比**：支持导入其他校准系数进行效果对比
7. **预测数据导出**：生成完整量程的对比预测数据 CSV 文件

---

## 快速开始

### 安装依赖

```bash
pip install numpy matplotlib
```

### 基本使用

1. **准备配置文件** `calibration_config.json`（首次运行会自动创建默认配置）
2. **准备测量数据** `calibration_data.csv`（包含测试点的实测输出）
3. **运行校准工具**：

```bash
python calibration_tool.py
```

### 完整命令示例

```bash
python calibration_tool.py \
  --config calibration_config.json \
  --data calibration_data.csv \
  --output calibration_result.png \
  --log calibration_result.log \
  --compare-coefs prev_calib.json \
  --comparison-csv comparison_output.csv
```

---

## 核心概念

### 1. 校准系数 (Calibration Coefficients)

本工具使用**两点校准法**，通过三个参数描述校准：

```c
typedef struct {
    int zero_offset;  // 零点偏移（码值），用于校正零点误差
    int span_offset;  // 满量程偏移（码值），本工具固定为 0
    int gain_10k;     // 增益（万分比），10000 = 1.0 倍
} Calib_t;
```

- **zero_offset**：在基准零点（code_min）处的码值偏移量，用于校正零点误差
- **gain_10k**：整体增益调整，以万分比表示（10000 = 不缩放，9000 = 0.9倍，11000 = 1.1倍）
- **span_offset**：满量程偏移，本工具算法中固定为 0（简化为线性校准）

### 2. 数据模式 (Data Mode)

支持两种数据输入模式：

#### Input 模式（输入值模式）
- 提供物理输入值（如频率 49.8 Hz）
- 工具根据配置自动计算对应的理论码值和期望输出

#### Code 模式（码值模式）
- 直接提供 DAC 码值（如 0x147A = 5242）
- 跳过输入值到码值的转换，直接使用码值进行校准
- 若同时提供 `input_value` 与 `code/raw_code`，会优先使用码值列；`input_value` 仅作为参考

### 3. 校准流程

```
测试数据 → 拟合实测模型 → 建立理论模型 → 解析求解系数 → 验证校准效果
```

1. **拟合实测模型**：`I_meas(code) = a_m * code + b_m`
2. **建立理论模型**：`I_exp(code) = a_t * code + b_t`
3. **解析求解**：通过公式直接计算 `zero_offset` 和 `gain_10k`
4. **应用校准**：模拟 MCU 侧的校准公式验证效果

---

## 使用方法

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-c, --config` | 配置文件路径 | `calibration_config.json` |
| `-d, --data` | 测量数据 CSV 路径 | `calibration_data.csv` |
| `-o, --output` | 校准曲线图保存路径 | `output/calibration_result.png` |
| `-l, --log` | 日志文件保存路径 | `output/calibration_result.log` |
| `--compare-coefs` | 额外校准系数 JSON 文件列表 | 无 |
| `--comparison-csv` | 保存系数对比预测数据的 CSV 路径 | 无 |
| `--no-show` | 仅保存图像，不弹出窗口 | False |

### 配置文件格式 (calibration_config.json)

```json
{
  "input_min": 49.8,           // 输入最小值（如频率 Hz）
  "input_max": 50.2,           // 输入最大值
  "output_min": 4.0,           // 输出最小值（如电流 mA）
  "output_max": 20.0,          // 输出最大值
  "code_min": 5242,            // 最小码值（对应 output_min）
  "code_max": 26213,           // 最大码值（对应 output_max）
  "max_avg_error": 0.3,        // 允许的最大平均绝对误差
  "offset_limit": 2000,        // 允许的偏移量范围（码值）
  "gain_min": 5000,            // 最小增益（0.5 倍）
  "gain_max": 15000,           // 最大增益（1.5 倍）
  "code_saturation_min": 0,    // 码值饱和下限
  "code_saturation_max": 32767 // 码值饱和上限
}
```

### 测量数据格式 (calibration_data.csv)

#### 格式 1：Input 模式 + 自动推导期望值

```csv
input_value,measured_output
49.8,4.1
50.0,12.05
50.2,19.9
```

#### 格式 2：Input 模式 + 显式提供期望值

```csv
input_value,expected_output,measured_output
49.8,4.0,4.1
50.0,12.0,12.05
50.2,20.0,19.9
```

#### 格式 3：Code 模式（直接提供码值）

```csv
code,measured_output
5242,4.1
15727,12.05
26213,19.9
```

或使用 `raw_code` 字段：

```csv
raw_code,expected_output,measured_output
5242,4.0,4.1
15727,12.0,12.05
26213,20.0,19.9
```

---

## 设计思路

### 架构设计

项目采用**模块化分离设计**：

```
calibration_core.py          # 核心算法模块
├── CalibrationConfig        # 配置数据类
├── CalibrationData          # 数据管理类
├── CalibrationCoefficients  # 校准系数类
├── LinearCalibrator         # 线性校准算法类
└── CalibrationAnalyzer      # 校准质量评估类

calibration_tool.py          # 命令行工具模块
├── CalibrationVisualizer    # 可视化与报告类
└── main()                   # 命令行入口函数
```

### 关键设计原则

#### 1. MCU 侧校准公式一致性

工具中的 `LinearCalibrator.apply_calibration()` 函数**完全模拟** MCU 侧的校准流程：

```python
def apply_calibration(self, raw_code: int, coef: CalibrationCoefficients) -> int:
    """
    按 MCU 侧 ma_out_apply_calibration 的两点校准流程模拟：
    1) 以 code_min/code_max 基准做零/满偏移
    2) 再乘万分比增益
    3) 按配置的码值饱和范围裁剪
    """
    # ... 与 MCU 侧 C 代码逻辑一致的实现 ...
```

**关键点**：
- 使用整数除法向零截断（`int(numer / denom)`），与 C 语言行为一致
- 先做两点校准，再做增益调整，最后饱和保护
- 确保 Python 工具的预测与实际 MCU 行为完全匹配

#### 2. 解析解算法（非迭代优化）

不使用梯度下降等迭代优化方法，而是通过**数学推导**直接求解校准系数：

```python
# 解析求解零点偏移
denom_z = a_t * (1.0 + code_min / S) + (b_t - b_m) / S
zero = (b_t - b_m) / denom_z

# 解析求解增益
gain = a_t / (a_m * (1.0 - zero / S))
```

**优势**：
- 计算速度快，无需迭代
- 结果稳定，不受初值影响
- 数学意义明确，便于调试

#### 3. 测量分辨率自适应

工具会自动从测量数据推断仪表分辨率：

```python
@staticmethod
def _infer_measurement_resolution(raw_values: List[str]) -> float:
    """
    从测量值文本推断最小分辨率:
    - 找到小数点后最后一个非零数字所在位数
    - 例: '3.8' → 1位 → 0.1, '12.450' → 2位 → 0.01
    """
```

**用途**：
- 用于 `flex_zone` 误差容忍（`分辨率 / 2`）
- 用于生成对比预测 CSV 的采样精度

#### 4. 多系数对比功能

支持导入多个历史校准系数进行效果对比：

```bash
python calibration_tool.py --compare-coefs prev1.json prev2.json --comparison-csv output.csv
```

**输出内容**：
- 参数对比表格（zero/span/gain + 误差/线性度/R²）
- 详细数据对比表（每个测试点的 Expected/Measured/Calibrated/Error）
- 完整量程预测数据 CSV（最多 300 行，按头中尾采样）

#### 5. 可视化与交互

生成的图表包含**鼠标悬停交互功能**

- 鼠标移动时实时显示理论值和校准值
- 方便在图表上快速查看任意点的数据

---

## 数据格式说明

### CSV 数据要求

1. **必须包含表头**（第一行为字段名）
2. **必须有 `measured_output` 列**（实测输出值）
3. **必须有以下之一**：
   - `input_value`（输入值）
   - `code` 或 `raw_code`（码值）
4. **可选字段**：
   - `expected_output`（期望输出，不提供则根据配置自动推导）
5. **优先级说明**：
   - 若同时存在 `input_value` 与 `code/raw_code` 列，工具会优先使用码值列参与拟合/校准，`input_value` 仅作参考

### 配置参数说明

#### 物理量程参数

- `input_min/input_max`：输入量程（如频率 49.8~50.2 Hz）
- `output_min/output_max`：输出量程（如电流 4~20 mA）
- `code_min/code_max`：码值量程（如 DAC 码值 5242~26213）

**注意**：这三组参数定义了线性映射关系：
```
input_min → code_min → output_min
input_max → code_max → output_max
```

#### 约束参数

- `offset_limit`：零点偏移允许范围（默认 ±2000 码值）
- `gain_min/gain_max`：增益允许范围（默认 0.5~1.5 倍）
- `code_saturation_min/max`：码值饱和保护范围
- `max_avg_error`：允许的最大平均误差（用于报告，不影响计算）

---

## 校准算法原理

### 数学模型

#### 1. 实测模型（通过测试数据拟合）

```
I_meas(code) = a_m * code + b_m
```

其中：
- `a_m`：实测斜率（通过线性回归拟合）
- `b_m`：实测截距

#### 2. 理论模型（根据配置计算）

```
I_exp(code) = a_t * code + b_t
```

其中：
- `a_t = (output_max - output_min) / (code_max - code_min)`
- `b_t = output_min - a_t * code_min`

#### 3. 校准公式（与 MCU 侧一致）

```c
// MCU 侧校准流程
span_full = (code_max + span_offset) - (code_min + zero_offset);
scaled = (raw_code - code_min) * span_full / span_code;
calibrated = scaled + (code_min + zero_offset);
calibrated = calibrated * gain_10k / 10000;
calibrated = saturate(calibrated, sat_min, sat_max);
```

简化为数学表达式（span_offset = 0）：

```
code_cal = G * [(code - code_min) * (1 - z/S) + code_min + z]
```

其中：
- `z = zero_offset`
- `S = code_max - code_min`（码值量程）
- `G = gain_10k / 10000`

#### 4. 解析解推导

目标：使校准后的实测模型与理论模型一致

```
I_meas(code_cal) = I_exp(code)
a_m * code_cal + b_m = a_t * code + b_t
```

展开校准公式并匹配系数，得到：

```
# 零点偏移解：
z = (b_t - b_m) / [a_t * (1 + code_min/S) + (b_t - b_m)/S]

# 增益解：
G = a_t / [a_m * (1 - z/S)]
```

#### 5. 整数化与约束

```python
# 转换为整数（万分比）
gain_10k = int(round(gain * 10000.0))
zero_offset = int(round(zero))

# 约束限制
gain_10k = clip(gain_10k, gain_min, gain_max)          # [5000, 15000]
zero_offset = clip(zero_offset, -offset_limit, offset_limit)  # [-2000, 2000]
```

---

## 示例

### 示例 1：基本校准流程

#### 准备配置文件 `calibration_config.json`

```json
{
  "input_min": 49.8,
  "input_max": 50.2,
  "output_min": 4.0,
  "output_max": 20.0,
  "code_min": 5242,
  "code_max": 26213,
  "max_avg_error": 0.3,
  "offset_limit": 2000,
  "gain_min": 5000,
  "gain_max": 15000,
  "code_saturation_min": 0,
  "code_saturation_max": 32767
}
```

#### 准备测量数据 `calibration_data.csv`

```csv
input_value,measured_output
49.8,4.15
49.9,8.1
50.0,12.05
50.1,16.0
50.2,19.85
```

#### 运行校准

```bash
python calibration_tool.py -c calibration_config.json -d calibration_data.csv
```

#### 输出结果

**终端输出**（同时保存到 `calibration_result.log`）：

```
============================================================
校准分析报告
============================================================

校准模式: 线性校准(zero + gain)

建议 C 代码(示例变量名 calib):
static const Calib_t calib = {
  .zero_offset = -150,
  .span_offset = 0,
  .gain_10k = 9800
};

线性度指标(越小越好):
...
...

误差指标:
...
...

拟合优度 R²(越接近 1 越好):
...
...

详细数据对比:
     Input   Expected   Measured  Calibrated  Err_Before   Err_After
----------------------------------------------------------------------
...
----------------------------------------------------------------------
```

**生成文件**：
- `output/calibration_result.png`：校准曲线对比图 + 误差柱状图
- `output/calibration_result.log`：完整日志文件

### 示例 2：系数对比

#### 准备历史校准系数 `prev_calib.json`

```json
{
  "zero_offset": -100,
  "span_offset": 0,
  "gain_10k": 10000
}
```

#### 运行对比

```bash
python calibration_tool.py \
  --data calibration_data.csv \
  --compare-coefs prev_calib.json \
  --comparison-csv comparison.csv
```

#### 对比输出

```
校准系数对比(基准: auto)
Name         zero     span       gain      avg_err      max_err     lin(%)        R2
---------------------------------------------------------------------------------------
auto         -150        0       9800        0.0023        0.0050     0.0012   0.99999
prev_calib   -100        0      10000        0.0350        0.0800     0.0450   0.99950
---------------------------------------------------------------------------------------
```

#### 生成的 `comparison.csv`

包含完整量程的预测数据（最多 300 行，按头中尾采样）：

```csv
Input,Expected,auto,prev_calib
49.800,4.000,4.002,4.050
49.801,4.008,4.010,4.058
...
50.000,12.000,12.003,12.035
...
50.200,20.000,19.995,19.950
```

### 示例 3：Code 模式（直接使用码值）

#### 准备测量数据 `calibration_data_code.csv`

```csv
code,expected_output,measured_output
5242,4.0,4.15
10485,8.0,8.10
15727,12.0,12.05
20970,16.0,16.00
26213,20.0,19.85
```

#### 运行校准

```bash
python calibration_tool.py -d calibration_data_code.csv
```

**效果**：工具自动识别为 Code 模式，跳过 input → code 转换，直接使用提供的码值进行校准。

---

## 高级功能

### 1. terminal环境运行（服务器/自动化）

```bash
python calibration_tool.py --no-show
```

仅保存图像，不弹出 matplotlib 窗口，适合无图形界面的服务器环境。

### 2. 自定义输出路径

```bash
python calibration_tool.py \
  -o results/calib_2024.png \
  -l logs/calib_2024.log \
  --comparison-csv results/comparison_2024.csv
```

### 3. 批量对比多个历史系数

```bash
python calibration_tool.py \
  --compare-coefs calib_v1.json calib_v2.json calib_v3.json \
  --comparison-csv batch_comparison.csv
```

生成的对比表格将包含所有系数的误差和线性度指标。

---

## 常见问题 (FAQ)

### Q1: 计算出的 `zero_offset` 或 `gain_10k` 超出限制怎么办？

**A**: 工具会自动裁剪到配置的 `offset_limit` 和 `gain_min/gain_max` 范围内。如果裁剪后误差仍然过大，可能原因：

1. **测量数据质量差**：检查传感器/仪表精度
2. **系统非线性严重**：线性校准不适用，需考虑非线性校准
3. **配置参数错误**：检查 `code_min/code_max` 是否与实际系统匹配

### Q2: 校准后误差反而变大了？

**A**: 可能原因：

1. **测量点太少**：建议至少 5 个均匀分布的测试点
2. **测量点分布不均**：应覆盖整个量程（input_min ~ input_max）
3. **MCU 侧实现与工具不一致**：检查 MCU 的校准公式是否与 `apply_calibration()` 一致

### Q3: 如何验证工具的预测准确性？

**A**: 使用 `--comparison-csv` 功能：

```bash
python calibration_tool.py --comparison-csv predict.csv
```

将生成的 `predict.csv` 导入表格软件，与实际 MCU 输出对比，验证预测误差。

### Q4: `span_offset` 为什么固定为 0？

**A**: 本工具采用简化的线性校准模型，只调整零点和增益。大多数线性系统只需这两个参数即可满足精度要求。如需完整的两点校准（独立调整零点和满量程），需修改算法。

### Q5: 如何处理负输出（如 -10V ~ +10V）？

**A**: 配置文件支持负数：

```json
{
  "output_min": -10.0,
  "output_max": 10.0,
  ...
}
```

算法自动支持负值范围。

---

## 技术细节

### 分辨率推断算法

工具通过分析 CSV 中 `measured_output` 列的**文本格式**推断仪表分辨率：

```python
# 示例：
"3.8"    → 1 位小数 → 分辨率 0.1
"12.450" → 2 位有效小数（去除尾部 0）→ 分辨率 0.01
"4"      → 无小数 → 分辨率 1.0
```

**用途**：
- `flex_zone = 分辨率 / 2`，用于误差容忍（未来可能用于优化）
- 对比预测 CSV 的采样间隔

### 整数除法一致性

为确保 Python 预测与 MCU 实际行为一致，工具使用**向零截断除法**：

```python
def _div_trunc(numer: int, denom: int) -> int:
    return int(numer / denom)  # Python 的 int() 向零截断，与 C 语言一致
```

**注意**：Python 的 `//` 是**向下取整除法**（floor division），对负数结果不同：

```python
-7 // 2  # Python: -4  (向下取整)
int(-7 / 2)  # Python: -3  (向零截断，与 C 一致)
```

### 代码组织

```
calibration_core.py
├── 数据结构
│   ├── CalibrationCoefficients  # 校准系数
│   ├── MeasurementPoint         # 测量点
│   ├── CalibrationConfig        # 配置
│   └── CalibrationData          # 数据管理
├── 校准算法
│   ├── LinearCalibrator         # 线性校准器
│   │   ├── apply_calibration()  # MCU 侧公式模拟
│   │   └── calculate_linear_calibration()  # 解析解算法
│   └── CalibrationAnalyzer      # 误差/线性度分析
└── 工具函数

calibration_tool.py
├── CalibrationVisualizer
│   ├── plot_calibration_curves()      # 可视化
│   ├── print_analysis_report()        # 分析报告
│   ├── print_coefficient_comparison() # 系数对比
│   └── _save_comparison_csv()         # 导出预测数据
└── main()                             # 命令行入口
```

---

## 附录

### A. 配置文件模板

见 `calibration_config.json`（首次运行自动生成）

### B. 测试数据模板

见 `calibration_data.csv`（用户自行准备）

### C. C 代码集成示例

```c
// 在 MCU 代码中使用生成的校准系数
static const Calib_t calib = {
  .zero_offset = -150,
  .span_offset = 0,
  .gain_10k = 9800
};

// 应用校准
int16_t raw_code = 15727;  // 原始 DAC 码值
int16_t calibrated = ma_out_apply_calibration(raw_code, &calib);
// 输出: calibrated ≈ 15577（校准后码值）
```

### D. 算法验证方法

1. **单元测试**：测试 `apply_calibration()` 与 MCU 侧结果一致性
2. **回归测试**：使用已知数据验证解析解的正确性
3. **边界测试**：测试饱和保护、极端增益等边界情况

---
