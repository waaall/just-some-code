# 输入输出时序信号数据对比绘图工具

一个模块化的Python工具集，用于PMU频率测试数据的可视化分析与精度评估。

## 功能特性

### 主程序功能

- 支持两种CSV格式的自动解析
- 自动检测变化点并对齐时间轴
- 阶梯图（输入）+ 点线图（输出）双图对比
- 鼠标交互显示双y值
- 时间轴精确到100ms可分辨
- 配置文件 + 命令行参数灵活配置
- 静态图保存（高清PNG）+ 动态交互显示

### 辅助工具（tools/）

- **精度分析**：对齐数据的误差统计（全采样/稳态）
- **数据转换**：4-20mA 与频率线性映射转换
- **测试数据生成**：多种波形的频率测试数据生成

## 安装依赖

```bash
pip install numpy matplotlib
```

## 目录结构

```
measure_comparison_plot/
├── measure_plotter.py              # 主程序入口
├── measure_data_parser.py          # CSV数据解析模块
├── measure_data_alignment.py       # 时间对齐模块
├── measure_plotter_core.py         # 绘图核心模块
├── measure_compare_plot.json       # 主程序配置文件
└── tools/                          # 辅助工具目录
    ├── measure_accuracy.py         # 精度分析工具
    ├── measure_accuracy_config.json
    ├── liner_converter.py          # 数据转换工具
    ├── ma_converter_config.json
    └── generate_freq_test_data.py  # 测试数据生成工具
```

## 使用示例

整体的开发流程是:

1. generate_freq_test_data.py 生成测试输入数据，如果测试输入设备也存在信号变化的延迟问题，可同步生成该延迟的校准信号对比使用。
2. 进行测试，采集被测设备输出的数据。
3. 如果输出数据和输入数据不是一个单位或有线性映射关系,比如频率映射为4-20mA信号, 则使用tools/liner_converter.py 将输入或者输出的数据映射为一个单位/量级可以同步对比。注意时间戳的格式可能有所不同需要修改代码；如果没有映射关系跳过这一步。
4. 如果输入数据和输出数据时间戳不一致，则使用 measure_data_alignment.py 来对齐，不过这一步已经集成到了最终步。
5. 画图参数配置: measure_compare_plot.json 是配置文件，其调用到多个模块，例如上述的时间对齐模块还有CSV数据解析模块，配置参数都集成在了这个配置文件中，参数含义若不明白见相关代码文件。
6. 精度计算: 经过上述数据对齐后会默认保存input和output数据对齐后的csv文件, 可以通过 tools/measure_accuracy.py 根据该对齐文件计算稳态与整体误差，具体流程见下或者见代码。

### 示例1：基本用法（使用配置文件）

```bash
python measure_plotter.py
```

输出：
- 解析数据，检测变化点，对齐时间轴
- 生成对比图并保存为 `freq_comparison_result.png`
- 打开交互式窗口显示图表

### 示例2：指定输入输出文件

```bash
python measure_plotter.py -i test1.csv -o test1-result.csv
```

### 示例3：自定义y轴范围

```bash
python measure_plotter.py -i input.csv -o output.csv --ymin 49.85 --ymax 50.15
```

### 示例4：禁用时间对齐

```bash
python measure_plotter.py -i input.csv -o output.csv --no-align
```

### 示例5：仅保存图片，不显示窗口

```bash
python measure_plotter.py -i input.csv -o output.csv --no-show
```

### 示例6：使用自定义阈值

```bash
python measure_plotter.py -i input.csv -o output.csv --threshold 0.005
```

## 配置文件说明

配置文件 `measure_compare_plot.json` 包含所有可调参数：

### 路径解析规则

**配置文件中的相对路径**：相对于配置文件所在目录（即代码所在目录）
**命令行指定的相对路径**：相对于当前工作目录（执行命令的目录）
**绝对路径**：按原样使用

示例：
- 配置文件位于 `/path/to/measure_comparison_plot/measure_compare_plot.json`
- 配置中 `"input_csv_path": "../data/test.csv"` → 解析为 `/path/to/data/test.csv`
- 命令行 `python measure_plotter.py -i ../data/test.csv`（在 `/tmp` 执行） → 解析为 `/data/test.csv`


## CSV格式要求

### 输入文件格式

阶梯变化数据，格式：`日期,时间,毫秒,频率`

```csv
2025-12-9,10:00:00,000,49.900
2025-12-9,10:00:00,200,49.904
2025-12-9,10:00:00,400,49.908
```

**特点**：
- 只记录变化点（不是每个时间点都记录）
- 绘制为阶梯图（每个值保持到下一个变化点）

### 输出文件格式

连续记录数据，格式：`日期时间::毫秒,频率`

```csv
RX Date/Time,组/A_Freq
2025/12/09 10:01:37::608,50.000
2025/12/09 10:01:37::722,50.000
```

**特点**：
- 第一行为header（自动跳过）
- 时间格式为 `YYYY/MM/DD HH:MM:SS::mmm`
- 绘制为点图或折线图


## 模块详细说明

### 主程序模块

#### measure_plotter.py

主程序入口，负责协调整个绘图流程：
- 加载和解析配置文件
- 协调数据解析、对齐、绘图模块
- 提供命令行接口
- 日志输出

#### measure_data_parser.py

数据解析模块：
- 解析两种CSV格式（输入/输出）
- 统一时间戳为相对毫秒数
- 处理BOM字符、不同日期格式

#### measure_data_alignment.py

时间对齐模块：
- 检测首个显著变化点
- 计算时间偏移量
- 平移输出数据时间轴

### 时间对齐算法

可以手动指定对齐时间，也可以会自动对齐输入输出数据的时间轴：

1. **输入起点**：第一个数据点（通常是稳定值）
2. **输出起点**：首个频率变化 >= 阈值（默认0.002Hz）的点
3. **对齐方式**：计算时间差，平移输出数据时间轴

对齐报告示例：

```
[步骤2] 时间对齐
  变化检测阈值: 0.002 Hz
  状态: 对齐成功，时间偏移: 3100ms
  输入变化点:
    - 索引: 1
    - 时间: 200ms (0.200s)
  输出变化点:
    - 索引: 32
    - 原始时间: 3300ms (3.300s)
  时间偏移: 3100ms (3.100s)
```
#### measure_plotter_core.py

绘图核心模块：
- 阶梯图绘制（输入数据）
- 点图/折线图绘制（输出数据）
- 鼠标交互实现
- 时间轴精确配置（100ms可分辨）

### 辅助工具模块（tools/）

#### liner_converter.py

4-20mA 与频率数据转换工具。

**功能**：
- 频率输入 CSV → mA 输入 CSV（线性映射）
- mA 原始输出 CSV（0.1ms采样）→ 标准格式 CSV（时间聚合）
- 标准 mA 输出 CSV → 频率 CSV

**子命令**：
- `convert-input`: 转换频率输入为 mA 输入
- `aggregate-output`: 聚合 mA 原始输出为标准格式
- `aggregate-output-freq`: 将标准 mA 输出转换为频率

详细用法参见前文"4-20mA 数据处理功能"章节。

#### generate_freq_test_data.py

频率测试数据生成工具。

**功能**：生成标准格式的频率动态测试数据，支持三种波形：

- **linear**：线性扫频（阶梯变化）
- **triangle**：三角波（周期性上升下降）
- **sine**：正弦波（平滑周期变化）

**典型用法**：

```bash
# 线性扫频（默认模式）
python generate_freq_test_data.py --start-freq 49.9 --end-freq 50.1 \
  --freq-step 0.01 --interval-ms 200

# 正弦波模式
python generate_freq_test_data.py --waveform-type sine \
  --start-freq 49.9 --end-freq 50.1 \
  --waveform-period-s 10.0 --num-periods 1 --interval-ms 100

# 生成带时间累计误差的校准文件
python generate_freq_test_data.py --waveform-type sine \
  --start-freq 49.9 --end-freq 50.1 \
  --waveform-period-s 5.0 --num-periods 1 \
  --interval-ms 200 --cal-error-ms 4.5
```

**输出格式**：与输入 CSV 格式一致（日期,时间,毫秒,频率），可直接用于绘图测试。

#### measure_accuracy.py

精度分析工具，用于评估对齐后数据的测量误差。

**功能概述**：

从对齐后的 CSV 文件（aligned_ms, input_value, output_value）计算误差统计指标：
- **全采样误差**：对所有数据点计算误差统计
- **稳态误差**：按输入值平台分段，排除各平台的起始过渡期后统计误差，可选欠采样窗口过滤

**使用方法**：

```bash
# 通过配置文件运行
python measure_accuracy.py -c measure_accuracy_config.json
```

**配置参数**：

```json
{
  "aligned_csv_path": "out_aligned.csv",     // 对齐后的CSV文件路径
  "time_col": "aligned_ms",                  // 时间列名（毫秒）
  "input_col": "input_value",                // 输入参考值列名
  "output_col": "output_value",              // 输出测量值列名

  "input_deadband": 1e-6,                    // 输入平台切换阈值
  "steady_exclude_ms": 250,                  // 各平台起始排除时长（ms）
  "steady_min_duration_ms": 500,             // 稳态最小持续时长（ms）

  "undersample_window_ms": null,             // 欠采样窗口 [start, end]（ms）
  "per_level": false,                        // 是否输出各平台详细统计
  "json_out": null,                          // JSON输出路径（可选）
  "log_file": null,                          // 日志文件输出（可选）
  "steady_points_csv": null,                 // 稳态点明细CSV（可选）
  "steady_summary_csv": null                 // 稳态段汇总CSV（可选）
}
```

**主要参数说明**：
- `input_deadband`：检测输入值变化的死区，应大于输入噪声幅度
- `steady_exclude_ms`：排除各平台起始的过渡期，建议设置为算法窗口长度
- `steady_min_duration_ms`：稳态区最小时长，过短的平台将被忽略
- `undersample_window_ms`：可选欠采样窗口，如 `[250, 750]` 表示每秒只取 250-750ms 相位的点

**输出指标**：
- 误差统计：count（样本数）、bias_mean（平均误差）、abs_mean（平均绝对误差）、rmse（均方根误差）、abs_max（最大绝对误差）、abs_p95/p99（95%/99%分位数）
- 时间质量：总点数、非单调时间戳计数、时间步长统计
- 可选文件输出：稳态点明细 CSV、稳态段汇总 CSV、结果 JSON、日志文件

**注意事项**：
- 本工具仅评估数值偏差，不评估动态响应或延迟
- 输入值噪声过大会导致平台过度分段，建议确保输入死区合理
- 稳态区仅排除平台起始的过渡期，不排除结束时的过渡

## 常见问题

### Q1: 如何禁用时间对齐？

A: 使用 `--no-align` 参数或在配置文件中设置 `"enable_alignment": false`

### Q2: 如何调整变化检测灵敏度？

A: 使用 `--threshold` 参数或修改配置文件中的 `alignment_config.change_threshold`（单位由 `threshold_unit` 决定）。值越小越敏感。

### Q3: 输出图片分辨率太低？

A: 在配置文件中调整 `"dpi"` 值（默认300，可设置为600或更高）。

### Q4: 如何修改图表尺寸？

A: 在配置文件中修改 `"figsize": [宽, 高]`（单位：英寸）。

### Q5: 鼠标交互不响应？

A: 确保配置文件中 `"enable_cursor": true`，且使用交互式后端（如TkAgg）。

### Q6: 如何只绘制折线，不绘制散点？

A: 在配置文件中设置 `"output_style": "line"`。

### Q7: 如何批量处理多个文件？

A: 可以编写简单的bash脚本：

```bash
#!/bin/bash
for input_file in *.csv; do
  if [[ $input_file != *"-result"* ]]; then
    output_file="${input_file%.csv}-result.csv"
    python measure_plotter.py -i "$input_file" -o "$output_file" --no-show
  fi
done
```
