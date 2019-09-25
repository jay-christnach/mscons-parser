import sys

from PyQt5.QtCore import *  # Qt
from PyQt5.QtWidgets import *  # QApplication, QMainWindow, QLabel, QToolBar, QAction


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("MSCONS-Converter")
        label = QLabel("Convert an MSCONS file to a CSV file.")
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)
        button_action = QAction("Open File", self)
        button_action.setStatusTip("Open a File")
        print(type(button_action.triggered))
        button_action.triggered.connect(self.on_button_clicked)
        toolbar.addAction(button_action)

    def on_button_clicked(self, s):
        print(click, s)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()

