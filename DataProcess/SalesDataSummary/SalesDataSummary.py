import os
import json
import pandas as pd


class SalesDataSummary:
    def __init__(self):
        """
        初始化类变量，从固定的 JSON 配置文件加载
        """
        # 默认配置
        default_config = {
            "input_file": "input.xlsx",
            "output_file_name": "summary_output.xlsx",
            "sheet_name": "Sheet1",
            "months": ["1月", "2月"],
            "group_columns": ["省份", "销售代表", "大类"],
            "agg_columns": {
                "2023金额": "sum",
                "2024金额": "sum"
            },
            "output_columns_map": {
                "省份": "省份",
                "销售代表": "姓名",
                "大类": "大类",
                "2023金额": "2023年1-2月累计金额",
                "2024金额": "2024年1-2月累计金额"
            },
            "depart_name": "销售部"
        }

        config_file = 'config.json'  # 固定的配置文件名

        # 尝试从配置文件加载
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"Warning: 配置文件 '{config_file}' 不存在，使用默认配置。")
            config = default_config
        except json.JSONDecodeError:
            print(f"Warning: 配置文件 '{config_file}' 格式错误，使用默认配置。")
            config = default_config
        """
        初始化类变量: 从配置加载参数
        :param input_file: 输入的Excel文件路径
        :param sheet_name: 数据所在的sheet名称
        :param months: 筛选的月份范围
        :param group_columns: 用于分组的列名列表
        :param agg_columns: 需要汇总的列及对应的汇总方法，字典形式
        :param output_columns_map: 输出表中各列对应关系及其新列名，字典形式
        """
        self.input_file = config.get('input_file', default_config['input_file'])
        self.output_file_name = config.get('output_file_name', default_config['output_file_name'])
        self.sheet_name = config.get('sheet_name', default_config['sheet_name'])
        self.months = config.get('months', default_config['months'])
        self.group_columns = config.get('group_columns', default_config['group_columns'])
        self.agg_columns = config.get('agg_columns', default_config['agg_columns'])
        self.output_columns_map = config.get('output_columns_map', default_config['output_columns_map'])
        self.depart_name = config.get('depart_name', default_config['depart_name'])

    def read_check_data(self) -> bool:
        """
        读取Excel文件并检查必要条件
        :return: 是否通过检查，布尔值
        """
        # 检查输入文件是否存在
        if not os.path.exists(self.input_file):
            print(f"Error: Input file '{self.input_file}' does not exist.")
            return False

        # 尝试读取数据
        try:
            self.df = pd.read_excel(self.input_file, sheet_name=self.sheet_name)
        except Exception as e:
            print(f"Error: Unable to read '{self.sheet_name}' from file '{self.input_file}'.\n{e}")
            return False

        # 检查是否包含必要的列
        missing_columns = [col for col in self.output_columns_map.keys()
                           if col not in self.df.columns]
        if missing_columns:
            print(f"Error: The following required columns are missing: {missing_columns}")
            return False

        self.df.dropna(how='all', inplace=True)             # 删除全NA的行
        self.df.dropna(how='all', axis=1, inplace=True)     # 删除全NA的列
        return True

    def filter_data(self):
        """筛选指定月份的数据"""
        self.df_filtered = self.df[self.df['月份'].isin(self.months)]

    def group_and_aggregate(self):
        """按指定列分组并汇总数据"""
        self.df_grouped = self.df_filtered.groupby(self.group_columns).agg(self.agg_columns).reset_index()

    def check_or_create_output_file(self):
        """检查输出文件是否存在，并准备基础表格"""
        if os.path.exists(self.output_file_name):
            # 文件存在，加载数据
            self.output_df = pd.read_excel(self.output_file_name)

            if not self.output_df.empty:
                self.output_df.dropna(how='all', inplace=True)  # 删除全NA的行
                self.df.dropna(how='all', axis=1, inplace=True)     # 删除全NA的列

            # 检查是否缺失列
            for new_col in self.output_columns_map.values():
                if new_col not in self.output_df.columns:
                    self.output_df[new_col] = None  # 创建缺失列
                    print(f"Warning: Output column '{new_col}' not found in {self.output_file_name}. Column created.")
        else:
            # 文件不存在，创建一个空表
            print(f"Warning: {self.output_file_name} does not exist. Creating a new file.")
            self.output_df = pd.DataFrame(columns=self.output_columns_map.values())

    def prepare_output(self):
        """准备输出表格数据"""
        self.df_summary = self.df_grouped.copy()
        self.df_summary.rename(columns=self.output_columns_map, inplace=True)

    def update_output_file(self):
        """更新输出文件内容"""
        # 检查是否为空
        if self.df_summary.empty:
            print("Warning: No data to update. Skipping update.")
            return

        # 确保 df_summary 和 output_df 列名一致
        missing_cols = [col for col in self.output_df.columns if col not in self.df_summary.columns]
        for col in missing_cols:
            self.df_summary[col] = None  # 补充缺失列

        # 按 output_df 的列顺序重新排列 df_summary
        all_columns = list(self.output_df.columns)  # 原有列的顺序
        self.df_summary = self.df_summary.reindex(columns=all_columns)

        if self.output_df.empty:
            self.output_df = self.df_summary.copy()
            return

        # 检查是否有重复数据（避免重复拼接）
        combined_df = pd.concat([self.output_df, self.df_summary], ignore_index=True)
        self.output_df = combined_df.drop_duplicates()

    def save_to_excel(self):
        """保存结果到Excel文件"""
        if '部门' in self.output_df.columns:
            self.output_df['部门'] = self.depart_name
        else:
            print("Warning: '部门' not found in output file. Skipping add department.")

        self.output_df.to_excel(self.output_file_name, index=False)
        print(f"汇总结果已保存到 {self.output_file_name}")

    def run(self):
        """执行数据处理的完整流程"""
        if not self.read_check_data():
            return  # 如果检查失败，直接返回
        self.filter_data()
        self.group_and_aggregate()
        self.check_or_create_output_file()
        self.prepare_output()
        self.update_output_file()
        self.save_to_excel()


# 使用示例
if __name__ == "__main__":
    summarizer = SalesDataSummary()
    summarizer.run()
