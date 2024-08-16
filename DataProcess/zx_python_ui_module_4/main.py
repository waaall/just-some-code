from widgets import *
from main_window import MainWindow

from modules.dicom_to_imgs import DicomToImage
from modules.merge_colors import MergeColors

import resources_rc
##=========================================================
##=======               绑定modules               =========
##=========================================================

class DicomBinding(QThread):
    def __init__(self, bind_name = 'DICOM处理'):
        super().__init__()
        self.work_folder = ''
        self.wanted_items = []
        self.bind_name = bind_name

        # 实例化DicomToImage
        self.DicomHandler = DicomToImage()

    def get_user_select(self, work_folder, wanted_items):
        self.work_folder = work_folder
        self.wanted_items = wanted_items

    def run(self):
        # 在线程中执行耗时操作
        self.DicomHandler.set_work_folder(self.work_folder)
        self.DicomHandler.selected_dirs_handler(self.wanted_items)

    def dicom_handler_bind(self):
        # 启动线程
        self.start()

class MergeColorsBinding(QThread):
    def __init__(self, bind_name = 'RG通道合成'):
        super().__init__()
        self.work_folder = ''
        self.wanted_items = []
        self.bind_name = bind_name

        # 实例化DicomToImage
        self.ColorsHandler = MergeColors()

    def get_user_select(self, work_folder, wanted_items):
        self.work_folder = work_folder
        self.wanted_items = wanted_items

    def dicom_handler_bind(self):
        # 启动线程
        self.start()

    def run(self):
        # 在线程中执行耗时操作
        self.ColorsHandler.set_work_folder(self.work_folder)
        self.ColorsHandler.selected_dirs_handler(self.wanted_items)


##=========================================================
##=======                main函数                 =========
##=========================================================

def main():
    # 初始化app
    app = QApplication(sys.argv)
    # app_icon = QIcon((QPixmap(u":/resouces/icons/branden.ico")))
    # app.setWindowIcon(app_icon)
    
    # 初始化主窗口
    window = MainWindow()
    # window.setWindowIcon(app_icon)

##============================绑定mergeRGs===============================
    # 初始化绑定
    mergeRGs_bind = MergeColorsBinding()
    # file_window信号数据selected_signal传入绑定对象mergeRGs_bind
    window.file_window.selected_signal.connect(mergeRGs_bind.get_user_select)
        
    # dicom对象信息信号绑定file_window显示
    mergeRGs_bind.ColorsHandler.result_signal.connect(window.file_window.set_file_but1_result)

    # file_window操作按钮绑定modules的操作
    window.file_window.bind_file_but1(mergeRGs_bind.bind_name, mergeRGs_bind.dicom_handler_bind)


##=============================绑定dicom================================
    # 初始化dicom绑定
    dicom_bind = DicomBinding()
    # file_window信号数据selected_signal传入绑定对象dicom_bind
    window.file_window.selected_signal.connect(dicom_bind.get_user_select)
        
    # dicom对象信息信号绑定file_window显示
    dicom_bind.DicomHandler.result_signal.connect(window.file_window.set_file_but2_result)

    # file_window操作按钮绑定modules的操作
    window.file_window.bind_file_but2(dicom_bind.bind_name, dicom_bind.dicom_handler_bind)


    # app运行
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()