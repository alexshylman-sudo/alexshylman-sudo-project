"""
Система отслеживания нажатий кнопок (callback query)
Помогает обнаружить "мёртвые" кнопки, которые не работают
"""
import logging
import time
import functools
from collections import defaultdict
from datetime import datetime

# Получаем root logger, чтобы писать в тот же файл что и main
logger = logging.getLogger('callback_tracker')
logger.setLevel(logging.WARNING)  # Записываем только предупреждения

# Статистика нажатий кнопок
callback_stats = defaultdict(lambda: {
    'count': 0,
    'last_used': None,
    'errors': 0,
    'last_error': None
})

# Зарегистрированные обработчики
registered_handlers = {}


def track_callback(callback_prefix=None):
    """
    Декоратор для отслеживания callback обработчиков
    
    Использование:
    @track_callback("my_button")
    @bot.callback_query_handler(func=lambda call: call.data.startswith("my_button_"))
    def my_handler(call):
        ...
    """
    def decorator(func):
        handler_name = callback_prefix or func.__name__
        
        # Регистрируем обработчик
        registered_handlers[handler_name] = {
            'function': func.__name__,
            'file': func.__code__.co_filename,
            'line': func.__code__.co_firstlineno,
            'registered_at': datetime.now().isoformat()
        }
        
        @functools.wraps(func)
        def wrapper(call):
            callback_data = call.data
            user_id = call.from_user.id
            username = call.from_user.username or "NoUsername"
            
            # Логируем нажатие
            logger.info(
                f"🔘 CALLBACK PRESSED: '{callback_data}' "
                f"| User: {user_id} (@{username}) "
                f"| Handler: {handler_name}"
            )
            
            # Обновляем статистику
            callback_stats[callback_data]['count'] += 1
            callback_stats[callback_data]['last_used'] = datetime.now().isoformat()
            
            start_time = time.time()
            
            try:
                # Выполняем оригинальную функцию
                result = func(call)
                
                # Вычисляем время выполнения
                execution_time = (time.time() - start_time) * 1000  # в миллисекундах
                
                logger.info(
                    f"✅ CALLBACK SUCCESS: '{callback_data}' "
                    f"| Executed in {execution_time:.2f}ms "
                    f"| Handler: {handler_name}"
                )
                
                return result
                
            except Exception as e:
                # Логируем ошибку
                execution_time = (time.time() - start_time) * 1000
                
                callback_stats[callback_data]['errors'] += 1
                callback_stats[callback_data]['last_error'] = str(e)
                
                logger.error(
                    f"❌ CALLBACK ERROR: '{callback_data}' "
                    f"| User: {user_id} (@{username}) "
                    f"| Handler: {handler_name} "
                    f"| File: {func.__code__.co_filename}:{func.__code__.co_firstlineno} "
                    f"| Error: {str(e)[:200]} "
                    f"| Execution time: {execution_time:.2f}ms",
                    exc_info=True
                )
                
                # Отправляем уведомление пользователю
                try:
                    from loader import bot
                    bot.answer_callback_query(
                        call.id,
                        "⚠️ Произошла ошибка. Попробуйте позже.",
                        show_alert=True
                    )
                except:
                    pass
                
                raise  # Пробрасываем ошибку дальше
        
        return wrapper
    return decorator


def log_unhandled_callback(call):
    """
    Логирует нажатия на кнопки, для которых нет обработчика
    Эта функция должна быть последним обработчиком
    """
    callback_data = call.data
    user_id = call.from_user.id
    username = call.from_user.username or "NoUsername"
    
    logger.warning(
        f"⚠️ UNHANDLED CALLBACK: '{callback_data}' "
        f"| User: {user_id} (@{username}) "
        f"| 🚨 НЕТ ОБРАБОТЧИКА ДЛЯ ЭТОЙ КНОПКИ!"
    )
    
    # Отправляем уведомление пользователю
    try:
        from loader import bot
        bot.answer_callback_query(
            call.id,
            "❌ Кнопка не работает. Обратитесь к администратору.",
            show_alert=True
        )
    except:
        pass


def get_callback_statistics():
    """Возвращает статистику по всем callback-кнопкам"""
    stats = {
        'total_callbacks': len(callback_stats),
        'total_presses': sum(s['count'] for s in callback_stats.values()),
        'total_errors': sum(s['errors'] for s in callback_stats.values()),
        'callbacks': dict(callback_stats),
        'registered_handlers': registered_handlers
    }
    return stats


def print_callback_report():
    """Выводит отчёт по использованию кнопок в консоль"""
    stats = get_callback_statistics()
    
    print("\n" + "="*80)
    print("📊 ОТЧЁТ ПО CALLBACK КНОПКАМ")
    print("="*80)
    print(f"Всего уникальных callback: {stats['total_callbacks']}")
    print(f"Всего нажатий: {stats['total_presses']}")
    print(f"Всего ошибок: {stats['total_errors']}")
    print(f"Зарегистрировано обработчиков: {len(stats['registered_handlers'])}")
    
    if stats['callbacks']:
        print("\n" + "-"*80)
        print("ТОП-10 САМЫХ ИСПОЛЬЗУЕМЫХ КНОПОК:")
        print("-"*80)
        
        sorted_callbacks = sorted(
            stats['callbacks'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]
        
        for i, (callback, data) in enumerate(sorted_callbacks, 1):
            error_info = f" (❌ {data['errors']} ошибок)" if data['errors'] > 0 else ""
            print(f"{i}. {callback}: {data['count']} нажатий{error_info}")
    
    if stats['total_errors'] > 0:
        print("\n" + "-"*80)
        print("⚠️ КНОПКИ С ОШИБКАМИ:")
        print("-"*80)
        
        error_callbacks = {k: v for k, v in stats['callbacks'].items() if v['errors'] > 0}
        for callback, data in sorted(error_callbacks.items(), key=lambda x: x[1]['errors'], reverse=True):
            print(f"❌ {callback}: {data['errors']} ошибок")
            if data['last_error']:
                print(f"   Последняя ошибка: {data['last_error'][:100]}")
    
    print("\n" + "-"*80)
    print("🔧 ЗАРЕГИСТРИРОВАННЫЕ ОБРАБОТЧИКИ:")
    print("-"*80)
    for name, info in stats['registered_handlers'].items():
        print(f"✓ {name}")
        print(f"  Функция: {info['function']}")
        print(f"  Файл: {info['file']}:{info['line']}")
    
    print("\n" + "="*80)


def setup_callback_tracker(bot):
    """
    Настраивает отслеживание необработанных callback
    Вызывается в main.py после регистрации всех обработчиков
    """
    # Регистрируем обработчик для всех необработанных callback
    @bot.callback_query_handler(func=lambda call: True)
    def catch_all_callbacks(call):
        print(f"🔴 CATCH-ALL перехватил callback: {call.data[:80]}...")
        log_unhandled_callback(call)
    
    logger.info("✅ Callback tracker настроен (catch-all обработчик зарегистрирован)")


print("✅ callback_tracker.py загружен")
