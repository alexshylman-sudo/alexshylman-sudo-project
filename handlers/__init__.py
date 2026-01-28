# -*- coding: utf-8 -*-
"""
Handlers Package
Загружает все обработчики для Telegram бота
"""

# Website handlers
try:
    from handlers.website import *
    print("✅ handlers/website/ загружен")
except Exception as e:
    print(f"⚠️ handlers/website/ не загружен: {e}")

# Reviews handlers
try:
    from handlers.reviews import *
    print("✅ handlers/reviews/ загружен")
except Exception as e:
    print(f"⚠️ handlers/reviews/ не загружен: {e}")

# Platform connections
try:
    from handlers.platform_connections import *
    print("✅ handlers/platform_connections/ загружен")
except Exception as e:
    print(f"⚠️ handlers/platform_connections/ не загружен: {e}")

# Platform category
try:
    from handlers.platform_category import *
    print("✅ handlers/platform_category/ загружен")
except Exception as e:
    print(f"⚠️ handlers/platform_category/ не загружен: {e}")

# Platform settings
try:
    from handlers.platform_settings import *
    print("✅ handlers/platform_settings/ загружен")
except Exception as e:
    print(f"⚠️ handlers/platform_settings/ не загружен: {e}")

# Admin handlers
try:
    from handlers.admin import *
    print("✅ handlers/admin/ загружен")
except Exception as e:
    print(f"⚠️ handlers/admin/ не загружен: {e}")

# Main handlers
try:
    from handlers.start import *
    print("✅ handlers/start.py загружен")
except Exception as e:
    print(f"⚠️ handlers/start.py не загружен: {e}")

try:
    from handlers.projects import *
    print("✅ handlers/projects.py загружен")
except Exception as e:
    print(f"⚠️ handlers/projects.py не загружен: {e}")

try:
    from handlers.bot_creation import *
    print("✅ handlers/bot_creation.py загружен")
except Exception as e:
    print(f"⚠️ handlers/bot_creation.py не загружен: {e}")

try:
    from handlers.bot_card import *
    print("✅ handlers/bot_card.py загружен")
except Exception as e:
    print(f"⚠️ handlers/bot_card.py не загружен: {e}")

try:
    from handlers.profile import *
    print("✅ handlers/profile.py загружен")
except Exception as e:
    print(f"⚠️ handlers/profile.py не загружен: {e}")

try:
    from handlers.tariffs import *
    print("✅ handlers/tariffs.py загружен")
except Exception as e:
    print(f"⚠️ handlers/tariffs.py не загружен: {e}")

try:
    from handlers.settings import *
    print("✅ handlers/settings.py загружен")
except Exception as e:
    print(f"⚠️ handlers/settings.py не загружен: {e}")

try:
    from handlers.categories import *
    print("✅ handlers/categories.py загружен")
except Exception as e:
    print(f"⚠️ handlers/categories.py не загружен: {e}")

try:
    from handlers.keywords import *
    print("✅ handlers/keywords.py загружен")
except Exception as e:
    print(f"⚠️ handlers/keywords.py не загружен: {e}")

try:
    from handlers.category_sections import *
    print("✅ handlers/category_sections.py загружен")
except Exception as e:
    print(f"⚠️ handlers/category_sections.py не загружен: {e}")

try:
    from handlers.connections import *
    print("✅ handlers/connections.py загружен")
except Exception as e:
    print(f"⚠️ handlers/connections.py не загружен: {e}")

try:
    from handlers.connection_instructions import *
    print("✅ handlers/connection_instructions.py загружен")
except Exception as e:
    print(f"⚠️ handlers/connection_instructions.py не загружен: {e}")

try:
    from handlers.site_analysis import *
    print("✅ handlers/site_analysis.py загружен")
except Exception as e:
    print(f"⚠️ handlers/site_analysis.py не загружен: {e}")

try:
    from handlers.site_colors_detector import *
    print("✅ handlers/site_colors_detector.py загружен")
except Exception as e:
    print(f"⚠️ handlers/site_colors_detector.py не загружен: {e}")

try:
    from handlers.media_upload import *
    print("✅ handlers/media_upload.py загружен")
except Exception as e:
    print(f"⚠️ handlers/media_upload.py не загружен: {e}")

try:
    from handlers.pinterest_settings import *
    print("✅ handlers/pinterest_settings.py загружен")
except Exception as e:
    print(f"⚠️ handlers/pinterest_settings.py не загружен: {e}")

try:
    from handlers.pinterest_images_settings import *
    print("✅ handlers/pinterest_images_settings.py загружен")
except Exception as e:
    print(f"⚠️ handlers/pinterest_images_settings.py не загружен: {e}")

try:
    from handlers.telegram_images_settings import *
    print("✅ handlers/telegram_images_settings.py загружен")
except Exception as e:
    print(f"⚠️ handlers/telegram_images_settings.py не загружен: {e}")

try:
    from handlers.text_style_settings import *
    print("✅ handlers/text_style_settings.py загружен")
except Exception as e:
    print(f"⚠️ handlers/text_style_settings.py не загружен: {e}")

try:
    from handlers.universal_platform_settings import *
    print("✅ handlers/universal_platform_settings.py загружен")
except Exception as e:
    print(f"⚠️ handlers/universal_platform_settings.py не загружен: {e}")

try:
    from handlers.telegram_topics import *
    print("✅ handlers/telegram_topics.py загружен")
except Exception as e:
    print(f"⚠️ handlers/telegram_topics.py не загружен: {e}")

try:
    from handlers.global_scheduler import *
    print("✅ handlers/global_scheduler.py загружен")
except Exception as e:
    print(f"⚠️ handlers/global_scheduler.py не загружен: {e}")

try:
    from handlers.platform_scheduler import *
    print("✅ handlers/platform_scheduler.py загружен")
except Exception as e:
    print(f"⚠️ handlers/platform_scheduler.py не загружен: {e}")

try:
    from handlers.auto_notifications import *
    print("✅ handlers/auto_notifications.py загружен")
except Exception as e:
    print(f"⚠️ handlers/auto_notifications.py не загружен: {e}")

try:
    from handlers.notification_scheduler import *
    print("✅ handlers/notification_scheduler.py загружен")
except Exception as e:
    print(f"⚠️ handlers/notification_scheduler.py не загружен: {e}")

try:
    from handlers.auto_publish_scheduler import *
    print("✅ handlers/auto_publish_scheduler.py загружен")
except Exception as e:
    print(f"⚠️ handlers/auto_publish_scheduler.py не загружен: {e}")

try:
    from handlers.reviews_generator import *
    print("✅ handlers/reviews_generator.py загружен")
except Exception as e:
    print(f"⚠️ handlers/reviews_generator.py не загружен: {e}")

try:
    from handlers.state_manager import *
    print("✅ handlers/state_manager.py загружен")
except Exception as e:
    print(f"⚠️ handlers/state_manager.py не загружен: {e}")

try:
    from handlers.text_input_handler import *
    print("✅ handlers/text_input_handler.py загружен")
except Exception as e:
    print(f"⚠️ handlers/text_input_handler.py не загружен: {e}")

# VK Integration (OAuth)
try:
    from handlers.vk_integration import *
    print("✅ VK Integration Package загружен")
except Exception as e:
    print(f"⚠️ VK Integration не загружен: {e}")

print("=" * 80)
print("✅ Все handlers загружены")
print("=" * 80)
