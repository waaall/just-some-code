# HIS文件批量CSV导出器 - 简化使用说明

## 概述

**最新版本(v2.0)**：完全自动化，只需一个配置文件，零命令行参数！

## 🚀 超简单使用方法

### 步骤1：首次运行
```bash
python batch_his_files_to_csv.py
```

程序会自动：
- 检测到没有配置文件
- 自动生成 `his_config.json` 配置文件模板
- 提示您编辑配置文件
- 退出程序

### 步骤2：编辑配置文件

编辑自动生成的 `his_config.json`：

```json
{
    "data_dir": "./his-data",
    "output_dir": "./csv-output",
    "target_points": [
        "SYS_XCU001_Memory",
        "20MCS-UNITMW"
    ],
    "days": 1,
    "start_date": "20250702",
    "max_workers": 4,
    "point_threads": 4,
    "csv_format": "detailed"
}
```

### 步骤3：再次运行
```bash
python batch_his_files_to_csv.py
```

程序会自动：
- 加载配置文件
- 验证参数
- 开始批量处理
- 输出CSV文件

## 配置参数说明

| 参数名 | 类型 | 描述 | 示例值 |
|--------|------|------|--------|
| `data_dir` | string | HIS数据文件目录 | `"./his-data"` |
| `output_dir` | string | CSV输出目录 | `"./csv-output"` |
| `target_points` | array | 数据点列表(最多10个) | `["SYS_XCU001_Memory"]` |
| `days` | number | 处理天数(1-7) | `1` |
| `start_date` | string | 开始日期(YYYYMMDD) | `"20250702"` |
| `max_workers` | number | 文件级线程数(1-4) | `4` |
| `point_threads` | number | 数据点级线程数(1-4) | `4` |
| `csv_format` | string | CSV格式 | `"detailed"` 或 `"simple"` |

## 常见配置示例

### 示例1：单点快速分析
```json
{
    "data_dir": "./his-data",
    "output_dir": "./quick-analysis",
    "target_points": ["20MCS-UNITMW"],
    "days": 1,
    "start_date": "20250702",
    "max_workers": 2,
    "point_threads": 2,
    "csv_format": "simple"
}
```

### 示例2：多点一周数据
```json
{
    "data_dir": "./his-data",
    "output_dir": "./weekly-report",
    "target_points": [
        "SYS_XCU001_Memory",
        "SYS_XCU001_CPULoad", 
        "20MCS-UNITMW"
    ],
    "days": 7,
    "start_date": "20250701",
    "max_workers": 4,
    "point_threads": 4,
    "csv_format": "detailed"
}
```

### 示例3：高性能处理
```json
{
    "data_dir": "./his-data",
    "output_dir": "./batch-output",
    "target_points": [
        "SYS_XCU001_Memory",
        "SYS_XCU002_Memory",
        "SYS_XCU003_Memory",
        "SYS_XCU004_Memory",
        "SYS_XCU005_Memory"
    ],
    "days": 3,
    "start_date": "20250702",
    "max_workers": 4,
    "point_threads": 4,
    "csv_format": "simple"
}
```

## ✨ 新版本优势

1. **零学习成本**：不需要记住任何命令行参数
2. **自动化体验**：首次运行自动生成配置模板
3. **配置验证**：启动时自动验证所有参数
4. **错误提示**：清晰的错误信息和修复建议
5. **一键运行**：编辑配置后直接运行

## 错误处理

### 数据目录不存在
```
[ERROR] 数据目录不存在: ./his-data
[HINT] 请在配置文件中设置正确的 data_dir 路径
```

### 未配置数据点
```
[ERROR] 未配置数据点
[HINT] 请在配置文件的 target_points 中设置要导出的数据点列表
```

### JSON格式错误
```
[ERROR] 配置文件 his_config.json 格式错误
[HINT] 请检查JSON格式是否正确
```

## 迁移指南

如果您之前使用带命令行参数的版本，只需：

1. 运行一次新版本生成配置文件模板
2. 将之前的参数填入配置文件
3. 以后只需运行 `python batch_his_files_to_csv.py`

## 技术特性

- **智能配置管理**：自动检测、生成、验证配置文件
- **高性能处理**：多线程并发处理大文件
- **内存优化**：批次处理避免内存溢出
- **详细日志**：完整的处理日志和统计信息
- **容错设计**：完善的错误处理和提示机制
