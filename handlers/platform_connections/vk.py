"""
Подключение VK (ВКонтакте)
Поддерживает как группы, так и личные страницы
"""
from telebot import types
from loader import bot, db
from utils import escape_html
from .utils import check_global_platform_uniqueness
import re
import json


# Словарь для хранения состояния добавления платформы
user_adding_platform = {}


@bot.callback_query_handler(func=lambda call: call.data == "add_platform_vk")
def add_platform_vk_start(call):
    """Начало подключения ВКонтакте"""
    user_id = call.from_user.id
    
    text = (
        "💬 <b>ПОДКЛЮЧЕНИЕ ВКОНТАКТЕ</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "<b>Шаг 1 из 3:</b> Выберите тип\n\n"
        "Куда вы хотите публиковать посты?"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("👥 Группа/Сообщество", callback_data="vk_type_group")
    )
    markup.add(
        types.InlineKeyboardButton("👤 Личная страница", callback_data="vk_type_user")
    )
    markup.add(
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
    )
    
    user_adding_platform[user_id] = {
        'type': 'vk',
        'step': 'select_type',
        'data': {}
    }
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("vk_type_"))
def handle_vk_type_selection(call):
    """Обработка выбора типа VK (группа или личная страница)"""
    user_id = call.from_user.id
    vk_type = call.data.split("_")[2]  # group или user
    
    if user_id not in user_adding_platform:
        bot.answer_callback_query(call.id, "❌ Сессия истекла. Начните заново.")
        return
    
    user_adding_platform[user_id]['data']['vk_type'] = vk_type
    user_adding_platform[user_id]['step'] = 'enter_id'
    
    if vk_type == 'group':
        text = (
            "💬 <b>ПОДКЛЮЧЕНИЕ ГРУППЫ VK</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "<b>Шаг 2 из 3:</b> ID группы\n\n"
            "Отправьте ID или ссылку на вашу группу ВКонтакте.\n\n"
            "<b>Примеры:</b>\n"
            "<code>mycompany</code>\n"
            "<code>https://vk.com/mycompany</code>\n"
            "<code>club123456</code>\n\n"
            "<i>💡 Вы должны быть администратором группы</i>"
        )
    else:  # user
        text = (
            "👤 <b>ПОДКЛЮЧЕНИЕ ЛИЧНОЙ СТРАНИЦЫ VK</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "<b>Шаг 2 из 3:</b> ID страницы\n\n"
            "Отправьте ID или ссылку на вашу страницу ВКонтакте.\n\n"
            "<b>Примеры:</b>\n"
            "<code>id123456789</code>\n"
            "<code>https://vk.com/id123456789</code>\n"
            "<code>myusername</code>\n\n"
            "<i>💡 Публикация будет на вашей стене</i>"
        )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.from_user.id in user_adding_platform 
                     and user_adding_platform[message.from_user.id].get('type') == 'vk'
                     and user_adding_platform[message.from_user.id].get('step') == 'enter_id')
def handle_vk_id_input(message):
    """Обработка ввода ID группы или страницы VK"""
    user_id = message.from_user.id
    vk_input = message.text.strip()
    
    if user_id not in user_adding_platform:
        return
    
    vk_type = user_adding_platform[user_id]['data'].get('vk_type')
    
    # Извлекаем ID из различных форматов
    vk_id = extract_vk_id(vk_input, vk_type)
    
    if not vk_id:
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат ID или ссылки.\n\n"
            "Попробуйте еще раз или нажмите ❌ Отмена"
        )
        return
    
    # Сохраняем ID
    user_adding_platform[user_id]['data']['vk_id'] = vk_id
    user_adding_platform[user_id]['data']['vk_input'] = vk_input
    user_adding_platform[user_id]['step'] = 'enter_token'
    
    # Генерируем ссылку для получения токена (используем старое VK приложение)
    if vk_type == 'group':
        scope = "wall,photos,groups,offline"
        token_info = "группы"
    else:
        scope = "wall,photos,offline"
        token_info = "личной страницы"
    
    # Используем старое VK приложение (54431232) вместо VK ID
    token_url = f"https://oauth.vk.com/authorize?client_id=54431232&scope={scope}&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token"
    
    text = (
        f"🔑 <b>ПОДКЛЮЧЕНИЕ VK</b>\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"<b>Шаг 3 из 3:</b> Токен доступа\n\n"
        f"✅ ID {token_info}: <code>{vk_id}</code>\n\n"
        f"<b>Получите токен доступа:</b>\n"
        f"1. Нажмите кнопку ниже\n"
        f"2. Разрешите доступ\n"
        f"3. Скопируйте токен из адресной строки\n"
        f"4. Отправьте токен сюда\n\n"
        f"<i>💡 Токен начинается с vk1.a. или похож на длинную строку символов</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔑 Получить токен", url=token_url)
    )
    markup.add(
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
    )
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.from_user.id in user_adding_platform 
                     and user_adding_platform[message.from_user.id].get('type') == 'vk'
                     and user_adding_platform[message.from_user.id].get('step') == 'enter_token')
def handle_vk_token_input(message):
    """Обработка ввода токена VK"""
    user_id = message.from_user.id
    token_input = message.text.strip()
    
    if user_id not in user_adding_platform:
        return
    
    # Извлекаем токен из URL если пользователь вставил всю ссылку
    token = extract_vk_token(token_input)
    
    if not token:
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат токена.\n\n"
            "Токен должен начинаться с vk1.a. или быть длинной строкой символов.\n\n"
            "Попробуйте еще раз или нажмите ❌ Отмена"
        )
        return
    
    vk_data = user_adding_platform[user_id]['data']
    vk_type = vk_data['vk_type']
    vk_id = vk_data['vk_id']
    
    # Сохраняем платформу в БД
    try:
        # Получаем пользователя
        user = db.get_user(user_id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
            return
        
        # Проверяем уникальность
        if not check_global_platform_uniqueness(db, 'vk', vk_id):
            bot.send_message(
                message.chat.id,
                "❌ Эта страница/группа VK уже подключена к другому пользователю"
            )
            return
        
        # Получаем существующие подключения
        platform_connections = user.get('platform_connections', {})
        if isinstance(platform_connections, str):
            platform_connections = json.loads(platform_connections)
        
        # Добавляем VK
        platform_connections['vk'] = {
            'type': vk_type,  # 'group' или 'user'
            'id': vk_id,
            'access_token': token,
            'status': 'active',
            'connected_at': 'now()',
            'name': vk_id
        }
        
        # Сохраняем в БД
        db.cursor.execute("""
            UPDATE users
            SET platform_connections = %s::jsonb
            WHERE id = %s
        """, (json.dumps(platform_connections), user_id))
        
        db.conn.commit()
        
        # Очищаем состояние
        del user_adding_platform[user_id]
        
        if vk_type == 'group':
            success_text = f"✅ <b>Группа VK подключена!</b>\n\n🆔 ID: <code>{vk_id}</code>"
        else:
            success_text = f"✅ <b>Личная страница VK подключена!</b>\n\n🆔 ID: <code>{vk_id}</code>"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📱 Мои платформы", callback_data="platforms")
        )
        
        bot.send_message(message.chat.id, success_text, reply_markup=markup, parse_mode='HTML')
        
    except Exception as e:
        print(f"❌ Ошибка сохранения VK: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении. Попробуйте еще раз.")


def extract_vk_id(input_text: str, vk_type: str) -> str:
    """
    Извлекает VK ID из различных форматов
    
    Примеры:
    - mycompany → mycompany
    - https://vk.com/mycompany → mycompany
    - club123456 → club123456
    - id123456789 → id123456789
    """
    input_text = input_text.strip()
    
    # Удаляем пробелы и лишние символы
    input_text = input_text.replace(' ', '')
    
    # Если это полная ссылка
    if 'vk.com/' in input_text:
        # Извлекаем часть после vk.com/
        match = re.search(r'vk\.com/([^/?#]+)', input_text)
        if match:
            vk_id = match.group(1)
            return vk_id
    
    # Если это просто ID
    # Для групп: может быть club123, public123, event123, или короткое имя
    # Для пользователей: может быть id123 или короткое имя
    if vk_type == 'group':
        # Принимаем club, public, event, или любое короткое имя
        if re.match(r'^(club|public|event)\d+$', input_text) or re.match(r'^[a-zA-Z0-9_]+$', input_text):
            return input_text
    else:  # user
        # Принимаем id123456 или короткое имя
        if re.match(r'^id\d+$', input_text) or re.match(r'^[a-zA-Z0-9_]+$', input_text):
            return input_text
    
    return None


def extract_vk_token(input_text: str) -> str:
    """
    Извлекает VK токен из различных форматов
    
    Примеры:
    - vk1.a.xxxxx → vk1.a.xxxxx
    - https://oauth.vk.com/blank.html#access_token=vk1.a.xxxxx&... → vk1.a.xxxxx
    - длинная строка символов → длинная строка
    """
    input_text = input_text.strip()
    
    # Если это URL с токеном
    if 'access_token=' in input_text:
        match = re.search(r'access_token=([^&]+)', input_text)
        if match:
            return match.group(1)
    
    # Если это просто токен
    # Токен VK обычно начинается с vk1.a. или длинная строка букв и цифр
    if re.match(r'^vk1\.[a-zA-Z]\.[a-zA-Z0-9_-]+$', input_text):
        return input_text
    
    # Старый формат токенов (длинная строка)
    if len(input_text) > 50 and re.match(r'^[a-zA-Z0-9]+$', input_text):
        return input_text
    
    return None


print("✅ handlers/platform_connections/vk.py загружен")

