from PyQt6.QtWidgets import QDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea
from PyQt6.QtCore import Qt
from .base import Control

# --- Dialogs and Page ---

class Page(Control):
    """
    يمثل النافذة الرئيسية للتطبيق.
    يحتوي على خصائص مثل العنوان، الأبعاد، والخلفية، ويدير إضافة وإزالة العناصر.
    """
    def __init__(self, title="FluxPy Application", bgcolor="#FFFFFF", theme_mode="light", 
                 window_width=800, window_height=600, padding=10, scroll=False, **kwargs):
        self.title = title
        self.bgcolor = bgcolor
        self.theme_mode = theme_mode
        self.window_width = window_width
        self.window_height = window_height
        self.padding = padding
        self.scroll = scroll
        self.controls = []
        super().__init__(**kwargs)

    def _create_internal_control(self):
        # Page هي النافذة الرئيسية، لذا سنعيد QWidget كحاوية
        widget = QWidget()
        widget.setWindowTitle(self.title)
        widget.resize(self.window_width, self.window_height)
        
        # إعداد التخطيط الأساسي
        if self.scroll:
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            
            self.content_widget = QWidget()
            self.scroll_area.setWidget(self.content_widget)
            
            self.main_layout = QVBoxLayout(self.content_widget)
            self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            window_layout = QVBoxLayout(widget)
            window_layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
            window_layout.addWidget(self.scroll_area)
        else:
            self.main_layout = QVBoxLayout(widget)
            self.main_layout.setContentsMargins(self.padding, self.padding, self.padding, self.padding)
            self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # تطبيق الخلفية
        widget.setStyleSheet(f"QWidget {{ background-color: {self.bgcolor}; }}")
        
        return widget

    def add(self, *controls):
        """إضافة عناصر تحكم إلى الصفحة."""
        for control in controls:
            if isinstance(control, Control):
                self.controls.append(control)
                control._page = self
                self.main_layout.addWidget(control.internal_control)
        self.update()

    def remove(self, control):
        """إزالة عنصر تحكم من الصفحة."""
        if control in self.controls:
            self.controls.remove(control)
            self.main_layout.removeWidget(control.internal_control)
            control.internal_control.deleteLater()
            self.update()

    def update_control(self, control):
        """تحديث عنصر تحكم محدد (يتم استدعاؤها من Control.update())."""
        # في PyQt6، التحديث يتم تلقائيًا بمجرد تغيير خصائص عنصر التحكم
        # يمكن استخدام هذه الدالة لإعادة رسم التخطيط إذا لزم الأمر
        if self.scroll:
            self.content_widget.adjustSize()
        self._internal_control.update()

    def clean(self):
        """إزالة جميع عناصر التحكم من الصفحة."""
        for control in list(self.controls):
            self.remove(control)
        self.controls = []
        self.update()

class AlertDialog(Control):
    def __init__(self, title="", content=None, actions=None, **kwargs):
        self.title = title
        self.content = content
        self.actions = actions if actions is not None else []
        super().__init__(**kwargs)

    def _create_internal_control(self):
        # نستخدم QDialog مخصص لتضمين عناصر تحكم FluxPy
        dialog = QDialog()
        dialog.setWindowTitle(self.title)
        
        layout = QVBoxLayout(dialog)
        
        if self.content and isinstance(self.content, Control):
            layout.addWidget(self.content.internal_control)
            self.content._page = self._page
        
        # إضافة الأزرار (Actions) في تخطيط أفقي
        if self.actions:
            action_layout = QHBoxLayout()
            for action in self.actions:
                if isinstance(action, Control):
                    action_layout.addWidget(action.internal_control)
                    action._page = self._page
            layout.addLayout(action_layout)
        
        return dialog

    def open(self):
        """عرض مربع الحوار."""
        if isinstance(self._internal_control, QDialog):
            self._internal_control.exec()

class BottomSheet(Control):
    def __init__(self, content=None, **kwargs):
        self.content = content
        super().__init__(**kwargs)

    def _create_internal_control(self):
        # محاكاة BottomSheet باستخدام QDialog
        dialog = QDialog()
        dialog.setWindowTitle("Bottom Sheet")
        
        layout = QVBoxLayout(dialog)
        if self.content and isinstance(self.content, Control):
            layout.addWidget(self.content.internal_control)
            self.content._page = self._page
            
        # تطبيق نمط لجعله يبدو كـ BottomSheet (محاذاة للأسفل)
        dialog.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        
        return dialog

    def open(self):
        """عرض BottomSheet."""
        if isinstance(self._internal_control, QDialog):
            self._internal_control.exec()

# --- Export for easy import ---
__all__ = [
    "Page", "AlertDialog", "BottomSheet"
]
