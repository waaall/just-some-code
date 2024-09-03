"""
    这个文件是把appsetting的具体设置和页面显示都写到了一起,因为
    这两个强相关, 如果需要修改某些设置相关的,在一个文件方面修改方便一些.
    需要注意的一点: 参数的名字要唯一, 唯一会让代码变得简单很多. 
"""

import os, sys
import json
# from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine, QObject, Signal
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

##=========================================================
##=======               软件设置参数类              =========
##=========================================================
class AppSettings(QObject):
    result_signal = Signal(str)
    def __init__(self):
        super().__init__()
        # 定义设置项名称到设置路径的映射
        self._settings_mapping = {
            "language": ("General", "language"),
            "autosave": ("General", "autosave"),
            "serial_baud_rate": ("Network", "Serial", "baud_rate"),
            "serial_data_bits": ("Network", "Serial", "data_bits"),
            "serial_stop_bits": ("Network", "Serial", "stop_bits"),
            "serial_parity": ("Network", "Serial", "parity"),
            "use_proxy": ("Network", "Internet", "use_proxy"),
            "proxy_address": ("Network", "Internet", "proxy_address"),
            "proxy_port": ("Network", "Internet", "proxy_port"),
            "resolution": ("Display", "Apparence", "resolution"),
            "fullscreen": ("Display", "Apparence", "fullscreen"),
            "theme": ("Display", "Apparence", "theme"),
            "motion_on": ("Display", "Motion", "motion_on"),
            "dicom_log_folder_name": ("Batch_Files", "Dicom", "dicom_log_folder_name"),
            "dicom_fps": ("Batch_Files", "Dicom", "fps"),
            "dicom_frame_dpi": ("Batch_Files", "Dicom", "frame_dpi"),
            "dicom_out_dir_suffix": ("Batch_Files", "Dicom", "dicom_out_dir_suffix"),
            "mergecolor_log_folder_name": ("Batch_Files", "MergeColor", "mergecolor_log_folder_name"),
            "mergecolor_out_dir_suffix": ("Batch_Files", "MergeColor", "mergecolor_out_dir_suffix"),
        }
        # 加载设置到成员变量
        self._load_settings()
    ##========================发送log信息========================##
    def send_message(self, message):
        print(message)
        self.result_signal.emit(message)

    # 加载设置到成员变量
    def _load_settings(self):
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建 settings.json 的完整路径, 并打开文件加载json数据
        self.settings_file = os.path.join(base_dir, 'configs', 'settings.json')
        with open(self.settings_file, 'r') as file:
            self._settings = json.load(file)
        for name, path in self._settings_mapping.items():
            value = self._get_value_from_path(path)
            setattr(self, name, value)

    # 保存设置到文件
    def save_settings(self, name, value):
        path = self._settings_mapping.get(name)
        if path:
            d = self._settings
            for key in path[:-1]:
                d = d.get(key, {})
            d[path[-1]] = value
            self.send_message(f"Updating setting: {path} = {value}")
        else:
            self.send_message(f"Setting '{name}' not found.")
            return False
        
        with open(self.settings_file, 'w') as file:
            json.dump(self._settings, file, indent=4)
            self.send_message(f"settings.json已保存")
            return True

    def _get_value_from_path(self, path):
        d = self._settings
        for key in path:
            d = d.get(key, {})
        return d

##=========================================================
##=======                 设置界面                 =========
##=========================================================
class SettingWindow(QWidget):
    result_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.settings.result_signal.connect(self.send_message)

        self.setWindowTitle('Settings')
        self.setGeometry(100, 100, 400, 400)

        window_layout = QHBoxLayout(self)

        # 侧边栏 - 显示设置组名
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(100)
        self.sidebar.setStyleSheet("QListWidget { font-size: 18px; }")

        # 添加列表项
        self.sidebar.addItem(QListWidgetItem("General"))
        self.sidebar.addItem(QListWidgetItem("Network"))
        self.sidebar.addItem(QListWidgetItem("Display"))
        self.sidebar.addItem(QListWidgetItem("Batch_Files"))

        # 调整项的行间距
        for index in range(self.sidebar.count()):
            item = self.sidebar.item(index)
            item.setSizeHint(QSize(item.sizeHint().width(), 40))

        self.sidebar.currentItemChanged.connect(self._display_settings)

        # 显示设置参数的区域
        self.parms_display = QScrollArea()
        self.parms_display.setWidgetResizable(True)
        self.parms_container = QWidget()
        self.page_layout = QVBoxLayout(self.parms_container)
        self.parms_display.setWidget(self.parms_container)

        window_layout.addWidget(self.sidebar)
        window_layout.addWidget(self.parms_display, stretch=1)

        self.setLayout(window_layout)

    ##========================发送log信息========================##
    def send_message(self, message):
        print(message)
        self.result_signal.emit(message)

    # 设置页面初始化
    def _display_settings(self, current, previous):
        page_name = current.text()
    
        # 清空当前显示
        for i in reversed(range(self.page_layout.count())):
            widget = self.page_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
        # 根据一级分类设置设置对应的显示组件
        if page_name == "General":
            self._add_setting("language", self.settings.language, options=["English", "French", "Spanish"])
            self._add_setting("autosave", self.settings.autosave, control_type="checkbox")
        elif page_name == "Network":
            self._add_group("Serial", {
                "serial_baud_rate": (self.settings.serial_baud_rate, "combo", [800, 1200, 2400, 4800, 9600, 14400, 19200, 38400]),
                "serial_data_bits": (self.settings.serial_data_bits, "combo", [4, 8]),
                "serial_stop_bits": (self.settings.serial_stop_bits, "combo", [1, 0]),
                "serial_parity": (self.settings.serial_parity, "combo", ["None", "Even", "Odd"])
            })
            self._add_group("Internet", {
                "use_proxy": (self.settings.use_proxy, "checkbox"),
                "proxy_address": (self.settings.proxy_address, "text"),
                "proxy_port": (self.settings.proxy_port, "text")
            })
        elif page_name == "Display":
            self._add_group("Apparence", {
                "theme": (self.settings.theme, "combo", ["Light", "Dark"]),
                "resolution": (self.settings.resolution, "combo", ["1920x1080", "1280x720", "800x600"]),
                "fullscreen": (self.settings.fullscreen, "checkbox")
            })
            self._add_group("Motion", {
                "motion_on": (self.settings.motion_on, "checkbox")
            })
        elif page_name == "Batch_Files":
            self._add_group("Dicom", {
                "dicom_log_folder_name": (self.settings.dicom_log_folder_name, "text"),
                "fps": (self.settings.dicom_fps, "combo", [10, 20, 30]),
                "frame_dpi": (self.settings.dicom_frame_dpi, "combo", [100, 200, 400, 800]),
                "dicom_out_dir_suffix": (self.settings.dicom_out_dir_suffix, "text")
            })
            self._add_group("MergeColor", {
                "mergecolor_log_folder_name": (self.settings.mergecolor_log_folder_name, "text"),
                "mergecolor_out_dir_suffix": (self.settings.mergecolor_out_dir_suffix, "text")
            })

    # 添加具体设置页面的分组
    def _add_group(self, group_name, settings_dict):
        group_box = QGroupBox(group_name)
        group_layout = QVBoxLayout()
        for name, (value, control_type, *options) in settings_dict.items():
            options = options[0] if options else None
            self._add_setting(name, value, options=options, control_type=control_type,layout=group_layout)
        group_box.setLayout(group_layout)
        self.page_layout.addWidget(group_box)  
        print(f"group {group_name} 添加到page")

    # 添加具体设置的显示组件
    def _add_setting(self, name, value, options=None, control_type="combo", layout=None):
        if layout is None:
            layout = self.page_layout
        if control_type == "combo" and options:
            combo = QComboBox()
            # 处理选项，检查是否为数字，如果是，转换为字符串显示
            str_options = [str(opt) for opt in options]
            combo.addItems(str_options)
            # 设置当前值，确保也是字符串形式
            combo.setCurrentText(str(value))
            
            # 更新设置值时，检查并转换回原始数据类型
            combo.currentIndexChanged.connect(lambda index: self._combo_changed_handler(combo, name, index, options[0]))
            
            layout.addWidget(QLabel(name))
            layout.addWidget(combo)
        elif control_type == "checkbox":
            checkbox = QCheckBox(name)
            checkbox.setChecked(value)
            checkbox.stateChanged.connect(lambda: self.update_setting(name, checkbox.isChecked()))
            layout.addWidget(checkbox)
        elif control_type == "text":
            # 使用 QLineEdit 文本编辑
            text_setting = QLineEdit()
            text_setting.setText(value)
            text_setting.textChanged.connect(lambda: self.update_setting(name, text_setting.text()))
            layout.addWidget(QLabel(name))
            layout.addWidget(text_setting)
    
    def _combo_changed_handler(self, combo, name, index, option):
        # 获取当前选项的文本
        text = combo.itemText(index)
        # 转换文本为原始数据类型
        value = self._convert_type(name, text, option)
        # 更新设置
        if value:
            self.update_setting(name, value)
    
    # 判断 options 中是否为数字，如果是，转换 text 为数字
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

    def update_setting(self, name, value):
        # 更新设置对象中的值
        if hasattr(self.settings, name):
            # 更新设置对象中的值
            setattr(self.settings, name, value)
            if self.settings.save_settings(name, value):
                self.send_message(f"「{name}」Settings Saved!")
            else:
                self.send_message(f"Error: 「{name}」Settings Not Saved!")
        else:
            self.send_message(f"Error:「{name}」 not found in settings.")

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 初始化设置页面
    trial = SettingWindow()
    trial.show()
    sys.exit(app.exec())
