# 频率对比绘图工具

一个模块化的Python工具，用于绘制PMU频率测试的输入输出对比图。

## 功能特性

- ✅ 支持两种CSV格式的自动解析
- ✅ 自动检测变化点并对齐时间轴
- ✅ 阶梯图（输入）+ 点线图（输出）双图对比
- ✅ 鼠标交互显示双y值
- ✅ 时间轴精确到100ms可分辨
- ✅ 配置文件 + 命令行参数灵活配置
- ✅ 静态图保存（高清PNG）+ 动态交互显示

## 安装依赖

```bash
pip install numpy matplotlib
```

或者使用requirements.txt（如果提供）：

```bash
pip install -r requirements.txt
```

## 快速开始

### 方式1：使用配置文件（推荐）

1. 编辑配置文件 `measure_compare_plot.json`（与脚本同目录），设置输入输出文件路径：

```json
{
  "input_csv_path": "251209test200ms.csv",
  "output_csv_path": "251209test200ms-result.csv"
}
```

2. 运行程序：

```bash
cd measure_comparison_plot
python measure_plotter.py
```

### 方式2：命令行指定文件

```bash
python measure_plotter.py -i ../251209test200ms.csv -o ../251209test200ms-result.csv
```

## 4-20mA 数据处理功能

除频率数据对比外，工具还支持 4-20mA 数据的转换与绘图。

### 功能特性

- **线性映射**：4-20mA ↔ 频率（可配置，默认 4-20mA 对应 49.8-50.2Hz）
- **精度可调**：mA/频率输出四舍五入步进可设置（如 0.001mA、0.001Hz）
- **输入转换**：频率输入 CSV → mA 输入 CSV
- **输出转换**：mA 输出 CSV（0.1ms采样）→ 标准格式（可配置聚合时间精度）
- **输出频率转换**：标准 mA 输出 CSV → 频率 CSV（默认 0.001Hz）
- **完全兼容**：转换后的文件可直接用于绘图和对齐

### 快速使用

#### 1. 转换频率输入为 mA 输入

```bash
# 使用默认映射（4-20mA ↔ 49.8-50.2Hz）
python liner_converter.py convert-input \
  -i input_freq.csv \
  -o input_ma.csv

# 自定义映射范围
python liner_converter.py convert-input \
  -i input_freq.csv -o input_ma.csv \
  --ma-min 4 --ma-max 20 --freq-min 49.5 --freq-max 50.5

# 指定 mA 输出精度（步进）
python liner_converter.py convert-input \
  -i input_freq.csv -o input_ma.csv \
  --ma-precision 0.001
```

#### 2. 转换 mA 输出为标准格式

```bash
# 将 0.1ms 采样数据聚合为每毫秒一个值（默认 1ms）
python liner_converter.py convert-output \
  -i ma_output_raw.csv \
  -o output_ma_standard.csv

# 指定聚合后的时间精度（如 100ms）
python liner_converter.py convert-output \
  -i ma_output_raw.csv \
  -o output_ma_standard_100ms.csv \
  --aggregate-ms 100

# 指定聚合后 mA 精度（如 0.001mA）
python liner_converter.py convert-output \
  -i ma_output_raw.csv \
  -o output_ma_standard.csv \
  --ma-precision 0.001
```

#### 2.1 转换标准 mA 输出为频率 CSV

```bash
python liner_converter.py convert-output-freq \
  -i output_ma_standard.csv \
  -o output_freq_standard.csv
```

#### 3. 绘制 mA 数据对比图

```bash
# 使用转换后的文件绘图（Y轴显示mA值）
python measure_plotter.py \
  -i input_ma.csv \
  -o output_ma_standard.csv \
  --ymin 4 --ymax 20
```

### 数据格式说明

**输入格式（频率）**：`日期,时间,毫秒,频率`
```csv
2025-12-9,16:00:05,000,49.916
2025-12-9,16:00:05,500,49.920
```

**输出格式（mA原始）**：`YYYY-MM-DD HH:MM:SS.微秒,mA值`（0.1ms采样）
```csv
2025-12-11 10:22:26.419200,19.99777
2025-12-11 10:22:26.419300,19.99777
```

**输出格式（标准化）**：`YYYY/MM/DD HH:MM:SS::毫秒,mA值`（每毫秒聚合）
```csv
2025/12/09 10:05:28::805,18.90
2025/12/09 10:05:28::806,18.90
```

### 配置文件支持

在 `measure_compare_plot.json` 中添加映射配置：

```json
{
  "ma_freq_mapping": {
    "ma_min": 4.0,
    "ma_max": 20.0,
    "freq_min": 49.8,
    "freq_max": 50.2,
    "ma_precision": 0.01,
    "freq_precision": 0.001
  },
  "plot_config": {
    "data_min": 4.0,
    "data_max": 20.0
  }
}
```

### 相关文件

- `liner_converter.py` - 核心转换模块与 CLI（含线性映射、格式转换、毫秒聚合）

### 线性映射公式

**频率 → mA**：`mA = ma_min + (freq - freq_min) / (freq_max - freq_min) × (ma_max - ma_min)`

**示例**（默认 4-20mA ↔ 49.8-50.2Hz）：
- 49.8Hz → 4.00mA
- 50.0Hz → 12.00mA
- 50.2Hz → 20.00mA

## 命令行参数

```bash
python measure_plotter.py [选项]

选项:
  -c, --config CONFIG    配置文件路径（默认: 脚本同目录的 measure_compare_plot.json）
  -i, --input INPUT      输入CSV文件路径
  -o, --output OUTPUT    输出CSV文件路径
  --aligned-output PATH  对齐且裁剪后的输出数据保存路径
  --ymin YMIN            频率轴最小值 (Hz)
  --ymax YMAX            频率轴最大值 (Hz)
  --no-align             禁用时间对齐
  --threshold THRESHOLD  变化检测阈值（单位与配置中的 threshold_unit 一致）
  --no-show              禁用交互式显示（仅保存图片）
  -h, --help             显示帮助信息
```

## 使用示例

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

### 路径解析规则（重要）

**配置文件中的相对路径**：相对于配置文件所在目录（即代码所在目录）
**命令行指定的相对路径**：相对于当前工作目录（执行命令的目录）
**绝对路径**：按原样使用

示例：
- 配置文件位于 `/path/to/measure_comparison_plot/measure_compare_plot.json`
- 配置中 `"input_csv_path": "../data/test.csv"` → 解析为 `/path/to/data/test.csv`
- 命令行 `python measure_plotter.py -i ../data/test.csv`（在 `/tmp` 执行） → 解析为 `/data/test.csv`

### 配置参数详解

```json
{
  // 文件路径（配置文件中的相对路径相对于配置文件所在目录）
  "input_csv_path": "251209test200ms.csv",
  "output_csv_path": "251209test200ms-result.csv",
  "aligned_output_csv_path": "out_aligned.csv",

  // 对齐参数
  "enable_alignment": true,           // 是否启用时间对齐
  "alignment_config": {
    "change_threshold": 0.002,        // 变化检测阈值
    "threshold_unit": "Hz"            // 阈值单位（与数据单位一致）
  },

  // 绘图参数
  "plot_config": {
    "figsize": [14, 6],               // 图表尺寸（英寸）
    "data_min": null,                 // y轴最小值（null=自动）
    "data_max": null,                 // y轴最大值（null=自动）
    "time_min": 0.0,                  // x轴起始时间（秒）
    "time_max": null,                 // x轴结束时间（null=自动）
    "output_style": "both",           // 输出样式：scatter/line/both
    "input_color": "#1f77b4",         // 输入数据颜色（蓝色）
    "output_color": "#ff7f0e",        // 输出数据颜色（橙色）
    "enable_cursor": true,            // 启用鼠标交互
    "dpi": 300,                       // 图片分辨率
    "output_filename": "freq_comparison_result.png"  // 输出图片文件名（相对路径相对于配置文件所在目录）
  },

  // 输出选项
  "save_static": true,                // 保存静态图片
  "show_interactive": true            // 显示交互式窗口
}
```

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

## 时间对齐算法

工具会自动对齐输入输出数据的时间轴：

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

## 交互功能

打开交互式窗口后，鼠标移动时会显示：
- 当前时间（秒，精确到3位小数）
- 输入频率值（如果鼠标靠近输入线）
- 输出频率值（如果鼠标靠近输出点）

示例：

```
Time: 2.456s
Input: 49.920 Hz
Output: 49.918 Hz
```

## 模块说明

### measure_data_parser.py

数据解析模块，负责：
- 解析两种CSV格式
- 统一时间戳为相对毫秒数
- 处理BOM字符、不同日期格式

### measure_data_alignment.py

时间对齐模块，负责：
- 检测首个显著变化点
- 计算时间偏移
- 平移输出数据时间轴

### measure_plotter_core.py

绘图核心模块，负责：
- 阶梯图绘制（输入数据）
- 点图/折线图绘制（输出数据）
- 鼠标交互实现
- 时间轴精确配置（100ms可分辨）

### measure_plotter.py

主程序入口，负责：
- 加载配置文件
- 协调各模块工作流
- 命令行接口
- 日志输出

## 测试各模块

每个模块都包含测试代码，可单独运行：

```bash
# 测试数据解析模块
cd measure_comparison_plot
python measure_data_parser.py

# 测试时间对齐模块
python measure_data_alignment.py

# 测试绘图核心模块
python measure_plotter_core.py
```

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

## 许可证

本工具为PMU测试项目内部使用工具。

## 版本历史

- **v1.0** (2025-12-09): 初始版本
  - 支持两种CSV格式解析
  - 自动时间对齐
  - 阶梯图 + 点线图对比
  - 鼠标交互功能

## 联系方式

如有问题或建议，请联系项目维护者。
