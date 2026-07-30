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
        
        #一个窗口的最小尺寸,分别代表左半和右半的最小宽度 & 上半和下半的最小高度
        self.window_minimum_size = [200, 300, 200, 200]
        mainLayout = QVBoxLayout()
        self.__init_workfolder_group()
        mainLayout.addWidget(self.workfolder_group)
        
        self.__init_file_option_group()
        mainLayout.addWidget(self.file_option_group)
        self.setWindowTitle("文件窗口")

        ##设置总的布局
        self.setLayout(mainLayout)

    def __init_workfolder_group(self):
        self.workfolder_group = QGroupBox("一:begin",self)
        group_layout = QHBoxLayout()
        
        # 选择文件等操作的layout (group_layout:左select_layout右)
        select_layout = QVBoxLayout()

        chooseFolderBut = QPushButton(f"1.选择工作目录", self)
        select_layout.addWidget(chooseFolderBut)
        chooseFolderBut.clicked.connect(self.__get_work_folder)
        
        hint_lable1 = QLabel('2.请选择想要处理的序号:',self)
        hint_lable1.setMinimumWidth(self.window_minimum_size[0])
        select_layout.addWidget(hint_lable1)

        self.__user_index = QLineEdit(self)
        self.__user_index.setMinimumWidth(self.window_minimum_size[0])
        select_layout.addWidget(self.__user_index)

        self.get_select_file_but = QPushButton('3.提取选中序号',self)
        self.get_select_file_but.setMinimumWidth(self.window_minimum_size[0])
        self.get_select_file_but.clicked.connect(self.__get_work_folder_indexs)
        select_layout.addWidget(self.get_select_file_but)

        # lable本用来显示执行结果，后决定传递变量由controler显示
        self.select_index_result_label = QLabel(self)
        select_layout.addWidget(self.select_index_result_label)

        # layout层级嵌套, stretch=1表示select_layout占据小部分空间
        group_layout.addLayout(select_layout, stretch=1)

        self.__files_list_area = QPlainTextEdit(self)
        self.__files_list_area.setMinimumSize(self.window_minimum_size[0],
                                                self.window_minimum_size[2])
        self.__files_list_area.setReadOnly(True)
        group_layout.addWidget(self.__files_list_area, stretch=3)
    
        self.workfolder_group.setLayout(group_layout)

    ##===============创建文件的具体操作界面=================
    def __init_file_option_group(self):
        self.file_option_group = QGroupBox('二:文件操作',self)
        file_option_layout = QHBoxLayout(self)

        # 创建侧边栏
        self.sidebar = QListWidget()
        # 尽量不用setFixedWidth,用stretch和setMinimumWidth
        self.sidebar.setMinimumSize(self.window_minimum_size[0],
                                    self.window_minimum_size[2])
        self.sidebar.setStyleSheet("QListWidget { font-size: 16px; }")
        self.sidebar.currentItemChanged.connect(self._switch_file_option)

        # 创建显示内容的区域
        self.file_options_stack = QStackedWidget()
        # self.file_options_stack.setSizePolicy(self.sizePolicy())

        # 添加侧边栏和显示区域
        file_option_layout.addWidget(self.sidebar, stretch=1)
        file_option_layout.addWidget(self.file_options_stack, stretch=3)
        self.file_option_group.setLayout(file_option_layout)

    def _switch_file_option(self, current, previous):
        if not current:
            return
        # 获取选中项目的索引，并切换到对应的页面
        index = self.sidebar.currentRow()
        self.file_options_stack.setCurrentIndex(index)
        
        # 清空当前页面的 QPlainTextEdit
        for widget in self.file_options_stack.currentWidget().findChildren(QPlainTextEdit):
            widget.clear()

    def add_file_operation(self, name, slot_func):
        """
        添加一个新的文件操作项，包括一个按钮和一个结果显示区域。
        :param name: 操作的名称，在侧边栏显示。
        :param slot_func: 按钮点击时执行的槽函数。
        """
        # 创建新页面
        file_options_page = QWidget()
        file_options_layout = QVBoxLayout(file_options_page)

        # 添加操作按钮
        operation_button = QPushButton(name)
        operation_button.clicked.connect(slot_func)
        file_options_layout.addWidget(operation_button)

        # 添加执行结果显示区域
        result_display = QPlainTextEdit()
        result_display.setMinimumSize(self.window_minimum_size[0],
                                      self.window_minimum_size[2])
        result_display.setReadOnly(True)
        file_options_layout.addWidget(result_display)

        # 添加页面到 QStackedWidget
        self.file_options_stack.addWidget(file_options_page)

        # 在侧边栏添加操作项
        item = QListWidgetItem(name)
        self.sidebar.addItem(item)

    def set_operation_result(self, message):
        # 获取当前选中页面的 QPlainTextEdit
        current_index = self.sidebar.currentRow()
        if current_index == -1:
            print("No operation selected.")
            return

        # 获取当前页面的 QPlainTextEdit 并显示消息
        current_widget = self.file_options_stack.widget(current_index)
        if current_widget:
            result_display = current_widget.findChild(QPlainTextEdit)
            if result_display:
                result_display.appendPlainText(message)
                try:
                    result_display.moveCursor(QPlainTextEdit().textCursor().End)
                except:
                    result_display.moveCursor(QTextCursor.End)

    def __get_work_folder(self):
        self.__work_folder = QFileDialog.getExistingDirectory(self,"选择目录","./")
        
        # 检查是否选择了有效的目录
        if not self.__work_folder:
            # 用户取消选择或者未选择有效目录，提示用户
            print(f"From FileWindow:\n\tError: 未选择目录")
            return  # 退出函数，避免后续错误
        
        self.__work_folder_items = [f for f in os.listdir(self.__work_folder) if not f.startswith('.')]
        
        # 构建显示的字符串内容
        content = "当前目录内文件为:\n\n"
        for i, item in enumerate(self.__work_folder_items):
            content += f"{i}: {item}\n"
        self.__files_list_area.setPlainText(content)

    def __get_work_folder_indexs(self):
        # 将用户输入的索引字符串进行预处理
        temp = re.sub(r"\s+|,|，", r" ", self.__user_index.text()).split()
        wanted_items = []
        try:
            # 将字符串转换为整数列表
            self.__wanted_indexs = list(map(int, temp))
        except ValueError:
            # 如果转换失败，说明输入中有非整数，显示错误消息
            self.select_index_result_label.setText('输入包含非整数值')
            return

        # 检查是否提取到了有效的索引
        if not self.__wanted_indexs:
            self.select_index_result_label.setText('没有提取到有效输入')
            return

        # 检查索引是否在范围内
        for index in self.__wanted_indexs:
            if index < 0 or index >= len(self.__work_folder_items):
                self.select_index_result_label.setText(f'给出序号 {index} 超出范围')
                return
            else:
                wanted_items.append(self.__work_folder_items[index])

        # 如果所有检查通过，显示成功消息并发出信号
        self.select_index_result_label.setText('成功提取序号, 可以进行文件操作')
        self.selected_signal.emit(self.__work_folder, wanted_items)

##===========================调试用==============================
def simple_main():
    app = QApplication(sys.argv)
    window = FileWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    simple_main()