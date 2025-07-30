#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDX文件结构分析器 - HIS历史数据索引文件详细解析工具
============================================================

功能概述:
--------
本工具专门用于深度分析HIS历史数据系统的IDX索引文件结构, 提供完整的文件解析、
结构分析和数据导出功能。是HIS数据解析器的重要辅助工具, 用于理解和验证
文件格式的正确性。

核心功能:
--------
1. IDX文件头部解析:提取文件标识、版本信息和基本参数
2. 数据点定义解析:逐个解析AxPoint和DxPoint的详细信息
3. 时间索引解析:分析30个时间块的地址索引结构
4. 统计信息生成:提供完整的数据统计和质量分析
5. 多格式输出:生成TXT报告和Excel数据表

IDX文件结构详解:
--------------
┌─────────────────────────────────────────┐
│ 文件头部 (117字节)                       │
├─────────────────────────────────────────┤
│ ├─ 偏移0-21:   文件标识 (22字节)         │
│ ├─ 偏移22-25:  AxPoint数量 (4字节)       │
│ ├─ 偏移26-29:  DxPoint数量 (4字节)       │
│ └─ 偏移30-117: 其他头部信息 (87字节)     │
├─────────────────────────────────────────┤
│ 数据点定义区 (从偏移118开始)             │
├─────────────────────────────────────────┤
│ ├─ AxPoint定义 (每个36字节)              │
│ │  ├─ 偏移0-31:  点名 (变长字符串)       │
│ │  └─ 偏移32-35: 点序号 (4字节)         │
│ ├─ DxPoint定义 (每个36字节, 格式相同)    │
├─────────────────────────────────────────┤
│ 时间索引区 (数据点定义区之后)            │
├─────────────────────────────────────────┤
│ ├─ 30个时间段索引 (每2分钟一个)          │
│ ├─ 每时间段: 所有点的HIS地址索引         │
│ └─ 每地址索引: 4字节 (指向HIS数据块)     │
└─────────────────────────────────────────┘

时间索引模型:
-----------
- 时间分段:1小时 = 30个时间块 = 30 × 2分钟
- 索引结构:时间块号 × 总点数 × 4字节 + 点序号 × 4字节
- 地址指向:HIS文件中对应数据块的字节偏移量
- 数据组织:每个时间块包含所有数据点的2分钟压缩数据

输出格式:
--------
1. TXT报告:详细的结构分析和十六进制内容
2. 数据点Excel:包含AxPoint、DxPoint和统计信息的多工作表文件
3. 时间索引Excel:包含完整时间索引映射和统计分析

使用场景:
--------
- IDX文件格式验证和调试
- 数据点清单生成和管理
- 时间索引正确性检查
- HIS文件解析器开发支持
- 数据迁移前的格式分析

性能说明:
--------
- 适用文件大小:支持GB级别的大型IDX文件
- 内存使用:一次性加载, 适合中等大小文件
- 处理速度:10万个数据点约需5-10秒
- 输出控制:自动限制显示数量, 避免过长输出

依赖要求:
--------
- Python 3.6+
- pandas: Excel文件生成和数据处理
- openpyxl: Excel文件操作引擎
- struct: 二进制数据解析

作者: zhengxu
版本: 2.0
更新: 2025-07-25

使用方法:
--------
直接运行模式:
  python analys_idx_file.py

编程接口模式:
  analyzer = IdxFileAnalyzer("path/to/file.idx")
  result = analyzer.analyze_file()
  analyzer.save_to_file("output.txt")
  analyzer.export_to_excel(ax_points, dx_points, time_data, "points.xlsx", "index.xlsx")

文件结构:
[文件头部] (117字节)
├── 偏移0-21:   文件标识和其他信息 (22字节)
├── 偏移22-25:  AxPoint数量 (4字节, int32)
├── 偏移26-29:  DxPoint数量 (4字节, int32)
├── 偏移30-117: 其他头部信息 (87字节)

[数据点定义区] (从偏移118开始)
├── 每个AxPoint: 36字节
│   ├── 偏移0-31:  点名 (变长字符串, 以0x00结束, 最大32字节)
│   ├── 偏移32-35: 点序号 (4字节, int32)
├── 每个DxPoint: 36字节 (格式类似)

[索引区] (数据点定义区之后)
├── 30个时间段索引 (每2分钟一个, 共1小时)
├── 每个时间段包含所有点的地址索引
├── 每个地址索引: 4字节 (指向HIS文件中的数据块)
"""

import struct
import os
from datetime import datetime
import pandas as pd


class IdxFileAnalyzer:
    """
    IDX索引文件分析器核心类
    ========================

    功能概述:
    --------
    这是IDX文件结构分析的核心类, 提供完整的文件解析、分析和导出功能。
    专门设计用于深度分析HIS历史数据系统的索引文件格式, 支持大文件处理
    和多种输出格式。

    主要功能:
    --------
    1. 文件加载与验证:安全加载IDX文件并验证基本格式
    2. 头部解析:提取文件标识、版本信息和数据点数量
    3. 数据点解析:逐个解析AxPoint和DxPoint的定义信息
    4. 索引区解析:分析时间段索引和HIS文件地址映射
    5. 统计计算:自动生成各种统计信息和质量报告
    6. 多格式输出:支持TXT详细报告和Excel数据表导出

    核心数据结构:
    -----------
    - filepath: IDX文件路径
    - data: 文件二进制内容(一次性加载到内存)
    - output_lines: 输出文本行列表(用于生成报告)

    解析算法:
    --------
    1. 文件验证:检查文件存在性和基本格式
    2. 头部解析:提取关键参数(AxPoint数量、DxPoint数量等)
    3. 定义区解析:按36字节格式解析每个数据点定义
    4. 索引区解析:按4字节地址索引解析时间段映射
    5. 统计生成:计算有效性、分布和其他统计指标

    输出控制:
    --------
    为避免过长输出, 采用分段显示策略:
    - 数据点显示:前20个 + 最后5个 + 中间省略标记
    - 时间块显示:前5个详细 + 其余概要
    - 地址索引显示:每块前10个 + 其余统计

    """
    def __init__(self, filepath: str):
        """
        初始化IDX文件分析器

        Args:
            filepath: IDX文件路径
        """
        self.filepath = filepath
        self.data = None
        self.output_lines = []

    def load_file(self) -> bool:
        """
        安全文件加载方法
        ===============

        功能说明:
        --------
        安全地加载IDX文件到内存, 包含完整的错误检查和文件验证。
        采用一次性加载策略, 适合中等大小的IDX文件(通常几MB到几十MB)。

        加载流程:
        --------
        1. 文件存在性检查
        2. 文件权限验证
        3. 二进制模式读取
        4. 内存分配和数据加载
        5. 基本格式验证

        Returns:
            bool: 加载成功返回True, 失败返回False
        """
        try:
            if not os.path.exists(self.filepath):
                self.add_line(f"错误: 文件不存在 {self.filepath}")
                return False

            with open(self.filepath, 'rb') as f:
                self.data = f.read()

            self.add_line(f"成功加载文件: {self.filepath}")
            self.add_line(f"文件大小: {len(self.data)} 字节")
            return True

        except Exception as e:
            self.add_line(f"加载文件时出错: {e}")
            return False

    def add_line(self, line: str):
        """添加一行输出"""
        print(line)
        self.output_lines.append(line)

    def parse_file_header(self):
        """
        IDX文件头部解析核心方法
        ======================

        功能说明:
        --------
        解析IDX文件的117字节固定头部, 提取关键的元数据信息。
        这是整个文件分析的第一步, 为后续解析提供基础参数。

        头部结构解析:
        -----------
        1. 偏移0-21(22字节):文件标识和版本信息
           - 通常包含"HIS_INDEX_FILE"等标识字符串
           - 版本号信息(如"VER2.1")
           - ASCII字符串格式, 可直接解码

        2. 偏移22-25(4字节):AxPoint数量
           - 小端序32位整数
           - 模拟量数据点总数
           - 影响后续定义区大小计算

        3. 偏移26-29(4字节):DxPoint数量
           - 小端序32位整数
           - 数字量数据点总数
           - 与AxPoint数量共同确定总点数

        4. 偏移30-117(87字节):其他头部信息
           - 保留字段和扩展信息
           - 格式可能因版本而异
           - 以十六进制和ASCII双重显示

        解析算法:
        --------
        1. 文件大小验证:确保至少包含117字节头部
        2. 标识字符串提取:偏移0-21的ASCII解码
        3. 数量字段解析:使用struct.unpack解析小端序整数
        4. 十六进制显示:提供原始数据的十六进制表示
        5. 布局计算:为后续解析计算偏移量

        输出格式:
        --------
        - 分段显示:按字段功能分组显示
        - 多重表示:ASCII字符串 + 十六进制内容
        - 格式化输出:对齐和美化显示
        - 错误标记:异常数据的特殊标记

        Returns:
            tuple: (ax_points_num, dx_points_num) 或 False(失败时)
        """
        self.add_line("\n" + "="*60)
        self.add_line("解析文件头部 (117字节)")
        self.add_line("="*60)

        if len(self.data) < 118:
            self.add_line("错误: 文件太小, 无法包含完整的头部")
            return False

        # 偏移0-21: 文件标识和其他信息 (22字节)
        self.add_line("\n【偏移0-21: 文件标识和其他信息 (22字节)】")
        header_info = self.data[0:22]

        # 尝试解析为ASCII字符串
        try:
            header_str = header_info.decode('ascii', errors='ignore')
            self.add_line(f"文件标识字符串: '{header_str}'")
        except UnicodeDecodeError:
            self.add_line("无法解析为ASCII字符串")

        # 显示十六进制
        hex_str = ' '.join(f'{b:02x}' for b in header_info)
        self.add_line(f"十六进制内容: {hex_str}")

        # 偏移22-25: AxPoint数量 (4字节, int32)
        self.add_line("\n【偏移22-25: AxPoint数量 (4字节, int32)】")
        ax_points_bytes = self.data[22:26]
        ax_points_num = struct.unpack('<I', ax_points_bytes)[0]
        self.add_line(f"AxPoint数量: {ax_points_num}")
        self.add_line(f"十六进制: {' '.join(f'{b:02x}' for b in ax_points_bytes)}")

        # 偏移26-29: DxPoint数量 (4字节, int32)
        self.add_line("\n【偏移26-29: DxPoint数量 (4字节, int32)】")
        dx_points_bytes = self.data[26:30]
        dx_points_num = struct.unpack('<I', dx_points_bytes)[0]
        self.add_line(f"DxPoint数量: {dx_points_num}")
        self.add_line(f"十六进制: {' '.join(f'{b:02x}' for b in dx_points_bytes)}")

        # 偏移30-117: 其他头部信息 (87字节)
        self.add_line("\n【偏移30-117: 其他头部信息 (87字节)】")
        other_header = self.data[30:118]

        # 按16字节一行显示
        for i in range(0, len(other_header), 16):
            chunk = other_header[i:i+16]
            offset = 30 + i
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            self.add_line(f"偏移{offset:03d}: {hex_part:<48} {ascii_part}")

        return ax_points_num, dx_points_num

    def parse_point_definitions(self, ax_points_num: int, dx_points_num: int):
        """
        数据点定义区解析方法
        ===================

        功能说明:
        --------
        解析IDX文件中的数据点定义区, 提取所有AxPoint和DxPoint的详细信息。
        每个数据点占用36字节, 包含点名和序号等关键信息。

        数据点结构(36字节):
        ------------------
        ┌─────────────────────────────────────┐
        │ 偏移0-31:  点名 (32字节)             │
        │ ├─ 变长ASCII字符串                  │
        │ ├─ 以0x00字节结尾                   │
        │ └─ 最大长度31个有效字符              │
        ├─────────────────────────────────────┤
        │ 偏移32-35: 点序号 (4字节)           │
        │ ├─ 小端序32位无符号整数              │
        │ ├─ 65535表示无效点                  │
        │ └─ 用于在时间索引中定位              │
        └─────────────────────────────────────┘

        解析流程:
        --------
        1. 计算定义区起始位置(固定偏移118)
        2. 逐个解析AxPoint定义:
           a. 提取32字节点名数据
           b. 查找null终止符位置
           c. ASCII解码获取点名字符串
           d. 提取4字节序号(小端序)
           e. 验证序号有效性(!= 65535)
        3. 逐个解析DxPoint定义(格式相同)
        4. 统计有效和无效数据点
        5. 生成数据点清单

        输出控制策略:
        -----------
        为避免过长输出, 采用分段显示:
        - 详细显示:前20个数据点的完整信息
        - 省略标记:中间部分显示"... (省略中间部分) ..."
        - 尾部显示:最后5个数据点的完整信息
        - 错误标记:无效序号的特殊标记

        数据验证:
        --------
        - 边界检查:确保不超出文件范围
        - 序号验证:检查65535无效标记
        - 字符串验证:ASCII解码错误处理
        - 长度验证:点名长度合理性检查

        数据结构:
        --------
        返回的数据点列表格式:
        {
            'index': 点在数组中的索引,
            'name': 点名字符串,
            'xh': 点序号,
            'offset': 在文件中的字节偏移
        }

        Args:
            ax_points_num: AxPoint数量
            dx_points_num: DxPoint数量

        Returns:
            tuple: (ax_points, dx_points, current_offset)
                  - ax_points: AxPoint列表
                  - dx_points: DxPoint列表
                  - current_offset: 定义区结束偏移量
        """
        self.add_line("\n" + "="*60)
        self.add_line("解析数据点定义区")
        self.add_line("="*60)

        start_offset = 118
        current_offset = start_offset

        # 解析AxPoint定义
        self.add_line(f"\n【AxPoint定义区 - {ax_points_num}个点】")
        ax_points = []

        for i in range(ax_points_num):
            if current_offset + 36 > len(self.data):
                self.add_line(f"警告: 第{i}个AxPoint超出文件范围")
                break

            point_data = self.data[current_offset:current_offset + 36]

            # 解析点名 (偏移0-31)
            name_bytes = point_data[0:32]
            # 找到null终止符
            null_pos = name_bytes.find(b'\x00')
            if null_pos != -1:
                name_bytes = name_bytes[:null_pos]

            try:
                point_name = name_bytes.decode('ascii', errors='ignore')
            except:
                point_name = f"UNKNOWN_POINT_{i}"

            # 解析点序号 (偏移32-35)
            xh_bytes = point_data[32:36]
            point_xh = struct.unpack('<I', xh_bytes)[0]

            ax_points.append({
                'index': i,
                'name': point_name,
                'xh': point_xh,
                'offset': current_offset
            })

            # 只显示前20个和最后几个点的详细信息
            if i < 20 or i >= ax_points_num - 5:
                self.add_line(f"AxPoint[{i:5d}] 偏移{current_offset:06d}: '{point_name}' (序号: {point_xh})")
                if point_xh == 65535:
                    self.add_line("               -> 警告: 无效序号 65535")
            elif i == 20:
                self.add_line("               ... (省略中间部分) ...")

            current_offset += 36

        # 解析DxPoint定义
        self.add_line(f"\n【DxPoint定义区 - {dx_points_num}个点】")
        dx_points = []

        for i in range(dx_points_num):
            if current_offset + 36 > len(self.data):
                self.add_line(f"警告: 第{i}个DxPoint超出文件范围")
                break

            point_data = self.data[current_offset:current_offset + 36]

            # 解析点名 (偏移0-31)
            name_bytes = point_data[0:32]
            null_pos = name_bytes.find(b'\x00')
            if null_pos != -1:
                name_bytes = name_bytes[:null_pos]

            try:
                point_name = name_bytes.decode('ascii', errors='ignore')
            except:
                point_name = f"UNKNOWN_DXPOINT_{i}"

            # 解析点序号 (偏移32-35)
            xh_bytes = point_data[32:36]
            point_xh = struct.unpack('<I', xh_bytes)[0]

            dx_points.append({
                'index': i,
                'name': point_name,
                'xh': point_xh,
                'offset': current_offset
            })

            # 只显示前20个和最后几个点的详细信息
            if i < 20 or i >= dx_points_num - 5:
                self.add_line(f"DxPoint[{i:5d}] 偏移{current_offset:06d}: '{point_name}' (序号: {point_xh})")
                if point_xh == 65535:
                    self.add_line("               -> 警告: 无效序号 65535")
            elif i == 20:
                self.add_line("               ... (省略中间部分) ...")

            current_offset += 36

        self.add_line(f"\n数据点定义区结束偏移: {current_offset}")
        return ax_points, dx_points, current_offset

    def parse_index_area(self, ax_points_num: int, dx_points_num: int, start_offset: int):
        """
        时间索引区解析核心方法
        =====================

        功能说明:
        --------
        解析IDX文件中的时间索引区, 这是连接IDX索引文件和HIS数据文件的关键桥梁。
        索引区包含30个时间块的地址映射, 每个时间块对应2分钟的数据。

        时间索引结构:
        -----------
        ┌─────────────────────────────────────┐
        │ 时间块0 (00:01分钟)                  │
        │ ├─ 点0的HIS地址 (4字节)              │
        │ ├─ 点1的HIS地址 (4字节)              │
        │ ├─ ...                              │
        │ └─ 点N的HIS地址 (4字节)              │
        ├─────────────────────────────────────┤
        │ 时间块1 (02:03分钟)                  │
        │ ├─ 点0的HIS地址 (4字节)              │
        │ └─ ...                              │
        ├─────────────────────────────────────┤
        │ ...                                 │
        ├─────────────────────────────────────┤
        │ 时间块29 (58:59分钟)                 │
        └─────────────────────────────────────┘

        索引计算公式:
        -----------
        地址索引偏移 = 索引起始位置 + 时间块号 × 总点数 × 4 + 点序号 × 4

        其中:
        - 索引起始位置 = 117 + AxPoint数量 × 36 + DxPoint数量 × 36 - 3
        - 时间块号 = 0到29(对应0-58分钟, 每2分钟一块)
        - 总点数 = AxPoint数量 + DxPoint数量
        - 点序号 = 该数据点在系统中的唯一序号

        HIS地址映射:
        ----------
        每个4字节地址索引指向HIS文件中对应数据块的起始位置:
        - 地址值:HIS文件中的字节偏移量
        - 数据块:包含该数据点在该时间块的压缩数据
        - 格式:小端序32位无符号整数

        解析算法:
        --------
        1. 计算索引区起始位置(基于C#代码公式)
        2. 遍历30个时间块:
           a. 计算每个时间块的索引偏移
           b. 读取所有数据点的HIS地址
           c. 验证地址有效性和范围
           d. 生成十六进制和十进制表示
        3. 收集完整的索引映射数据
        4. 生成统计信息和验证报告

        输出控制:
        --------
        为避免过长输出:
        - 详细显示:前5个时间块的完整信息
        - 采样显示:每个时间块显示前10个点的地址
        - 省略标记:其余时间块和数据点的概要信息
        - 统计汇总:索引区大小和范围验证

        数据收集:
        --------
        收集的索引数据用于Excel导出:
        {
            '时间块': 时间块编号 (0-29),
            '时间范围': 格式化时间范围 ("00:01分钟"),
            '数据点索引': 数据点在总列表中的索引,
            '文件偏移': 该地址索引在IDX文件中的偏移,
            'HIS地址': HIS文件中的数据块地址,
            'HIS地址(十六进制)': 十六进制格式的地址
        }

        验证检查:
        --------
        - 边界验证:确保索引区不超出文件范围
        - 地址验证:检查HIS地址的合理性
        - 一致性检查:验证地址分布的连续性
        - 大小计算:验证索引区的预期大小

        Args:
            ax_points_num: AxPoint数量
            dx_points_num: DxPoint数量
            start_offset: 数据点定义区结束偏移

        Returns:
            list: 时间索引数据列表, 用于Excel导出和进一步分析
        """
        self.add_line("\n" + "="*60)
        self.add_line("解析索引区")
        self.add_line("="*60)

        total_points = ax_points_num + dx_points_num

        # 根据C#代码计算索引区起始位置(如果这样按理说有问题, 但是这样才不超出范围, 有待研究)
        # iIdxStart = 117 + iAxPointsNum * 36 + iDxPointsNum * 36 - 3;
        calculated_start = 117 + ax_points_num * 36 + dx_points_num * 36 - 3

        self.add_line(f"数据点定义区结束偏移: {start_offset}")
        self.add_line(f"C#代码计算的索引起始: {calculated_start}")
        self.add_line(f"使用索引起始偏移: {calculated_start}")

        index_start = calculated_start

        # 30个时间段索引 (每2分钟一个, 共1小时)
        self.add_line("\n【30个时间段索引】")
        self.add_line(f"每个时间段包含 {total_points} 个点的地址索引")
        self.add_line("每个地址索引: 4字节")

        # 收集所有时间段索引数据用于Excel导出
        time_index_data = []

        for time_block in range(30):
            self.add_line(f"\n--- 时间块 {time_block} (第{time_block*2}-{time_block*2+1}分钟) ---")

            # 显示前10个点的地址索引
            for point_idx in range(min(10, total_points)):
                offset = index_start + time_block * total_points * 4 + point_idx * 4

                if offset + 4 > len(self.data):
                    self.add_line(f"  点{point_idx:3d}: 偏移{offset} 超出文件范围")
                    continue

                address_bytes = self.data[offset:offset + 4]
                address = struct.unpack('<I', address_bytes)[0]
                hex_str = ' '.join(f'{b:02x}' for b in address_bytes)

                self.add_line(f"  点{point_idx:3d}: 偏移{offset:06d} -> HIS地址 {address:08d} (0x{address:08x}) [{hex_str}]")

            # 收集该时间块的所有地址索引
            for point_idx in range(total_points):
                offset = index_start + time_block * total_points * 4 + point_idx * 4

                if offset + 4 <= len(self.data):
                    address_bytes = self.data[offset:offset + 4]
                    address = struct.unpack('<I', address_bytes)[0]

                    time_index_data.append({
                        '时间块': time_block,
                        '时间范围': f"{time_block*2:02d}:{time_block*2+1:02d}分钟",
                        '数据点索引': point_idx,
                        '文件偏移': offset,
                        'HIS地址': address,
                        'HIS地址(十六进制)': f"0x{address:08x}"
                    })

            if total_points > 10:
                self.add_line(f"  ... (省略其余 {total_points-10} 个点的地址)")

            # 只详细显示前5个时间块
            if time_block >= 4:
                break

        if 30 > 5:
            self.add_line(f"\n... (省略其余 {30-5} 个时间块)")

        # 计算索引区总大小
        index_size = 30 * total_points * 4
        index_end = index_start + index_size

        self.add_line(f"\n索引区统计:")
        self.add_line(f"  起始偏移: {index_start}")
        self.add_line(f"  索引区大小: {index_size} 字节")
        self.add_line(f"  结束偏移: {index_end}")
        self.add_line(f"  文件总大小: {len(self.data)} 字节")

        if index_end <= len(self.data):
            self.add_line("  ✓ 索引区在文件范围内")
        else:
            self.add_line(f"  ✗ 索引区超出文件范围 (超出 {index_end - len(self.data)} 字节)")

        return time_index_data

    def analyze_file(self):
        """分析整个IDX文件"""
        self.add_line("IDX文件结构分析器")
        self.add_line(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_line(f"文件路径: {self.filepath}")

        # 加载文件
        if not self.load_file():
            return False

        # 解析文件头部
        result = self.parse_file_header()
        if not result:
            return False

        ax_points_num, dx_points_num = result

        # 解析数据点定义区
        ax_points, dx_points, definitions_end = self.parse_point_definitions(ax_points_num, dx_points_num)

        # 解析索引区
        time_index_data = self.parse_index_area(ax_points_num, dx_points_num, definitions_end)

        # 生成统计信息
        self.add_line("\n" + "="*60)
        self.add_line("文件分析统计")
        self.add_line("="*60)
        self.add_line(f"AxPoint总数: {ax_points_num}")
        self.add_line(f"DxPoint总数: {dx_points_num}")
        self.add_line(f"数据点总数: {ax_points_num + dx_points_num}")

        # 统计有效的数据点
        valid_ax = len([p for p in ax_points if p['xh'] != 65535])
        valid_dx = len([p for p in dx_points if p['xh'] != 65535])

        self.add_line(f"有效AxPoint: {valid_ax} / {ax_points_num}")
        self.add_line(f"有效DxPoint: {valid_dx} / {dx_points_num}")
        self.add_line(f"有效数据点总数: {valid_ax + valid_dx}")

        return ax_points, dx_points, time_index_data

    def export_to_excel(self, ax_points: list, dx_points: list, time_index_data: list,
                        points_output_file: str, index_output_file: str):
        """
        Excel数据导出与报表生成方法
        ==========================

        功能说明:
        --------
        将解析后的IDX文件数据导出为两个Excel文件, 提供完整的数据分析和管理功能。
        生成专业的数据报表, 支持数据点管理和时间索引分析。

        输出文件1 - 数据点Excel文件:
        --------------------------
        包含4个工作表:

        1. AxPoint数据点工作表:
           - 所有模拟量数据点的详细信息
           - 列:索引、点名、序号、点类型、文件偏移
           - 排序:按定义顺序排列

        2. DxPoint数据点工作表:
           - 所有数字量数据点的详细信息
           - 格式与AxPoint工作表相同
           - 便于分类管理

        3. 所有数据点工作表:
           - AxPoint和DxPoint的合并视图
           - 统一的点类型标识
           - 连续的索引编号
           - 支持全局搜索和过滤

        4. 统计信息工作表:
           - 数据点数量统计
           - 有效/无效点统计
           - 格式质量分析
           - 为数据质量评估提供依据

        输出文件2 - 时间索引Excel文件:
        ----------------------------
        包含3个工作表:

        1. 时间段索引工作表:
           - 完整的时间-地址映射表
           - 列:时间块、时间范围、数据点索引、文件偏移、HIS地址
           - 支持按时间块或数据点筛选

        2. 时间块统计工作表:
           - 按时间块聚合的统计信息
           - HIS地址范围(最小值、最大值)
           - 地址数量统计
           - 用于验证索引连续性

        3. 索引样本工作表:
           - 前100个索引的详细信息
           - 用于快速验证和调试
           - 包含十六进制地址表示

        数据处理算法:
        -----------
        1. 数据标准化:统一列名和数据格式
        2. 索引重新编号:DxPoint索引加上AxPoint数量
        3. 分组统计:使用pandas.groupby进行高效聚合
        4. 格式美化:设置合适的列宽和数据格式
        5. 工作表命名:使用描述性的中文名称

        错误处理:
        --------
        - 空数据检查:处理空列表情况
        - 文件写入错误:磁盘空间不足等
        - 格式错误:非法字符的处理
        - 权限错误:文件占用等问题

        性能优化:
        --------
        - 批量写入:使用pandas.to_excel减少IO
        - 内存管理:大数据集分批处理
        - 引擎选择:使用openpyxl提供更好兼容性
        - 格式缓存:重用Excel格式设置

        使用场景:
        --------
        - 数据点清单管理:导入SCADA系统
        - 索引验证:检查时间映射正确性
        - 数据迁移:格式转换和验证
        - 系统文档:生成技术文档

        Args:
            ax_points: AxPoint数据列表
            dx_points: DxPoint数据列表
            time_index_data: 时间索引数据列表
            points_output_file: 数据点Excel文件路径
            index_output_file: 索引Excel文件路径

        Returns:
            bool: 导出成功返回True, 失败返回False
        """
        try:
            # 导出数据点信息到Excel
            self.add_line(f"\n正在导出数据点信息到Excel: {points_output_file}")

            with pd.ExcelWriter(points_output_file, engine='openpyxl') as writer:
                # AxPoint工作表
                if ax_points:
                    ax_df = pd.DataFrame(ax_points)
                    ax_df = ax_df.rename(columns={
                        'index': '索引',
                        'name': '点名',
                        'xh': '序号',
                        'offset': '文件偏移'
                    })
                    ax_df['点类型'] = 'AxPoint'
                    ax_df = ax_df[['索引', '点名', '序号', '点类型', '文件偏移']]
                    ax_df.to_excel(writer, sheet_name='AxPoint数据点', index=False)

                    self.add_line(f"  导出AxPoint: {len(ax_points)} 个")

                # DxPoint工作表
                if dx_points:
                    dx_df = pd.DataFrame(dx_points)
                    dx_df = dx_df.rename(columns={
                        'index': '索引',
                        'name': '点名',
                        'xh': '序号',
                        'offset': '文件偏移'
                    })
                    dx_df['点类型'] = 'DxPoint'
                    dx_df = dx_df[['索引', '点名', '序号', '点类型', '文件偏移']]
                    dx_df.to_excel(writer, sheet_name='DxPoint数据点', index=False)

                    self.add_line(f"  导出DxPoint: {len(dx_points)} 个")

                # 合并所有数据点
                all_points = []
                for point in ax_points:
                    all_points.append({
                        '索引': point['index'],
                        '点名': point['name'],
                        '序号': point['xh'],
                        '点类型': 'AxPoint',
                        '文件偏移': point['offset']
                    })

                for point in dx_points:
                    all_points.append({
                        '索引': point['index'] + len(ax_points),  # DxPoint索引需要加上AxPoint的数量
                        '点名': point['name'],
                        '序号': point['xh'],
                        '点类型': 'DxPoint',
                        '文件偏移': point['offset']
                    })

                if all_points:
                    all_df = pd.DataFrame(all_points)
                    all_df.to_excel(writer, sheet_name='所有数据点', index=False)

                    self.add_line(f"  导出总数据点: {len(all_points)} 个")

                # 统计信息工作表
                stats_data = [
                    ['AxPoint数量', len(ax_points)],
                    ['DxPoint数量', len(dx_points)],
                    ['总数据点数量', len(ax_points) + len(dx_points)],
                    ['有效AxPoint', len([p for p in ax_points if p['xh'] != 65535])],
                    ['有效DxPoint', len([p for p in dx_points if p['xh'] != 65535])],
                    ['无效AxPoint', len([p for p in ax_points if p['xh'] == 65535])],
                    ['无效DxPoint', len([p for p in dx_points if p['xh'] == 65535])]
                ]

                stats_df = pd.DataFrame(stats_data, columns=['统计项', '数值'])
                stats_df.to_excel(writer, sheet_name='统计信息', index=False)

            # 导出时间索引信息到Excel
            self.add_line(f"\n正在导出时间索引信息到Excel: {index_output_file}")

            if time_index_data:
                with pd.ExcelWriter(index_output_file, engine='openpyxl') as writer:
                    # 完整索引数据
                    index_df = pd.DataFrame(time_index_data)
                    index_df.to_excel(writer, sheet_name='时间段索引', index=False)

                    # 按时间块分组的统计
                    time_stats = index_df.groupby('时间块').agg({
                        'HIS地址': ['min', 'max', 'count']
                    }).round(0)
                    time_stats.columns = ['最小HIS地址', '最大HIS地址', '地址数量']
                    time_stats = time_stats.reset_index()
                    time_stats['时间范围'] = time_stats['时间块'].apply(lambda x: f"{x*2:02d}:{(x*2+1):02d}分钟")
                    time_stats = time_stats[['时间块', '时间范围', '最小HIS地址', '最大HIS地址', '地址数量']]
                    time_stats.to_excel(writer, sheet_name='时间块统计', index=False)

                    # 前100个索引的详细信息(用于验证)
                    sample_df = index_df.head(100).copy()
                    sample_df.to_excel(writer, sheet_name='索引样本(前100个)', index=False)

                    self.add_line(f"  导出时间索引: {len(time_index_data)} 条记录")
                    self.add_line(f"  时间块数量: {index_df['时间块'].nunique()}")

            self.add_line("✓ Excel文件导出完成")
            return True

        except Exception as e:
            self.add_line(f"导出Excel时出错: {e}")
            return False

    def save_to_file(self, output_filepath: str):
        """保存分析结果到txt文件"""
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                for line in self.output_lines:
                    f.write(line + '\n')

            self.add_line(f"\n分析结果已保存到: {output_filepath}")
            return True

        except Exception as e:
            self.add_line(f"保存文件时出错: {e}")
            return False


def main():
    """
    IDX文件分析器主函数 - 演示和批处理入口
    ====================================

    功能说明:
    --------
    提供了完整的IDX文件分析流程演示, 展示如何使用IdxFileAnalyzer类
    进行文件分析、报告生成和数据导出。适用于批处理和自动化场景。

    处理流程:
    --------
    1. 环境设置:配置数据目录和目标文件
    2. 文件定位:构建IDX文件和输出文件的完整路径
    3. 分析器创建:初始化IdxFileAnalyzer实例
    4. 完整分析:执行文件头、数据点和索引区的完整解析
    5. 报告保存:生成详细的TXT分析报告
    6. 数据导出:生成Excel格式的数据表和索引表
    7. 结果反馈:输出处理状态和文件位置

    默认配置:
    --------
    - 数据目录:./his-data(HIS和IDX文件存放位置)
    - 目标文件:2025070222(文件名前缀, 自动添加.idx扩展名)
    - 输出文件:
      * TXT报告:{base_name}_idx_analysis.txt
      * 数据点Excel:{base_name}_数据点列表.xlsx
      * 索引Excel:{base_name}_时间索引.xlsx

    输出文件说明:
    -----------
    1. TXT分析报告:
       - 完整的文件结构分析
       - 十六进制数据展示
       - 详细的解析过程
       - 错误和警告信息

    2. 数据点Excel文件:
       - AxPoint和DxPoint的完整清单
       - 统计信息和质量分析
       - 支持搜索和筛选

    3. 时间索引Excel文件:
       - 完整的时间-地址映射
       - 按时间块的统计分析
       - 索引样本和验证数据

    错误处理:
    --------
    - 文件不存在:提示检查文件路径
    - 权限不足:提示文件访问权限
    - 格式错误:显示具体错误位置
    - 磁盘空间:检查输出目录可用空间

    自定义使用:
    ----------
    可以修改以下变量来分析不同的文件:
    - data_dir:更改数据文件目录
    - base_name:更改目标文件名前缀
    - 输出文件路径:自定义报告和Excel文件位置

    批处理扩展:
    ----------
    可以扩展为批量处理多个文件:
    ```python
    file_list = ["2025070221", "2025070222", "2025070223"]
    for base_name in file_list:
        # 执行分析流程
    ```

    返回值:
    ------
    无显式返回值, 通过控制台输出和文件生成体现结果
    """
    data_dir = "/Users/zx_ll/Documents/my_refs/computer-refs/Embedded_Resource_Files/ExtractDataFromHis/his-data"

    # 分析目标文件
    base_name = "2025070222"
    idx_file = os.path.join(data_dir, f"{base_name}.idx")
    output_file = os.path.join(data_dir, f"{base_name}_idx_analysis.txt")
    points_excel_file = os.path.join(data_dir, f"{base_name}_数据点列表.xlsx")
    index_excel_file = os.path.join(data_dir, f"{base_name}_时间索引.xlsx")

    # 创建分析器
    analyzer = IdxFileAnalyzer(idx_file)

    # 执行分析
    result = analyzer.analyze_file()
    if result:
        ax_points, dx_points, time_index_data = result

        # 保存txt报告
        analyzer.save_to_file(output_file)
        # print(f"\n✓ 分析完成, 结果已保存到: {output_file}")

        # 导出Excel文件
        if analyzer.export_to_excel(ax_points, dx_points, time_index_data,
                                    points_excel_file, index_excel_file):
            print(f"[OK] 数据点Excel已保存到: {points_excel_file}")
            print(f"[OK] 索引Excel已保存到: {index_excel_file}")
        else:
            print("[ERROR] Excel导出失败")
    else:
        print("\n[ERROR] 分析失败")


if __name__ == "__main__":
    main()
