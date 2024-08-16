import os, sys, re
from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine, Signal
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

##=========================================================
##=======                文件操作界面               =========
##=========================================================
class FileWindow(QWidget):
    selected_signal = Signal(str, list)
    def __init__(self):
        super().__init__()

        # 初始化文件名，之后的函数会改
        self.__work_folder = os.getcwd()
        self.__work_folder_items = []
        self.__wanted_indexs = []
        
        mainLayout = QVBoxLayout()
        self.__init_workfolder_group()
        mainLayout.addWidget(self.workfolder_group)
        
        self.__init_file_option_group()
        mainLayout.addWidget(self.file_option_group)
        self.setWindowTitle("文件窗口")

        ##设置总的布局
        # self.setForEachWork()  
        self.setLayout(mainLayout)

    def __init_workfolder_group(self):
        self.workfolder_group = QGroupBox("begin",self)
        layout = QVBoxLayout()

        chooseFolderBut = QPushButton(f"选择工作目录", self)
        layout.addWidget(chooseFolderBut)
        chooseFolderBut.clicked.connect(self.__get_work_folder)
        
        self.__work_folder_label = QLabel(self)
        self.__work_folder_label.resize(self.__work_folder_label.sizeHint())
        layout.addWidget(self.__work_folder_label)

        hint_lable1 = QLabel('请选择想要处理的序号:',self)
        layout.addWidget(hint_lable1)

        self.__user_index = QLineEdit(self)
        layout.addWidget(self.__user_index)

        self.workfolder_group.setLayout(layout)

        self.get_select_file_but = QPushButton('提取选中序号',self)
        self.get_select_file_but.clicked.connect(self.__get_work_folder_indexs)
        layout.addWidget(self.get_select_file_but)

        # lable本用来显示执行结果，后决定传递变量由controler显示
        self.get_select_result = QLabel(self)
        layout.addWidget(self.get_select_result)

    ##===============创建文件的具体操作界面=================
    def __init_file_option_group(self):
        self.file_option_group = QGroupBox('文件操作',self)
        layout = QGridLayout()

        # 第一个file操作按钮
        self.file_but1 = QPushButton('file_but1',self)
        layout.addWidget(self.file_but1, 0,0)

        # 第一个file操作按钮的执行信息显示
        self.file_but1_result = QPlainTextEdit(self)
        self.file_but1_result.setReadOnly(True)
        layout.addWidget(self.file_but1_result, 1,0)

        # 第二个file操作按钮
        self.file_but2 = QPushButton('file_but2',self)
        # self.file_but2.setToolTip('')
        self.file_but2.resize(self.file_but2.sizeHint())
        # self.file_but2.clicked.connect(self.copyIntimeFile)
        layout.addWidget(self.file_but2, 0,1)
        
        # 第二个file操作按钮的执行信息显示
        self.file_but2_result = QPlainTextEdit(self)
        self.file_but2_result.setReadOnly(True)
        layout.addWidget(self.file_but2_result, 1,1)

        self.file_option_group.setLayout(layout)

    def __get_work_folder(self):
        self.__work_folder = QFileDialog.getExistingDirectory(self,"选择目录","./")
        self.__work_folder_items = os.listdir(self.__work_folder)
        # 构建显示的字符串内容
        content = "当前目录内文件为:\n\n"
        for i, item in enumerate(self.__work_folder_items):
            content += f"{i}: {item}\n"
        self.__work_folder_label.setText(content)

    def __get_work_folder_indexs(self):
        # 将用户输入的索引字符串进行预处理
        temp = re.sub(r"\s+|,|，", r" ", self.__user_index.text()).split()
        wanted_items = []
        try:
            # 将字符串转换为整数列表
            self.__wanted_indexs = list(map(int, temp))
        except ValueError:
            # 如果转换失败，说明输入中有非整数，显示错误消息
            self.get_select_result.setText('输入包含非整数值')
            return

        # 检查是否提取到了有效的索引
        if not self.__wanted_indexs:
            self.get_select_result.setText('没有提取到有效输入')
            return

        # 检查索引是否在范围内
        for index in self.__wanted_indexs:
            if index < 0 or index >= len(self.__work_folder_items):
                self.get_select_result.setText(f'给出序号 {index} 超出范围')
                return
            else:
                wanted_items.append(self.__work_folder_items[index])
        # 如果所有检查通过，显示成功消息并发出信号
        self.get_select_result.setText('成功提取序号')
        self.selected_signal.emit(self.__work_folder, wanted_items)

    def bind_file_but1(self, new_name, slot_func):
        self.file_but1.setText(new_name)
        self.file_but1.clicked.connect(slot_func)

    def bind_file_but2(self, new_name, slot_func):
        self.file_but2.setText(new_name)
        self.file_but2.clicked.connect(slot_func)

    ## 显示file_but1的操作执行结果
    def set_file_but1_result(self, messages):
        self.file_but1_result.appendPlainText(messages)
        self.file_but1_result.moveCursor(QTextCursor.End)

    ## 显示file_but2的操作执行结果
    def set_file_but2_result(self, messages):
        self.file_but2_result.appendPlainText(messages)
        self.file_but2_result.moveCursor(QTextCursor.End)

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = FileWindow()
    trial.show()
    sys.exit(app.exec())