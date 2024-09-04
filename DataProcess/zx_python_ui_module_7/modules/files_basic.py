##=========================用到的库==========================
import os
import queue
from datetime import datetime

from PySide6.QtCore import QObject, Signal
##=========================================================
##=======              文件批量处理基类             =========
##=========================================================
class FilesBasic(QObject):
    result_signal = Signal(str)
    def __init__(self,log_folder_name='handle_log',out_dir_suffix='Out-'):
        super().__init__()
        # 设置消息队列(初始化顺序不是随意的)
        self.result_queue = queue.Queue()
        
        # work_folder是dicom文件夹的上一级文件夹，之后要通过set_work_folder改
        self._work_folder = os.getcwd()

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
            self.possble_dirs = os.listdir(work_folder)
            self.send_message(f"工作目录已设置为: {os.getcwd()}")
        else:
            raise ValueError(f"The directory {work_folder} does not exist or is not a directory.")
            # 遍历所有文件夹

    ##===========用户选择workfolder内的selected_dirs处理===========##
    def selected_dirs_handler(self, indexs_list):
        # 接收的indexs_list可以是indexs也可以是文件夹名（字符串数组）
        if indexs_list[0] in self.possble_dirs:
            self._selected_dirs = indexs_list
        else: 
            for index in indexs_list:
                if index in range(len(self.possble_dirs)):
                    self._selected_dirs.append(self.possble_dirs[index])
        if not self._selected_dirs:
            return False
        for dir in self._selected_dirs:
            self._data_dir = dir
            out_dir_name = self.out_dir_suffix + self._data_dir
            os.makedirs(out_dir_name, exist_ok=True)
            self._data_dir_handler()

        self.send_message('SUCCESS! log file saved.')
        self._save_log()

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

    ##=====================处理(单个数据文件夹)函数======================##
    def _data_dir_handler(self):
        self.send_message('这是基类, 请在子类中重写该方法.')

