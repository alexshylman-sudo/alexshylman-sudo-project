"""
Класс для работы с PostgreSQL базой данных с автоматическим rollback
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from config import DATABASE_URL, WELCOME_BONUS
from functools import wraps
import time


def handle_db_errors(func):
    """Декоратор для автоматической обработки ошибок БД"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Проверяем соединение перед выполнением запроса
                if not self._check_connection_alive():
                    print(f"⚠️ Соединение потеряно, переподключаемся...")
                    self._reconnect()
                
                result = func(self, *args, **kwargs)
                return result
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                # Ошибки подключения - пробуем переподключиться
                error_msg = str(e)
                print(f"⚠️ Ошибка соединения с БД в {func.__name__}: {error_msg}")
                retry_count += 1
                
                if retry_count < max_retries:
                    print(f"🔄 Попытка переподключения {retry_count}/{max_retries}...")
                    try:
                        self._reconnect()
                        print("✅ Переподключение успешно")
                        time.sleep(0.5)  # Небольшая задержка перед повтором
                        continue  # Повторяем попытку
                    except Exception as reconnect_error:
                        print(f"❌ Ошибка переподключения: {reconnect_error}")
                        if retry_count >= max_retries:
                            break
                else:
                    print("❌ Превышено количество попыток переподключения")
                    break
                    
            except Exception as e:
                # Другие ошибки - обрабатываем как обычно
                try:
                    if self.conn and not self.conn.closed:
                        self.conn.rollback()
                except:
                    pass
                    
                print(f"❌ Ошибка БД в {func.__name__}: {e}")
                
                # Возвращаем None, False, [], {} или 0 в зависимости от контекста
                if 'get_' in func.__name__ and 'list' not in func.__name__:
                    return None
                elif 'update' in func.__name__ or 'delete' in func.__name__ or 'create' in func.__name__:
                    return False
                elif '_list' in func.__name__ or 'get_user_bots' in func.__name__ or 'get_bot_categories' in func.__name__:
                    return []
                elif 'stats' in func.__name__:
                    return {}
                elif 'count' in func.__name__:
                    return 0
                else:
                    return None
        
        # Если все попытки неудачны
        print(f"❌ Все попытки выполнения {func.__name__} неудачны")
        if 'get_' in func.__name__ and 'list' not in func.__name__:
            return None
        elif 'update' in func.__name__ or 'delete' in func.__name__ or 'create' in func.__name__:
            return False
        elif '_list' in func.__name__ or 'get_user_bots' in func.__name__ or 'get_bot_categories' in func.__name__:
            return []
        elif 'stats' in func.__name__:
            return {}
        elif 'count' in func.__name__:
            return 0
        else:
            return None
            
    return wrapper


class Database:
    def __init__(self):
        """Инициализация подключения к БД с keepalive и SSL для Neon.tech"""
        try:
            # Параметры подключения для Neon.tech
            # ВАЖНО: НЕ используем statement_timeout в options (Neon pooler не поддерживает)
            self.conn = psycopg2.connect(
                DATABASE_URL,
                # SSL для безопасного подключения (требование Neon)
                sslmode='require',
                # Keepalive параметры для поддержания соединения
                keepalives=1,
                keepalives_idle=30,  # Начинать keepalive после 30 сек простоя
                keepalives_interval=10,  # Интервал между keepalive пакетами
                keepalives_count=5,  # Количество попыток keepalive
                # Таймаут подключения
                connect_timeout=10
            )
            self.conn.set_session(autocommit=False)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            self._last_used = time.time()
            print("✅ База данных подключена (Neon.tech с SSL и keepalive)")
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    def _check_connection_alive(self):
        """Проверка состояния соединения"""
        try:
            # Проверяем что объекты существуют
            if not hasattr(self, 'conn') or self.conn is None:
                return False
            
            if not hasattr(self, 'cursor') or self.cursor is None:
                return False
            
            # Если соединение закрыто
            if self.conn.closed:
                return False
            
            # Если прошло больше 5 минут с последнего использования, проверяем
            if time.time() - self._last_used > 300:
                self.cursor.execute("SELECT 1")
                self.conn.commit()
            
            self._last_used = time.time()
            return True
        except Exception as e:
            print(f"⚠️ Проверка соединения: {e}")
            return False
    
    def _reconnect(self):
        """Переподключение к БД"""
        try:
            # Закрываем старое соединение
            if hasattr(self, 'cursor') and self.cursor:
                try:
                    self.cursor.close()
                except:
                    pass
            if hasattr(self, 'conn') and self.conn:
                try:
                    self.conn.close()
                except:
                    pass
        except:
            pass
        
        # Создаем новое с теми же параметрами
        self.conn = psycopg2.connect(
            DATABASE_URL,
            sslmode='require',
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
            connect_timeout=10
        )
        self.conn.set_session(autocommit=False)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self._last_used = time.time()
        print("✅ Переподключение к БД выполнено")
    
    def check_connection(self):
        """Публичный метод проверки соединения (для совместимости)"""
        return self._check_connection_alive()
    
    def reconnect(self):
        """Публичный метод переподключения (для совместимости)"""
        self._reconnect()
    
    def __del__(self):
        """Закрытие подключения при удалении объекта"""
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════
    # ПОЛЬЗОВАТЕЛИ
    # ═══════════════════════════════════════════════════════════════
    
    @handle_db_errors
    def get_user(self, user_id):
        """Получить пользователя по ID"""
        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ Ошибка БД в get_user: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            return None
    
    @handle_db_errors
    def add_user(self, user_id, username=None, first_name=None):
        """Добавить нового пользователя или обновить существующего"""
        # Проверяем, новый ли это пользователь
        is_new_user = False
        try:
            self.cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            existing = self.cursor.fetchone()
            is_new_user = (existing is None)
        except:
            pass
        
        # Пробуем сначала схему с полем balance (новая)
        try:
            self.cursor.execute(
                """
                INSERT INTO users (id, username, first_name, balance)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    balance = CASE 
                        WHEN users.balance IS NULL OR users.balance = 0 THEN %s
                        ELSE users.balance
                    END
                RETURNING balance
                """,
                (user_id, username, first_name, WELCOME_BONUS, WELCOME_BONUS)
            )
            result = self.cursor.fetchone()
            self.conn.commit()
            
            if result:
                print(f"✅ add_user: пользователь {user_id} - balance: {result.get('balance', 0)}")
            
            # Отправляем приветственное сообщение только новым пользователям
            if is_new_user:
                try:
                    from handlers.auto_notifications import send_welcome_notification
                    send_welcome_notification(user_id, username)
                except Exception as e:
                    print(f"⚠️ Не удалось отправить приветствие пользователю {user_id}: {e}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Не удалось использовать поле balance, пробуем tokens: {e}")
            # Если не получилось, пробуем старую схему с tokens
            try:
                self.cursor.execute(
                    """
                    INSERT INTO users (id, username, first_name, tokens, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        tokens = CASE 
                            WHEN users.tokens IS NULL OR users.tokens = 0 THEN %s
                            ELSE users.tokens
                        END
                    RETURNING tokens
                    """,
                    (user_id, username, first_name, WELCOME_BONUS, datetime.now(), WELCOME_BONUS)
                )
                result = self.cursor.fetchone()
                self.conn.commit()
                
                if result:
                    print(f"✅ add_user: пользователь {user_id} - tokens: {result.get('tokens', 0)}")
                
                # Отправляем приветственное сообщение только новым пользователям
                if is_new_user:
                    try:
                        from handlers.auto_notifications import send_welcome_notification
                        send_welcome_notification(user_id, username)
                    except Exception as e:
                        print(f"⚠️ Не удалось отправить приветствие пользователю {user_id}: {e}")
                
                return True
            except Exception as e2:
                print(f"❌ Ошибка add_user: {e2}")
                return False
    
    @handle_db_errors
    def update_user(self, user_id, updates):
        """
        Обновить данные пользователя
        
        Args:
            user_id: ID пользователя
            updates: dict с полями для обновления, например:
                    {'platform_connections': {...}, 'balance': 1000}
        
        Returns:
            bool: True если успешно
        """
        import json
        
        for field, value in updates.items():
            # Если значение - dict или list, конвертируем в JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            self.cursor.execute(
                f"UPDATE users SET {field} = %s WHERE id = %s",
                (value, user_id)
            )
        
        self.conn.commit()
        return True
    
    def get_user_tokens(self, user_id):
        """Получить баланс токенов пользователя (из поля balance)"""
        try:
            user = self.get_user(user_id)
            
            # Детальное логирование
            if user is None:
                print(f"⚠️ get_user_tokens: пользователь {user_id} не найден")
                return 0
            
            # Проверяем наличие поля balance (новая схема) или tokens (старая схема)
            balance = None
            
            if 'balance' in user:
                balance = user['balance']
                print(f"✅ Используем поле 'balance': {balance}")
            elif 'tokens' in user:
                balance = user['tokens']
                print(f"✅ Используем поле 'tokens': {balance}")
            else:
                print(f"⚠️ get_user_tokens: нет полей 'balance' или 'tokens'")
                print(f"   Доступные поля: {list(user.keys())}")
                return 0
            
            if balance is None:
                print(f"⚠️ get_user_tokens: balance = None для {user_id}, устанавливаем WELCOME_BONUS")
                # Устанавливаем приветственный бонус
                # Пробуем оба поля
                try:
                    self.cursor.execute(
                        "UPDATE users SET balance = %s WHERE id = %s",
                        (WELCOME_BONUS, user_id)
                    )
                    self.conn.commit()
                except:
                    # Если balance не существует, пробуем tokens
                    self.cursor.execute(
                        "UPDATE users SET tokens = %s WHERE id = %s",
                        (WELCOME_BONUS, user_id)
                    )
                    self.conn.commit()
                return WELCOME_BONUS
            
            print(f"✅ get_user_tokens: пользователь {user_id} имеет {balance} токенов")
            return balance
            
        except Exception as e:
            print(f"❌ Ошибка в get_user_tokens для {user_id}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    @handle_db_errors
    def update_tokens(self, user_id, amount):
        """Обновить баланс токенов (может быть отрицательным для списания)"""
        # Пробуем обновить balance (новая схема)
        try:
            self.cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE id = %s",
                (amount, user_id)
            )
            self.conn.commit()
            print(f"✅ update_tokens: обновлен balance на {amount} для {user_id}")
            return True
        except Exception as e:
            # Если не получилось (поля balance нет), пробуем tokens (старая схема)
            print(f"⚠️ Не удалось обновить balance, пробуем tokens: {e}")
            try:
                self.cursor.execute(
                    "UPDATE users SET tokens = tokens + %s WHERE id = %s",
                    (amount, user_id)
                )
                self.conn.commit()
                print(f"✅ update_tokens: обновлен tokens на {amount} для {user_id}")
                return True
            except Exception as e2:
                print(f"❌ Не удалось обновить ни balance, ни tokens: {e2}")
                return False
    
    # ═══════════════════════════════════════════════════════════════
    # БОТЫ (ПРОЕКТЫ)
    # ═══════════════════════════════════════════════════════════════
    
    @handle_db_errors
    def create_bot(self, user_id, name):
        """Создать нового бота"""
        self.cursor.execute(
            """
            INSERT INTO bots (user_id, name, company_data, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, name, json.dumps({}), datetime.now())
        )
        bot_id = self.cursor.fetchone()['id']
        self.conn.commit()
        return bot_id
    
    @handle_db_errors
    def get_bot(self, bot_id):
        """Получить бота по ID"""
        try:
            # Создаём новый курсор с RealDictCursor для возврата dict
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT * FROM bots WHERE id = %s",
                (bot_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"❌ Ошибка БД в get_bot: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            # Пытаемся переподключиться
            try:
                self.reconnect()
            except:
                pass
            return None
    
    @handle_db_errors
    def get_user_bots(self, user_id):
        """Получить всех ботов пользователя"""
        # Создаём новый курсор с RealDictCursor для возврата dict вместо tuple
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM bots WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        result = cursor.fetchall()
        cursor.close()
        return result
    
    @handle_db_errors
    def update_bot(self, bot_id, name=None, company_data=None, connected_platforms=None):
        """Обновить данные бота"""
        if name:
            self.cursor.execute(
                "UPDATE bots SET name = %s WHERE id = %s",
                (name, bot_id)
            )
        if company_data:
            self.cursor.execute(
                "UPDATE bots SET company_data = %s WHERE id = %s",
                (json.dumps(company_data), bot_id)
            )
        if connected_platforms is not None:
            self.cursor.execute(
                "UPDATE bots SET connected_platforms = %s WHERE id = %s",
                (json.dumps(connected_platforms), bot_id)
            )
        self.conn.commit()
        return True
    
    @handle_db_errors
    def delete_bot(self, bot_id):
        """Удалить бота"""
        self.cursor.execute("DELETE FROM bots WHERE id = %s", (bot_id,))
        self.conn.commit()
        return True
    
    # ═══════════════════════════════════════════════════════════════
    # КАТЕГОРИИ
    # ═══════════════════════════════════════════════════════════════
    
    @handle_db_errors
    def create_category(self, bot_id, name, description=''):
        """Создать категорию"""
        self.cursor.execute(
            """
            INSERT INTO categories (bot_id, name, description, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (bot_id, name, description, datetime.now())
        )
        cat_id = self.cursor.fetchone()['id']
        self.conn.commit()
        return cat_id
    
    @handle_db_errors
    def get_category(self, category_id):
        """Получить категорию по ID"""
        try:
            self.cursor.execute(
                "SELECT * FROM categories WHERE id = %s",
                (category_id,)
            )
            category = self.cursor.fetchone()
            
            if category:
                # Парсим JSONB поля если они строки
                jsonb_fields = ['keywords', 'media', 'prices', 'reviews', 'telegram_topics', 'platform_schedulers']
                for field in jsonb_fields:
                    if field in category and isinstance(category[field], str):
                        if field == 'telegram_topics':
                            print(f"📊 DEBUG get_category: telegram_topics до парсинга = {category[field][:200]}")
                        try:
                            category[field] = json.loads(category[field])
                            if field == 'telegram_topics':
                                print(f"📊 DEBUG get_category: telegram_topics после парсинга = {category[field]}")
                        except Exception as parse_error:
                            print(f"❌ Ошибка парсинга {field}: {parse_error}")
                            category[field] = [] if field in ['keywords', 'media', 'reviews', 'telegram_topics'] else {}
            
            return category
        except Exception as e:
            print(f"❌ Ошибка БД в get_category: {e}")
            try:
                self.conn.rollback()
            except:
                pass
            return None
    
    @handle_db_errors
    def get_bot_categories(self, bot_id):
        """Получить все категории бота"""
        self.cursor.execute(
            "SELECT * FROM categories WHERE bot_id = %s ORDER BY created_at",
            (bot_id,)
        )
        return self.cursor.fetchall()
    
    @handle_db_errors
    def update_category(self, category_id, **kwargs):
        """Обновить категорию"""
        allowed_fields = ['name', 'description', 'keywords', 'media', 'prices', 'reviews', 'telegram_topics', 'platform_schedulers']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field in ['keywords', 'media', 'prices', 'reviews', 'telegram_topics', 'platform_schedulers']:
                    value = json.dumps(value)
                
                self.cursor.execute(
                    f"UPDATE categories SET {field} = %s WHERE id = %s",
                    (value, category_id)
                )
        
        self.conn.commit()
        return True
    
    @handle_db_errors
    def delete_category(self, category_id):
        """Удалить категорию"""
        self.cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        self.conn.commit()
        return True
    
    # ═══════════════════════════════════════════════════════════════
    # СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════════
    
    @handle_db_errors
    def get_bot_stats(self):
        """Общая статистика по ботам"""
        self.cursor.execute("SELECT COUNT(*) as users FROM users")
        users = self.cursor.fetchone()['users']
        
        self.cursor.execute("SELECT COUNT(*) as projects FROM bots")
        projects = self.cursor.fetchone()['projects']
        
        return {
            'users': users,
            'projects': projects
        }
    
    @handle_db_errors
    def get_financial_stats(self):
        """Финансовая статистика (заглушка)"""
        return 0
    
    @handle_db_errors
    def get_users_by_status(self):
        """Статистика пользователей по статусу (заглушка)"""
        return {
            'free': 0,
            'test_drive': 0,
            'seo_start': 0,
            'seo_pro': 0,
            'pbn_agent': 0
        }
    
    @handle_db_errors
    def get_last_payments(self, limit=5):
        """Последние платежи (заглушка)"""
        return []
    
    @handle_db_errors
    def get_free_users_count(self):
        """Количество бесплатных пользователей"""
        self.cursor.execute("SELECT COUNT(*) as count FROM users WHERE balance <= 1500")
        result = self.cursor.fetchone()
        return result['count'] if result else 0
    
    @handle_db_errors
    def get_paid_users_count(self):
        """Количество платных пользователей"""
        self.cursor.execute("SELECT COUNT(*) as count FROM users WHERE balance > 1500")
        result = self.cursor.fetchone()
        return result['count'] if result else 0
    
    @handle_db_errors
    def get_referral_stats_admin(self):
        """Статистика рефералов для админа (заглушка)"""
        return {
            'total_activations': 0,
            'total_bonuses': 0,
            'doubled_deposits': 0
        }


# Создаем глобальный экземпляр БД
db = Database()


print("✅ database/database.py загружен")
