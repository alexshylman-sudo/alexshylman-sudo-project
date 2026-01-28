"""
Меню управления платформой в контексте категории
Позволяет подключать/отключать платформу, делать посты, настраивать планировщик
"""
import os
from telebot import types
from loader import bot, db
from utils import escape_html
import json
from datetime import datetime

# Безопасное логирование
try:
    from debug_logger import debug
except:
    # Fallback - простой print
    class SimpleDebug:
        def header(self, *args): pass
        def info(self, *args): pass
        def success(self, *args): pass
        def warning(self, *args): pass
        def error(self, *args): pass
        def debug(self, *args): pass
        def dict_dump(self, *args, **kwargs): pass
        def footer(self): pass
    debug = SimpleDebug()


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_menu_"))
def handle_platform_menu(call):
    """
    Открытие меню управления платформой для категории
    
    Формат: platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}
    Или: platform_menu_manage_{category_id}_{bot_id}_{platform_type}_{platform_id}
    """
    debug.header("HANDLE_PLATFORM_MENU")
    debug.info("callback_data", call.data)
    
    # Убираем _manage если есть
    callback_data = call.data.replace("platform_menu_manage_", "platform_menu_")
    
    parts = callback_data.split("_")
    
    # Парсим параметры
    category_id = int(parts[2])
    bot_id = int(parts[3])
    platform_type = parts[4]  # website, pinterest, telegram
    platform_id = "_".join(parts[5:])  # ID платформы (может содержать _)
    
    debug.info("category_id", category_id)
    debug.info("bot_id", bot_id)
    debug.info("platform_type", platform_type)
    debug.info("platform_id", platform_id)
    
    user_id = call.from_user.id
    
    # Получаем данные
    category = db.get_category(category_id)
    bot_data = db.get_bot(bot_id)
    
    if not category or not bot_data or bot_data['user_id'] != user_id:
        bot.answer_callback_query(call.id, "❌ Ошибка доступа")
        return
    
    category_name = category['name']
    
    # Получаем информацию о платформе
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {}) if user else {}
    
    # Получаем подключения бота
    bot_connections = bot_data.get('connected_platforms', {})
    if isinstance(bot_connections, str):
        try:
            bot_connections = json.loads(bot_connections)
        except:
            bot_connections = {}
    
    debug.dict_dump("bot_connections", bot_connections)
    
    # Определяем активность подключения
    # Новая структура: {pinterest: [{id: "username"}], telegram: [{id: "channel"}]}
    # Старая структура: {pinterests: ["username"], telegrams: ["channel"]}
    is_connected = False
    
    # 1. Проверяем новую структуру (без 's' в конце)
    if platform_type in bot_connections:
        platform_list = bot_connections[platform_type]
        debug.debug(f"Found '{platform_type}' in bot_connections (new structure)")
        debug.dict_dump(f"platform_list", platform_list)
        
        if isinstance(platform_list, list):
            # Проверяем список объектов
            for idx, item in enumerate(platform_list):
                debug.debug(f"Checking item [{idx}]: {item}")
                if isinstance(item, dict):
                    item_id = item.get('id')
                    debug.info(f"item_id", item_id)
                    debug.info(f"platform_id", platform_id)
                    debug.info(f"Match?", item_id == platform_id)
                    if item_id == platform_id:
                        is_connected = True
                        debug.success("✅ MATCH in new structure (dict)!")
                        break
                elif isinstance(item, str):
                    # Список строк (промежуточный формат)
                    debug.info(f"item (string)", item)
                    debug.info(f"platform_id", platform_id)
                    if item == platform_id:
                        is_connected = True
                        debug.success("✅ MATCH in new structure (string)!")
                        break
    else:
        debug.warning(f"'{platform_type}' NOT in bot_connections")
    
    # 2. Проверяем старую структуру (с 's' в конце)
    if not is_connected:
        old_key = platform_type + 's'
        platforms_list = bot_connections.get(old_key, [])
        debug.debug(f"Checking old structure '{old_key}'")
        debug.dict_dump(f"platforms_list (old)", platforms_list)
        
        if isinstance(platforms_list, list):
            # В старой структуре это список строк
            for item in platforms_list:
                debug.debug(f"Checking old item: {item}")
                if item == platform_id:
                    is_connected = True
                    debug.success("✅ MATCH in old structure!")
                    break
    
    debug.info("FINAL is_connected", is_connected)
    debug.footer()
    
    # Получаем название платформы
    platform_name = ""
    platform_emoji = ""
    
    if platform_type == "website":
        sites = connections.get('websites', [])
        for site in sites:
            if site.get('url', '') == platform_id:
                platform_name = site.get('cms', 'Website')
                platform_emoji = "🌐"
                break
    elif platform_type == "pinterest":
        pinterests = connections.get('pinterests', [])
        for pinterest in pinterests:
            if pinterest.get('board', '') == platform_id:
                platform_name = f"Pinterest: {pinterest.get('board', '')}"
                platform_emoji = "📌"
                break
    elif platform_type == "telegram":
        telegrams = connections.get('telegrams', [])
        for telegram in telegrams:
            if telegram.get('channel', '') == platform_id:
                platform_name = f"Telegram: @{telegram.get('channel', '')}"
                platform_emoji = "✈️"
                break
    elif platform_type == "vk":
        vks = connections.get('vks', [])
        for vk in vks:
            if str(vk.get('user_id', '')) == str(platform_id):
                platform_name = f"VK: {vk.get('group_name', 'ВКонтакте')}"
                platform_emoji = "💬"
                break
    
    # Формируем текст
    status_icon = "🟢" if is_connected else "❌"
    status_text = "ПОДКЛЮЧЕНА" if is_connected else "ОТКЛЮЧЕНА"
    
    text = (
        f"{platform_emoji} <b>{platform_name}</b>\n"
        f"📂 Категория: {escape_html(category_name)}\n"
        "━━━━━━━━━━━━━━\n\n"
        f"<b>Статус:</b> {status_icon} {status_text}\n\n"
    )
    
    if is_connected:
        # Получаем информацию о планировщике
        from handlers.global_scheduler import _get_platform_scheduler
        import datetime
        
        schedule = _get_platform_scheduler(category_id, platform_type, platform_id)
        is_scheduler_enabled = schedule.get('enabled', False)
        
        if is_scheduler_enabled:
            days = schedule.get('days', [])  # ['mon', 'tue', ...]
            posts_per_day = schedule.get('posts_per_day', 1) or 1
            
            # Названия дней
            days_names = {
                'mon': 'Пн', 'tue': 'Вт', 'wed': 'Ср',
                'thu': 'Чт', 'fri': 'Пт', 'sat': 'Сб', 'sun': 'Вс'
            }
            days_text = ", ".join([days_names.get(d, d) for d in days]) if days else "Не выбраны"
            
            # Расчёт постов в неделю
            posts_per_week = len(days) * posts_per_day if days else 0
            
            # Форматируем расписание
            if len(days) == 7:
                schedule_text = f"Каждый день ({days_text}), {posts_per_day} {'пост' if posts_per_day == 1 else 'поста' if posts_per_day < 5 else 'постов'}/день"
            else:
                schedule_text = f"{days_text}, {posts_per_day} {'раз' if posts_per_day == 1 else 'раза' if posts_per_day < 5 else 'раз'}/день"
            
            # Расчёт затрат (40 токенов за пост)
            tokens_per_week = posts_per_week * 40
            tokens_per_month = tokens_per_week * 4
            
            # Следующая публикация (примерно)
            if len(days) == 7:
                # Каждый день - через ~24/posts_per_day часов
                hours_until_next = 24 / posts_per_day if posts_per_day > 0 else 24
                next_time = datetime.datetime.now() + datetime.timedelta(hours=hours_until_next)
            elif len(days) > 0:
                # Через ~7/количество_дней
                days_until_next = 7 / len(days)
                next_time = datetime.datetime.now() + datetime.timedelta(days=days_until_next)
            else:
                next_time = datetime.datetime.now()
            
            next_time_str = next_time.strftime("%d.%m в %H:%M")
            
            text += (
                "📅 <b>ПЛАНИРОВЩИК:</b> 🟢 Активен\n"
                f"   • Расписание: {schedule_text}\n"
                f"   • Постов в неделю: {posts_per_week}\n"
                f"   • Следующая публикация: ~{next_time_str}\n\n"
                "💰 <b>ЗАТРАТЫ НА ПУБЛИКАЦИИ:</b>\n"
                f"   • Неделя: {tokens_per_week} токенов\n"
                f"   • Месяц: {tokens_per_month} токенов\n\n"
            )
        else:
            text += (
                "📅 <b>ПЛАНИРОВЩИК:</b> ⚪ Не настроен\n\n"
            )
        
        text += (
            "✅ Платформа активна для этой категории\n\n"
            "<b>Доступные действия:</b>\n"
            "• Опубликовать пост вручную\n"
            "• Настроить автопостинг\n"
            "• Отключить платформу\n"
        )
    else:
        text += (
            "❌ Платформа не активна\n\n"
            "Подключите платформу, чтобы публиковать контент из этой категории.\n"
        )
    
    # Создаем клавиатуру
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if is_connected:
        # Активная платформа - показываем функции
        # Меняем текст кнопки в зависимости от платформы
        if platform_type.lower() == 'pinterest':
            post_button_text = "📌 Опубликовать пин"
        elif platform_type.lower() == 'telegram':
            post_button_text = "📤 Опубликовать пост"
        else:
            post_button_text = "📤 Опубликовать"
        
        # Опубликовать - большая кнопка на всю ширину
        markup.add(
            types.InlineKeyboardButton(
                post_button_text,
                callback_data=f"platform_ai_post_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            )
        )
        
        # Кнопки настроек для всех платформ
        markup.row(
            types.InlineKeyboardButton(
                "🖼 Изображения",
                callback_data=f"platform_images_menu_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            ),
            types.InlineKeyboardButton(
                "✍️ Текст",
                callback_data=f"platform_text_menu_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            )
        )
        
        markup.add(
            types.InlineKeyboardButton(
                "📷 Мои медиа",
                callback_data=f"platform_media_{platform_type}_{category_id}_{bot_id}"
            )
        )
        
        # Кнопка "Ссылка на сайт" для всех платформ КРОМЕ website
        if platform_type.lower() != 'website':
            markup.add(
                types.InlineKeyboardButton(
                    "🔗 Ссылка на сайт",
                    callback_data=f"platform_link_{platform_type}_{category_id}_{bot_id}_{platform_id}"
                )
            )
        
        # Специальная кнопка "Выбор досок" только для Pinterest
        if platform_type.lower() == 'pinterest':
            markup.add(
                types.InlineKeyboardButton(
                    "📋 Выбор досок",
                    callback_data=f"pinterest_boards_{category_id}_{bot_id}_{platform_id}"
                )
            )
        
        # Специальная кнопка "Настройка топиков" только для Telegram
        if platform_type.lower() == 'telegram':
            markup.add(
                types.InlineKeyboardButton(
                    "📡 Настройка топиков",
                    callback_data=f"telegram_topics_{category_id}_{bot_id}_{platform_id}"
                )
            )
        
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отключить платформу",
                callback_data=f"platform_toggle_{category_id}_{bot_id}_{platform_type}_{platform_id}"
            )
        )
    else:
        # Неактивная платформа - только подключение
        markup.add(
            types.InlineKeyboardButton(
                "✅ Подключить платформу",
                callback_data=f"platform_toggle_{category_id}_{bot_id}_{platform_type}_{platform_id}"
            )
        )
    
    # Кнопка назад
    markup.add(
        types.InlineKeyboardButton(
            "🔙 К категории",
            callback_data=f"open_category_{category_id}"
        )
    )
    
    # Отправляем сообщение
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_toggle_"))
def handle_platform_toggle(call):
    """
    Переключение подключения платформы (вкл/выкл)
    
    Формат: platform_toggle_{category_id}_{bot_id}_{platform_type}_{platform_id}
    """
    parts = call.data.split("_")
    
    category_id = int(parts[2])
    bot_id = int(parts[3])
    platform_type = parts[4]
    platform_id = "_".join(parts[5:])
    
    user_id = call.from_user.id
    
    # Получаем бота
    bot_data = db.get_bot(bot_id)
    
    if not bot_data or bot_data['user_id'] != user_id:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return
    
    # Получаем текущие подключения
    bot_connections = bot_data.get('connected_platforms', {})
    if isinstance(bot_connections, str):
        try:
            bot_connections = json.loads(bot_connections)
        except:
            bot_connections = {}
    
    if not isinstance(bot_connections, dict):
        bot_connections = {}
    
    # Работаем с новой структурой (без 's')
    # {pinterest: [{id: "username"}], telegram: [{id: "channel"}]}
    if platform_type not in bot_connections:
        bot_connections[platform_type] = []
    
    platform_list = bot_connections[platform_type]
    if not isinstance(platform_list, list):
        platform_list = []
    
    # Проверяем активность (ищем в списке объектов)
    is_active = False
    active_index = -1
    
    for i, item in enumerate(platform_list):
        if isinstance(item, dict) and item.get('id') == platform_id:
            is_active = True
            active_index = i
            break
        elif isinstance(item, str) and item == platform_id:
            is_active = True
            active_index = i
            break
    
    # Переключаем
    if is_active:
        # Отключаем
        platform_list.pop(active_index)
        action = "отключена"
        icon = "❌"
    else:
        # Подключаем - добавляем как объект с id
        platform_list.append({'id': platform_id})
        action = "подключена"
        icon = "✅"
    
    bot_connections[platform_type] = platform_list
    
    # Сохраняем в БД
    db.update_bot(bot_id, connected_platforms=bot_connections)
    
    # Возвращаемся в меню платформы
    call.data = f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
    handle_platform_menu(call)
    
    bot.answer_callback_query(call.id, f"{icon} Платформа {action}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_post_"))
def handle_platform_post(call):
    """Ручная публикация поста на платформу"""
    parts = call.data.split("_")
    
    platform_type = parts[2]  # website, pinterest, telegram
    category_id = int(parts[3])
    bot_id = int(parts[4])
    platform_id = "_".join(parts[5:])
    
    # Получаем данные категории
    category = db.get_category(category_id)
    if not category:
        bot.answer_callback_query(call.id, "❌ Категория не найдена")
        return
    
    category_name = category['name']
    description = category.get('description', '')
    
    text = (
        f"✍️ <b>ПУБЛИКАЦИЯ ПОСТА</b>\n"
        f"📂 Категория: {escape_html(category_name)}\n"
        f"📱 Платформа: {platform_type.upper()}\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите способ создания поста:\n"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Если есть описание - можно использовать его
    if description:
        markup.add(
            types.InlineKeyboardButton(
                "📝 Использовать готовое описание",
                callback_data=f"post_use_desc_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            )
        )
    
    markup.add(
        types.InlineKeyboardButton(
            "✍️ Написать текст вручную",
            callback_data=f"post_manual_{platform_type}_{category_id}_{bot_id}_{platform_id}"
        )
    )
    
    markup.add(
        types.InlineKeyboardButton(
            "🤖 Сгенерировать с AI",
            callback_data=f"platform_ai_post_{platform_type}_{category_id}_{bot_id}_{platform_id}"
        )
    )
    
    markup.add(
        types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data=f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
        )
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_ai_post_"))
def handle_platform_ai_post(call):
    """Генерация и публикация поста с помощью AI"""
    parts = call.data.split("_")
    
    platform_type = parts[3]
    category_id = int(parts[4])
    bot_id = int(parts[5])
    platform_id = "_".join(parts[6:])
    
    category = db.get_category(category_id)
    if not category:
        bot.answer_callback_query(call.id, "❌ Категория не найдена")
        return
    
    category_name = category['name']
    user_id = call.from_user.id
    
    # Словарь названий публикаций для разных платформ
    platform_names = {
        'pinterest': {
            'title': 'ПИНА',
            'noun': 'пин',
            'action': 'опубликует пин'
        },
        'telegram': {
            'title': 'ПОСТА',
            'noun': 'пост',
            'action': 'опубликует пост'
        },
        'instagram': {
            'title': 'ПОСТА',
            'noun': 'пост',
            'action': 'опубликует пост'
        },
        'vk': {
            'title': 'ПОСТА',
            'noun': 'пост',
            'action': 'опубликует пост'
        },
        'website': {
            'title': 'СТАТЬИ',
            'noun': 'статью',
            'action': 'создаст статью'
        }
    }
    
    # Получаем название для текущей платформы
    platform_info = platform_names.get(platform_type.lower(), {
        'title': 'КОНТЕНТА',
        'noun': 'контент',
        'action': 'создаст контент'
    })
    
    # Проверяем баланс
    tokens = db.get_user_tokens(user_id)
    
    # Для Pinterest: изображение (30) + текст (10) = 40 токенов
    if platform_type.lower() == 'pinterest':
        cost = 40
        cost_breakdown = (
            "💰 <b>Стоимость публикации:</b>\n"
            "• Генерация изображения: 30 токенов\n"
            "• Генерация текста: 10 токенов\n"
            "• <b>Итого: 40 токенов</b>\n\n"
        )
    elif platform_type.lower() == 'telegram':
        cost = 40
        cost_breakdown = (
            "💰 <b>Стоимость публикации:</b>\n"
            "• Генерация текста (до 100 слов): 10 токенов\n"
            "• Генерация изображения: 30 токенов\n"
            "• <b>Итого: 40 токенов</b>\n\n"
        )
    elif platform_type.lower() == 'website':
        # Для Website рассчитываем по настройкам
        from handlers.website.image_advanced_settings import get_user_advanced_params
        params = get_user_advanced_params(user_id, category_id)
        
        # Расчёт стоимости: текст (10 токенов за 100 слов) + изображения (30 токенов за штуку)
        text_cost = (params['words'] // 100) * 10
        if text_cost == 0:
            text_cost = 10
        image_cost = (params['images'] + 1) * 30  # +1 за обложку
        cost = text_cost + image_cost
        
        cost_breakdown = (
            f"💰 <b>Стоимость публикации:</b>\n"
            f"• Генерация изображения: {image_cost} токенов ({params['images']} + обложка)\n"
            f"• Генерация текста: {text_cost} токенов (~{params['words']} слов)\n"
            f"• <b>Итого: {cost} токенов</b>\n\n"
        )
    else:
        # Для VK, Pinterest, Telegram: текст (20) + изображение (30) = 50 токенов
        cost = 50
        cost_breakdown = (
            "💰 <b>Стоимость:</b> 50 токенов\n"
            "• Генерация текста: 20 токенов\n"
            "• Генерация изображения: 30 токенов\n\n"
        )
    
    text = (
        f"📌 <b>ПУБЛИКАЦИЯ {platform_info['title'].upper()}</b>\n"
        f"📂 Категория: {escape_html(category_name)}\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{cost_breakdown}"
        f"💳 Ваш баланс: <b>{tokens:,}</b> токенов\n\n"
    )
    
    if tokens < cost:
        text += f"❌ Недостаточно токенов!\nНужно: {cost}, у вас: {tokens}"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
            )
        )
    else:
        if platform_type.lower() == 'telegram':
            text += (
                f"AI создаст и {platform_info['action']}:\n"
                "• Уникальное изображение\n"
                "• Текст до 100 слов (без хештегов)\n"
                "• Автоматическая публикация в канал\n\n"
                "❗️ Пост будет опубликован сразу\n"
                "Подтвердить публикацию?"
            )
        else:
            text += (
                f"AI создаст и {platform_info['action']}:\n"
                "• Уникальное изображение\n"
                "• Описание с ключевыми словами\n"
                "• Автоматическая публикация\n\n"
                "Подтвердить публикацию?"
            )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Да, опубликовать",
                callback_data=f"ai_post_confirm_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
            )
        )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("ai_post_confirm_"))
def handle_ai_post_confirm(call):
    """Подтверждение генерации AI поста"""
    parts = call.data.split("_")
    
    platform_type = parts[3]
    category_id = int(parts[4])
    bot_id = int(parts[5])
    platform_id = "_".join(parts[6:])
    
    user_id = call.from_user.id
    
    # Словарь названий для разных платформ
    platform_names = {
        'pinterest': {
            'title': 'ПИНА',
            'noun_gen': 'пина',  # родительный падеж
            'platform_name': 'Pinterest'
        },
        'telegram': {
            'title': 'ПОСТА',
            'noun_gen': 'поста',
            'platform_name': 'Telegram'
        },
        'instagram': {
            'title': 'ПОСТА',
            'noun_gen': 'поста',
            'platform_name': 'Instagram'
        },
        'vk': {
            'title': 'ПОСТА',
            'noun_gen': 'поста',
            'platform_name': 'VK'
        },
        'website': {
            'title': 'СТАТЬИ',
            'noun_gen': 'статьи',
            'platform_name': 'сайт'
        }
    }
    
    # Получаем название для текущей платформы
    platform_info = platform_names.get(platform_type.lower(), {
        'title': 'КОНТЕНТА',
        'noun_gen': 'контента',
        'platform_name': 'платформу'
    })
    
    # Списываем токены сразу
    if platform_type.lower() == 'pinterest':
        cost = 40  # изображение 30 + текст 10
    elif platform_type.lower() == 'telegram':
        cost = 40  # текст 10 + изображение 30
    elif platform_type.lower() == 'vk':
        cost = 50  # текст 20 + изображение 30
    else:
        cost = 20
    
    # Проверяем и списываем
    tokens = db.get_user_tokens(user_id)
    if tokens < cost:
        bot.answer_callback_query(call.id, f"❌ Недостаточно токенов! Нужно: {cost}", show_alert=True)
        return
    
    if not db.update_tokens(user_id, -cost):
        bot.answer_callback_query(call.id, "❌ Ошибка списания токенов", show_alert=True)
        return
    
    new_balance = db.get_user_tokens(user_id)
    
    # ═══════════════════════════════════════════════════════════════
    # WEBSITE - ПЕРЕНАПРАВЛЕНИЕ НА СПЕЦИАЛЬНЫЙ ОБРАБОТЧИК
    # ═══════════════════════════════════════════════════════════════
    if platform_type.lower() == 'website':
        # Возвращаем токены - они спишутся в обработчике website
        db.update_tokens(user_id, cost)
        
        # Перенаправляем на правильный обработчик
        call.data = f"platform_ai_post_website_{category_id}_{bot_id}_{platform_id}"
        
        # Импортируем и вызываем обработчик website
        from handlers.website.article_generation import handle_platform_ai_post_website
        handle_platform_ai_post_website(call)
        return
    
    # ═══════════════════════════════════════════════════════════════
    # TELEGRAM - СРАЗУ ГЕНЕРАЦИЯ И ПУБЛИКАЦИЯ С ИЗОБРАЖЕНИЕМ
    # ═══════════════════════════════════════════════════════════════
    if platform_type.lower() == 'telegram':
        # Получаем категорию
        category = db.get_category(category_id)
        if not category:
            db.update_tokens(user_id, cost)
            bot.answer_callback_query(call.id, "❌ Категория не найдена")
            return
        
        category_name = category['name']
        description = category.get('description', '')
        telegram_topics = category.get('telegram_topics', [])
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: если telegram_topics не список - сбрасываем!
        if not isinstance(telegram_topics, list):
            print(f"⚠️ WARNING в публикации: telegram_topics не список! Тип: {type(telegram_topics)}")
            print(f"⚠️ Значение: {telegram_topics}")
            telegram_topics = []
        
        # Если есть топики - спрашиваем куда публиковать
        if telegram_topics:
            # Отладка
            print(f"📊 DEBUG: telegram_topics = {telegram_topics}")
            print(f"📊 DEBUG: Количество топиков: {len(telegram_topics)}")
            
            text = (
                f"📡 <b>ВЫБОР ТОПИКА</b>\n"
                f"📂 Категория: {escape_html(category_name)}\n"
                "━━━━━━━━━━━━━━\n\n"
                "В какой топик опубликовать пост?\n\n"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for i, topic in enumerate(telegram_topics):
                topic_id = topic.get('topic_id')
                topic_name = topic.get('topic_name', 'Без названия')
                
                print(f"📊 DEBUG: Топик {i+1}: ID={topic_id}, Name={topic_name}")
                
                markup.add(
                    types.InlineKeyboardButton(
                        f"📌 {topic_name}",
                        callback_data=f"telegram_publish_topic_{category_id}_{bot_id}_{platform_id}_{topic_id}"
                    )
                )
            
            markup.add(
                types.InlineKeyboardButton(
                    "📤 В основной чат (без топика)",
                    callback_data=f"telegram_publish_topic_{category_id}_{bot_id}_{platform_id}_0"
                )
            )
            
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена (вернуть токены)",
                    callback_data=f"telegram_cancel_publish_{category_id}_{bot_id}_{platform_id}_{cost}"
                )
            )
            
            try:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            except:
                bot.send_message(
                    call.message.chat.id,
                    text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            bot.answer_callback_query(call.id)
            return
        
        # Если топиков нет - публикуем в основной чат
        else:
            bot.answer_callback_query(call.id, "🤖 Генерирую и публикую...")
            _telegram_publish_post(
                call, 
                category_id, 
                bot_id, 
                platform_id, 
                topic_id=0, 
                cost=cost, 
                new_balance=new_balance,
                platform_info=platform_info
            )
            return
    
    # ═══════════════════════════════════════════════════════════════
    # PINTEREST - СТАРАЯ ЛОГИКА
    # ═══════════════════════════════════════════════════════════════
    # Для Pinterest - сразу генерация и публикация
    if platform_type.lower() == 'pinterest':
        bot.answer_callback_query(call.id, "🤖 Генерирую и публикую...")
        
        # Инициализируем прогресс-бар с GIF
        from utils.generation_progress import show_generation_progress
        progress = show_generation_progress(call.message.chat.id, "pinterest", total_steps=3)
        progress.start("Подготовка к генерации...")
        
        # Получаем данные категории
        category = db.get_category(category_id)
        if not category:
            db.update_tokens(user_id, cost)  # Возвращаем токены
            bot.send_message(call.message.chat.id, "❌ Ошибка: категория не найдена")
            return
        
        category_name = category['name']
        description = category.get('description', '')
        keywords = category.get('keywords', [])
        
        # Получаем настройки для платформы
        # Получаем настройки изображений из новой системы
        from handlers.platform_settings import get_platform_settings, build_image_prompt
        
        platform_image_settings = get_platform_settings(category, platform_type)
        
        # Обновляем прогресс - шаг 1: Генерация изображения
        progress.update(1, "🖼 Генерирую изображение...", f"📝 Категория: {category_name}")
        
        # Генерируем изображение (30 токенов уже списаны)
        try:
            from ai.image_generator import generate_image
            import tempfile
            import os
            import random
            
            # ЧИТАЕМ НАСТРОЙКУ "ТЕКСТ НА ИЗОБРАЖЕНИИ"
            settings = category.get('settings', {})
            if isinstance(settings, str):
                import json
                settings = json.loads(settings)
            
            text_on_image_setting = settings.get(f'{platform_type}_text_on_image', 'random')
            
            # Варианты текста на изображении
            TEXT_ON_IMAGE_OPTIONS = {
                'with_text': {
                    'prompt': 'text overlay, elegant typography, readable text on image'
                },
                'without_text': {
                    'prompt': 'no text, clean image, no typography, no letters, no words'
                },
                'random': None  # Случайно
            }
            
            # Определяем что использовать
            if text_on_image_setting == 'random':
                text_on_image_setting = random.choice(['with_text', 'without_text'])
            
            text_overlay_prompt = TEXT_ON_IMAGE_OPTIONS.get(text_on_image_setting, {}).get('prompt', '')
            
            # 20% шанс коллажа
            use_collage = random.random() < 0.2
            
            if use_collage:
                base_prompt = f"{category_name}, collection of photos, multiple panels"
            else:
                base_prompt = f"{category_name}, single unified image"
            
            # 10% шанс использовать описание БОТА (для разнообразия)
            # НЕ для website - там свои правила для статей
            use_bot_description = (platform_type != 'website') and (random.random() < 0.1)
            
            if use_bot_description:
                # Получаем описание бота
                bot_info = db.get_bot(bot_id)
                bot_description = bot_info.get('description', '') if bot_info else ''
                
                if bot_description and len(bot_description) > 20:
                    # Берём 1-2 фразы из описания бота
                    bot_phrases = [s.strip() for s in bot_description.split('.') if s.strip() and len(s.strip()) > 10]
                    
                    if bot_phrases:
                        # Берём только 1 фразу (было 1-2)
                        selected_phrases = [random.choice(bot_phrases)]
                        phrases_text = selected_phrases[0]
                        base_prompt = f"{base_prompt}. {phrases_text}"
                        print(f"🎲 Используем описание БОТА: {phrases_text[:80]}...")
                    else:
                        use_bot_description = False
                else:
                    use_bot_description = False
            
            # Если НЕ используем описание бота - берём из описания категории
            if not use_bot_description and description:
                desc_phrases = [s.strip() for s in description.split('.') if s.strip() and len(s.strip()) > 10]
                
                if desc_phrases:
                    # Берём только 1 фразу (было 1-2)
                    selected_phrases = [random.choice(desc_phrases)]
                    phrases_text = selected_phrases[0]
                    base_prompt = f"{base_prompt}. {phrases_text}"
                    
                    # Добавляем настройку текста
                    if text_overlay_prompt:
                        base_prompt += f". {text_overlay_prompt}"
                    
                    # Примечание: конкретный текст не добавляем для избежания переполнения промпта
                else:
                    if text_overlay_prompt:
                        base_prompt += f". {text_overlay_prompt}"
            else:
                if text_overlay_prompt:
                    base_prompt += f". {text_overlay_prompt}"
            
            print(f"🎨 Базовый промпт для {platform_type}: {base_prompt[:100]}...")
            
            # build_image_prompt ДОБАВИТ: стили, тональность, камеры, ракурсы, качество из настроек
            full_prompt, image_format = build_image_prompt(base_prompt, platform_image_settings)
            
            print(f"✅ Полный промпт: {full_prompt[:150]}...")
            print(f"📐 Формат: {image_format}")
            
            # Генерируем изображение
            image_result = generate_image(full_prompt, aspect_ratio=image_format)
            
            if not image_result.get('success'):
                raise Exception(image_result.get('error', 'Ошибка генерации изображения'))
            
            # Получаем байты изображения
            image_bytes = image_result.get('image_bytes')
            if not image_bytes:
                raise Exception('Изображение не содержит данных')
            
            # Сохраняем во временный файл
            fd, image_path = tempfile.mkstemp(suffix='.jpg', prefix='pinterest_pin_')
            with os.fdopen(fd, 'wb') as f:
                f.write(image_bytes)
            
        except Exception as e:
            print(f"❌ Ошибка генерации изображения: {e}")
            progress.finish()  # Удаляем прогресс-бар
            db.update_tokens(user_id, cost)  # Возвращаем токены
            bot.send_message(call.message.chat.id,
                f"❌ Ошибка генерации изображения: {e}\n\n"
                f"Токены возвращены на ваш счёт."
            )
            return
        
        # Генерируем описание (10 токенов уже списаны)
        try:
            from ai.text_generator import generate_social_post
            import json
            
            topic = f"{category_name}"
            if description:
                topic += f". {description[:200]}"
            
            # Получаем настройки текстового стиля
            settings = category.get('settings', {})
            if isinstance(settings, str):
                settings = json.loads(settings)
            
            text_style_key = f'{platform_type}_text_style'
            text_style = settings.get(text_style_key, 'conversational')
            
            # Маппинг стилей на параметры генератора
            style_map = {
                'sales': 'engaging',
                'motivational': 'inspiring',
                'friendly': 'engaging',
                'conversational': 'engaging',
                'creative': 'engaging',
                'professional': 'professional',
                'informative': 'engaging'
            }
            
            generator_style = style_map.get(text_style, 'engaging')
            
            # Обновляем прогресс - шаг 2: Генерация описания
            progress.update(2, "✍️ Генерирую описание...", f"📝 Стиль: {text_style}")
            
            # Генерируем описание для Pinterest (короткое, без спецсимволов, с хэштегами)
            from ai.text_generator import generate_pinterest_description
            
            result = generate_pinterest_description(
                topic=topic,
                max_length=500,  # Pinterest лимит - 500 символов
                include_hashtags=True
            )
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Ошибка генерации текста'))
            
            post_text = result['description']
            
        except Exception as e:
            print(f"❌ Ошибка генерации текста: {e}")
            progress.finish()  # Удаляем прогресс-бар
            db.update_tokens(user_id, cost)  # Возвращаем токены
            bot.send_message(call.message.chat.id,
                f"❌ Ошибка генерации описания: {e}\n\n"
                f"Токены возвращены на ваш счёт."
            )
            return
        
        # Обновляем прогресс - шаг 3: Публикация
        progress.update(3, "📤 Публикую в Pinterest...", f"📌 Описание готово!")
        
        # Публикуем в Pinterest
        try:
            from platforms.pinterest.client import PinterestClient
            
            # Получаем данные пользователя (не бота!)
            user_data = db.get_user(user_id)
            if not user_data:
                raise Exception('Пользователь не найден')
            
            # Pinterest хранится в platform_connections
            connections = user_data.get('platform_connections', {})
            if isinstance(connections, str):
                import json
                connections = json.loads(connections)
            
            pinterests = connections.get('pinterests', [])
            
            if not pinterests:
                raise Exception('Pinterest не подключен. Подключите Pinterest в разделе "⚙️ Настройки → 🔌 Подключения"')
            
            # Берем первый подключенный Pinterest
            pinterest_data = pinterests[0]
            access_token = pinterest_data.get('access_token')
            
            if not access_token:
                raise Exception('Токен Pinterest не найден')
            
            # Инициализируем клиент с токеном
            client = PinterestClient(access_token)
            
            # Получаем список досок
            boards = client.get_boards()
            if not boards:
                raise Exception('Нет доступных досок. Создайте доску в Pinterest.')
            
            # Получаем настройки выбранных досок
            settings = category.get('settings', {})
            if isinstance(settings, str):
                settings = json.loads(settings)
            
            selected_boards = settings.get('pinterest_boards', [])
            
            # Выбираем доску
            if selected_boards:
                # Ищем первую выбранную доску из списка
                board_id = None
                for board in boards:
                    if board.get('id') in selected_boards:
                        board_id = board.get('id')
                        break
                
                if not board_id:
                    # Если выбранные доски не найдены, используем первую доступную
                    board_id = boards[0].get('id')
            else:
                # Если доски не выбраны, используем первую доступную
                board_id = boards[0].get('id')
            
            if not board_id:
                raise Exception('Не удалось получить ID доски')
            
            # Конвертируем изображение в base64
            import base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Получаем ссылку на сайт из настроек
            pinterest_link = settings.get('pinterest_link', '')
            
            # Публикуем пин
            # Pinterest лимит: ~500 символов, оставляем место для хештегов
            description_text = post_text[:400] if len(post_text) > 400 else post_text
            
            pin_result = client.create_pin(
                board_id=board_id,
                title=category_name[:100],
                description=description_text,
                image_base64=image_base64,
                link=pinterest_link if pinterest_link else None
            )
            
            if pin_result.get('status') != 'ok':
                raise Exception(pin_result.get('message', 'Ошибка публикации'))
            
            pin_url = pin_result.get('url', '')
            
            # Удаляем временный файл
            try:
                import os
                os.unlink(image_path)
            except:
                pass
            
            # Удаляем прогресс-бар
            progress.finish()
            
            # Успешная публикация
            text = (
                f"✅ <b>{platform_info['title'].upper()} ОПУБЛИКОВАН{'А' if platform_info['title'] == 'СТАТЬИ' else ''}!</b>\n"
                "━━━━━━━━━━━━━━\n\n"
                f"📂 Категория: {escape_html(category_name)}\n"
                f"💳 Списано: {cost} токенов\n"
                f"💰 Баланс: {new_balance:,} токенов\n\n"
            )
            
            if pin_url:
                text += f"📌 {platform_info['title'].capitalize()} успешно опубликован{'а' if platform_info['title'] == 'СТАТЬИ' else ''} в {platform_info['platform_name']}!"
            else:
                text += f"📌 {platform_info['title'].capitalize()} успешно опубликован{'а' if platform_info['title'] == 'СТАТЬИ' else ''} в {platform_info['platform_name']}!"
            
            markup = types.InlineKeyboardMarkup()
            
            # Кнопка "Открыть" если есть URL
            if pin_url:
                open_btn_text = {
                    'pinterest': '🔗 Открыть пин',
                    'telegram': '🔗 Открыть пост', 
                    'instagram': '🔗 Открыть пост',
                    'vk': '🔗 Открыть пост',
                    'website': '🔗 Открыть статью'
                }.get(platform_type.lower(), '🔗 Открыть')
                
                markup.add(
                    types.InlineKeyboardButton(
                        open_btn_text,
                        url=pin_url
                    )
                )
            
            # Кнопка "Генерировать ещё"
            markup.add(
                types.InlineKeyboardButton(
                    "🎨 Генерировать ещё",
                    callback_data=f"platform_ai_post_{platform_type}_{category_id}_{bot_id}_{platform_id}"
                )
            )
            
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
                )
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            # Удаляем временный файл при ошибке
            try:
                import os
                os.unlink(image_path)
            except:
                pass
            
            # Удаляем прогресс-бар
            progress.finish()
            
            print(f"❌ Ошибка публикации в Pinterest: {e}")
            db.update_tokens(user_id, cost)  # Возвращаем токены
            bot.send_message(call.message.chat.id,
                f"❌ Ошибка публикации в Pinterest: {e}\n\n"
                f"Токены возвращены на ваш счёт."
            )
        
        return
    
    # VK - прямая публикация (как Pinterest)
    if platform_type.lower() == 'vk':
        bot.answer_callback_query(call.id, "🤖 Генерирую и публикую в VK...")
        
        # Вызываем функцию прямой публикации
        from handlers.platform_category.vk_direct_publish import publish_vk_directly
        publish_vk_directly(call, user_id, bot_id, platform_id, category_id, cost)
        return
    
    # Для других платформ - старая логика с показом поста
    bot.answer_callback_query(call.id, "🤖 Генерирую пост...")
    
    try:
        bot.edit_message_text(
            f"🤖 <b>Генерация {platform_info['noun_gen']}...</b>\n\n"
            f"Claude AI создаёт уникальный {platform_info['noun_gen'].lower()} для вас.\n"
            "Это займёт несколько секунд ⏳",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
    except:
        pass
    
    # Получаем данные категории
    category = db.get_category(category_id)
    if not category:
        db.update_tokens(user_id, cost)  # Возвращаем токены
        bot.send_message(call.message.chat.id, "❌ Ошибка: категория не найдена")
        return
    
    category_name = category['name']
    description = category.get('description', '')
    keywords = category.get('keywords', [])
    
    # Генерируем пост через Claude
    from ai.text_generator import generate_social_post
    
    # Формируем тему
    topic = f"{category_name}"
    if description:
        topic += f". {description[:200]}"
    
    # Определяем платформу для генератора
    platform_map = {
        'website': 'facebook',
        'pinterest': 'instagram',
        'telegram': 'telegram'
    }
    
    ai_platform = platform_map.get(platform_type, 'instagram')
    
    result = generate_social_post(
        topic=topic,
        platform=ai_platform,
        style='engaging',
        include_hashtags=True,
        include_emoji=True
    )
    
    if result.get('success'):
        post_text = result['post']
        
        # Показываем результат
        text = (
            f"✅ <b>{platform_info['title'].upper()} СГЕНЕРИРОВАН{'А' if platform_info['title'] == 'СТАТЬИ' else ''}!</b>\n"
            f"📱 Платформа: {platform_info['platform_name']}\n"
            "━━━━━━━━━━━━━━\n\n"
            f"{post_text}\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📊 Символов: {len(post_text)}\n"
            f"💳 Списано: {cost} токенов\n"
            f"💰 Баланс: {new_balance:,} токенов\n\n"
            "Опубликовать этот пост?"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "📤 Опубликовать",
                callback_data=f"publish_post_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "🔄 Сгенерировать заново",
                callback_data=f"ai_post_confirm_{platform_type}_{category_id}_{bot_id}_{platform_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
            )
        )
        
    else:
        db.update_tokens(user_id, cost)  # Возвращаем токены
        text = (
            f"❌ <b>ОШИБКА ГЕНЕРАЦИИ</b>\n\n"
            f"Причина: {result.get('error', 'Неизвестная ошибка')}\n\n"
            "Токены возвращены. Попробуйте еще раз."
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_menu_{category_id}_{bot_id}_{platform_type}_{platform_id}"
            )
        )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML'
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("publish_post_"))
def handle_publish_post(call):
    """
    Обработчик публикации поста на платформу
    
    Формат: publish_post_{platform_type}_{category_id}_{bot_id}_{platform_id}
    """
    user_id = call.from_user.id
    parts = call.data.split("_")
    
    # Парсим параметры
    platform_type = parts[2]  # vk, pinterest, telegram, website
    category_id = int(parts[3])
    bot_id = int(parts[4])
    platform_id = "_".join(parts[5:])
    
    # Получаем данные бота
    bot_data = db.get_bot(bot_id)
    if not bot_data or bot_data['user_id'] != user_id:
        bot.answer_callback_query(call.id, "❌ Нет доступа")
        return
    
    # Получаем сгенерированный текст из сообщения
    message_text = call.message.text or call.message.caption or ""
    
    # Извлекаем текст поста (между разделителями)
    post_text = ""
    if "━━━━━━━━━━━━━━" in message_text:
        lines = message_text.split("\n")
        in_post = False
        post_lines = []
        
        for line in lines:
            if "━━━━━━━━━━━━━━" in line:
                if not in_post:
                    in_post = True
                    continue
                else:
                    break
            if in_post and line.strip():
                post_lines.append(line)
        
        post_text = "\n".join(post_lines).strip()
    
    if not post_text:
        bot.answer_callback_query(call.id, "❌ Текст поста не найден")
        return
    
    # Показываем статус
    bot.edit_message_text(
        "🔄 <b>ПУБЛИКАЦИЯ НАЧАТА</b>\n\n"
        f"Платформа: {platform_type.upper()}\n"
        f"Категория ID: {category_id}\n\n"
        "⏳ Подготовка к публикации...",
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML'
    )
    
    # В зависимости от платформы вызываем нужный метод
    if platform_type == "vk":
        publish_to_vk(call, user_id, bot_id, platform_id, category_id, post_text)
    elif platform_type == "pinterest":
        publish_to_pinterest(call, user_id, bot_id, platform_id, category_id, post_text)
    elif platform_type == "telegram":
        publish_to_telegram(call, user_id, bot_id, platform_id, category_id, post_text)
    elif platform_type == "website":
        publish_to_website(call, user_id, bot_id, platform_id, category_id, post_text)
    else:
        bot.edit_message_text(
            f"❌ <b>ОШИБКА</b>\n\n"
            f"Платформа '{platform_type}' не поддерживается",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )


def publish_to_vk(call, user_id, bot_id, platform_id, category_id, post_text):
    """Публикация в VK с генерацией изображения"""
    from ai.image_generator import generate_image
    from handlers.platform_settings.utils import build_image_prompt
    import tempfile
    import os
    import random
    import requests
    
    try:
        # Этап 1: Генерация изображения
        bot.edit_message_text(
            "🎨 <b>ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ</b>\n\n"
            f"Текст поста: {len(post_text)} символов\n"
            "⏳ Создаём AI-изображение...",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        
        # Получаем категорию для построения промпта
        category = db.get_category(category_id)
        category_name = category.get('name', 'контент')
        description = category.get('description', '')
        
        # Получаем настройки изображения категории
        settings = category.get('settings', {})
        if isinstance(settings, str):
            import json
            settings = json.loads(settings)
        
        platform_image_settings = settings.get('vk_image_settings', {})
        
        # Если настроек нет - используем дефолтные для VK
        if not platform_image_settings or 'formats' not in platform_image_settings:
            platform_image_settings = {
                'formats': ['1:1', '4:5'],  # Квадрат и вертикаль
                'styles': [],
                'tones': [],
                'cameras': [],
                'angles': [],
                'qualities': ['high_quality']
            }
        
        # 20% шанс коллажа
        use_collage = random.random() < 0.2
        
        if use_collage:
            base_prompt = f"{category_name}, collection of photos, multiple panels"
        else:
            base_prompt = f"{category_name}, single unified image"
        
        # Добавляем фразу из описания категории
        if description:
            desc_phrases = [s.strip() for s in description.split('.') if s.strip() and len(s.strip()) > 10]
            if desc_phrases:
                selected_phrase = random.choice(desc_phrases)
                base_prompt = f"{base_prompt}. {selected_phrase}"
        
        print(f"🎨 Базовый промпт для VK: {base_prompt[:100]}...")
        
        # build_image_prompt добавит: стили, тональность, камеры, ракурсы, качество
        full_prompt, image_format = build_image_prompt(base_prompt, platform_image_settings)
        
        print(f"✅ Полный промпт: {full_prompt[:150]}...")
        print(f"📐 Формат: {image_format}")
        
        # Генерируем изображение
        image_result = generate_image(full_prompt, aspect_ratio=image_format)
        
        if not image_result.get('success'):
            error_msg = image_result.get('error', 'Ошибка генерации изображения')
            bot.edit_message_text(
                f"❌ <b>ОШИБКА ГЕНЕРАЦИИ</b>\n\n{error_msg}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            return
        
        # Получаем байты изображения
        image_bytes = image_result.get('image_bytes')
        if not image_bytes:
            bot.edit_message_text(
                "❌ <b>ОШИБКА</b>\n\nИзображение не содержит данных",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            return
        
        # Сохраняем во временный файл
        fd, image_path = tempfile.mkstemp(suffix='.jpg', prefix='vk_post_')
        with os.fdopen(fd, 'wb') as f:
            f.write(image_bytes)
        
        # Показываем превью изображения пользователю
        with open(image_path, 'rb') as photo:
            bot.send_photo(
                call.message.chat.id,
                photo,
                caption="✅ <b>Изображение создано!</b>\n\n"
                        "📤 Загружаем в VK...",
                parse_mode='HTML'
            )
        
        # Показываем успех Этапа 2
        bot.edit_message_text(
            "✅ <b>ЭТАП 2 ЗАВЕРШЁН</b>\n\n"
            "🎨 Изображение сгенерировано\n"
            "📤 Начинаем загрузку в VK...",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        
        # Этап 3: Загрузка изображения в VK
        image_path = image_data['image_path']
        
        # Получаем access_token для VK
        user = db.get_user(user_id)
        connections = user.get('platform_connections', {})
        vks = connections.get('vks', [])
        
        # Находим нужное VK подключение
        vk_connection = None
        for vk in vks:
            if str(vk.get('user_id')) == str(platform_id):
                vk_connection = vk
                break
        
        if not vk_connection:
            bot.edit_message_text(
                "❌ <b>VK не подключен</b>\n\n"
                "Подключение не найдено. Подключите VK заново.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            return
        
        access_token = vk_connection.get('access_token')
        
        if not access_token:
            bot.edit_message_text(
                "❌ <b>Нет токена VK</b>\n\n"
                "Access token отсутствует. Переподключите VK.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            return
        
        # Загружаем изображение в VK
        import requests
        
        # Шаг 1: Получаем URL для загрузки
        try:
            upload_server_response = requests.get(
                "https://api.vk.com/method/photos.getWallUploadServer",
                params={
                    "access_token": access_token,
                    "v": "5.131"
                },
                timeout=10
            )
            
            upload_server_data = upload_server_response.json()
            
            if 'error' in upload_server_data:
                error_msg = upload_server_data['error'].get('error_msg', 'Unknown error')
                bot.edit_message_text(
                    f"❌ <b>Ошибка VK API</b>\n\n{error_msg}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                return
            
            upload_url = upload_server_data['response']['upload_url']
            
            # Шаг 2: Загружаем фото на сервер VK
            with open(image_path, 'rb') as photo_file:
                upload_response = requests.post(
                    upload_url,
                    files={'photo': photo_file},
                    timeout=30
                )
            
            upload_result = upload_response.json()
            
            # Шаг 3: Сохраняем фото на стене
            save_response = requests.get(
                "https://api.vk.com/method/photos.saveWallPhoto",
                params={
                    "access_token": access_token,
                    "v": "5.131",
                    "photo": upload_result['photo'],
                    "server": upload_result['server'],
                    "hash": upload_result['hash']
                },
                timeout=10
            )
            
            save_result = save_response.json()
            
            if 'error' in save_result:
                error_msg = save_result['error'].get('error_msg', 'Unknown error')
                bot.edit_message_text(
                    f"❌ <b>Ошибка сохранения фото</b>\n\n{error_msg}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                return
            
            # Получаем attachment ID
            photo_data = save_result['response'][0]
            photo_attachment = f"photo{photo_data['owner_id']}_{photo_data['id']}"
            
            bot.edit_message_text(
                "✅ <b>ЭТАП 3 ЗАВЕРШЁН</b>\n\n"
                "📤 Изображение загружено в VK\n"
                f"🆔 Attachment: {photo_attachment}\n\n"
                "🔜 Следующий этап: публикация поста",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            
            # Сохраняем attachment для следующего этапа
            # (передаём через временное хранилище)
            import json
            temp_data = {
                'post_text': post_text,
                'photo_attachment': photo_attachment,
                'access_token': access_token,
                'image_path': image_path
            }
            
            # Этап 4: Публикация на стену VK
            bot.edit_message_text(
                "📝 <b>ПУБЛИКАЦИЯ НА СТЕНУ VK</b>\n\n"
                "⏳ Отправляем пост...",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            
            # Публикуем пост с изображением
            post_response = requests.get(
                "https://api.vk.com/method/wall.post",
                params={
                    "access_token": access_token,
                    "v": "5.131",
                    "message": post_text,
                    "attachments": photo_attachment,
                    "from_group": 0  # От имени пользователя
                },
                timeout=10
            )
            
            post_result = post_response.json()
            
            if 'error' in post_result:
                error_msg = post_result['error'].get('error_msg', 'Unknown error')
                error_code = post_result['error'].get('error_code', 0)
                
                bot.edit_message_text(
                    f"❌ <b>Ошибка публикации</b>\n\n"
                    f"Код: {error_code}\n"
                    f"Сообщение: {error_msg}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                return
            
            # Получаем ID опубликованного поста
            post_id = post_result['response']['post_id']
            owner_id = vk_connection.get('user_id')
            post_url = f"https://vk.com/wall{owner_id}_{post_id}"
            
            # Успех! Показываем результат
            bot.edit_message_text(
                "🎉 <b>ПОСТ ОПУБЛИКОВАН!</b>\n\n"
                "✅ Изображение создано\n"
                "✅ Загружено в VK\n"
                "✅ Опубликовано на стене\n\n"
                f"🔗 <a href='{post_url}'>Открыть пост</a>\n\n"
                f"📊 Символов: {len(post_text)}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            # Очищаем временный файл
            try:
                import os
                os.remove(image_path)
            except:
                pass
            
        except requests.exceptions.Timeout:
            bot.edit_message_text(
                "❌ <b>Таймаут VK API</b>\n\n"
                "Превышено время ожидания. Попробуйте позже.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        except Exception as e:
            bot.edit_message_text(
                f"❌ <b>Ошибка загрузки в VK</b>\n\n{str(e)}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            import traceback
            traceback.print_exc()
        
        # TODO: Этап 3 - загрузка в VK (следующий этап)
        
    except Exception as e:
        bot.edit_message_text(
            f"❌ <b>ОШИБКА</b>\n\n{str(e)}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        import traceback
        traceback.print_exc()


def publish_to_pinterest(call, user_id, bot_id, platform_id, category_id, post_text):
    """Публикация в Pinterest (TODO)"""
    bot.edit_message_text(
        "⚠️ Публикация в Pinterest пока не реализована",
        call.message.chat.id,
        call.message.message_id
    )


def publish_to_telegram(call, user_id, bot_id, platform_id, category_id, post_text):
    """Публикация в Telegram (TODO)"""
    bot.edit_message_text(
        "⚠️ Публикация в Telegram пока не реализована",
        call.message.chat.id,
        call.message.message_id
    )


def publish_to_website(call, user_id, bot_id, platform_id, category_id, post_text):
    """Публикация на сайт (TODO)"""
    bot.edit_message_text(
        "⚠️ Публикация на сайт пока не реализована",
        call.message.chat.id,
        call.message.message_id
    )



print("✅ platform_category/main_menu.py загружен")
