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
        self.workfolder_group = QGroupBox("一:begin",self)
        group_layout = QVBoxLayout()

        chooseFolderBut = QPushButton(f"1.选择工作目录", self)
        group_layout.addWidget(chooseFolderBut)
        chooseFolderBut.clicked.connect(self.__get_work_folder)
        
        # 用来显示工作目录内的文件和文件夹
        files_layout = QHBoxLayout()
 
        select_layout = QVBoxLayout()
        hint_lable1 = QLabel('2.请选择想要处理的序号:',self)
        hint_lable1.setMaximumWidth(150)
        select_layout.addWidget(hint_lable1)

        self.__user_index = QLineEdit(self)
        self.__user_index.setMaximumWidth(150)
        select_layout.addWidget(self.__user_index)

        self.get_select_file_but = QPushButton('3.提取选中序号',self)
        self.get_select_file_but.setMaximumWidth(150)
        self.get_select_file_but.clicked.connect(self.__get_work_folder_indexs)
        select_layout.addWidget(self.get_select_file_but)

        # lable本用来显示执行结果，后决定传递变量由controler显示
        self.get_select_result = QLabel(self)
        select_layout.addWidget(self.get_select_result)

        # 这几个layout层级嵌套
        files_layout.addLayout(select_layout)

        self.__work_folder_label = QPlainTextEdit(self)
        self.__work_folder_label.setReadOnly(True)
        files_layout.addWidget(self.__work_folder_label)
    
        group_layout.addLayout(files_layout)
        self.workfolder_group.setLayout(group_layout)

    ##===============创建文件的具体操作界面=================
    def __init_file_option_group(self):
        self.file_option_group = QGroupBox('二:文件操作',self)
        file_option_layout = QHBoxLayout(self)

        # 创建侧边栏
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        self.sidebar.setStyleSheet("QListWidget { font-size: 16px; }")
        self.sidebar.currentItemChanged.connect(self._switch_file_option)

        # 创建显示内容的区域
        self.file_options_stack = QStackedWidget()
        # self.file_options_stack.setSizePolicy(self.sizePolicy())

        # 添加侧边栏和显示区域
        file_option_layout.addWidget(self.sidebar)
        file_option_layout.addWidget(self.file_options_stack, stretch=1)
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
                result_display.moveCursor(QPlainTextEdit().textCursor().End)

    #     # 第一个file操作按钮
    #     self.file_but1 = QPushButton('file_but1',self)
    #     group_layout.addWidget(self.file_but1, 0,0)

    #     # 第一个file操作按钮的执行信息显示
    #     self.file_but1_result = QPlainTextEdit(self)
    #     self.file_but1_result.setReadOnly(True)
    #     group_layout.addWidget(self.file_but1_result, 1,0)

    #     # 第二个file操作按钮
    #     self.file_but2 = QPushButton('file_but2',self)
    #     # self.file_but2.setToolTip('')
    #     self.file_but2.resize(self.file_but2.sizeHint())
    #     # self.file_but2.clicked.connect(self.copyIntimeFile)
    #     group_layout.addWidget(self.file_but2, 0,1)
        
    #     # 第二个file操作按钮的执行信息显示
    #     self.file_but2_result = QPlainTextEdit(self)
    #     self.file_but2_result.setReadOnly(True)
    #     group_layout.addWidget(self.file_but2_result, 1,1)

    #     self.file_option_group.setLayout(group_layout)

    # def bind_file_but1(self, new_name, slot_func):
    #     self.file_but1.setText(new_name)
    #     self.file_but1.clicked.connect(slot_func)

    # def bind_file_but2(self, new_name, slot_func):
    #     self.file_but2.setText(new_name)
    #     self.file_but2.clicked.connect(slot_func)

    # ## 显示file_but1的操作执行结果
    # def set_file_but1_result(self, messages):
    #     self.file_but1_result.appendPlainText(messages)
    #     self.file_but1_result.moveCursor(QTextCursor.End)

    # ## 显示file_but2的操作执行结果
    # def set_file_but2_result(self, messages):
    #     self.file_but2_result.appendPlainText(messages)
    #     self.file_but2_result.moveCursor(QTextCursor.End)

    def __get_work_folder(self):
        self.__work_folder = QFileDialog.getExistingDirectory(self,"选择目录","./")
        self.__work_folder_items = os.listdir(self.__work_folder)
        # 构建显示的字符串内容
        content = "当前目录内文件为:\n\n"
        for i, item in enumerate(self.__work_folder_items):
            content += f"{i}: {item}\n"
        self.__work_folder_label.setPlainText(content)

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
        self.get_select_result.setText('成功提取序号, 可以进行文件操作')
        self.selected_signal.emit(self.__work_folder, wanted_items)

##===========================调试用==============================
def simple_main():
    app = QApplication(sys.argv)
    window = FileWindow()
    window.show()
    sys.exit(app.exec())

def total_main():
    from main import BatchFilesBinding
    from modules.dicom_to_imgs import DicomToImage
    from modules.merge_colors import MergeColors
    # 初始化app
    app = QApplication(sys.argv)
    window = FileWindow()
    ##============================绑定mergeRGs===============================
    # 初始化绑定
    merge_colors_bind = BatchFilesBinding(MergeColors(), '颜色通道合成')
    # file_window信号数据selected_signal传入绑定对象merge_colors_bind
    window.selected_signal.connect(merge_colors_bind.get_user_select)
    # dicom对象信息信号绑定file_window显示
    merge_colors_bind.handler_object.result_signal.connect(window.set_operation_result)
    # file_window操作按钮绑定modules的操作
    window.bind_file_but1(merge_colors_bind.bind_name, merge_colors_bind.handler_binding)

    ##=============================绑定dicom================================
    # 初始化dicom绑定
    dicom_bind = BatchFilesBinding(DicomToImage(), 'DICOM处理')
    # file_window信号数据selected_signal传入绑定对象dicom_bind
    window.selected_signal.connect(dicom_bind.get_user_select)
    # dicom对象信息信号绑定file_window显示
    dicom_bind.handler_object.result_signal.connect(window.set_operation_result)
    # file_window操作按钮绑定modules的操作
    window.bind_file_but2(dicom_bind.bind_name, dicom_bind.handler_binding)

    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    simple_main()
    # total_main()