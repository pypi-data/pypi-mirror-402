from PyQt6.QtWidgets import (QPushButton, QLabel, QFrame, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QCheckBox, QRadioButton, QComboBox, QSlider, 
                             QProgressBar, QScrollArea, QStackedWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QIcon

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
        if self.widget:
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
        if "size" not in kwargs: self.size = 14 # Larger default font

    def build(self):
        self.widget = QLabel(self.value)
        self.apply_styles()
        return self.widget

class TextField(BaseWidget):
    def __init__(self, value="", placeholder="", on_change=None, password=False, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.placeholder = placeholder
        self.on_change = on_change
        self.password = password
        if "bgcolor" not in kwargs: self.bgcolor = "white"
        if "padding" not in kwargs: self.padding = 8
        if "border_radius" not in kwargs: self.border_radius = 5
        if "border_width" not in kwargs: self.border_width = 1
        if "border_color" not in kwargs: self.border_color = "#cccccc"

    def build(self):
        self.widget = QLineEdit()
        self.widget.setText(self.value)
        self.widget.setPlaceholderText(self.placeholder)
        if self.password:
            self.widget.setEchoMode(QLineEdit.EchoMode.Password)
        if self.on_change:
            self.widget.textChanged.connect(self._handle_change)
        self.apply_styles()
        return self.widget

    def _handle_change(self, text):
        self.value = text
        if self.on_change:
            self.on_change(text)

class Row(BaseWidget):
    def __init__(self, controls=None, spacing=10, alignment="start", **kwargs):
        super().__init__(**kwargs)
        self.controls = controls or []
        self.spacing = spacing
        self.alignment = alignment

    def build(self):
        self.widget = QFrame()
        layout = QHBoxLayout(self.widget)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if self.alignment == "center": layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self.alignment == "end": layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        else: layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for c in self.controls:
            layout.addWidget(c.build())
        self.apply_styles()
        return self.widget

class Column(BaseWidget):
    def __init__(self, controls=None, spacing=10, alignment="start", **kwargs):
        super().__init__(**kwargs)
        self.controls = controls or []
        self.spacing = spacing
        self.alignment = alignment

    def build(self):
        self.widget = QFrame()
        layout = QVBoxLayout(self.widget)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if self.alignment == "center": layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self.alignment == "end": layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        else: layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for c in self.controls:
            layout.addWidget(c.build())
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
    def __init__(self, text="", on_click=None, icon=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.on_click = on_click
        self.icon = icon
        if "bgcolor" not in kwargs: self.bgcolor = "#2196F3"
        if "color" not in kwargs: self.color = "white"
        if "padding" not in kwargs: self.padding = 12
        if "border_radius" not in kwargs: self.border_radius = 8

    def build(self):
        self.widget = QPushButton(self.text)
        if self.icon:
            self.widget.setIcon(QIcon(self.icon))
        if self.on_click:
            self.widget.clicked.connect(self.on_click)
        self.apply_styles()
        return self.widget

class Icon(BaseWidget):
    def __init__(self, name, size=24, color="black", **kwargs):
        super().__init__(**kwargs)
        self.name = name # Path to icon or name
        self.size = size
        self.color = color

    def build(self):
        self.widget = QLabel()
        icon = QIcon(self.name)
        pixmap = icon.pixmap(QSize(self.size, self.size))
        self.widget.setPixmap(pixmap)
        self.apply_styles()
        return self.widget

class Checkbox(BaseWidget):
    def __init__(self, label="", value=False, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.value = value
        self.on_change = on_change

    def build(self):
        self.widget = QCheckBox(self.label)
        self.widget.setChecked(self.value)
        if self.on_change:
            self.widget.stateChanged.connect(lambda state: self.on_change(state == 2))
        self.apply_styles()
        return self.widget
