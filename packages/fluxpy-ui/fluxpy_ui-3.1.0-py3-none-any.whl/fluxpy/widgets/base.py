from PyQt6.QtWidgets import (QPushButton, QLabel, QLineEdit, QVBoxLayout, 
                             QHBoxLayout, QWidget, QCheckBox, QFrame, QRadioButton,
                             QSlider, QProgressBar, QListWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QScrollArea, QTabWidget,
                             QToolButton)
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap
from PyQt6.QtCore import Qt, QSize
import os

class Control:
    def __init__(self, visible=True, disabled=False, data=None, opacity=1.0, tooltip="", 
                 on_click=None, on_hover=None):
        self.visible = visible
        self.disabled = disabled
        self.data = data
        self.opacity = opacity
        self.tooltip = tooltip
        self.on_click = on_click
        self.on_hover = on_hover

    def render_desktop(self):
        pass

    def render_web(self):
        pass

class Text(Control):
    def __init__(self, value="", size=16, color=None, weight="normal", italic=False, 
                 text_align="left", max_lines=None, overflow="none", **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.size = size
        self.color = color
        self.weight = weight
        self.italic = italic
        self.text_align = text_align
        self.max_lines = max_lines
        self.overflow = overflow

    def render_desktop(self):
        label = QLabel(str(self.value))
        font = QFont("Arial", self.size)
        if self.weight == "bold": font.setBold(True)
        font.setItalic(self.italic)
        label.setFont(font)
        
        style = f"color: {self.color if self.color else 'inherit'};"
        label.setStyleSheet(style)
        
        align = Qt.AlignmentFlag.AlignLeft
        if self.text_align == "center": align = Qt.AlignmentFlag.AlignCenter
        elif self.text_align == "right": align = Qt.AlignmentFlag.AlignRight
        label.setAlignment(align)
        
        if self.max_lines:
            label.setWordWrap(True)
            # Simple max lines logic
        
        label.setVisible(self.visible)
        label.setEnabled(not self.disabled)
        label.setToolTip(self.tooltip)
        return label

    def render_web(self):
        style = f"font-size: {self.size}px; color: {self.color}; font-weight: {self.weight}; text-align: {self.text_align};"
        return f'<div class="control" style="{style}">{self.value}</div>'

class ElevatedButton(Control):
    def __init__(self, text="", icon=None, on_click=None, bgcolor=None, color=None, 
                 width=None, height=None, **kwargs):
        super().__init__(on_click=on_click, **kwargs)
        self.text = text
        self.icon = icon
        self.bgcolor = bgcolor
        self.color = color
        self.width = width
        self.height = height

    def render_desktop(self):
        btn = QPushButton(self.text)
        if self.icon:
            btn.setIcon(QIcon(self.icon))
        
        style = f"""
            QPushButton {{
                background-color: {self.bgcolor if self.bgcolor else '#e0e0e0'};
                color: {self.color if self.color else 'black'};
                border-radius: 8px;
                padding: 10px;
            }}
        """
        btn.setStyleSheet(style)
        if self.width: btn.setFixedWidth(self.width)
        if self.height: btn.setFixedHeight(self.height)
        if self.on_click: btn.clicked.connect(self.on_click)
        btn.setVisible(self.visible)
        btn.setEnabled(not self.disabled)
        return btn

class TextField(Control):
    def __init__(self, value="", label="", hint_text="", password=False, multiline=False, 
                 max_length=None, on_change=None, on_submit=None, border_radius=5, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.label = label
        self.hint_text = hint_text
        self.password = password
        self.multiline = multiline
        self.max_length = max_length
        self.on_change = on_change
        self.on_submit = on_submit
        self.border_radius = border_radius

    def render_desktop(self):
        edit = QLineEdit(str(self.value))
        edit.setPlaceholderText(self.hint_text)
        if self.password: edit.setEchoMode(QLineEdit.EchoMode.Password)
        if self.max_length: edit.setMaxLength(self.max_length)
        
        edit.setStyleSheet(f"border-radius: {self.border_radius}px; padding: 8px; border: 1px solid #ccc;")
        
        if self.on_change: edit.textChanged.connect(lambda text: self.on_change(text))
        if self.on_submit: edit.returnPressed.connect(self.on_submit)
        
        return edit

class Container(Control):
    def __init__(self, content=None, padding=0, margin=0, bgcolor=None, border_radius=0, 
                 width=None, height=None, alignment=None, shadow=None, gradient=None, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.padding = padding
        self.margin = margin
        self.bgcolor = bgcolor
        self.border_radius = border_radius
        self.width = width
        self.height = height
        self.alignment = alignment

    def render_desktop(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        p = self.padding
        layout.setContentsMargins(p, p, p, p)
        
        if self.content:
            layout.addWidget(self.content.render_desktop())
            
        style = f"background-color: {self.bgcolor if self.bgcolor else 'transparent'}; border-radius: {self.border_radius}px;"
        frame.setStyleSheet(style)
        if self.width: frame.setFixedWidth(self.width)
        if self.height: frame.setFixedHeight(self.height)
        return frame

class Row(Control):
    def __init__(self, controls=None, spacing=10, alignment="start", **kwargs):
        super().__init__(**kwargs)
        self.controls = controls if controls else []
        self.spacing = spacing
        self.alignment = alignment

    def render_desktop(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(self.spacing)
        for c in self.controls:
            w = c.render_desktop()
            if w: layout.addWidget(w)
        return widget

class Column(Control):
    def __init__(self, controls=None, spacing=10, **kwargs):
        super().__init__(**kwargs)
        self.controls = controls if controls else []
        self.spacing = spacing

    def render_desktop(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(self.spacing)
        for c in self.controls:
            w = c.render_desktop()
            if w: layout.addWidget(w)
        return widget

class Checkbox(Control):
    def __init__(self, label="", value=False, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.value = value
        self.on_change = on_change

    def render_desktop(self):
        cb = QCheckBox(self.label)
        cb.setChecked(self.value)
        if self.on_change: cb.stateChanged.connect(lambda: self.on_change(cb.isChecked()))
        return cb

class Dropdown(Control):
    def __init__(self, options=None, label="", on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.options = options if options else []
        self.label = label
        self.on_change = on_change

    def render_desktop(self):
        from PyQt6.QtWidgets import QComboBox
        combo = QComboBox()
        for opt in self.options:
            combo.addItem(opt.text if hasattr(opt, 'text') else str(opt))
        if self.on_change: combo.currentTextChanged.connect(self.on_change)
        return combo

class Slider(Control):
    def __init__(self, min=0, max=100, value=0, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max
        self.value = value
        self.on_change = on_change

    def render_desktop(self):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(self.min)
        slider.setMaximum(self.max)
        slider.setValue(self.value)
        if self.on_change: slider.valueChanged.connect(self.on_change)
        return slider

class Switch(Control):
    def __init__(self, value=False, label="", on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.label = label
        self.on_change = on_change

    def render_desktop(self):
        # Using Checkbox as a simple switch for now
        cb = QCheckBox(self.label)
        cb.setChecked(self.value)
        if self.on_change: cb.stateChanged.connect(lambda: self.on_change(cb.isChecked()))
        return cb
