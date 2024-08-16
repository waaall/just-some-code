import sys, time
from functools import partial
from PySide6.QtGui import *
# QPixmap, QPainter
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QTextEdit, QWidget

from widgets.dock_widget import DockWindow
from widgets.help_page import HelpWindow
from widgets.file_page import FileWindow
from widgets.images_page import ImagesHanderWindow
from widgets.plot_page import PlotWindow

##=========================================================
##=======                 主界面类                 =========
##=========================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        
        #初始化一些组件的名字
        self.__file_stack_name = 'stack_file'
        self.__plot_stack_name = 'stack_plot'
        self.__help_stack_name = 'stack_help'
        
        #初始化StatusBar
        self.createStatusBar()

        # 初始化主窗口(centralWidget)和Dock
        # 注意有一些顺序是不能更改的，因为有依赖关系
        self.__init_dock()
        self.__init_stack_windows()
        self.setCentralWidget(self.Stack)
        
        #初始化menu bar
        self.__createActions()
        self.__createMenu()
        self.setWindowTitle("Branden_Tools")
        
        ##================bind options ==================
        self.bind_dock_options()

    def bind_dock_options(self):
        #链接button和stack窗口切换的链接, 添加绑定需要在函数__init_stack_windows中初始化对应页面
        self.dock_window.bind_dock2_but1('通信画图操作',partial(self.switch_stack, self.__plot_stack_name))
        self.dock_window.bind_dock3_but1('文件操作',partial(self.switch_stack, self.__file_stack_name))

    ##=======================左边Dock栏=======================
    def __init_dock(self):
        # 检查是否已经有一个 'dock'
        if hasattr(self, 'dock'):
            return  # 如果存在，直接返回，不创建新的 dock
        self.dock = QDockWidget()
        self.dock.setWindowTitle('工作目录')
        self.dock_window = DockWindow()
        self.dock.setWidget(self.dock_window)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
    
    def show_dock_window(self):
        # 检查是否已经有一个 'dock_window'
        if hasattr(self, 'dock'):
            self.dock.show()
            self.statusBar().showMessage("dock重新打开")
            return  # 如果存在，直接返回，不创建新的 dock
        else:
            self.statusBar().showMessage("初始化dock")
            self.__init_dock()

    ##=======设置多个窗口“同时”在主窗口的stack布局========
    def __init_stack_windows(self):
        self.Stack = QStackedWidget()
        self.Stack.addWidget(QWidget())

        self.help_window = HelpWindow()
        self.Stack.addWidget(self.help_window)
        self.help_window.setObjectName(self.__help_stack_name)
        self.help_window.userBut.clicked.connect(self.show_user_help)
        self.help_window.devBut.clicked.connect(self.show_dev_help)
        # self.Stack.setCurrentIndex(1)

        # 实例化plotwindow, 并将其添加到stackwindow中
        self.plot_window = PlotWindow()
        self.Stack.addWidget(self.plot_window)
        self.plot_window.setObjectName(self.__plot_stack_name)

        # 实例化filewindow, 并将其添加到stackwindow中
        self.file_window = FileWindow()
        self.Stack.addWidget(self.file_window)
        self.file_window.setObjectName(self.__file_stack_name)

    ##=======================主界面的功能区=======================
    def createStatusBar(self):
        self.statusBar().showMessage("一切就绪, 确保您阅读文档, 再进行操作")

    def __createActions(self):
        # 创建 QAction 对象
        self.help_act = QAction("打开帮助", self, statusTip="帮助界面")
        # 连接 triggered 信号到槽函数，传递参数
        self.help_act.triggered.connect(partial(self.switch_stack, self.__help_stack_name))
        self.userHelpAct = QAction("使用文档",statusTip="使用文档")

        self.userHelpAct.triggered.connect(self.show_user_help)
        self.devHelpAct = QAction("开发文档", statusTip="开发文档")
        self.devHelpAct.triggered.connect(self.show_dev_help)

        self.openDockAct = QAction("打开导航", statusTip="重新打开导航栏")
        self.openDockAct.triggered.connect(self.show_dock_window)

    def __createMenu(self):
        self.windowMenu = self.menuBar().addMenu("窗口")
        self.windowMenu.addAction(self.openDockAct)
        self.windowMenu.addAction(self.help_act)

        self.helpMenu = self.menuBar().addMenu("帮助")
        self.helpMenu.addAction(self.help_act)
        self.helpMenu.addAction(self.userHelpAct)
        self.helpMenu.addAction(self.devHelpAct)

    def show_user_help(self):
        QMessageBox.about(self, "hai", "This part is still under developed")
    def show_dev_help(self):
        QMessageBox.about(self, "hai", "This part is still under developed")

    ##==========centerWidget/stack窗口的切换动画==========
    def fadeInWidget(self, new_widget): #有点假, 不需要old界面
        animationIn = QPropertyAnimation(new_widget) #动画的父控件为 login
        animationIn.setTargetObject(new_widget)  #给register 做动画
        animationIn.setPropertyName(b"pos")
        animationIn.setStartValue(QPoint(-new_widget.width(),0))
        animationIn.setEndValue(QPoint(0,0))
        animationIn.setDuration(500)
        animationIn.setEasingCurve(QEasingCurve.InOutExpo)
        animationIn.start(QAbstractAnimation.DeleteWhenStopped)

    def switch_stack(self, window_name):
        widget = self.Stack.findChild(QWidget, window_name)
        if widget:
            self.Stack.setCurrentWidget(widget)
            self.fadeInWidget(self.Stack.currentWidget())
            self.statusBar().showMessage(f"open {window_name}")
        else:
            QMessageBox.about(self, 'error', f"Window:  '{window_name}' not found.")

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = MainWindow()
    trial.show()
    sys.exit(app.exec())