"""
Safe Debug Logger - Безопасная обёртка для логирования
Если основной логгер не работает - пишет в print
"""

try:
    from debug_logger import debug as _debug
    DEBUG_AVAILABLE = True
except Exception as e:
    print(f"⚠️ debug_logger не загружен: {e}")
    DEBUG_AVAILABLE = False


class SafeDebug:
    """Безопасный логгер с fallback на print"""
    
    def __init__(self):
        self.enabled = DEBUG_AVAILABLE
    
    def _safe_call(self, method_name, *args, **kwargs):
        """Безопасный вызов метода логгера"""
        if not self.enabled:
            return
        
        try:
            if hasattr(_debug, method_name):
                method = getattr(_debug, method_name)
                method(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ Ошибка логирования ({method_name}): {e}")
    
    def header(self, title):
        self._safe_call('header', title)
    
    def info(self, key, value):
        self._safe_call('info', key, value)
    
    def success(self, message):
        self._safe_call('success', message)
    
    def warning(self, message):
        self._safe_call('warning', message)
    
    def error(self, message):
        self._safe_call('error', message)
    
    def debug(self, message):
        self._safe_call('debug', message)
    
    def dict_dump(self, title, data, max_depth=3):
        self._safe_call('dict_dump', title, data, max_depth)
    
    def exception(self, e, context=""):
        self._safe_call('exception', e, context)
    
    def footer(self):
        self._safe_call('footer')


# Глобальный безопасный логгер
debug = SafeDebug()

print("✅ safe_debug.py загружен")
