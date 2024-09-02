import os, sys
# from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

# 获取当前项目根目录,并加入系统环境变量(临时)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 从 modules 目录中导入 AppSettings
from modules.app_settings import AppSettings
##=========================================================
##=======                 帮助界面                 =========
##=========================================================

class SettingWindow(QWidget):
    save_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.settings = AppSettings()

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

        # 调整项的行间距
        for index in range(self.sidebar.count()):
            item = self.sidebar.item(index)
            item.setSizeHint(QSize(item.sizeHint().width(), 40))

        self.sidebar.currentItemChanged.connect(self.display_group_settings)

        # 显示设置参数的区域
        self.parms_display = QScrollArea()
        self.parms_display.setWidgetResizable(True)
        self.parms_container = QWidget()
        self.parms_container_layout = QVBoxLayout(self.parms_container)
        self.parms_display.setWidget(self.parms_container)

        window_layout.addWidget(self.sidebar)
        window_layout.addWidget(self.parms_display, stretch=1)

        self.setLayout(window_layout)

    def display_group_settings(self, current, previous):
        group_name = current.text()

        # 清空当前显示
        for i in reversed(range(self.parms_container_layout.count())):
            widget = self.parms_container_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 根据组名显示设置
        if group_name == "General":
            self.add_setting("Language", self.settings.language, options=["English", "French", "Spanish"])
            self.add_setting("Theme", self.settings.theme, options=["Light", "Dark"])
            self.add_setting("Autosave", self.settings.autosave, control_type="checkbox")
        elif group_name == "Network":
            self.add_setting("Use Proxy", self.settings.use_proxy, control_type="checkbox")
            self.add_setting("Proxy Address", self.settings.proxy_address, control_type="text")
            self.add_setting("Proxy Port", self.settings.proxy_port, control_type="text")
        elif group_name == "Display":
            self.add_setting("Resolution", self.settings.resolution, options=["1920x1080", "1280x720", "800x600"])
            self.add_setting("Fullscreen", self.settings.fullscreen, control_type="checkbox")

    def add_setting(self, name, value, options=None, control_type="combo"):
        if control_type == "combo" and options:
            combo = QComboBox()
            combo.addItems(options)
            combo.setCurrentText(value)
            combo.currentIndexChanged.connect(lambda: self.update_setting(name, combo.currentText()))
            self.parms_container_layout.addWidget(combo)
        elif control_type == "checkbox":
            checkbox = QCheckBox(name)
            checkbox.setChecked(value)
            checkbox.stateChanged.connect(lambda: self.update_setting(name, checkbox.isChecked()))
            self.parms_container_layout.addWidget(checkbox)
        elif control_type == "text":
            label = QLabel(f"{name}: {value}")
            self.parms_container_layout.addWidget(label)

    def update_setting(self, name, value):
        # 更新设置对象中的值
        setattr(self.settings, name.lower().replace(" ", "_"), value)
        self.settings.save_settings()
        self.save_signal.emit(f"「{name}」Settings saved!")

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 初始化设置页面
    trial = SettingWindow()
    trial.show()
    sys.exit(app.exec())
