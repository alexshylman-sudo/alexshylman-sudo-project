"""
Подключение Website - обработка ввода и сохранение
"""
from telebot import types
from loader import bot, db
from utils import escape_html
from .utils import check_global_platform_uniqueness
from .website_add_start import user_adding_platform
import json


                            
                            del user_adding_platform[user_id]
                            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                            return
                        # ==========================================
                        
                        # Удаляем временный state
                        if '_pinterest_oauth_state' in connections:
                            del connections['_pinterest_oauth_state']
                        
                        # Сохраняем Pinterest
                        if 'pinterests' not in connections:
                            connections['pinterests'] = []
                        
                        # Загружаем доски пользователя
                        from platforms.pinterest.client import PinterestClient
                        pinterest_client = PinterestClient(access_token)
                        boards = pinterest_client.get_boards()
                        
                        # Форматируем доски для хранения
                        boards_list = []
                        for board in boards:
                            boards_list.append({
                                'id': board.get('id'),
                                'name': board.get('name'),
                                'description': board.get('description', '')
                            })
                        
                        connections['pinterests'].append({
                            'access_token': access_token,
                            'username': pinterest_username,
                            'account_type': test_result['user_info'].get('account_type', 'Unknown'),
                            'board': pinterest_username,
                            'boards': boards_list,  # Добавляем список досок
                            'added_at': datetime.now().isoformat(),
                            'status': 'active'
                        })
                        
                        db.cursor.execute("""
                            UPDATE users 
                            SET platform_connections = %s::jsonb
                            WHERE id = %s
                        """, (json.dumps(connections), user_id))
                        db.conn.commit()
                        
                        del user_adding_platform[user_id]
                        
                        boards_count = len(boards_list)
                        text = (
                            "✅ <b>PINTEREST ПОДКЛЮЧЕН!</b>\n"
                            "━━━━━━━━━━━━━━\n\n"
                            f"📌 Аккаунт: <code>@{escape_html(test_result['user_info'].get('username', 'Unknown'))}</code>\n"
                            f"👤 Тип: {test_result['user_info'].get('account_type', 'Personal')}\n"
                            f"📋 Досок загружено: <b>{boards_count}</b>\n"
                            f"🔒 Доступ: OAuth\n\n"
                            "Готово к созданию пинов!"
                        )
                        
                        markup = types.InlineKeyboardMarkup(row_width=1)
                        markup.add(
                            types.InlineKeyboardButton("🔌 Мои подключения", callback_data="settings_api_keys"),
                            types.InlineKeyboardButton("➕ Добавить ещё", callback_data="add_platform_menu")
                        )
                        
                        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                    else:
                        raise Exception(test_result.get('message', 'Connection test failed'))
                
                else:
                    error_data = response.json() if response.status_code != 500 else {}
                    error_msg = error_data.get('message', f'HTTP {response.status_code}')
                    raise Exception(error_msg)
            
            except Exception as e:
                text = (
                    "❌ <b>ОШИБКА ПОДКЛЮЧЕНИЯ</b>\n"
                    "━━━━━━━━━━━━━━\n\n"
                    f"Не удалось получить доступ:\n"
                    f"{escape_html(str(e))}\n\n"
                    "<b>Возможные причины:</b>\n"
                    "• Неверный код авторизации\n"
                    "• Код уже использован (можно использовать только 1 раз)\n"
                    "• Истек срок действия кода (60 секунд)\n\n"
                    "Попробуйте авторизоваться заново."
                )
                
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="add_platform_pinterest"),
                    types.InlineKeyboardButton("🔙 Назад", callback_data="add_platform_menu")
                )
                
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                
                # Очищаем state
                if '_pinterest_oauth_state' in connections:
                    del connections['_pinterest_oauth_state']
                    db.cursor.execute("""
                        UPDATE users 
                        SET platform_connections = %s::jsonb
                        WHERE id = %s
                    """, (json.dumps(connections), user_id))
                    db.conn.commit()
                
                del user_adding_platform[user_id]
    
    # ============ TELEGRAM CHANNEL ============
    elif platform_type == 'telegram':
        if step == 'channel':
            # Шаг 1: Получили ссылку на канал
            channel_input = message.text.strip()
            
            # Обрабатываем разные форматы
            if channel_input.startswith('https://t.me/'):
                channel = channel_input.replace('https://t.me/', '').replace('/', '')
            elif channel_input.startswith('@'):
                channel = channel_input
            elif channel_input.startswith('-100'):
                # ID приватного канала
                channel = channel_input
            else:
                # Просто username без @
                channel = '@' + channel_input
            
            # Сохраняем канал
            platform_data['data']['channel'] = channel
            platform_data['step'] = 'token'
            
            text = (
                "✈️ <b>ПОДКЛЮЧЕНИЕ TELEGRAM</b>\n"
                "━━━━━━━━━━━━━━\n\n"
                f"✅ Канал: <code>{escape_html(channel)}</code>\n\n"
                "<b>Шаг 2 из 2:</b> Токен бота\n\n"
                "Отправьте токен бота от @BotFather.\n\n"
                "<b>Где взять токен:</b>\n"
                "1. Откройте @BotFather в Telegram\n"
                "2. Отправьте /mybots\n"
                "3. Выберите вашего бота\n"
                "4. API Token → скопируйте\n\n"
                "<b>Формат:</b> <code>1234567890:ABCdefGHIjklMNOpqrsTUVwxyz</code>\n\n"
                "💡 <i>Токен будет удален сразу после получения</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
            )
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
        
        elif step == 'token':
            # Шаг 2: Получили токен бота
            token = message.text.strip()
            
            # Удаляем сообщение с токеном для безопасности
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            
            # Проверяем формат токена
            if ':' not in token or len(token) < 40:
                text = (
                    "❌ <b>НЕВЕРНЫЙ ФОРМАТ ТОКЕНА</b>\n\n"
                    "Токен должен быть вида:\n"
                    "<code>1234567890:ABCdefGHIjklMNOpqrsTUVwxyz</code>\n\n"
                    "Попробуйте ещё раз:"
                )
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
            
            # Сохраняем токен
            platform_data['data']['bot_token'] = token
            
            # Тестируем подключение
            import telebot
            
            channel = platform_data['data']['channel']
            
            # Определяем channel_id для API
            if channel.startswith('@'):
                channel_id = channel
            elif channel.startswith('-100'):
                channel_id = channel
            else:
                channel_id = '@' + channel if not channel.startswith('@') else channel
            
            # Создаём экземпляр бота для проверки
            try:
                test_bot = telebot.TeleBot(token)
                
                # 1. Проверяем что токен валидный
                try:
                    bot_info = test_bot.get_me()
                    bot_username = bot_info.username
                    bot_id = bot_info.id
                except Exception as token_error:
                    text = (
                        "❌ <b>НЕВЕРНЫЙ ТОКЕН БОТА</b>\n\n"
                        f"Токен не работает: {str(token_error)}\n\n"
                        "Проверьте правильность токена и попробуйте снова."
                    )
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
                    return
                
                # 2. Проверяем доступ к каналу
                try:
                    chat_info = test_bot.get_chat(channel_id)
                    channel_title = chat_info.title if hasattr(chat_info, 'title') else channel
                    actual_channel_id = chat_info.id
                except Exception as chat_error:
                    text = (
                        "❌ <b>КАНАЛ НЕ НАЙДЕН</b>\n\n"
                        f"Не могу получить информацию о канале: {str(chat_error)}\n\n"
                        "Проверьте:\n"
                        "• Правильность названия канала\n"
                        "• Канал существует и доступен"
                    )
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
                    return
                
                # 3. КРИТИЧНО: Проверяем что бот В КАНАЛЕ и АДМИНИСТРАТОР
                try:
                    bot_member = test_bot.get_chat_member(channel_id, bot_id)
                    bot_status = bot_member.status
                    
                    if bot_status not in ['administrator', 'creator']:
                        text = (
                            "❌ <b>БОТ НЕ ЯВЛЯЕТСЯ АДМИНИСТРАТОРОМ</b>\n\n"
                            f"🤖 Бот: @{bot_username}\n"
                            f"📊 Статус в канале: <code>{bot_status}</code>\n\n"
                            "<b>📋 Что нужно сделать:</b>\n\n"
                            f"1️⃣ Откройте канал {channel}\n"
                            "2️⃣ Нажмите → Администраторы\n"
                            f"3️⃣ Добавьте бота @{bot_username}\n"
                            "4️⃣ Дайте права:\n"
                            "   • Публикация сообщений ✅\n"
                            "   • Управление сообщениями ✅\n\n"
                            "После этого попробуйте подключить снова!"
                        )
                        bot.send_message(message.chat.id, text, parse_mode='HTML')
                        return
                    
                    # Проверяем права на публикацию
                    can_post = getattr(bot_member, 'can_post_messages', True)
                    if not can_post and chat_info.type == 'channel':
                        text = (
                            "⚠️ <b>НЕТ ПРАВ НА ПУБЛИКАЦИЮ</b>\n\n"
                            f"Бот @{bot_username} является администратором,\n"
                            "но не имеет права публиковать сообщения!\n\n"
                            "Дайте боту право на публикацию в настройках администратора."
                        )
                        bot.send_message(message.chat.id, text, parse_mode='HTML')
                        return
                    
                except Exception as member_error:
                    text = (
                        "❌ <b>БОТ НЕ ДОБАВЛЕН В КАНАЛ</b>\n\n"
                        f"🤖 Бот: @{bot_username}\n"
                        f"Ошибка: {str(member_error)}\n\n"
                        "<b>📋 Инструкция:</b>\n\n"
                        f"1️⃣ Откройте канал {channel}\n"
                        "2️⃣ Нажмите → Администраторы\n"
                        f"3️⃣ Добавьте бота @{bot_username}\n"
                        "4️⃣ Дайте права на публикацию\n\n"
                        "После добавления попробуйте ещё раз!"
                    )
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
                    return
                
                # Всё ОК! Формируем результат
                test_result = {
                    'status': 'ok',
                    'bot_info': {
                        'username': bot_username,
                        'id': bot_id
                    },
                    'channel_info': {
                        'title': channel_title,
                        'id': actual_channel_id
                    }
                }
                
            except Exception as e:
                text = (
                    "❌ <b>ОШИБКА ПОДКЛЮЧЕНИЯ</b>\n\n"
                    f"Не удалось подключить Telegram:\n"
                    f"{str(e)}"
                )
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
            
            if test_result['status'] == 'ok':
                # ========== ПРОВЕРКА УНИКАЛЬНОСТИ ==========
                # Используем channel_id для проверки, так как он более надежный идентификатор
                uniqueness = check_global_platform_uniqueness('telegram', channel_id)
                if not uniqueness['is_unique']:
                    # Платформа уже подключена
                    owner_display = f"@{uniqueness['owner_username']}" if uniqueness['owner_username'] else f"ID: {uniqueness['owner_id']}"
                    
                    text = (
                        "❌ <b>ПЛАТФОРМА УЖЕ ПОДКЛЮЧЕНА</b>\n"
                        "━━━━━━━━━━━━━━\n\n"
                        f"✈️ <b>Telegram:</b> {escape_html(channel)}\n\n"
                        "⚠️ Этот Telegram канал уже подключен к другому аккаунту.\n\n"
                        "Каждая платформа может быть подключена только к одному аккаунту в системе.\n\n"
                        "<i>💡 Если это ваш канал, отключите его от другого аккаунта или обратитесь в поддержку.</i>"
                    )
                    
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.add(
                        types.InlineKeyboardButton("🔙 Вернуться к подключениям", callback_data="settings_api_keys")
                    )
                    
                    del user_adding_platform[user_id]
                    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                    return
                # ==========================================
                
                # Успешное подключение - сохраняем
                user = db.get_user(user_id)
                connections = user.get('platform_connections', {})
                
                if not isinstance(connections, dict):
                    connections = {}
                
                if 'telegrams' not in connections:
                    connections['telegrams'] = []
                
                # Сохраняем подключение
                connections['telegrams'].append({
                    'channel': channel.replace('@', ''),
                    'channel_id': test_result['channel_info']['id'],  # Числовой ID!
                    'bot_token': token,
                    'bot_username': test_result['bot_info']['username'],
                    'channel_title': test_result['channel_info']['title'],
                    'status': 'active',
                    'added_at': datetime.now().isoformat()
                })
                
                db.cursor.execute("""
                    UPDATE users 
                    SET platform_connections = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(connections), user_id))
                db.conn.commit()
                
                del user_adding_platform[user_id]
                
                channel_title = test_result['channel_info']['title']
                bot_username = test_result['bot_info']['username']
                
                text = (
                    "✅ <b>TELEGRAM ПОДКЛЮЧЕН!</b>\n"
                    "━━━━━━━━━━━━━━\n\n"
                    f"✈️ Канал: <code>{escape_html(channel)}</code>\n"
                    f"📝 Название: {escape_html(channel_title)}\n"
                    f"🤖 Бот: @{bot_username}\n"
                    f"🟢 Статус: Активен\n\n"
                    "Теперь вы можете использовать этот канал для публикации контента!"
                )
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("🔌 Мои подключения", callback_data="settings_api_keys"),
                    types.InlineKeyboardButton("➕ Добавить ещё", callback_data="add_platform_menu")
                )
                
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
        
        elif step == 'forward_message':
            # Шаг 3 (альтернативный): Получили пересланное сообщение
            if not message.forward_from_chat:
                text = (
                    "❌ <b>ЭТО НЕ ПЕРЕСЛАННОЕ СООБЩЕНИЕ</b>\n\n"
                    "Пожалуйста, перешлите сообщение <b>из канала</b>:\n\n"
                    "1. Откройте канал\n"
                    "2. Нажмите на любое сообщение\n"
                    "3. Переслать → выберите этот чат\n\n"
                    "💡 Не отправляйте обычное сообщение - нужно именно переслать!"
                )
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
            
            # Получаем ID канала из пересланного сообщения
            channel_id = message.forward_from_chat.id
            channel_title = message.forward_from_chat.title
            channel_username = message.forward_from_chat.username
            
            # Тестируем подключение с реальным ID
            from platforms.telegram_channel import TelegramChannelClient
            
            token = platform_data['data'].get('bot_token')
            if not token:
                # Если токен еще не сохранен (не должно быть)
                text = "❌ Ошибка: токен бота не найден. Начните подключение заново."
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("🔄 Начать заново", callback_data="begin_connect_telegram")
                )
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                del user_adding_platform[user_id]
                return
            
            client = TelegramChannelClient(token, str(channel_id))
            test_result = client.test_connection()
            
            if test_result['status'] == 'ok':
                # ========== ПРОВЕРКА УНИКАЛЬНОСТИ ==========
                # Используем channel_id для проверки
                uniqueness = check_global_platform_uniqueness('telegram', str(channel_id))
                if not uniqueness['is_unique']:
                    # Платформа уже подключена
                    owner_display = f"@{uniqueness['owner_username']}" if uniqueness['owner_username'] else f"ID: {uniqueness['owner_id']}"
                    
                    text = (
                        "❌ <b>ПЛАТФОРМА УЖЕ ПОДКЛЮЧЕНА</b>\n"
                        "━━━━━━━━━━━━━━\n\n"
                        f"✈️ <b>Telegram:</b> {escape_html(channel_title)}\n\n"
                        "⚠️ Этот Telegram канал уже подключен к другому аккаунту.\n\n"
                        "Каждая платформа может быть подключена только к одному аккаунту в системе.\n\n"
                        "<i>💡 Если это ваш канал, отключите его от другого аккаунта или обратитесь в поддержку.</i>"
                    )
                    
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.add(
                        types.InlineKeyboardButton("🔙 Вернуться к подключениям", callback_data="settings_api_keys")
                    )
                    
                    del user_adding_platform[user_id]
                    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                    return
                # ==========================================
                
                # Успешное подключение
                user = db.get_user(user_id)
                connections = user.get('platform_connections', {})
                
                if not isinstance(connections, dict):
                    connections = {}
                
                if 'telegrams' not in connections:
                    connections['telegrams'] = []
                
                # Сохраняем подключение с реальным ID
                channel_display = f"@{channel_username}" if channel_username else channel_title
                
                connections['telegrams'].append({
                    'channel': channel_username or str(channel_id),
                    'channel_id': str(channel_id),
                    'bot_token': token,
                    'channel_title': channel_title,
                    'status': 'active',
                    'added_at': datetime.now().isoformat()
                })
                
                db.cursor.execute("""
                    UPDATE users 
                    SET platform_connections = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(connections), user_id))
                db.conn.commit()
                
                del user_adding_platform[user_id]
                
                text = (
                    "✅ <b>TELEGRAM ПОДКЛЮЧЕН!</b>\n"
                    "━━━━━━━━━━━━━━\n\n"
                    f"✈️ Канал: <code>{escape_html(channel_display)}</code>\n"
                    f"📝 Название: {escape_html(channel_title)}\n"
                    f"🆔 ID: <code>{channel_id}</code>\n"
                    f"🤖 Бот: подключен\n"
                    f"🟢 Статус: Активен\n\n"
                    "Теперь вы можете использовать этот канал для публикации контента!"
                )
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("🔌 Мои подключения", callback_data="settings_api_keys"),
                    types.InlineKeyboardButton("➕ Добавить ещё", callback_data="add_platform_menu")
                )
                
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
            else:
                # Ошибка даже с реальным ID
                error_msg = test_result.get('error', 'Неизвестная ошибка')
                
                text = (
                    "❌ <b>ОШИБКА ПОДКЛЮЧЕНИЯ</b>\n"
                    "━━━━━━━━━━━━━━\n\n"
                    f"<b>Ошибка:</b> {escape_html(error_msg)}\n\n"
                    "Скорее всего бот не добавлен в канал как администратор.\n\n"
                    "<b>Что делать:</b>\n"
                    "1. Откройте канал: {escape_html(channel_title)}\n"
                    "2. Администраторы → Добавить администратора\n"
                    "3. Найдите вашего бота и добавьте\n"
                    "4. Дайте права на публикацию сообщений\n"
                    "5. Попробуйте подключить снова"
                )
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="begin_connect_telegram"),
                    types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
                )
                
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
                
                del user_adding_platform[user_id]


# ═══════════════════════════════════════════════════════════════
# INSTAGRAM
# ═══════════════════════════════════════════════════════════════


print("✅ handlers/platform_connections/website_add_handler.py загружен")
