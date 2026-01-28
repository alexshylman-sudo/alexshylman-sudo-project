# -*- coding: utf-8 -*-
"""
Flask Webhook для обработки VK OAuth callback
"""
from flask import Flask, request, redirect, render_template_string
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from handlers.vk_integration.vk_oauth import VKOAuth
from database.database import db

app = Flask(__name__)


# HTML страница для успешной авторизации
SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VK подключен</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .button {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: #0088cc;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✅</div>
        <h1>VK успешно подключен!</h1>
        <p>Ваш аккаунт ВКонтакте успешно подключен к боту.</p>
        <p>Вы можете закрыть это окно и вернуться в Telegram.</p>
        <a href="https://t.me/best_seo_master_bot" class="button">Вернуться в бот</a>
    </div>
</body>
</html>
"""

ERROR_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ошибка подключения</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .button {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: #0088cc;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Ошибка подключения</h1>
        <p>{{ error_message }}</p>
        <p>Попробуйте еще раз или обратитесь в поддержку.</p>
        <a href="https://t.me/best_seo_master_bot" class="button">Вернуться в бот</a>
    </div>
</body>
</html>
"""


@app.route('/vk_callback')
def vk_callback():
    """
    Обработчик OAuth callback от VK
    
    Получает:
    - code: Authorization code
    - state: tg_{telegram_user_id}
    """
    # Получаем параметры
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    device_id = request.args.get('device_id')  # Нужен для VK ID
    
    print(f"\n{'='*80}")
    print(f"🔵 VK CALLBACK ПОЛУЧЕН")
    print(f"   Code: {code[:20] if code else None}...")
    print(f"   State: {state}")
    print(f"   Device ID: {device_id}")
    print(f"   Error: {error}")
    print(f"{'='*80}\n")
    
    # Проверяем ошибку
    if error:
        error_description = request.args.get('error_description', 'Неизвестная ошибка')
        print(f"❌ VK OAuth error: {error} - {error_description}")
        return render_template_string(ERROR_PAGE, error_message=error_description)
    
    # Проверяем наличие code
    if not code:
        print(f"❌ VK OAuth: отсутствует code")
        return render_template_string(ERROR_PAGE, error_message="Отсутствует код авторизации")
    
    # Извлекаем telegram_user_id из state
    if not state or not state.startswith('tg_'):
        print(f"❌ VK OAuth: некорректный state")
        return render_template_string(ERROR_PAGE, error_message="Некорректный state")
    
    try:
        telegram_user_id = int(state.replace('tg_', ''))
    except:
        print(f"❌ VK OAuth: не удалось извлечь telegram_user_id из state")
        return render_template_string(ERROR_PAGE, error_message="Некорректный формат state")
    
    # Получаем PKCE code_verifier для этого пользователя
    from handlers.vk_integration.vk_config import get_pkce_verifier
    code_verifier = get_pkce_verifier(telegram_user_id)
    
    if not code_verifier:
        print(f"❌ VK OAuth: PKCE verifier не найден для пользователя {telegram_user_id}")
        return render_template_string(ERROR_PAGE, error_message="Сессия истекла, попробуйте снова")
    
    # Обмениваем code на access_token с PKCE
    vk_oauth = VKOAuth()
    token_data = vk_oauth.exchange_code_for_token(code, code_verifier, device_id)
    
    if not token_data:
        print(f"❌ VK OAuth: не удалось обменять code на token")
        return render_template_string(ERROR_PAGE, error_message="Не удалось получить токен доступа")
    
    print(f"✅ VK Token получен:")
    print(f"   User ID: {token_data.get('user_id')}")
    print(f"   Email: {token_data.get('email', 'не предоставлен')}")
    
    # Сохраняем подключение в БД
    success = vk_oauth.save_vk_connection(db, telegram_user_id, token_data)
    
    if not success:
        print(f"❌ Не удалось сохранить VK подключение")
        return render_template_string(ERROR_PAGE, error_message="Ошибка сохранения данных")
    
    # Отправляем уведомление и показываем подключения
    try:
        from loader import bot  # Импортируем только здесь
        from handlers.platform_connections.main_menu import show_connections_menu
        
        # Отправляем уведомление
        bot.send_message(
            telegram_user_id,
            "✅ <b>VK успешно подключен!</b>\n\n"
            "Теперь вы можете публиковать посты в ВКонтакте.",
            parse_mode='HTML'
        )
        
        # Показываем меню подключений
        from telebot import types
        
        # Создаём фейковый callback для вызова функции
        class FakeCall:
            def __init__(self, user_id):
                self.from_user = types.User(user_id, False, 'User')
                self.message = None
                self.id = 0
        
        fake_call = FakeCall(telegram_user_id)
        
        # Получаем все подключения
        user = db.get_user(telegram_user_id)
        connections = user.get('platform_connections', {})
        
        if not isinstance(connections, dict):
            connections = {}
        
        # Считаем подключения
        websites = connections.get('websites', [])
        instagrams = connections.get('instagrams', [])
        vks = connections.get('vks', [])
        pinterests = connections.get('pinterests', [])
        telegrams = connections.get('telegrams', [])
        
        text = (
            "🔌 <b>МОИ ПОДКЛЮЧЕНИЯ</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "Управляйте подключениями к внешним площадкам:\n\n"
        )
        
        has_connections = False
        
        if websites:
            has_connections = True
            text += f"🌐 <b>Сайты ({len(websites)}):</b>\n"
            for idx, site in enumerate(websites, 1):
                url = site.get('url', 'Unknown')
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc or url
                    text += f"   {idx}. {domain}\n"
                except:
                    text += f"   {idx}. {url}\n"
            text += "\n"
        
        if vks:
            has_connections = True
            text += f"💬 <b>ВКонтакте ({len(vks)}):</b>\n"
            for idx, vk in enumerate(vks, 1):
                group_name = vk.get('group_name', 'Unknown')
                text += f"   {idx}. {group_name}\n"
            text += "\n"
        
        if pinterests:
            has_connections = True
            text += f"📌 <b>Pinterest ({len(pinterests)}):</b>\n"
            for idx, pin in enumerate(pinterests, 1):
                board = pin.get('board', 'Unknown')
                text += f"   {idx}. {board}\n"
            text += "\n"
        
        if telegrams:
            has_connections = True
            text += f"✈️ <b>Telegram ({len(telegrams)}):</b>\n"
            for idx, tg in enumerate(telegrams, 1):
                channel = tg.get('channel', 'Unknown')
                text += f"   {idx}. @{channel}\n"
            text += "\n"
        
        if not has_connections:
            text += "У вас пока нет подключенных площадок.\n\n"
        
        text += "━━━━━━━━━━━━━━\n\n<i>💡 Подключите площадки для автопостинга контента</i>"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("➕ Добавить площадку", callback_data="add_platform_menu"),
            types.InlineKeyboardButton("📝 Управление подключениями", callback_data="manage_platforms"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")
        )
        
        bot.send_message(
            telegram_user_id,
            text,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
    except Exception as e:
        print(f"⚠️ Не удалось отправить уведомление в Telegram: {e}")
        import traceback
        traceback.print_exc()
    
    # Показываем страницу успеха
    return render_template_string(SUCCESS_PAGE)


@app.route('/health')
def health_check():
    """Health check endpoint для Render.com"""
    return {'status': 'ok', 'service': 'vk_webhook'}, 200


@app.route('/')
def index():
    """Главная страница"""
    return {
        'service': 'VK OAuth Webhook',
        'status': 'running',
        'endpoints': {
            '/vk_callback': 'VK OAuth callback handler',
            '/health': 'Health check'
        }
    }, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


print("✅ VK Webhook Server готов к запуску")
