import os, sys
from PySide6.QtGui import QFont
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

##=========================================================
##=======                 帮助界面                 =========
##=========================================================
class HelpWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        
        # 主布局
        mainLayout = QVBoxLayout(self)

        # 顶部按钮组
        buttonLayout = QHBoxLayout()
        self.userBut = QPushButton("User Manual")
        self.devBut = QPushButton("Develop Manual")
        buttonLayout.addWidget(self.userBut)
        buttonLayout.addWidget(self.devBut)

        self.init_doc_browser()

        # 将布局添加到主布局
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(self.textBrowser)

        self.setGeometry(100, 100, 400, 600)

    ##=====创建文档查看窗口======
    def init_doc_browser(self):
        # 显示文档的文本浏览器，支持 Markdown
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.doc_dir = os.path.join(base_dir, 'configs')

        self.textBrowser = QTextBrowser()
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setMinimumSize(350,500)
        self.show_user_manual()
        # 设置字体
        font = QFont()
        # font.setFamily("Arial")  # 设置字体名称
        font.setPointSize(15)    # 设置字体大小
        self.textBrowser.setFont(font)


        # 绑定按钮的点击事件到相应的函数
        self.userBut.clicked.connect(self.show_user_manual)
        self.devBut.clicked.connect(self.show_develop_manual)

    def show_user_manual(self):
        manual_path = os.path.join(self.doc_dir, 'user_manual.md')
        # 显示使用手册的内容，可以是 Markdown 格式
        self.display_markdown(manual_path)

    def show_develop_manual(self):
        manual_path = os.path.join(self.doc_dir, 'develop_manual.md')
        self.display_markdown(manual_path)

    def display_markdown(self, file_path):
        # 检查文件是否存在并显示内容
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.textBrowser.setMarkdown(content)
        except FileNotFoundError:
            self.textBrowser.setMarkdown(f"Error: File {file_path} not found.")
        except Exception as e:
            self.textBrowser.setMarkdown(f"Error reading file {file_path}: {str(e)}")

##===========================调试用==============================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = HelpWindow()
    trial.show()
    sys.exit(app.exec())
