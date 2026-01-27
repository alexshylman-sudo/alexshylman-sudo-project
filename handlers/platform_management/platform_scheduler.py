# -*- coding: utf-8 -*-
"""
platform_management/platform_scheduler.py - Планировщик автопостинга

Содержит:
- Универсальный планировщик для всех платформ
- Настройка частоты публикаций
- Настройка времени публикаций
- Включение/выключение автопостинга
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import json
from datetime import datetime


def register_platform_scheduler_handlers(bot):
    """Регистрирует обработчики планировщика"""
    
    print("  ├─ platform_scheduler.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # ОТКРЫТИЕ ПЛАНИРОВЩИКА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_scheduler_'))
    def handle_platform_scheduler(call):
        """Обработчик открытия планировщика"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]  # website, instagram, vk, pinterest, telegram
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем данные платформы
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            
            # Получаем нужную платформу
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Показываем меню планировщика
            show_scheduler_menu(call, platform, platform_type, platform_index, category_id, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_platform_scheduler: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def get_platform_key(platform_type):
        """Возвращает ключ для platform_connections"""
        mapping = {
            'website': 'websites',
            'instagram': 'instagrams',
            'vk': 'vks',
            'pinterest': 'pinterests',
            'telegram': 'telegrams'
        }
        return mapping.get(platform_type, 'websites')
    
    
    def get_platform_emoji(platform_type):
        """Возвращает emoji для платформы"""
        emojis = {
            'website': '🌐',
            'instagram': '📸',
            'vk': '💬',
            'pinterest': '📌',
            'telegram': '✈️'
        }
        return emojis.get(platform_type, '📱')
    
    
    def get_platform_name(platform, platform_type):
        """Возвращает название платформы"""
        if platform_type == 'website':
            return platform.get('url', 'Unknown')
        elif platform_type == 'instagram':
            return f"@{platform.get('username', 'unknown')}"
        elif platform_type == 'vk':
            return platform.get('group_name', 'Unknown')
        elif platform_type == 'pinterest':
            return f"@{platform.get('username', 'unknown')}"
        elif platform_type == 'telegram':
            return platform.get('channel_title', 'Unknown')
        return 'Unknown'
    
    
    def show_scheduler_menu(call, platform, platform_type, platform_index, category_id, subproject):
        """Показывает меню планировщика"""
        
        platform_emoji = get_platform_emoji(platform_type)
        platform_name = get_platform_name(platform, platform_type)
        category_name = subproject.get('name', 'Unknown')
        
        # Получаем текущие настройки планировщика
        scheduler = platform.get('scheduler', {})
        is_enabled = scheduler.get('enabled', False)
        frequency = scheduler.get('frequency', 'daily')
        times = scheduler.get('times', ['10:00'])
        
        # Определяем текст частоты
        frequency_text = get_frequency_text(frequency)
        times_text = ", ".join(times) if times else "Не настроено"
        
        # Базовый текст
        text = (
            f"📅 <b>ПЛАНИРОВЩИК АВТОПОСТИНГА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"{platform_emoji} <b>Платформа:</b> {escape_html(platform_name)}\n"
            f"📦 <b>Категория:</b> {escape_html(category_name)}\n\n"
            f"<b>📊 Текущие настройки:</b>\n"
            f"• Статус: {'✅ Включён' if is_enabled else '⭕ Выключен'}\n"
            f"• Частота: {frequency_text}\n"
            f"• Время: {times_text}\n"
        )
        
        # Добавляем информацию о топиках для Telegram
        if platform_type.lower() == 'telegram':
            telegram_topics = subproject.get('telegram_topics', [])
            if not isinstance(telegram_topics, list):
                telegram_topics = []
            
            selected_topics = scheduler.get('selected_topics', [])
            if not isinstance(selected_topics, list):
                selected_topics = []
            
            if telegram_topics:
                if selected_topics:
                    text += f"• Топики: {len(selected_topics)} выбрано\n"
                else:
                    text += f"• Топики: В основной чат\n"
            else:
                text += f"• Топики: Не настроены\n"
        
        # Добавляем информацию о досках для Pinterest
        if platform_type.lower() == 'pinterest':
            settings = subproject.get('settings', {})
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except:
                    settings = {}
            
            selected_boards = settings.get('pinterest_boards', [])
            if not isinstance(selected_boards, list):
                selected_boards = []
            
            if selected_boards:
                text += f"• Доски: {len(selected_boards)} выбрано\n"
            else:
                text += f"• Доски: Все доски\n"
        
        text += f"\n<i>💡 Выберите действие:</i>"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Кнопка включения/выключения
        if is_enabled:
            markup.add(
                types.InlineKeyboardButton(
                    "🔴 Выключить автопостинг",
                    callback_data=f"sched_toggle_{platform_type}_{platform_index}_{category_id}_off"
                )
            )
        else:
            markup.add(
                types.InlineKeyboardButton(
                    "🟢 Включить автопостинг",
                    callback_data=f"sched_toggle_{platform_type}_{platform_index}_{category_id}_on"
                )
            )
        
        # Настройка частоты
        markup.add(
            types.InlineKeyboardButton(
                "📊 Настроить частоту",
                callback_data=f"sched_frequency_{platform_type}_{platform_index}_{category_id}"
            )
        )
        
        # Настройка времени
        markup.add(
            types.InlineKeyboardButton(
                "🕐 Настроить время",
                callback_data=f"sched_times_{platform_type}_{platform_index}_{category_id}"
            )
        )
        
        # Выбор топиков для Telegram
        if platform_type.lower() == 'telegram':
            telegram_topics = subproject.get('telegram_topics', [])
            if not isinstance(telegram_topics, list):
                telegram_topics = []
            
            if telegram_topics:
                markup.add(
                    types.InlineKeyboardButton(
                        "📡 Выбор топиков",
                        callback_data=f"sched_topics_{platform_type}_{platform_index}_{category_id}"
                    )
                )
            else:
                markup.add(
                    types.InlineKeyboardButton(
                        "⚠️ Топики не настроены",
                        callback_data=f"sched_topics_warning_{platform_type}_{platform_index}_{category_id}"
                    )
                )
        
        # Выбор досок для Pinterest
        if platform_type.lower() == 'pinterest':
            markup.add(
                types.InlineKeyboardButton(
                    "📋 Выбор досок",
                    callback_data=f"sched_boards_{platform_type}_{platform_index}_{category_id}"
                )
            )
        
        # Назад
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
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
    
    
    def get_frequency_text(frequency):
        """Возвращает текстовое описание частоты"""
        mapping = {
            'daily': '📅 Ежедневно (1 раз)',
            'twice_daily': '📅 2 раза в день',
            'thrice_daily': '📅 3 раза в день',
            'custom': '⚙️ Настраиваемая',
            'weekly': '📅 Еженедельно',
            'twice_weekly': '📅 2 раза в неделю',
            'thrice_weekly': '📅 3 раза в неделю'
        }
        return mapping.get(frequency, '❓ Не настроено')
    
    
    # ═══════════════════════════════════════════════════════════════
    # ВКЛЮЧЕНИЕ/ВЫКЛЮЧЕНИЕ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_toggle_'))
    def handle_scheduler_toggle(call):
        """Включение/выключение планировщика"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            action = parts[5]  # on / off
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {
                    'enabled': False,
                    'frequency': 'daily',
                    'times': ['10:00']
                }
            
            # Переключаем статус
            new_status = (action == 'on')
            platform['scheduler']['enabled'] = new_status
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            # Показываем уведомление
            status_text = "включён ✅" if new_status else "выключен ⭕"
            bot.answer_callback_query(call.id, f"Автопостинг {status_text}", show_alert=True)
            
            # Обновляем меню
            subproject = db.get_subproject(category_id)
            show_scheduler_menu(call, platform, platform_type, platform_index, category_id, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_toggle: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    # ═══════════════════════════════════════════════════════════════
    # НАСТРОЙКА ЧАСТОТЫ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_frequency_'))
    def handle_scheduler_frequency(call):
        """Настройка частоты публикаций"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            text = (
                f"📊 <b>НАСТРОЙКА ЧАСТОТЫ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"Выберите как часто публиковать посты:\n\n"
                f"<i>💡 Время публикации настроите на следующем шаге</i>"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            # Варианты частоты
            markup.add(
                types.InlineKeyboardButton(
                    "📅 Ежедневно (1 раз)",
                    callback_data=f"sched_setfreq_{platform_type}_{platform_index}_{category_id}_daily"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "📅 2 раза в день",
                    callback_data=f"sched_setfreq_{platform_type}_{platform_index}_{category_id}_twice_daily"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "📅 3 раза в день",
                    callback_data=f"sched_setfreq_{platform_type}_{platform_index}_{category_id}_thrice_daily"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "📅 Еженедельно",
                    callback_data=f"sched_setfreq_{platform_type}_{platform_index}_{category_id}_weekly"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "📅 2 раза в неделю",
                    callback_data=f"sched_setfreq_{platform_type}_{platform_index}_{category_id}_twice_weekly"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "📅 3 раза в неделю",
                    callback_data=f"sched_setfreq_{platform_type}_{platform_index}_{category_id}_thrice_weekly"
                )
            )
            
            # Назад
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_scheduler_{platform_type}_{platform_index}_{category_id}"
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
            print(f"❌ Ошибка в handle_scheduler_frequency: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_setfreq_'))
    def handle_set_frequency(call):
        """Сохранение частоты"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            frequency = parts[5]
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {}
            
            # Сохраняем частоту
            platform['scheduler']['frequency'] = frequency
            
            # Устанавливаем время по умолчанию в зависимости от частоты
            if frequency == 'daily':
                platform['scheduler']['times'] = ['10:00']
            elif frequency == 'twice_daily':
                platform['scheduler']['times'] = ['10:00', '18:00']
            elif frequency == 'thrice_daily':
                platform['scheduler']['times'] = ['09:00', '14:00', '19:00']
            elif frequency == 'weekly':
                platform['scheduler']['times'] = ['10:00']
                platform['scheduler']['weekday'] = 1  # Понедельник
            elif frequency == 'twice_weekly':
                platform['scheduler']['times'] = ['10:00']
                platform['scheduler']['weekdays'] = [1, 4]  # Пн, Чт
            elif frequency == 'thrice_weekly':
                platform['scheduler']['times'] = ['10:00']
                platform['scheduler']['weekdays'] = [1, 3, 5]  # Пн, Ср, Пт
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            bot.answer_callback_query(call.id, "✅ Частота сохранена", show_alert=True)
            
            # Возвращаемся в меню планировщика
            subproject = db.get_subproject(category_id)
            show_scheduler_menu(call, platform, platform_type, platform_index, category_id, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_set_frequency: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    # ═══════════════════════════════════════════════════════════════
    # НАСТРОЙКА ВРЕМЕНИ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_times_'))
    def handle_scheduler_times(call):
        """Настройка времени публикаций"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            scheduler = platform.get('scheduler', {})
            frequency = scheduler.get('frequency', 'daily')
            current_times = scheduler.get('times', ['10:00'])
            
            frequency_text = get_frequency_text(frequency)
            times_text = ", ".join(current_times)
            
            text = (
                f"🕐 <b>НАСТРОЙКА ВРЕМЕНИ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"<b>Частота:</b> {frequency_text}\n"
                f"<b>Текущее время:</b> {times_text}\n\n"
                f"Выберите время публикации:\n\n"
                f"<i>💡 Доступные варианты зависят от частоты</i>"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=3)
            
            # Популярные варианты времени
            time_options = [
                ('09:00', '🌅'), ('10:00', '☀️'), ('12:00', '🌞'),
                ('14:00', '📆'), ('16:00', '🌤'), ('18:00', '🌆'),
                ('19:00', '🌇'), ('20:00', '🌃'), ('21:00', '🌙')
            ]
            
            buttons = []
            for time, emoji in time_options:
                buttons.append(
                    types.InlineKeyboardButton(
                        f"{emoji} {time}",
                        callback_data=f"sched_settime_{platform_type}_{platform_index}_{category_id}_{time.replace(':', '')}"
                    )
                )
            
            # Добавляем по 3 кнопки в ряд
            for i in range(0, len(buttons), 3):
                markup.add(*buttons[i:i+3])
            
            # Назад
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_scheduler_{platform_type}_{platform_index}_{category_id}"
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
            print(f"❌ Ошибка в handle_scheduler_times: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_settime_'))
    def handle_set_time(call):
        """Сохранение времени"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            time_str = parts[5]  # Формат: 0900, 1400, etc
            
            # Преобразуем в формат HH:MM
            time_formatted = f"{time_str[:2]}:{time_str[2:]}"
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {}
            
            frequency = platform['scheduler'].get('frequency', 'daily')
            
            # Устанавливаем время в зависимости от частоты
            if frequency == 'daily' or frequency.endswith('weekly'):
                platform['scheduler']['times'] = [time_formatted]
            elif frequency == 'twice_daily':
                # Устанавливаем выбранное время как первое, второе - через 8 часов
                hour = int(time_str[:2])
                second_hour = (hour + 8) % 24
                second_time = f"{second_hour:02d}:00"
                platform['scheduler']['times'] = [time_formatted, second_time]
            elif frequency == 'thrice_daily':
                # Три раза: выбранное, через 5 часов, через 10 часов
                hour = int(time_str[:2])
                second_hour = (hour + 5) % 24
                third_hour = (hour + 10) % 24
                platform['scheduler']['times'] = [
                    time_formatted,
                    f"{second_hour:02d}:00",
                    f"{third_hour:02d}:00"
                ]
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            bot.answer_callback_query(call.id, f"✅ Время установлено: {time_formatted}", show_alert=True)
            
            # Возвращаемся в меню планировщика
            subproject = db.get_subproject(category_id)
            show_scheduler_menu(call, platform, platform_type, platform_index, category_id, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_set_time: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    # ═══════════════════════════════════════════════════════════════
    # ВЫБОР ТОПИКОВ ДЛЯ TELEGRAM
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_topics_warning_'))
    def handle_scheduler_topics_warning(call):
        """Предупреждение о ненастроенных топиках"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            bot.answer_callback_query(
                call.id,
                "⚠️ Топики не настроены!\n\nСначала настройте их в разделе 'Настройка топиков'",
                show_alert=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_topics_warning: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_topics_'))
    def handle_scheduler_topics(call):
        """Выбор топиков для публикации в планировщике"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            category_name = subproject.get('name', 'Unknown')
            
            # Получаем топики категории
            telegram_topics = subproject.get('telegram_topics', [])
            if not isinstance(telegram_topics, list):
                telegram_topics = []
            
            if not telegram_topics:
                bot.answer_callback_query(
                    call.id,
                    "⚠️ Топики не настроены!\n\nСначала настройте их в разделе 'Настройка топиков'",
                    show_alert=True
                )
                return
            
            # Получаем выбранные топики из планировщика
            scheduler = platform.get('scheduler', {})
            selected_topics = scheduler.get('selected_topics', [])
            if not isinstance(selected_topics, list):
                selected_topics = []
            
            # Текст
            if selected_topics:
                selected_text = f"Выбрано: {len(selected_topics)} топик(ов)"
            else:
                selected_text = "Публикация в основной чат (без топиков)"
            
            text = (
                f"📡 <b>ВЫБОР ТОПИКОВ</b>\n"
                f"📂 Категория: {escape_html(category_name)}\n"
                "━━━━━━━━━━━━━━\n\n"
                f"<b>{selected_text}</b>\n\n"
                "Выберите топики для автопостинга.\n"
                "Если ничего не выбрано - публикация в основной чат.\n\n"
                "💡 <b>Доступные топики:</b>"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            # Кнопки топиков
            for topic in telegram_topics:
                topic_id = topic.get('topic_id')
                topic_name = topic.get('topic_name', 'Без названия')
                
                is_selected = topic_id in selected_topics
                button_text = f"✅ {topic_name}" if is_selected else f"☐ {topic_name}"
                
                markup.add(
                    types.InlineKeyboardButton(
                        button_text,
                        callback_data=f"sched_topic_toggle_{platform_type}_{platform_index}_{category_id}_{topic_id}"
                    )
                )
            
            # Специальная опция - публикация в основной чат
            is_main_selected = len(selected_topics) == 0
            markup.add(
                types.InlineKeyboardButton(
                    "📤 В основной чат (без топика)" if is_main_selected else "☐ В основной чат (без топика)",
                    callback_data=f"sched_topic_main_{platform_type}_{platform_index}_{category_id}"
                )
            )
            
            # Кнопки управления
            markup.row(
                types.InlineKeyboardButton(
                    "☑️ Все топики",
                    callback_data=f"sched_topics_all_{platform_type}_{platform_index}_{category_id}"
                ),
                types.InlineKeyboardButton(
                    "❌ Сбросить",
                    callback_data=f"sched_topics_clear_{platform_type}_{platform_index}_{category_id}"
                )
            )
            
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_scheduler_{platform_type}_{platform_index}_{category_id}"
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
            print(f"❌ Ошибка в handle_scheduler_topics: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_topic_toggle_'))
    def handle_scheduler_topic_toggle(call):
        """Переключение выбора топика"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            topic_id = int(parts[6])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {}
            
            # Получаем выбранные топики
            selected_topics = platform['scheduler'].get('selected_topics', [])
            if not isinstance(selected_topics, list):
                selected_topics = []
            
            # Переключаем
            if topic_id in selected_topics:
                selected_topics.remove(topic_id)
            else:
                selected_topics.append(topic_id)
            
            # Сохраняем
            platform['scheduler']['selected_topics'] = selected_topics
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            bot.answer_callback_query(call.id)
            
            # Обновляем интерфейс
            call.data = f"sched_topics_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_topics(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_topic_toggle: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_topic_main_'))
    def handle_scheduler_topic_main(call):
        """Публикация в основной чат (без топика)"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {}
            
            # Очищаем выбор топиков (публикация в основной чат)
            platform['scheduler']['selected_topics'] = []
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            bot.answer_callback_query(call.id, "✅ Публикация в основной чат")
            
            # Обновляем интерфейс
            call.data = f"sched_topics_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_topics(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_topic_main: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_topics_all_'))
    def handle_scheduler_topics_all(call):
        """Выбрать все топики"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Получаем все топики категории
            telegram_topics = subproject.get('telegram_topics', [])
            if not isinstance(telegram_topics, list):
                telegram_topics = []
            
            # Собираем все ID топиков
            all_topic_ids = [topic.get('topic_id') for topic in telegram_topics if topic.get('topic_id')]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {}
            
            # Сохраняем все топики
            platform['scheduler']['selected_topics'] = all_topic_ids
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            bot.answer_callback_query(call.id, "✅ Выбраны все топики")
            
            # Обновляем интерфейс
            call.data = f"sched_topics_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_topics(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_topics_all: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_topics_clear_'))
    def handle_scheduler_topics_clear(call):
        """Сбросить выбор топиков"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Инициализируем scheduler если его нет
            if 'scheduler' not in platform:
                platform['scheduler'] = {}
            
            # Очищаем выбор
            platform['scheduler']['selected_topics'] = []
            
            # Обновляем в БД
            platforms[platform_index] = platform
            connections[platform_key] = platforms
            
            db.execute(
                "UPDATE users SET platform_connections = %s WHERE telegram_id = %s",
                (json.dumps(connections), user_id)
            )
            
            bot.answer_callback_query(call.id, "✅ Публикация в основной чат")
            
            # Обновляем интерфейс
            call.data = f"sched_topics_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_topics(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_topics_clear: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    # ═══════════════════════════════════════════════════════════════
    # ВЫБОР ДОСОК ДЛЯ PINTEREST
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_boards_'))
    def handle_scheduler_boards(call):
        """Выбор досок для публикации в планировщике Pinterest"""
        try:
            parts = call.data.split('_')
            platform_type = parts[2]
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            category_name = subproject.get('name', 'Unknown')
            
            # Получаем доски через API
            from platforms.pinterest.client import PinterestClient
            
            access_token = platform.get('access_token')
            if not access_token:
                bot.answer_callback_query(call.id, "❌ Токен не найден", show_alert=True)
                return
            
            try:
                client = PinterestClient(access_token)
                all_boards = client.get_boards()
            except Exception as e:
                print(f"❌ Ошибка получения досок: {e}")
                bot.answer_callback_query(call.id, "❌ Ошибка получения досок", show_alert=True)
                return
            
            if not all_boards:
                bot.answer_callback_query(call.id, "⚠️ Доски не найдены", show_alert=True)
                return
            
            # Получаем выбранные доски из настроек категории
            settings = subproject.get('settings', {})
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except:
                    settings = {}
            
            selected_boards = settings.get('pinterest_boards', [])
            if not isinstance(selected_boards, list):
                selected_boards = []
            
            # Текст
            if selected_boards:
                selected_text = f"Выбрано: {len(selected_boards)} досок"
            else:
                selected_text = "Все доски (по умолчанию)"
            
            text = (
                f"📋 <b>ВЫБОР ДОСОК PINTEREST</b>\n"
                f"📂 Категория: {escape_html(category_name)}\n"
                "━━━━━━━━━━━━━━\n\n"
                f"<b>{selected_text}</b>\n\n"
                "Выберите доски для автопостинга.\n"
                "Если ничего не выбрано - постинг на все доски.\n\n"
                "💡 <b>Доступные доски:</b>"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            # Кнопки досок
            for board in all_boards:
                board_id = board.get('id')
                board_name = board.get('name', 'Без названия')
                
                is_selected = board_id in selected_boards
                button_text = f"✅ {board_name}" if is_selected else f"☐ {board_name}"
                
                markup.add(
                    types.InlineKeyboardButton(
                        button_text,
                        callback_data=f"sched_board_toggle_{platform_type}_{platform_index}_{category_id}_{board_id}"
                    )
                )
            
            # Кнопки управления
            markup.row(
                types.InlineKeyboardButton(
                    "☑️ Все доски",
                    callback_data=f"sched_boards_all_{platform_type}_{platform_index}_{category_id}"
                ),
                types.InlineKeyboardButton(
                    "❌ Сбросить",
                    callback_data=f"sched_boards_clear_{platform_type}_{platform_index}_{category_id}"
                )
            )
            
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_scheduler_{platform_type}_{platform_index}_{category_id}"
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
            print(f"❌ Ошибка в handle_scheduler_boards: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_board_toggle_'))
    def handle_scheduler_board_toggle(call):
        """Переключение выбора доски"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            board_id = "_".join(parts[6:])  # board_id может содержать подчёркивания
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Получаем настройки
            settings = subproject.get('settings', {})
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except:
                    settings = {}
            
            selected_boards = settings.get('pinterest_boards', [])
            if not isinstance(selected_boards, list):
                selected_boards = []
            
            # Переключаем
            if board_id in selected_boards:
                selected_boards.remove(board_id)
            else:
                selected_boards.append(board_id)
            
            # Сохраняем
            settings['pinterest_boards'] = selected_boards
            
            db.cursor.execute("""
                UPDATE categories
                SET settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), category_id))
            db.conn.commit()
            
            bot.answer_callback_query(call.id)
            
            # Обновляем интерфейс
            call.data = f"sched_boards_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_boards(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_board_toggle: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_boards_all_'))
    def handle_scheduler_boards_all(call):
        """Выбрать все доски"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            user_id = call.from_user.id
            
            # Получаем платформу
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            platform_key = get_platform_key(platform_type)
            platforms = connections.get(platform_key, [])
            
            if platform_index >= len(platforms):
                bot.answer_callback_query(call.id, "❌ Платформа не найдена", show_alert=True)
                return
            
            platform = platforms[platform_index]
            
            # Получаем все доски через API
            from platforms.pinterest.client import PinterestClient
            
            access_token = platform.get('access_token')
            if not access_token:
                bot.answer_callback_query(call.id, "❌ Токен не найден", show_alert=True)
                return
            
            try:
                client = PinterestClient(access_token)
                all_boards = client.get_boards()
                all_board_ids = [board.get('id') for board in all_boards if board.get('id')]
            except Exception as e:
                print(f"❌ Ошибка получения досок: {e}")
                bot.answer_callback_query(call.id, "❌ Ошибка получения досок", show_alert=True)
                return
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Сохраняем все доски
            settings = subproject.get('settings', {})
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except:
                    settings = {}
            
            settings['pinterest_boards'] = all_board_ids
            
            db.cursor.execute("""
                UPDATE categories
                SET settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), category_id))
            db.conn.commit()
            
            bot.answer_callback_query(call.id, "✅ Выбраны все доски")
            
            # Обновляем интерфейс
            call.data = f"sched_boards_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_boards(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_boards_all: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('sched_boards_clear_'))
    def handle_scheduler_boards_clear(call):
        """Сбросить выбор досок"""
        try:
            parts = call.data.split('_')
            platform_type = parts[3]
            platform_index = int(parts[4])
            category_id = int(parts[5])
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Очищаем выбор
            settings = subproject.get('settings', {})
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except:
                    settings = {}
            
            settings['pinterest_boards'] = []
            
            db.cursor.execute("""
                UPDATE categories
                SET settings = %s::jsonb
                WHERE id = %s
            """, (json.dumps(settings), category_id))
            db.conn.commit()
            
            bot.answer_callback_query(call.id, "✅ Постинг на все доски")
            
            # Обновляем интерфейс
            call.data = f"sched_boards_{platform_type}_{platform_index}_{category_id}"
            handle_scheduler_boards(call)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_scheduler_boards_clear: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)


# Экспорт
__all__ = ['register_platform_scheduler_handlers']
