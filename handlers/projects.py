"""
Обработчик меню проектов (ботов) - расширенная версия
"""
from telebot import types
from loader import bot
from database.database import db
from utils import escape_html, safe_answer_callback
from datetime import datetime


def show_projects_menu(message):
    """Показать меню проектов с расширенной информацией"""
    user_id = message.from_user.id
    
    # Получаем список ботов пользователя
    bots = db.get_user_bots(user_id)
    
    if not bots:
        # Если ботов нет - предлагаем создать первого
        text = (
            "📁 <b>МОИ ПРОЕКТЫ</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "У вас пока нет ни одного проекта.\n\n"
            "🚀 <b>Создайте своего первого бота!</b>\n\n"
            "После создания вы сможете:\n"
            "✅ Настроить категории товаров/услуг\n"
            "✅ Генерировать ключевые фразы с AI\n"
            "✅ Создавать описания с помощью Claude\n"
            "✅ Генерировать изображения с Nano Banana Pro\n"
            "✅ Загружать медиа-контент\n"
            "✅ Подключать площадки для автопостинга\n"
            "✅ Управлять ценами и отзывами\n\n"
            "👇 Нажмите кнопку ниже, чтобы начать:"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ Создать первый проект", callback_data="create_bot")
        )
        
    else:
        # Показываем список ботов с расширенной статистикой
        text = (
            f"📁 <b>МОИ ПРОЕКТЫ</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"📊 Всего проектов: <b>{len(bots)}</b>\n\n"
        )
        
        # Считаем общую статистику
        total_categories = 0
        total_keywords = 0
        total_media = 0
        
        for bot_item in bots:
            bot_id = bot_item['id']
            categories = db.get_bot_categories(bot_id)
            
            if categories:
                total_categories += len(categories)
                
                for cat in categories:
                    # Подсчитываем ключевые фразы
                    keywords = cat.get('keywords', [])
                    if isinstance(keywords, list):
                        total_keywords += len(keywords)
                    
                    # Подсчитываем медиа
                    media = cat.get('media', [])
                    if isinstance(media, list):
                        total_media += len(media)
        
        text += (
            f"📂 Категорий: <b>{total_categories}</b>\n"
            f"🔑 Ключевых фраз: <b>{total_keywords}</b>\n"
            f"📷 Медиа файлов: <b>{total_media}</b>\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "Выберите проект для работы:\n\n"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Добавляем кнопки для каждого бота
        for idx, bot_item in enumerate(bots[:15], 1):  # Показываем до 15
            bot_id = bot_item['id']
            bot_name = bot_item['name']
            
            # Получаем количество категорий
            categories = db.get_bot_categories(bot_id)
            cat_count = len(categories) if categories else 0
            
            # Формируем текст кнопки с номером
            btn_text = f"{idx}. {bot_name}"
            if cat_count > 0:
                btn_text += f" • {cat_count} кат."
            
            markup.add(
                types.InlineKeyboardButton(btn_text, callback_data=f"open_bot_{bot_id}")
            )
        
        # Кнопка быстрого доступа к публикациям
        markup.add(
            types.InlineKeyboardButton("🚀 Быстрый доступ к публикациям", callback_data="quick_publish_menu")
        )
        
        # Дополнительные кнопки
        markup.row(
            types.InlineKeyboardButton("➕ Создать", callback_data="create_bot"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="projects_stats")
        )
        
        # Если ботов больше 15 - показываем кнопку "Показать все"
        if len(bots) > 15:
            markup.add(
                types.InlineKeyboardButton(f"📋 Показать все ({len(bots)})", callback_data="show_all_projects")
            )
    
    # Отправляем сообщение
    try:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка отправки меню проектов: {e}")


@bot.message_handler(func=lambda message: message.text == "📁 Проекты")
def handle_projects_button(message):
    """Обработчик кнопки 'Проекты'"""
    show_projects_menu(message)


@bot.callback_query_handler(func=lambda call: call.data == "show_projects")
def handle_show_projects_callback(call):
    """Обработчик callback для показа списка проектов"""
    # Создаем fake message
    fake_msg = type('obj', (object,), {
        'from_user': call.from_user,
        'chat': type('obj', (object,), {'id': call.message.chat.id})()
    })()
    
    # Удаляем предыдущее сообщение
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    show_projects_menu(fake_msg)
    safe_answer_callback(bot, call.id)


# ═══════════════════════════════════════════════════════════════
# ДЕТАЛЬНАЯ СТАТИСТИКА ПРОЕКТОВ
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == "projects_stats")
def show_projects_statistics(call):
    """Показать детальную статистику всех проектов"""
    user_id = call.from_user.id
    
    bots = db.get_user_bots(user_id)
    
    if not bots:
        safe_answer_callback(bot, call.id, "❌ Нет проектов")
        return
    
    text = (
        "📊 <b>СТАТИСТИКА ПРОЕКТОВ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
    )
    
    # Собираем детальную статистику
    total_categories = 0
    total_keywords = 0
    total_media = 0
    total_descriptions = 0
    total_prices = 0
    total_reviews = 0
    
    most_active_bot = None
    max_categories = 0
    
    for bot_item in bots:
        bot_id = bot_item['id']
        bot_name = bot_item['name']
        categories = db.get_bot_categories(bot_id)
        
        if not categories:
            continue
        
        cat_count = len(categories)
        total_categories += cat_count
        
        # Обновляем самый активный бот
        if cat_count > max_categories:
            max_categories = cat_count
            most_active_bot = bot_name
        
        for cat in categories:
            # Ключевые фразы
            keywords = cat.get('keywords', [])
            if isinstance(keywords, list):
                total_keywords += len(keywords)
            
            # Медиа
            media = cat.get('media', [])
            if isinstance(media, list):
                total_media += len(media)
            
            # Описания
            if cat.get('description'):
                total_descriptions += 1
            
            # Цены
            prices = cat.get('prices', {})
            if isinstance(prices, dict) and prices:
                total_prices += len(prices)
            
            # Отзывы
            reviews = cat.get('reviews', [])
            if isinstance(reviews, list):
                total_reviews += len(reviews)
    
    # Средние показатели
    avg_categories = total_categories / len(bots) if bots else 0
    avg_keywords = total_keywords / total_categories if total_categories else 0
    
    text += (
        f"<b>📁 ПРОЕКТЫ:</b>\n"
        f"• Всего: <code>{len(bots)}</code>\n"
        f"• Самый активный: <b>{most_active_bot or 'N/A'}</b> ({max_categories} кат.)\n\n"
        
        f"<b>📂 КАТЕГОРИИ:</b>\n"
        f"• Всего: <code>{total_categories}</code>\n"
        f"• В среднем: <code>{avg_categories:.1f}</code> на проект\n\n"
        
        f"<b>🔑 КОНТЕНТ:</b>\n"
        f"• Ключевых фраз: <code>{total_keywords}</code>\n"
        f"• В среднем: <code>{avg_keywords:.1f}</code> на категорию\n"
        f"• Описаний: <code>{total_descriptions}</code>\n\n"
        
        f"<b>📷 МЕДИА:</b>\n"
        f"• Файлов: <code>{total_media}</code>\n\n"
        
        f"<b>💰 ДОПОЛНИТЕЛЬНО:</b>\n"
        f"• Прайс-листов: <code>{total_prices}</code>\n"
        f"• Отзывов: <code>{total_reviews}</code>\n\n"
        
        "━━━━━━━━━━━━━━\n\n"
        "<i>💡 Продолжайте развивать ваши проекты!</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📈 Топ проектов", callback_data="top_projects"),
        types.InlineKeyboardButton("🔙 К проектам", callback_data="show_projects")
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
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    safe_answer_callback(bot, call.id)


@bot.callback_query_handler(func=lambda call: call.data == "top_projects")
def show_top_projects(call):
    """Показать топ проектов по активности"""
    user_id = call.from_user.id
    
    bots = db.get_user_bots(user_id)
    
    if not bots:
        safe_answer_callback(bot, call.id, "❌ Нет проектов")
        return
    
    # Собираем статистику для каждого бота
    bot_stats = []
    
    for bot_item in bots:
        bot_id = bot_item['id']
        bot_name = bot_item['name']
        categories = db.get_bot_categories(bot_id)
        
        cat_count = len(categories) if categories else 0
        keywords_count = 0
        media_count = 0
        
        if categories:
            for cat in categories:
                keywords = cat.get('keywords', [])
                if isinstance(keywords, list):
                    keywords_count += len(keywords)
                
                media = cat.get('media', [])
                if isinstance(media, list):
                    media_count += len(media)
        
        # Считаем общий балл активности
        activity_score = cat_count * 10 + keywords_count + media_count * 2
        
        bot_stats.append({
            'id': bot_id,
            'name': bot_name,
            'categories': cat_count,
            'keywords': keywords_count,
            'media': media_count,
            'score': activity_score
        })
    
    # Сортируем по активности
    bot_stats.sort(key=lambda x: x['score'], reverse=True)
    
    text = (
        "📈 <b>ТОП ПРОЕКТОВ ПО АКТИВНОСТИ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
    )
    
    medals = ["🥇", "🥈", "🥉"]
    
    for idx, stat in enumerate(bot_stats[:10], 1):
        medal = medals[idx-1] if idx <= 3 else f"{idx}."
        
        text += (
            f"{medal} <b>{stat['name']}</b>\n"
            f"   📂 {stat['categories']} кат. | "
            f"🔑 {stat['keywords']} фраз | "
            f"📷 {stat['media']} медиа\n"
            f"   💯 Активность: <code>{stat['score']}</code>\n\n"
        )
    
    text += "━━━━━━━━━━━━━━\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Общая статистика", callback_data="projects_stats"),
        types.InlineKeyboardButton("🔙 К проектам", callback_data="show_projects")
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
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    safe_answer_callback(bot, call.id)


# ═══════════════════════════════════════════════════════════════
# ПОКАЗ ВСЕХ ПРОЕКТОВ (ПОСТРАНИЧНО)
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_all_projects"))
def show_all_projects(call):
    """Показать все проекты постранично"""
    user_id = call.from_user.id
    
    # Получаем страницу из callback (по умолчанию 0)
    parts = call.data.split("_")
    page = int(parts[-1]) if len(parts) > 3 and parts[-1].isdigit() else 0
    
    bots = db.get_user_bots(user_id)
    
    if not bots:
        safe_answer_callback(bot, call.id, "❌ Нет проектов")
        return
    
    # Пагинация
    per_page = 10
    total_pages = (len(bots) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    
    current_bots = bots[start_idx:end_idx]
    
    text = (
        f"📁 <b>ВСЕ ПРОЕКТЫ</b>\n"
        f"Страница {page + 1} из {total_pages}\n"
        "━━━━━━━━━━━━━━\n\n"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for idx, bot_item in enumerate(current_bots, start_idx + 1):
        bot_id = bot_item['id']
        bot_name = bot_item['name']
        
        categories = db.get_bot_categories(bot_id)
        cat_count = len(categories) if categories else 0
        
        btn_text = f"{idx}. {bot_name}"
        if cat_count > 0:
            btn_text += f" • {cat_count} кат."
        
        markup.add(
            types.InlineKeyboardButton(btn_text, callback_data=f"open_bot_{bot_id}")
        )
    
    # Кнопки навигации
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(
            types.InlineKeyboardButton("◀️ Назад", callback_data=f"show_all_projects_{page-1}")
        )
    
    if page < total_pages - 1:
        nav_buttons.append(
            types.InlineKeyboardButton("Вперед ▶️", callback_data=f"show_all_projects_{page+1}")
        )
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    markup.add(
        types.InlineKeyboardButton("🔙 К главному меню", callback_data="show_projects")
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
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    safe_answer_callback(bot, call.id)


# ═══════════════════════════════════════════════════════════════
# БЫСТРЫЕ ДЕЙСТВИЯ С ПРОЕКТАМИ
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == "quick_actions_projects")
def show_quick_actions(call):
    """Быстрые действия с проектами"""
    text = (
        "⚡ <b>БЫСТРЫЕ ДЕЙСТВИЯ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите действие:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Создать новый проект", callback_data="create_bot"),
        types.InlineKeyboardButton("📊 Статистика проектов", callback_data="projects_stats"),
        types.InlineKeyboardButton("📈 Топ по активности", callback_data="top_projects"),
        types.InlineKeyboardButton("🔍 Поиск проекта", callback_data="search_project"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="show_projects")
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
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    safe_answer_callback(bot, call.id)


# Заглушка для поиска
@bot.callback_query_handler(func=lambda call: call.data == "search_project")
def search_project(call):
    """Поиск проекта (заглушка)"""
    text = (
        "🔍 <b>ПОИСК ПРОЕКТА</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Функция поиска будет доступна в ближайшее время!\n\n"
        "Вы сможете искать проекты по:\n"
        "• Названию\n"
        "• Категориям\n"
        "• Ключевым словам\n\n"
        "<i>Следите за обновлениями</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="show_projects")
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
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    safe_answer_callback(bot, call.id)


@bot.callback_query_handler(func=lambda call: call.data == "quick_publish_menu")
def show_quick_publish_menu(call):
    """Меню быстрого доступа к публикациям"""
    user_id = call.from_user.id
    
    # Получаем все проекты пользователя
    bots = db.get_user_bots(user_id)
    
    if not bots:
        safe_answer_callback(bot, call.id, "❌ У вас нет проектов", show_alert=True)
        return
    
    text = """
🚀 <b>БЫСТРЫЙ ДОСТУП К ПУБЛИКАЦИЯМ</b>

Выберите платформу для мгновенной публикации:
• Публикация из случайной категории
• Без подтверждений и вопросов
• Моментальная отправка

<i>Показаны только подключенные платформы</i>
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    platforms_found = False
    platform_names = {
        'website': ('🌐 WordPress', 'website'),
        'pinterest': ('📌 Pinterest', 'pinterest'),
        'instagram': ('📷 Instagram', 'instagram'),
        'telegram': ('✈️ Telegram', 'telegram'),
        'vk': ('🔵 VK', 'vk')
    }
    
    # Собираем все подключенные платформы из всех проектов
    connected_platforms = set()
    
    for bot_item in bots:
        bot_connections = bot_item.get('connected_platforms', {})
        
        for platform_type in ['website', 'pinterest', 'instagram', 'telegram', 'vk']:
            # Проверяем старый и новый формат подключений
            platform_key_old = f"{platform_type}s"  # websites, telegrams, etc
            platform_key_new = platform_type  # website, telegram, etc
            
            if bot_connections.get(platform_key_new) or bot_connections.get(platform_key_old):
                connected_platforms.add(platform_type)
    
    # Добавляем кнопки для подключенных платформ
    for platform_type in ['website', 'pinterest', 'instagram', 'telegram', 'vk']:
        if platform_type in connected_platforms:
            platforms_found = True
            icon, name = platform_names[platform_type]
            markup.add(
                types.InlineKeyboardButton(
                    f"{icon} Опубликовать",
                    callback_data=f"quick_publish_{platform_type}"
                )
            )
    
    if not platforms_found:
        text += "\n\n⚠️ <b>Нет подключенных платформ</b>\n"
        text += "Подключите площадки в настройках проектов"
    
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_projects")
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
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    safe_answer_callback(bot, call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("quick_publish_"))
def handle_quick_publish(call):
    """Быстрая публикация на платформу"""
    platform_type = call.data.replace("quick_publish_", "")
    user_id = call.from_user.id
    
    safe_answer_callback(bot, call.id, f"🔄 Публикую на {platform_type.upper()}...")
    
    try:
        # Получаем все проекты пользователя
        bots = db.get_user_bots(user_id)
        
        # Собираем все категории из всех проектов
        all_categories = []
        for bot_item in bots:
            bot_id = bot_item['id']
            categories = db.get_bot_categories(bot_id)
            if categories:
                for cat in categories:
                    all_categories.append({
                        'category': cat,
                        'bot_id': bot_id,
                        'bot_name': bot_item['name']
                    })
        
        if not all_categories:
            bot.send_message(call.message.chat.id, "❌ Нет категорий для публикации")
            return
        
        # Выбираем случайную категорию
        import random
        selected = random.choice(all_categories)
        category = selected['category']
        bot_id = selected['bot_id']
        category_id = category['id']
        
        # Получаем platform_id из подключений
        bot_data = db.get_bot(bot_id)
        bot_connections = bot_data.get('connected_platforms', {})
        
        # Ищем platform_id (может быть в старом или новом формате)
        platform_key_old = f"{platform_type}s"  # websites, telegrams
        platform_key_new = platform_type  # website, telegram
        
        platforms_list = bot_connections.get(platform_key_new) or bot_connections.get(platform_key_old) or []
        
        if not platforms_list:
            bot.send_message(call.message.chat.id, f"❌ Платформа {platform_type.upper()} не подключена")
            return
        
        # Берём первую подключенную платформу
        if isinstance(platforms_list, list) and len(platforms_list) > 0:
            platform_id = platforms_list[0]
        else:
            platform_id = platform_type
        
        # Перенаправляем на обработчик публикации
        from handlers.platform_category.main_menu import handle_platform_ai_post
        
        # Создаём фейковый callback для публикации
        class FakeCall:
            def __init__(self, data, message, from_user, call_id):
                self.data = data
                self.message = message
                self.from_user = from_user
                self.id = call_id  # Используем реальный ID
        
        fake_call = FakeCall(
            data=f"platform_ai_post_{platform_type}_{category_id}_{bot_id}_{platform_id}",
            message=call.message,
            from_user=call.from_user,
            call_id=call.id  # Передаём реальный ID оригинального callback
        )
        
        # Вызываем обработчик публикации
        handle_platform_ai_post(fake_call)
        
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка публикации: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "back_to_projects")
def back_to_projects(call):
    """Возврат к меню проектов"""
    show_projects_menu(call.message)
    safe_answer_callback(bot, call.id)


print("✅ handlers/projects.py (расширенный) загружен")
