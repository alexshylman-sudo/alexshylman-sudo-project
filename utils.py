# -*- coding: utf-8 -*-
"""
Утилиты для бота
"""
import html as html_module
import logging

logger = logging.getLogger(__name__)


def escape_html(text):
    """
    Экранирует HTML символы для безопасного отображения в Telegram
    
    Args:
        text: Текст для экранирования
        
    Returns:
        str: Экранированный текст
    """
    if not text:
        return ""
    return html_module.escape(str(text))


def safe_answer_callback(bot, call_id, text="", show_alert=False):
    """
    Безопасный ответ на callback query
    Обрабатывает ошибку "query is too old"
    
    Args:
        bot: Объект бота
        call_id: ID callback query
        text: Текст ответа
        show_alert: Показывать как alert
        
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        bot.answer_callback_query(call_id, text, show_alert=show_alert)
        return True
    except Exception as e:
        # Игнорируем ошибку "query is too old" - это нормально для долгих операций
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            logger.debug(f"Callback query устарел (это нормально для долгих операций)")
            return False
        else:
            logger.error(f"Ошибка answer_callback_query: {e}")
            return False


print("✅ utils.py загружен")
