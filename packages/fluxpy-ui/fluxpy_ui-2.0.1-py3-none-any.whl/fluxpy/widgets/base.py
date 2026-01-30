from PyQt6.QtWidgets import QPushButton, QLabel, QFrame, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class BaseWidget:
    def __init__(self, **kwargs):
        self.width = kwargs.get("width")
        self.height = kwargs.get("height")
        self.padding = kwargs.get("padding", 0)
        self.margin = kwargs.get("margin", 0)
        self.bgcolor = kwargs.get("bgcolor", "transparent")
        self.color = kwargs.get("color", "black")
        self.border_radius = kwargs.get("border_radius", 0)
        self.border_color = kwargs.get("border_color", "transparent")
        self.border_width = kwargs.get("border_width", 0)
        self.font_family = kwargs.get("font_family", "Segoe UI")
        self.size = kwargs.get("size", 12)
        self.weight = kwargs.get("weight", "normal")
        self.widget = None

    def apply_styles(self):
        style = f"""
            background-color: {self.bgcolor};
            color: {self.color};
            border-radius: {self.border_radius}px;
            border: {self.border_width}px solid {self.border_color};
            padding: {self.padding}px;
            margin: {self.margin}px;
        """
        self.widget.setStyleSheet(style)
        if self.width: self.widget.setFixedWidth(self.width)
        if self.height: self.widget.setFixedHeight(self.height)
        
        font = QFont(self.font_family, self.size)
        if self.weight == "bold": font.setBold(True)
        self.widget.setFont(font)

class Text(BaseWidget):
    def __init__(self, value="", **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def build(self):
        self.widget = QLabel(self.value)
        self.apply_styles()
        return self.widget

class Container(BaseWidget):
    def __init__(self, content=None, **kwargs):
        super().__init__(**kwargs)
        self.content = content

    def build(self):
        self.widget = QFrame()
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(0, 0, 0, 0)
        if self.content:
            layout.addWidget(self.content.build())
        self.apply_styles()
        return self.widget

class ElevatedButton(BaseWidget):
    def __init__(self, text="", on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.on_click = on_click
        if "bgcolor" not in kwargs: self.bgcolor = "#2196F3"
        if "color" not in kwargs: self.color = "white"
        if "padding" not in kwargs: self.padding = 10
        if "border_radius" not in kwargs: self.border_radius = 5

    def build(self):
        self.widget = QPushButton(self.text)
        if self.on_click:
            self.widget.clicked.connect(self.on_click)
        self.apply_styles()
        return self.widget
