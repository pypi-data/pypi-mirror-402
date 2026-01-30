from PyQt6.QtWidgets import (QPushButton, QLabel, QLineEdit, QVBoxLayout, 
                             QHBoxLayout, QWidget, QCheckBox, QFrame)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
import os

class Control:
    def __init__(self, visible=True, disabled=False, data=None):
        self.visible = visible
        self.disabled = disabled
        self.data = data

    def render_desktop(self):
        pass

    def render_web(self):
        pass

class Text(Control):
    def __init__(self, value="", size=16, color="black", weight="normal", font_family="Arial", **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.size = size
        self.color = color
        self.weight = weight
        self.font_family = font_family

    def render_desktop(self):
        label = QLabel(self.value)
        font = QFont(self.font_family, self.size)
        if self.weight == "bold": font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(f"color: {self.color};")
        label.setVisible(self.visible)
        label.setEnabled(not self.disabled)
        return label

    def render_web(self):
        style = f"font-size: {self.size}px; color: {self.color}; font-weight: {self.weight}; font-family: {self.font_family};"
        return f'<div class="control" style="{style}">{self.value}</div>'

class ElevatedButton(Control):
    def __init__(self, text="", on_click=None, icon=None, bgcolor=None, color=None, 
                 border_radius=5, padding=10, size=14, weight="normal", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.on_click = on_click
        self.icon = icon
        self.bgcolor = bgcolor
        self.color = color
        self.border_radius = border_radius
        self.padding = padding
        self.size = size
        self.weight = weight

    def render_desktop(self):
        btn = QPushButton(self.text)
        if self.icon:
            btn.setIcon(QIcon(self.icon))
            btn.setIconSize(QSize(24, 24))
        
        style = f"""
            QPushButton {{
                background-color: {self.bgcolor if self.bgcolor else "#f0f0f0"};
                color: {self.color if self.color else "black"};
                border-radius: {self.border_radius}px;
                padding: {self.padding}px;
                font-size: {self.size}px;
                font-weight: {self.weight};
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """
        btn.setStyleSheet(style)
        if self.on_click:
            btn.clicked.connect(self.on_click)
        btn.setVisible(self.visible)
        btn.setEnabled(not self.disabled)
        return btn

    def render_web(self):
        style = f"background-color: {self.bgcolor}; color: {self.color}; border-radius: {self.border_radius}px; padding: {self.padding}px;"
        return f'<button class="control" style="{style}" onclick="alert(\'Clicked\')">{self.text}</button>'

class Container(Control):
    def __init__(self, content=None, padding=0, margin=0, bgcolor=None, 
                 border_radius=0, border_width=0, border_color=None, 
                 width=None, height=None, **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.padding = padding
        self.margin = margin
        self.bgcolor = bgcolor
        self.border_radius = border_radius
        self.border_width = border_width
        self.border_color = border_color
        self.width = width
        self.height = height

    def render_desktop(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        
        if self.content:
            layout.addWidget(self.content.render_desktop())
            
        style = f"""
            QFrame {{
                background-color: {self.bgcolor if self.bgcolor else "transparent"};
                border: {self.border_width}px solid {self.border_color if self.border_color else "transparent"};
                border-radius: {self.border_radius}px;
            }}
        """
        frame.setStyleSheet(style)
        if self.width: frame.setFixedWidth(self.width)
        if self.height: frame.setFixedHeight(self.height)
        return frame

    def render_web(self):
        style = f"padding: {self.padding}px; background-color: {self.bgcolor}; border-radius: {self.border_radius}px;"
        inner = self.content.render_web() if self.content else ""
        return f'<div class="control" style="{style}">{inner}</div>'

class Row(Control):
    def __init__(self, controls=None, spacing=10, **kwargs):
        super().__init__(**kwargs)
        self.controls = controls if controls else []
        self.spacing = spacing

    def render_desktop(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(self.spacing)
        for c in self.controls:
            layout.addWidget(c.render_desktop())
        return widget

    def render_web(self):
        inner = "".join([c.render_web() for c in self.controls])
        return f'<div class="control" style="display: flex; gap: {self.spacing}px;">{inner}</div>'

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
            layout.addWidget(c.render_desktop())
        return widget

    def render_web(self):
        inner = "".join([c.render_web() for c in self.controls])
        return f'<div class="control" style="display: flex; flex-direction: column; gap: {self.spacing}px;">{inner}</div>'

class TextField(Control):
    def __init__(self, value="", placeholder="", password=False, border_radius=5, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.placeholder = placeholder
        self.password = password
        self.border_radius = border_radius

    def render_desktop(self):
        edit = QLineEdit(self.value)
        edit.setPlaceholderText(self.placeholder)
        if self.password:
            edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.setStyleSheet(f"border-radius: {self.border_radius}px; padding: 5px; border: 1px solid #ccc;")
        return edit

    def render_web(self):
        type_attr = "password" if self.password else "text"
        return f'<input class="control" type="{type_attr}" value="{self.value}" placeholder="{self.placeholder}" style="border-radius: {self.border_radius}px;">'
