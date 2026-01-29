"""
Обработка выбора VK профиля или группы после OAuth
"""
from telebot import types
from loader import bot, db
import json
import time


@bot.callback_query_handler(func=lambda call: call.data.startswith('vk_select_'))
def handle_vk_selection(call):
    """
    Обработчик выбора VK профиля или группы
    
    Callback data:
    - vk_select_user_{user_id} - выбор личной страницы
    - vk_select_group_{user_id}_{group_index} - выбор группы
    - vk_select_cancel_{user_id} - отмена
    """
    user_id = call.from_user.id
    
    try:
        # Получаем пользователя и временные данные
        user = db.get_user(user_id)
        
        if not user:
            bot.answer_callback_query(call.id, "❌ Пользователь не найден")
            return
        
        connections = user.get('platform_connections', {})
        if isinstance(connections, str):
            connections = json.loads(connections)
        
        # Проверяем наличие временных данных выбора
        pending_data = connections.get('_vk_selection_pending')
        
        if not pending_data:
            bot.answer_callback_query(call.id, "❌ Данные выбора не найдены. Попробуйте подключить VK заново.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
        
        # ============================================
        # ОБРАБОТКА ОТМЕНЫ
        # ============================================
        
        if call.data.startswith('vk_select_cancel_'):
            # Удаляем временные данные
            del connections['_vk_selection_pending']
            
            db.cursor.execute("""
                UPDATE users
                SET platform_connections = %s::jsonb
                WHERE id = %s
            """, (json.dumps(connections), user_id))
            db.conn.commit()
            
            bot.answer_callback_query(call.id, "❌ Подключение отменено")
            bot.edit_message_text(
                "❌ Подключение VK отменено.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # ============================================
        # ОБРАБОТКА ВЫБОРА
        # ============================================
        
        # Парсим callback data
        parts = call.data.split('_')
        selection_type = parts[2]  # 'user' или 'group'
        
        # Получаем данные для сохранения
        access_token = pending_data['access_token']
        refresh_token = pending_data.get('refresh_token')
        device_id = pending_data.get('device_id')
        expires_in = pending_data.get('expires_in', 86400)
        vk_user_id = pending_data['user_id']
        email = pending_data.get('email')
        available_groups = pending_data.get('available_groups', [])
        
        # Импортируем VKOAuth для получения информации
        from handlers.vk_integration.vk_oauth import VKOAuth
        
        # Получаем информацию о пользователе VK
        vk_user_info = VKOAuth.get_user_info(access_token, vk_user_id)
        
        if not vk_user_info:
            bot.answer_callback_query(call.id, "❌ Не удалось получить информацию VK")
            return
        
        # Вычисляем время истечения токена
        expires_at = int(time.time()) + expires_in
        
        # Инициализируем массив VK подключений
        if 'vks' not in connections:
            connections['vks'] = []
        
        vks = connections['vks']
        if not isinstance(vks, list):
            vks = []
        
        # ============================================
        # ВЫБОР ЛИЧНОЙ СТРАНИЦЫ
        # ============================================
        
        if selection_type == 'user':
            # Проверка глобальной уникальности
            db.cursor.execute("""
                SELECT u.id, u.username
                FROM users u
                WHERE u.platform_connections::text LIKE %s
            """, (f'%"user_id": "{vk_user_id}"%',))
            
            existing_users = db.cursor.fetchall()
            
            if existing_users:
                for existing_user in existing_users:
                    existing_user_id = existing_user.get('id') if isinstance(existing_user, dict) else existing_user[0]
                    
                    if existing_user_id != user_id:
                        bot.answer_callback_query(call.id, "❌ Эта страница уже подключена у другого пользователя")
                        return
            
            # Проверка у текущего пользователя
            for existing_vk in vks:
                if existing_vk.get('user_id') == vk_user_id and existing_vk.get('type') == 'user':
                    bot.answer_callback_query(call.id, "❌ Эта страница уже подключена")
                    return
            
            # Создаём подключение личной страницы
            vk_connection = {
                'type': 'user',
                'user_id': vk_user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'device_id': device_id,
                'expires_at': expires_at,
                'email': email,
                'first_name': vk_user_info.get('first_name'),
                'last_name': vk_user_info.get('last_name'),
                'photo': vk_user_info.get('photo_200'),
                'status': 'active',
                'connected_at': 'now()',
                'group_name': f"{vk_user_info.get('first_name', '')} {vk_user_info.get('last_name', '')}".strip()
            }
            
            vks.append(vk_connection)
            
            bot.answer_callback_query(call.id, "✅ Личная страница подключена!")
            success_text = f"✅ Подключена личная страница VK:\n👤 {vk_connection['group_name']}"
        
        # ============================================
        # ВЫБОР ГРУППЫ
        # ============================================
        
        elif selection_type == 'group':
            # Получаем индекс группы
            group_index = int(parts[4])
            
            if group_index >= len(available_groups):
                bot.answer_callback_query(call.id, "❌ Группа не найдена")
                return
            
            selected_group = available_groups[group_index]
            group_id = selected_group['id']
            
            # Проверка глобальной уникальности
            db.cursor.execute("""
                SELECT u.id, u.username
                FROM users u
                WHERE u.platform_connections::text LIKE %s
            """, (f'%"group_id": {group_id}%',))
            
            existing_users = db.cursor.fetchall()
            
            if existing_users:
                for existing_user in existing_users:
                    existing_user_id = existing_user.get('id') if isinstance(existing_user, dict) else existing_user[0]
                    
                    if existing_user_id != user_id:
                        bot.answer_callback_query(call.id, "❌ Эта группа уже подключена у другого пользователя")
                        return
            
            # Проверка у текущего пользователя
            for existing_vk in vks:
                if existing_vk.get('group_id') == group_id:
                    bot.answer_callback_query(call.id, "❌ Эта группа уже подключена")
                    return
            
            # Создаём подключение группы
            vk_connection = {
                'type': 'group',
                'user_id': vk_user_id,  # ID владельца токена
                'group_id': -group_id,  # ОТРИЦАТЕЛЬНЫЙ для VK API!
                'access_token': access_token,
                'refresh_token': refresh_token,
                'device_id': device_id,
                'expires_at': expires_at,
                'email': email,
                'first_name': vk_user_info.get('first_name'),
                'last_name': vk_user_info.get('last_name'),
                'photo': selected_group.get('photo_200'),
                'status': 'active',
                'connected_at': 'now()',
                'group_name': selected_group['name'],
                'screen_name': selected_group.get('screen_name', ''),
                'members_count': selected_group.get('members_count', 0)
            }
            
            vks.append(vk_connection)
            
            members_text = f" ({vk_connection['members_count']:,} подписчиков)" if vk_connection['members_count'] > 0 else ""
            bot.answer_callback_query(call.id, "✅ Группа подключена!")
            success_text = f"✅ Подключена группа VK:\n📝 {vk_connection['group_name']}{members_text}"
        
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестный тип выбора")
            return
        
        # ============================================
        # СОХРАНЕНИЕ В БД
        # ============================================
        
        connections['vks'] = vks
        
        # Удаляем временные данные
        if '_vk_selection_pending' in connections:
            del connections['_vk_selection_pending']
        
        db.cursor.execute("""
            UPDATE users
            SET platform_connections = %s::jsonb
            WHERE id = %s
        """, (json.dumps(connections), user_id))
        db.conn.commit()
        
        print(f"✅ VK подключение сохранено для пользователя {user_id}")
        print(f"   Тип: {vk_connection['type']}")
        print(f"   Название: {vk_connection['group_name']}")
        
        # Обновляем сообщение
        bot.edit_message_text(
            success_text + "\n\n💡 Можете подключить еще группы через 'Добавить площадку'",
            call.message.chat.id,
            call.message.message_id
        )
        
    except Exception as e:
        print(f"❌ Ошибка обработки выбора VK: {e}")
        import traceback
        traceback.print_exc()
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}")


print("✅ handlers/platform_connections/vk_selection.py загружен")
