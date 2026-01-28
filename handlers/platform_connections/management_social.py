# -*- coding: utf-8 -*-
"""
Управление соцсетями - просмотр, редактирование, удаление
"""
from telebot import types
from loader import bot, db
from utils import escape_html
import json
from .vk import user_adding_platform  # Импорт для совместимости с VK handlers

def manage_social_platforms(call):
    """Управление соцсетями"""
    platform_type = call.data.split("_")[-1]  # instagrams, vks, pinterests, telegrams
    user_id = call.from_user.id
    
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    platforms = connections.get(platform_type, [])
    
    platform_names = {
        'instagrams': ('📸', 'INSTAGRAM', 'username'),
        'vks': ('💬', 'ВКОНТАКТЕ', 'group_name'),
        'pinterests': ('📌', 'PINTEREST', 'board'),
        'telegrams': ('✈️', 'TELEGRAM', 'channel')
    }
    
    emoji, name, key = platform_names.get(platform_type, ('', 'ПЛОЩАДКИ', 'name'))
    
    text = (
        f"{emoji} <b>МОИ {name}</b>\n"
        "━━━━━━━━━━━━━━\n\n"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for idx, platform in enumerate(platforms):
        identifier = platform.get(key, 'Unknown')
        status = platform.get('status', 'active')
        status_emoji = "✅" if status == 'active' else "⚠️"
        
        text += f"{idx + 1}. {status_emoji} <code>{escape_html(identifier)}</code>\n"
        
        markup.add(
            types.InlineKeyboardButton(
                f"{idx + 1}. {identifier}",
                callback_data=f"edit_{platform_type[:-1]}_{idx}"
            )
        )
    
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="manage_platforms")
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
    
    bot.answer_callback_query(call.id)


# Обработчики удаления для соцсетей
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_instagram_") or call.data.startswith("edit_vk_") or call.data.startswith("edit_pinterest_") or call.data.startswith("edit_telegram_"))
def edit_social_platform(call):
    """Редактирование соцсети"""
    parts = call.data.split("_")
    platform_type = parts[1]  # instagram, vk, pinterest, telegram
    idx = int(parts[-1])
    user_id = call.from_user.id
    
    # Определяем множественное число
    platform_type_map = {
        'instagram': 'instagrams',
        'vk': 'vks',
        'pinterest': 'pinterests',
        'telegram': 'telegrams'
    }
    platform_type_plural = platform_type_map.get(platform_type, platform_type + 's')
    
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    platforms = connections.get(platform_type_plural, [])
    
    if idx >= len(platforms):
        bot.answer_callback_query(call.id, "❌ Не найдено")
        return
    
    platform = platforms[idx]
    
    names = {
        'instagram': ('📸', 'INSTAGRAM', platform.get('username', 'Unknown')),
        'vk': ('💬', 'ВКОНТАКТЕ', platform.get('group_name', 'Unknown')),
        'pinterest': ('📌', 'PINTEREST', platform.get('board', 'Unknown')),
        'telegram': ('✈️', 'TELEGRAM', '@' + platform.get('channel', 'Unknown'))
    }
    
    emoji, name, identifier = names.get(platform_type, ('', '', 'Unknown'))
    
    text = (
        f"{emoji} <b>УПРАВЛЕНИЕ {name}</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"Аккаунт: <code>{escape_html(identifier)}</code>\n"
        f"Статус: {'✅ Активен' if platform.get('status') == 'active' else '⚠️ Неактивен'}\n\n"
        "Выберите действие:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{platform_type}_{idx}"),
        types.InlineKeyboardButton("🔙 К списку", callback_data=f"manage_{platform_type_plural}")
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
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_instagram_") or call.data.startswith("delete_vk_") or call.data.startswith("delete_pinterest_") or call.data.startswith("delete_telegram_"))
def delete_social_platform(call):
    """Удаление соцсети"""
    parts = call.data.split("_")
    platform_type = parts[1]
    idx = int(parts[-1])
    user_id = call.from_user.id
    
    # Определяем множественное число
    platform_type_map = {
        'instagram': 'instagrams',
        'vk': 'vks',
        'pinterest': 'pinterests',
        'telegram': 'telegrams'
    }
    platform_type_plural = platform_type_map.get(platform_type, platform_type + 's')
    
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    platforms = connections.get(platform_type_plural, [])
    
    if idx >= len(platforms):
        bot.answer_callback_query(call.id, "❌ Не найдено")
        return
    
    deleted = platforms.pop(idx)
    connections[platform_type_plural] = platforms
    
    db.cursor.execute("""
        UPDATE users 
        SET platform_connections = %s::jsonb
        WHERE id = %s
    """, (json.dumps(connections), user_id))
    db.conn.commit()
    
    bot.answer_callback_query(call.id, "✅ Удалено")
    
    # Возврат к списку
    fake_call = type('obj', (object,), {
        'data': f'manage_{platform_type_plural}',
        'from_user': call.from_user,
        'message': call.message,
        'id': call.id
    })()
    
    manage_social_platforms(fake_call)


print("✅ handlers/platform_connections.py полностью загружен")


# ═══════════════════════════════════════════════════════════════
# ПОКАЗ ИНСТРУКЦИЙ
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_instruction_"))
def show_platform_instruction(call):
    """Показ детальной инструкции по подключению"""
    from handlers.connection_instructions import (
        get_wordpress_instruction, get_joomla_instruction, 
        get_bitrix_instruction, get_tilda_instruction,
        get_shopify_instruction, get_instagram_instruction,
        get_vk_instruction, get_telegram_instruction,
        get_pinterest_instruction
    )
    
    platform = call.data.replace("show_instruction_", "")
    
    instructions = {
        'wordpress': get_wordpress_instruction(),
        'joomla': get_joomla_instruction(),
        'bitrix': get_bitrix_instruction(),
        'tilda': get_tilda_instruction(),
        'shopify': get_shopify_instruction(),
        'instagram': get_instagram_instruction(),
        'vk': get_vk_instruction(),
        'telegram': get_telegram_instruction(),
        'pinterest': get_pinterest_instruction()
    }
    
    text = instructions.get(platform, "Инструкция не найдена")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="add_platform_menu")
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
    
    bot.answer_callback_query(call.id)


# Обновим меню выбора CMS
@bot.callback_query_handler(func=lambda call: call.data == "add_platform_website")
def add_platform_website_choose_cms(call):
    """Выбор типа CMS для подключения"""
    text = (
        "🌐 <b>ВЫБОР CMS</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите систему управления вашего сайта:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔷 WordPress", callback_data="connect_cms_wordpress"),
        types.InlineKeyboardButton("🔶 Joomla", callback_data="connect_cms_joomla"),
        types.InlineKeyboardButton("🔵 Битрикс24", callback_data="connect_cms_bitrix"),
        types.InlineKeyboardButton("🟣 Tilda", callback_data="connect_cms_tilda"),
        types.InlineKeyboardButton("🟢 Shopify", callback_data="connect_cms_shopify"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="add_platform_menu")
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
    
    bot.answer_callback_query(call.id)


# Обработчики для каждой CMS
@bot.callback_query_handler(func=lambda call: call.data.startswith("connect_cms_"))
def start_cms_connection(call):
    """Начало подключения CMS"""
    cms = call.data.replace("connect_cms_", "")
    user_id = call.from_user.id
    
    cms_names = {
        'wordpress': '🔷 WordPress',
        'joomla': '🔶 Joomla',
        'bitrix': '🔵 Битрикс24',
        'tilda': '🟣 Tilda',
        'shopify': '🟢 Shopify'
    }
    
    cms_name = cms_names.get(cms, 'CMS')
    
    text = (
        f"<b>{cms_name}</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Что вы хотите сделать?"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📖 Показать инструкцию", callback_data=f"show_instruction_{cms}"),
        types.InlineKeyboardButton("🔌 Начать подключение", callback_data=f"begin_connect_{cms}"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="add_platform_website")
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
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("begin_connect_"))
def begin_cms_connection(call):
    """Начало процесса подключения CMS"""
    cms = call.data.replace("begin_connect_", "")
    user_id = call.from_user.id
    
    # Устанавливаем тип CMS
    user_adding_platform[user_id] = {
        'type': 'website',
        'cms': cms,
        'step': 'url',
        'data': {}
    }
    
    cms_names = {
        'wordpress': 'WordPress',
        'joomla': 'Joomla',
        'bitrix': 'Битрикс24',
        'tilda': 'Tilda',
        'shopify': 'Shopify'
    }
    
    cms_name = cms_names.get(cms, 'сайта')
    
    text = (
        f"🌐 <b>ПОДКЛЮЧЕНИЕ {cms_name.upper()}</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "<b>Шаг 1:</b> URL сайта\n\n"
        f"Отправьте адрес вашего {cms_name} сайта.\n\n"
        "<b>Пример:</b> <code>https://mysite.com</code>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
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
    
    bot.answer_callback_query(call.id, f"📝 Ожидаю URL {cms_name} сайта...")


# Аналогично добавим кнопки инструкций для соцсетей
@bot.callback_query_handler(func=lambda call: call.data == "add_platform_instagram")
def add_platform_instagram_with_instruction(call):
    """Instagram с кнопкой инструкции"""
    text = (
        "📸 <b>ПОДКЛЮЧЕНИЕ INSTAGRAM</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Что вы хотите сделать?"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📖 Показать инструкцию", callback_data="show_instruction_instagram"),
        types.InlineKeyboardButton("🔌 Начать подключение", callback_data="begin_connect_instagram"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="add_platform_menu")
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
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "begin_connect_instagram")
def begin_instagram_connection(call):
    """Начало подключения Instagram"""
    user_id = call.from_user.id
    
    text = (
        "📸 <b>ПОДКЛЮЧЕНИЕ INSTAGRAM</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "<b>Шаг 1 из 2:</b> Username аккаунта\n\n"
        "Отправьте username вашего Instagram Business аккаунта.\n\n"
        "<b>Пример:</b> <code>@mycompany</code>\n\n"
        "<i>💡 Необходим Instagram Business аккаунт</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📖 Как получить Business?", callback_data="show_instruction_instagram"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
    )
    
    user_adding_platform[user_id] = {
        'type': 'instagram',
        'step': 'username',
        'data': {}
    }
    
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
    
    bot.answer_callback_query(call.id, "📝 Ожидаю username...")


@bot.callback_query_handler(func=lambda call: call.data == "show_instruction_vk")
def show_vk_instruction(call):
    """Показать подробную инструкцию по получению токена VK"""
    text = (
        "📖 <b>ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ VK</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>ШАГ 1: Создание приложения</b>\n\n"
        "1. Перейдите на <code>vk.com/apps?act=manage</code>\n"
        "2. Нажмите \"Создать приложение\"\n"
        "3. Выберите тип \"Standalone приложение\"\n"
        "4. Введите название (например \"AutoPost Bot\")\n"
        "5. Нажмите \"Подключить приложение\"\n\n"
        
        "<b>ШАГ 2: Получение токена</b>\n\n"
        "Вариант А - Для управления группой:\n"
        "1. Зайдите в настройки вашей группы\n"
        "2. Раздел \"API usage\" → \"Ключи доступа\"\n"
        "3. Создайте токен сообщества\n"
        "4. Выберите права: wall, photos\n"
        "5. Скопируйте токен\n\n"
        
        "Вариант Б - Быстрый способ (через OAuth):\n"
        "1. Откройте в браузере ссылку:\n"
        "<code>https://oauth.vk.com/authorize?client_id=ВАШЕ_APP_ID&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=wall,photos,groups,offline&response_type=token&v=5.131</code>\n\n"
        "2. Замените ВАШЕ_APP_ID на ID вашего приложения\n"
        "3. После авторизации скопируйте access_token из адресной строки\n\n"
        
        "<b>ШАГ 3: Подключение в боте</b>\n\n"
        "1. Нажмите \"🔌 Начать подключение\"\n"
        "2. Отправьте ID или ссылку на группу\n"
        "3. Отправьте токен доступа\n\n"
        
        "<b>📝 Примеры ID группы:</b>\n"
        "• <code>mycompany</code>\n"
        "• <code>https://vk.com/mycompany</code>\n"
        "• <code>-123456789</code> (если ID отрицательный)\n\n"
        
        "⚠️ <b>Важно:</b>\n"
        "• Вы должны быть администратором группы\n"
        "• Токен должен иметь права на публикацию\n"
        "• Токен сохраняется в зашифрованном виде"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔌 Начать подключение", callback_data="begin_connect_vk"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="add_platform_vk")
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
    
    bot.answer_callback_query(call.id)


# УДАЛЕН: дублирующий обработчик add_platform_vk
# Теперь используется обработчик из vk_integration/vk_telegram_handler.py


@bot.callback_query_handler(func=lambda call: call.data == "begin_connect_vk")
def begin_vk_connection(call):
    """Начало подключения ВКонтакте"""
    user_id = call.from_user.id
    
    text = (
        "💬 <b>ПОДКЛЮЧЕНИЕ ВКОНТАКТЕ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "<b>Шаг 1 из 2:</b> ID группы\n\n"
        "Отправьте ID или ссылку на вашу группу ВКонтакте.\n\n"
        "<b>Примеры:</b>\n"
        "<code>mycompany</code>\n"
        "<code>https://vk.com/mycompany</code>\n\n"
        "<i>💡 Вы должны быть администратором группы</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📖 Как получить токен?", callback_data="show_instruction_vk"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
    )
    
    user_adding_platform[user_id] = {
        'type': 'vk',
        'step': 'group_id',
        'data': {}
    }
    
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
    
    bot.answer_callback_query(call.id, "📝 Ожидаю ID группы...")


print("✅ handlers/platform_connections/management_social.py загружен")
