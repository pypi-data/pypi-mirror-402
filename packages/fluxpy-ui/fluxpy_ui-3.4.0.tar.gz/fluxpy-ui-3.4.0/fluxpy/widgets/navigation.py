from PyQt6.QtWidgets import QTabWidget, QToolBar, QWidget, QVBoxLayout
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from .base import Control

# --- Navigation Widgets ---

class NavigationBar(Control):
    def __init__(self, controls=None, **kwargs):
        self.controls = controls if controls is not None else []
        super().__init__(**kwargs)

    def _create_internal_control(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        for control in self.controls:
            # نفترض أن عناصر التحكم هي أزرار أو عناصر قابلة للنقر
            if isinstance(control, Control):
                # يجب أن يكون العنصر زرًا أو إجراءً (QAction)
                if isinstance(control.internal_control, QAction):
                    toolbar.addAction(control.internal_control)
                elif isinstance(control.internal_control, QWidget):
                    toolbar.addWidget(control.internal_control)
                control._page = self._page
                
        return toolbar

class Tabs(Control):
    def __init__(self, tabs=None, on_change=None, **kwargs):
        self.tabs = tabs if tabs is not None else [] # [{text: "...", content: Control}]
        self.on_change = on_change
        super().__init__(**kwargs)

    def _create_internal_control(self):
        tab_widget = QTabWidget()
        
        for tab in self.tabs:
            text = tab.get('text', 'Tab')
            content_control = tab.get('content')
            
            if content_control and isinstance(content_control, Control):
                tab_widget.addTab(content_control.internal_control, text)
                content_control._page = self._page
        
        if self.on_change:
            tab_widget.currentChanged.connect(lambda index: self.on_change(self, index))
            
        return tab_widget

# --- Export for easy import ---
__all__ = [
    "NavigationBar", "Tabs"
]
