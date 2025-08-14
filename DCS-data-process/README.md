# DCS数据处理工具集

电厂DCS传感器数据的HIS/IDX文件解析与ClickHouse数据库导入工具。

## 项目概述

本项目提供完整的电力控制系统(DCS)历史数据处理方案，包括HIS/IDX文件格式逆向解析、数据提取与数据库导入功能。

## 环境要求

### Python版本

- Python 3.7+

### 第三方依赖库

```bash
# 方式1: 使用requirements.txt一键安装
pip install -r requirements.txt

# 方式2: 手动安装核心依赖
pip install requests pandas numpy openpyxl
```

**核心依赖说明:**

- `requests` - HTTP请求库，用于ClickHouse数据库连接
- `pandas` - 数据分析库，用于Excel文件生成和数据处理
- `numpy` - 科学计算库，用于数值数据处理
- `openpyxl` - Excel文件读写引擎，支持xlsx格式

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

### 批量处理模块

- **`batch_his_files_to_ck.py`** - HIS文件批量处理器
  - 自动发现目录下所有HIS/IDX文件对
  - 支持指定特定文件和数据点进行处理
  - **双重多线程架构**: 文件级别+数据点级别并行处理
  - 完整的日志记录和进度监控
  - 支持失败重试和错误处理
  - 线程安全的状态管理和输出控制

## 多线程性能优化

### 双重并行架构

本项目采用创新的双重多线程架构，提供两个层次的并行处理：

1. **文件级多线程** (`--threads`参数)

   - 多个HIS文件同时处理
   - 适用场景：大量文件批处理
   - 推荐值：4个线程
   - 性能提升：文件数量 × 线程数
2. **数据点级多线程** (`--point-threads`参数)

   - 单个文件内多个数据点同时解析
   - 适用场景：大文件数据点处理
   - 推荐值：2-4个线程
   - 性能提升：数据点数量 × 线程数

### 多线程建议

- **小规模数据**: 使用单线程模式 (`--threads 1`)
- **大量文件**: 使用文件级多线程 (`--threads 4`)
- **大文件处理**: 使用数据点级多线程 (`--point-threads 2`)
- **最佳性能**: 双重多线程 (`--threads 4 --point-threads 2`)

## 快速使用

### 基础功能

```bash
# 分析IDX文件结构
python analys_idx_file.py --file 2025070222.idx

# 解析数据并导出Excel
python parse_his_data.py --file 2025070222 --point SYS_XCU001_Memory

# 检查数据库结构
python clickhouse_db_inspector.py --host 192.168.50.30

# 单文件导入ClickHouse数据库  
python his_to_clickhouse.py --points "point1,point2" --method values
```

### 批量处理 - 单线程模式

```bash
# 批量处理多个HIS文件 (单线程，默认)
python batch_his_files_to_ck.py --dir ./his-data --method values

# 列出所有可用文件
python batch_his_files_to_ck.py --listfiles

# 处理指定文件
python batch_his_files_to_ck.py --files 2025070222 2025070221

# 处理指定数据点
python batch_his_files_to_ck.py --points "SYS_XCU001_Memory,SYS_XCU101_AN_OFF"

# 处理指定文件的指定数据点
python batch_his_files_to_ck.py --files 2025070222 --points "point1,point2"
```

### 批量处理 - 多线程模式 🚀

```bash
# 文件级多线程 (4个线程并行处理文件)
python batch_his_files_to_ck.py --threads 4

# 数据点级多线程 (单文件内2个线程处理数据点)
python batch_his_files_to_ck.py --point-threads 2

# 双重多线程 (最佳性能，推荐配置)
python batch_his_files_to_ck.py --threads 4 --point-threads 2

# 指定文件 + 指定数据点 + 双重多线程
python batch_his_files_to_ck.py --files 2025070222 --points "SYS_XCU001_Memory,SYS_XCU001_CPULoad" --threads 2 --point-threads 2

# 大规模批处理 (推荐生产环境配置)
python batch_his_files_to_ck.py --dir /data/his --threads 4 --point-threads 2 --method values --retry 2
```

### 性能对比示例

```bash
# 单线程模式 (基准性能)
python batch_his_files_to_ck.py --files 2025070222 --points "point1,point2"
# 预期：处理速度 10K-20K 记录/秒

# 双重多线程模式 (优化性能)  
python batch_his_files_to_ck.py --files 2025070222 --points "point1,point2" --threads 2 --point-threads 2
# 预期：处理速度 30K-40K 记录/秒，提升 2-3倍
```

## 技术架构详解

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                   DCS数据处理系统                          │
├─────────────────────────────────────────────────────────────┤
│  批量处理器 (batch_his_files_to_ck.py)                     │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  文件级线程池   │  │  文件级线程池   │  ...             │
│  │  Thread 1       │  │  Thread 2       │                  │
│  └─────────────────┘  └─────────────────┘                  │
│         │                      │                           │
│         ▼                      ▼                           │
│  ┌─────────────────────────────────────────────────────────┤
│  │  单文件处理器 (his_to_clickhouse.py)                    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  │ 数据点线程1 │  │ 数据点线程2 │  │ 数据点线程3 │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │
│  └─────────────────────────────────────────────────────────┤
│         │                      │                      │    │
│         ▼                      ▼                      ▼    │
├─────────────────────────────────────────────────────────────┤
│  数据解析层 (parse_his_data.py)                            │
│  - IDX文件解析    - HIS文件解析    - 数据类型转换           │
├─────────────────────────────────────────────────────────────┤
│  数据库层 (ClickHouse)                                      │
│  - 连接池管理     - 批量插入       - 事务处理               │
└─────────────────────────────────────────────────────────────┘
```

### 性能基准测试

**测试环境:**

- CPU: Intel/Apple Silicon (4核心)
- 内存: 8GB+
- 存储: SSD
- 网络: 千兆局域网

**测试数据:**

- 文件大小: 52.3MB HIS文件
- 数据点数量: 2-4个数据点
- 记录数量: 3,600条/数据点

**性能结果:**

| 配置模式     | 线程配置                          | 处理时间 | 处理速度       | 性能提升 |
| ------------ | --------------------------------- | -------- | -------------- | -------- |
| 单线程       | `--threads 1`                   | 0.4秒    | 18,688 记录/秒 | 基准     |
| 数据点多线程 | `--point-threads 2`             | 0.2秒    | 36,000 记录/秒 | 1.9x     |
| 双重多线程   | `--threads 2 --point-threads 2` | 0.2秒    | 38,217 记录/秒 | 2.0x     |

### 配置建议

**开发环境:**

```bash
# 单线程模式，便于调试
python batch_his_files_to_ck.py --threads 1 --point-threads 1
```

**测试环境:**

```bash
# 中等并发，平衡性能和资源
python batch_his_files_to_ck.py --threads 2 --point-threads 2
```

**生产环境:**

```bash
# 高并发，最大化性能
python batch_his_files_to_ck.py --threads 4 --point-threads 4 --retry 2
```

## 开发指南

### 注意事项

request 用 `http://host:port/` ；sql语句查 `database.table` 才能查到正确的数据；

而不是request用 `http://host:port/database` ；sql语句查 `table`。


### 代码结构

```
DCS-data-process/
├── batch_his_files_to_ck.py    # 批量处理器 (双重多线程)
├── his_to_clickhouse.py        # 单文件处理器 (数据点多线程)
├── parse_his_data.py           # 数据解析基础类
├── analys_idx_file.py          # IDX文件分析器
├── clickhouse_db_inspector.py  # 数据库结构检查器
└── README.md                   # 项目文档
```
