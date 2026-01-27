"""
Angle Selector - Выбор ракурса/угла обзора
Опциональные настройки для детальной настройки изображений
"""
from telebot import types
from loader import bot
from database.database import db
from .constants import ANGLE_PRESETS, PLATFORM_NAMES
from .utils import get_platform_settings, save_platform_settings


# ═══════════════════════════════════════════════════════════════
# РАКУРСЫ
# ═══════════════════════════════════════════════════════════════

def show_angle_selector(call, platform_type, category_id, bot_id):
    """
    Показать интерфейс выбора ракурса
    """
    category = db.get_category(category_id)
    if not category:
        bot.answer_callback_query(call.id, "❌ Категория не найдена")
        return
    
    category_name = category.get('name', 'Без названия')
    settings = get_platform_settings(category, platform_type)
    current_angles = settings['angles']
    platform_name = PLATFORM_NAMES.get(platform_type, platform_type.upper())
    
    # Текст
    if len(current_angles) == 0:
        selected_text = "Не выбраны"
    elif len(current_angles) == len(ANGLE_PRESETS):
        selected_text = "Все выбраны"
    else:
        selected_text = f"{len(current_angles)} из {len(ANGLE_PRESETS)}"
    
    text = (
        f"📐 <b>РАКУРС И УГОЛ ОБЗОРА</b>\n"
        f"📱 Платформа: {platform_name}\n"
        f"📂 Категория: {category_name}\n"
        "━━━━━━━━━━━━━━\n\n"
        f"✅ Выбрано: <b>{selected_text}</b>\n\n"
        "Выберите ракурс съёмки. Можно несколько.\n"
        "💡 Если не выбрано - ракурс случайный."
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Кнопки ракурсов в 2 колонки
    for angle_code, angle_data in ANGLE_PRESETS.items():
        is_selected = angle_code in current_angles
        emoji = angle_data.get('emoji', '📐')
        button_text = f"{emoji} {angle_data['name']}" if not is_selected else f"✅ {angle_data['name']}"
        
        markup.add(
            types.InlineKeyboardButton(
                button_text,
                callback_data=f"toggle_angle_{platform_type}_{category_id}_{bot_id}_{angle_code}"
            )
        )
    
    # Кнопки управления
    markup.row(
        types.InlineKeyboardButton(
            "✅ Все",
            callback_data=f"angles_all_{platform_type}_{category_id}_{bot_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Сбросить",
            callback_data=f"angles_clear_{platform_type}_{category_id}_{bot_id}"
        )
    )
    
    # Навигация
    markup.add(
        types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data=f"platform_images_menu_{platform_type}_{category_id}_{bot_id}_"
        )
    )
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                            reply_markup=markup, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    bot.answer_callback_query(call.id)


def handle_toggle_angle(call, platform_type, category_id, bot_id, angle_code):
    """Переключить ракурс"""
    category = db.get_category(category_id)
    if not category:
        bot.answer_callback_query(call.id, "❌ Категория не найдена")
        return
    
    settings = get_platform_settings(category, platform_type)
    current_angles = settings['angles'].copy() if settings['angles'] else []
    
    # Переключаем
    if angle_code in current_angles:
        current_angles.remove(angle_code)
    else:
        current_angles.append(angle_code)
    
    # Сохраняем
    save_platform_settings(db, category_id, platform_type, angles=current_angles)
    
    # Обновляем интерфейс
    show_angle_selector(call, platform_type, category_id, bot_id)


def handle_angles_all(call, platform_type, category_id, bot_id):
    """Выбрать все ракурсы"""
    all_angles = list(ANGLE_PRESETS.keys())
    save_platform_settings(db, category_id, platform_type, angles=all_angles)
    show_angle_selector(call, platform_type, category_id, bot_id)


def handle_angles_clear(call, platform_type, category_id, bot_id):
    """Очистить выбор ракурсов"""
    save_platform_settings(db, category_id, platform_type, angles=[])
    show_angle_selector(call, platform_type, category_id, bot_id)


def register_angle_handlers(bot_instance):
    """Регистрация обработчиков для выбора ракурсов"""
    
    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith('next_angle_'))
    def handle_next_angle(call):
        parts = call.data.split('_')
        platform_type = parts[2]
        category_id = int(parts[3])
        bot_id = int(parts[4])
        show_angle_selector(call, platform_type, category_id, bot_id)
    
    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith('toggle_angle_'))
    def handle_toggle(call):
        parts = call.data.split('_')
        # toggle_angle_pinterest_123_456_close_up
        # Собираем angle_code из всех частей после bot_id
        platform_type = parts[2]
        category_id = int(parts[3])
        bot_id = int(parts[4])
        angle_code = "_".join(parts[5:])  # Собираем всё что после bot_id
        handle_toggle_angle(call, platform_type, category_id, bot_id, angle_code)
    
    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith('angles_all_'))
    def handle_all(call):
        parts = call.data.split('_')
        platform_type = parts[2]
        category_id = int(parts[3])
        bot_id = int(parts[4])
        handle_angles_all(call, platform_type, category_id, bot_id)
    
    @bot_instance.callback_query_handler(func=lambda call: call.data.startswith('angles_clear_'))
    def handle_clear(call):
        parts = call.data.split('_')
        platform_type = parts[2]
        category_id = int(parts[3])
        bot_id = int(parts[4])
        handle_angles_clear(call, platform_type, category_id, bot_id)
    
    print("  ├─ angle_selector.py загружен")


print("✅ platform_settings/angle_selector.py загружен")
