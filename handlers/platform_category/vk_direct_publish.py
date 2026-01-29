# -*- coding: utf-8 -*-
"""
Прямая публикация в VK (без показа в чате)
Аналогично Pinterest - генерация и публикация в один клик
"""
from loader import bot, db
from telebot import types
from utils import escape_html
import requests
import tempfile
import os
import random
import json


def publish_vk_directly(call, user_id, bot_id, platform_id, category_id, cost):
    """
    Прямая публикация в VK с генерацией изображения
    
    Args:
        call: callback query
        user_id: ID пользователя Telegram
        bot_id: ID бота (категории)
        platform_id: VK user_id
        category_id: ID категории
        cost: Стоимость (50 токенов)
    """
    # Инициализируем прогресс-бар
    from utils.generation_progress import show_generation_progress
    progress = show_generation_progress(call.message.chat.id, "vk", total_steps=4)
    progress.start("Подготовка к генерации...")
    
    try:
        # Шаг 1: Получаем данные категории
        category = db.get_category(category_id)
        if not category:
            progress.finish()
            db.update_tokens(user_id, cost)  # Возвращаем токены
            bot.send_message(call.message.chat.id, "❌ Ошибка: категория не найдена")
            return
        
        category_name = category['name']
        description = category.get('description', '')
        keywords = category.get('keywords', [])
        
        # Получаем настройки изображения для VK
        settings = category.get('settings', {})
        if isinstance(settings, str):
            settings = json.loads(settings)
        
        platform_image_settings = settings.get('vk_image_settings', {})
        
        # Если настроек нет - используем дефолтные
        if not platform_image_settings or 'formats' not in platform_image_settings:
            platform_image_settings = {
                'formats': ['1:1', '4:5'],
                'styles': [],
                'tones': [],
                'cameras': [],
                'angles': [],
                'quality': 'high_quality'
            }
        
        # Шаг 2: Генерируем изображение
        progress.update(1, "🖼 Генерирую изображение...", f"📝 Категория: {category_name}")
        
        from ai.image_generator import generate_image
        from handlers.platform_settings.utils import build_image_prompt
        
        # Строим промпт
        use_collage = random.random() < 0.2
        
        if use_collage:
            base_prompt = f"{category_name}, collection of photos, multiple panels"
        else:
            base_prompt = f"{category_name}, single unified image"
        
        # Добавляем описание
        if description:
            desc_phrases = [s.strip() for s in description.split('.') if s.strip() and len(s.strip()) > 10]
            if desc_phrases:
                selected_phrase = random.choice(desc_phrases)
                base_prompt = f"{base_prompt}. {selected_phrase}"
        
        # Строим полный промпт
        full_prompt, image_format = build_image_prompt(base_prompt, platform_image_settings)
        
        print(f"🎨 VK промпт: {full_prompt[:150]}...")
        print(f"📐 Формат: {image_format}")
        
        # Генерируем изображение
        image_result = generate_image(full_prompt, aspect_ratio=image_format)
        
        if not image_result.get('success'):
            error_msg = image_result.get('error', 'Ошибка генерации')
            progress.finish()
            db.update_tokens(user_id, cost)
            bot.send_message(call.message.chat.id, f"❌ Ошибка генерации изображения: {error_msg}\n\nТокены возвращены.")
            return
        
        image_bytes = image_result.get('image_bytes')
        if not image_bytes:
            progress.finish()
            db.update_tokens(user_id, cost)
            bot.send_message(call.message.chat.id, "❌ Изображение не содержит данных\n\nТокены возвращены.")
            return
        
        # Сохраняем во временный файл
        fd, image_path = tempfile.mkstemp(suffix='.jpg', prefix='vk_post_')
        with os.fdopen(fd, 'wb') as f:
            f.write(image_bytes)
        
        # Шаг 3: Генерируем текст поста
        progress.update(2, "✍️ Генерирую текст...", f"📝 Категория: {category_name}")
        
        from ai.text_generator import generate_social_post
        
        # Формируем topic из названия и описания
        if description:
            topic = f"{category_name}. {description[:200]}"
        else:
            topic = category_name
        
        post_result = generate_social_post(
            topic=topic,
            platform='vk',
            style='engaging',
            include_hashtags=True,
            include_emoji=True
        )
        
        if not post_result.get('success'):
            error_msg = post_result.get('error', 'Ошибка генерации текста')
            progress.finish()
            db.update_tokens(user_id, cost)
            os.unlink(image_path)
            bot.send_message(call.message.chat.id, f"❌ Ошибка генерации текста: {error_msg}\n\nТокены возвращены.")
            return
        
        post_text = post_result.get('text', '')
        
        # Шаг 4: Публикуем в VK
        progress.update(3, "📤 Публикую в VK...", f"📝 Категория: {category_name}")
        
        # Получаем валидный токен (автоматически обновит если истёк)
        from handlers.vk_integration.vk_oauth import VKOAuth
        
        access_token = VKOAuth.ensure_valid_token(db, user_id, platform_id)
        
        if not access_token:
            progress.finish()
            db.update_tokens(user_id, cost)
            try:
                os.unlink(image_path)
            except:
                pass
            bot.send_message(
                call.message.chat.id,
                "❌ VK не подключен или токен истёк\n\n"
                "Переподключите VK через 'МОИ ПОДКЛЮЧЕНИЯ'\n\n"
                "Токены возвращены."
            )
            return
        
        # Получаем VK подключение (личная страница или группа)
        user = db.get_user(user_id)
        connections = user.get('platform_connections', {})
        vks = connections.get('vks', [])
        
        vk_connection = None
        
        # Ищем подключение по platform_id
        # platform_id может быть:
        # - user_id для личной страницы
        # - group_id для группы (отрицательный)
        for vk in vks:
            vk_type = vk.get('type', 'user')
            
            if vk_type == 'user':
                # Личная страница
                if str(vk.get('user_id')) == str(platform_id):
                    vk_connection = vk
                    break
            elif vk_type == 'group':
                # Группа (сравниваем с group_id)
                if str(vk.get('group_id')) == str(platform_id):
                    vk_connection = vk
                    break
        
        if not vk_connection:
            progress.finish()
            db.update_tokens(user_id, cost)
            try:
                os.unlink(image_path)
            except:
                pass
            bot.send_message(call.message.chat.id, "❌ VK не подключен\n\nТокены возвращены.")
            return
        
        # Загружаем изображение в VK
        try:
            # Шаг 1: Получаем URL для загрузки
            upload_server_response = requests.get(
                "https://api.vk.com/method/photos.getWallUploadServer",
                params={
                    "access_token": access_token,
                    "v": "5.131"
                },
                timeout=10
            )
            
            upload_server_data = upload_server_response.json()
            
            if 'error' in upload_server_data:
                raise Exception(upload_server_data['error'].get('error_msg', 'VK API error'))
            
            upload_url = upload_server_data['response']['upload_url']
            
            # Шаг 2: Загружаем фото
            with open(image_path, 'rb') as photo_file:
                upload_response = requests.post(
                    upload_url,
                    files={'photo': photo_file},
                    timeout=30
                )
            
            upload_result = upload_response.json()
            
            # Шаг 3: Сохраняем фото
            save_response = requests.get(
                "https://api.vk.com/method/photos.saveWallPhoto",
                params={
                    "access_token": access_token,
                    "v": "5.131",
                    "photo": upload_result['photo'],
                    "server": upload_result['server'],
                    "hash": upload_result['hash']
                },
                timeout=10
            )
            
            save_result = save_response.json()
            
            if 'error' in save_result:
                raise Exception(save_result['error'].get('error_msg', 'VK save error'))
            
            photo_data = save_result['response'][0]
            photo_attachment = f"photo{photo_data['owner_id']}_{photo_data['id']}"
            
            # Определяем owner_id и from_group в зависимости от типа
            vk_type = vk_connection.get('type', 'user')
            
            if vk_type == 'group':
                # Для группы
                owner_id = vk_connection.get('group_id')  # Уже отрицательный
                from_group = 1  # Публикация от имени группы
            else:
                # Для личной страницы
                owner_id = vk_connection.get('user_id')
                from_group = 0  # Публикация от имени пользователя
            
            # Шаг 4: Публикуем пост
            post_params = {
                "access_token": access_token,
                "v": "5.131",
                "message": post_text,
                "attachments": photo_attachment,
                "from_group": from_group
            }
            
            # Добавляем owner_id только для групп
            if vk_type == 'group':
                post_params["owner_id"] = owner_id
            
            post_response = requests.get(
                "https://api.vk.com/method/wall.post",
                params=post_params,
                timeout=10
            )
            
            post_result_vk = post_response.json()
            
            if 'error' in post_result_vk:
                raise Exception(post_result_vk['error'].get('error_msg', 'VK post error'))
            
            post_id = post_result_vk['response']['post_id']
            # owner_id уже определен выше
            post_url = f"https://vk.com/wall{owner_id}_{post_id}"
            
            # Успех!
            progress.finish()
            
            # Удаляем временный файл
            try:
                os.unlink(image_path)
            except:
                pass
            
            # Показываем результат
            text = (
                f"🎉 <b>ПОСТ ОПУБЛИКОВАН В VK!</b>\n\n"
                f"📂 Категория: {escape_html(category_name)}\n"
                f"📊 Символов: {len(post_text)}\n"
                f"💰 Списано: {cost} токенов\n\n"
                f"✅ Изображение создано\n"
                f"✅ Текст сгенерирован\n"
                f"✅ Опубликовано на стене VK"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🔗 Открыть пост", url=post_url)
            )
            markup.add(
                types.InlineKeyboardButton(
                    "🎨 Генерировать ещё",
                    callback_data=f"platform_ai_post_vk_{category_id}_{bot_id}_{platform_id}"
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "🔙 Назад",
                    callback_data=f"platform_menu_{category_id}_{bot_id}_vk_{platform_id}"
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
            progress.finish()
            db.update_tokens(user_id, cost)
            
            try:
                os.unlink(image_path)
            except:
                pass
            
            print(f"❌ Ошибка публикации в VK: {e}")
            bot.send_message(
                call.message.chat.id,
                f"❌ Ошибка публикации в VK: {e}\n\nТокены возвращены."
            )
    
    except Exception as e:
        progress.finish()
        db.update_tokens(user_id, cost)
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(
            call.message.chat.id,
            f"❌ Критическая ошибка: {e}\n\nТокены возвращены."
        )


print("✅ handlers/platform_category/vk_direct_publish.py загружен")
