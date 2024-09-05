import os, sys , random
# from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget
from pyqtgraph import PlotWidget, mkPen

##=========================================================
##=======                图表制作界面               =========
##=========================================================

class PlottingWindow(QWidget):    
    def __init__(self):
        super().__init__()

        # 设置主窗口
        self.setWindowTitle("波形显示系统")
        self.setGeometry(100, 100, 1000, 600)

        # 创建布局
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # 创建左侧波形显示区域
        left_layout = QVBoxLayout()
        self.plot_widget1 = PlotWidget()  # 第一个波形显示
        self.plot_widget2 = PlotWidget()  # 第二个波形显示

        # 初始化波形曲线
        self.curve1 = self.plot_widget1.plot(pen=mkPen('r'))
        self.curve2 = self.plot_widget2.plot(pen=mkPen('b'))

        # 添加到左侧布局
        left_layout.addWidget(self.plot_widget1)
        left_layout.addWidget(self.plot_widget2)

        # 创建右侧按钮区域
        right_layout = QVBoxLayout()
        button_start = QPushButton("开始")
        button_stop = QPushButton("停止")
        button3 = QPushButton("保存")
        button4 = QPushButton("加载")

        # 按钮信号槽
        button_start.clicked.connect(self.start_plot)
        button_stop.clicked.connect(self.stop_plot)

        # 将按钮添加到右侧布局
        right_layout.addWidget(button_start)
        right_layout.addWidget(button_stop)
        right_layout.addWidget(button3)
        right_layout.addWidget(button4)

        # 将左侧波形和右侧按钮布局添加到主布局
        main_layout.addLayout(left_layout, stretch=3)  # 左侧占大部分空间
        main_layout.addLayout(right_layout, stretch=1)

        # 创建定时器用于更新波形
        self.data_buffer1 = []
        self.data_buffer2 = []
        self.max_buffer_size = 100
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def open_file(self):
        # 打开文件对话框
        file_name, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "All Files (*);;Text Files (*.txt)")
        if file_name:
            print(f"打开了文件: {file_name}")

    def save_file(self):
        # 保存文件对话框
        file_name, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "All Files (*);;Text Files (*.txt)")
        if file_name:
            print(f"保存到文件: {file_name}")

    def update_plot(self):
        # 生成随机数据，模拟波形更新
        data1 = [random.randint(-100, 100)]
        data2 = [random.randint(-50, 50)]

        # 更新第一个波形的数据
        self.data_buffer1.extend(data1)
        if len(self.data_buffer1) > self.max_buffer_size:
            self.data_buffer1 = self.data_buffer1[-self.max_buffer_size:]
        self.curve1.setData(self.data_buffer1)

        # 更新第二个波形的数据
        self.data_buffer2.extend(data2)
        if len(self.data_buffer2) > self.max_buffer_size:
            self.data_buffer2 = self.data_buffer2[-self.max_buffer_size:]
        self.curve2.setData(self.data_buffer2)
    
    def stop_plot(self):
        self.timer.stop()

    def start_plot(self):
        self.timer.start(50)
##===============调试用==================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = PlottingWindow()
    trial.show()
    sys.exit(app.exec())