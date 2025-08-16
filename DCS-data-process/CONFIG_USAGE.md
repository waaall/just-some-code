# HIS文件批量CSV导出使用说明

## 步骤1：首次运行

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

| 参数名            | 类型   | 描述                 | 示例值                         |
| ----------------- | ------ | -------------------- | ------------------------------ |
| `data_dir`      | string | HIS数据文件目录      | `"./his-data"`               |
| `output_dir`    | string | CSV输出目录          | `"./csv-output"`             |
| `target_points` | array  | 数据点列表(最多20个) | `["SYS_XCU001_Memory"]`      |
| `days`          | number | 处理天数(1-31)       | `1`                          |
| `start_date`    | string | 开始日期(YYYYMMDD)   | `"20250702"`                 |
| `max_workers`   | number | 文件级线程数(1-4)    | `4`                          |
| `point_threads` | number | 数据点级线程数(1-4)  | `4`                          |
| `csv_format`    | string | CSV格式              | `"detailed"` 或 `"simple"` |

## 常见配置示例

### 示例

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
