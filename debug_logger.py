"""
Debug Logger - Система детального логирования для отладки
"""
import traceback
from datetime import datetime


class DebugLogger:
    """Класс для детального логирования с цветами"""
    
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
    }
    
    def __init__(self, enabled=True):
        self.enabled = enabled
    
    def _print(self, message, color='white'):
        """Печать с цветом"""
        if not self.enabled:
            return
        
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        color_code = self.COLORS.get(color, self.COLORS['white'])
        reset = self.COLORS['reset']
        print(f"{color_code}[{timestamp}] {message}{reset}")
    
    def header(self, title):
        """Заголовок блока"""
        self._print(f"\n{'='*60}", 'cyan')
        self._print(f"  {title}", 'cyan')
        self._print(f"{'='*60}", 'cyan')
    
    def info(self, key, value):
        """Информация (ключ: значение)"""
        self._print(f"  {key}: {value}", 'white')
    
    def success(self, message):
        """Успешная операция"""
        self._print(f"  ✅ {message}", 'green')
    
    def warning(self, message):
        """Предупреждение"""
        self._print(f"  ⚠️  {message}", 'yellow')
    
    def error(self, message):
        """Ошибка"""
        self._print(f"  ❌ {message}", 'red')
    
    def debug(self, message):
        """Отладочное сообщение"""
        self._print(f"  🔍 {message}", 'blue')
    
    def dict_dump(self, title, data, max_depth=3):
        """Детальный вывод словаря"""
        self._print(f"  📦 {title}:", 'magenta')
        self._print_dict(data, indent=4, depth=0, max_depth=max_depth)
    
    def _print_dict(self, data, indent=0, depth=0, max_depth=3):
        """Рекурсивный вывод словаря"""
        if depth >= max_depth:
            self._print(" " * indent + "... (max depth)", 'white')
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._print(" " * indent + f"{key}:", 'white')
                    self._print_dict(value, indent + 2, depth + 1, max_depth)
                else:
                    self._print(" " * indent + f"{key}: {value}", 'white')
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._print(" " * indent + f"[{i}]:", 'white')
                    self._print_dict(item, indent + 2, depth + 1, max_depth)
                else:
                    self._print(" " * indent + f"[{i}]: {item}", 'white')
        else:
            self._print(" " * indent + str(data), 'white')
    
    def exception(self, e, context=""):
        """Вывод исключения с трейсбэком"""
        self._print(f"\n{'!'*60}", 'red')
        self._print(f"  💥 EXCEPTION: {context}", 'red')
        self._print(f"{'!'*60}", 'red')
        self._print(f"  Type: {type(e).__name__}", 'red')
        self._print(f"  Message: {str(e)}", 'red')
        self._print(f"\n  Traceback:", 'red')
        tb_lines = traceback.format_exc().split('\n')
        for line in tb_lines:
            if line.strip():
                self._print(f"    {line}", 'red')
        self._print(f"{'!'*60}\n", 'red')
    
    def footer(self):
        """Подвал блока"""
        self._print(f"{'='*60}\n", 'cyan')


# Глобальный экземпляр логгера
debug = DebugLogger(enabled=True)


def log_function_call(func):
    """Декоратор для автоматического логирования вызовов функций"""
    def wrapper(*args, **kwargs):
        debug.header(f"CALL: {func.__name__}")
        debug.info("Args", args)
        debug.info("Kwargs", kwargs)
        
        try:
            result = func(*args, **kwargs)
            debug.success(f"{func.__name__} completed successfully")
            debug.footer()
            return result
        except Exception as e:
            debug.exception(e, f"in {func.__name__}")
            debug.footer()
            raise
    
    return wrapper


print("✅ debug_logger.py загружен")
