# -*- coding: utf-8 -*-
"""
Обработка VK токенов от пользователей
"""
from telebot import types
from loader import bot, db
import requests
import json
import re


@bot.message_handler(func=lambda message: check_vk_token_awaiting(message))
def handle_vk_token_input(message):
    """
    Обработка токена от пользователя
    """
    user_id = message.from_user.id
    token = message.text.strip()
    
    # Удаляем сообщение с токеном для безопасности
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    # Проверяем формат токена
    if not token.startswith('vk1.'):
        bot.send_message(
            user_id,
            "❌ Неверный формат токена!\n\n"
            "Токен должен начинаться с <code>vk1.a.</code> или <code>vk1.g.</code>\n\n"
            "Попробуйте ещё раз.",
            parse_mode='HTML'
        )
        return
    
    # Проверяем валидность токена
    try:
        # Проверяем токен через API
        response = requests.get(
            "https://api.vk.com/method/users.get",
            params={
                "access_token": token,
                "v": "5.131",
                "fields": "photo_200"
            },
            timeout=10
        )
        
        result = response.json()
        
        if 'error' in result:
            error_msg = result['error'].get('error_msg', 'Unknown error')
            bot.send_message(
                user_id,
                f"❌ Ошибка проверки токена:\n\n"
                f"<code>{error_msg}</code>\n\n"
                f"Проверьте правильность токена и попробуйте снова.",
                parse_mode='HTML'
            )
            return
        
        vk_user = result['response'][0]
        vk_user_id = str(vk_user['id'])
        vk_name = f"{vk_user.get('first_name', '')} {vk_user.get('last_name', '')}".strip()
        
        print(f"✅ VK токен валиден: User {vk_user_id} ({vk_name})")
        
        # Получаем список групп
        groups_response = requests.get(
            "https://api.vk.com/method/groups.get",
            params={
                "access_token": token,
                "v": "5.131",
                "filter": "admin,editor",
                "extended": 1,
                "fields": "members_count,photo_200"
            },
            timeout=10
        )
        
        groups_result = groups_response.json()
        
        user_groups = []
        if 'response' in groups_result and 'items' in groups_result['response']:
            for group in groups_result['response']['items']:
                user_groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'screen_name': group.get('screen_name', ''),
                    'photo_200': group.get('photo_200', ''),
                    'members_count': group.get('members_count', 0)
                })
        
        print(f"📝 Найдено групп: {len(user_groups)}")
        
        # Сохраняем временные данные для выбора
        user = db.get_user(user_id)
        connections = user.get('platform_connections', {})
        if isinstance(connections, str):
            connections = json.loads(connections)
        
        # Получаем тип токена
        token_type = connections.get('_vk_awaiting_token', {}).get('type', 'personal')
        
        connections['_vk_selection_pending'] = {
            'access_token': token,
            'refresh_token': None,
            'device_id': None,
            'expires_in': 0,  # Бессрочный
            'user_id': vk_user_id,
            'email': None,
            'available_groups': user_groups,
            'token_type': token_type
        }
        
        # Удаляем флаг ожидания
        if '_vk_awaiting_token' in connections:
            del connections['_vk_awaiting_token']
        
        db.cursor.execute("""
            UPDATE users
            SET platform_connections = %s::jsonb
            WHERE id = %s
        """, (json.dumps(connections), user_id))
        db.conn.commit()
        
        # Отправляем меню выбора
        message_text = (
            "✅ <b>Токен проверен успешно!</b>\n\n"
            f"👤 VK: {vk_name}\n"
            f"📝 Доступно групп: {len(user_groups)}\n\n"
            "Выберите что хотите подключить:"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Для токена сообщества показываем только группы
        if token_type == 'group':
            # Кнопки только для групп
            for idx, group in enumerate(user_groups[:10]):
                group_name = group['name']
                members = group.get('members_count', 0)
                members_text = f" ({members:,} подписчиков)" if members > 0 else ""
                
                markup.add(
                    types.InlineKeyboardButton(
                        f"📝 {group_name}{members_text}",
                        callback_data=f"vk_select_group_{user_id}_{idx}"
                    )
                )
            
            if len(user_groups) == 0:
                markup.add(
                    types.InlineKeyboardButton(
                        "◀️ Назад",
                        callback_data="add_platform_vk"
                    )
                )
                message_text = (
                    "⚠️ <b>Группы не найдены</b>\n\n"
                    "Токен сообщества действует только для одной группы.\n"
                    "Убедитесь что вы скопировали токен из настроек нужной группы."
                )
        else:
            # Для личного токена - и личная страница и группы
            markup.add(
                types.InlineKeyboardButton(
                    f"👤 {vk_name}",
                    callback_data=f"vk_select_user_{user_id}"
                )
            )
            
            for idx, group in enumerate(user_groups[:10]):
                group_name = group['name']
                members = group.get('members_count', 0)
                members_text = f" ({members:,} подписчиков)" if members > 0 else ""
                
                markup.add(
                    types.InlineKeyboardButton(
                        f"📝 {group_name}{members_text}",
                        callback_data=f"vk_select_group_{user_id}_{idx}"
                    )
                )
        
        # Кнопка отмены
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"vk_select_cancel_{user_id}"
            )
        )
        
        bot.send_message(
            user_id,
            message_text,
            parse_mode='HTML',
            reply_markup=markup
        )
        
    except Exception as e:
        print(f"❌ Ошибка обработки токена: {e}")
        import traceback
        traceback.print_exc()
        
        bot.send_message(
            user_id,
            f"❌ Ошибка при проверке токена:\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Попробуйте получить токен заново.",
            parse_mode='HTML'
        )


def check_vk_token_awaiting(message):
    """
    Проверяет ожидает ли бот VK токен от пользователя
    """
    if not message.text:
        return False
    
    user_id = message.from_user.id
    
    try:
        user = db.get_user(user_id)
        connections = user.get('platform_connections', {})
        if isinstance(connections, str):
            connections = json.loads(connections)
        
        return '_vk_awaiting_token' in connections
    except:
        return False


print("✅ handlers/platform_connections/vk_token_input.py загружен")
