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
class DockWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.__init_group1('prepare')
        self.__init_group2('image_opt')
        self.__init_group3('file_opt')

        #设置总的布局
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.group1)
        mainLayout.addWidget(self.group2)
        mainLayout.addWidget(self.group3)
        self.setLayout(mainLayout)
        self.setWindowTitle("导航栏")
        self.show()

    def __init_group1(self,group_name):
        self.group1 = QGroupBox(group_name)
        layout = QVBoxLayout()
        # layout.setSpacing(20)

        self.group1_but1 = QPushButton('group1_but1')
        self.group1_but1.resize(self.group1_but1.sizeHint())
        layout.addWidget(self.group1_but1)

        self.group1.setLayout(layout)

    def __init_group2(self, group_name):
        self.group2 = QGroupBox(group_name)
        layout = QVBoxLayout()

        self.group2_but1 = QPushButton('group2_but1')
        # self.group2_but1.setToolTip('')
        self.group2_but1.resize(self.group2_but1.sizeHint())
        layout.addWidget(self.group2_but1)

        self.group2_but2 = QPushButton('group2_but2')
        self.group2_but2.resize(self.group2_but2.sizeHint())
        layout.addWidget(self.group2_but2)

        self.group2.setLayout(layout)
    
    def __init_group3(self, group_name):
        self.group3 = QGroupBox(group_name)
        layout = QVBoxLayout()

        self.group3_but1 = QPushButton('group3_but1')
        self.group3_but1.resize(self.group3_but1.sizeHint())
        layout.addWidget(self.group3_but1) 

        # self.group3_but2 = QPushButton(but_name[1])
        # self.group3_but2.resize(self.group3_but2.sizeHint())
        # layout.addWidget(self.group3_but2)

        self.group3.setLayout(layout)

    def bind_dock1_but1(self, new_name, slot_func):
        self.group1_but1.setText(new_name)
        self.group1_but1.clicked.connect(slot_func)

    def bind_dock2_but1(self, new_name, slot_func):
        self.group2_but1.setText(new_name)
        self.group2_but1.clicked.connect(slot_func)

    def bind_dock2_but2(self, new_name, slot_func):
        self.group2_but2.setText(new_name)
        self.group2_but2.clicked.connect(slot_func)

    def bind_dock3_but1(self, new_name, slot_func):
        self.group3_but1.setText(new_name)
        self.group3_but1.clicked.connect(slot_func)


##===============调试用==================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = DockWindow()
    trial.show()
    sys.exit(app.exec_())