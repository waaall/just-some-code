#该库是操作系统相关函数库
import os
import platform

#该库是系统功能性库
from datetime import datetime

#该库为json解析库，用于保存和更改设置
import json

#该库是数学/表格运算库
import numpy as np
import pandas as pd

#该库用来导入导出excel
# import xlrd
# import xlwt
import openpyxl

#该库是可视化库
from PySide6.QtWidgets import (
    QApplication, QTableView, QVBoxLayout, QPushButton, QWidget, 
    QLabel, QAbstractItemDelegate, QStyledItemDelegate, QDateTimeEdit, 
    QHBoxLayout, QDialog, QToolBar, QLineEdit
)
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QAction, QKeyEvent, QIcon

##=========================================================
##=======                  设置                   =========
##=========================================================
BackupFolder = '../data/backup'        # 数据所在的文件夹
FileName = '../data/2024年考核目标软件内容'
SettingFileName = '../resourse/settings.json'
Modifiable_columns = [0,1,2,3,4,5,6,7]
ReminderDays = 7
#-----------安装/打包-----------
#pyinstaller --onedir --windowed --name "项目绩效追踪App" --icon=branden.ico --hidden-import plyer.platforms.win.notification .\Countdown_to_appraisal_beta5.py

#-------设置每天定时打开-------
# Windows系统搜索：任务计划程序。
# 在右侧操作面板中选择“创建基本任务…”。
# 按提示填写任务名称和描述，比如“项目绩效追踪提醒”。
# 选择触发器，例如“每天”或“登录时”，并设置具体的时间或条件。
# 在操作步骤中，选择“启动程序”，然后选择**.exe文件。
# 完成设置并保存任务。

##=========================================================
##=======                 函数/类                 =========
##=========================================================·

# 读取和处理数据
def load_data():
    df = pd.read_excel(f"{FileName}.xlsx", parse_dates=['要求完成时间'], index_col=0)
    df = df.dropna(how="all")
    # df['要求完成时间'] = pd.to_datetime(df['要求完成时间'])
    df['倒计时'] = (df['要求完成时间'] - pd.Timestamp(datetime.now())).dt.days
    df['要求完成时间'] = df['要求完成时间'].dt.date

    return df.sort_values(by='倒计时')  # 按倒计时天数排序

# 日期选择委托
class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDateTimeEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("yyyy-MM-dd")
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.EditRole)
        # 如果是，可以选择设置一个默认日期，例如当前日期
        if pd.isnull(date_str):
            editor.setDate(pd.Timestamp(datetime.now()).date())
        editor.setDate(pd.to_datetime(date_str).date())

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date().toString("yyyy-MM-dd"), Qt.EditRole)

# 设置页面
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        layout = QVBoxLayout(self)

        # 文件名设置
        layout.addWidget(QLabel("文件名:"))
        self.fileNameEdit = QLineEdit(self)
        layout.addWidget(self.fileNameEdit)

        # 提醒天数设置
        layout.addWidget(QLabel("提醒天数:"))
        self.reminderDaysEdit = QLineEdit(self)
        layout.addWidget(self.reminderDaysEdit)

        # 保存按钮
        saveBtn = QPushButton("保存")
        saveBtn.clicked.connect(self.saveSettings)
        layout.addWidget(saveBtn)

    def saveSettings(self):
        settings = {
            "FileName": self.fileNameEdit.text(),
            "ReminderDays": self.reminderDaysEdit.text()
        }
        with open(SettingFileName, "w") as f:
            json.dump(settings, f, indent=4)
        self.accept()

# Pandas Model
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [Qt.EditRole])
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
         # 此为可修改列
        if index.column() in Modifiable_columns: 
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            else:
                return section

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        for _ in range(rows):
            # 添加空行
            empty_line = []
            for x in Modifiable_columns:
                empty_line.append('')
            self._data = pd.concat([self._data.iloc[:position], pd.DataFrame([empty_line], columns=self._data.columns), self._data.iloc[position:]]).reset_index(drop=True)
        self.endInsertRows()
        return self._data

    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        self._data = self._data.drop(self._data.index[position:position+rows]).reset_index(drop=True)
        self.endRemoveRows()
        return self._data

# 主窗口
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("项目绩效追踪App")  # 设置窗口的标题
        self.setWindowIcon(QIcon('../resourse/branden.ico'))  # 设置窗口图标
        
        ## 
        self.layout = QVBoxLayout()
        self.table_view = QTableView()

        self.buttons_up_layout = QHBoxLayout()  # 水平布局用于按钮
        self.update_button = QPushButton('更新倒计时')
        self.backup_button = QPushButton('备份数据')
        self.save_button = QPushButton('保存数据')

        self.buttons_up_layout.addWidget(self.backup_button)
        self.buttons_up_layout.addWidget(self.save_button)
        self.buttons_up_layout.addWidget(self.update_button)

        self.buttons_down_layout = QHBoxLayout()  # 水平布局用于按钮
        self.add_row_button = QPushButton("增加行")
        self.delete_row_button = QPushButton("删除选中行")
        self.buttons_down_layout.addWidget(self.add_row_button)
        self.buttons_down_layout.addWidget(self.delete_row_button)

        self.info_label = QLabel('准备就绪')

        self.layout.addLayout(self.buttons_up_layout)
        self.layout.addWidget(self.table_view)
        self.layout.addLayout(self.buttons_down_layout)
        self.layout.addWidget(self.info_label)

        self.setLayout(self.layout)
        self.df = load_data()
        self.save_data()
        self.load_table_data()
        self.backup_data()
        self.table_view.setItemDelegateForColumn(3, DateDelegate())  # 第4列使用日期选择器

        # 按钮事件
        self.update_button.clicked.connect(self.load_table_data)
        self.backup_button.clicked.connect(self.backup_data)
        self.save_button.clicked.connect(self.save_data)
        self.add_row_button.clicked.connect(self.add_row)
        self.delete_row_button.clicked.connect(self.delete_row)

    def add_row(self):
        row_count = self.model.rowCount()
        self.df = self.model.insertRows(row_count, 1)

    def delete_row(self):
        selected_indexes = self.table_view.selectedIndexes()
        rows = set(index.row() for index in selected_indexes)
        for row in sorted(rows, reverse=True):
            self.df = self.model.removeRows(row, 1)

    def load_table_data(self):
        self.save_data()
        self.df = load_data()
        self.model = PandasModel(self.df)
        self.table_view.setModel(self.model)
        self.adjust_table_width()
        self.info_label.setText('数据已更新')
        self.check_reminders()  # 检查是否需要发送提醒

    def check_reminders(self):
        # 遍历DataFrame检查倒计时
        for index, row in self.df.iterrows():
            if row['倒计时'] <= ReminderDays:
                self.send_reminder(row['负责人'], row['考核指标'], row['倒计时'])

    def send_reminder(self, name, task, days_left):
        current_platform = platform.system()

        if current_platform == 'Darwin':  # macOS
            import pync
            # 还需要安装terminal-notifier
            # brew install terminal-notifier
            pync.notify(
                title='任务提醒',
                message=f'{name}的考核指标 "{task}" 还有 {days_left} 天到期。'
            )

        elif current_platform == 'Windows':  # Windows
            from plyer import notification
            # 使用plyer发送Windows通知
            notification.notify(
                title='任务提醒',
                message=f'{name}的考核指标 "{task}" 还有 {days_left} 天到期。',
                app_name='项目绩效追踪软件'
            )

        elif current_platform == 'Linux':  # Linux
            import notify2
            notify2.init('MyApp')
            n = notify2.Notification(
                title='任务提醒',
                message=f'{name}的考核指标 "{task}" 还有 {days_left} 天到期。'
            )
            n.show()

        else:
            print(f'Unsupported platform: {current_platform}')


    def adjust_table_width(self):
        self.table_view.resizeColumnsToContents()
        width = self.table_view.verticalHeader().width()
        width += self.table_view.horizontalHeader().length()
        if self.table_view.verticalScrollBar().isVisible():
            width += self.table_view.verticalScrollBar().width()
        width += self.table_view.frameWidth() * 2
        self.resize(width, self.height())

    def backup_data(self):
        # 获取当前日期和时间
        now = datetime.now()
        # 格式化日期时间字符串，例如 '2024-01-27-15-45-30'
        formatted_date = now.strftime('%Y-%m-%d-%H-%M-%S')

        # 设置备份文件的名称，包括日期时间
        backup_filename = f'{BackupFolder}/backup-{formatted_date}.xlsx'
        self.df.to_excel(backup_filename)
        self.info_label.setText(f"数据已备份到 '{backup_filename}'")

    def save_data(self):
        # 保存数据到原文件或新文件
        self.df.to_excel(f"{FileName}.xlsx")  # 保存到原文件，也可以指定新文件名
        self.info_label.setText('数据已保存')

##=========================================================
##=======                  主代码                 =========
##=========================================================
# 创建应用程序实例
app = QApplication([])
# 创建主窗口
window = MainWindow()

# 显示主窗口
window.show()

# 运行应用程序
app.exec()