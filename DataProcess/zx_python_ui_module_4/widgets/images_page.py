import os, sys, re
# from PySide6.QtGui import *
# # QPixmap, QIcon, QImage
from PySide6.QtCore import *
# QFile, QFileInfo, QPoint, QSettings, QSaveFile, Qt, QTimeLine
from PySide6.QtWidgets import *
# QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QLineEdit, QWidget

##=========================================================
##=======                图片操作界面               =========
##=========================================================
class ImagesHanderWindow(QWidget):    
    def __init__(self):
        super().__init__()



##===============调试用==================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    trial = ImagesHanderWindow()
    trial.show()
    sys.exit(app.exec())