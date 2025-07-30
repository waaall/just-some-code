# DCS数据处理工具集

电厂DCS传感器数据的HIS/IDX文件解析与ClickHouse数据库导入工具。

## 项目概述

本项目提供完整的电力控制系统(DCS)历史数据处理方案，包括HIS/IDX文件格式逆向解析、数据提取与数据库导入功能。


## 数据流程

```
HIS/IDX文件 → 解析器 → 数据提取 → Excel导出/数据库导入
     ↓           ↓         ↓            ↓
  原始数据    索引解析   时序数据    ClickHouse存储
```

## 核心文件

### 数据解析模块


- **` analys_idx_file.py`** - IDX文件结构深度分析器

- 详细解析IDX文件头部、数据点定义、时间索引
- 生成完整的文件结构报告
- 支持TXT和Excel格式输出

- **`parse_his_data.py`** - HIS历史数据文件解析器(核心基础类)

  - 解析IDX索引文件获取数据点定义和时间索引
  - 解析HIS文件提取压缩时序数据
  - 支持Excel格式数据导出
  - 提供单点或批量数据处理


### 数据库集成模块

- **`his_to_clickhouse.py`** - ClickHouse数据库导入器

  - 继承HIS解析功能，直接导入数据库
  - 支持VALUES和CSV两种批量插入方式
  - 提供命令行接口和进度监控
  - 支持指定数据点或批量处理
- **`clickhouse_db_inspector.py`** - ClickHouse数据库结构检查器

  - 分析数据库、表结构、字段类型
  - 检查数据分区、索引和存储统计
  - 生成CSV格式的结构报告


## 快速使用

```bash
# 分析IDX文件结构
python analys_idx_file.py --file 2025070222.idx

# 解析数据并导出Excel
python parse_his_data.py --file 2025070222 --point SYS_XCU001_Memory


# 检查数据库结构
python clickhouse_db_inspector.py --host 127.0.0.1

# 导入ClickHouse数据库  
python his_to_clickhouse.py --points "point1,point2" --method values
```

