import sys
import os
import traceback
import threading
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QScrollArea, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QIcon, QFont, QColor
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
    def __init__(self, window=None, is_web=False):
        super().__init__()
        self.window = window
        self.is_web = is_web
        
        # Flet-style properties
        self.title = "FluxPy App"
        self.bgcolor = "#ffffff"
        self.theme_mode = "light" # light, dark
        self.window_width = 800
        self.window_height = 600
        self.padding = 20
        self.scroll = True
        self.controls = []
        
        # Window controls
        self.show_minimize = True
        self.show_maximize = True
        self.show_close = True
        self.frameless = False
        
        # Assets
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        self.icon = os.path.join(assets_dir, "flux_logo_new.png")

    def add(self, *controls):
        for control in controls:
            self.controls.append(control)
        self.update()

    def remove(self, control):
        if control in self.controls:
            self.controls.remove(control)
            self.update()

    def clean(self):
        self.controls = []
        self.update()

    def update(self):
        if not self.is_web and self.window:
            self.window.update_ui_signal.emit()

    def show_message(self, title, message, type="info"):
        if not self.is_web:
            msg = QMessageBox()
            msg.setWindowTitle(title)
            msg.setText(message)
            if type == "success": msg.setIcon(QMessageBox.Icon.Information)
            elif type == "error": msg.setIcon(QMessageBox.Icon.Critical)
            else: msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()

class FluxApp:
    def __init__(self, target="desktop", port=5000, hot_reload=False):
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
            html = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>{self.page.title}</title>
                <style>
                    body {{ 
                        background-color: {self.page.bgcolor}; 
                        padding: {self.page.padding}px; 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        overflow-y: {"scroll" if self.page.scroll else "hidden"};
                    }}
                    .control {{ margin-bottom: 15px; }}
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
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{self.port}")).start()
        self.flask_app.run(port=self.port, debug=False)

class FluxWindow(QMainWindow):
    update_ui_signal = pyqtSignal()

    def __init__(self, main_fn):
        super().__init__()
        self.main_fn = main_fn
        self.page = Page(self)
        self.update_ui_signal.connect(self.update_ui)
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)

        self.main_fn(self.page)
        self.update_ui()

    def update_ui(self):
        self.setWindowTitle(self.page.title)
        self.setWindowIcon(QIcon(self.page.icon))
        self.resize(self.page.window_width, self.page.window_height)
        
        # Apply theme
        bg_color = self.page.bgcolor
        if self.page.theme_mode == "dark" and bg_color == "#ffffff":
            bg_color = "#1e1e1e"
        
        self.central_widget.setStyleSheet(f"background-color: {bg_color};")
        self.content_layout.setContentsMargins(self.page.padding, self.page.padding, self.page.padding, self.page.padding)
        
        # Clear layout
        for i in reversed(range(self.content_layout.count())): 
            item = self.content_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        for control in self.page.controls:
            widget = control.render_desktop()
            if widget:
                self.content_layout.addWidget(widget)
        
        # Window Flags
        flags = Qt.WindowType.Window
        if self.page.frameless: flags |= Qt.WindowType.FramelessWindowHint
        if not self.page.show_minimize: flags &= ~Qt.WindowType.WindowMinimizeButtonHint
        if not self.page.show_maximize: flags &= ~Qt.WindowType.WindowMaximizeButtonHint
        if not self.page.show_close: flags &= ~Qt.WindowType.WindowCloseButtonHint
        
        if self.windowFlags() != flags:
            self.setWindowFlags(flags)
            self.show() # Re-show after flag change
