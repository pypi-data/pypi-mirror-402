import sys
import os
import traceback
import threading
import webbrowser
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QScrollArea, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont
from flask import Flask, render_template_string, jsonify, request

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

    def __init__(self, window=None, is_web=False):
        super().__init__()
        self.window = window
        self.is_web = is_web
        self.title = "FluxPy Universal App"
        self.bgcolor = "#ffffff"
        self.padding = 20
        self.controls = []
        self.theme_mode = "light"
        
        # Assets
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        self.icon = os.path.join(assets_dir, "flux_logo_new.png")
        
        self.show_minimize = True
        self.show_maximize = True
        self.show_close = True
        self.frameless = False

    def add(self, *controls):
        for control in controls:
            self.controls.append(control)
        if not self.is_web and self.window:
            self.window.update_ui()

    def update(self):
        if not self.is_web and self.window:
            self.window.update_ui()

    def show_message(self, title, message, type="info"):
        if not self.is_web:
            msg = QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(message)
            if type == "success": msg.setIcon(QMessageBox.Icon.Information)
            elif type == "error": msg.setIcon(QMessageBox.Icon.Critical)
            else: msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
        else:
            # Web implementation would use JS alert or toast
            pass

class FluxApp:
    def __init__(self, target="desktop", port=5000):
        self.target = target.lower()
        self.port = port
        self.flask_app = Flask(__name__)
        self.page = None

    def run(self, main_fn):
        if self.target == "web":
            self._run_web(main_fn)
        else:
            self._run_desktop(main_fn)

    def _run_desktop(self, main_fn):
        app = QApplication(sys.argv)
        window = FluxWindow(main_fn)
        window.show()
        sys.exit(app.exec())

    def _run_web(self, main_fn):
        self.page = Page(is_web=True)
        main_fn(self.page)
        
        @self.flask_app.route('/')
        def index():
            # Basic Web Rendering Engine (Simplified for now)
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{self.page.title}</title>
                <style>
                    body {{ background-color: {self.page.bgcolor}; padding: {self.page.padding}px; font-family: sans-serif; }}
                    .control {{ margin-bottom: 10px; }}
                </style>
            </head>
            <body>
                <div id="app">
                    {"".join([c.render_web() for c in self.page.controls])}
                </div>
            </body>
            </html>
            """
            return render_template_string(html)

        print(f"Starting FluxPy Web at http://127.0.0.1:{self.port}")
        threading.Timer(1.25, lambda: webbrowser.open(f"http://127.0.0.1:{self.port}")).start()
        self.flask_app.run(port=self.port, debug=False)

class FluxWindow(QMainWindow):
    def __init__(self, main_fn):
        super().__init__()
        self.main_fn = main_fn
        self.page = Page(self)
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)

        self.main_fn(self.page)
        self.update_ui()

    def update_ui(self):
        self.setWindowTitle(self.page.title)
        self.setWindowIcon(QIcon(self.page.icon))
        self.central_widget.setStyleSheet(f"background-color: {self.page.bgcolor};")
        
        # Clear layout
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)
            
        for control in self.page.controls:
            widget = control.render_desktop()
            self.scroll_layout.addWidget(widget)
        
        if self.page.frameless:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        flags = self.windowFlags()
        if not self.page.show_minimize: flags &= ~Qt.WindowType.WindowMinimizeButtonHint
        if not self.page.show_maximize: flags &= ~Qt.WindowType.WindowMaximizeButtonHint
        if not self.page.show_close: flags &= ~Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)
