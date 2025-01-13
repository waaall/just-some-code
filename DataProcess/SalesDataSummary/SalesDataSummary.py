
"""
    ===========================README============================
    create date:    20250108
    change date:    20250109
    creator:        zhengxu

    function:       1. 统计销售数据表
                    2. 核对花名册补充/删除信息

    version:        beta0.2
    updates:

    details:        1. input_file是数据表, sheet_name是数据表中需要的子表名, index_file是花名册
                    2. role_groups/group_columns/agg_columns是数据表合并后的保留的列
                    3. role_groups是有优先级的, 在前面存在的, 后面不考虑
                    4. agg_columns就是数据表中的合并项, 其必须存在于output_cols_map和数据表的列名中
                    5. output_cols_map后者是输出表中需要填写的列名,前者是input_file和index_file对应的列名
                    6. output_cols_map中的前几个列名最好不要改

"""
# =========================用到的库==========================
import os
import json
import pandas as pd


# =========================================================
# =======               excel处理类                =========
# =========================================================
class SalesDataSummary:
    def __init__(self):
        """
        初始化类变量, 从固定的 JSON 配置文件加载
        """
        default_config = {
            "input_file": "input.xlsx",
            "index_file": "index.xlsx",
            "output_file_name": "summary_output.xlsx",
            "sheet_name": "Sheet1",
            "filter_cols": {"月份": ["1月", "2月"]},
            "role_groups": ["销售主管", "销售代表"],
            "group_columns": ["大类"],
            "agg_columns": {
                "2023金额": "sum",
                "2024金额": "sum"},
            "output_cols_map": {
                "部门": "部门",
                "区域": "区域",
                "姓名": "姓名",
                "职务/岗位": "职务/岗位",
                "大类": "大类",
                "2023金额": "2023年1-2月累计金额",
                "2024金额": "2024年1-2月累计金额"}
        }
        # 尝试从配置文件加载
        config_file = "config.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Warning: 配置文件 '{config_file}' 不存在或格式错误, 使用默认配置。")
            config = default_config
        # 配置参数
        self.input_file = config.get('input_file', default_config['input_file'])
        self.index_file = config.get('index_file', default_config['index_file'])
        self.output_file_name = config.get('output_file_name', default_config['output_file_name'])
        self.sheet_name = config.get('sheet_name', default_config['sheet_name'])

        self.filter_cols = config.get('filter_cols', default_config['filter_cols'])
        self.role_groups = config.get('role_groups', default_config['role_groups'])
        self.group_columns = config.get('group_columns', default_config['group_columns'])
        self.agg_columns = config.get('agg_columns', default_config['agg_columns'])
        self.output_cols_map = config.get('output_cols_map', default_config['output_cols_map'])

    def _check_file(self, file_path: str) -> bool:
        """检查文件是否存在"""
        if not os.path.exists(file_path):
            print(f"Error: 文件 '{file_path}' 不存在。")
            return False
        return True

    def read_check_data(self) -> bool:
        """
        读取信息表和花名册, 并做基础检查
        """
        # 文件检查
        if (not self._check_file(self.input_file)) or (not self._check_file(self.index_file)):
            return False

        # 读信息表
        try:
            self.df_input = pd.read_excel(self.input_file, sheet_name=self.sheet_name)
        except Exception as e:
            print(f"Error: 无法读取信息表 '{self.input_file}' / sheet='{self.sheet_name}'\n{e}")
            return False
        # 清理空行、空列
        self.df_input.dropna(how='all', inplace=True)
        self.df_input.dropna(how='all', axis=1, inplace=True)

        # 读花名册
        try:
            self.df_index = pd.read_excel(self.index_file)
        except Exception as e:
            print(f"Error: 无法读取花名册 '{self.index_file}'\n{e}")
            return False
        # 清理空行、空列
        self.df_index.dropna(how='all', inplace=True)
        self.df_index.dropna(how='all', axis=1, inplace=True)

        # 校验 agg_columns 中的列必须在信息表和 output_cols_map 中
        for col in self.agg_columns.keys():
            if (col not in self.df_input.columns) or (col not in self.output_cols_map):
                print(f"Error: 合计列 '{col}' 不存在于信息表或 output_cols_map 中。")
                return False

        return True

    def filter_group_aggregate(self):
        """
        1. 根据 self.filter_col 对 self.df_input 进行初步筛选
        2. 从高优先级到低优先级依次遍历 self.role_groups:
           a) 设置一个“已分配姓名”集合 assigned_names, 初始为空。
           b) 在 self.df_input 中筛选该角色非空的行, 再排除已分配姓名
           c) 对筛选结果按 [role] + self.group_columns 分组汇总
           d) 将分组结果里的角色列重命名为 "姓名"
           e) 把本轮出现的姓名加入 assigned_names
        3. 合并所有角色的分组结果到 self.df_summary
        """
        # ----------------【1. 根据 filter_col 进行初步筛选】----------------
        if hasattr(self, "filter_cols") and isinstance(self.filter_cols, dict):
            df_filtered = self.df_input.copy()
            for col_name, values in self.filter_cols.items():
                df_filtered = df_filtered[df_filtered[col_name].isin(values)]
        else:
            # 如果没定义 filter_cols，就直接用 df_input 全表
            df_filtered = self.df_input

        # ----------------【2. 从高优先级到低优先级遍历角色】----------------
        # a) 设置一个“已分配姓名”集合 assigned_names, 初始为空。
        assigned_names = set()
        grouped_results = []

        for role in self.role_groups:
            # b) 在 input 表中找到该角色非空的行
            sub_df = df_filtered[df_filtered[role].notna()].copy()
            if sub_df.empty:
                # 没有此角色的任何记录, 跳过
                continue
            # 排除已经被更高优先级角色占用的姓名,这样就不会把这些人再统计到当前role中
            sub_df = sub_df[~sub_df[role].isin(assigned_names)]
            if sub_df.empty:
                # 经过排除后没有数据, 跳过
                continue

            # c) 按 [role] + group_columns 做分组汇总
            group_cols = [role] + self.group_columns
            grouped = (
                sub_df
                .groupby(group_cols)[list(self.agg_columns.keys())]
                .agg(self.agg_columns)
                .reset_index()
            )

            # d) 将 role 这一列重命名为 "姓名"
            grouped.rename(columns={role: "姓名"}, inplace=True)

            # e) 将本轮出现的姓名加入已分配集合
            new_assigned = grouped["姓名"].unique().tolist()
            assigned_names.update(new_assigned)

            grouped_results.append(grouped)
        # ----------------【3. 合并所有角色结果】----------------
        if grouped_results:
            self.df_summary = pd.concat(grouped_results, ignore_index=True)
        else:
            self.df_summary = pd.DataFrame()

    def merge_with_indexdf(self):
        """
        按照 df_summary 的“姓名”在花名册匹配:
        若花名册中无此“姓名”, 则删除该行；
        若花名册中有, 则补充花名册中的对应列（部门、区域、职务等）。
        """
        if self.df_summary.empty:
            return

        # 花名册与信息表里都使用"姓名"列, 左连接(left)/全连接(outer)
        df_merged = pd.merge(self.df_summary, self.df_index,
                             on="姓名", how="outer")

        # 如果某人的姓名在花名册中找不到, 对应花名册信息为空, 删除该行
        # 1. 获取按插入顺序的键列表
        keys_order = list(self.output_cols_map.keys())
        # 2. 过滤掉 "姓名"
        keys_filtered = [k for k in keys_order if k != "姓名"]
        # 3. 取前 3 个
        flower_cols = keys_filtered[:3]
        # 4. 只要这几个花名册列全是 NaN，就判定此人没在花名册找到, 删除该行
        df_merged = df_merged[~df_merged[flower_cols].isnull().all(axis=1)]

        self.df_summary = df_merged

    def rename_columns(self):
        """
        最后将 df_summary 的列名转换为 output_cols_map 的“输出列名”。
        这里需要注意只映射实际出现过的列, 不做多余处理。
        """
        if self.df_summary.empty:
            return

        # 仅对交集列进行 rename, 避免因多余列导致报错
        intersect_cols = [col for col in self.df_summary.columns if col in self.output_cols_map.keys()]
        rename_dict = {col: self.output_cols_map[col] for col in intersect_cols}
        self.df_summary.rename(columns=rename_dict, inplace=True)

        # 2) 根据 output_cols_map 的顺序重排列=先按插入顺序拿到所有键，然后映射到输出列名，如果该输出列名在 df_summary 列中就保留
        col_order = []
        for old_col in self.output_cols_map:
            new_col = self.output_cols_map[old_col]  # 映射后的列名
            if new_col in self.df_summary.columns:
                col_order.append(new_col)

        self.df_summary = self.df_summary.reindex(columns=col_order)

    def save_to_excel(self):
        """保存最终结果到Excel文件"""
        if self.df_summary.empty:
            print("Warning: 最终无有效数据, 不生成输出文件。")
            return

        self.df_summary.to_excel(self.output_file_name, index=False)
        print(f"汇总结果已保存到: {self.output_file_name}")

    def run(self):
        """执行数据处理的完整流程"""
        if not self.read_check_data():
            return  # 如果检查失败, 直接返回

        # 1. 分组汇总
        self.filter_group_aggregate()

        # 2. 与花名册比对: 若姓名不存在花名册则删除, 否则补充花名册信息
        self.merge_with_indexdf()

        # 3. 重命名列为最终输出列名
        self.rename_columns()

        # 4. 保存结果到 Excel
        self.save_to_excel()


# ============== 使用示例 ==============
if __name__ == "__main__":
    summarizer = SalesDataSummary()
    summarizer.run()
