from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSize
from .base import Control

# --- Media Widgets ---

class Image(Control):
    def __init__(self, src, width=None, height=None, fit="cover", **kwargs):
        self.src = src
        self.width = width
        self.height = height
        self.fit = fit # 'cover', 'contain', 'fill', 'scale-down', 'none'
        super().__init__(**kwargs)

    def _create_internal_control(self):
        lbl = QLabel()
        self._load_image(lbl)
        return lbl

    def _load_image(self, label):
        if self.src:
            pixmap = QPixmap(self.src)
            if pixmap.isNull():
                label.setText("Image not found")
                return

            if self.width and self.height:
                size = QSize(self.width, self.height)
                if self.fit == "cover":
                    # محاكاة cover: قص الصورة لتناسب الأبعاد
                    scaled_pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    # قد تحتاج إلى قص إضافي هنا
                    label.setPixmap(scaled_pixmap)
                elif self.fit == "contain":
                    # محاكاة contain: تغيير الحجم للحفاظ على نسبة العرض إلى الارتفاع
                    scaled_pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    label.setPixmap(scaled_pixmap)
                elif self.fit == "fill":
                    # محاكاة fill: تمديد الصورة لملء الأبعاد
                    scaled_pixmap = pixmap.scaled(size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    label.setPixmap(scaled_pixmap)
                else: # scale-down, none
                    label.setPixmap(pixmap)
            else:
                label.setPixmap(pixmap)

    def _apply_properties(self):
        super()._apply_properties()
        self._load_image(self._internal_control) # إعادة تحميل الصورة عند تحديث الخصائص

class Icon(Control):
    def __init__(self, name, size=24, color=None, **kwargs):
        self.name = name # اسم الأيقونة (افتراضياً مسار ملف أو اسم أيقونة Qt)
        self.size = size
        self.color = color
        super().__init__(**kwargs)

    def _create_internal_control(self):
        lbl = QLabel()
        self._load_icon(lbl)
        return lbl

    def _load_icon(self, label):
        if self.name:
            # محاولة التحميل كأيقونة نظام Qt
            icon = QIcon.fromTheme(self.name)
            if icon.isNull():
                # محاولة التحميل كملف
                icon = QIcon(self.name)
            
            if not icon.isNull():
                pixmap = icon.pixmap(QSize(self.size, self.size))
                label.setPixmap(pixmap)
            else:
                label.setText(f"Icon: {self.name}")

    def _apply_properties(self):
        super()._apply_properties()
        self._load_icon(self._internal_control)

# --- Export for easy import ---
__all__ = [
    "Image", "Icon"
]
