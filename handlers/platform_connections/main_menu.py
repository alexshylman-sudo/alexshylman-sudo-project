# -*- coding: utf-8 -*-
"""
Главное меню подключений платформ
"""
from telebot import types
from loader import bot, db
from utils import escape_html
from .utils import check_global_platform_uniqueness
import json

@bot.callback_query_handler(func=lambda call: call.data == "settings_api_keys")
def handle_platform_connections(call):
    """Управление подключениями к площадкам"""
    user_id = call.from_user.id
    
    # Получаем все подключения пользователя
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    
    if not isinstance(connections, dict):
        connections = {}
    
    # Считаем подключения по типам
    websites = connections.get('websites', [])
    instagrams = connections.get('instagrams', [])
    vks = connections.get('vks', [])
    pinterests = connections.get('pinterests', [])
    telegrams = connections.get('telegrams', [])
    
    text = (
        "🔌 <b>МОИ ПОДКЛЮЧЕНИЯ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Управляйте подключениями к внешним площадкам:\n\n"
    )
    
    has_connections = False
    
    # Сайты (только если есть)
    if websites:
        has_connections = True
        text += f"🌐 <b>Сайты ({len(websites)}):</b>\n"
        for idx, site in enumerate(websites, 1):
            url = site.get('url', 'Unknown')
            # Извлекаем только домен из URL
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc or url
                text += f"   {idx}. {escape_html(domain)}\n"
            except:
                text += f"   {idx}. {escape_html(url)}\n"
        text += "\n"
    
    # Instagram (только если есть)
    if instagrams:
        has_connections = True
        text += f"📸 <b>Instagram ({len(instagrams)}):</b>\n"
        for idx, ig in enumerate(instagrams, 1):
            username = ig.get('username', 'Unknown')
            text += f"   {idx}. @{escape_html(username)}\n"
        text += "\n"
    
    # ВКонтакте (только если есть)
    if vks:
        has_connections = True
        text += f"💬 <b>ВКонтакте ({len(vks)}):</b>\n"
        for idx, vk in enumerate(vks, 1):
            group_name = vk.get('group_name', 'Unknown')
            vk_type = vk.get('type', 'user')
            
            # Определяем иконку по типу
            if vk_type == 'group':
                icon = "📝"  # Группа
                members = vk.get('members_count', 0)
                members_text = f" ({members:,})" if members > 0 else ""
                text += f"   {idx}. {icon} {escape_html(group_name)}{members_text}\n"
            else:
                icon = "👤"  # Личная страница
                text += f"   {idx}. {icon} {escape_html(group_name)}\n"
        text += "\n"
    
    # Pinterest (только если есть)
    if pinterests:
        has_connections = True
        text += f"📌 <b>Pinterest ({len(pinterests)}):</b>\n"
        for idx, pin in enumerate(pinterests, 1):
            board = pin.get('board', 'Unknown')
            text += f"   {idx}. {escape_html(board)}\n"
        text += "\n"
    
    # Telegram (только если есть)
    if telegrams:
        has_connections = True
        text += f"✈️ <b>Telegram ({len(telegrams)}):</b>\n"
        for idx, tg in enumerate(telegrams, 1):
            channel = tg.get('channel', 'Unknown')
            text += f"   {idx}. @{escape_html(channel)}\n"
        text += "\n"
    
    # Если нет подключений
    if not has_connections:
        text += "У вас пока нет подключенных площадок.\n\n"
    
    text += "━━━━━━━━━━━━━━\n\n<i>💡 Подключите площадки для автопостинга контента</i>"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Добавить площадку", callback_data="add_platform_menu"),
        types.InlineKeyboardButton("📝 Управление подключениями", callback_data="manage_platforms"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True  # ← Отключаем превью!
        )
    except:
        bot.send_message(
            call.message.chat.id, 
            text, 
            reply_markup=markup, 
            parse_mode='HTML',
            disable_web_page_preview=True  # ← Отключаем превью!
        )
    
    bot.answer_callback_query(call.id)


# ═══════════════════════════════════════════════════════════════
# ДОБАВЛЕНИЕ ПЛОЩАДКИ
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data == "add_platform_menu")
def add_platform_menu(call):
    """Меню выбора типа площадки"""
    text = (
        "➕ <b>ДОБАВИТЬ ПЛОЩАДКУ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Выберите тип площадки которую хотите подключить:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Одна кнопка для всех CMS
    markup.add(
        types.InlineKeyboardButton("🌐 WEB сайт", callback_data="add_website_menu")
    )
    
    # Соцсети
    markup.add(
        types.InlineKeyboardButton("📸 Instagram", callback_data="add_platform_instagram"),
        types.InlineKeyboardButton("💬 ВКонтакте", callback_data="add_platform_vk"),
        types.InlineKeyboardButton("📌 Pinterest", callback_data="add_platform_pinterest"),
        types.InlineKeyboardButton("✈️ Telegram канал", callback_data="add_platform_telegram"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="settings_api_keys")
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML', disable_web_page_preview=True)
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "manage_platforms")
def handle_manage_platforms(call):
    """Управление существующими подключениями"""
    user_id = call.from_user.id
    
    # Получаем все подключения пользователя
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    
    if not isinstance(connections, dict):
        connections = {}
    
    # Считаем подключения
    websites = connections.get('websites', [])
    pinterests = connections.get('pinterests', [])
    telegrams = connections.get('telegrams', [])
    vks = connections.get('vks', [])
    
    total = len(websites) + len(pinterests) + len(telegrams) + len(vks)
    
    if total == 0:
        text = (
            "📋 <b>УПРАВЛЕНИЕ ПОДКЛЮЧЕНИЯМИ</b>\n\n"
            "У вас пока нет подключенных площадок.\n\n"
            "Добавьте площадку для начала работы."
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("➕ Добавить площадку", callback_data="add_platform_menu")
        )
        markup.add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="settings_api_keys")
        )
    else:
        text = (
            f"📋 <b>УПРАВЛЕНИЕ ПОДКЛЮЧЕНИЯМИ</b>\n\n"
            f"Управляйте подключениями и внешним площадкам:\n\n"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Кнопки для каждого типа площадки
        if websites:
            text += f"🌐 <b>Сайты ({len(websites)}):</b>\n"
            for site in websites:
                url = site.get('url', 'Неизвестный')
                text += f"   • {url}\n"
            text += "\n"
            markup.add(
                types.InlineKeyboardButton(f"🌐 Сайты ({len(websites)})", callback_data="manage_websites")
            )
        
        if pinterests:
            text += f"📌 <b>Pinterest ({len(pinterests)}):</b>\n"
            for pin in pinterests:
                board = pin.get('board', 'Неизвестная')
                text += f"   • @{board}\n"
            text += "\n"
            markup.add(
                types.InlineKeyboardButton(f"📌 Pinterest ({len(pinterests)})", callback_data="manage_pinterests")
            )
        
        if telegrams:
            text += f"✈️ <b>Telegram ({len(telegrams)}):</b>\n"
            for tg in telegrams:
                channel = tg.get('channel', 'Неизвестный')
                text += f"   • @{channel}\n"
            text += "\n"
            markup.add(
                types.InlineKeyboardButton(f"✈️ Telegram ({len(telegrams)})", callback_data="manage_telegrams")
            )
        
        if vks:
            text += f"💬 <b>VK ({len(vks)}):</b>\n"
            for vk in vks:
                group_name = vk.get('group_name', 'Неизвестная')
                vk_type = vk.get('type', 'user')
                
                # Определяем иконку
                if vk_type == 'group':
                    icon = "📝"
                    members = vk.get('members_count', 0)
                    members_text = f" ({members:,})" if members > 0 else ""
                    text += f"   • {icon} {group_name}{members_text}\n"
                else:
                    icon = "👤"
                    text += f"   • {icon} {group_name}\n"
            text += "\n"
            markup.add(
                types.InlineKeyboardButton(f"💬 VK ({len(vks)})", callback_data="manage_vks")
            )
        
        markup.add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="settings_api_keys")
        )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML', disable_web_page_preview=True)
    
    bot.answer_callback_query(call.id)


print("✅ handlers/platform_connections/main_menu.py загружен")
