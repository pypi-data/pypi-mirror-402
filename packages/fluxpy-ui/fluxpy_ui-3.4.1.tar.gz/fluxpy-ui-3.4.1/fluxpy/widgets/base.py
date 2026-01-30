from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QFrame
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap
import inspect

# --- Base Control Class (Flet-compatible) ---

class Control:
    """
    الفئة الأساسية لجميع عناصر واجهة المستخدم في FluxPy.
    تطبق الخصائص المشتركة (visible, disabled, opacity, tooltip)
    وآلية التحديث (update) بأسلوب Flet.
    """
    def __init__(self, **kwargs):
        # لا يتم إنشاء عنصر PyQt6 الداخلي هنا، بل يتم تأجيله إلى _create_internal_control
        self._internal_control = None
        self._page = None # مرجع للصفحة التي ينتمي إليها العنصر
        self._children = []
        self._set_common_properties(**kwargs)
        # إنشاء عنصر PyQt6 الداخلي بعد تعيين الخصائص
        self._internal_control = self._create_internal_control()

    def _create_internal_control(self):
        """يجب أن يتم تجاوز هذه الدالة بواسطة الفئات الفرعية لإنشاء عنصر PyQt6 الفعلي."""
        # لضمان عدم ظهور نوافذ صغيرة، نستخدم QWidget بدون parent
        return QWidget()

    def _parse_alignment(self, alignment):
        """تحويل المحاذاة النصية إلى Qt.AlignmentFlag."""
        if isinstance(alignment, Qt.AlignmentFlag):
            return alignment
        
        align_map = {
            "center": Qt.AlignmentFlag.AlignCenter,
            "left": Qt.AlignmentFlag.AlignLeft,
            "right": Qt.AlignmentFlag.AlignRight,
            "top": Qt.AlignmentFlag.AlignTop,
            "bottom": Qt.AlignmentFlag.AlignBottom,
            "top_left": Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
            "top_right": Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
            "bottom_left": Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
            "bottom_right": Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
        }
        return align_map.get(str(alignment).lower(), Qt.AlignmentFlag.AlignLeft)

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
        self.weight = kwargs.get('weight', None) # إضافة خاصية الوزن (bold)
        
        # تطبيق الخصائص بعد إنشاء العنصر الداخلي
        if self._internal_control:
            self._apply_properties()

    def _apply_properties(self):
        """تطبيق الخصائص على عنصر PyQt6 الداخلي باستخدام QSS بشكل أساسي."""
        if self._internal_control:
            self._internal_control.setVisible(self.visible)
            self._internal_control.setEnabled(not self.disabled)
            
            style_parts = []
            
            if self.color:
                style_parts.append(f"color: {self.color};")
            if self.bgcolor:
                style_parts.append(f"background-color: {self.bgcolor};")
            if self.border:
                style_parts.append(f"border: {self.border};")
            
            # معالجة الخطوط بذكاء لمنع أخطاء النوع (TypeError)
            if self.font_family or self.font_size or self.weight:
                font = self._internal_control.font()
                if self.font_family:
                    font.setFamily(self.font_family)
                if self.font_size is not None:
                    # تحويل إجباري إلى int لمنع خطأ PyQt6 مع float
                    try:
                        font.setPointSize(int(float(self.font_size)))
                    except (ValueError, TypeError):
                        pass
                if self.weight == "bold":
                    font.setBold(True)
                elif self.weight == "normal":
                    font.setBold(False)
                
                self._internal_control.setFont(font)
            
            if style_parts:
                # استخدام اسم الفئة في QSS لضمان دقة التطبيق
                class_name = self._internal_control.__class__.__name__
                self._internal_control.setStyleSheet(f"{class_name} {{ " + " ".join(style_parts) + " } }")

            if self.tooltip:
                self._internal_control.setToolTip(self.tooltip)

            if self.on_click and isinstance(self._internal_control, QPushButton):
                # فك الارتباط القديم لمنع التكرار
                try:
                    self._internal_control.clicked.disconnect()
                except:
                    pass
                self._internal_control.clicked.connect(lambda: _safe_call(self.on_click, self))

    def update(self):
        """تحديث خصائص العنصر وإعادة رسمه."""
        self._apply_properties()
        if self._page:
            self._page.update_control(self)

    @property
    def internal_control(self):
        """إرجاع عنصر PyQt6 الداخلي."""
        return self._internal_control

def _safe_call(func, *args):
    """دالة مساعدة لاستدعاء الدوال بأمان بغض النظر عن عدد الوسائط."""
    if not func:
        return
    try:
        sig = inspect.signature(func)
        params_count = len(sig.parameters)
        if params_count == 0:
            func()
        elif params_count == 1:
            func(args[0])
        else:
            func(*args[:params_count])
    except Exception as e:
        print(f"[FluxPy Warning] Error calling event handler: {e}")

# --- Basic Widgets ---

class Text(Control):
    def __init__(self, value, **kwargs):
        self.value = value
        # التعديل هنا: تعيين اللون الافتراضي إلى الأسود الصريح
        if 'color' not in kwargs:
            kwargs['color'] = '#000000'
        super().__init__(**kwargs)

    def _create_internal_control(self):
        label = QLabel(str(self.value))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _apply_properties(self):
        super()._apply_properties()
        if self._internal_control:
            self._internal_control.setText(str(self.value))

class ElevatedButton(Control):
    def __init__(self, text, width=None, **kwargs):
        self.text = text
        self.width = width
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton(self.text)
        if self.width:
            btn.setFixedWidth(self.width)
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
        self.icon = icon
        super().__init__(**kwargs)

    def _create_internal_control(self):
        btn = QPushButton()
        if self.icon:
            # محاولة تحميل أيقونة نظام أو ملف
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
