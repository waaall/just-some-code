import sys, time
from PySide6.QtGui import *
# QPixmap, QPainter
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QTextEdit, QWidget

##=========================================================
##=======               导航窗口类                =========
##=========================================================
class DockPage(QWidget):
    def __init__(self, group_names=None):
        super().__init__()
        main_layout = QVBoxLayout(self)
        
        # 初始化各个「页面按钮」组
        self.group_names = []
        initial_group_names = group_names or ['settings_help', 'image_opt', 'file_opt']
        for name in initial_group_names:
            self.__add_group(name)

        self.setLayout(main_layout)
        self.setWindowTitle("导航栏")

    # 通用方法初始化组并添加到布局
    def __add_group(self, group_name):
        if group_name in self.group_names:
            print(f"From DockPage:\n\t组'{group_name}'已存在,无法重复添加\n")
            return
        group = QGroupBox(group_name)
        layout = QVBoxLayout(group)
        group.setLayout(layout)
        self.layout().addWidget(group)
    
    # 向指定的组添加按钮并绑定点击事件
    def add_button(self, group_name, button_name, slot_func):
        # 遍历 main_layout 查找组名对应的 QGroupBox
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i).widget()
            if isinstance(item, QGroupBox) and item.title() == group_name:
                button = QPushButton(button_name)
                button.clicked.connect(slot_func)
                item.layout().addWidget(button)
                return
        print(f"From DockPage:\n\t组 {group_name} 不存在\n")



##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = DockPage()
    trial.show()
    sys.exit(app.exec())