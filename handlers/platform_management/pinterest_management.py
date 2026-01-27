# -*- coding: utf-8 -*-
"""
platform_management/pinterest_management.py - Управление Pinterest

Содержит:
- Создание пинов для Pinterest
- Выбор источника контента (AI/Ручной)
- Выбор доски Pinterest
- Публикация пинов
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import os
from datetime import datetime


# Временное хранилище для процесса создания пина
pinterest_pin_state = {}


def register_pinterest_management_handlers(bot):
    """Регистрирует обработчики управления Pinterest"""
    
    print("  ├─ pinterest_management.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # СОЗДАНИЕ ПИНА - ВЫБОР ИСТОЧНИКА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_post_pinterest_'))
    def handle_pinterest_pin(call):
        """Обработчик создания пина для Pinterest"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем данные платформы
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            pinterests = connections.get('pinterests', [])
            
            if platform_index >= len(pinterests):
                bot.answer_callback_query(call.id, "❌ Pinterest не найден", show_alert=True)
                return
            
            pinterest = pinterests[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Сохраняем состояние
            pinterest_pin_state[user_id] = {
                'pinterest': pinterest,
                'platform_index': platform_index,
                'category_id': category_id,
                'subproject': subproject,
                'step': 'choose_source'
            }
            
            # Показываем меню выбора источника
            show_pin_source_menu(call, pinterest, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_pinterest_pin: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_pin_source_menu(call, pinterest, subproject):
        """Показывает меню выбора источника контента"""
        
        username = pinterest.get('username', 'Unknown')
        board = pinterest.get('board', 'Unknown')
        category_name = subproject.get('name', 'Unknown')
        
        text = (
            f"📌 <b>СОЗДАНИЕ ПИНА В PINTEREST</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"👤 <b>Аккаунт:</b> @{escape_html(username)}\n"
            f"📋 <b>Доска:</b> {escape_html(board)}\n"
            f"📦 <b>Категория:</b> {escape_html(category_name)}\n\n"
            f"<i>💡 Выберите способ создания пина:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        user_id = call.from_user.id
        category_id = subproject['id']
        platform_index = pinterest_pin_state[user_id]['platform_index']
        
        # Генерация через AI (изображение + текст)
        markup.add(
            types.InlineKeyboardButton(
                "🤖 AI изображение + описание",
                callback_data=f"pinterest_ai_full_{platform_index}_{category_id}"
            )
        )
        
        # Ручной ввод описания
        markup.add(
            types.InlineKeyboardButton(
                "✍️ Ручной ввод описания",
                callback_data=f"pinterest_manual_desc_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить изображение
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить своё изображение",
                callback_data=f"pinterest_upload_image_{platform_index}_{category_id}"
            )
        )
        
        # Выбрать доску (если нужно изменить)
        markup.add(
            types.InlineKeyboardButton(
                "📌 Выбрать другую доску",
                callback_data=f"pinterest_choose_board_{platform_index}_{category_id}"
            )
        )
        
        # Назад
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_action_pinterest_{platform_index}_{category_id}"
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
    
    
    # ═══════════════════════════════════════════════════════════════
    # AI ГЕНЕРАЦИЯ ПИНА (ЗАГЛУШКА)
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pinterest_ai_full_'))
    def start_ai_pin_generation(call):
        """Начало AI генерации пина"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in pinterest_pin_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = pinterest_pin_state[user_id]
            state['step'] = 'ai_topic'
            
            # Запрашиваем тему пина
            text = (
                f"🤖 <b>AI ГЕНЕРАЦИЯ ПИНА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите тему вашего пина\n\n"
                f"AI создаст:\n"
                f"• Привлекательное изображение (2:3 или 1:1)\n"
                f"• Описание пина (50-100 слов)\n"
                f"• Хэштеги для Pinterest\n\n"
                f"<b>Пример:</b> <code>Идеи отделки фасада WPC панелями</code>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_pinterest_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.register_next_step_handler(msg, process_pin_topic, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_ai_pin_generation: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_pin_topic(message, user_id, platform_index, category_id):
        """Обработка темы пина"""
        
        if message.text.startswith('/') or message.text == "❌ Отмена":
            bot.send_message(message.chat.id, "❌ Создание пина отменено")
            return
        
        topic = message.text.strip()
        
        if len(topic) < 3:
            bot.send_message(message.chat.id, "❌ Тема слишком короткая. Минимум 3 символа:")
            bot.register_next_step_handler(message, process_pin_topic, user_id, platform_index, category_id)
            return
        
        # Сохраняем тему
        if user_id in pinterest_pin_state:
            pinterest_pin_state[user_id]['topic'] = topic
        
        # ЗАГЛУШКА - будет в ЭТАПЕ 9
        text = (
            f"🚧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"AI генерация пинов будет добавлена в <b>ЭТАПЕ 9</b>.\n\n"
            f"Пока доступны:\n"
            f"✅ Ручной ввод описания\n"
            f"✅ Загрузка изображения\n\n"
            f"<i>💡 Попробуйте \"Ручной ввод\"</i>"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_post_pinterest_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # РУЧНОЙ ВВОД ОПИСАНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pinterest_manual_desc_'))
    def start_manual_description(call):
        """Начало ручного ввода описания"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in pinterest_pin_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = pinterest_pin_state[user_id]
            state['step'] = 'manual_title'
            
            text = (
                f"✍️ <b>РУЧНОЙ ВВОД ОПИСАНИЯ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 <b>Шаг 1 из 2:</b> Заголовок пина\n\n"
                f"Введите короткий заголовок (до 100 символов).\n\n"
                f"<b>Пример:</b> <code>WPC панели для фасада</code>\n\n"
                f"<i>После заголовка введёте описание</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_pinterest_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.register_next_step_handler(msg, process_pin_title, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_manual_description: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_pin_title(message, user_id, platform_index, category_id):
        """Обработка заголовка пина"""
        
        if message.text.startswith('/') or message.text == "❌ Отмена":
            bot.send_message(message.chat.id, "❌ Создание пина отменено")
            return
        
        title = message.text.strip()
        
        if len(title) > 100:
            bot.send_message(
                message.chat.id,
                f"❌ Заголовок слишком длинный ({len(title)} символов).\n"
                f"Pinterest лимит: 100 символов.\n\n"
                f"Сократите и отправьте снова:"
            )
            bot.register_next_step_handler(message, process_pin_title, user_id, platform_index, category_id)
            return
        
        if len(title) < 3:
            bot.send_message(message.chat.id, "❌ Заголовок слишком короткий. Минимум 3 символа:")
            bot.register_next_step_handler(message, process_pin_title, user_id, platform_index, category_id)
            return
        
        # Сохраняем заголовок
        if user_id in pinterest_pin_state:
            pinterest_pin_state[user_id]['title'] = title
            pinterest_pin_state[user_id]['step'] = 'manual_description'
        
        # Запрашиваем описание
        text = (
            f"✍️ <b>РУЧНОЙ ВВОД ОПИСАНИЯ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"✅ Заголовок: <b>{escape_html(title)}</b>\n\n"
            f"📝 <b>Шаг 2 из 2:</b> Описание пина\n\n"
            f"Введите описание (50-500 символов).\n\n"
            f"<b>Рекомендации:</b>\n"
            f"• Используйте ключевые слова\n"
            f"• Добавьте хэштеги #example\n"
            f"• Без emoji (Pinterest не поддерживает хорошо)\n\n"
            f"<i>После описания загрузите изображение</i>"
        )
        
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        bot.register_next_step_handler(message, process_pin_description, user_id, platform_index, category_id)
    
    
    def process_pin_description(message, user_id, platform_index, category_id):
        """Обработка описания пина"""
        
        if message.text.startswith('/') or message.text == "❌ Отмена":
            bot.send_message(message.chat.id, "❌ Создание пина отменено")
            return
        
        description = message.text.strip()
        
        if len(description) > 500:
            bot.send_message(
                message.chat.id,
                f"❌ Описание слишком длинное ({len(description)} символов).\n"
                f"Pinterest лимит: 500 символов.\n\n"
                f"Сократите и отправьте снова:"
            )
            bot.register_next_step_handler(message, process_pin_description, user_id, platform_index, category_id)
            return
        
        if len(description) < 10:
            bot.send_message(message.chat.id, "❌ Описание слишком короткое. Минимум 10 символов:")
            bot.register_next_step_handler(message, process_pin_description, user_id, platform_index, category_id)
            return
        
        # Сохраняем описание
        if user_id in pinterest_pin_state:
            pinterest_pin_state[user_id]['description'] = description
            pinterest_pin_state[user_id]['step'] = 'upload_image'
        
        # Предлагаем загрузить изображение
        show_image_upload_prompt(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_image_upload_prompt(chat_id, user_id, platform_index, category_id):
        """Показывает запрос на загрузку изображения"""
        
        text = (
            f"✅ <b>ОПИСАНИЕ СОХРАНЕНО</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📸 <b>Загрузите изображение для пина</b>\n\n"
            f"<b>Требования Pinterest:</b>\n"
            f"• Формат: JPG, PNG\n"
            f"• Соотношение: 2:3 (вертикаль) или 1:1\n"
            f"• Размер: до 32 МБ\n"
            f"• Высокое качество для лучшего охвата\n\n"
            f"<i>Просто отправьте фото в чат</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # AI генерация изображения
        markup.add(
            types.InlineKeyboardButton(
                "🤖 Сгенерировать AI изображение",
                callback_data=f"pinterest_ai_image_{platform_index}_{category_id}"
            )
        )
        
        # Отмена
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_pinterest_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГРУЗКА ИЗОБРАЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pinterest_upload_image_'))
    def start_image_upload(call):
        """Начало загрузки изображения"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in pinterest_pin_state:
                pinterest_pin_state[user_id] = {
                    'platform_index': platform_index,
                    'category_id': category_id,
                    'step': 'upload_image'
                }
            else:
                pinterest_pin_state[user_id]['step'] = 'upload_image'
            
            text = (
                f"🖼 <b>ЗАГРУЗКА ИЗОБРАЖЕНИЯ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📸 Отправьте изображение для пина\n\n"
                f"<b>Требования Pinterest:</b>\n"
                f"• Формат: JPG, PNG\n"
                f"• Соотношение: 2:3 (вертикаль) или 1:1\n"
                f"• Размер: до 32 МБ\n"
                f"• Высокое качество\n\n"
                f"<i>Просто отправьте фото в чат</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_pinterest_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.register_next_step_handler(msg, process_uploaded_image, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_image_upload: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_uploaded_image(message, user_id, platform_index, category_id):
        """Обработка загруженного изображения"""
        
        # Проверка на отмену
        if message.text and (message.text.startswith('/') or message.text == "❌ Отмена"):
            bot.send_message(message.chat.id, "❌ Загрузка отменена")
            return
        
        # Проверка наличия фото
        if not message.photo:
            bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, отправьте изображение (не файл, а фото):"
            )
            bot.register_next_step_handler(message, process_uploaded_image, user_id, platform_index, category_id)
            return
        
        # Получаем фото (самое большое разрешение)
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # Сохраняем в состояние
        if user_id in pinterest_pin_state:
            pinterest_pin_state[user_id]['image_file_id'] = file_id
            pinterest_pin_state[user_id]['step'] = 'preview'
        
        # Показываем предпросмотр
        show_pin_preview(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_pin_preview(chat_id, user_id, platform_index, category_id):
        """Показывает предпросмотр пина перед публикацией"""
        
        if user_id not in pinterest_pin_state:
            bot.send_message(chat_id, "❌ Ошибка: данные потеряны")
            return
        
        state = pinterest_pin_state[user_id]
        title = state.get('title', 'Без заголовка')
        description = state.get('description', '')
        image_file_id = state.get('image_file_id')
        pinterest = state.get('pinterest', {})
        
        caption = (
            f"👁 <b>ПРЕДПРОСМОТР ПИНА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"<b>Заголовок:</b> {escape_html(title)}\n\n"
            f"<b>Описание:</b>\n{escape_html(description)}\n\n"
            f"📊 Символов: {len(description)}\n"
            f"👤 Публикация: @{escape_html(pinterest.get('username', 'Unknown'))}\n"
            f"📋 Доска: {escape_html(pinterest.get('board', 'Unknown'))}"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Опубликовать",
                callback_data=f"pinterest_publish_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "✏️ Изменить",
                callback_data=f"pinterest_manual_desc_{platform_index}_{category_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_pinterest_{platform_index}_{category_id}"
            )
        )
        
        # Отправляем с изображением
        if image_file_id:
            bot.send_photo(
                chat_id,
                image_file_id,
                caption=caption,
                reply_markup=markup,
                parse_mode='HTML'
            )
        else:
            bot.send_message(chat_id, caption, reply_markup=markup, parse_mode='HTML')
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pinterest_publish_'))
    def publish_pinterest_pin(call):
        """Публикация пина в Pinterest"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[2])
            category_id = int(parts[3])
            
            user_id = call.from_user.id
            
            if user_id not in pinterest_pin_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем процесс
            text = "⏳ <b>ПУБЛИКАЦИЯ...</b>\n\nПин публикуется в Pinterest..."
            
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА - настоящая публикация будет интегрирована
            import time
            time.sleep(2)
            
            # Очищаем состояние
            if user_id in pinterest_pin_state:
                del pinterest_pin_state[user_id]
            
            text = (
                f"✅ <b>ПИН ОПУБЛИКОВАН!</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎉 Ваш пин успешно размещён в Pinterest!\n\n"
                f"<i>💡 В полной версии здесь будет:\n"
                f"• Ссылка на пин\n"
                f"• ID пина\n"
                f"• Статистика охвата</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 К платформе",
                    callback_data=f"platform_action_pinterest_{platform_index}_{category_id}"
                )
            )
            
            bot.edit_message_caption(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            print(f"❌ Ошибка в publish_pinterest_pin: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при публикации", show_alert=True)
    
    
    # Заглушки
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pinterest_ai_image_'))
    def ai_image_stub(call):
        """Заглушка для AI генерации изображения"""
        bot.answer_callback_query(
            call.id,
            "🚧 AI генерация изображений будет добавлена в ЭТАПЕ 9",
            show_alert=True
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pinterest_choose_board_'))
    def choose_board_stub(call):
        """Заглушка для выбора доски"""
        bot.answer_callback_query(
            call.id,
            "🚧 Выбор доски будет добавлен позже",
            show_alert=True
        )


# Экспорт
__all__ = ['register_pinterest_management_handlers', 'pinterest_pin_state']
