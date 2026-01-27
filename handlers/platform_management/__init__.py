# -*- coding: utf-8 -*-
"""
platform_management/__init__.py - Управление платформами

Модули:
- platform_menu - Главное меню платформы
- website_management - Управление сайтами
- instagram_management - Управление Instagram
- vk_management - Управление ВКонтакте
- pinterest_management - Управление Pinterest
- telegram_management - Управление Telegram
- platform_scheduler - Планировщик автопостинга
"""

from .platform_menu import register_platform_menu_handlers
from .website_management import register_website_management_handlers
from .instagram_management import register_instagram_management_handlers
from .vk_management import register_vk_management_handlers
from .pinterest_management import register_pinterest_management_handlers
from .telegram_management import register_telegram_management_handlers
from .platform_scheduler import register_platform_scheduler_handlers


def register_platform_handlers(bot):
    """Регистрирует все обработчики управления платформами"""
    print("📦 Регистрация обработчиков управления платформами...")
    
    # Меню платформ (ЭТАП 1)
    register_platform_menu_handlers(bot)
    
    # Управление сайтами (ЭТАП 2)
    register_website_management_handlers(bot)
    
    # Управление Instagram (ЭТАП 3)
    register_instagram_management_handlers(bot)
    
    # Управление ВКонтакте (ЭТАП 4)
    register_vk_management_handlers(bot)
    
    # Управление Pinterest (ЭТАП 5)
    register_pinterest_management_handlers(bot)
    
    # Управление Telegram (ЭТАП 6)
    register_telegram_management_handlers(bot)
    
    # Планировщик автопостинга (ЭТАП 7)
    register_platform_scheduler_handlers(bot)
    
    print("✅ Обработчики платформ зарегистрированы")


__all__ = ['register_platform_handlers']
