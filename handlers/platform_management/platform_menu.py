# -*- coding: utf-8 -*-
"""
platform_management/platform_menu.py - Главное меню платформы

Содержит:
- Обработчик клика на платформу
- Отображение детального меню платформы
- Навигация к функциям управления
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import json
from datetime import datetime


def register_platform_menu_handlers(bot):
    """Регистрирует обработчики главного меню платформ"""
    
    print("  ├─ platform_menu.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # ОТКРЫТИЕ МЕНЮ ПЛАТФОРМЫ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_action_'))
    def handle_platform_action(call):
        """
        Обработчик клика на платформу в категории
        Формат: platform_action_{platform_type}_{platform_index}_{category_id}
        """
        try:
            parts = call.data.split('_')
            # platform_action_website_0_123
            platform_type = parts[2]  # website, instagram, vk, pinterest, telegram
            platform_index = int(parts[3])  # индекс в массиве
            category_id = int(parts[4])  # ID категории
            
            user_id = call.from_user.id
            
            # Получаем пользователя и его подключения
            user = db.get_user(user_id)
            if not user:
                bot.answer_callback_query(call.id, "❌ Пользователь не найден", show_alert=True)
                return
            
            connections = user.get('platform_connections', {})
            if not isinstance(connections, dict):
                connections = {}
            
            # Получаем конкретную платформу
            platform_data = None
            platform_list = None
            
            if platform_type == 'website':
                platform_list = connections.get('websites', [])
            elif platform_type == 'instagram':
                platform_list = connections.get('instagrams', [])
            elif platform_type == 'vk':
                platform_list = connections.get('vks', [])
            elif platform_type == 'pinterest':
                platform_list = connections.get('pinterests', [])
            elif platform_type == 'telegram':
                platform_list = connections.get('telegrams', [])
            
            if not platform_list or platform_index >= len(platform_list):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform_data = platform_list[platform_index]
            
            # Отображаем меню платформы
            show_platform_menu(
                call,
                platform_type,
                platform_index,
                platform_data,
                category_id,
                user_id
            )
            
        except Exception as e:
            print(f"❌ Ошибка в handle_platform_action: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при открытии платформы", show_alert=True)
    
    
    def show_platform_menu(call, platform_type, platform_index, platform_data, category_id, user_id):
        """Отображает детальное меню платформы"""
        
        # Формируем заголовок в зависимости от типа платформы
        if platform_type == 'website':
            icon = '🌐'
            title = 'Website'
            url = platform_data.get('url', 'Unknown')
            cms = platform_data.get('cms', 'Unknown')
            identifier = url
            
            details = (
                f"🔗 <b>URL:</b> <code>{escape_html(url)}</code>\n"
                f"⚙️ <b>CMS:</b> {cms}\n"
            )
            action_btn_text = "📝 Написать статью"
            action_callback = f"platform_post_website_{platform_index}_{category_id}"
            
        elif platform_type == 'instagram':
            icon = '📸'
            title = 'Instagram'
            username = platform_data.get('username', 'Unknown')
            identifier = f"@{username}"
            
            details = (
                f"👤 <b>Аккаунт:</b> @{escape_html(username)}\n"
            )
            action_btn_text = "📝 Сделать пост"
            action_callback = f"platform_post_instagram_{platform_index}_{category_id}"
            
        elif platform_type == 'vk':
            icon = '💬'
            title = 'ВКонтакте'
            group_name = platform_data.get('group_name', 'Unknown')
            identifier = group_name
            
            details = (
                f"👥 <b>Группа:</b> {escape_html(group_name)}\n"
            )
            action_btn_text = "📝 Сделать пост"
            action_callback = f"platform_post_vk_{platform_index}_{category_id}"
            
        elif platform_type == 'pinterest':
            icon = '📌'
            title = 'Pinterest'
            username = platform_data.get('username', 'Unknown')
            board = platform_data.get('board', 'Unknown')
            identifier = f"@{username}"
            
            details = (
                f"👤 <b>Аккаунт:</b> @{escape_html(username)}\n"
                f"📋 <b>Доска:</b> {escape_html(board)}\n"
            )
            action_btn_text = "📌 Создать пин"
            action_callback = f"platform_post_pinterest_{platform_index}_{category_id}"
            
        elif platform_type == 'telegram':
            icon = '✈️'
            title = 'Telegram'
            channel = platform_data.get('channel', 'Unknown')
            channel_title = platform_data.get('channel_title', channel)
            identifier = f"@{channel}"
            
            details = (
                f"📢 <b>Канал:</b> {escape_html(channel_title)}\n"
                f"🔗 <b>Username:</b> @{escape_html(channel)}\n"
            )
            action_btn_text = "📝 Сделать пост"
            action_callback = f"platform_post_telegram_{platform_index}_{category_id}"
        else:
            # Неизвестный тип
            bot.answer_callback_query(call.id, "❌ Неизвестный тип платформы", show_alert=True)
            return
        
        # Получаем информацию о планировщике (если есть)
        scheduler_info = platform_data.get('scheduler', {})
        scheduler_enabled = scheduler_info.get('enabled', False)
        
        if scheduler_enabled:
            scheduler_status = "🟢 <b>Автопостинг:</b> Включен"
            frequency = scheduler_info.get('frequency', 'daily')
            times = scheduler_info.get('times', [])
            
            freq_names = {
                'daily': 'Ежедневно',
                'twice_daily': '2 раза в день',
                'thrice_daily': '3 раза в день',
                'custom': 'Настроенное'
            }
            
            scheduler_status += f"\n   • Частота: {freq_names.get(frequency, frequency)}"
            if times:
                scheduler_status += f"\n   • Время: {', '.join(times)}"
        else:
            scheduler_status = "⭕ <b>Автопостинг:</b> Выключен"
        
        # Дата подключения
        added_at = platform_data.get('added_at', 'Unknown')
        if added_at and added_at != 'NOW()':
            try:
                if 'T' in added_at:
                    date_obj = datetime.fromisoformat(added_at)
                    added_at = date_obj.strftime('%d.%m.%Y')
            except:
                pass
        
        # Формируем текст меню
        text = (
            f"{icon} <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"{details}"
            f"📅 <b>Подключено:</b> {added_at}\n"
            f"📊 <b>Статус:</b> ✅ Активен\n\n"
            f"{scheduler_status}\n\n"
            f"<i>💡 Выберите действие:</i>"
        )
        
        # Формируем кнопки
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Основное действие (создать пост/статью/пин)
        markup.add(
            types.InlineKeyboardButton(
                action_btn_text,
                callback_data=action_callback
            )
        )
        
        # Планировщик (автопостинг)
        scheduler_btn_text = "⚙️ Планировщик (автопостинг)"
        scheduler_callback = f"platform_scheduler_{platform_type}_{platform_index}_{category_id}"
        markup.add(
            types.InlineKeyboardButton(
                scheduler_btn_text,
                callback_data=scheduler_callback
            )
        )
        
        # Настройки подключения
        settings_btn_text = "🔧 Настройки подключения"
        settings_callback = f"platform_settings_{platform_type}_{platform_index}_{category_id}"
        markup.add(
            types.InlineKeyboardButton(
                settings_btn_text,
                callback_data=settings_callback
            )
        )
        
        # Удаление
        delete_btn_text = "🗑 Удалить подключение"
        delete_callback = f"platform_delete_confirm_{platform_type}_{platform_index}_{category_id}"
        markup.add(
            types.InlineKeyboardButton(
                delete_btn_text,
                callback_data=delete_callback
            )
        )
        
        # Назад к категориям
        markup.add(
            types.InlineKeyboardButton(
                "🔙 К категориям",
                callback_data=f"manage_subproject_{category_id}"
            )
        )
        
        # Отправляем или редактируем сообщение
        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"⚠️ Не удалось отредактировать сообщение: {e}")
            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        
        bot.answer_callback_query(call.id)
    
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГЛУШКИ ДЛЯ БУДУЩИХ ФУНКЦИЙ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_post_'))
    def handle_platform_post(call):
        """Заглушка для создания поста (будет реализовано позже)"""
        bot.answer_callback_query(
            call.id,
            "🚧 Функция создания постов будет добавлена в следующем этапе",
            show_alert=True
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_scheduler_'))
    def handle_platform_scheduler(call):
        """Заглушка для планировщика (будет реализовано позже)"""
        bot.answer_callback_query(
            call.id,
            "🚧 Планировщик будет добавлен в следующих этапах",
            show_alert=True
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_settings_'))
    def handle_platform_settings(call):
        """Заглушка для настроек (будет реализовано позже)"""
        bot.answer_callback_query(
            call.id,
            "🚧 Настройки подключения будут добавлены позже",
            show_alert=True
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_delete_confirm_'))
    def handle_platform_delete(call):
        """Подтверждение удаления платформы"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            # Получаем информацию о платформе для подтверждения
            user_id = call.from_user.id
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            
            platform_list = connections.get(f"{platform_type}s", [])
            if platform_index >= len(platform_list):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform_data = platform_list[platform_index]
            
            # Формируем название платформы для подтверждения
            if platform_type == 'website':
                platform_name = platform_data.get('url', 'Unknown')
            elif platform_type in ['instagram', 'pinterest']:
                platform_name = f"@{platform_data.get('username', 'Unknown')}"
            elif platform_type == 'vk':
                platform_name = platform_data.get('group_name', 'Unknown')
            elif platform_type == 'telegram':
                platform_name = f"@{platform_data.get('channel', 'Unknown')}"
            else:
                platform_name = 'Unknown'
            
            text = (
                f"⚠️ <b>УДАЛЕНИЕ ПОДКЛЮЧЕНИЯ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"Вы действительно хотите удалить подключение?\n\n"
                f"<b>Платформа:</b> {escape_html(platform_name)}\n\n"
                f"⚠️ <b>Это действие нельзя отменить!</b>\n"
                f"Все настройки планировщика будут удалены."
            )
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    "✅ Да, удалить",
                    callback_data=f"platform_delete_execute_{platform_type}_{platform_index}_{category_id}"
                ),
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_action_{platform_type}_{platform_index}_{category_id}"
                )
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_platform_delete: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_delete_execute_'))
    def execute_platform_delete(call):
        """Выполняет удаление платформы"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            user_id = call.from_user.id
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            
            if not isinstance(connections, dict):
                connections = {}
            
            # Определяем ключ в connections
            key_map = {
                'website': 'websites',
                'instagram': 'instagrams',
                'vk': 'vks',
                'pinterest': 'pinterests',
                'telegram': 'telegrams'
            }
            
            platform_key = key_map.get(platform_type)
            if not platform_key:
                bot.answer_callback_query(call.id, "❌ Неизвестный тип платформы", show_alert=True)
                return
            
            platform_list = connections.get(platform_key, [])
            
            if platform_index >= len(platform_list):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            # Удаляем платформу
            deleted_platform = platform_list.pop(platform_index)
            connections[platform_key] = platform_list
            
            # Сохраняем в БД
            db.cursor.execute("""
                UPDATE users 
                SET platform_connections = %s::jsonb
                WHERE id = %s
            """, (json.dumps(connections), user_id))
            db.conn.commit()
            
            # Получаем название для уведомления
            if platform_type == 'website':
                platform_name = deleted_platform.get('url', 'Unknown')
            elif platform_type in ['instagram', 'pinterest']:
                platform_name = f"@{deleted_platform.get('username', 'Unknown')}"
            elif platform_type == 'vk':
                platform_name = deleted_platform.get('group_name', 'Unknown')
            elif platform_type == 'telegram':
                platform_name = f"@{deleted_platform.get('channel', 'Unknown')}"
            else:
                platform_name = 'Unknown'
            
            text = (
                f"✅ <b>ПОДКЛЮЧЕНИЕ УДАЛЕНО</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"Платформа успешно отключена:\n"
                f"<b>{escape_html(platform_name)}</b>\n\n"
                f"Вы можете подключить её снова в любое время."
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 К категориям",
                    callback_data=f"manage_subproject_{category_id}"
                )
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.answer_callback_query(call.id, "✅ Удалено")
            
        except Exception as e:
            print(f"❌ Ошибка в execute_platform_delete: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при удалении", show_alert=True)


# Экспорт
__all__ = ['register_platform_menu_handlers']
