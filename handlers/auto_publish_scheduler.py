# -*- coding: utf-8 -*-
"""
Планировщик автоматических публикаций на платформы
Публикует контент по расписанию из таблицы platform_schedules
"""
import threading
import time
import logging
from datetime import datetime, time as dt_time
# from psycopg2.extras import RealDictCursor  # Не используется

logger = logging.getLogger(__name__)


def get_user_id_from_category(db, category):
    """
    Получает user_id из категории через bot_id
    
    Args:
        db: Database instance
        category: dict с данными категории
        
    Returns:
        int: user_id или None если не найден
    """
    try:
        # Получаем bot_id из категории
        bot_id = category.get('bot_id')
        if not bot_id:
            logger.error(f"❌ В категории отсутствует bot_id")
            return None
        
        # Получаем user_id через бота
        db.cursor.execute("SELECT user_id FROM bots WHERE id = %s", (bot_id,))
        bot_result = db.cursor.fetchone()
        
        if not bot_result:
            logger.error(f"❌ Бот {bot_id} не найден")
            return None
        
        user_id = bot_result['user_id'] if isinstance(bot_result, dict) else bot_result[0]
        return user_id
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения user_id: {e}")
        return None


class AutoPublishScheduler:
    """Планировщик автоматических публикаций"""
    
    def __init__(self):
        self.is_running = False
        self.thread = None
        logger.info("📅 AutoPublishScheduler инициализирован")
    
    def start(self):
        """Запускает планировщик в отдельном потоке"""
        if self.is_running:
            logger.warning("⚠️ Планировщик публикаций уже запущен")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("✅ Планировщик автоматических публикаций запущен")
    
    def stop(self):
        """Останавливает планировщик"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("🛑 Планировщик автоматических публикаций остановлен")
    
    def _get_scheduled_publications(self):
        """
        Получает список запланированных публикаций на текущее время
        
        Returns:
            list: Список словарей с информацией о публикациях
        """
        try:
            from database.database import db
            
            # Откатываем любую незавершенную транзакцию
            try:
                db.conn.rollback()
            except:
                pass
            
            # Создаём новый cursor для этого запроса с совместимостью psycopg2/3
            try:
                import psycopg
                from psycopg.rows import dict_row
                cursor = db.conn.cursor(row_factory=dict_row)
            except ImportError:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                cursor = db.conn.cursor(cursor_factory=RealDictCursor)
            
            now = datetime.now()
            current_time = now.time()
            current_day = now.strftime('%A').lower()  # monday, tuesday, etc.
            
            # Проверяем существование таблицы
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'platform_schedules'
                )
            """)
            result = cursor.fetchone()
            table_exists = result['exists'] if result else False
            
            if not table_exists:
                logger.warning("⚠️ Таблица platform_schedules не существует")
                cursor.close()
                return []
            
            # Находим все активные расписания
            cursor.execute("""
                SELECT 
                    category_id, 
                    platform_type, 
                    platform_id,
                    schedule_days,
                    schedule_times,
                    posts_per_day
                FROM platform_schedules
                WHERE enabled = TRUE
            """)
            
            schedules = cursor.fetchall()
            cursor.close()
            
            publications = []
            
            # Маппинг сокращенных дней в полные
            days_map_short = {
                'mon': 'monday',
                'tue': 'tuesday',
                'wed': 'wednesday',
                'thu': 'thursday',
                'fri': 'friday',
                'sat': 'saturday',
                'sun': 'sunday'
            }
            
            for schedule in schedules:
                # Проверяем день недели (поддержка обоих форматов)
                days = schedule.get('schedule_days', []) or []
                if days:
                    day_match = False
                    for day in days:
                        day_lower = day.lower()
                        # Конвертируем сокращенный формат в полный
                        if day_lower in days_map_short:
                            day_lower = days_map_short[day_lower]
                        
                        if day_lower == current_day:
                            day_match = True
                            break
                    
                    if not day_match:
                        continue
                
                # Проверяем время
                times = schedule.get('schedule_times', []) or []
                if not times:
                    continue
                
                # Сравниваем время (с точностью до минуты)
                for time_str in times:
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        schedule_time = dt_time(hour, minute)
                        
                        # Если текущее время совпадает (с точностью до минуты)
                        if current_time.hour == schedule_time.hour and current_time.minute == schedule_time.minute:
                            publications.append({
                                'category_id': schedule['category_id'],
                                'platform_type': schedule['platform_type'],
                                'platform_id': schedule['platform_id'],
                                'posts_per_day': schedule.get('posts_per_day', 1)
                            })
                    except:
                        continue
            
            return publications
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения расписания публикаций: {e}")
            try:
                from database.database import db
                db.conn.rollback()
            except:
                pass
            return []
    
    def _publish_content(self, category_id, platform_type, platform_id):
        """
        Публикует контент на платформу
        
        Args:
            category_id: ID категории
            platform_type: Тип платформы (website, telegram, pinterest)
            platform_id: ID платформы
        """
        try:
            logger.info(f"📤 Начинаю публикацию: category={category_id}, platform={platform_type}, id={platform_id}")
            
            if platform_type == 'website':
                self._publish_to_website(category_id, platform_id)
            elif platform_type == 'telegram':
                self._publish_to_telegram(category_id, platform_id)
            elif platform_type == 'pinterest':
                self._publish_to_pinterest(category_id, platform_id)
            else:
                logger.warning(f"⚠️ Неизвестный тип платформы: {platform_type}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка публикации на {platform_type}: {e}")
    
    def _publish_to_website(self, category_id, platform_id):
        """Публикация статьи на сайт"""
        try:
            from database.database import db
            import json
            
            # Получаем категорию
            category = db.get_category(category_id)
            if not category:
                logger.error(f"❌ Категория {category_id} не найдена")
                return
            
            # Конвертируем в dict если нужно
            if not isinstance(category, dict):
                category = dict(category)
            
            # Проверяем наличие user_id
            user_id = get_user_id_from_category(db, category)
            if not user_id:
                return
            
            # Получаем пользователя
            user = db.get_user(user_id)
            if not user:
                logger.error(f"❌ Пользователь {user_id} не найден")
                return
            
            # Конвертируем в dict если нужно
            if not isinstance(user, dict):
                user = dict(user)
            
            # Находим подключенный сайт
            connections = user.get('platform_connections', {})
            if isinstance(connections, str):
                connections = json.loads(connections)
            
            websites = connections.get('websites', [])
            
            website = None
            for site in websites:
                if isinstance(site, dict) and site.get('url') == platform_id and site.get('status') == 'active':
                    website = site
                    break
            
            if not website:
                logger.error(f"❌ Сайт {platform_id} не найден или не активен")
                return
            
            # Генерируем и публикуем статью
            from handlers.website.article_generation import generate_and_publish_article
            
            logger.info(f"📝 Генерация статьи для категории '{category['name']}'")
            result = generate_and_publish_article(
                user_id=user_id,
                category_id=category_id,
                website=website
            )
            
            if result.get('success'):
                logger.info(f"✅ Статья опубликована на {website['url']}")
            else:
                logger.error(f"❌ Ошибка публикации статьи: {result.get('error')}")
            
        except KeyError as e:
            logger.error(f"❌ Ошибка публикации на сайт: отсутствует ключ {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка публикации на сайт: {e}")
    
    def _publish_to_telegram(self, category_id, platform_id):
        """Публикация поста в Telegram"""
        try:
            from database.database import db
            from loader import bot
            import json
            
            # Получаем категорию
            category = db.get_category(category_id)
            if not category:
                logger.error(f"❌ Категория {category_id} не найдена")
                return
            
            # Конвертируем в dict если нужно
            if not isinstance(category, dict):
                category = dict(category)
            
            # Проверяем наличие user_id
            user_id = get_user_id_from_category(db, category)
            if not user_id:
                return
            
            # Получаем пользователя
            user = db.get_user(user_id)
            if not user:
                logger.error(f"❌ Пользователь {user_id} не найден")
                return
            
            # Конвертируем в dict если нужно
            if not isinstance(user, dict):
                user = dict(user)
            
            # Находим подключенный телеграм канал
            connections = user.get('platform_connections', {})
            if isinstance(connections, str):
                connections = json.loads(connections)
            
            telegrams = connections.get('telegrams', [])
            
            telegram = None
            platform_index = int(platform_id) if platform_id.isdigit() else 0
            
            if platform_index < len(telegrams):
                telegram = telegrams[platform_index]
            
            if not telegram or telegram.get('status') != 'active':
                logger.error(f"❌ Telegram канал не найден или не активен")
                return
            
            # Генерируем контент через AI
            from ai.text_generator import generate_social_post
            
            # Получаем настройки платформы
            settings = category.get('settings', {})
            if isinstance(settings, str):
                settings = json.loads(settings)
            
            telegram_settings = settings.get('telegram', {})
            
            # Генерируем текст поста
            topic = f"Пост для Telegram канала на тему категории \"{category['name']}\""
            
            result = generate_social_post(
                topic=topic,
                platform='telegram',
                style='engaging',
                include_hashtags=True,
                include_emoji=True
            )
            
            if not result.get('success'):
                logger.error(f"❌ Не удалось сгенерировать текст поста: {result.get('error')}")
                return
            
            post_text = result.get('post', '')
            
            if not post_text:
                logger.error("❌ Не удалось сгенерировать текст поста")
                return
            
            # Публикуем в канал
            channel_id = telegram.get('channel_id')
            if not channel_id:
                logger.error("❌ Не указан ID канала")
                return
            
            try:
                bot.send_message(channel_id, post_text, parse_mode='HTML')
                logger.info(f"✅ Пост опубликован в Telegram канал {telegram.get('channel_title', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки в Telegram: {e}")
            
        except KeyError as e:
            logger.error(f"❌ Ошибка публикации в Telegram: отсутствует ключ {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка публикации в Telegram: {e}")
    
    def _publish_to_pinterest(self, category_id, platform_id):
        """Публикация пина в Pinterest"""
        try:
            from database.database import db
            
            # Получаем категорию
            category = db.get_category(category_id)
            if not category:
                logger.error(f"❌ Категория {category_id} не найдена")
                return
            
            # Конвертируем в dict если нужно
            if not isinstance(category, dict):
                category = dict(category)
            
            # Проверяем наличие user_id
            user_id = get_user_id_from_category(db, category)
            if not user_id:
                return
            
            # Получаем пользователя
            user = db.get_user(user_id)
            if not user:
                logger.error(f"❌ Пользователь {user_id} не найден")
                return
            
            # Конвертируем в dict если нужно
            if not isinstance(user, dict):
                user = dict(user)
            
            # Находим подключенный Pinterest
            connections = user.get('platform_connections', {})
            if isinstance(connections, str):
                import json
                connections = json.loads(connections)
            
            pinterests = connections.get('pinterests', [])
            
            pinterest = None
            platform_index = int(platform_id) if platform_id.isdigit() else 0
            
            if platform_index < len(pinterests):
                pinterest = pinterests[platform_index]
            
            if not pinterest or pinterest.get('status') != 'active':
                logger.error(f"❌ Pinterest не найден или не активен")
                return
            
            logger.info(f"🚧 Публикация в Pinterest пока не реализована полностью")
            logger.info(f"📌 Запланирован пин для {pinterest.get('username', 'Unknown')}")
            
        except KeyError as e:
            logger.error(f"❌ Ошибка публикации в Pinterest: отсутствует ключ {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка публикации в Pinterest: {e}")
    
    def _run_scheduler(self):
        """Основной цикл планировщика"""
        logger.info("🔄 Планировщик публикаций начал работу")
        
        # Запускаем первую проверку через 30 секунд после старта
        time.sleep(30)
        
        last_check_minute = -1
        
        while self.is_running:
            try:
                # Откатываем любую незавершенную транзакцию в начале цикла
                try:
                    from database.database import db
                    db.conn.rollback()
                except:
                    pass
                
                current_time = datetime.now()
                minute = current_time.minute
                
                # Проверяем только раз в минуту
                if minute == last_check_minute:
                    time.sleep(10)
                    continue
                
                last_check_minute = minute
                
                # Получаем список публикаций на текущее время
                publications = self._get_scheduled_publications()
                
                if publications:
                    logger.info(f"⏰ Найдено {len(publications)} запланированных публикаций")
                    
                    for pub in publications:
                        try:
                            logger.info(f"📤 Публикация: {pub['platform_type']} (категория {pub['category_id']})")
                            self._publish_content(
                                pub['category_id'],
                                pub['platform_type'],
                                pub['platform_id']
                            )
                            
                            # Небольшая задержка между публикациями
                            time.sleep(5)
                            
                        except Exception as e:
                            logger.error(f"❌ Ошибка публикации: {e}")
                    
                    # Ждём 2 минуты после публикации
                    time.sleep(120)
                    last_check_minute = -1
                else:
                    # Ждём 30 секунд перед следующей проверкой
                    time.sleep(30)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике публикаций: {e}")
                time.sleep(60)
        
        logger.info("🏁 Планировщик публикаций завершил работу")


# Глобальный экземпляр планировщика
auto_publish_scheduler = AutoPublishScheduler()


def start_auto_publish_scheduler():
    """Запускает планировщик автоматических публикаций"""
    auto_publish_scheduler.start()


def stop_auto_publish_scheduler():
    """Останавливает планировщик автоматических публикаций"""
    auto_publish_scheduler.stop()


print("✅ handlers/auto_publish_scheduler.py загружен")
