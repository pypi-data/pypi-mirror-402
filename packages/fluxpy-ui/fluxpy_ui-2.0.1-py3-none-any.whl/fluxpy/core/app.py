import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QObject

class FluxDebugger:
    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        tb = traceback.extract_tb(exc_traceback)
        last_call = tb[-1]
        print(f"\n[FluxPy Smart Debugger]")
        print(f"File: {last_call.filename}")
        print(f"Line: {last_call.lineno}")
        print(f"Error Type: {exc_type.__name__}")
        print(f"Message: {exc_value}")
        print("-" * 30)

sys.excepthook = FluxDebugger.handle_exception

class Page(QObject):
    update_signal = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.title = "FluxPy App"
        self.bgcolor = "#ffffff"
        self.padding = 10
        self.controls = []
        
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.central_widget)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.window.setCentralWidget(self.scroll)

    def add(self, *args):
        for control in args:
            self.controls.append(control)
            qt_widget = control.build()
            self.layout.addWidget(qt_widget)
        self.update()

    def update(self):
        self.window.setWindowTitle(self.title)
        self.central_widget.setStyleSheet(f"background-color: {self.bgcolor};")
        self.layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        self.update_signal.emit()

class FluxApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = QMainWindow()
        self.window.resize(800, 600)
        self.page = Page(self.window)

    def run(self, target):
        target(self.page)
        self.window.show()
        sys.exit(self.app.exec())
