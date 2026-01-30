from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QFrame
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap

# --- Base Control Class (Flet-compatible) ---

class Control:
    """
    الفئة الأساسية لجميع عناصر واجهة المستخدم في FluxPy.
    تطبق الخصائص المشتركة (visible, disabled, opacity, tooltip)
    وآلية التحديث (update) بأسلوب Flet.
    """
    def __init__(self, **kwargs):
        self._internal_control = self._create_internal_control()
        self._page = None # مرجع للصفحة التي ينتمي إليها العنصر
        self._children = []
        self._set_common_properties(**kwargs)

    def _create_internal_control(self):
        """يجب أن يتم تجاوز هذه الدالة بواسطة الفئات الفرعية لإنشاء عنصر PyQt6 الفعلي."""
        # يجب أن تعيد QWidget أو فئة فرعية منها
        return QWidget()

    def _set_common_properties(self, **kwargs):
        """تطبيق الخصائص المشتركة من kwargs."""
        self.visible = kwargs.get('visible', True)
        self.disabled = kwargs.get('disabled', False)
        self.opacity = kwargs.get('opacity', 1.0)
        self.tooltip = kwargs.get('tooltip', None)
        self.on_click = kwargs.get('on_click', None)
        self.on_hover = kwargs.get('on_hover', None)
        
        # خصائص التخصيص المتقدمة
        self.font_family = kwargs.get('font_family', None)
        self.font_size = kwargs.get('font_size', None)
        self.color = kwargs.get('color', None)
        self.bgcolor = kwargs.get('bgcolor', None)
        self.border = kwargs.get('border', None)
        self.shadow = kwargs.get('shadow', None)
        self.gradient = kwargs.get('gradient', None)
        
        self._apply_properties()

    def _apply_properties(self):
        """تطبيق الخصائص على عنصر PyQt6 الداخلي باستخدام QSS بشكل أساسي."""
        if self._internal_control:
            self._internal_control.setVisible(self.visible)
            self._internal_control.setEnabled(not self.disabled)
            
            style_parts = []
            
            # 1. الألوان والخلفية والحدود
            if self.color:
                style_parts.append(f"color: {self.color};")
            if self.bgcolor:
                style_parts.append(f"background-color: {self.bgcolor};")
            if self.border:
                # Border format: "1px solid #ccc"
                style_parts.append(f"border: {self.border};")
            
            # 2. الخطوط
            if self.font_family or self.font_size:
                font = self._internal_control.font()
                if self.font_family:
                    font.setFamily(self.font_family)
                if self.font_size:
                    font.setPointSize(self.font_size)
                self._internal_control.setFont(font)
            
            # 3. الشفافية (Opacity) - يتم محاكاتها عبر QSS أو تأثيرات رسومية متقدمة
            # حالياً، نكتفي بتطبيق الخصائص الأساسية عبر QSS
            
            if style_parts:
                # تطبيق QSS على العنصر الداخلي
                self._internal_control.setStyleSheet("QWidget {" + " ".join(style_parts) + "}")

            if self.tooltip:
                self._internal_control.setToolTip(self.tooltip)

            # 4. ربط الأحداث
            if self.on_click and isinstance(self._internal_control, QPushButton):
                # يجب أن يكون on_click دالة تقبل العنصر نفسه كوسيط
                self._internal_control.clicked.connect(lambda: self.on_click(self))
            
            # TODO: تنفيذ on_hover و animate_*

    def update(self):
        """تحديث خصائص العنصر وإعادة رسمه."""
        self._apply_properties()
        if self._page:
            self._page.update_control(self) # إبلاغ الصفحة بضرورة التحديث

    @property
    def internal_control(self):
        """إرجاع عنصر PyQt6 الداخلي."""
        return self._internal_control

# --- Basic Widgets ---

class Text(Control):
    def __init__(self, value, **kwargs):
        self.value = value
        super().__init__(**kwargs)

    def _create_internal_control(self):
        return QLabel(str(self.value))

    def _apply_properties(self):
        super()._apply_properties()
        if self._internal_control:
            self._internal_control.setText(str(self.value))

class ElevatedButton(Control):
    def __init__(self, text, **kwargs):
        self.text = text
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton(self.text)
        # تطبيق نمط مرتفع افتراضي
        btn.setStyleSheet("QPushButton { padding: 10px 20px; border-radius: 5px; background-color: #007bff; color: white; }")
        return btn

    def _apply_properties(self):
        super()._apply_properties()
        if self._internal_control:
            self._internal_control.setText(self.text)

class TextButton(Control):
    def __init__(self, text, **kwargs):
        self.text = text
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton(self.text)
        btn.setFlat(True)
        btn.setStyleSheet("QPushButton { border: none; background-color: transparent; color: #007bff; }")
        return btn

class OutlinedButton(Control):
    def __init__(self, text, **kwargs):
        self.text = text
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton(self.text)
        btn.setStyleSheet("QPushButton { padding: 10px 20px; border-radius: 5px; border: 1px solid #007bff; background-color: transparent; color: #007bff; }")
        return btn

class IconButton(Control):
    def __init__(self, icon, **kwargs):
        self.icon = icon # مسار ملف أو اسم أيقونة
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton()
        if self.icon:
            btn.setIcon(QIcon(self.icon))
            btn.setIconSize(QSize(24, 24))
        btn.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
        return btn

class FloatingActionButton(Control):
    def __init__(self, icon, **kwargs):
        self.icon = icon
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton()
        if self.icon:
            btn.setIcon(QIcon(self.icon))
            btn.setIconSize(QSize(28, 28))
        btn.setFixedSize(QSize(56, 56))
        btn.setStyleSheet("QPushButton { border-radius: 28px; background-color: #ff4081; color: white; }")
        return btn

# --- Export for easy import ---
__all__ = [
    "Control", "Text", "ElevatedButton", "TextButton", "OutlinedButton", "IconButton", "FloatingActionButton"
]
