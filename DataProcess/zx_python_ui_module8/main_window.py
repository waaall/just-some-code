import sys
from functools import partial
from PySide6.QtGui import *
# QPixmap, QPainter
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QTextEdit, QWidget

from widgets import *
##=========================================================
##=======                 主界面类                 =========
##=========================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # 注意有一些初始化的顺序是不能更改的, 因为有依赖关系
        self.setWindowTitle("R&D_Tools")
        self.send_status_message("一切就绪, 确保您阅读文档, 再进行操作")

        # 初始化Dock和主窗口(centralWidget)
        self.__init_general_windows()
        self.setCentralWidget(self.Stack)

        # 初始化menu bar
        self.__createActions()
        self.__createMenu()

    # 初始化Dock和主窗口(centralWidget)
    def __init_general_windows(self):
        # 虽然我在DockPage提供了add_group, 但最好还是在这里初始化
        page_groups_names = ['settings_help', 'image_opt', 'file_opt']

        # 初始化dock
        if hasattr(self, 'dock'):
            return  # 如果存在, 直接返回, 不创建新的 dock
        self.dock = QDockWidget()
        self.dock.setWindowTitle('工作目录')
        self.dock_page = DockPage(page_groups_names)
        self.dock.setWidget(self.dock_page)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        self.Stack = QStackedWidget()

        # 初始化具体页面, 如果需要在外部访问你对象, 需要定义到self, 否则无需定义
        # 第一个初始化的就是开始界面, 当然不仅仅这一两行代码, 还有一些前置的步骤, 具体见文档
        self.__help_window_name = 'HelpWindow'
        self.add_stack_page(HelpWindow(), group_name = page_groups_names[0])

        self.SettingWindow = SettingWindow()
        self.add_stack_page(self.SettingWindow, group_name = page_groups_names[0])

        self.PlottingWindow = PlottingWindow()
        self.add_stack_page(self.PlottingWindow, group_name = page_groups_names[1])

        self.FileWindow = FileWindow()
        self.add_stack_page(self.FileWindow, group_name = page_groups_names[2])

    ##====================右侧stack中添加一页=====================
    def add_stack_page(self, page_instance, group_name:str='file_opt'):
        """
        :param page_instance: 页面的类示例, 当然, 需要import你的页面类所在的文件
        :param group_name: dock_page的组名
        """
        # 确定stack子页面名称 = 对应的dock按钮名称
        page_name = page_instance.__class__.__name__
                
        # 将页面添加到 QStackedWidget 中
        self.Stack.addWidget(page_instance)
        page_instance.setObjectName(page_name)

        # 在指定的组中添加按钮并绑定切换页面的事件
        self.dock_page.add_button(group_name, page_name, 
                                  lambda: self.switch_stack_page(page_name))

        # 如果有result_signal, 信号发送到 main window 的 status bar
        if hasattr(page_instance, 'result_signal'):
            page_instance.result_signal.connect(self.send_status_message)
    ##===================显示左边Dock栏===================
    def show_dock(self):
        # 检查是否已经有一个 'dock_window'
        if hasattr(self, 'dock'):
            self.dock.show()
            self.statusBar().showMessage("dock重新打开")
            return  # 如果存在，直接返回，不创建新的 dock
        else:
            self.statusBar().showMessage("初始化dock")
            self.__init_dock()

    ##=======================主界面的功能区=======================
    def send_status_message(self, message):
        self.statusBar().showMessage(message)

    def __createActions(self):
        # 创建 QAction 对象
        self.help_act = QAction("打开帮助", self, statusTip="帮助界面")
        # 连接 triggered 信号到槽函数，传递参数
        self.help_act.triggered.connect(partial(self.switch_stack_page, self.__help_window_name))
        self.userHelpAct = QAction("使用文档",statusTip="使用文档")

        self.userHelpAct.triggered.connect(self.show_user_help)
        self.devHelpAct = QAction("开发文档", statusTip="开发文档")
        self.devHelpAct.triggered.connect(self.show_dev_help)

        self.openDockAct = QAction("打开导航", statusTip="重新打开导航栏")
        self.openDockAct.triggered.connect(self.show_dock)

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

    ##====================stack窗口的切换&动画====================
    def switch_stack_page(self, window_name):
        widget = self.Stack.findChild(QWidget, window_name)
        if widget:
            self.Stack.setCurrentWidget(widget)
            self.fadeInWidget(self.Stack.currentWidget())
            self.statusBar().showMessage(f"open {window_name}")
        else:
            QMessageBox.about(self, 'error', f"Window:  '{window_name}' not found.")
    
    def fadeInWidget(self, new_widget): #有点假, 不需要old界面
        animationIn = QPropertyAnimation(new_widget) #动画的父控件为 login
        animationIn.setTargetObject(new_widget)  #给register 做动画
        animationIn.setPropertyName(b"pos")
        animationIn.setStartValue(QPoint(-new_widget.width(),0))
        animationIn.setEndValue(QPoint(0,0))
        animationIn.setDuration(500)
        animationIn.setEasingCurve(QEasingCurve.InOutExpo)
        animationIn.start(QAbstractAnimation.DeleteWhenStopped)

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = MainWindow()
    trial.show()
    sys.exit(app.exec())