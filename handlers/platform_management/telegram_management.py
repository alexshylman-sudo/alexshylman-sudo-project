# -*- coding: utf-8 -*-
"""
platform_management/telegram_management.py - Управление Telegram

Содержит:
- Создание постов для Telegram каналов
- Выбор источника контента (AI/Ручной)
- Публикация с изображением и видео
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import os
from datetime import datetime


# Временное хранилище для процесса создания поста
telegram_post_state = {}


def register_telegram_management_handlers(bot):
    """Регистрирует обработчики управления Telegram"""
    
    print("  ├─ telegram_management.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # СОЗДАНИЕ ПОСТА - ВЫБОР ИСТОЧНИКА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_post_telegram_'))
    def handle_telegram_post(call):
        """Обработчик создания поста для Telegram"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем данные платформы
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            telegrams = connections.get('telegrams', [])
            
            if platform_index >= len(telegrams):
                bot.answer_callback_query(call.id, "❌ Telegram канал не найден", show_alert=True)
                return
            
            telegram = telegrams[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Сохраняем состояние
            telegram_post_state[user_id] = {
                'telegram': telegram,
                'platform_index': platform_index,
                'category_id': category_id,
                'subproject': subproject,
                'step': 'choose_source'
            }
            
            # Показываем меню выбора источника
            show_post_source_menu(call, telegram, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_telegram_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_post_source_menu(call, telegram, subproject):
        """Показывает меню выбора источника контента"""
        
        channel = telegram.get('channel', 'Unknown')
        channel_title = telegram.get('channel_title', channel)
        category_name = subproject.get('name', 'Unknown')
        
        text = (
            f"✈️ <b>СОЗДАНИЕ ПОСТА В TELEGRAM</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📢 <b>Канал:</b> {escape_html(channel_title)}\n"
            f"🔗 <b>Username:</b> @{escape_html(channel)}\n"
            f"📦 <b>Категория:</b> {escape_html(category_name)}\n\n"
            f"<i>💡 Выберите способ создания поста:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        user_id = call.from_user.id
        category_id = subproject['id']
        platform_index = telegram_post_state[user_id]['platform_index']
        
        # Генерация через AI
        markup.add(
            types.InlineKeyboardButton(
                "🤖 AI текст + изображение",
                callback_data=f"telegram_ai_full_{platform_index}_{category_id}"
            )
        )
        
        # Ручной ввод текста
        markup.add(
            types.InlineKeyboardButton(
                "✍️ Ручной ввод текста",
                callback_data=f"telegram_manual_text_{platform_index}_{category_id}"
            )
        )
        
        # С изображением
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить изображение",
                callback_data=f"telegram_upload_image_{platform_index}_{category_id}"
            )
        )
        
        # С видео
        markup.add(
            types.InlineKeyboardButton(
                "📹 Загрузить видео",
                callback_data=f"telegram_upload_video_{platform_index}_{category_id}"
            )
        )
        
        # Назад
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_action_telegram_{platform_index}_{category_id}"
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
    # AI ГЕНЕРАЦИЯ ПОСТА (ЗАГЛУШКА)
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_ai_full_'))
    def start_ai_post_generation(call):
        """Начало AI генерации поста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in telegram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = telegram_post_state[user_id]
            state['step'] = 'ai_topic'
            
            # Запрашиваем тему поста
            text = (
                f"🤖 <b>AI ГЕНЕРАЦИЯ ПОСТА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите тему вашего поста\n\n"
                f"AI создаст:\n"
                f"• Текст поста (150-300 слов)\n"
                f"• Изображение для поста\n"
                f"• HTML форматирование\n\n"
                f"<b>Пример:</b> <code>Преимущества WPC панелей в зимний период</code>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.register_next_step_handler(msg, process_post_topic, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_ai_post_generation: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_post_topic(message, user_id, platform_index, category_id):
        """Обработка темы поста"""
        
        if message.text.startswith('/') or message.text == "❌ Отмена":
            bot.send_message(message.chat.id, "❌ Создание поста отменено")
            return
        
        topic = message.text.strip()
        
        if len(topic) < 3:
            bot.send_message(message.chat.id, "❌ Тема слишком короткая. Минимум 3 символа:")
            bot.register_next_step_handler(message, process_post_topic, user_id, platform_index, category_id)
            return
        
        # Сохраняем тему
        if user_id in telegram_post_state:
            telegram_post_state[user_id]['topic'] = topic
        
        # ЗАГЛУШКА - будет в ЭТАПЕ 9
        text = (
            f"🚧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"AI генерация постов будет добавлена в <b>ЭТАПЕ 9</b>.\n\n"
            f"Пока доступны:\n"
            f"✅ Ручной ввод текста\n"
            f"✅ Загрузка изображения\n"
            f"✅ Загрузка видео\n\n"
            f"<i>💡 Попробуйте \"Ручной ввод\"</i>"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # РУЧНОЙ ВВОД ТЕКСТА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_manual_text_'))
    def start_manual_text(call):
        """Начало ручного ввода текста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in telegram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = telegram_post_state[user_id]
            state['step'] = 'manual_text'
            
            text = (
                f"✍️ <b>РУЧНОЙ ВВОД ТЕКСТА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите текст вашего поста\n\n"
                f"<b>Рекомендации для Telegram:</b>\n"
                f"• Длина: 150-300 слов оптимально\n"
                f"• Используйте HTML форматирование:\n"
                f"  <code>&lt;b&gt;жирный&lt;/b&gt;</code>\n"
                f"  <code>&lt;i&gt;курсив&lt;/i&gt;</code>\n"
                f"  <code>&lt;code&gt;код&lt;/code&gt;</code>\n"
                f"• Emoji 🎉\n"
                f"• Лимит: 4096 символов\n\n"
                f"<i>После текста сможете добавить медиа</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.register_next_step_handler(msg, process_manual_text, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_manual_text: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_manual_text(message, user_id, platform_index, category_id):
        """Обработка ручного текста"""
        
        if message.text.startswith('/') or message.text == "❌ Отмена":
            bot.send_message(message.chat.id, "❌ Создание поста отменено")
            return
        
        text_content = message.text.strip()
        
        # Проверка длины (Telegram лимит 4096 символов)
        if len(text_content) > 4096:
            bot.send_message(
                message.chat.id,
                f"❌ Текст слишком длинный ({len(text_content)} символов).\n"
                f"Telegram лимит: 4096 символов.\n\n"
                f"Сократите текст и отправьте снова:"
            )
            bot.register_next_step_handler(message, process_manual_text, user_id, platform_index, category_id)
            return
        
        if len(text_content) < 10:
            bot.send_message(message.chat.id, "❌ Текст слишком короткий. Минимум 10 символов:")
            bot.register_next_step_handler(message, process_manual_text, user_id, platform_index, category_id)
            return
        
        # Сохраняем текст
        if user_id in telegram_post_state:
            telegram_post_state[user_id]['text'] = text_content
            telegram_post_state[user_id]['step'] = 'choose_media'
        
        # Предлагаем добавить медиа
        show_media_choice(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_media_choice(chat_id, user_id, platform_index, category_id):
        """Показывает выбор способа добавления медиа"""
        
        text = (
            f"✅ <b>ТЕКСТ СОХРАНЁН</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📸 <b>Хотите добавить медиа?</b>\n\n"
            f"Telegram поддерживает посты с медиа и без.\n\n"
            f"<i>Выберите действие:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # AI генерация изображения
        markup.add(
            types.InlineKeyboardButton(
                "🤖 Сгенерировать AI изображение",
                callback_data=f"telegram_ai_image_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить изображение
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить изображение",
                callback_data=f"telegram_upload_now_image_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить видео
        markup.add(
            types.InlineKeyboardButton(
                "📹 Загрузить видео",
                callback_data=f"telegram_upload_now_video_{platform_index}_{category_id}"
            )
        )
        
        # Без медиа
        markup.add(
            types.InlineKeyboardButton(
                "📝 Без медиа (только текст)",
                callback_data=f"telegram_no_media_{platform_index}_{category_id}"
            )
        )
        
        # Отмена
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГРУЗКА ИЗОБРАЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_upload_image_') or call.data.startswith('telegram_upload_now_image_'))
    def start_image_upload(call):
        """Начало загрузки изображения"""
        try:
            parts = call.data.split('_')
            
            # Определяем откуда вызвано
            if 'now' in call.data:
                platform_index = int(parts[4])
                category_id = int(parts[5])
            else:
                platform_index = int(parts[3])
                category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in telegram_post_state:
                telegram_post_state[user_id] = {
                    'platform_index': platform_index,
                    'category_id': category_id,
                    'step': 'upload_image'
                }
            else:
                telegram_post_state[user_id]['step'] = 'upload_image'
            
            text = (
                f"🖼 <b>ЗАГРУЗКА ИЗОБРАЖЕНИЯ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📸 Отправьте изображение для поста\n\n"
                f"<b>Требования Telegram:</b>\n"
                f"• Формат: JPG, PNG, GIF\n"
                f"• Размер: до 10 МБ для фото\n"
                f"• Любое соотношение сторон\n\n"
                f"<i>Просто отправьте фото в чат</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
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
        if user_id in telegram_post_state:
            telegram_post_state[user_id]['media_file_id'] = file_id
            telegram_post_state[user_id]['media_type'] = 'photo'
            telegram_post_state[user_id]['step'] = 'preview'
        
        # Показываем предпросмотр
        show_post_preview(message.chat.id, user_id, platform_index, category_id)
    
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГРУЗКА ВИДЕО
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_upload_video_') or call.data.startswith('telegram_upload_now_video_'))
    def start_video_upload(call):
        """Начало загрузки видео"""
        try:
            parts = call.data.split('_')
            
            # Определяем откуда вызвано
            if 'now' in call.data:
                platform_index = int(parts[4])
                category_id = int(parts[5])
            else:
                platform_index = int(parts[3])
                category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in telegram_post_state:
                telegram_post_state[user_id] = {
                    'platform_index': platform_index,
                    'category_id': category_id,
                    'step': 'upload_video'
                }
            else:
                telegram_post_state[user_id]['step'] = 'upload_video'
            
            text = (
                f"📹 <b>ЗАГРУЗКА ВИДЕО</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎬 Отправьте видео для поста\n\n"
                f"<b>Требования Telegram:</b>\n"
                f"• Формат: MP4, AVI, MOV\n"
                f"• Размер: до 50 МБ\n"
                f"• Длительность: любая\n\n"
                f"<i>Просто отправьте видео в чат</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            bot.register_next_step_handler(msg, process_uploaded_video, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_video_upload: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_uploaded_video(message, user_id, platform_index, category_id):
        """Обработка загруженного видео"""
        
        # Проверка на отмену
        if message.text and (message.text.startswith('/') or message.text == "❌ Отмена"):
            bot.send_message(message.chat.id, "❌ Загрузка отменена")
            return
        
        # Проверка наличия видео
        if not message.video and not message.video_note:
            bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, отправьте видео:"
            )
            bot.register_next_step_handler(message, process_uploaded_video, user_id, platform_index, category_id)
            return
        
        # Получаем видео
        video = message.video if message.video else message.video_note
        file_id = video.file_id
        
        # Сохраняем в состояние
        if user_id in telegram_post_state:
            telegram_post_state[user_id]['media_file_id'] = file_id
            telegram_post_state[user_id]['media_type'] = 'video'
            telegram_post_state[user_id]['step'] = 'preview'
        
        # Показываем предпросмотр
        show_post_preview(message.chat.id, user_id, platform_index, category_id)
    
    
    # ═══════════════════════════════════════════════════════════════
    # БЕЗ МЕДИА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_no_media_'))
    def handle_no_media(call):
        """Пост без медиа"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in telegram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем предпросмотр без медиа
            show_post_preview(call.message.chat.id, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_no_media: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_post_preview(chat_id, user_id, platform_index, category_id):
        """Показывает предпросмотр поста перед публикацией"""
        
        if user_id not in telegram_post_state:
            bot.send_message(chat_id, "❌ Ошибка: данные потеряны")
            return
        
        state = telegram_post_state[user_id]
        text_content = state.get('text', '')
        media_file_id = state.get('media_file_id')
        media_type = state.get('media_type', 'photo')
        telegram = state.get('telegram', {})
        
        # Обрезаем текст для предпросмотра
        preview_text = text_content[:300] + "..." if len(text_content) > 300 else text_content
        
        caption = (
            f"👁 <b>ПРЕДПРОСМОТР ПОСТА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"<b>Текст:</b>\n{preview_text}\n\n"
            f"📊 Символов: {len(text_content)}\n"
            f"📢 Публикация: {escape_html(telegram.get('channel_title', 'Unknown'))}"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Опубликовать",
                callback_data=f"telegram_publish_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "✏️ Изменить текст",
                callback_data=f"telegram_manual_text_{platform_index}_{category_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_telegram_{platform_index}_{category_id}"
            )
        )
        
        # Если есть медиа - отправляем с медиа
        if media_file_id:
            if media_type == 'video':
                bot.send_video(
                    chat_id,
                    media_file_id,
                    caption=caption,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                bot.send_photo(
                    chat_id,
                    media_file_id,
                    caption=caption,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
        else:
            bot.send_message(chat_id, caption, reply_markup=markup, parse_mode='HTML')
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_publish_'))
    def publish_telegram_post(call):
        """Публикация поста в Telegram"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[2])
            category_id = int(parts[3])
            
            user_id = call.from_user.id
            
            if user_id not in telegram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем процесс
            text = "⏳ <b>ПУБЛИКАЦИЯ...</b>\n\nПост публикуется в Telegram канал..."
            
            try:
                bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА - настоящая публикация будет интегрирована
            import time
            time.sleep(2)
            
            # Очищаем состояние
            if user_id in telegram_post_state:
                del telegram_post_state[user_id]
            
            text = (
                f"✅ <b>ПОСТ ОПУБЛИКОВАН!</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎉 Ваш пост успешно размещён в Telegram канале!\n\n"
                f"<i>💡 В полной версии здесь будет:\n"
                f"• Ссылка на пост\n"
                f"• ID сообщения\n"
                f"• Статистика просмотров</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 К платформе",
                    callback_data=f"platform_action_telegram_{platform_index}_{category_id}"
                )
            )
            
            try:
                bot.edit_message_caption(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            except:
                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            print(f"❌ Ошибка в publish_telegram_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при публикации", show_alert=True)
    
    
    # Заглушка для AI генерации изображения
    @bot.callback_query_handler(func=lambda call: call.data.startswith('telegram_ai_image_'))
    def ai_image_stub(call):
        """Заглушка для AI генерации изображения"""
        bot.answer_callback_query(
            call.id,
            "🚧 AI генерация изображений будет добавлена в ЭТАПЕ 9",
            show_alert=True
        )


# Экспорт
__all__ = ['register_telegram_management_handlers', 'telegram_post_state']
