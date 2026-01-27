"""
Главный файл запуска Telegram бота
"""
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Проверка .env файла
if not Path(".env").exists():
    print("❌ Файл .env не найден!")
    print("📝 Создайте файл .env с необходимыми переменными")
    sys.exit(1)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN.startswith("your_"):
    print("❌ BOT_TOKEN не указан в .env!")
    sys.exit(1)

print("=" * 60)
print("🔧 Инициализация бота...")
logger.info("Запуск AI Bot Creator")

# Выполняем миграции базы данных
print("\n🔄 Проверка миграций базы данных...")
try:
    from database.migrations.migration_manager import MigrationManager
    migration_manager = MigrationManager()
    migration_manager.run_migrations()
    print("✅ Миграции выполнены\n")
except Exception as e:
    print(f"⚠️ Ошибка выполнения миграций: {e}")
    print("⚠️ Продолжаю запуск без миграций...\n")

try:
    from telebot.types import BotCommand
    from loader import bot
    logger.info("Loader импортирован")
except Exception as e:
    logger.error(f"Ошибка импорта: {e}", exc_info=True)
    sys.exit(1)

# Обновляем loader с инициализированной БД
from database.database import db as database
from loader import bot
import loader
loader.db = database

print("⏳ Загрузка модулей...")

try:
    # Импортируем обработчики
    from handlers import (start, projects, bot_creation, bot_card, profile, 
                         tariffs, settings, categories, keywords, category_sections,
                         connections, site_analysis, media_upload,
                         reviews_generator, pinterest_settings, 
                         text_style_settings, universal_platform_settings, telegram_topics,
                         global_scheduler, auto_notifications,
                         notification_scheduler, auto_publish_scheduler)
    
    # Импортируем настройки платформ
    from handlers import platform_settings
    
    # Импортируем админ-панель
    from handlers.admin import admin_main
    
    # ВАЖНО: text_input_handler должен загружаться ПОСЛЕДНИМ!
    from handlers import text_input_handler
    
    logger.info("✅ Все модули загружены")
    
    # ═══════════════════════════════════════════════════════════════
    # НАСТРОЙКА CALLBACK TRACKER (отлов "мёртвых" кнопок)
    # ═══════════════════════════════════════════════════════════════
    print("\n🔍 Настройка отслеживания callback кнопок...")
    try:
        from callback_tracker import setup_callback_tracker, print_callback_report
        setup_callback_tracker(bot)
        logger.info("✅ Callback tracker активирован")
        print("✅ Отслеживание кнопок активировано")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось настроить callback tracker: {e}")
        print(f"⚠️ Callback tracker не активирован: {e}")
    
except Exception as e:
    logger.error(f"Ошибка загрузки модулей: {e}", exc_info=True)
    sys.exit(1)


def main():
    """Главная функция запуска бота"""
    print("=" * 60)
    print("🚀 AI BOT CREATOR v1.0")
    print("=" * 60)
    
    # Проверка подключения к Telegram
    try:
        bot_info = bot.get_me()
        logger.info(f"Бот: @{bot_info.username} (ID: {bot_info.id})")
        print(f"✅ Бот: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {e}")
        sys.exit(1)
    
    # Установка команд бота
    try:
        commands = [
            BotCommand("start", "🏠 Главное меню"),
            BotCommand("help", "🆘 Помощь"),
        ]
        bot.set_my_commands(commands)
        logger.info("Команды установлены")
    except Exception as e:
        logger.warning(f"Не удалось установить команды: {e}")
    
    # Удаление webhook (для polling режима)
    try:
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook очищен")
    except Exception as e:
        logger.warning(f"Ошибка очистки webhook: {e}")
    
    print("=" * 60)
    print("✅ БОТ ЗАПУЩЕН")
    print("=" * 60)
    print("💡 Нажмите Ctrl+C для остановки")
    print()
    
    # Запускаем планировщик автоматических уведомлений
    try:
        from handlers.notification_scheduler import start_notification_scheduler
        start_notification_scheduler()
        logger.info("✅ Планировщик уведомлений запущен")
        print("✅ Автоматические уведомления активированы")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось запустить планировщик уведомлений: {e}")
        print(f"⚠️ Планировщик уведомлений не запущен: {e}")
    
    # Запускаем планировщик автоматических публикаций
    try:
        from handlers.auto_publish_scheduler import start_auto_publish_scheduler
        start_auto_publish_scheduler()
        logger.info("✅ Планировщик автопубликаций запущен")
        print("✅ Автоматические публикации активированы")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось запустить планировщик публикаций: {e}")
        print(f"⚠️ Планировщик публикаций не запущен: {e}")
    
    # Запуск бота в режиме polling
    try:
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=30,
            skip_pending=True,
            allowed_updates=['message', 'callback_query']
        )
    except KeyboardInterrupt:
        logger.info("Остановка бота по Ctrl+C")
        print("\n👋 Бот остановлен")
        
        # Останавливаем планировщик уведомлений
        try:
            from handlers.notification_scheduler import stop_notification_scheduler
            stop_notification_scheduler()
        except:
            pass
        
        # Останавливаем планировщик публикаций
        try:
            from handlers.auto_publish_scheduler import stop_auto_publish_scheduler
            stop_auto_publish_scheduler()
        except:
            pass
        
        # Выводим статистику по кнопкам при остановке
        try:
            from callback_tracker import print_callback_report
            print_callback_report()
        except:
            pass
            
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        print("✅ Выход")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
