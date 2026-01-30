from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from ..widgets.dialogs import Page
from .debugger import FluxDebugger
import sys
import os
import threading
import webbrowser
from flask import Flask, render_template_string

# تعيين معالج الاستثناءات المخصص
sys.excepthook = FluxDebugger.handle_exception

class FluxApp:
    """
    الفئة الرئيسية لتشغيل تطبيق FluxPy.
    """
    def __init__(self, target="desktop", port=5000):
        self.target = target
        self.port = port
        self.page = None
        self.app = None
        self.flask_app = Flask(__name__)
        
        # مسار الشعار الشفاف
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        self.icon_path = os.path.join(assets_dir, "logo_transparent.png")

    def run(self, page_func):
        """
        تشغيل التطبيق.
        :param page_func: دالة تأخذ كائن Page وتقوم ببناء واجهة المستخدم.
        """
        if self.target == "desktop":
            self._run_desktop(page_func)
        elif self.target == "web":
            self._run_web(page_func)
        else:
            raise ValueError("Target must be 'desktop' or 'web'")

    def _run_desktop(self, page_func):
        """تشغيل التطبيق كـ تطبيق سطح مكتب (Desktop)."""
        self.app = QApplication(sys.argv)
        
        # إنشاء كائن الصفحة
        self.page = Page()
        
        # بناء واجهة المستخدم
        page_func(self.page)
        
        # تطبيق خصائص النافذة
        window = self.page.internal_control
        window.setWindowTitle(self.page.title)
        if os.path.exists(self.icon_path):
            window.setWindowIcon(QIcon(self.icon_path))
        window.resize(self.page.window_width, self.page.window_height)
        
        # عرض النافذة الرئيسية
        window.show()
        
        # بدء حلقة الأحداث
        sys.exit(self.app.exec())

    def _run_web(self, page_func):
        """تشغيل التطبيق كـ تطبيق ويب (Web) باستخدام Flask."""
        self.page = Page(scroll=True) # افتراض التمرير في الويب
        page_func(self.page)
        
        @self.flask_app.route('/')
        def index():
            # يجب أن يتم استدعاء render_web() لكل عنصر تحكم هنا
            # حالياً، نستخدم محاكاة بسيطة
            content_html = "<h1>Web Target (Under Development)</h1>"
            
            html = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>{self.page.title}</title>
                <style>
                    body {{ 
                        background-color: {self.page.bgcolor}; 
                        padding: {self.page.padding}px; 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                    }}
                </style>
            </head>
            <body>
                {content_html}
            </body>
            </html>
            """
            return render_template_string(html)

        print(f"Starting FluxPy Web at http://127.0.0.1:{self.port}")
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{self.port}")).start()
        self.flask_app.run(port=self.port, debug=False)

# --- Export for easy import ---
__all__ = [
    "FluxApp"
]
