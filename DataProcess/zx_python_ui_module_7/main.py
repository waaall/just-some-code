import sys
from widgets import *
from main_window import MainWindow

from modules.dicom_to_imgs import DicomToImage
from modules.merge_colors import MergeColors

import resources_rc
##=========================================================
##=======          绑定文件批量处理modules          =========
##=========================================================
class BatchFilesBinding(QThread):
    def __init__(self, object, bind_name):
        super().__init__()
        self.work_folder = ''
        self.wanted_items = []
        self.bind_name = bind_name
        self.handler_object = object  # 直接接收处理对象实例

    def update_setting(self, object_name, attribute, value):
        # 检查处理对象是否与传递的 object_name 匹配，并且对象有这个属性
        if self.handler_object.__class__.__name__ == object_name and hasattr(self.handler_object, attribute):
            setattr(self.handler_object, attribute, value)
            print(f"From BatchFilesBinding:\n\tUpdated {attribute} to {value} in {object_name}\n")

    def get_user_select(self, work_folder, wanted_items):
        self.work_folder = work_folder
        self.wanted_items = wanted_items

    def run(self):
        # 在线程中执行耗时操作
        self.handler_object.set_work_folder(self.work_folder)
        self.handler_object.selected_dirs_handler(self.wanted_items)

    def handler_binding(self):
        # 启动线程
        self.start()

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
    merge_colors_bind = BatchFilesBinding(MergeColors(), '颜色通道合成')

    # file_window信号数据selected_signal传入绑定对象merge_colors_bind
    window.file_window.selected_signal.connect(merge_colors_bind.get_user_select)
        
    # dicom对象信息信号绑定file_window显示
    merge_colors_bind.handler_object.result_signal.connect(window.file_window.set_file_but1_result)

    # file_window操作按钮绑定modules的操作
    window.file_window.bind_file_but1(merge_colors_bind.bind_name, merge_colors_bind.handler_binding)
    
    # 设置的参数被修改的信号数据绑定update_setting函数
    window.setting_window.settings.changed_signal.connect(merge_colors_bind.update_setting)


##=============================绑定dicom================================
    # 初始化dicom绑定
    dicom_bind = BatchFilesBinding(DicomToImage(), 'DICOM处理') 

    # file_window信号数据selected_signal传入绑定对象dicom_bind
    window.file_window.selected_signal.connect(dicom_bind.get_user_select)
        
    # dicom对象信息信号绑定file_window显示
    dicom_bind.handler_object.result_signal.connect(window.file_window.set_file_but2_result)

    # file_window操作按钮绑定modules的操作
    window.file_window.bind_file_but2(dicom_bind.bind_name, dicom_bind.handler_binding)

    # 设置的参数被修改的信号数据绑定update_setting函数
    window.setting_window.settings.changed_signal.connect(dicom_bind.update_setting)
    ##=============================app运行=============================##
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()