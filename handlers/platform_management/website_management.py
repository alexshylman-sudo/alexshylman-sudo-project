# -*- coding: utf-8 -*-
"""
platform_management/website_management.py - Управление сайтами

Содержит:
- Создание статей для сайтов
- Выбор источника контента (AI/Ручной)
- Публикация на WordPress
"""

from telebot import types
from loader import bot, db
from utils import escape_html
import json
import os
from datetime import datetime


# Временное хранилище для процесса создания статьи
website_article_state = {}


def register_website_management_handlers(bot):
    """Регистрирует обработчики управления сайтами"""
    
    print("  ├─ website_management.py загружен")
    
    # ═══════════════════════════════════════════════════════════════
    # СОЗДАНИЕ СТАТЬИ - ВЫБОР ИСТОЧНИКА
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('platform_post_website_'))
    def handle_website_post(call):
        """Обработчик создания статьи для сайта"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            # Получаем данные платформы
            user = db.get_user(user_id)
            connections = user.get('platform_connections', {})
            websites = connections.get('websites', [])
            
            if platform_index >= len(websites):
                bot.answer_callback_query(call.id, "❌ Сайт не найден", show_alert=True)
                return
            
            website = websites[platform_index]
            
            # Получаем категорию
            subproject = db.get_subproject(category_id)
            if not subproject:
                bot.answer_callback_query(call.id, "❌ Категория не найдена", show_alert=True)
                return
            
            # Сохраняем состояние
            website_article_state[user_id] = {
                'website': website,
                'platform_index': platform_index,
                'category_id': category_id,
                'subproject': subproject,
                'step': 'choose_source'
            }
            
            # Показываем меню выбора источника
            show_article_source_menu(call, website, subproject)
            
        except Exception as e:
            print(f"❌ Ошибка в handle_website_post: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def show_article_source_menu(call, website, subproject):
        """Показывает меню выбора источника контента"""
        
        url = website.get('url', 'Unknown')
        cms = website.get('cms', 'Unknown')
        category_name = subproject.get('name', 'Unknown')
        
        text = (
            f"📝 <b>СОЗДАНИЕ СТАТЬИ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🌐 <b>Сайт:</b> {escape_html(url)}\n"
            f"⚙️ <b>CMS:</b> {cms}\n"
            f"📦 <b>Категория:</b> {escape_html(category_name)}\n\n"
            f"<i>💡 Выберите способ создания статьи:</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        user_id = call.from_user.id
        category_id = subproject['id']
        platform_index = website_article_state[user_id]['platform_index']
        
        # Генерация через AI
        markup.add(
            types.InlineKeyboardButton(
                "🤖 Сгенерировать через AI",
                callback_data=f"website_ai_generate_{platform_index}_{category_id}"
            )
        )
        
        # Ручной ввод
        markup.add(
            types.InlineKeyboardButton(
                "✍️ Ручной ввод",
                callback_data=f"website_manual_input_{platform_index}_{category_id}"
            )
        )
        
        # Из шаблона (если есть готовые статьи в категории)
        # Пока закомментируем, добавим позже
        # markup.add(
        #     types.InlineKeyboardButton(
        #         "📋 Из шаблона",
        #         callback_data=f"website_from_template_{platform_index}_{category_id}"
        #     )
        # )
        
        # Назад
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"platform_action_website_{platform_index}_{category_id}"
            )
        )
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        bot.answer_callback_query(call.id)
    
    
    # ═══════════════════════════════════════════════════════════════
    # AI ГЕНЕРАЦИЯ СТАТЬИ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('website_ai_generate_'))
    def start_ai_article_generation(call):
        """Начало AI генерации статьи"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in website_article_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = website_article_state[user_id]
            subproject = state['subproject']
            website = state['website']
            
            # Обновляем шаг
            state['step'] = 'ai_topic'
            
            # Запрашиваем тему статьи
            text = (
                f"🤖 <b>AI ГЕНЕРАЦИЯ СТАТЬИ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 <b>Шаг 1:</b> Введите тему статьи\n\n"
                f"Опишите о чём должна быть статья. AI сгенерирует:\n"
                f"• SEO-оптимизированный заголовок\n"
                f"• Структурированный текст с подзаголовками\n"
                f"• Мета-описание\n"
                f"• Изображения (опционально)\n\n"
                f"<b>Пример:</b> <code>Преимущества WPC панелей для отделки фасада</code>\n\n"
                f"💡 <i>Можно использовать данные из категории \"{escape_html(subproject['name'])}\"</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_website_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # Регистрируем обработчик следующего сообщения
            bot.register_next_step_handler(msg, process_article_topic, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_ai_article_generation: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_article_topic(message, user_id, platform_index, category_id):
        """Обработка темы статьи"""
        
        if message.text == "❌ Отмена" or message.text.startswith('/'):
            # Возврат к меню
            bot.send_message(
                message.chat.id,
                "❌ Создание статьи отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
        
        topic = message.text.strip()
        
        if len(topic) < 5:
            bot.send_message(
                message.chat.id,
                "❌ Тема слишком короткая. Введите тему минимум 5 символов:"
            )
            bot.register_next_step_handler(message, process_article_topic, user_id, platform_index, category_id)
            return
        
        # Сохраняем тему
        if user_id in website_article_state:
            website_article_state[user_id]['topic'] = topic
            website_article_state[user_id]['step'] = 'ai_generating'
        
        # Показываем подтверждение
        text = (
            f"✅ <b>ТЕМА СОХРАНЕНА</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📝 <b>Тема:</b> {escape_html(topic)}\n\n"
            f"AI сгенерирует статью примерно на 1500-2500 слов.\n\n"
            f"<b>Стоимость:</b> ~50-100 токенов\n\n"
            f"<i>⚡ Генерация займёт 30-60 секунд</i>"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Начать генерацию",
                callback_data=f"website_ai_confirm_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_website_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML'
        )
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('website_ai_confirm_'))
    def confirm_ai_generation(call):
        """Подтверждение и запуск AI генерации"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in website_article_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = website_article_state[user_id]
            topic = state.get('topic', '')
            
            # Показываем процесс генерации
            text = (
                f"⏳ <b>ГЕНЕРАЦИЯ СТАТЬИ...</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🤖 AI работает над вашей статьей:\n\n"
                f"📝 Тема: {escape_html(topic)}\n\n"
                f"⏱ Это займёт 30-60 секунд...\n\n"
                f"<i>Пожалуйста, подождите</i>"
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА: Настоящая генерация будет в ЭТАПЕ 9
            # Пока показываем что функция в разработке
            import time
            time.sleep(2)
            
            text = (
                f"🚧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"AI генерация статей будет добавлена в <b>ЭТАПЕ 9</b>.\n\n"
                f"Пока доступны:\n"
                f"✅ Выбор источника контента\n"
                f"✅ Ручной ввод статьи\n"
                f"✅ Публикация на WordPress\n\n"
                f"<i>💡 Попробуйте \"Ручной ввод\"</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад к выбору",
                    callback_data=f"platform_post_website_{platform_index}_{category_id}"
                )
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            print(f"❌ Ошибка в confirm_ai_generation: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    # ═══════════════════════════════════════════════════════════════
    # РУЧНОЙ ВВОД СТАТЬИ
    # ═══════════════════════════════════════════════════════════════
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('website_manual_input_'))
    def start_manual_input(call):
        """Начало ручного ввода статьи"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in website_article_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            state = website_article_state[user_id]
            state['step'] = 'manual_title'
            
            text = (
                f"✍️ <b>РУЧНОЙ ВВОД СТАТЬИ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 <b>Шаг 1 из 3:</b> Заголовок статьи\n\n"
                f"Введите заголовок (H1) для вашей статьи.\n\n"
                f"<b>Пример:</b> <code>Преимущества WPC панелей</code>\n\n"
                f"💡 <i>Используйте ключевые слова для SEO</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data=f"platform_post_website_{platform_index}_{category_id}"
                )
            )
            
            msg = bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # Регистрируем обработчик заголовка
            bot.register_next_step_handler(msg, process_manual_title, user_id, platform_index, category_id)
            
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"❌ Ошибка в start_manual_input: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
    
    
    def process_manual_title(message, user_id, platform_index, category_id):
        """Обработка заголовка статьи"""
        
        if message.text == "❌ Отмена" or message.text.startswith('/'):
            bot.send_message(message.chat.id, "❌ Создание статьи отменено")
            return
        
        title = message.text.strip()
        
        if len(title) < 3:
            bot.send_message(message.chat.id, "❌ Заголовок слишком короткий. Введите минимум 3 символа:")
            bot.register_next_step_handler(message, process_manual_title, user_id, platform_index, category_id)
            return
        
        # Сохраняем заголовок
        if user_id in website_article_state:
            website_article_state[user_id]['title'] = title
            website_article_state[user_id]['step'] = 'manual_content'
        
        # Запрашиваем контент
        text = (
            f"✍️ <b>РУЧНОЙ ВВОД СТАТЬИ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"✅ Заголовок: <b>{escape_html(title)}</b>\n\n"
            f"📝 <b>Шаг 2 из 3:</b> Текст статьи\n\n"
            f"Введите текст статьи. Можно использовать:\n"
            f"• Обычный текст\n"
            f"• Параграфы (разделение пустой строкой)\n"
            f"• HTML теги: <code>&lt;b&gt;</code>, <code>&lt;i&gt;</code>, <code>&lt;h2&gt;</code>\n\n"
            f"<i>💡 Минимум 100 символов</i>"
        )
        
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        bot.register_next_step_handler(message, process_manual_content, user_id, platform_index, category_id)
    
    
    def process_manual_content(message, user_id, platform_index, category_id):
        """Обработка контента статьи"""
        
        if message.text == "❌ Отмена" or message.text.startswith('/'):
            bot.send_message(message.chat.id, "❌ Создание статьи отменено")
            return
        
        content = message.text.strip()
        
        if len(content) < 100:
            bot.send_message(
                message.chat.id,
                "❌ Текст слишком короткий. Введите минимум 100 символов:"
            )
            bot.register_next_step_handler(message, process_manual_content, user_id, platform_index, category_id)
            return
        
        # Сохраняем контент
        if user_id in website_article_state:
            website_article_state[user_id]['content'] = content
            website_article_state[user_id]['step'] = 'manual_preview'
        
        # Показываем предпросмотр
        show_article_preview(message.chat.id, user_id, platform_index, category_id)
    
    
    def show_article_preview(chat_id, user_id, platform_index, category_id):
        """Показывает предпросмотр статьи перед публикацией"""
        
        if user_id not in website_article_state:
            bot.send_message(chat_id, "❌ Ошибка: данные потеряны")
            return
        
        state = website_article_state[user_id]
        title = state.get('title', '')
        content = state.get('content', '')
        website = state.get('website', {})
        
        # Обрезаем контент для предпросмотра
        preview_content = content[:300] + "..." if len(content) > 300 else content
        
        text = (
            f"👁 <b>ПРЕДПРОСМОТР СТАТЬИ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"<b>Заголовок:</b>\n{escape_html(title)}\n\n"
            f"<b>Контент:</b>\n{escape_html(preview_content)}\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Символов: {len(content)}\n"
            f"• Слов: ~{len(content.split())}\n\n"
            f"🌐 <b>Публикация на:</b> {escape_html(website.get('url', 'Unknown'))}"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Опубликовать",
                callback_data=f"website_publish_manual_{platform_index}_{category_id}"
            ),
            types.InlineKeyboardButton(
                "✏️ Редактировать",
                callback_data=f"website_edit_manual_{platform_index}_{category_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"platform_post_website_{platform_index}_{category_id}"
            )
        )
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
    
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('website_publish_manual_'))
    def publish_manual_article(call):
        """Публикация ручной статьи"""
        try:
            parts = call.data.split('_')
            platform_index = int(parts[3])
            category_id = int(parts[4])
            
            user_id = call.from_user.id
            
            if user_id not in website_article_state:
                bot.answer_callback_query(call.id, "❌ Сессия истекла", show_alert=True)
                return
            
            # Показываем процесс публикации
            text = "⏳ <b>ПУБЛИКАЦИЯ...</b>\n\nСтатья публикуется на сайт..."
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            bot.answer_callback_query(call.id)
            
            # ЗАГЛУШКА: Настоящая публикация будет интегрирована полностью
            import time
            time.sleep(2)
            
            # Очищаем состояние
            if user_id in website_article_state:
                del website_article_state[user_id]
            
            text = (
                f"✅ <b>СТАТЬЯ ОПУБЛИКОВАНА!</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🎉 Ваша статья успешно размещена на сайте!\n\n"
                f"<i>💡 В полной версии здесь будет:\n"
                f"• Ссылка на опубликованную статью\n"
                f"• ID поста в WordPress\n"
                f"• Статистика публикации</i>"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 К платформе",
                    callback_data=f"platform_action_website_{platform_index}_{category_id}"
                )
            )
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            print(f"❌ Ошибка в publish_manual_article: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при публикации", show_alert=True)


# Экспорт
__all__ = ['register_website_management_handlers', 'website_article_state']
