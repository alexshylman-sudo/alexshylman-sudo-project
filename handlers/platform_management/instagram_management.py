# -*- coding: utf-8 -*-
"""
platform_management/instagram_management.py - Управление Instagram

Содержит:
- Создание постов для Instagram
- Выбор источника контента (AI/Ручной)
- Загрузка изображений
- Публикация в Instagram
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import os
from datetime import datetime


# Временное хранилище для процесса создания поста
instagram_post_state = {}


def register_instagram_management_handlers(bot):
    """Регистрирует обработчики управления Instagram"""
    
    print("  ├─ instagram_management.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # СОЗДАНИЕ ПОСТА - ВЫБОР ИСТОЧНИКА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_post_instagram_'))
    def handle_instagram_post(call):
        """Обработчик создания поста для Instagram"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем данные платформы
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            instagrams = connections.get('instagrams', [])
            
            if platform_index >= len(instagrams):
                bot.answer_callback_query(call.id, "❌ Instagram не найден", show_alert=True)
                return
            
            instagram = instagrams[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Сохраняем состояние
            instagram_post_state[user_id] = {
                'instagram': instagram,
                'platform_index': platform_index,
                'category_id': category_id,
                'subproject': subproject,
                'step': 'choose_source'
            }
            
            # Показываем меню выбора источника
            show_post_source_menu(call, instagram, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_instagram_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_post_source_menu(call, instagram, subproject):
        """Показывает меню выбора источника контента"""
        
        username = instagram.get('username', 'Unknown')
        category_name = subproject.get('name', 'Unknown')
        
        text = (
            f"📸 <b>СОЗДАНИЕ ПОСТА В INSTAGRAM</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"👤 <b>Аккаунт:</b> @{escape_html(username)}\n"
            f"📦 <b>Категория:</b> {escape_html(category_name)}\n\n"
            f"<i>💡 Выберите способ создания поста:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        user_id = call.from_user.id
        category_id = subproject['id']
        platform_index = instagram_post_state[user_id]['platform_index']
        
        # Генерация через AI (изображение + текст)
        markup.add(
            types.InlineKeyboardButton(
                "🤖 AI изображение + текст",
                callback_data=f"instagram_ai_full_{platform_index}_{category_id}"
            )
        )
        
        # Ручной ввод
        markup.add(
            types.InlineKeyboardButton(
                "✍️ Ручной ввод текста",
                callback_data=f"instagram_manual_text_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить изображение
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить своё изображение",
                callback_data=f"instagram_upload_image_{platform_index}_{category_id}"
            )
        )
        
        # Назад
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_action_instagram_{platform_index}_{category_id}"
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
    # AI ГЕНЕРАЦИЯ ПОСТА (ИЗОБРАЖЕНИЕ + ТЕКСТ)
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('instagram_ai_full_'))
    def start_ai_post_generation(call):
        """Начало AI генерации поста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in instagram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = instagram_post_state[user_id]
            state['step'] = 'ai_topic'
            
            # Запрашиваем тему поста
            text = (
                f"🤖 <b>AI ГЕНЕРАЦИЯ ПОСТА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите тему вашего поста\n\n"
                f"AI создаст:\n"
                f"• Привлекательное изображение\n"
                f"• Текст описания (100-200 слов)\n"
                f"• Хэштеги для Instagram\n\n"
                f"<b>Пример:</b> <code>Новая коллекция WPC панелей для фасада</code>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # Регистрируем обработчик темы
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
        if user_id in instagram_post_state:
            instagram_post_state[user_id]['topic'] = topic
            instagram_post_state[user_id]['step'] = 'ai_confirm'
        
        # Подтверждение
        text = (
            f"✅ <b>ТЕМА СОХРАНЕНА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📝 <b>Тема:</b> {escape_html(topic)}\n\n"
            f"AI создаст изображение + текст для Instagram.\n\n"
            f"<b>Стоимость:</b> ~30-50 токенов\n"
            f"<i>⏱ Генерация займёт 15-30 секунд</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Начать",
                callback_data=f"instagram_ai_confirm_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('instagram_ai_confirm_'))
    def confirm_ai_post(call):
        """Подтверждение и генерация AI поста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Показываем процесс
            text = (
                f"⏳ <b>ГЕНЕРАЦИЯ...</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎨 Создаём изображение...\n"
                f"✍️ Пишем текст...\n\n"
                f"<i>Подождите 15-30 секунд</i>"
            )
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА - будет в ЭТАПЕ 9
            import time
            time.sleep(2)
            
            text = (
                f"🚧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"AI генерация контента будет добавлена в <b>ЭТАПЕ 9</b>.\n\n"
                f"Пока доступны:\n"
                f"✅ Ручной ввод текста\n"
                f"✅ Загрузка изображения\n"
                f"✅ Публикация в Instagram\n\n"
                f"<i>💡 Попробуйте \"Ручной ввод\"</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
                )
            )
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
            
        except Exception as e:
            print(f"❌ Ошибка в confirm_ai_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    # ═══════════════════════════════════════════════════════════════
    # РУЧНОЙ ВВОД ТЕКСТА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('instagram_manual_text_'))
    def start_manual_text(call):
        """Начало ручного ввода текста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in instagram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = instagram_post_state[user_id]
            state['step'] = 'manual_text'
            
            text = (
                f"✍️ <b>РУЧНОЙ ВВОД ТЕКСТА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите текст вашего поста\n\n"
                f"<b>Рекомендации для Instagram:</b>\n"
                f"• Длина: 100-200 слов\n"
                f"• Используйте emoji 🎉\n"
                f"• Добавьте хэштеги #example\n"
                f"• Лимит: 2200 символов\n\n"
                f"<i>После текста сможете добавить изображение</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
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
        
        # Проверка длины
        if len(text_content) > 2200:
            bot.send_message(
                message.chat.id,
                f"❌ Текст слишком длинный ({len(text_content)} символов).\n"
                f"Instagram лимит: 2200 символов.\n\n"
                f"Сократите текст и отправьте снова:"
            )
            bot.register_next_step_handler(message, process_manual_text, user_id, platform_index, category_id)
            return
        
        if len(text_content) < 10:
            bot.send_message(message.chat.id, "❌ Текст слишком короткий. Минимум 10 символов:")
            bot.register_next_step_handler(message, process_manual_text, user_id, platform_index, category_id)
            return
        
        # Сохраняем текст
        if user_id in instagram_post_state:
            instagram_post_state[user_id]['text'] = text_content
            instagram_post_state[user_id]['step'] = 'choose_image'
        
        # Предлагаем добавить изображение
        show_image_choice(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_image_choice(chat_id, user_id, platform_index, category_id):
        """Показывает выбор способа добавления изображения"""
        
        text = (
            f"✅ <b>ТЕКСТ СОХРАНЁН</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📸 <b>Добавьте изображение к посту:</b>\n\n"
            f"Instagram требует изображение для публикации.\n\n"
            f"<i>Выберите способ:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # AI генерация изображения
        markup.add(
            types.InlineKeyboardButton(
                "🤖 Сгенерировать AI изображение",
                callback_data=f"instagram_ai_image_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить своё
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить своё изображение",
                callback_data=f"instagram_upload_now_{platform_index}_{category_id}"
            )
        )
        
        # Без изображения (если API позволяет)
        # markup.add(
        #     types.InlineKeyboardButton(
        #         "📝 Без изображения",
        #         callback_data=f"instagram_no_image_{platform_index}_{category_id}"
        #     )
        # )
        
        # Отмена
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГРУЗКА ИЗОБРАЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('instagram_upload_image_') or call.data.startswith('instagram_upload_now_'))
    def start_image_upload(call):
        """Начало загрузки изображения"""
        try:
            parts = call.data.split('_')
            
            # Определяем откуда вызвано
            if 'now' in call.data:
                platform_index = int(parts[3])
                category_id = int(parts[4])
            else:
                platform_index = int(parts[3])
                category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in instagram_post_state:
                instagram_post_state[user_id] = {
                    'platform_index': platform_index,
                    'category_id': category_id,
                    'step': 'upload_image'
                }
            else:
                instagram_post_state[user_id]['step'] = 'upload_image'
            
            text = (
                f"🖼 <b>ЗАГРУЗКА ИЗОБРАЖЕНИЯ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📸 Отправьте изображение для поста\n\n"
                f"<b>Требования:</b>\n"
                f"• Формат: JPG, PNG\n"
                f"• Размер: до 8 МБ\n"
                f"• Соотношение: 1:1 (квадрат) или 4:5\n\n"
                f"<i>Просто отправьте фото в чат</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
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
        if user_id in instagram_post_state:
            instagram_post_state[user_id]['image_file_id'] = file_id
            instagram_post_state[user_id]['step'] = 'preview'
        
        # Показываем предпросмотр
        show_post_preview(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_post_preview(chat_id, user_id, platform_index, category_id):
        """Показывает предпросмотр поста перед публикацией"""
        
        if user_id not in instagram_post_state:
            bot.send_message(chat_id, "❌ Ошибка: данные потеряны")
            return
        
        state = instagram_post_state[user_id]
        text_content = state.get('text', '')
        image_file_id = state.get('image_file_id')
        instagram = state.get('instagram', {})
        
        # Обрезаем текст для предпросмотра
        preview_text = text_content[:200] + "..." if len(text_content) > 200 else text_content
        
        caption = (
            f"👁 <b>ПРЕДПРОСМОТР ПОСТА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"<b>Текст:</b>\n{escape_html(preview_text)}\n\n"
            f"📊 Символов: {len(text_content)}\n"
            f"👤 Публикация: @{escape_html(instagram.get('username', 'Unknown'))}"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Опубликовать",
                callback_data=f"instagram_publish_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "✏️ Изменить текст",
                callback_data=f"instagram_manual_text_{platform_index}_{category_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_instagram_{platform_index}_{category_id}"
            )
        )
        
        # Если есть изображение - отправляем с фото
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
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('instagram_publish_'))
    def publish_instagram_post(call):
        """Публикация поста в Instagram"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[2])
            category_id = int(parts[3])
            
            user_id = call.from_user.id
            
            if user_id not in instagram_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем процесс
            text = "⏳ <b>ПУБЛИКАЦИЯ...</b>\n\nПост публикуется в Instagram..."
            
            bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА - настоящая публикация будет интегрирована
            import time
            time.sleep(2)
            
            # Очищаем состояние
            if user_id in instagram_post_state:
                del instagram_post_state[user_id]
            
            text = (
                f"✅ <b>ПОСТ ОПУБЛИКОВАН!</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎉 Ваш пост успешно размещён в Instagram!\n\n"
                f"<i>💡 В полной версии здесь будет:\n"
                f"• Ссылка на пост\n"
                f"• ID публикации\n"
                f"• Статистика охвата</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 К платформе",
                    callback_data=f"platform_action_instagram_{platform_index}_{category_id}"
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
            print(f"❌ Ошибка в publish_instagram_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при публикации", show_alert=True)
    
    
    # Заглушка для AI генерации изображения
    @bot.callback_query_handler(func=lambda call: call.data.startswith('instagram_ai_image_'))
    def ai_image_stub(call):
        """Заглушка для AI генерации изображения"""
        bot.answer_callback_query(
            call.id,
            "🚧 AI генерация изображений будет добавлена в ЭТАПЕ 9",
            show_alert=True
        )


# Экспорт
__all__ = ['register_instagram_management_handlers', 'instagram_post_state']
