#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
文件编码修复工具！ (File Encoding Fixer)
==============================================================================

作者: zhengxu
版本: v2.3
日期: 2025-08-21
许可: MIT License

==============================================================================
项目简介: 文件编码检测和修复，尤其是用于解决中文文件的乱码问题。
==============================================================================

根据乱码产生的机制，本工具将乱码分为两种类型：

【一型乱码】- 简单编码错误
    原始文件: encoding_init (如 gbk/gb2312)
    错误读取: 用错误编码解码 (如 utf-8/latin-1)
    修复方法: 直接用正确编码重新读取文件

【二型乱码】- 双重编码错误  
    原始文件: encoding_init (如 gbk/gb2312)
    第一次错误: 用 encoding_mid 解码 (如 latin-1/windows-1252)
    第二次错误: 重新编码为 encoding_end (如 utf-8/gbk)
    修复方法: 逆向三重编码链恢复原始内容

==============================================================================
基本用法
==============================================================================

【分析文件编码】
python file_encoding_fixer.py <文件路径> --analyze

【生成一型修复文件】(推荐首选)
python file_encoding_fixer.py <文件路径> --force-type1

【生成二型修复文件】(复杂乱码使用)
python file_encoding_fixer.py <文件路径> --force-type2

【指定编码优先级】
python file_encoding_fixer.py <文件路径> --force-type1 --priority 1  # 仅第一优先级
python file_encoding_fixer.py <文件路径> --force-type1 --priority 2  # 前两个优先级(默认)
python file_encoding_fixer.py <文件路径> --force-type1 --priority 3  # 所有优先级

【详细日志输出】
python file_encoding_fixer.py <文件路径> --force-type1 --verbose

==============================================================================
输出说明
==============================================================================

【一型修复输出】
- 文件夹: <原文件名>_type1_encodings/
- 文件格式: <原文件名>_<编码名>.txt
- 质量指标: 中文字符数量、是否包含乱码

【二型修复输出】  
- 文件夹: <原文件名>_type2_encoding_chains/
- 文件格式: <原文件名>_<编码1>_<编码2>_<编码3>.txt
- 质量评级: 优(>10个中文字符且无乱码) / 中(有中文字符) / 差(有乱码)

【选择建议】
1. 优先查看质量为"优"和"中"的文件
2. 选择中文字符数量多的文件
3. 确认文件内容是否正确可读

==============================================================================
依赖库
==============================================================================

- charset-normalizer: 编码检测
- re: 正则表达式匹配
- subprocess: 系统命令调用
- argparse: 命令行参数解析


==============================================================================
实现逻辑
==============================================================================

1. 【编码检测】
   - 系统级检测: 使用 file --mime-encoding 命令
   - 乱码分析: 通过 charset_normalizer 分析乱码模式
   - 优先级管理: 三级编码优先级调整

2. 【批量修复生成】
   - 一型修复: 为每种编码生成单独的修复文件
   - 二型修复: 生成所有可能的编码链组合修复文件
   - 质量评估: 自动评估修复质量(中文字符数、乱码检测)


==============================================================================
"""

import charset_normalizer
import codecs
import sys
import os
import shutil
from typing import List, Tuple, Optional, Dict
import re
import itertools
import logging
import argparse


class FileEncodingFixer:
    def __init__(self, logger=None):
        # 设置日志记录器
        if logger is None:
            self.logger = logging.getLogger(__name__)
            # 如果没有处理器, 添加默认处理器
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger
            
        # 编码优先级配置
        self.priority1_encodings = ['utf-8', 'gbk', 'windows-1252']  # 第一优先级
        self.priority2_encodings = ['gb2312', 'latin1']              # 第二优先级
        self.priority3_encodings = ['big5', 'shift_jis', 'euc-kr']    # 第三优先级
        
        # 常见的编码列表, 按优先级排序
        self.common_encodings = self.priority1_encodings + self.priority2_encodings + self.priority3_encodings

        # 中文字符正则模式
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        
        # 特殊字符模式（乱码特征）
        self.special_char_patterns = [
            r'[°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏӳ]',  # 特殊符号
            r'[?]',     # 问号
            r'�',       # 替换字符
            r'[\x80-\xff]',  # 高位字符
        ]
        
        # 乱码判断模式（更严格的模式）
        self.mojibake_patterns = [
            r'[°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏӳ]{2,}',  # 连续特殊符号
            r'[?]{4,}',  # 连续问号
            r'�{2,}',    # 连续替换字符
            r'(?:[A-Za-z]{1,2}[°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏ]){3,}',  # 字母+特殊符号组合
        ]

        # 标准化编码名称
        self._sys_encoding_map = {
                            # ASCII 相关
                            'ascii': 'ascii',
                            'us-ascii': 'ascii',
                            'ansi_x3.4-1968': 'ascii',
                            
                            # UTF 系列
                            'utf-8': 'utf-8',
                            'utf8': 'utf-8',
                            'utf-16': 'utf-16',
                            'utf16': 'utf-16',
                            'utf-16le': 'utf-16le',
                            'utf-16be': 'utf-16be',
                            'utf-32': 'utf-32',
                            'utf32': 'utf-32',
                            
                            # ISO 系列
                            'iso-8859-1': 'latin1',
                            'iso8859-1': 'latin1',
                            'latin-1': 'latin1',
                            'latin1': 'latin1',
                            'iso-8859-2': 'iso-8859-2',
                            'iso-8859-15': 'iso-8859-15',
                            
                            # Windows 代码页
                            'windows-1252': 'windows-1252',
                            'cp1252': 'windows-1252',
                            'windows-1251': 'windows-1251',
                            'cp1251': 'windows-1251',
                            'windows-1250': 'windows-1250',
                            'cp1250': 'windows-1250',
                            
                            # 中文编码
                            'gb2312': 'gb2312',
                            'gb18030': 'gb18030',
                            'gbk': 'gbk',
                            'hz-gb-2312': 'hz',
                            
                            # 繁体中文
                            'big5': 'big5',
                            'big5-hkscs': 'big5hkscs',
                            
                            # 日文编码
                            'shift_jis': 'shift_jis',
                            'shiftjis': 'shift_jis',
                            'sjis': 'shift_jis',
                            'euc-jp': 'euc-jp',
                            'eucjp': 'euc-jp',
                            'iso-2022-jp': 'iso-2022-jp',
                            
                            # 韩文编码
                            'euc-kr': 'euc-kr',
                            'euckr': 'euc-kr',
                            'korean': 'euc-kr',
                            'ks_c_5601-1987': 'euc-kr',
                            
                            # 其他常见编码
                            'koi8-r': 'koi8-r',
                            'koi8-u': 'koi8-u',
                            'mac-roman': 'mac-roman',
                            'macroman': 'mac-roman',
        }
        # 置信度阈值
        self.confidence_threshold = 0.7

    def get_sys_file_encoding(self, file_path: str) -> Tuple[str, float]:
        """
        使用系统的 file --mime-encoding 命令检测文件编码
        返回: (编码名称, 置信度)
        """
        try:
            import subprocess
            
            # 执行 file --mime-encoding 命令
            result = subprocess.run(
                ['file', '--mime-encoding', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # 输出格式: "filename: encoding"
                if ':' in output:
                    encoding = output.split(':', 1)[1].strip()
                    
                    # 处理特殊情况
                    if encoding == 'unknown-8bit':
                        self.logger.warning(f"系统检测为: {encoding} (编码错误)")
                        return None, 0.0
                    elif encoding == 'binary':
                        self.logger.warning(f"系统检测为: {encoding} (二进制文件)")
                        return None, 0.0
                    else:
                        self.logger.info(f"系统检测为: {encoding}")
                        
                        # 标准化编码名称
                        normalized_encoding = self._sys_encoding_map.get(encoding.lower(), encoding)
                        
                        # 将检测到的编码提升到第一优先级
                        self._promote_encoding_to_priority1(normalized_encoding)
                        
                        return normalized_encoding, 0.9  # file命令通常比较准确
                        
            self.logger.error(f"file命令执行失败: {result.stderr}")
            return None, 0.0
            
        except subprocess.TimeoutExpired:
            self.logger.error("file命令执行超时")
            return None, 0.0
        except FileNotFoundError:
            self.logger.error("未找到file命令, 请确保系统已安装")
            return None, 0.0
        except Exception as e:
            self.logger.error(f"file命令执行出错: {e}")
            return None, 0.0

    def _promote_encoding_to_priority1(self, _encoding: str):
        """
        将检测到的编码提升到第一优先级
        """
        if not _encoding:
            return
            
        # 如果已经在第一优先级, 不做处理
        if _encoding in self.priority1_encodings:
            return
            
        # 从其他优先级中移除
        if _encoding in self.priority2_encodings:
            self.priority2_encodings.remove(_encoding)
        elif _encoding in self.priority3_encodings:
            self.priority3_encodings.remove(_encoding)
            
        # 添加到第一优先级的开头
        self.priority1_encodings.insert(0, _encoding)
        
        # 重新构建完整编码列表
        self.common_encodings = self.priority1_encodings + self.priority2_encodings + self.priority3_encodings
        
        self.logger.info(f"将编码 {_encoding} 提升到第一优先级")

    def get_encodings_by_priority(self, max_priority: int = 2) -> List[str]:
        """
        根据指定的最大优先级获取编码列表
        
        参数:
            max_priority: 最大优先级 (1, 2, 或 3)
        返回:
            编码列表
        """
        encodings = self.priority1_encodings.copy()
        
        if max_priority >= 2:
            encodings.extend(self.priority2_encodings)
            
        if max_priority >= 3:
            encodings.extend(self.priority3_encodings)
            
        return encodings

    def init_possible_encodings(self, file_path: str) -> None:
        """
        初始化可能的编码，设置编码优先级
        
        参数:
            file_path: 文件路径
        """
        self.logger.info("初始化编码优先级...")
        
        # 1. 先执行系统编码检测
        detected_encoding, confidence = self.get_sys_file_encoding(file_path)
        
        if detected_encoding and confidence > 0.5:
            self.logger.info(f"系统检测到编码: {detected_encoding} (置信度: {confidence:.2f})")
            # 编码已经在 get_sys_file_encoding 中被提升到第一优先级
        else:
            # 如果没有系统编码，使用 utf-8 作为系统编码
            self.logger.info("未检测到系统编码，使用 utf-8 作为默认系统编码")
        
        # 2. 调用 _test_possible_encodings 获取更多可能的编码
        try:
            result = self._test_possible_encodings(file_path)
            
            if result is not None:
                # result 是 (encoding, confidence) 元组
                if isinstance(result, tuple) and len(result) == 2:
                    encoding, confidence = result
                    
                    if encoding and confidence > 0.6:
                        self.logger.info(f"通过乱码分析检测到编码: {encoding} (置信度: {confidence:.2f})")
                        
                        # 根据置信度决定优先级
                        if confidence >= 0.8:
                            # 高置信度，提升到第一优先级
                            self._promote_encoding_to_priority1(encoding)
                        elif confidence >= 0.6:
                            # 中等置信度，提升到第二优先级
                            self._promote_encoding_to_priority2(encoding)
                        
                        self.logger.info(f"已将编码 {encoding} 加入到优先级列表")
                    else:
                        self.logger.debug(f"检测到编码 {encoding} 但置信度较低: {confidence:.2f}")
                else:
                    self.logger.debug("_test_possible_encodings 返回了意外的结果格式")
            else:
                self.logger.debug("_test_possible_encodings 未发现额外的编码信息")
                
        except Exception as e:
            self.logger.warning(f"执行 _test_possible_encodings 时出错: {e}")
        
        # 3. 输出最终的编码优先级
        self.logger.info("最终编码优先级:")
        self.logger.info(f"  第一优先级: {self.priority1_encodings}")
        self.logger.info(f"  第二优先级: {self.priority2_encodings}")
        self.logger.info(f"  第三优先级: {self.priority3_encodings}")

    def _promote_encoding_to_priority2(self, encoding: str):
        """
        将编码提升到第二优先级
        """
        if not encoding:
            return
            
        # 如果已经在第一或第二优先级，不做处理
        if encoding in self.priority1_encodings or encoding in self.priority2_encodings:
            return
            
        # 从第三优先级中移除
        if encoding in self.priority3_encodings:
            self.priority3_encodings.remove(encoding)
            
        # 添加到第二优先级的开头
        self.priority2_encodings.insert(0, encoding)
        
        # 重新构建完整编码列表
        self.common_encodings = self.priority1_encodings + self.priority2_encodings + self.priority3_encodings
        
        self.logger.info(f"将编码 {encoding} 提升到第二优先级")

    def _test_possible_encodings(self, file_path: str, exclude_encoding: str = None, 
                                   skip_utf8: bool = False) -> Tuple[str, float]:
        """
        尝试其他常用编码来读取文件
        参数:
            file_path: 文件路径
            exclude_encoding: 要排除的编码
            skip_utf8: 是否跳过UTF-8编码
        返回: (编码名称, 置信度) 或 None
        """
        _CANOPEN = False
        for encoding in self.common_encodings:
            if encoding == exclude_encoding:
                continue  # 跳过指定排除的编码
            if skip_utf8 and encoding == 'utf-8':
                continue  # 跳过UTF-8
                
            try:
                success, mojibake_lines = self.detect_mojibake_lines(file_path, encoding)
                if success and len(mojibake_lines) != 0:  # 能打开且有乱码
                    try:
                        # 可能的encodings和对应的置信度
                        possible_encodings_confidence = self._detect_mojibake_encoding(
                                file_path, mojibake_lines, encoding)
                        return possible_encodings_confidence
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                elif success == True:
                    _CANOPEN = True
            except Exception:
                continue
        if _CANOPEN == True:
            # 所有编码都失败，使用charset_normalizer作为最后手段
            self.logger.warning("好像不存在乱码？")
            return None
        else:
            self.logger.error("所有常用编码都无法打开文件...")
            return None

    def _detect_mojibake_encoding(self, file_path: str, mojibake_lines: List[str], current_encoding: str) -> Tuple[str, float]:
        """
        基于已知的乱码行和当前编码, 检测原始编码
        参数: 
            file_path - 文件路径
            mojibake_lines - List[str] 乱码行内容列表
            current_encoding - 当前读取文件使用的编码
        返回: (原始编码名称, 置信度)
        """
        if not mojibake_lines:
            return None, 0.0
            
        try:
            # 将乱码行重新编码为字节, 然后尝试用不同编码解码
            mojibake_text = '\n'.join(mojibake_lines)
            
            # 将当前编码下的乱码文本转换为字节
            mojibake_bytes = mojibake_text.encode(current_encoding, errors='ignore')
        except Exception as e:
            self.logger.error(f"乱码行编码失败: {e}")
            return None, 0.0

        self.logger.info(f"基于乱码行检测原始编码 (当前编码: {current_encoding})")
        self.logger.debug(f"乱码样本: {mojibake_text[:100].replace(chr(10), ' ')[:100]}...")
        
        try:
            # 使用charset_normalizer检测这些字节的编码
            results = charset_normalizer.from_bytes(mojibake_bytes)
        except Exception as e:
            self.logger.error(f"charset_normalizer检测失败: {e}")
            return None, 0.0

        if results:
            self.logger.info(f"charset_normalizer检测结果: 共{len(results)}个候选编码")
            self.logger.debug("候选编码详情:")
            
            # 安全地遍历结果, 避免切片操作
            count = 0
            for i, result in enumerate(results):
                if count >= 5:  # 只显示前5个
                    break
                self.logger.debug(f"  {i+1}. {result.encoding:12} 置信度: {result.coherence:.3f} "
                      f"语言: {result.language or 'N/A':8} 混乱度: {result.chaos:.3f}")
                count += 1
            
            # 测试每个候选编码是否能产生正常的中文文本
            for result in results:
                encoding = result.encoding
                confidence = result.coherence
                
                try:
                    # 用候选编码解码字节
                    decoded_text = mojibake_bytes.decode(encoding, errors='ignore')
                    
                    # 检查解码后的文本是否包含中文且无乱码
                    chinese_count = len(self.chinese_pattern.findall(decoded_text))
                    has_mojibake = self._text_has_mojibake(decoded_text)
                    
                    self.logger.debug(f"  测试 {encoding}: 中文字符数={chinese_count}, 有乱码={has_mojibake}")

                    if chinese_count > 0 and not has_mojibake:
                        self.logger.info(f"✓ 找到可能的原始编码: {encoding} (置信度: {confidence:.3f})")
                        self.logger.debug(f"  解码样本: {decoded_text[:100].replace(chr(10), ' ')[:100]}...")
                        return encoding, confidence
                        
                except Exception as e:
                    self.logger.debug(f"✗ {encoding} 解码失败: {e}")
                    continue
            
            # 如果没有找到理想的编码, 返回最佳候选
            best_result = results.best()
            if best_result and best_result.coherence >= 0.5:
                self.logger.info(f"未找到理想编码, 返回最佳候选: {best_result.encoding} (置信度: {best_result.coherence:.3f})")
                return best_result.encoding, best_result.coherence

        # 如果charset_normalizer失败, 尝试常见编码
        self.logger.info("charset_normalizer无法检测到有效编码, 尝试常见编码...")
        for encoding in self.common_encodings:
            if encoding == current_encoding:
                continue
            try:
                decoded_text = mojibake_bytes.decode(encoding, errors='ignore')
                chinese_count = len(self.chinese_pattern.findall(decoded_text))
                has_mojibake = self._text_has_mojibake(decoded_text)
                
                if chinese_count > 0 and not has_mojibake:
                    self.logger.info(f"✓ 常见编码测试成功: {encoding}")
                    self.logger.debug(f"  解码样本: {decoded_text[:100].replace(chr(10), ' ')[:100]}...")
                    return encoding, 0.8  # 给一个合理的置信度
                    
            except Exception:
                continue
        self.logger.warning("无法检测到有效的原始编码")
        return None, 0.0    

    def detect_mojibake_lines(self, file_path: str, encoding: str, n: int = 5) -> Tuple[bool, List[str]]:
        """
        检测文件中的乱码并返回含特殊字符最多的几行
        参数:
            file_path: 文件路径
            encoding: 编码方式
            n: 返回的乱码行数量
        返回: (success, mojibake_lines)
            success: False=解码失败/读取失败/文件无内容, True=成功检测
            mojibake_lines: 乱码行列表, 空列表表示无乱码
        """
        if n is None:
            n = 5

        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, UnicodeError, LookupError) as e:
            self.logger.debug(f"文件编码错误 ({encoding}): {e}")
            return False, []

        if not lines:
            self.logger.debug("文件内容为空或无法读取")
            return False, []
        
        # 分析每行的特殊字符密度
        line_scores = []
        has_mojibake_chars = False
        
        for i, line in enumerate(lines):
            score = 0
            
            # 计算特殊字符数量
            for pattern in self.special_char_patterns:
                matches = re.findall(pattern, line)
                score += len(matches)
            
            # 检查是否真的有乱码特征
            if self._text_has_mojibake(line):
                has_mojibake_chars = True
                score += 10  # 确认乱码的行给高分
       
            line_scores.append((i, score, line))
        
        # 如果没有检测到乱码特征, 返回空列表（无乱码）
        if not has_mojibake_chars:
            return True, []
        
        # 按特殊字符密度排序, 选择得分最高的n行
        line_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 只选择有特殊字符的行, 返回行内容（行号作为debug信息）
        mojibake_lines = []
        for line_num, score, line in line_scores:
            if score > 0 and len(mojibake_lines) < n:
                self.logger.debug(f"乱码行 {line_num+1}: {line.strip()[:50]}...")
                mojibake_lines.append(line)
        
        return True, mojibake_lines

    def _text_has_mojibake(self, text: str) -> bool:
        """
        检查文本是否有乱码（基于文本内容）
        """
        if not text:
            return False

        for pattern in self.mojibake_patterns:
            if re.search(pattern, text):
                return True

        return False

    def generate_type1_encodings(self, file_path: str, max_priority: int = 2) -> bool:
        """
        强制使用一型乱码方式生成所有编码文件
        为每种编码生成一个文件到新建的文件夹中
        
        参数:
            file_path: 原始文件路径
            max_priority: 最大优先级 (1, 2, 或 3), 默认为2
        返回:
            bool: 是否成功生成文件
        """
        try:
            # 获取指定优先级的编码列表
            encodings_to_use = self.get_encodings_by_priority(max_priority)
            
            # 创建输出文件夹
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = f"{base_name}_type1_encodings"
            os.makedirs(output_dir, exist_ok=True)
            
            self.logger.info(f"创建一型编码文件夹: {output_dir}")
            self.logger.info(f"使用优先级1-{max_priority}的编码: {encodings_to_use}")
            
            success_count = 0
            
            # 尝试每种编码读取原文件
            for encoding in encodings_to_use:
                try:
                    # 尝试用当前编码读取文件
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    
                    # 生成输出文件名
                    output_file = os.path.join(output_dir, f"{base_name}_{encoding}.txt")
                    
                    # 保存为UTF-8编码
                    with open(output_file, 'w', encoding='utf-8', newline='') as f:
                        f.write(content)
                    
                    # 检查中文字符数量作为质量指标
                    chinese_count = len(self.chinese_pattern.findall(content))
                    has_mojibake = self._text_has_mojibake(content)
                    
                    self.logger.info(f"一型编码 {encoding:12}: 中文字符={chinese_count:3}, 有乱码={has_mojibake}, 文件={output_file}")
                    success_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"一型编码 {encoding:12}: 读取失败 - {e}")
                    
            self.logger.info(f"一型编码生成完成: 成功{success_count}/{len(encodings_to_use)}个文件")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"生成一型编码文件失败: {e}")
            return False

    def generate_type2_encodings(self, file_path: str, max_priority: int = 2) -> bool:
        """
        强制使用二型乱码方式生成所有编码组合文件
        为每种编码链组合生成一个文件到新建的文件夹中
        
        参数:
            file_path: 原始文件路径
            max_priority: 最大优先级 (1, 2, 或 3), 默认为2
        返回:
            bool: 是否成功生成文件
        """
        try:
            # 读取原始字节数据
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # 获取指定优先级的编码列表
            encodings_to_use = self.get_encodings_by_priority(max_priority)
            
            # 创建输出文件夹
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = f"{base_name}_type2_encoding_chains"
            os.makedirs(output_dir, exist_ok=True)
            
            self.logger.info(f"创建二型编码链文件夹: {output_dir}")
            self.logger.info(f"使用优先级1-{max_priority}的编码: {encodings_to_use}")
            
            success_count = 0
            
            # 生成第一优先级的排列组合（去除三个都重复的情况）
            priority1_chains = []
            for enc1 in self.priority1_encodings:
                for enc2 in self.priority1_encodings:
                    for enc3 in self.priority1_encodings:
                        # 排除三个都相同的情况
                        if not (enc1 == enc2 == enc3):
                            priority1_chains.append((enc1, enc2, enc3))
            
            # 常见的跨优先级编码链组合
            cross_priority_chains = []
            if max_priority >= 2:
                # 添加一些经过验证的跨优先级组合
                cross_priority_chains.extend([
                    ('gb2312', 'latin1', 'utf-8')
                ])
                
                # 生成更多组合
                for enc1 in encodings_to_use:
                    for enc2 in ['latin1', 'windows-1252']:
                        for enc3 in self.priority1_encodings + self.priority2_encodings[:1]:  # 只取gb2312
                            chain = (enc1, enc2, enc3)
                            if chain not in cross_priority_chains and chain not in priority1_chains:
                                cross_priority_chains.append(chain)
            
            # 合并所有链
            all_chains = priority1_chains + cross_priority_chains
            
            # 去重并限制数量
            unique_chains = []
            seen_chains = set()
            for chain in all_chains:
                if chain not in seen_chains and len(unique_chains) < 50:  # 限制最大数量
                    unique_chains.append(chain)
                    seen_chains.add(chain)
            
            self.logger.info(f"总共生成 {len(unique_chains)} 个编码链组合")
            
            # 测试每个编码链
            for i, chain in enumerate(unique_chains):
                try:
                    # 尝试逆向编码链: decode(chain[2]) -> encode(chain[1]) -> decode(chain[0])
                    step1 = raw_data.decode(chain[2], errors='ignore')
                    step2 = step1.encode(chain[1], errors='ignore')
                    recovered_text = step2.decode(chain[0], errors='ignore')
                    
                    # 生成输出文件名
                    chain_name = "_".join(chain)
                    output_file = os.path.join(output_dir, f"{base_name}_{chain_name}.txt")
                    
                    # 保存恢复的文本
                    with open(output_file, 'w', encoding='utf-8', newline='') as f:
                        f.write(recovered_text)
                    
                    # 检查恢复质量
                    chinese_count = len(self.chinese_pattern.findall(recovered_text))
                    has_mojibake = self._text_has_mojibake(recovered_text)
                    
                    quality = "优" if chinese_count > 10 and not has_mojibake else "差" if has_mojibake else "中"
                    
                    self.logger.info(f"二型编码链 {i+1:2}/{len(unique_chains)} {chain_name:30}: 中文字符={chinese_count:3}, 有乱码={has_mojibake}, 质量={quality}")
                    success_count += 1
                    
                except Exception as e:
                    chain_name = "_".join(chain)
                    self.logger.warning(f"二型编码链 {i+1:2}/{len(unique_chains)} {chain_name:30}: 处理失败 - {e}")
                    
            self.logger.info(f"二型编码链生成完成: 成功{success_count}/{len(unique_chains)}个文件")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"生成二型编码链文件失败: {e}")
            return False


def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='通用编码检测和修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 添加位置参数
    parser.add_argument('file_path', help='要处理的文件路径')
    
    # 添加可选参数
    parser.add_argument('--analyze', action='store_true', 
                       help='只分析不修复')
    parser.add_argument('--output', type=str, 
                       help='指定输出文件路径')
    parser.add_argument('--no-backup', action='store_true', 
                       help='不创建备份文件')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='显示详细日志')
    parser.add_argument('--force-type1', action='store_true',
                       help='强制使用一型乱码方式生成所有编码文件到新建文件夹')
    parser.add_argument('--force-type2', action='store_true',
                       help='强制使用二型乱码方式生成所有编码组合文件到新建文件夹')
    parser.add_argument('--priority', type=int, choices=[1, 2, 3], default=2,
                       help='编码优先级 (1=仅第一优先级, 2=前两个优先级, 3=所有优先级), 默认为2')
    
    # 解析参数
    args = parser.parse_args()
    
    # 创建修复器
    fixer = FileEncodingFixer()
    
    # 设置日志级别
    if args.verbose:
        fixer.logger.setLevel(logging.DEBUG)
    
    # 检查互斥参数
    if args.force_type1 and args.force_type2:
        fixer.logger.error("--force-type1 和 --force-type2 不能同时使用")
        return
    
    # 初始化编码优先级（系统检测 + 乱码分析）
    fixer.init_possible_encodings(args.file_path)
    
    # 处理强制生成编码文件的选项
    if args.force_type1:
        fixer.logger.info(f"强制使用一型乱码方式生成编码文件 (优先级1-{args.priority})")
        fixer.logger.info("=" * 50)
        success = fixer.generate_type1_encodings(args.file_path, args.priority)
        if success:
            fixer.logger.info("一型编码文件生成成功!")
        else:
            fixer.logger.error("一型编码文件生成失败!")
        return
    
    if args.force_type2:
        fixer.logger.info(f"强制使用二型乱码方式生成编码组合文件 (优先级1-{args.priority})")
        fixer.logger.info("=" * 50)
        success = fixer.generate_type2_encodings(args.file_path, args.priority)
        if success:
            fixer.logger.info("二型编码链文件生成成功!")
        else:
            fixer.logger.error("二型编码链文件生成失败!")
        return
    
    # 分析文件
    fixer.logger.info(f"开始分析文件: {args.file_path}")
    fixer.logger.info("=" * 50)
    
    # 使用新的编码检测和修复流程
    if not args.analyze:
        fixer.logger.info("正常的编码修复功能尚未完整实现")
        fixer.logger.info("请使用 --force-type1 或 --force-type2 选项生成编码文件")
        fixer.logger.info("然后手动选择最佳的编码结果")
    else:
        fixer.logger.info("编码分析完成，请查看上述编码优先级信息")

if __name__ == "__main__":
    main()
