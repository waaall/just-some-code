import os, sys, re
# from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

##=========================================================
##=======                图表制作界面               =========
##=========================================================

class PlotWindow(QWidget):    
    def __init__(self):
        super().__init__()
        # 创建布局
        self.layout = QVBoxLayout()

        # 上半部分
        self.file_button = QPushButton("选择文件")
        self.file_button.clicked.connect(self.load_file)
        self.data_label = QLabel("选择的数据文件路径将在这里显示")
        
        # 下半部分
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        # 添加部件到布局
        self.layout.addWidget(self.file_button)
        self.layout.addWidget(self.data_label)
        self.layout.addWidget(self.canvas)
        
        self.setLayout(self.layout)

    def load_file(self):
        # 打开文件对话框
        file_name, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "Text Files (*.txt);;CSV Files (*.csv)")
        if file_name:
            self.data_label.setText(f"已选择文件: {file_name}")
            self.plot_data(file_name)

    def plot_data(self, file_name):
        # 清除当前图形
        self.figure.clear()
        
        # 读取数据
        try:
            data = self.read_data(file_name)
            if data:
                # 绘制图形
                ax = self.figure.add_subplot(111)
                ax.plot(data, marker='o', linestyle='-')
                ax.set_title("数据图表")
                ax.set_xlabel("X 轴")
                ax.set_ylabel("Y 轴")
                
                # 更新画布
                self.canvas.draw()
            else:
                self.data_label.setText("数据文件格式错误或为空")
        except Exception as e:
            self.data_label.setText(f"读取数据时出错: {str(e)}")

    def read_data(self, file_name):
        # 读取文件数据并返回
        try:
            with open(file_name, 'r') as file:
                # 假设数据文件每行一个数值
                data = [float(line.strip()) for line in file if line.strip()]
            return data
        except Exception as e:
            self.data_label.setText(f"读取数据时出错: {str(e)}")
            return []
        
##===============调试用==================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = PlotWindow()
    trial.show()
    sys.exit(app.exec())