"""
    ===========================README============================
    create date:    20250427
    change date:
    creator:        zhengxu
    function:       根据时间范围和数值范围裁剪CSV文件
    details:        python cut_csv.py test.csv sampling_rate 1000 --time "0-3, 4-5, 8-11" --value "2000-2200"
                    将保留0-3秒、4-5秒和8-11秒的数据, 且只保留值在2000-2200范围内的数据

                    采样率默认为1000Hz, 可以省略sampling_rate参数
                    如果不指定--time参数, 则保留全部时间范围的数据, --value参数同理
                    例如: python cut_csv.py test.csv --value "2000-2200"

    version:        beta 1.0
    updates:
"""
# =========================用到的库==========================
import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# =======                CSV文件裁剪类             =========
# =========================================================
class CSVCutter:
    """CSV文件裁剪处理类, 提供按时间和数值范围裁剪的功能"""
    def __init__(self, input_file=None, sampling_rate=1000):
        """
        初始化CSV裁剪器
        Args:
            input_file (str): 输入CSV文件路径
            sampling_rate (int): 采样率（Hz）, 默认为1000Hz
        """
        self.input_file = input_file
        self.sampling_rate = sampling_rate
        self.time_ranges = []
        self.value_ranges = []
        self.original_data = None
        self.original_time = None
        self.filtered_data = None
        self.filtered_time = None
        self.time_axis = None
        self.filtered_time_axis = None
        self.df = None
        self.result_df = None

    def set_input_file(self, input_file):
        """设置输入文件路径"""
        if os.path.isfile(input_file):
            self.input_file = input_file
            return True
        else:
            print(f"错误: 文件 {input_file} 不存在")
            return False

    def set_sampling_rate(self, sampling_rate):
        """设置采样率"""
        try:
            if sampling_rate is None:
                self.sampling_rate = 1000
                print("未指定采样率, 使用默认值: 1000Hz")
                return True
            self.sampling_rate = int(sampling_rate)
            return True
        except ValueError:
            print(f"错误: 采样率 {sampling_rate} 必须是整数")
            return False

    def set_time_ranges(self, time_range_str):
        """设置要保留的时间范围"""
        self.time_ranges = self._parse_range_string(time_range_str)
        return bool(self.time_ranges) or not time_range_str

    def set_value_ranges(self, value_range_str):
        """设置要保留的数值范围"""
        self.value_ranges = self._parse_range_string(value_range_str)
        return bool(self.value_ranges) or not value_range_str

    def _parse_range_string(self, range_str):
        """解析范围字符串, 如 "0-3, 4-5, 8-11" 转为 [(0, 3), (4, 5), (8, 11)]"""
        if not range_str:
            return []

        ranges = []
        segments = [s.strip() for s in range_str.split(",")]

        for segment in segments:
            if "-" in segment:
                start, end = segment.split("-")
                try:
                    start = float(start.strip())
                    end = float(end.strip())
                    if start <= end:
                        ranges.append((start, end))
                    else:
                        print(f"警告: 范围 {segment} 的起点大于终点, 已忽略")
                except ValueError:
                    print(f"警告: 无法解析范围 {segment}, 已忽略")
            else:
                try:
                    # 单一数值视为相同的起点和终点
                    value = float(segment.strip())
                    ranges.append((value, value))
                except ValueError:
                    print(f"警告: 无法解析值 {segment}, 已忽略")

        return ranges

    def _get_mask_from_ranges(self, values, ranges):
        """根据范围列表生成布尔掩码"""
        if not ranges:
            # 如果没有指定范围, 保留所有数据
            return np.ones(len(values), dtype=bool)

        mask = np.zeros(len(values), dtype=bool)
        for start, end in ranges:
            # 包含上下界
            mask = mask | ((values >= start) & (values <= end))

        return mask

    def load_data(self):
        """加载CSV数据"""
        try:
            if not self.input_file:
                raise ValueError("未设置输入文件")
            if not self.sampling_rate:
                raise ValueError("未设置采样率")

            # 读取CSV文件
            self.df = pd.read_csv(self.input_file)

            # 确保至少有两列数据
            if self.df.shape[1] < 2:
                raise ValueError(f"CSV文件 {self.input_file} 至少需要两列数据")

            # 第一列是时间, 第二列是值
            self.original_time = self.df.iloc[:, 0].values
            self.original_data = self.df.iloc[:, 1].values

            # 生成基于采样率的时间轴
            self.time_axis = np.arange(len(self.original_data)) / self.sampling_rate

            return True
        except Exception as e:
            print(f"加载数据失败: {str(e)}")
            return False

    def process(self):
        """处理数据, 应用时间和数值筛选"""
        try:
            if self.original_data is None:
                if not self.load_data():
                    return False

            # 应用时间范围筛选
            time_mask = self._get_mask_from_ranges(self.time_axis, self.time_ranges)

            # 应用数值范围筛选
            value_mask = self._get_mask_from_ranges(self.original_data, self.value_ranges)

            # 合并掩码
            combined_mask = time_mask & value_mask

            # 应用掩码
            self.filtered_data = self.original_data[combined_mask]
            filtered_time_orig = self.original_time[combined_mask]
            self.filtered_time_axis = self.time_axis[combined_mask]

            # 创建结果DataFrame
            self.result_df = pd.DataFrame({
                self.df.columns[0]: filtered_time_orig,
                self.df.columns[1]: self.filtered_data
            })

            return True
        except Exception as e:
            print(f"处理数据失败: {str(e)}")
            return False

    def save_result(self, output_file=None):
        """保存处理结果"""
        try:
            if self.result_df is None:
                raise ValueError("没有可保存的处理结果")

            # 确定输出文件名
            if not output_file:
                base_name, ext = os.path.splitext(self.input_file)
                output_file = f"{base_name}_cut{ext}"

            # 保存结果
            self.result_df.to_csv(output_file, index=False)
            print(f"裁剪后的数据已保存为 {output_file}")
            print(f"原始数据点数: {len(self.original_data)}")
            print(f"裁剪后数据点数: {len(self.filtered_data)}")

            return True
        except Exception as e:
            print(f"保存结果失败: {str(e)}")
            return False

    def generate_plot(self, output_file=None):
        """生成对比预览图"""
        try:
            if self.original_data is None or self.filtered_data is None:
                raise ValueError("没有可用于绘图的数据")

            # 确定输出文件名
            if not output_file:
                base_name = os.path.splitext(self.input_file)[0]
                output_file = f"{base_name}_cut_preview.png"

            plt.figure(figsize=(12, 8))

            # 上图显示原始数据和筛选区域
            plt.subplot(211)
            plt.plot(self.time_axis, self.original_data, 'b-', label='原始数据')
            plt.ylabel('数值')

            # 高亮显示保留的时间区域
            for start, end in self.time_ranges:
                plt.axvspan(start, end, color='green', alpha=0.2)

            # 标记保留的值范围
            if self.value_ranges:
                for start, end in self.value_ranges:
                    plt.axhline(y=start, color='r', linestyle='--', alpha=0.5)
                    plt.axhline(y=end, color='r', linestyle='--', alpha=0.5)

            plt.title('原始数据与筛选区域')
            plt.grid(True)
            plt.legend()

            # 下图显示筛选结果
            plt.subplot(212)
            plt.plot(self.filtered_time_axis, self.filtered_data, 'r-', label='筛选后数据')
            plt.xlabel('时间 (秒)')
            plt.ylabel('数值')
            plt.title('筛选后数据')
            plt.grid(True)
            plt.legend()

            plt.tight_layout()

            # 保存图片
            plt.savefig(output_file, dpi=300)
            print(f"预览图已保存为 {output_file}")
            plt.close()

            return True
        except Exception as e:
            print(f"生成预览图失败: {str(e)}")
            return False

    def run(self, generate_plot=False):
        """运行完整的处理流程"""
        if not self.process():
            return False

        if not self.save_result():
            return False

        if generate_plot and not self.generate_plot():
            return False

        return True

    def print_summary(self):
        """打印处理参数摘要"""
        print("\n处理参数摘要:")
        print(f"  - 输入文件: {self.input_file}")
        print(f"  - 采样率: {self.sampling_rate} Hz")

        if self.time_ranges:
            print(f"  - 时间范围: {self.time_ranges}")

        if self.value_ranges:
            print(f"  - 数值范围: {self.value_ranges}")

        if self.filtered_data is not None:
            print("\n处理结果:")
            print(f"  - 原始数据点数: {len(self.original_data)}")
            print(f"  - 筛选后数据点数: {len(self.filtered_data)}")
            print(f"  - 保留数据比例: {len(self.filtered_data) / len(self.original_data) * 100:.2f}%")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='根据时间范围和数值范围裁剪CSV文件')
    parser.add_argument('input_file', help='输入CSV文件路径')
    parser.add_argument('sampling_rate_key', nargs='?', default='sampling_rate', help='"sampling_rate" 关键字, 可省略')
    parser.add_argument('sampling_rate', type=int, nargs='?', default=None, help='采样率（Hz）, 可省略, 默认为1000Hz')
    parser.add_argument('--time', help='要保留的时间范围, 格式: "0-3, 4-5, 8-11"')
    parser.add_argument('--value', help='要保留的数值范围, 格式: "2000-2200"')
    parser.add_argument('--plot', action='store_true', help='生成对比预览图')

    args = parser.parse_args()

    # 验证采样率关键字
    if args.sampling_rate_key.lower() != "sampling_rate" and args.sampling_rate is not None:
        print("错误: 第二个参数必须是 'sampling_rate'")
        sys.exit(1)

    # 创建CSV裁剪器实例
    cutter = CSVCutter()

    # 设置参数
    if not cutter.set_input_file(args.input_file):
        sys.exit(1)

    if not cutter.set_sampling_rate(args.sampling_rate):
        sys.exit(1)

    cutter.set_time_ranges(args.time)
    cutter.set_value_ranges(args.value)

    # 显示处理参数
    cutter.print_summary()

    # 执行处理流程
    if cutter.run(generate_plot=args.plot):
        cutter.print_summary()
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
