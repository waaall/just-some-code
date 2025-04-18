"""
    ===========================README============================
    create date:    20241022
    creator:        zhengxu
    function:       批量清理 macOS 系统创建的_PoopPrefix开头隐藏文件

    version:        beta 1.0
    details:        当 macOS 系统在非原生文件系统上创建文件时, 会自动创建以 ._ 开头的隐藏文件
                    这个工具用于清理这些隐藏文件, 如果有同名文件（去掉前缀后）, 则删除隐藏文件
"""
# =========================用到的库==========================
import os
import sys
from concurrent.futures import ThreadPoolExecutor


# =========================================================
# =======           清理 macOS 隐藏文件            =========
# =========================================================
class MacPoopSccoper:
    def __init__(self, parallel: bool = True):
        # 工作目录
        self._work_folder = ""
        # 可能的子目录列表
        self.possble_dirs = []

        # 是否启用并行处理
        self.parallel = parallel
        self.max_threads = 3

        # 统计信息
        self.files_found = 0
        self.files_deleted = 0
        # 定义隐藏文件前缀
        self._PoopPrefix = '._'

    def set_work_folder(self, folder_path):
        """设置工作目录并获取所有子目录"""
        self._work_folder = folder_path
        print(f"设置工作目录: {folder_path}")

        # 获取并存储工作目录下的所有子目录
        try:
            self.possble_dirs = [d for d in os.listdir(folder_path)
                                 if os.path.isdir(os.path.join(folder_path, d))]
            # 添加当前目录选项
            self.possble_dirs.append("当前目录")
            print(f"找到 {len(self.possble_dirs)} 个可处理的目录")
        except Exception as e:
            print(f"获取子目录时出错: {str(e)}")
            self.possble_dirs = ["当前目录"]

        return self.possble_dirs

    def selected_dirs_handler(self, indices):
        """处理用户选择的目录"""
        # 验证索引是否有效
        if not all(0 <= idx < len(self.possble_dirs) for idx in indices):
            return False

        # 处理选中的目录
        for idx in indices:
            dir_name = self.possble_dirs[idx]
            if dir_name == "当前目录":
                print(f"开始处理当前目录: {self._work_folder}")
                self._data_dir_handler("")
            else:
                print(f"开始处理目录: {dir_name}")
                self._data_dir_handler(dir_name)

        return True

    def _delete_file(self, file_path):
        """删除文件并更新计数"""
        try:
            os.remove(file_path)
            self.files_deleted += 1
            print(f"已删除: {file_path}")
            return True
        except Exception as e:
            print(f"删除文件失败 {file_path}: {str(e)}")
            return False

    def _data_dir_handler(self, _data_dir: str):
        """
        递归遍历文件夹查找并处理._开头的文件
        """
        # 获取全路径
        full_path = os.path.join(self._work_folder, _data_dir)

        # 创建要处理的任务列表
        real_poop_files = []

        # 递归遍历所有文件
        for root, _, files in os.walk(full_path):
            # 筛选出._开头的文件
            poop_files = [f for f in files if f.startswith(self._PoopPrefix)]

            if poop_files:
                for poop_file in poop_files:
                    # 构建完整文件路径
                    poop_file_path = os.path.join(root, poop_file)
                    # 获取对应的正常文件名（去掉前缀）
                    normal_file = poop_file[len(self._PoopPrefix):]

                    # 只有当对应的正常文件存在时, 才添加到任务列表
                    if os.path.exists(os.path.join(root, normal_file)):
                        real_poop_files.append(poop_file_path)

        self.files_found += len(real_poop_files)

        # 根据 parallel 参数决定是否使用并行处理
        if self.parallel and real_poop_files:
            max_works = min(self.max_threads, os.cpu_count(), len(real_poop_files))
            with ThreadPoolExecutor(max_workers=max_works) as executor:
                # 将每个文件的处理提交给线程池
                futures = [executor.submit(self._delete_file, poop_path)
                           for poop_path in real_poop_files]
                # 等待所有任务完成
                for future in futures:
                    try:
                        future.result()  # 获取任务结果, 如果有异常会在这里抛出
                    except Exception as e:
                        print(f"处理文件时出错: {str(e)}")
        else:
            # 串行处理每个文件
            for poop_path in real_poop_files:
                try:
                    self._delete_file(poop_path)
                except Exception as e:
                    print(f"处理文件时出错: {str(e)}")

        # 输出处理结果
        print(f"文件夹处理完成: {_data_dir}")
        print(f"累积找到了{self.files_found}个poop文件, 删除了{self.files_deleted}个")


# =====================main(单独执行时使用)=====================
def main():
    # 获取用户输入的路径
    input_path = input("请复制要清理的文件夹绝对路径(若脚本在同一目录, 请直接按Enter):\n")

    # 判断用户是否直接按Enter, 设置为当前工作目录
    if not input_path:
        work_folder = os.getcwd()
    elif os.path.isdir(input_path):
        work_folder = input_path
    else:
        print(f"错误:路径 {input_path} 不存在或不是文件夹")
        return

    cleaner = MacPoopSccoper()
    cleaner.set_work_folder(work_folder)
    possble_dirs = cleaner.possble_dirs

    # 给用户显示, 请用户输入index
    number = len(possble_dirs)
    print('\n')
    for i in range(number):
        print(f"{i}: {possble_dirs[i]}")
    user_input = input("\n请选择要处理的序号(用空格分隔多个序号):\n")

    # 解析用户输入
    try:
        indices = user_input.split()
        index_list = [int(index) for index in indices]
    except ValueError:
        print("输入错误, 必须输入数字")
        return

    RESULT = cleaner.selected_dirs_handler(index_list)
    if not RESULT:
        print("输入数字不在提供范围, 请重新运行")


# =========================调试用============================
if __name__ == '__main__':
    main()
