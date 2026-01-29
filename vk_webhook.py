# -*- coding: utf-8 -*-
"""
Flask Webhook для обработки VK OAuth callback
"""
from flask import Flask, request, redirect, render_template_string
import os
import sys
import json

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from handlers.vk_integration.vk_oauth import VKOAuth
# БД будет создаваться локально в каждом callback

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
    
    # Старый OAuth не требует PKCE verifier
    # Обмениваем code на access_token
    vk_oauth = VKOAuth()
    token_data = vk_oauth.exchange_code_for_token(code)
    
    if not token_data:
        print(f"❌ VK OAuth: не удалось обменять code на token")
        return render_template_string(ERROR_PAGE, error_message="Не удалось получить токен доступа")
    
    print(f"✅ VK Token получен:")
    print(f"   User ID: {token_data.get('user_id')}")
    print(f"   Email: {token_data.get('email', 'не предоставлен')}")
    
    # ============================================
    # ============================================
    # ПОЛУЧАЕМ СПИСОК ГРУПП (СТАРЫЙ OAUTH)
    # ============================================
    
    # Получаем список групп где пользователь админ
    user_groups = vk_oauth.get_user_groups(token_data['access_token'])
    
    print(f"📝 Доступно групп для подключения: {len(user_groups)}")
    
    # ============================================
    # СОХРАНЯЕМ ВРЕМЕННЫЕ ДАННЫЕ ДЛЯ ВЫБОРА
    # ============================================
    
    # Создаём свежее подключение к БД для сохранения временных данных
    from database.database import Database
    db_temp = Database()
    
    try:
        # Сохраняем токен и группы во временное хранилище для выбора
        vk_selection_data = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'device_id': token_data.get('device_id'),
            'expires_in': token_data.get('expires_in', 0),
            'user_id': token_data['user_id'],
            'email': token_data.get('email'),
            'available_groups': user_groups
        }
        
        # Получаем пользователя и сохраняем временные данные
        user = db_temp.get_user(telegram_user_id)
        connections = user.get('platform_connections', {})
        if isinstance(connections, str):
            connections = json.loads(connections)
        
        connections['_vk_selection_pending'] = vk_selection_data
        
        db_temp.cursor.execute("""
            UPDATE users
            SET platform_connections = %s::jsonb
            WHERE id = %s
        """, (json.dumps(connections), telegram_user_id))
        db_temp.conn.commit()
        
        # Закрываем БД
        db_temp.cursor.close()
        db_temp.conn.close()
        
    except Exception as e:
        print(f"⚠️ Ошибка сохранения временных данных: {e}")
        try:
            db_temp.cursor.close()
            db_temp.conn.close()
        except:
            pass
    
    # ============================================
    # ОТПРАВЛЯЕМ TELEGRAM СООБЩЕНИЕ С ВЫБОРОМ
    # ============================================
    
    try:
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        if BOT_TOKEN:
            import requests as req
            telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            
            # Получаем информацию о пользователе VK
            vk_user_info = vk_oauth.get_user_info(token_data['access_token'], token_data['user_id'])
            user_name = f"{vk_user_info.get('first_name', '')} {vk_user_info.get('last_name', '')}".strip() if vk_user_info else "Личная страница"
            
            # Формируем текст сообщения
            message_text = (
                "✅ <b>VK авторизация успешна!</b>\n\n"
                "Выберите что хотите подключить:\n\n"
            )
            
            # Формируем inline кнопки
            inline_keyboard = []
            
            # Кнопка для личной страницы
            inline_keyboard.append([{
                'text': f"👤 {user_name}",
                'callback_data': f"vk_select_user_{telegram_user_id}"
            }])
            
            # Кнопки для групп
            for idx, group in enumerate(user_groups[:10]):  # Максимум 10 групп
                group_name = group['name']
                members = group.get('members_count', 0)
                members_text = f" ({members:,} подписчиков)" if members > 0 else ""
                
                inline_keyboard.append([{
                    'text': f"📝 {group_name}{members_text}",
                    'callback_data': f"vk_select_group_{telegram_user_id}_{idx}"
                }])
            
            # Кнопка отмены
            inline_keyboard.append([{
                'text': "❌ Отмена",
                'callback_data': f"vk_select_cancel_{telegram_user_id}"
            }])
            
            response = req.post(
                telegram_api_url,
                json={
                    'chat_id': telegram_user_id,
                    'text': message_text,
                    'parse_mode': 'HTML',
                    'reply_markup': {
                        'inline_keyboard': inline_keyboard
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Telegram selection menu sent to user {telegram_user_id}")
            else:
                print(f"⚠️ Telegram notification failed: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️ Не удалось отправить меню выбора в Telegram: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================
    # ПОКАЗЫВАЕМ СТРАНИЦУ УСПЕХА
    # ============================================
    
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VK - Выберите что подключить</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #4680C2 0%, #5181B8 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
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
            color: #4680C2;
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
            background: #4680C2;
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
        <h1>Авторизация успешна!</h1>
        <p>Вернитесь в Telegram и выберите что хотите подключить:</p>
        <p>👤 Личную страницу<br>или<br>📝 Группы где вы админ</p>
        <a href="https://t.me/best_seo_master_bot" class="button">Вернуться в бота</a>
    </div>
</body>
</html>
    """)


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
"" 
