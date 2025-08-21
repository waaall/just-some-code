#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乱码有两种情况: 我称之为一型和二型。
    1. 原始编码可能为encoding_init(gbk或者gb2312), 被错误的解码decoding(比如utf8或者Latin-1)就会乱码;
       这时候检测encoding然后统一重编码为utf8(文件没有被错误编码, 也就是encoding_init==encoding_end); 再按照utf8 decoding(这都是默认)
    2. 原始编码可能为encoding_init(gbk或者gb2312), 被错误地用encoding_mid(Latin-1或Windows-1252解码), 然后重编码为当前的encoding_end(可能是utf8或者是gb2312)

重写整个代码的思路:
    1. 检测文件默认编码类型
    2. 用默认编码读取示例行并检查乱码
    3. 根据不同情况判断乱码类型并修复:
       3.1 非UTF8编码: 与UTF8对比判断乱码类型
       3.2 UTF8编码: 通过charset_normalizer或遍历常用编码判断
    4. 二型乱码: 尝试三重编码链修复
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
            # 如果没有处理器，添加默认处理器
            if not self.logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger
            
        # 常见的编码列表, 按优先级排序
        self.common_encodings = ['utf-8', 'gbk', 'windows-1252', 'gb2312', 'latin1', 'big5']

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
                        self.logger.warning(f"file命令检测结果: {encoding} (编码错误)")
                        return None, 0.0
                    elif encoding == 'binary':
                        self.logger.warning(f"file命令检测结果: {encoding} (二进制文件)")
                        return None, 0.0
                    else:
                        self.logger.info(f"file命令检测结果: {encoding}")
                        
                        # 标准化编码名称
                        encoding_map = {
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
                        
                        normalized_encoding = encoding_map.get(encoding.lower(), encoding)
                        return normalized_encoding, 0.9  # file命令通常比较准确
                        
            self.logger.error(f"file命令执行失败: {result.stderr}")
            return None, 0.0
            
        except subprocess.TimeoutExpired:
            self.logger.error("file命令执行超时")
            return None, 0.0
        except FileNotFoundError:
            self.logger.error("未找到file命令，请确保系统已安装")
            return None, 0.0
        except Exception as e:
            self.logger.error(f"file命令执行出错: {e}")
            return None, 0.0

    def _try_alternative_encodings(self, file_path: str, exclude_encoding: str = None, 
                                   skip_utf8: bool = False) -> Tuple[int, str]:
        """
        尝试其他常用编码来读取文件
        参数:
            file_path: 文件路径
            exclude_encoding: 要排除的编码
            skip_utf8: 是否跳过UTF-8编码
        返回: (状态码, 内容)
        """
        for encoding in self.common_encodings:
            if encoding == exclude_encoding:
                continue  # 跳过指定排除的编码
            if skip_utf8 and encoding == 'utf-8':
                continue  # 跳过UTF-8
                
            try:
                success, mojibake_lines = self.detect_mojibake_lines(file_path, encoding)
                if success and len(mojibake_lines) == 0:  # 无乱码
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        self.logger.info(f"一型乱码: 找到合适编码 {encoding}")
                        return 1, content
                    except (UnicodeDecodeError, UnicodeError):
                        continue
            except Exception:
                continue
        
        # 所有编码都失败，使用charset_normalizer作为最后手段
        self.logger.info("所有常用编码都失败，使用charset_normalizer分析整个文件...")
        status_code, content = self._detect_file_encoding(file_path)
        return status_code, content

    def smart_decode(self, file_path: str) -> Tuple[int, str]:
        """
        智能解码文件
        
        整体逻辑流程：
        1. 系统编码检测阶段：
           - 使用系统 file --mime-encoding 命令检测文件编码
           - 如果检测失败(返回None)，跳过UTF-8，尝试其他常用编码
           
        2. 乱码检测阶段：
           - 使用检测到的系统编码读取文件并检测乱码行
           - 如果读取失败，尝试其他常用编码(排除系统编码)
           - 统计乱码行数量，判断是否存在乱码
           
        3. 分情况处理阶段：
           3.1 UTF-8编码情况：
               - 无乱码：直接读取返回(状态码0)，读取失败则尝试其他编码
               - 有乱码：基于乱码行检测原始编码，成功则读取返回(状态码1)
                        失败则尝试其他编码
           
           3.2 非UTF-8编码情况：
               - 无乱码：直接读取返回(状态码1)，读取失败则尝试其他编码
               - 有乱码：基于乱码行检测原始编码，成功则读取返回(状态码1)
                        失败则尝试其他编码
        
        4. 最终fallback阶段：
           - 如果以上所有步骤都失败，尝试其他常用编码
           - 最后使用charset_normalizer检测整个文件(可能返回状态码2)
        
        核心设计思想：
        - 一型乱码：文件编码正确，但被错误解释(encoding_init ≠ decoding)
        - 二型乱码：文件经过多重错误编码转换(encoding_init → encoding_mid → encoding_end)
        - 通过系统编码检测 + 乱码行分析 + 备选编码尝试的多层策略确保准确性
        
        参数:
            file_path: 文件路径
            
        返回: (状态码, 内容)
            状态码: 负数=错误, 0=无问题, 1=一型乱码, 2=二型乱码
            内容: 解码后的文件内容
        """
        
        # 1. 首先使用系统file命令检测文件编码
        sys_encoding, confidence = self.get_sys_file_encoding(file_path)
        
        # 如果没有系统默认的编码方式（有unknown字段）就按照默认不是utf8且有乱码处理
        if sys_encoding is None:
            self.logger.warning("file命令无法检测编码，按照非UTF-8且有乱码处理")
            # 尝试其他常用编码
            status_code, content = self._try_alternative_encodings(file_path, skip_utf8=True)
            return status_code, content
        
        self.logger.info(f"file命令检测到编码: {sys_encoding} (置信度: {confidence:.3f})")
        
        # 2. 检测是否有乱码
        try:
            success, detected_mojibake_lines = self.detect_mojibake_lines(file_path, sys_encoding)
            if not success:
                self.logger.warning(f"{sys_encoding}编码检测: 读取失败")
                # 读取失败，尝试其他编码
                status_code, content = self._try_alternative_encodings(file_path, exclude_encoding=sys_encoding)
                return status_code, content
            
            has_mojibake = len(detected_mojibake_lines) > 0
        except Exception as e:
            self.logger.warning(f"{sys_encoding}编码检测异常: {e}")
            has_mojibake = True  # 假设有乱码
        
        # 3. 根据编码类型和是否有乱码进行判断
        if sys_encoding == 'utf-8':
            if not has_mojibake:
                # 如果默认是utf8，且没乱码，0，跳过
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.logger.info("文件无编码问题: UTF-8无乱码")
                    return 0, content
                except (UnicodeDecodeError, UnicodeError):
                    self.logger.warning("UTF-8读取失败，尝试其他编码")
                    # UTF-8读取失败，尝试其他编码
                    status_code, content = self._try_alternative_encodings(file_path, exclude_encoding='utf-8')
                    return status_code, content
            else:
                # 如果默认是utf8有乱码，就调用乱码行匹配函数
                self.logger.info("UTF-8编码检测到乱码，尝试基于乱码行检测原始编码...")
                original_encoding, original_confidence = self._detect_mojibake_encoding(
                    file_path, detected_mojibake_lines, sys_encoding
                )
                
                if original_encoding and original_confidence > 0.6:
                    try:
                        with open(file_path, 'r', encoding=original_encoding) as f:
                            content = f.read()
                        self.logger.info(f"一型乱码: 找到原始编码 {original_encoding}")
                        return 1, content
                    except (UnicodeDecodeError, UnicodeError):
                        self.logger.warning(f"原始编码 {original_encoding} 读取失败")
                
                # 原始编码失败，尝试其他编码
                status_code, content = self._try_alternative_encodings(file_path, exclude_encoding='utf-8')
                return status_code, content
        else:
            if not has_mojibake:
                # 如果默认不是utf8，且没乱码，一型
                try:
                    with open(file_path, 'r', encoding=sys_encoding) as f:
                        content = f.read()
                    self.logger.info(f"一型乱码: {sys_encoding}编码无乱码")
                    return 1, content
                except (UnicodeDecodeError, UnicodeError):
                    self.logger.warning(f"{sys_encoding}编码读取失败")
                
                # 系统编码读取失败，尝试其他编码
                status_code, content = self._try_alternative_encodings(file_path, exclude_encoding=sys_encoding)
                return status_code, content
            else:
                # 非UTF-8且有乱码，尝试基于乱码行检测原始编码
                self.logger.info(f"{sys_encoding}编码检测到乱码，尝试基于乱码行检测原始编码...")
                original_encoding, original_confidence = self._detect_mojibake_encoding(
                    file_path, detected_mojibake_lines, sys_encoding
                )
                
                if original_encoding and original_confidence > 0.6:
                    try:
                        with open(file_path, 'r', encoding=original_encoding) as f:
                            content = f.read()
                        self.logger.info(f"一型乱码: 找到原始编码 {original_encoding}")
                        return 1, content
                    except (UnicodeDecodeError, UnicodeError):
                        self.logger.warning(f"原始编码 {original_encoding} 读取失败")
                
                # 原始编码失败，尝试其他编码
                status_code, content = self._try_alternative_encodings(file_path, exclude_encoding=sys_encoding)
                return status_code, content
        
        # 4. 如果以上都失败，尝试其他常用编码
        self.logger.info("尝试其他常用编码...")
        status_code, content = self._try_alternative_encodings(file_path, exclude_encoding=sys_encoding)
        return status_code, content

    def _detect_file_encoding(self, file_path: str) -> Tuple[int, str]:
        # 尝试用charset_normalizer检测整个文件
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            results = charset_normalizer.from_bytes(raw_data)
            
            self.logger.info(f"charset_normalizer检测结果: 共{len(results)}个候选编码")
            
            if results:
                # 打印详细调试信息
                self.logger.debug("候选编码详情:")
                try:
                    count = 0
                    for i, result in enumerate(results):
                        if count >= 5:  # 只显示前5个
                            break
                        self.logger.debug(f"  {i+1}. {result.encoding:12} 置信度: {result.coherence:.3f} "
                              f"语言: {result.language or 'N/A':8} 混乱度: {result.chaos:.3f}")
                        count += 1
                except Exception as e:
                    self.logger.error(f"显示候选编码详情失败: {e}")

                # 测试最佳候选编码
                try:
                    best_result = results.best()
                    if best_result:
                        self.logger.info(f"最佳候选: {best_result.encoding} (置信度: {best_result.coherence:.3f})")
                        
                        if best_result.coherence >= self.confidence_threshold:
                            try:
                                with open(file_path, 'r', encoding=best_result.encoding) as f:
                                    content = f.read()
                                self.logger.info(f"一型乱码:最佳候选 {best_result.encoding} 读取成功")
                                return 1, content
                            except (UnicodeDecodeError, UnicodeError):
                                self.logger.warning(f"二型乱码:最佳候选 {best_result.encoding} 读取失败")
                                return 2, ""

                        # 置信度低或读取失败 -> 二型乱码
                        self.logger.info("二型乱码:置信度低或读取失败")
                        return 2, ""
                    else:
                        self.logger.info("二型乱码:未找到最佳候选")
                        return 2, ""
                except Exception as e:
                    self.logger.error(f"二型乱码:处理最佳候选编码失败: {e}")
                    return 2, ""
            else:
                self.logger.info("二型乱码:charset_normalizer未检测到有效编码")
                return 2, ""
                
        except Exception as e:
            self.logger.error(f"二型乱码:charset_normalizer检测失败: {e}")
            return 2, ""

    def fix_encoding(self, file_path: str, status_code: int, content: str, 
                     output_path: str = None, create_backup: bool = True) -> bool:
        """
        修复文件编码问题
        参数:
            file_path: 文件路径
            status_code: smart_decode返回的状态码
            content: smart_decode返回的内容
            output_path: 输出路径
            create_backup: 是否创建备份
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        # 创建备份
        if create_backup and output_path is None:
            backup_path = file_path + '.backup'
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"已创建备份: {backup_path}")
        
        if output_path is None:
            output_path = file_path
                
        if status_code == 0:
            # 无编码问题，直接保存
            try:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)
                self.logger.info(f"文件无编码问题，已保存: {output_path}")
                return True
            except Exception as e:
                self.logger.error(f"保存文件失败: {e}")
                return False
                
        elif status_code == 1:
            # 一型乱码，重编码为UTF-8
            try:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)
                self.logger.info(f"一型乱码修复成功，已保存为UTF-8编码: {output_path}")

                # 验证结果
                chinese_count = len(self.chinese_pattern.findall(content))
                self.logger.info(f"验证: 检测到 {chinese_count} 个中文字符")
                return True

            except Exception as e:
                self.logger.error(f"保存文件失败: {e}")
                return False

        elif status_code == 2:
            # 二型乱码，需要三重编码链修复
            self.logger.info("检测到二型乱码，尝试修复...")
            
            try:
                # 读取原始字节数据
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                
                # 尝试修复
                recovered_text = self._double_encoding_fix(raw_data)
                
                if recovered_text:
                    # 保存修复结果
                    with open(output_path, 'w', encoding='utf-8', newline='') as f:
                        f.write(recovered_text)
                    
                    # 验证结果
                    chinese_count = len(self.chinese_pattern.findall(recovered_text))
                    self.logger.info(f"二型乱码修复成功，已保存: {output_path}")
                    self.logger.info(f"验证: 检测到 {chinese_count} 个中文字符")
                    return True
                else:
                    self.logger.error("二型乱码修复失败")
                    return False
                    
            except Exception as e:
                self.logger.error(f"二型乱码修复过程出错: {e}")
                return False

        else:
            # 错误情况
            self.logger.error("文件处理失败，状态码错误")
            return False

    def _detect_mojibake_encoding(self, file_path: str, mojibake_lines: List[str], current_encoding: str) -> Tuple[str, float]:
        """
        基于已知的乱码行和当前编码，检测原始编码
        参数: 
            file_path - 文件路径
            mojibake_lines - List[str] 乱码行内容列表
            current_encoding - 当前读取文件使用的编码
        返回: (原始编码名称, 置信度)
        """
        if not mojibake_lines:
            return None, 0.0
            
        try:
            # 将乱码行重新编码为字节，然后尝试用不同编码解码
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
            
            # 安全地遍历结果，避免切片操作
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
            
            # 如果没有找到理想的编码，返回最佳候选
            best_result = results.best()
            if best_result and best_result.coherence >= 0.5:
                self.logger.info(f"未找到理想编码，返回最佳候选: {best_result.encoding} (置信度: {best_result.coherence:.3f})")
                return best_result.encoding, best_result.coherence

        # 如果charset_normalizer失败，尝试常见编码
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
            mojibake_lines: 乱码行列表，空列表表示无乱码
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
        
        # 如果没有检测到乱码特征，返回空列表（无乱码）
        if not has_mojibake_chars:
            return True, []
        
        # 按特殊字符密度排序，选择得分最高的n行
        line_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 只选择有特殊字符的行，返回行内容（行号作为debug信息）
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

    def _double_encoding_fix(self, raw_data: bytes) -> str:
        """
        尝试修复二型乱码（三重编码链）
        参数: raw_data - 文件的原始字节数据
        返回: 修复后的文本内容，如果修复失败返回空字符串
        """
        self.logger.info("尝试二型乱码修复（三重编码链）...")
        
        # 常见的双重编码错误组合（减少搜索空间）
        common_chains = [
            ('gb2312', 'utf-8', 'utf-8'),     # GB2312 -> Latin1 -> UTF8
            ('gbk', 'latin1', 'utf-8'),        # GBK -> Latin1 -> UTF8
            ('gb2312', 'windows-1252', 'utf-8'), # GB2312 -> CP1252 -> UTF8
            ('gbk', 'windows-1252', 'utf-8'),   # GBK -> CP1252 -> UTF8
            ('utf-8', 'latin1', 'gb2312'),     # UTF8 -> Latin1 -> GB2312
            ('utf-8', 'latin1', 'gbk'),        # UTF8 -> Latin1 -> GBK
            ('utf-8', 'windows-1252', 'gb2312'), # UTF8 -> CP1252 -> GB2312
            ('utf-8', 'windows-1252', 'gbk'),   # UTF8 -> CP1252 -> GBK
        ]
        
        # 首先尝试常见组合
        for chain in common_chains:
            try:
                # 尝试逆向编码链: decode(chain[2]) -> encode(chain[1]) -> decode(chain[0])
                step1 = raw_data.decode(chain[2], errors='ignore')
                step2 = step1.encode(chain[1], errors='ignore')
                recovered_text = step2.decode(chain[0], errors='ignore')
                
                # 检查恢复的文本是否无乱码
                if not self._text_has_mojibake(recovered_text):
                    # 检查是否包含中文字符（如果是中文文件）
                    chinese_count = len(self.chinese_pattern.findall(recovered_text))
                    if chinese_count > 0:  # 找到包含中文的正确解码
                        self.logger.info(f"找到有效的编码链: {' -> '.join(chain)}")
                        self.logger.info(f"恢复的中文字符数: {chinese_count}")
                        return recovered_text
                        
            except (UnicodeDecodeError, UnicodeEncodeError, Exception):
                continue
        
        # 如果常见组合失败，尝试更多组合（但限制数量）
        self.logger.info("常见编码链失败，尝试更多组合...")
        tried_count = 0
        max_tries = 100  # 限制尝试次数
        
        for chain in itertools.permutations(self.common_encodings, 3):
            if chain in common_chains:
                continue  # 跳过已经尝试过的
                
            tried_count += 1
            if tried_count > max_tries:
                break
                
            try:
                # 尝试逆向编码链
                step1 = raw_data.decode(chain[2], errors='ignore')
                step2 = step1.encode(chain[1], errors='ignore')
                recovered_text = step2.decode(chain[0], errors='ignore')
                
                # 检查恢复的文本质量
                if not self._text_has_mojibake(recovered_text):
                    chinese_count = len(self.chinese_pattern.findall(recovered_text))
                    if chinese_count > 10:  # 提高中文字符要求
                        self.logger.info(f"找到有效的编码链: {' -> '.join(chain)}")
                        self.logger.info(f"恢复的中文字符数: {chinese_count}")
                        return recovered_text
                        
            except (UnicodeDecodeError, UnicodeEncodeError, Exception):
                continue
                
        self.logger.warning("未找到有效的三重编码链")
        return ""

    def generate_type1_files(self, file_path: str) -> bool:
        """
        强制使用一型乱码方式生成所有编码文件
        为每种编码生成一个文件到新建的文件夹中
        
        参数:
            file_path: 原始文件路径
        返回:
            bool: 是否成功生成文件
        """
        try:
            # 创建输出文件夹
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = f"{base_name}_type1_encodings"
            os.makedirs(output_dir, exist_ok=True)
            
            self.logger.info(f"创建一型编码文件夹: {output_dir}")
            
            success_count = 0
            
            # 尝试每种编码读取原文件
            for encoding in self.common_encodings:
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
                    
            self.logger.info(f"一型编码生成完成: 成功{success_count}/{len(self.common_encodings)}个文件")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"生成一型编码文件失败: {e}")
            return False

    def generate_type2_files(self, file_path: str) -> bool:
        """
        强制使用二型乱码方式生成所有编码组合文件
        为每种编码链组合生成一个文件到新建的文件夹中
        
        参数:
            file_path: 原始文件路径
        返回:
            bool: 是否成功生成文件
        """
        try:
            # 读取原始字节数据
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # 创建输出文件夹
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = f"{base_name}_type2_encoding_chains"
            os.makedirs(output_dir, exist_ok=True)
            
            self.logger.info(f"创建二型编码链文件夹: {output_dir}")
            
            success_count = 0
            
            # 常见的编码链组合
            common_chains = [
                ('gb2312', 'latin1', 'utf-8'),
                ('gbk', 'latin1', 'utf-8'),
                ('gb2312', 'windows-1252', 'utf-8'),
                ('gbk', 'windows-1252', 'utf-8'),
                ('utf-8', 'latin1', 'gb2312'),
                ('utf-8', 'latin1', 'gbk'),
                ('utf-8', 'windows-1252', 'gb2312'),
                ('utf-8', 'windows-1252', 'gbk'),
            ]
            
            # 生成更多编码链组合（限制数量避免过多文件）
            additional_chains = []
            for enc1 in self.common_encodings[:4]:  # 只用前4个编码
                for enc2 in ['latin1', 'windows-1252', 'utf-8']:
                    for enc3 in ['utf-8', 'gbk', 'gb2312']:
                        chain = (enc1, enc2, enc3)
                        if chain not in common_chains and len(additional_chains) < 20:
                            additional_chains.append(chain)
            
            all_chains = common_chains + additional_chains
            
            # 测试每个编码链
            for i, chain in enumerate(all_chains):
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
                    
                    self.logger.info(f"二型编码链 {i+1:2}/{len(all_chains)} {chain_name:30}: 中文字符={chinese_count:3}, 有乱码={has_mojibake}, 质量={quality}")
                    success_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"二型编码链 {i+1:2}/{len(all_chains)} {chain_name:30}: 处理失败 - {e}")
                    
            self.logger.info(f"二型编码链生成完成: 成功{success_count}/{len(all_chains)}个文件")
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
    
    # 处理强制生成编码文件的选项
    if args.force_type1:
        fixer.logger.info("强制使用一型乱码方式生成所有编码文件")
        fixer.logger.info("=" * 50)
        success = fixer.generate_type1_files(args.file_path)
        if success:
            fixer.logger.info("一型编码文件生成成功!")
        else:
            fixer.logger.error("一型编码文件生成失败!")
        return
    
    if args.force_type2:
        fixer.logger.info("强制使用二型乱码方式生成所有编码组合文件")
        fixer.logger.info("=" * 50)
        success = fixer.generate_type2_files(args.file_path)
        if success:
            fixer.logger.info("二型编码链文件生成成功!")
        else:
            fixer.logger.error("二型编码链文件生成失败!")
        return
    
    # 分析文件
    fixer.logger.info(f"开始分析文件: {args.file_path}")
    fixer.logger.info("=" * 50)
    
    # 解码
    status_code, content = fixer.smart_decode(args.file_path)
    
    if not args.analyze:
        # 修复文件
        success = fixer.fix_encoding(args.file_path, status_code, content, 
                                args.output, create_backup=not args.no_backup)
        if success:
            fixer.logger.info("文件处理成功!")
        else:
            fixer.logger.error("文件处理失败!")

if __name__ == "__main__":
    main()
