import sys
import traceback

class FluxDebugger:
    """
    نظام المصحح الذكي لـ FluxPy.
    يلتقط الاستثناءات غير المعالجة ويعرض معلومات مفصلة.
    """
    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        tb = traceback.extract_tb(exc_traceback)
        last_call = tb[-1]
        
        # TODO: إضافة منطق اقتراح الحلول الذكية
        
        print(f"\n[FluxPy Smart Debugger]")
        print("-" * 30)
        print(f"File: {last_call.filename}")
        print(f"Line: {last_call.lineno}")
        print(f"Error Type: {exc_type.__name__}")
        print(f"Message: {exc_value}")
        print("-" * 30)
        
        # استدعاء المعالج الافتراضي لعرض تتبع المكدس الكامل
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

# تعيين معالج الاستثناءات المخصص
sys.excepthook = FluxDebugger.handle_exception

__all__ = ["FluxDebugger"]
