import sys
# from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

##=========================================================
##=======                 帮助界面                 =========
##=========================================================
class HelpWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        self.init_help_window()

    ##=====创建帮助窗口======
    def init_help_window(self):

        layout1 = QVBoxLayout()
        GroupBox1 = QGroupBox("使用说明")
        self.userBut = QPushButton("使用文档")
        layout1.addWidget(self.userBut)
        userLable = QLabel("该文档说明具体的使用细节\n\n包括前期建模的格式问题等。")
        layout1.addWidget(userLable)
        GroupBox1.setLayout(layout1)
        
        layout2 = QVBoxLayout()
        GroupBox2 = QGroupBox("开发指导")
        self.devBut = QPushButton("开发文档")
        layout2.addWidget(self.devBut)
        devLable = QLabel("该文档对开发这个软件进行指导\n\n讲述软件的框架和部分实现的细节。")
        layout2.addWidget(devLable)
        GroupBox2.setLayout(layout2)
        
        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(GroupBox1)
        mainLayout.addWidget(GroupBox2)

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = HelpWindow()
    trial.show()
    sys.exit(app.exec())
