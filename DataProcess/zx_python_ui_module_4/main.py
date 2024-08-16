from widgets import *
from main_window import MainWindow
from modules.dicom_to_imgs import DicomToImage

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
        self.DicomHandler.dicomdirs_handler(self.wanted_items)

    def dicom_handler_bind(self):
        # 启动线程
        self.start()

##=========================================================
##=======                main函数                 =========
##=========================================================

def main():
    # 初始化绑定
    dicom_bind = DicomBinding()

    # 初始化app
    app = QApplication(sys.argv)
    app_icon = QIcon()
    app_icon.addFile(os.path.join('resources', 'branden.ico'))
    app.setWindowIcon(app_icon)
    
    # 初始化主窗口
    window = MainWindow()
    window.setWindowIcon(app_icon)

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