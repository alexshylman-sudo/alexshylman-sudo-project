"""
Подключение Instagram
"""
from telebot import types
from loader import bot, db
from utils import escape_html
from .utils import check_global_platform_uniqueness


@bot.callback_query_handler(func=lambda call: call.data == "add_platform_instagram")
def add_platform_instagram_start(call):
    """Начало подключения Instagram"""
    user_id = call.from_user.id
    
    text = (
        "📸 <b>ПОДКЛЮЧЕНИЕ INSTAGRAM</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "<b>Шаг 1 из 2:</b> Username аккаунта\n\n"
        "Отправьте username вашего Instagram Business аккаунта.\n\n"
        "<b>Пример:</b> <code>@mycompany</code>\n\n"
        "<i>💡 Необходим Instagram Business аккаунт</i>"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_platform_menu")
    )
    
    user_adding_platform[user_id] = {
        'type': 'instagram',
        'step': 'username',
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
    
    bot.answer_callback_query(call.id, "📝 Ожидаю username...")


# ═══════════════════════════════════════════════════════════════
# ВКОНТАКТЕ
# ═══════════════════════════════════════════════════════════════


print("✅ handlers/platform_connections/instagram.py загружен")
