from widgets import *
from main_window import MainWindow
from modules.dicom_to_imgs import DicomToImage

##=========================================================
##=======               绑定modules               =========
##=========================================================

class Binding():
    def __init__(self, bind_name = 'DICOM处理'):
        super().__init__()
        self.work_folder = ''
        self.wanted_items = []

        self.bind_name = bind_name
    
    def get_user_select(self, work_folder, wanted_items):
        self.work_folder = work_folder
        self.wanted_items = wanted_items

    def dicom_bind(self):
        DicomHandler = DicomToImage(self.work_folder)
        RESULT = DicomHandler.dicomdirs_handler(self.wanted_items)
        print('所有DICOM文件处理完成')
        return RESULT

##=========================================================
##=======                main函数                 =========
##=========================================================

def main():
        # 初始化绑定
        user_bind = Binding()

        # 初始化界面
        app = QApplication(sys.argv)
        window = MainWindow()

        # file_window信号数据selected_signal传入绑定对象user_bind
        window.file_window.selected_signal.connect(user_bind.get_user_select)
        
        # file_window操作按钮绑定modules的操作
        window.file_window.bind_file_but2(user_bind.bind_name, user_bind.dicom_bind)

        # app运行
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()