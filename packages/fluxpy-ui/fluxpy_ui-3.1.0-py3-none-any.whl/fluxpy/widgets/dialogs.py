from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTabWidget, QWidget
from PyQt6.QtCore import Qt

class AlertDialog:
    def __init__(self, title="", content=None, actions=None, on_dismiss=None):
        self.title = title
        self.content = content
        self.actions = actions if actions else []
        self.on_dismiss = on_dismiss

    def show(self, page):
        if not page.is_web:
            msg = QMessageBox()
            msg.setWindowTitle(self.title)
            if isinstance(self.content, str):
                msg.setText(self.content)
            msg.exec()

class Tabs(QWidget):
    def __init__(self, tabs=None, on_change=None):
        super().__init__()
        self.tabs_list = tabs if tabs else []
        self.on_change = on_change

    def render_desktop(self):
        tab_widget = QTabWidget()
        for tab in self.tabs_list:
            pane = QWidget()
            layout = QVBoxLayout(pane)
            if hasattr(tab, 'content') and tab.content:
                layout.addWidget(tab.content.render_desktop())
            tab_widget.addTab(pane, tab.label if hasattr(tab, 'label') else "Tab")
        
        if self.on_change:
            tab_widget.currentChanged.connect(self.on_change)
        return tab_widget

class Tab:
    def __init__(self, label="", content=None):
        self.label = label
        self.content = content
