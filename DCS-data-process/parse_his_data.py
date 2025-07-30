#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
HIS历史数据文件解析器

作者: zhengxu
版本: 2.1
更新: 2025-07-30

==========================================================
用于电力控制系统DCS生成的HIS历史数据文件格式, 提取时序数据并导出为Excel格式。

文件格式说明:
-----------
HIS文件系统包含两个关键文件:
1. IDX文件(索引文件):包含数据点定义、时间索引和数据块地址映射
2. HIS文件(历史数据文件):包含时序数据

数据结构:
--------
- 文件头:117字节固定头部, 包含版本信息和基本参数
- 数据点定义:每个AxPoint占36字节, 包含点名、序号等信息
- 时间索引:每小时分为30个2分钟数据块, 每块包含120秒数据
- 数据压缩:使用差值压缩算法, 首值+差值序列的方式存储

使用方法:
--------
命令行模式:

    --file/-f     : 可选, 文件名(不含扩展名)
                   格式:YYYYMMDDHH(默认:2025070222)

    --point/-p    : 可选, 单个数据点名称
                   示例:"20MCS-UNITMW", "SYS_XCU001_Memory"

    --points      : 可选, 多个数据点名称(用逗号分隔)
                   示例:"20MCS-UNITMW,SYS_XCU001_Memory,SYS_XCU101_AN_OFF"

    --allpoints   : 可选, 处理所有可用数据点

    --excel       : 可选, 导出Excel文件(默认不导出)

    --dir/-d      : 可选, 数据文件目录 (默认:"./his-data")

    使用示例:
    1. 查看可用数据点:
       python parse_his_data.py --file 2025070222

    2. 解析单个数据点(不导出Excel):
       python parse_his_data.py --file 2025070222 --point "20MCS-UNITMW"

    3. 解析单个数据点并导出Excel:
       python parse_his_data.py --file 2025070222 --point "20MCS-UNITMW" --excel

    4. 解析多个数据点并导出Excel:
       python parse_his_data.py --file 2025070222 --points "20MCS-UNITMW,SYS_XCU001_Memory" --excel

    5. 解析所有数据点(不导出Excel):
       python parse_his_data.py --file 2025070222 --allpoints

    6. 解析所有数据点并导出Excel:
       python parse_his_data.py --file 2025070222 --allpoints --excel

    7. 指定数据目录:
       python parse_his_data.py --file 2025070222 --point "20MCS-UNITMW" --dir "/data/his" --excel

输出格式:
--------
生成的Excel文件包含三个工作表:
1. 时序数据表:完整的时间戳-数值序列
2. 统计信息表:数据汇总统计
3. 每2分钟汇总表:按时间块聚合的统计信息
"""

import struct
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PointInfo:
    """数据点信息数据类"""
    name: str
    point_index: int  # 序号
    point_type: int  # 0=AX, 1=DX


class PointDataStruct:
    """
    工业数据点结构体类 - 数据库对接格式
    =====================================

    数据字段:
    --------
    - point_code: 数据点代码/标识符(如"20MCS-UNITMW")
    - point_value: 数据点的数值(浮点数)
    - point_index: 数据点序号(用于在idx索引块中定位)
    - date_time: 精确时间戳(datetime对象)
    - point_type: 数据点类型(0=AX模拟量, 1=DX数字量)

    使用示例:
    --------
    point = StructPoint()
    point.point_code = "20MCS-UNITMW"
    point.point_value = 123.45
    point.date_time = datetime.now()
    point.point_type = 0
    """
    def __init__(self):
        self.point_code = ""      # 数据点代码
        self.point_value = 0.0    # 数值
        self.point_index = 0      # 序号
        self.date_time = datetime.now()  # 时间戳
        self.point_type = 0       # 数据点类型


class HisDataParser:
    """
    HIS历史数据文件解析器核心类
    ===========================

    功能概述:
    --------
    这是整个解析系统的核心类, 负责处理HIS/IDX文件对的完整解析流程。

    1. IDX索引文件解析:提取数据点定义和时间索引信息
    2. HIS数据文件解析:读取压缩的时序数据块
    3. 数据解压缩:还原差值压缩的原始数值
    4. 时间戳计算:精确计算每个数据点的时间戳
    5. Excel导出:生成包含统计信息的完整报表
    6. 缓存优化:IDX文件智能缓存, 避免重复解析
    7. 批量处理优化:支持高效的多数据点处理

    核心数据结构:
    -----------
    - ax_points_num: AxPoint类型数据点总数
    - dx_points_num: DxPoint类型数据点总数
    - idx_start_offset: 时间索引在IDX文件中的起始偏移量
    - _point_info_cache: 数据点信息缓存
    - _idx_parsed: IDX文件解析状态标记
    - _idx_cache_filepath: 当前缓存的IDX文件路径

    解析流程:
    1. 读取IDX文件头, 获取数据点总数和布局信息
    2. 解析所有数据点定义, 建立序号-代码映射关系
    3. 根据目标数据点, 定位其在每个时间块的数据地址
    4. 从HIS文件读取压缩数据块, 解压还原为时序数据
    5. 计算精确时间戳, 生成完整的数据点序列
    6. 导出为Excel格式, 包含原始数据和统计信息
    """
    def __init__(self):
        """
        初始化解析器
        """
        self.ax_points_num = 0
        self.dx_points_num = 0
        self.idx_start_offset = 0

        # 缓存优化相关变量
        self._idx_cache_filepath = None  # 当前缓存的IDX文件路径
        self._idx_parsed = False  # IDX文件是否已解析并缓存
        self._point_info_cache = {}  # 数据点信息缓存

        # HIS文件缓存优化
        self._his_cache_filepath = None  # 当前缓存的HIS文件路径
        self._his_binary_data = None  # HIS文件二进制数据缓存
        self._his_loaded = False  # HIS文件是否已加载到内存

    def idx_info_parser(self, idx_filepath: str) -> Dict[int, str]:
        """
        IDX索引文件解析核心方法 - 带缓存优化
        =====================================

        功能说明:
        --------
        解析IDX文件的完整结构, 提取所有数据点的定义信息和索引映射关系。
        这是整个解析流程的第一步, 为后续数据提取建立基础映射表。

        缓存优化:
        --------
        - 检查是否已缓存当前IDX文件的解析结果
        - 如果已缓存且文件路径相同, 直接返回缓存结果
        - 否则重新解析并更新缓存

        文件结构解析:
        -----------
        1. 文件头验证(0-21字节):检查"HIS_INDEX_FILE VER2.1"标识
        2. AxPoint数量(22-25字节):4字节整数, 表示模拟量数据点总数
        3. DxPoint数量(26-29字节):4字节整数, 表示数字量数据点总数
        4. 数据点定义区(118字节开始):每个数据点占36字节
           - 点名称:变长字符串, 以0x00结尾
           - 序号:32字节偏移处的4字节整数
        5. 时间索引区:117 + (AxPoints + DxPoints) * 36 - 3字节开始

        Args:
            idx_filepath: IDX文件的完整路径

        Returns:
            bool: 解析成功返回True, 失败返回False
        """
        # 缓存优化: 检查是否已解析当前文件
        if (self._idx_parsed and self._idx_cache_filepath == idx_filepath and self._point_info_cache):
            print("使用IDX文件缓存数据")
            return True

        print(f"正在解析IDX文件: {idx_filepath}")

        try:
            # 把文件读取到字节数组 - 对应C#代码
            with open(idx_filepath, 'rb') as f:
                binary_data = f.read()

            file_length = len(binary_data)  # 文件总长度
            print(f"IDX文件大小: {file_length} 字节")

            # 验证文件头
            header = binary_data[:21].decode('ascii', errors='ignore')
            print(f"文件头: {header}")

            # 清空之前的缓存
            self._point_info_cache.clear()

            # Ax Point数量开始位置, 共4个字节 - 对应C#代码 iStart = 22
            i_start = 22
            point_num = binary_data[i_start:i_start + 4]
            self.ax_points_num = struct.unpack('<I', point_num)[0]
            print(f"AxPoint数量: {self.ax_points_num}")

            # DxPoint数量 - 对应C#代码 iStart = 26
            i_start = 26
            dx_point_num = binary_data[i_start:i_start + 4]
            self.dx_points_num = struct.unpack('<I', dx_point_num)[0]
            print(f"DxPoint数量: {self.dx_points_num}")

            # 计算索引开始位置
            self.idx_start_offset = 117 + self.ax_points_num * 36 + self.dx_points_num * 36 - 3
            print(f"索引开始位置: {self.idx_start_offset}")

            error_index_num = 0
            error_index = ""

            # =================================================
            # 读取所有Ax Point点代号和序号 - iStart = 118
            i_start = 118

            for i in range(self.ax_points_num):
                if i_start + 36 > len(binary_data):
                    print(f"警告: 读取第{i}个AxPoint时超出文件范围")
                    break

                # 计算点名偏移量(点名长度不一样)
                i_offset = 0
                while (i_start + i_offset < len(binary_data) and
                       binary_data[i_start + i_offset] != 0x00):
                    i_offset += 1

                # 读取点代码
                if i_offset > 0:
                    point_code_bytes = binary_data[i_start:i_start + i_offset]
                    point_code = point_code_bytes.decode('ascii', errors='ignore')
                else:
                    point_code = f"POINT_{i}"

                # 读取点序号(偏移32, 4字节)
                if i_start + 36 <= len(binary_data):
                    point_index_bytes = binary_data[i_start + 32:i_start + 36]
                    point_index = struct.unpack('<I', point_index_bytes)[0]
                else:
                    point_index = 65535

                # 对应C#代码的错误处理
                if point_index == 65535:
                    error_index += point_code + "; "
                    error_index_num += 1
                    i_start += 36
                    continue

                # 建立缓存
                if point_index != 65535:
                    # 缓存数据点信息
                    self._point_info_cache[point_code] = PointInfo(
                        name=point_code,
                        point_index=i,
                        point_type=0  # AxPoint类型为0
                    )

                if len(self._point_info_cache) <= 20:  # 只显示前20个
                    print(f"数据点 {i}: {point_code} (序号: {point_index}) [AX]")

                i_start += 36

            # =================================================
            # 读取所有Dx Point点代号和序号
            print("开始解析DxPoint...")
            for i in range(self.dx_points_num):
                if i_start + 36 > len(binary_data):
                    print(f"警告: 读取第{i}个DxPoint时超出文件范围")
                    break

                # 计算点名偏移量(点名长度不一样)
                i_offset = 0
                while (i_start + i_offset < len(binary_data) and
                       binary_data[i_start + i_offset] != 0x00):
                    i_offset += 1

                # 读取点代码
                if i_offset > 0:
                    point_code_bytes = binary_data[i_start:i_start + i_offset]
                    point_code = point_code_bytes.decode('ascii', errors='ignore')
                else:
                    point_code = f"DXPOINT_{i}"

                # 读取点序号(偏移32, 4字节)
                if i_start + 36 <= len(binary_data):
                    point_index_bytes = binary_data[i_start + 32:i_start + 36]
                    point_index = struct.unpack('<I', point_index_bytes)[0]
                else:
                    point_index = 65535

                # 错误处理
                if point_index == 65535:
                    error_index += point_code + "; "
                    error_index_num += 1
                    i_start += 36
                    continue

                # DxPoint的索引应该从AxPoint总数之后开始计算
                dx_index = self.ax_points_num + i
                if point_index != 65535:
                    # 缓存数据点信息
                    self._point_info_cache[point_code] = PointInfo(
                        name=point_code,
                        point_index=dx_index,
                        point_type=1  # DxPoint类型为1
                    )

                if len(self._point_info_cache) <= 40:  # 显示前40个(包括AxPoint和DxPoint)
                    print(f"数据点 {dx_index}: {point_code} (序号: {point_index}) [DX]")

                i_start += 36

            if error_index_num > 0:
                print(f"发现 {error_index_num} 个无效序号的数据点")

            # 更新缓存状态
            self._idx_cache_filepath = idx_filepath
            self._idx_parsed = True

            print(f"成功解析 {len(self._point_info_cache)} 个有效数据点")
            print(f"缓存了 {len(self._point_info_cache)} 个数据点信息")
            return True

        except Exception as e:
            print(f"解析IDX文件时出错: {e}")
            # 清空缓存状态
            self._idx_parsed = False
            self._idx_cache_filepath = None
            return False

    def load_his_file_to_cache(self, his_filepath: str) -> bool:
        """
        HIS文件缓存加载方法 - 性能优化核心
        ==================================

        功能说明:
        --------
        将HIS文件一次性加载到内存中进行缓, 避免重复的磁盘I/O操作。
        这是解决性能瓶颈的关键优化, 将文件读取次数从N次(数据点数量)减少到1次。

        Args:
            his_filepath: HIS文件的完整路径

        Returns:
            bool: 加载成功返回True, 失败返回False
        """
        # 缓存命中检查
        if (self._his_loaded and self._his_cache_filepath == his_filepath
                and self._his_binary_data is not None):
            print("[OK] 使用HIS文件缓存数据")
            return True

        print(f"[LOAD] 正在加载HIS文件到内存: {his_filepath}")

        try:
            # 检查文件是否存在
            if not os.path.exists(his_filepath):
                print(f"[ERROR] HIS文件不存在: {his_filepath}")
                return False

            # 获取文件大小信息
            file_size = os.path.getsize(his_filepath)
            file_size_mb = file_size / (1024 * 1024)
            print(f"HIS文件大小: {file_size_mb:.1f} MB")

            # 一次性读取整个文件到内存
            with open(his_filepath, 'rb') as f:
                self._his_binary_data = f.read()

            # 更新缓存状态
            self._his_cache_filepath = his_filepath
            self._his_loaded = True

            print(f"HIS文件已缓存到内存 ({file_size_mb:.1f} MB)")
            return True

        except Exception as e:
            print(f"[ERROR] 加载HIS文件失败: {e}")
            # 清空缓存状态
            self._his_loaded = False
            self._his_cache_filepath = None
            self._his_binary_data = None
            return False

    def to_unix_timestamp(self, dt: datetime) -> int:
        epoch = datetime(1970, 1, 1)
        return int((dt - epoch).total_seconds())

    def read_block_data(self, binary_data: bytes, array_count: int,
                        point_code: str, index: int, block_time: datetime,
                        point_type: int = 0) -> List[PointDataStruct]:
        """
        数据块解析与解压缩核心算法
        =========================

        功能说明:
        --------
        解析单个2分钟数据块的压缩数据, 还原为完整的时序数据点序列。

        HIS文件采用差值压缩来存储:
        1. 数组个数序列:每个字节表示一个数组包含的数据点个数
        2. 首值+差值模式:每个数组存储一个首值和一个差值
        3. 数值计算:后续值 = 前一个值 + 差值
        4. 时间递增:每个数据点对应1秒时间间隔

        数据块结构:
        ----------
        [数组个数序列] [首值1][差值1] [首值2][差值2] ... [首值N][差值N]
        - 数组个数序列:array_count个字节, 每字节为该数组的数据点个数
        - 首值:4字节浮点数, 数组第一个数据点的值
        - 差值:4字节浮点数, 数组内其他数据点与前一个点的差值

        解析流程:
        --------
        1. 读取数组个数序列, 确定数据组织结构
        2. 遍历每个数组:
           a. 读取首值, 创建第一个数据点
           b. 读取差值, 计算后续数据点值
           c. 为每个数据点计算精确时间戳
        3. 时间控制:确保不超过120秒(2分钟)限制
        4. 返回完整的数据点列表

        Args:
            binary_data: 数据块二进制数据
            array_count: 数组个数
            point_code: 数据点代码
            index: 数据点序号
            block_time: 当前数据块的起始时间

        Returns:
            List[StructPoint]: 解析出的数据点列表(通常120个)
        """
        try:
            # 先读取数组数据个数数据
            array_nums = []
            time_length = 0

            for i in range(array_count):
                if i >= len(binary_data):
                    break
                num = binary_data[i]
                time_length += num
                array_nums.append(num)

            i_start = array_count
            point_block_data = []

            # 开始逐个读取监测数据数组
            time_offset_seconds = 0  # 从数据块开始的秒数偏移

            for i in range(len(array_nums)):
                if time_offset_seconds >= 120:  # 2分钟 = 120秒
                    break

                if i_start + 8 > len(binary_data):
                    break

                # 读取第一位监测数据(4字节浮点数)
                temp = binary_data[i_start:i_start + 4]
                first_value = struct.unpack('<f', temp)[0]

                # 创建第一个数据点
                point = PointDataStruct()
                point.point_code = point_code
                point.point_value = first_value
                point.point_index = index
                point.date_time = block_time + timedelta(seconds=time_offset_seconds)
                point.point_type = point_type

                point_block_data.append(point)

                time_offset_seconds += 1
                if time_offset_seconds >= 120:
                    break

                # 读取后续差值(4字节浮点数)
                i_start += 4
                if i_start + 4 > len(binary_data):
                    break

                temp = binary_data[i_start:i_start + 4]
                cha = struct.unpack('<f', temp)[0]
                i_start += 4

                # 计算数组后边几位监测数据
                last_value = first_value
                for j in range(1, array_nums[i]):
                    if time_offset_seconds >= 120:
                        break

                    cha_point = PointDataStruct()
                    cha_point.point_code = point_code
                    cha_point.point_value = last_value + cha
                    last_value = cha_point.point_value
                    cha_point.point_index = index
                    cha_point.date_time = block_time + timedelta(seconds=time_offset_seconds)
                    cha_point.point_type = point_type

                    point_block_data.append(cha_point)

                    time_offset_seconds += 1
                    if time_offset_seconds >= 120:
                        break

            return point_block_data

        except Exception as e:
            print(f"解析数据块时出错: {e}")
            return []

    def read_single_point_all_blocks(self, directory: str, file_title: str, point_name: str) -> List[PointDataStruct]:
        """
        单数据点全时序数据提取主方法 - 使用缓存优化
        ==============================================

        功能说明:
        --------
        使用缓存的数据点信息提取指定数据点的完整时序数据。

        - 数据点定位:根据point_name查找对应的序号
        - 时间循环:遍历30个2分钟时间块
        - 地址计算:定位每个时间块中该数据点的数据地址
        - 数据提取:从HIS文件读取压缩数据块
        - 数据解析:调用read_block_data解压还原数据
        - 结果汇总:合并所有时间块的数据点

        时间块算法:
        ----------
        - 时间块总数:30个(1小时 = 30 × 2分钟)
        - 索引计算:idx_start + 时间块号 × 总点数 × 4 + 数据点序号 × 4
        - 地址读取:从IDX文件读取4字节数据块地址
        - 时间计算:基准时间 + 时间块号 × 2分钟

        关键优化:
        --------
        1. 使用缓存的数据点信息, 避免重复调用get_point_code_and_index
        2. 直接从self._point_info_cache获取数据点的index和类型信息
        3. 保持与原版本完全相同的功能和输出

        Args:
            directory: 文件目录
            file_title: 文件名标题(如 "2025070222")
            point_name: 数据点名称(如 "20MCS-UNITMW")

        Returns:
            List[StructPoint]: 解析出的该数据点的所有时序数据
        """
        his_filename = os.path.join(directory, f"{file_title}.his")
        idx_filename = os.path.join(directory, f"{file_title}.idx")

        print(f"=== 解析数据点 '{point_name}' 的全部时序数据 ===")
        print(f"处理文件对: {file_title}")

        if not os.path.exists(idx_filename):
            print(f"错误: IDX文件不存在 {idx_filename}")
            return []

        if not os.path.exists(his_filename):
            print(f"错误: HIS文件不存在 {his_filename}")
            return []

        try:
            # 如果缓存未初始化或文件不匹配, 先解析IDX文件
            if (not self._idx_parsed or self._idx_cache_filepath != idx_filename or not self._point_info_cache):
                print("[INIT] 初始化IDX缓存...")
                self.idx_info_parser(idx_filename)

            # 检查数据点是否在缓存中
            if point_name not in self._point_info_cache:
                print(f"错误: 找不到数据点 '{point_name}'")
                print(f"可用的数据点: {list(self._point_info_cache.keys())}")
                return []

            # 从缓存获取数据点信息
            point_info = self._point_info_cache[point_name]
            target_index = point_info.point_index
            print(f"找到数据点: {point_name} (序号: {target_index}, 类型: {'AX' if point_info.point_type == 0 else 'DX'})")

            # 将idx文件读到内存
            with open(idx_filename, 'rb') as f:
                idx_binary_data = f.read()

            # 加载HIS文件到缓存 - 性能优化关键
            if not self.load_his_file_to_cache(his_filename):
                print(f"[ERROR] 无法加载HIS文件: {his_filename}")
                return []

            # 使用缓存的HIS数据
            his_binary_data = self._his_binary_data

            # 解析时间
            try:
                year = int(file_title[:4])
                month = int(file_title[4:6])
                day = int(file_title[6:8])
                hour = int(file_title[8:10])
                current_hour = datetime(year, month, day, hour)
            except Exception:
                current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

            point_all_data = []
            total_points = self.ax_points_num + self.dx_points_num

            # 处理该数据点在所有30个时间块的数据
            for time_block in range(30):
                try:
                    # 计算该点在该时间块的索引位置
                    idx_index = self.idx_start_offset + time_block * total_points * 4 + target_index * 4

                    if idx_index + 4 > len(idx_binary_data):
                        continue

                    # 取出该点在该时间块的数据块开始地址
                    address_bytes = idx_binary_data[idx_index:idx_index + 4]
                    block_address = struct.unpack('<I', address_bytes)[0]

                    if block_address >= len(his_binary_data):
                        continue

                    # 从his文件中取出2分钟数据块
                    if block_address + 1 >= len(his_binary_data):
                        continue

                    array_count = his_binary_data[block_address]
                    offset = array_count * 9

                    if block_address + 2 + offset > len(his_binary_data):
                        continue

                    data_block = his_binary_data[block_address + 2:block_address + 2 + offset]

                    # 解析数据块
                    block_time = current_hour + timedelta(minutes=time_block * 2)
                    points_block_data = self.read_block_data(
                        data_block, array_count, point_name, target_index,
                        block_time, point_info.point_type)
                    point_all_data.extend(points_block_data)

                    # if len(points_block_data) > 0:
                    #     time_str = f"{time_block * 2:02d}:{time_block * 2 + 1:02d}分钟"
                    #     print(f"时间块 {time_block} ({time_str}): {len(points_block_data)} 个数据点")

                except Exception as e:
                    print(f"[Warning] 时间块 {time_block} 处理失败: {e}")
                    continue

            print(f"数据点 '{point_name}' 总共解析了 {len(point_all_data)} 个时序数据")
            return point_all_data

        except Exception as e:
            print(f"[ERROR] 读取数据点 '{point_name}' 失败: {e}")
            return []

    def get_cached_point_info(self, point_name: str) -> Optional[PointInfo]:
        return self._point_info_cache.get(point_name)

    def get_all_cached_points(self) -> Dict[str, PointInfo]:
        return self._point_info_cache.copy()

    def clear_cache(self):
        """清空所有缓存数据"""
        self._point_info_cache.clear()
        self._idx_parsed = False
        self._idx_cache_filepath = None

        # 清空HIS文件缓存
        self._his_loaded = False
        self._his_cache_filepath = None
        self._his_binary_data = None

        print("已清空所有缓存 (包括IDX和HIS文件缓存)")

    def export_to_excel(self, data_points: List[PointDataStruct],
                        file_title: str, point_name: str,
                        directory: str = "./his-data") -> str:
        """
        Excel报表导出与统计分析
        =====================

        功能说明:
        --------
        将解析后的时序数据导出为多工作表Excel文件, 包含原始数据、统计信息和汇总报表。
        提供完整的数据分析和可视化基础。

        输出结构:
        --------
        1. 主数据表({point_name}_时序数据):
           - TimeStamp: 精确时间戳
           - Value: 数据值
           - PointCode: 数据点代码
           - PointName: 数据点名称
           - index: 数据点序号

        2. 统计信息表:
           - 数据点基本信息(名称、代码、记录数)
           - 时间范围(起始-结束时间)
           - 数值统计(最小值、最大值、平均值、中位数)
           - 导出时间戳

        3. 每2分钟汇总表(如果数据量足够):
           - 按时间块分组统计
           - 每个时间块的记录数、平均值、最值
           - 数据质量统计

        文件命名:
        --------
        格式:{file_title}_{safe_point_name}_timeseries.xlsx
        安全化规则:/ \\ : * ? " < > | 替换为 _
        保存位置:HIS文件所在目录

        Args:
            data_points: 数据点列表
            file_title: 文件名标题
            point_name: 数据点名称
            directory: HIS文件所在目录 (默认: "./his-data")

        Returns:
            str: 输出文件的完整路径(成功时)或空字符串(失败时)
        """
        if not data_points:
            print("没有数据可导出")
            return ""

        # 清理文件名中的特殊字符
        safe_point_name = (point_name.replace('/', '_').replace('\\', '_').replace(':', '_')
                           .replace('*', '_').replace('?', '_').replace('"', '_')
                           .replace('<', '_').replace('>', '_').replace('|', '_'))
        
        # 构建完整的输出文件路径 - 保存到HIS文件所在目录
        output_filename = f"{file_title}_{safe_point_name}_timeseries.xlsx"
        output_filepath = os.path.join(directory, output_filename)
        
        print(f"正在导出数据点'{point_name}'的 {len(data_points)} 个时序数据到Excel文件: {output_filepath}")

        try:
            # 创建DataFrame
            df_data = []
            for point in data_points:
                df_data.append({
                    'date_time': point.date_time,
                    'point_value': point.point_value,
                    'point_code': point.point_code,
                    'point_index': point.point_index,
                    'point_type': point.point_type
                })

            df = pd.DataFrame(df_data)

            # 按时间排序
            df = df.sort_values('date_time')

            # 添加统计信息
            total_records = len(data_points)
            time_range = f"{df['date_time'].min()} 到 {df['date_time'].max()}"
            value_stats = {
                '最小值': df['point_value'].min(),
                '最大值': df['point_value'].max(),
                '平均值': df['point_value'].mean(),
                '中位数': df['point_value'].median()
            }

            # 导出到Excel
            with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
                # 主数据表
                df.to_excel(writer, sheet_name=f'{safe_point_name}_时序数据', index=False)

                # 统计信息表
                stats_data = [
                    ['数据点名称', point_name],
                    ['数据点代码', data_points[0].point_code if data_points else ''],
                    ['总记录数', total_records],
                    ['时间范围', time_range],
                    ['数值最小值', value_stats['最小值']],
                    ['数值最大值', value_stats['最大值']],
                    ['数值平均值', round(value_stats['平均值'], 4) if pd.notna(value_stats['平均值']) else 'N/A'],
                    ['数值中位数', value_stats['中位数']],
                    ['导出时间', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                ]
                stats_df = pd.DataFrame(stats_data, columns=['项目', '值'])
                stats_df.to_excel(writer, sheet_name='统计信息', index=False)

                # 每小时数据汇总(如果数据跨度超过1小时)
                if total_records > 30:  # 如果有多个时间块的数据
                    df['小时'] = df['date_time'].dt.strftime('%H:%M')
                    hourly_summary = df.groupby('小时').agg({
                        'point_value': ['count', 'mean', 'min', 'max']
                    }).round(4)
                    hourly_summary.columns = ['记录数', '平均值', '最小值', '最大值']
                    hourly_summary.to_excel(writer, sheet_name='每2分钟汇总')

            print(f"导出完成: {output_filepath}")
            print(f"导出了数据点'{point_name}'的 {total_records} 个时序数据")
            return output_filepath

        except Exception as e:
            print(f"导出Excel时出错: {e}")
            return ""


def main():
    """
    HIS历史数据解析器主函数 - 支持命令行和默认参数
    ===============================================

    功能说明:
    --------
    提供完整的命令行接口, 支持自定义参数的批量数据处理。
    当没有指定文件参数时, 使用默认值。

    新增功能:
    --------
    - --allpoints: 处理所有数据点
    - --points: 指定多个数据点 (用逗号分隔)
    - --excel: 是否导出Excel文件 (默认不导出)
    - --point: 单个数据点名称 (兼容原版本)

    使用方法: 见文件开头
    """
    import argparse

    parser_cmd = argparse.ArgumentParser(description='HIS历史数据解析器')
    parser_cmd.add_argument('--file', '-f', default='2025070222',
                            help='文件名(不含扩展名), 默认: 2025070222')
    parser_cmd.add_argument('--point', '-p',
                            help='单个数据点名称(兼容旧版本)')
    parser_cmd.add_argument('--points',
                            help='多个数据点名称，用逗号分隔，如: "20MCS-UNITMW,SYS_XCU001_Memory"')
    parser_cmd.add_argument('--allpoints', action='store_true',
                            help='处理所有可用数据点')
    parser_cmd.add_argument('--excel', action='store_true',
                            help='导出Excel文件 (默认不导出)')
    parser_cmd.add_argument('--dir', '-d', default='./his-data',
                            help='数据文件目录, 默认: ./his-data')

    args = parser_cmd.parse_args()

    # 创建解析器
    parser = HisDataParser()

    print("=== HIS历史数据解析器 ===")
    print(f"目标文件: {args.file}")
    print(f"数据目录: {args.dir}")
    print(f"导出Excel: {'是' if args.excel else '否'}")

    # 先解析IDX文件获取所有可用数据点
    idx_filepath = os.path.join(args.dir, f"{args.file}.idx")
    if not parser.idx_info_parser(idx_filepath):
        print("[ERROR] 无法解析IDX文件")
        return

    # 确定要处理的数据点列表
    target_points = []

    if args.allpoints:
        # 处理所有数据点
        target_points = list(parser._point_info_cache.keys())
        print(f"处理所有数据点: {len(target_points)} 个")
    elif args.points:
        # 处理多个指定数据点
        requested_points = [p.strip() for p in args.points.split(',')]
        available_points = set(parser._point_info_cache.keys())

        for point in requested_points:
            if point in available_points:
                target_points.append(point)
                print(f"找到数据点: {point}")
            else:
                print(f"[Warning] 数据点不存在: {point}")

        if not target_points:
            print("[ERROR] 没有找到任何有效的数据点")
            return
    elif args.point:
        # 处理单个数据点 (兼容旧版本)
        if args.point in parser._point_info_cache:
            target_points = [args.point]
            print(f"处理单个数据点: {args.point}")
        else:
            print(f"[ERROR] 数据点不存在: {args.point}")
            return
    else:
        # 没有指定数据点，显示可用列表
        if parser._point_info_cache:
            available_points = list(parser._point_info_cache.keys())[:20]
            print("可用数据点(前20个):")
            for i, point in enumerate(available_points):
                point_info = parser._point_info_cache[point]
                point_type = 'AX' if point_info.point_type == 0 else 'DX'
                print(f"  {i + 1:2d}. {point} [{point_type}]")

            print(f"\n总共 {len(parser._point_info_cache)} 个数据点")
            print("\n使用方法:")
            print("  --point <点名>        : 处理单个数据点")
            print("  --points <点1,点2>    : 处理多个数据点")
            print("  --allpoints          : 处理所有数据点")
            print("  --excel             : 导出Excel文件")
        else:
            print("无法获取数据点列表")
        return

    # 处理数据点
    print(f"\n开始处理 {len(target_points)} 个数据点...")
    successful_exports = 0
    failed_points = []

    for i, point_name in enumerate(target_points, 1):
        print(f"\n[{i}/{len(target_points)}] 处理数据点: {point_name}")

        try:
            # 解析数据点
            point_all_data = parser.read_single_point_all_blocks(args.dir, args.file, point_name)

            if point_all_data:
                print(f"成功解析 {len(point_all_data)} 个数据点")

                # 根据excel参数决定是否导出
                if args.excel:
                    output_file = parser.export_to_excel(point_all_data, args.file, point_name, args.dir)
                    if output_file:
                        print(f"Excel导出完成: {output_file}")
                        successful_exports += 1
                    else:
                        print(f"[ERROR] Excel导出失败: {point_name}")
                        failed_points.append(point_name)
                else:
                    print("数据解析完成(未导出Excel)")
                    successful_exports += 1
            else:
                print(f"[ERROR] 解析失败: {point_name}")
                failed_points.append(point_name)

        except Exception as e:
            print(f"[ERROR] 处理失败: {point_name} - {e}")
            failed_points.append(point_name)

    # 总结报告
    print(f"  总数据点: {len(target_points)}")
    print(f"  成功处理: {successful_exports}")
    print(f"  失败数量: {len(failed_points)}")

    if failed_points:
        print(f"   失败列表: {', '.join(failed_points)}")

    if args.excel:
        print(f"   Excel文件: {'已导出' if successful_exports > 0 else '未导出'}")

    print("批处理完成")


if __name__ == "__main__":
    main()
