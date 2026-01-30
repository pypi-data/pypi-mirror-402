from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QStackedWidget, QSizePolicy
from PyQt6.QtCore import Qt
from .base import Control

# --- Layout Widgets ---

class Container(Control):
    def __init__(self, content=None, padding=10, margin=0, width=None, height=None, alignment=None, **kwargs):
        self.content = content
        self.padding = padding
        self.margin = margin
        self.width = width
        self.height = height
        self.alignment = alignment
        super().__init__(**kwargs)

    def _create_internal_control(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
        layout.setSpacing(0)
        
        if self.content:
            layout.addWidget(self.content.internal_control)
            
        if self.margin > 0:
            frame.setStyleSheet(f"QFrame {{ margin: {self.margin}px; }}")
            
        if self.width:
            frame.setFixedWidth(self.width)
        if self.height:
            frame.setFixedHeight(self.height)
            
        return frame

    def _apply_properties(self):
        super()._apply_properties()
        frame = self._internal_control
        style = frame.styleSheet()
        
        if self.border:
            style += f" QFrame {{ border: {self.border}; }}"
        if self.shadow:
            style += f" QFrame {{ box-shadow: {self.shadow}; }}"
        if self.gradient:
            style += f" QFrame {{ background: {self.gradient}; }}"
            
        frame.setStyleSheet(style)
        
        if self.alignment:
            parsed_align = self._parse_alignment(self.alignment)
            if frame.layout():
                frame.layout().setAlignment(parsed_align)

class Row(Control):
    def __init__(self, controls=None, spacing=10, main_alignment="left", cross_alignment="top", **kwargs):
        self.controls = controls if controls is not None else []
        self.spacing = spacing
        self.main_alignment = main_alignment
        self.cross_alignment = cross_alignment
        super().__init__(**kwargs)

    def _create_internal_control(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for control in self.controls:
            layout.addWidget(control.internal_control)
            
        parsed_main = self._parse_alignment(self.main_alignment)
        parsed_cross = self._parse_alignment(self.cross_alignment)
        layout.setAlignment(parsed_main | parsed_cross)
        
        return widget

class Column(Control):
    def __init__(self, controls=None, spacing=10, main_alignment="top", cross_alignment="left", **kwargs):
        self.controls = controls if controls is not None else []
        self.spacing = spacing
        self.main_alignment = main_alignment
        self.cross_alignment = cross_alignment
        super().__init__(**kwargs)

    def _create_internal_control(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(self.spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for control in self.controls:
            layout.addWidget(control.internal_control)
            
        parsed_main = self._parse_alignment(self.main_alignment)
        parsed_cross = self._parse_alignment(self.cross_alignment)
        layout.setAlignment(parsed_main | parsed_cross)
        
        return widget

class Stack(Control):
    def __init__(self, controls=None, **kwargs):
        self.controls = controls if controls is not None else []
        super().__init__(**kwargs)

    def _create_internal_control(self):
        widget = QStackedWidget()
        for control in self.controls:
            widget.addWidget(control.internal_control)
        
        if self.controls:
            widget.setCurrentIndex(0)
            
        return widget

class Divider(Control):
    def __init__(self, height=1, color="#ccc", **kwargs):
        self.height = height
        self.color = color
        super().__init__(**kwargs)

    def _create_internal_control(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setFixedHeight(self.height)
        line.setStyleSheet(f"QFrame {{ background-color: {self.color}; }}")
        return line

# --- Export for easy import ---
__all__ = [
    "Container", "Row", "Column", "Stack", "Divider"
]
