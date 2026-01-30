# -*- coding: utf-8 -*-
"""
Подключение VK через токены (два способа)
"""
from telebot import types
from loader import bot, db
import json


@bot.callback_query_handler(func=lambda call: call.data == 'add_platform_vk')
def handle_vk_connection_choice(call):
    """
    Выбор способа подключения VK
    """
    user_id = call.from_user.id
    
    bot.answer_callback_query(call.id)
    
    # Показываем выбор способа
    message_text = (
        "🔵 <b>Подключение ВКонтакте</b>\n\n"
        "Выберите способ подключения:\n\n"
        "📝 <b>Токен сообщества</b> - для публикации в группы VK\n"
        "• Простой способ\n"
        "• Нужен токен из настроек группы\n"
        "• Только для групп где вы админ\n\n"
        "👤 <b>Личный токен</b> - для публикации на личную страницу\n"
        "• Универсальный способ\n"
        "• Нужно получить токен через OAuth\n"
        "• Работает для личной страницы + групп"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "📝 Токен сообщества (для групп)",
            callback_data=f"vk_method_group_{user_id}"
        ),
        types.InlineKeyboardButton(
            "👤 Личный токен (универсальный)",
            callback_data=f"vk_method_personal_{user_id}"
        ),
        types.InlineKeyboardButton(
            "◀️ Назад",
            callback_data="back_to_add_platform"
        )
    )
    
    bot.edit_message_text(
        message_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('vk_method_group_'))
def handle_vk_group_token_instruction(call):
    """
    Инструкция для токена сообщества
    """
    user_id = call.from_user.id
    
    bot.answer_callback_query(call.id)
    
    message_text = (
        "📝 <b>Подключение через токен сообщества</b>\n\n"
        "<b>Шаг 1:</b> Зайдите в настройки вашей группы VK\n"
        "Управление → Работа с API\n\n"
        "<b>Шаг 2:</b> Создайте ключ доступа:\n"
        "• Включите права: <code>Фотографии</code> и <code>Записи на стене</code>\n"
        "• Скопируйте токен (начинается с <code>vk1.a.</code>)\n\n"
        "<b>Шаг 3:</b> Отправьте токен боту\n"
        "Просто вставьте и отправьте следующим сообщением\n\n"
        "⚠️ <b>Важно:</b> Токен действует только для ОДНОЙ группы!"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "◀️ Назад к выбору способа",
            callback_data="add_platform_vk"
        )
    )
    
    bot.edit_message_text(
        message_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )
    
    # Устанавливаем состояние ожидания токена
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    if isinstance(connections, str):
        connections = json.loads(connections)
    
    connections['_vk_awaiting_token'] = {
        'type': 'group',
        'message_id': call.message.message_id
    }
    
    db.cursor.execute("""
        UPDATE users
        SET platform_connections = %s::jsonb
        WHERE id = %s
    """, (json.dumps(connections), user_id))
    db.conn.commit()


@bot.callback_query_handler(func=lambda call: call.data.startswith('vk_method_personal_'))
def handle_vk_personal_token_instruction(call):
    """
    Инструкция для личного токена
    """
    user_id = call.from_user.id
    
    bot.answer_callback_query(call.id)
    
    # Генерируем OAuth ссылку
    oauth_url = (
        f"https://oauth.vk.com/authorize"
        f"?client_id=5354809"
        f"&scope=wall,photos,groups,offline"
        f"&redirect_uri=https://oauth.vk.com/blank.html"
        f"&display=page"
        f"&response_type=token"
        f"&v=5.131"
    )
    
    message_text = (
        "👤 <b>Подключение через личный токен</b>\n\n"
        "<b>Шаг 1:</b> Нажмите на кнопку ниже ⬇️\n\n"
        "<b>Шаг 2:</b> Разрешите доступ к:\n"
        "• Фотографиям\n"
        "• Стене\n"
        "• Группам\n"
        "• Оффлайн доступу\n\n"
        "<b>Шаг 3:</b> После разрешения вы увидите адресную строку:\n"
        "<code>https://oauth.vk.com/blank.html#access_token=vk1.a....</code>\n\n"
        "<b>Шаг 4:</b> Скопируйте весь токен после <code>access_token=</code> и до <code>&expires_in</code>\n\n"
        "<b>Шаг 5:</b> Отправьте токен боту следующим сообщением\n\n"
        "💡 <b>Токен начинается с:</b> <code>vk1.a.</code>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔵 Получить токен VK",
            url=oauth_url
        ),
        types.InlineKeyboardButton(
            "◀️ Назад к выбору способа",
            callback_data="add_platform_vk"
        )
    )
    
    bot.edit_message_text(
        message_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )
    
    # Устанавливаем состояние ожидания токена
    user = db.get_user(user_id)
    connections = user.get('platform_connections', {})
    if isinstance(connections, str):
        connections = json.loads(connections)
    
    connections['_vk_awaiting_token'] = {
        'type': 'personal',
        'message_id': call.message.message_id
    }
    
    db.cursor.execute("""
        UPDATE users
        SET platform_connections = %s::jsonb
        WHERE id = %s
    """, (json.dumps(connections), user_id))
    db.conn.commit()


print("✅ handlers/platform_connections/vk_direct.py загружен")
