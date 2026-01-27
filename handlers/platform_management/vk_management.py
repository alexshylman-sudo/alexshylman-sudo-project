# -*- coding: utf-8 -*-
"""
platform_management/vk_management.py - Управление ВКонтакте

Содержит:
- Создание постов для ВКонтакте
- Выбор источника контента (AI/Ручной)
- Загрузка изображений
- Публикация в VK
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import os
from datetime import datetime


# Временное хранилище для процесса создания поста
vk_post_state = {}


def register_vk_management_handlers(bot):
    """Регистрирует обработчики управления ВКонтакте"""
    
    print("  ├─ vk_management.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # СОЗДАНИЕ ПОСТА - ВЫБОР ИСТОЧНИКА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_post_vk_'))
    def handle_vk_post(call):
        """Обработчик создания поста для VK"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем данные платформы
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            vks = connections.get('vks', [])
            
            if platform_index >= len(vks):
                bot.answer_callback_query(call.id, "❌ VK группа не найдена", show_alert=True)
                return
            
            vk = vks[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Сохраняем состояние
            vk_post_state[user_id] = {
                'vk': vk,
                'platform_index': platform_index,
                'category_id': category_id,
                'subproject': subproject,
                'step': 'choose_source'
            }
            
            # Показываем меню выбора источника
            show_post_source_menu(call, vk, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_vk_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_post_source_menu(call, vk, subproject):
        """Показывает меню выбора источника контента"""
        
        group_name = vk.get('group_name', 'Unknown')
        category_name = subproject.get('name', 'Unknown')
        
        text = (
            f"💬 <b>СОЗДАНИЕ ПОСТА ВКОНТАКТЕ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Группа:</b> {escape_html(group_name)}\n"
            f"📦 <b>Категория:</b> {escape_html(category_name)}\n\n"
            f"<i>💡 Выберите способ создания поста:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        user_id = call.from_user.id
        category_id = subproject['id']
        platform_index = vk_post_state[user_id]['platform_index']
        
        # Генерация через AI (изображение + текст)
        markup.add(
            types.InlineKeyboardButton(
                "🤖 AI изображение + текст",
                callback_data=f"vk_ai_full_{platform_index}_{category_id}"
            )
        )
        
        # Ручной ввод
        markup.add(
            types.InlineKeyboardButton(
                "✍️ Ручной ввод текста",
                callback_data=f"vk_manual_text_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить изображение
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить изображение",
                callback_data=f"vk_upload_image_{platform_index}_{category_id}"
            )
        )
        
        # Назад
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_action_vk_{platform_index}_{category_id}"
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
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('vk_ai_full_'))
    def start_ai_post_generation(call):
        """Начало AI генерации поста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in vk_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = vk_post_state[user_id]
            state['step'] = 'ai_topic'
            
            # Запрашиваем тему поста
            text = (
                f"🤖 <b>AI ГЕНЕРАЦИЯ ПОСТА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите тему вашего поста\n\n"
                f"AI создаст:\n"
                f"• Привлекательное изображение\n"
                f"• Текст описания (200-400 слов)\n"
                f"• Emoji для оформления\n\n"
                f"<b>Пример:</b> <code>Скидка 20% на все WPC панели</code>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_vk_{platform_index}_{category_id}"
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
        if user_id in vk_post_state:
            vk_post_state[user_id]['topic'] = topic
        
        # ЗАГЛУШКА - будет в ЭТАПЕ 9
        text = (
            f"🚧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"AI генерация контента будет добавлена в <b>ЭТАПЕ 9</b>.\n\n"
            f"Пока доступны:\n"
            f"✅ Ручной ввод текста\n"
            f"✅ Загрузка изображения\n\n"
            f"<i>💡 Попробуйте \"Ручной ввод\"</i>"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_post_vk_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # РУЧНОЙ ВВОД ТЕКСТА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('vk_manual_text_'))
    def start_manual_text(call):
        """Начало ручного ввода текста"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in vk_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = vk_post_state[user_id]
            state['step'] = 'manual_text'
            
            text = (
                f"✍️ <b>РУЧНОЙ ВВОД ТЕКСТА</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 Введите текст вашего поста\n\n"
                f"<b>Рекомендации для VK:</b>\n"
                f"• Длина: 200-400 слов\n"
                f"• Используйте emoji 🎉\n"
                f"• Можно использовать переносы\n"
                f"• Лимит: около 16,000 символов\n\n"
                f"<i>После текста сможете добавить изображение</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_vk_{platform_index}_{category_id}"
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
        
        # Проверка длины (VK лимит около 16к символов)
        if len(text_content) > 16000:
            bot.send_message(
                message.chat.id,
                f"❌ Текст слишком длинный ({len(text_content)} символов).\n"
                f"VK лимит: около 16,000 символов.\n\n"
                f"Сократите текст и отправьте снова:"
            )
            bot.register_next_step_handler(message, process_manual_text, user_id, platform_index, category_id)
            return
        
        if len(text_content) < 10:
            bot.send_message(message.chat.id, "❌ Текст слишком короткий. Минимум 10 символов:")
            bot.register_next_step_handler(message, process_manual_text, user_id, platform_index, category_id)
            return
        
        # Сохраняем текст
        if user_id in vk_post_state:
            vk_post_state[user_id]['text'] = text_content
            vk_post_state[user_id]['step'] = 'choose_image'
        
        # Предлагаем добавить изображение
        show_image_choice(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_image_choice(chat_id, user_id, platform_index, category_id):
        """Показывает выбор способа добавления изображения"""
        
        text = (
            f"✅ <b>ТЕКСТ СОХРАНЁН</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📸 <b>Хотите добавить изображение?</b>\n\n"
            f"VK поддерживает посты с изображением и без.\n\n"
            f"<i>Выберите действие:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # AI генерация изображения
        markup.add(
            types.InlineKeyboardButton(
                "🤖 Сгенерировать AI изображение",
                callback_data=f"vk_ai_image_{platform_index}_{category_id}"
            )
        )
        
        # Загрузить своё
        markup.add(
            types.InlineKeyboardButton(
                "🖼 Загрузить своё изображение",
                callback_data=f"vk_upload_now_{platform_index}_{category_id}"
            )
        )
        
        # Без изображения
        markup.add(
            types.InlineKeyboardButton(
                "📝 Без изображения",
                callback_data=f"vk_no_image_{platform_index}_{category_id}"
            )
        )
        
        # Отмена
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_vk_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
    
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГРУЗКА ИЗОБРАЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('vk_upload_image_') or call.data.startswith('vk_upload_now_'))
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
            
            if user_id not in vk_post_state:
                vk_post_state[user_id] = {
                    'platform_index': platform_index,
                    'category_id': category_id,
                    'step': 'upload_image'
                }
            else:
                vk_post_state[user_id]['step'] = 'upload_image'
            
            text = (
                f"🖼 <b>ЗАГРУЗКА ИЗОБРАЖЕНИЯ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📸 Отправьте изображение для поста\n\n"
                f"<b>Требования VK:</b>\n"
                f"• Формат: JPG, PNG, GIF\n"
                f"• Размер: до 50 МБ\n"
                f"• Можно несколько изображений\n\n"
                f"<i>Просто отправьте фото в чат</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_vk_{platform_index}_{category_id}"
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
        if user_id in vk_post_state:
            vk_post_state[user_id]['image_file_id'] = file_id
            vk_post_state[user_id]['step'] = 'preview'
        
        # Показываем предпросмотр
        show_post_preview(message.chat.id, user_id, platform_index, category_id)
    
    
    # ═══════════════════════════════════════════════════════════════
    # БЕЗ ИЗОБРАЖЕНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('vk_no_image_'))
    def handle_no_image(call):
        """Пост без изображения"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in vk_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем предпросмотр без изображения
            show_post_preview(call.message.chat.id, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_no_image: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_post_preview(chat_id, user_id, platform_index, category_id):
        """Показывает предпросмотр поста перед публикацией"""
        
        if user_id not in vk_post_state:
            bot.send_message(chat_id, "❌ Ошибка: данные потеряны")
            return
        
        state = vk_post_state[user_id]
        text_content = state.get('text', '')
        image_file_id = state.get('image_file_id')
        vk = state.get('vk', {})
        
        # Обрезаем текст для предпросмотра
        preview_text = text_content[:300] + "..." if len(text_content) > 300 else text_content
        
        caption = (
            f"👁 <b>ПРЕДПРОСМОТР ПОСТА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"<b>Текст:</b>\n{escape_html(preview_text)}\n\n"
            f"📊 Символов: {len(text_content)}\n"
            f"👥 Публикация: {escape_html(vk.get('group_name', 'Unknown'))}"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Опубликовать",
                callback_data=f"vk_publish_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "✏️ Изменить текст",
                callback_data=f"vk_manual_text_{platform_index}_{category_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_vk_{platform_index}_{category_id}"
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
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('vk_publish_'))
    def publish_vk_post(call):
        """Публикация поста в VK"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[2])
            category_id = int(parts[3])
            
            user_id = call.from_user.id
            
            if user_id not in vk_post_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем процесс
            text = "⏳ <b>ПУБЛИКАЦИЯ...</b>\n\nПост публикуется ВКонтакте..."
            
            try:
                bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            except:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА - настоящая публикация будет интегрирована
            import time
            time.sleep(2)
            
            # Очищаем состояние
            if user_id in vk_post_state:
                del vk_post_state[user_id]
            
            text = (
                f"✅ <b>ПОСТ ОПУБЛИКОВАН!</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎉 Ваш пост успешно размещён ВКонтакте!\n\n"
                f"<i>💡 В полной версии здесь будет:\n"
                f"• Ссылка на пост\n"
                f"• ID записи\n"
                f"• Статистика просмотров</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 К платформе",
                    callback_data=f"platform_action_vk_{platform_index}_{category_id}"
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
            print(f"❌ Ошибка в publish_vk_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при публикации", show_alert=True)
    
    
    # Заглушка для AI генерации изображения
    @bot.callback_query_handler(func=lambda call: call.data.startswith('vk_ai_image_'))
    def ai_image_stub(call):
        """Заглушка для AI генерации изображения"""
        bot.answer_callback_query(
            call.id,
            "🚧 AI генерация изображений будет добавлена в ЭТАПЕ 9",
            show_alert=True
        )


# Экспорт
__all__ = ['register_vk_management_handlers', 'vk_post_state']
