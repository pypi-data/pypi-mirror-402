import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QScrollArea, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont

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
        self.padding = 20
        self.controls = []
        
        # Default Logo
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        self.icon = os.path.join(assets_dir, "flux_logo.png")
        
        self.show_minimize = True
        self.show_maximize = True
        self.show_close = True
        self.frameless = False
        
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

    def clean(self):
        self.controls = []
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def update(self):
        self.window.setWindowTitle(self.title)
        self.central_widget.setStyleSheet(f"background-color: {self.bgcolor};")
        self.layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        
        if os.path.exists(self.icon):
            self.window.setWindowIcon(QIcon(self.icon))
            
        self.update_signal.emit()

    def show_message(self, title, message, type="info"):
        msg = QMessageBox(self.window)
        msg.setWindowTitle(title)
        msg.setText(message)
        if type == "success": msg.setIcon(QMessageBox.Icon.Information)
        elif type == "error": msg.setIcon(QMessageBox.Icon.Critical)
        elif type == "warning": msg.setIcon(QMessageBox.Icon.Warning)
        else: msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

class FluxApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        default_font = QFont("Segoe UI", 11)
        self.app.setFont(default_font)
        
        self.window = QMainWindow()
        self.window.resize(1000, 700)
        self.page = Page(self.window)

    def run(self, target):
        target(self.page)
        self.window.show()
        sys.exit(self.app.exec())
