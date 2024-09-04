"""
    这个文件是把appsetting的具体设置和页面显示都写到了一起,因为
    这两个强相关, 如果需要修改某些设置相关的,在一个文件方面修改方便一些.
    需要注意的几点: 
        1. 「设置项变量名称」要唯一, 
        2. 参数path[-1]的名字要与对应接收类的参数名一致
        3. 参数path[-2]的名字要与对应接收类的类名一致
        4. 增加设置**需要在 settings.json 和 AppSettings类中增加 **_Settingmap
"""
import os, sys
import json
# from PySide6.QtGui import QFont
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine, QObject, Signal
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

##=========================================================
##=======               软件设置参数类              =========
##=========================================================
class AppSettings(QObject):
    changed_signal = Signal(str, str, object)
    def __init__(self):
        super().__init__()
        """
            定义「设置项变量名称」到设置路径的映射, 附加选项在value第一项(如果有)
            **_Settingmap 命名要与json key 和 value的path[0]一致
        """
        self.General_Settingmap = {
            "language":         (["English", "French", "Spanish"], "General", "language"),
            "autosave":         ("General", "autosave")
        }
        self.Network_Settingmap = {
            "serial_baud_rate": ([800, 1200, 2400, 4800, 9600, 14400, 19200, 38400], "Network", "Serial", "baud_rate"),
            "serial_data_bits": ([4, 8], "Network", "Serial", "data_bits"),
            "serial_stop_bits": (["1", "0", "None"], "Network", "Serial", "stop_bits"),
            "serial_parity":    (["None", "Even", "Odd"], "Network", "Serial", "parity"),
            "use_proxy":        ("Network", "Internet", "use_proxy"),
            "proxy_address":    ("Network", "Internet", "proxy_address"),
            "proxy_port":       ("Network", "Internet", "proxy_port")
        }
        self.Display_Settingmap = {
            "resolution":       (["1920x1080", "1280x720", "800x600"], "Display", "Apparence", "resolution"),
            "fullscreen":       ("Display", "Apparence", "fullscreen"),
            "theme":            (["Light", "Dark"], "Display", "Apparence", "theme"),
            "motion_on":        ("Display", "Motion", "motion_on")
        }
        self.Batch_Files_Settingmap = {
            "dicom_log_folder_name": ("Batch_Files", "DicomToImage", "log_folder_name"),
            "dicom_fps":        ([10, 20, 30], "Batch_Files", "DicomToImage", "fps"),
            "dicom_frame_dpi":  ([100, 200, 400, 800], "Batch_Files", "DicomToImage", "frame_dpi"),
            "dicom_out_dir_suffix": ("Batch_Files", "DicomToImage", "out_dir_suffix"),
            "mergecolor_log_folder_name": ("Batch_Files", "MergeColors", "log_folder_name"),
            "mergecolor_out_dir_suffix": ("Batch_Files", "MergeColors", "out_dir_suffix"),
        }
        # 加载设置到成员变量
        self._load_settings()

    # 加载设置到成员变量
    def _load_settings(self):
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建 settings.json 的完整路径, 并打开文件加载json数据
        self.settings_file = os.path.join(base_dir, 'configs', 'settings.json')
        with open(self.settings_file, 'r') as file:
            self.__settings_json = json.load(file)
        
        # 提取第一级键作为main_categories
        self.__main_categories = list(self.__settings_json.keys())

        # 将设置的json数据加载到具体的变量中
        for category in self.__main_categories:
            setting_map = self.get_setting_map(category)
            for name, options_path in setting_map.items():
                _, path = self.extract_options_path(options_path)
                value = self.get_value_from_path(path)
                setattr(self, name, value)
    
    # 根据 category_name 动态获取对应的 Settingmap
    def get_setting_map(self, category_name):
        setting_map_name = f"{category_name}_Settingmap"
        return getattr(self, setting_map_name, {})

    # 从 options_path 中提取 path 和 options
    def extract_options_path(self, options_path):
        if isinstance(options_path[0], list):
            options = options_path[0]
            path = options_path[1:]
        else:
            options = None
            path = options_path
        return options, path

    def get_main_categories(self):       
        return self.__main_categories

    def get_value_from_path(self, path):
        d = self.__settings_json
        for key in path:
            d = d.get(key, {})
        return d

    # 保存设置到文件
    def save_settings(self, name, value):
        # 遍历几个setting_map找到name,解析出path就break
        for category in self.__main_categories:
            setting_map = self.get_setting_map(category)
            options_path = setting_map.get(name)
            if options_path:
                _, path = self.extract_options_path(options_path)
                break
        if path:
            d = self.__settings_json
            for key in path[:-1]:
                d = d.get(key, {})
            d[path[-1]] = value
            print(f"From AppSettings:\n\tUpdating setting: {path} = {value}\n")
        else:
            print(f"From AppSettings:\n\tSetting '{name}' not found\n")
            return False
        
        # 发送信号(类名,参数名和值), 通知设置修改
        self.changed_signal.emit(path[-2], path[-1], value)
        try:
            with open(self.settings_file, 'w') as file:
                json.dump(self.__settings_json, file, indent=4)
                return True
        except:
            print(f"From AppSettings:\n\tError to save {name}-{value}\n")
            return False

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

        window_layout = QHBoxLayout(self)
        self.__init_sidebar()
        
        # 初始化设置参数的页面
        self.pages_stack = QStackedWidget()
        self._initialize_all_pages()

        window_layout.addWidget(self.sidebar)
        # stretch 表示在其容器布局(window_layout)中能够伸展, 占据更多的空间
        window_layout.addWidget(self.pages_stack, stretch=1)

        self.setLayout(window_layout)
    
    ##======================初始化侧边栏======================##
    def __init_sidebar(self):
        # 侧边栏 - 显示设置组名
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(100)
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
            # 设置当前值，确保也是字符串形式
            combo.setCurrentText(str(value))
            
            # 更新设置值时，检查并转换回原始数据类型
            combo.currentIndexChanged.connect(lambda index: self._combo_changed_handler(combo, name, index, options[0]))
            
            # 设置Label和combo的样式
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            form_layout = QFormLayout()
            # 标签和选项成对出现
            form_layout.addRow(label, combo)
            form_layout.setFormAlignment(Qt.AlignLeft)
            layout.addLayout(form_layout)

        elif control_type == "checkbox":
            checkbox = QCheckBox()
            checkbox.setChecked(value)
            checkbox.stateChanged.connect(lambda: self.update_setting(name, checkbox.isChecked()))
            # 设置Label和checkbox的样式
            label = QLabel(name)
            label.setAlignment(Qt.AlignTop)
            form_layout = QFormLayout()
            # 标签和选项成对出现
            form_layout.addRow(label, checkbox)
            form_layout.setFormAlignment(Qt.AlignLeft)
            layout.addLayout(form_layout)
        elif control_type == "text":
            # 使用 QLineEdit 文本编辑
            text_setting = QLineEdit()
            text_setting.setText(value)
            # 设置QLineEdit 的内容边距，只调整上下边距，水平边距不固定
            text_setting.setContentsMargins(-1, 2, -1, 2)
            text_setting.textChanged.connect(lambda: self.update_setting(name, text_setting.text()))
            # 设置Label和checkbox的样式
            label = QLabel(name)
            form_layout = QFormLayout()
            form_layout.setFormAlignment(Qt.AlignLeft)
            form_layout.addRow(label,text_setting)
            layout.addLayout(form_layout)
    
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
