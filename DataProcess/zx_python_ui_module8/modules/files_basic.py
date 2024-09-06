##=========================用到的库==========================
import os
import queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal
##=========================================================
##=======              文件批量处理基类             =========
##=========================================================
class FilesBasic(QObject):
    result_signal = Signal(str)
    def __init__(self,log_folder_name='handle_log',out_dir_suffix='Out-', max_threads = 3):
        super().__init__()
        # 设置消息队列(初始化顺序不是随意的)
        self.result_queue = queue.Queue()
        self.max_threads = max_threads
        
        # work_folder是dicom文件夹的上一级文件夹，之后要通过set_work_folder改
        self._work_folder = os.getcwd()

        # 自类重定义此量,用于查找指定后缀的文件
        self.suffixs = ['.txt']

        # 之后会根据函数确定
        self.possble_dirs = None
        self._selected_dirs = []
        self._data_dir = None

        # 设置导出文件夹的前缀名 & log文件夹名字
        self.log_folder_name = log_folder_name
        self.out_dir_suffix = out_dir_suffix

    ##========================发送log信息========================##
    def send_message(self, message):
        print(f"From FilesBasic: \n\t{message}\n")
        self.result_queue.put(message)
        self.result_signal.emit(message)

    ##======================设置workfolder======================##
    def set_work_folder(self, work_folder):
        """设置工作目录, 并确保目录存在"""
        if os.path.exists(work_folder) and os.path.isdir(work_folder):
            self._work_folder = work_folder
            os.chdir(work_folder)
            self.possble_dirs = [f for f in os.listdir(work_folder) if not f.startswith('.')]
            self.send_message(f"工作目录已设置为: {os.getcwd()}")
        else:
            raise ValueError(f"The directory {work_folder} does not exist or is not a directory.")
            # 遍历所有文件夹

    ##===========用户选择workfolder内的selected_dirs处理===========##
    def selected_dirs_handler(self, indexs_list):
        # 接收的indexs_list可以是indexs也可以是文件夹名(字符串数组)
        if indexs_list[0] in self.possble_dirs:
            self._selected_dirs = indexs_list
        else: 
            for index in indexs_list:
                if index in range(len(self.possble_dirs)):
                    self._selected_dirs.append(self.possble_dirs[index])
        if not self._selected_dirs:
            return False
        
        # 使用 ThreadPoolExecutor 并发处理每个选定的文件夹
        max_works = min(self.max_threads, os.cpu_count(), len(self._selected_dirs))
        with ThreadPoolExecutor(max_workers=max_works) as executor:
            # 将每个文件夹的处理, 提交给线程池 (直接同步调用, 不再使用异步包装)
            futures = [executor.submit(self._data_dir_handler, _data_dir)  
                                    for _data_dir in self._selected_dirs]
            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()  # 获取任务结果，如果有异常会在这里抛出
                except Exception as e:
                    self.send_message(f"处理文件夹时出错: {str(e)}")

        self._save_log()
        self.send_message('SUCCESS! log file saved.')
        return True

    ##=======================保存log信息========================##
    def _save_log(self):
        os.makedirs(self.log_folder_name, exist_ok=True)
        # 获取当前时间并格式化为文件名
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{current_time}.log"
        log_file_path = os.path.join(self.log_folder_name, log_filename)
        # 打开文件并写入队列中的内容
        with open(log_file_path, 'w') as log_file:
            while not self.result_queue.empty():
                log_entry = self.result_queue.get()
                log_file.write(f"{log_entry}\n")

    def _get_filenames_by_suffix(self, path):
        if not os.path.isdir(path):
            self.send_message(f"Error: Folder「{path}」does not exist.")
            return None
        
        # not f.startswith('.')不包括隐藏文件
        return [f for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f)) 
                and not f.startswith('.') and
                any(f.endswith(suffix) for suffix in self.suffixs)]

    ##=====================处理(单个数据文件夹)函数======================##
    def _data_dir_handler(self, _data_dir):
        self.send_message("From FilesBasic:\n\t这是基类, 请在子类中重写该方法.\n")
        
        # # 这种在每个线程不同的量(且不大),就不用self,避免多线程出问题
        # # 这部分代码自类重写后加在搜索_data_dir的代码后
        # os.makedirs(self.out_dir_suffix + _data_dir, exist_ok=True)
