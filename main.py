from PyQt5 import QtWidgets
from scanner.mainwindow import MainWindow
from PyQt5.QtGui import QIcon
import sys
import os

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # 兼容打包和开发环境，处理 ico 路径
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    icon_path = os.path.join(base_path, "myicon.ico")

    win = MainWindow()
    win.setWindowIcon(QIcon(icon_path))  # 设置窗口图标
    win.show()
    sys.exit(app.exec_())