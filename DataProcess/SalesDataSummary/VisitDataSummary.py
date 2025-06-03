"""
    ===========================README============================
    create date:    20250530
    change date:    20250603
    creator:        zhengxu

    function:       1. 统计访问次数表

    version:        beta0.5
    updates:

        details:    1. group_columns是数据表合并后的保留的列
                    2. filter_col是数据表合并后的过滤列
                    3. output_suffix是输出文件的名称后缀
                    4. 如果input_files为空, 则自动查找当前目录下的所有xlsx文件
                       如果input_files不为空, 则使用input_files中的文件
                       如果input_files中的文件不存在, 则报错
"""
# =========================用到的库==========================
import os
import json
import pandas as pd
from datetime import datetime
import concurrent.futures
import glob


# =========================================================
# =======               excel处理类                =========
# =========================================================
class VisitDataSummary:
    def __init__(self):
        """
        初始化类变量, 从固定的 JSON 配置文件加载
        """
        # 尝试从配置文件加载
        config_file = "visit_config.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Error: 配置文件 '{config_file}' 不存在或格式错误。")
            return

        # 配置参数
        self.group_columns = config.get('group_columns', [])
        self.filter_col = config.get('filter_col')
        self.output_suffix = config.get('output_suffix', '访问次数统计')

        # 设置输入文件列表
        input_files = config.get('input_files', [])
        if input_files:
            self.input_files = input_files
        else:
            self.input_files = self._find_excel_files()

    def _find_excel_files(self):
        """
        查找当前目录下的所有xlsx文件，排除已生成的访问次数文件
        """
        all_excel_files = glob.glob("*.xlsx")
        return [f for f in all_excel_files if not f.endswith(f"_{self.output_suffix}.xlsx")]

    def _check_file(self, file_path: str) -> bool:
        """检查文件是否存在"""
        if not os.path.exists(file_path):
            print(f"Error: 文件 '{file_path}' 不存在。")
            return False
        return True

    def _count_by_group(self, df_filtered: pd.DataFrame, input_file: str) -> bool:
        """
        按医院和科室分组统计访问次数并保存结果
        """
        # 按分组统计访问次数
        df_summary = (
            df_filtered
            .groupby(self.group_columns + [self.filter_col])
            .size()
            .reset_index(name='访问次数')
        )

        # 保存结果
        if df_summary.empty:
            print(f"Warning: 文件 '{input_file}' 无有效数据, 不生成访问次数统计文件。")
            return False

        output_file = input_file.replace('.xlsx', f'_{self.output_suffix}.xlsx')
        df_summary.to_excel(output_file, index=False)
        print(f"访问次数统计结果已保存到: {output_file}")
        return True

    def _count_by_month(self, df_filtered: pd.DataFrame, input_file: str) -> bool:
        """
        按月统计医院数量、科室数量和访问次数并保存结果
        """
        # 按月份分组统计
        monthly_stats = df_filtered.groupby(self.filter_col).agg({
            self.group_columns[0]: 'nunique',
            self.group_columns[1]: 'nunique',
            self.filter_col: 'count'
        }).rename(columns={
            self.group_columns[0]: f"{self.group_columns[0]}个数",
            self.group_columns[1]: f"{self.group_columns[1]}个数",
            self.filter_col: '拜访次数'
        })

        df_summary = monthly_stats.reset_index()

        # 保存结果
        if df_summary.empty:
            print(f"Warning: 文件 '{input_file}' 无有效数据, 不生成月度统计文件。")
            return False

        output_file = input_file.replace('.xlsx', f'_{self.output_suffix}.xlsx')
        df_summary.to_excel(output_file, index=False)
        print(f"月度统计结果已保存到: {output_file}")
        return True

    def _process_single_file(self, input_file: str) -> bool:
        """
        处理单个Excel文件并保存结果
        返回处理是否成功
        """
        # 文件检查
        if not self._check_file(input_file):
            return False

        # 读数据表
        try:
            df_input = pd.read_excel(input_file)
        except Exception as e:
            print(f"Error: 无法读取数据表 '{input_file}'\n{e}")
            return False

        # 检查必要的列是否存在
        required_cols = self.group_columns + [self.filter_col]
        missing_cols = [col for col in required_cols if col not in df_input.columns]
        if missing_cols:
            print(f"Error: 数据表 '{input_file}' 缺少必要的列: {missing_cols}")
            return False

        # 清理空行、空列
        df_filtered = df_input.copy()
        df_filtered.dropna(how='all', inplace=True)
        df_filtered.dropna(how='all', axis=1, inplace=True)

        # 将反馈时间转换为日期格式
        df_filtered[self.filter_col] = pd.to_datetime(df_filtered[self.filter_col])

        # 将日期转换为年月格式 (YYYY.MM)
        df_filtered[self.filter_col] = df_filtered[self.filter_col].dt.strftime('%Y.%m')

        # 生成统计结果
        # success = self._count_by_group(df_filtered, input_file)
        success = self._count_by_month(df_filtered, input_file)

        return success

    def run(self):
        """执行数据处理的完整流程"""
        if not self.input_files:
            print("Error: 没有找到需要处理的Excel文件。")
            return

        # 使用线程池处理多个文件
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 创建任务列表
            future_to_file = {
                executor.submit(self._process_single_file, input_file): input_file
                for input_file in self.input_files
            }

            # 处理每个文件的结果
            for future in concurrent.futures.as_completed(future_to_file):
                input_file = future_to_file[future]
                try:
                    success = future.result()
                    if not success:
                        print(f"Warning: 文件 '{input_file}' 处理失败")
                except Exception as e:
                    print(f"Error: 处理文件 '{input_file}' 时发生错误: {e}")


# ============== 使用示例 ==============
if __name__ == "__main__":
    summarizer = VisitDataSummary()
    summarizer.run()
