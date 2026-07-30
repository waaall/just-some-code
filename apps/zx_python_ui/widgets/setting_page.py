import os, sys
# from PySide6.QtGui import *
# QPixmap, QIcon, QImage, QFont
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine, Signal
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget
# 获取当前文件所在目录,并加入系统环境变量(临时)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
from modules.app_settings import AppSettings
##=========================================================
##=======                 设置界面                 =========
##=========================================================
class SettingWindow(QWidget):
    result_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.main_categories = self.settings.get_main_categories()

        self.setWindowTitle('Settings')
        self.setGeometry(100, 100, 500, 500)

        #一个窗口的最小尺寸,分别代表左半和右半的最小宽度 & 上半和下半的最小高度
        self.window_minimum_size = [120, 350, 300, 300]
        main_layout = QHBoxLayout(self)
        
        self.__init_sidebar()
        # 初始化设置参数的页面
        self.pages_stack = QStackedWidget()
        self._initialize_all_pages()

        main_layout.addWidget(self.sidebar, stretch=1)
        # stretch=3 表示在其容器布局(main_layout)中,相比sidebar占据3倍空间
        main_layout.addWidget(self.pages_stack, stretch=3)

        self.setLayout(main_layout)
    
    ##======================初始化侧边栏======================##
    def __init_sidebar(self):
        # 侧边栏 - 显示设置组名
        self.sidebar = QListWidget()
        # 尽量不用setFixedWidth,用stretch和setMinimumWidth
        self.sidebar.setMinimumSize(self.window_minimum_size[0],self.window_minimum_size[2])
        self.sidebar.setStyleSheet("QListWidget { font-size: 16px; }")

        # 添加列表项
        for page_name in self.main_categories:
            self.sidebar.addItem(QListWidgetItem(page_name))

        # 调整项的行间距
        for index in range(self.sidebar.count()):
            item = self.sidebar.item(index)
            item.setSizeHint(QSize(item.sizeHint().width(), 40))

        # 绑定切换页面函数
        self.sidebar.currentItemChanged.connect(self._switch_page)

    ##======================页面切换回调======================##
    def _switch_page(self, current, previous):
        if not current:
            return
        # 切换到对应的页面索引
        self.pages_stack.setCurrentIndex(self.sidebar.currentRow())
    
    ##======================初始化所有页面======================##
    def _initialize_all_pages(self):
        for page_name in self.main_categories:
            # 创建一个新页面
            page_display = QScrollArea()
            page_display.setWidgetResizable(True)
            page_widget = QWidget()
            page_display.setMinimumSize(self.window_minimum_size[1],self.window_minimum_size[2])
            page_display.setWidget(page_widget)
            page_layout = QVBoxLayout(page_widget)
            setting_map = self.settings.get_setting_map(page_name)
            # 使用 generate_setting_components 生成页面的设置项
            self.__initialize_page(setting_map, page_layout)

            # 存储页面并添加到 QStackedLayout
            self.pages_stack.addWidget(page_display)

    ##======================初始化具体页面======================##
    def __initialize_page(self, setting_map, page_layout):
        # 根据一级分类设置设置对应的显示组件
        for name, options_and_path in setting_map.items():
            # 使用提取函数
            options, path = self.settings.extract_options_path(options_and_path)
            # 获取设置值
            value = getattr(self.settings,name,None)
            # 确定控件类型
            if options is not None:
                control_type = "combo"
            elif isinstance(value, bool):
                control_type = "checkbox"
            else:
                control_type = "text"

            # 根据 path 生成组件
            if len(path) == 2:  # 直接属于 main_category 的设置
                self.__add_setting(name, value, control_type, options, page_layout)
            elif len(path) > 2:  # 属于 group 的设置
                group_name = path[1]
                if not any(isinstance(w, QGroupBox) and w.title() == group_name for w in page_layout.parentWidget().findChildren(QGroupBox)):
                    group_box = QGroupBox(group_name)
                    group_layout = QVBoxLayout()
                    group_layout.setSpacing(20) #最小间距
                    group_box.setLayout(group_layout)
                    page_layout.addWidget(group_box)
                else:
                    group_box = next(w for w in page_layout.parentWidget().findChildren(QGroupBox) if w.title() == group_name)
                    group_layout = group_box.layout()
                self.__add_setting(name, value, control_type, options, group_layout)

    ##======================添加具体设置的显示组件======================##
    def __add_setting(self, name, value, control_type="text", options=None, layout=None):
        if control_type == "combo" and options:
            combo = QComboBox()
            
            # 处理选项，检查是否为数字，如果是，转换为字符串显示
            str_options = [str(opt) for opt in options]
            combo.addItems(str_options)
            combo.setCurrentText(str(value)) # 设置当前值，确保也是字符串形式          
            
            # 更新设置值时，检查并转换回原始数据类型
            combo.currentIndexChanged.connect(lambda index: self._combo_changed_handler(combo, name, index, options[0]))
            
            # 设置Label和combo的样式
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            child_layout = QFormLayout()
            child_layout.addRow(label, combo)# 标签和选项成对出现
            child_layout.setFormAlignment(Qt.AlignLeft)
            layout.addLayout(child_layout)

        elif control_type == "checkbox":
            checkbox = QCheckBox()
            checkbox.setChecked(value)
            checkbox.stateChanged.connect(lambda: self.update_setting(name, checkbox.isChecked()))
            
            # 设置Label和checkbox的样式
            label = QLabel(name)
            label.setAlignment(Qt.AlignTop)
            child_layout = QFormLayout()
            child_layout.addRow(label, checkbox)# 标签和选项成对出现
            child_layout.setFormAlignment(Qt.AlignLeft)
            layout.addLayout(child_layout)

        elif control_type == "text":
            # 使用 QLineEdit 文本编辑
            text_setting = QLineEdit()
            text_setting.setText(value)
            
            # 设置QLineEdit 的内容边距，只调整上下边距，水平边距不固定
            text_setting.setContentsMargins(-1, 2, -1, 2)
            text_setting.textChanged.connect(lambda: self.update_setting(name, text_setting.text()))
            
            # 设置Label和checkbox的样式
            label = QLabel(name)
            child_layout = QHBoxLayout()
            child_layout.addWidget(label)
            child_layout.addWidget(text_setting)
            layout.addLayout(child_layout)
    
    ##======================combo更新处理======================##
    def _combo_changed_handler(self, combo, name, index, option):
        # 获取当前选项的文本
        text = combo.itemText(index)
        # 转换文本为原始数据类型
        value = self._convert_type(name, text, option)
        # 更新设置
        if value:
            self.update_setting(name, value)
    
    #===========判断options中是否为数字,如果是,转换text为数字===========##
    def _convert_type(self, name, text, option):
        try:
            # 如果选项中的第一个元素是数字，尝试转换
            if isinstance(option, (int, float)):
                converted_value = type(option)(text)
                return converted_value
        except ValueError as e:
            self.send_message(f" {name} 处理失败: {e}")
            return False
        return text

    #======================更新设置======================##
    def update_setting(self, name, value):
        # 更新设置对象中的值
        if hasattr(self.settings, name):
            # 更新设置对象中的值
            setattr(self.settings, name, value)
            if self.settings.save_settings(name, value):
                self.send_message(f"Updating setting: {name} = {value}")
            else:
                self.send_message(f"Error: failed to save setting: {name}-{value}")
        else:
            self.send_message(f"Error:「{name}」 not found in settings.")

    ##=====================发送log信息=====================##
    def send_message(self, message):
        print(f"From SettingWindow:\n\t{message}\n")
        self.result_signal.emit(message)

##========================调试用===========================##
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 初始化设置页面
    trial = SettingWindow()
    trial.show()
    sys.exit(app.exec())