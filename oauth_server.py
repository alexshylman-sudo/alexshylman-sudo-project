"""
OAuth Server для обработки Pinterest callback
Запускается через gunicorn на Render
"""
from flask import Flask, request, render_template_string
import requests
import json
import os
import sys

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
from config import (
    PINTEREST_APP_ID, 
    PINTEREST_APP_SECRET, 
    PINTEREST_REDIRECT_URI
)

app = Flask(__name__)

# Функция для получения свежего подключения к БД
def get_db():
    """
    Создаёт новое подключение к БД для каждого запроса
    Решает проблему SSL connection timeout
    """
    try:
        db = Database()
        # Проверяем подключение
        db.cursor.execute("SELECT 1")
        return db
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

# HTML шаблон для страницы успеха
SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pinterest подключен!</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #059669;
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin: 10px 0;
        }
        .account {
            background: #f7f7f7;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .username {
            font-weight: bold;
            color: #333;
            font-size: 18px;
        }
        .button {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }
        .button:hover {
            background: #059669;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📌</div>
        <h1>Pinterest подключен!</h1>
        <p>Ваш аккаунт успешно подключен к боту</p>
        
        <div class="account">
            <div class="username">@{{ username }}</div>
            <div style="color: #999; font-size: 14px;">{{ account_type }}</div>
        </div>
        
        <p style="font-size: 14px;">
            Теперь вы можете публиковать пины через Telegram бота
        </p>
        
        <a href="https://t.me/{{ bot_username }}" class="button">
            Вернуться в бота
        </a>
    </div>
</body>
</html>
"""

# HTML шаблон для страницы ошибки
ERROR_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ошибка подключения</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #ff6b6b;
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin: 10px 0;
        }
        .error {
            background: #fff3f3;
            border-left: 4px solid #ff6b6b;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: left;
        }
        .button {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }
        .button:hover {
            background: #059669;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Ошибка подключения</h1>
        <p>Не удалось подключить Pinterest аккаунт</p>
        
        <div class="error">
            <strong>Ошибка:</strong><br>
            {{ error }}
        </div>
        
        <p style="font-size: 14px;">
            Попробуйте подключить аккаунт заново через бота
        </p>
        
        <a href="https://t.me/{{ bot_username }}" class="button">
            Вернуться в бота
        </a>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    """Главная страница"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Pinterest OAuth Server</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 40px;
                text-align: center;
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 40px;
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #10b981; }
            .status { color: #00c853; font-size: 24px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📌 Pinterest OAuth Server</h1>
            <p>This server handles Pinterest OAuth callbacks for the Telegram bot.</p>
            <div class="status">Status: Running ✅</div>
        </div>
    </body>
    </html>
    """


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'pinterest-vk-oauth-server'}


@app.route('/pinterest/callback')
def pinterest_callback():
    """
    Обработчик OAuth callback от Pinterest
    """
    print("=" * 60)
    print("📌 Pinterest OAuth Callback received")
    
    # Получаем параметры из URL
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    print(f"   Code: {code[:20] if code else None}...")
    print(f"   State: {state}")
    print(f"   Error: {error}")
    
    bot_username = os.getenv('BOT_USERNAME', 'yourbot')
    
    # Если пользователь отклонил доступ
    if error:
        print(f"❌ User denied access: {error}")
        return render_template_string(
            ERROR_PAGE,
            error=f"Доступ отклонен: {error}",
            bot_username=bot_username
        )
    
    # Проверяем наличие обязательных параметров
    if not code or not state:
        print("❌ Missing code or state parameter")
        return render_template_string(
            ERROR_PAGE,
            error="Отсутствует код авторизации или state параметр",
            bot_username=bot_username
        )
    
    # Получаем свежее подключение к БД
    db = get_db()
    
    if not db:
        print("❌ Database not connected")
        return render_template_string(
            ERROR_PAGE,
            error="Ошибка подключения к базе данных",
            bot_username=bot_username
        )
    
    try:
        # State содержит user_id
        user_id = int(state)
        print(f"👤 User ID: {user_id}")
        
        # Получаем сохраненный state из БД для проверки
        user = db.get_user(user_id)
        if not user:
            raise Exception(f"Пользователь {user_id} не найден в базе данных")
        
        connections = user.get('platform_connections', {})
        oauth_state = connections.get('_pinterest_oauth_state')
        
        if not oauth_state:
            raise Exception("OAuth state не найден в БД. Попробуйте подключить заново.")
        
        saved_state = oauth_state.get('state')
        if str(saved_state) != str(state):
            raise Exception(f"State не совпадает: {saved_state} != {state}")
        
        print("✅ State verified")
        
        # Обмениваем code на access_token
        print("🔄 Exchanging code for access token...")
        
        token_response = requests.post(
            'https://api.pinterest.com/v5/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': PINTEREST_REDIRECT_URI
            },
            auth=(PINTEREST_APP_ID, PINTEREST_APP_SECRET),
            timeout=10
        )
        
        print(f"   Response status: {token_response.status_code}")
        
        if token_response.status_code != 200:
            error_data = token_response.json() if token_response.status_code != 500 else {}
            error_msg = error_data.get('message', f'HTTP {token_response.status_code}')
            raise Exception(f"Failed to get token: {error_msg}")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise Exception("No access_token in response")
        
        print("✅ Access token received")
        
        # Получаем информацию о пользователе Pinterest
        print("🔄 Getting user info...")
        
        user_response = requests.get(
            'https://api.pinterest.com/v5/user_account',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if user_response.status_code != 200:
            raise Exception(f"Failed to get user info: HTTP {user_response.status_code}")
        
        user_data = user_response.json()
        pinterest_username = user_data.get('username', 'Unknown')
        account_type = user_data.get('account_type', 'PERSONAL')
        
        print(f"   Username: {pinterest_username}")
        print(f"   Account type: {account_type}")
        
        # Удаляем временный state
        if '_pinterest_oauth_state' in connections:
            del connections['_pinterest_oauth_state']
        
        # ============================================
        # ПРОВЕРКА ГЛОБАЛЬНОЙ УНИКАЛЬНОСТИ PINTEREST
        # ============================================
        
        # Проверяем что этот Pinterest аккаунт не подключен ни у кого (в ЛЮБОЙ БД)
        db.cursor.execute("""
            SELECT u.id, u.username
            FROM users u
            WHERE u.platform_connections::text LIKE %s
        """, (f'%"username": "{pinterest_username}"%',))
        
        existing_users = db.cursor.fetchall()
        
        if existing_users:
            # Pinterest уже подключен у кого-то (возможно у текущего пользователя)
            for existing_user in existing_users:
                existing_user_id = existing_user.get('id') if isinstance(existing_user, dict) else existing_user[0]
                existing_username = existing_user.get('username') if isinstance(existing_user, dict) else (existing_user[1] if len(existing_user) > 1 else 'Unknown')
                
                if existing_user_id == user_id:
                    # Текущий пользователь уже подключил этот Pinterest
                    print(f"❌ Pinterest @{pinterest_username} уже подключен у пользователя {user_id}")
                    
                    # Закрываем БД
                    try:
                        db.cursor.close()
                        db.conn.close()
                    except:
                        pass
                    
                    return render_template_string(
                        ERROR_PAGE,
                        error=f"Аккаунт @{pinterest_username} уже подключен к вашему боту",
                        bot_username=bot_username
                    )
                else:
                    # Другой пользователь уже подключил этот Pinterest
                    print(f"❌ Pinterest @{pinterest_username} уже подключен у другого пользователя (ID: {existing_user_id})")
                    
                    # Закрываем БД
                    try:
                        db.cursor.close()
                        db.conn.close()
                    except:
                        pass
                    
                    return render_template_string(
                        ERROR_PAGE,
                        error=f"Аккаунт @{pinterest_username} уже используется другим пользователем",
                        bot_username=bot_username
                    )
        
        # ============================================
        # Уникальность подтверждена - сохраняем
        # ============================================
        
        # Сохраняем Pinterest подключение
        if 'pinterests' not in connections:
            connections['pinterests'] = []
        
        from datetime import datetime
        
        connections['pinterests'].append({
            'access_token': access_token,
            'username': pinterest_username,
            'account_type': account_type,
            'board': pinterest_username,  # для совместимости
            'added_at': datetime.now().isoformat(),
            'status': 'active',
            'oauth_completed': True
        })
        
        # Обновляем в БД
        db.cursor.execute("""
            UPDATE users 
            SET platform_connections = %s::jsonb
            WHERE id = %s
        """, (json.dumps(connections), user_id))
        db.conn.commit()
        
        # Закрываем соединение
        try:
            db.cursor.close()
            db.conn.close()
        except:
            pass
        
        # Отправляем уведомление и меню подключений в Telegram
        try:
            from loader import bot
            from handlers.platform_connections.main_menu import show_connections_menu
            from telebot import types
            
            # Создаём фейковое сообщение для show_connections_menu
            class FakeMessage:
                def __init__(self, chat_id):
                    self.chat = types.Chat(chat_id, 'private')
                    self.message_id = 0
            
            class FakeCall:
                def __init__(self, user_id):
                    self.from_user = types.User(user_id, False, 'User')
                    self.message = FakeMessage(user_id)
                    self.id = 0
            
            fake_call = FakeCall(user_id)
            
            # Отправляем уведомление
            bot.send_message(
                user_id,
                "✅ <b>Pinterest успешно подключен!</b>\n\n"
                f"Аккаунт @{pinterest_username} готов к работе.",
                parse_mode='HTML'
            )
            
            # Показываем меню подключений
            show_connections_menu(fake_call)
            
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление в Telegram: {e}")
        
        print("✅ Pinterest connected successfully!")
        print("=" * 60)
        
        # Показываем страницу успеха
        return render_template_string(
            SUCCESS_PAGE,
            username=pinterest_username,
            account_type=account_type,
            bot_username=bot_username
        )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("=" * 60)
        
        # Закрываем соединение при ошибке
        try:
            if db:
                db.cursor.close()
                db.conn.close()
        except:
            pass
        
        return render_template_string(
            ERROR_PAGE,
            error=str(e),
            bot_username=bot_username
        )


# Для локального запуска
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting Pinterest OAuth Server on port {port}")
    print(f"📌 Callback URL: {PINTEREST_REDIRECT_URI}")
    app.run(host='0.0.0.0', port=port, debug=True)


# ═══════════════════════════════════════════════════════════════
# VK OAUTH CALLBACK
# ═══════════════════════════════════════════════════════════════

VK_SUCCESS_PAGE = """
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
            background: linear-gradient(135deg, #4680C2 0%, #5181B8 100%);
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
    </div>
</body>
</html>
"""

VK_ERROR_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ошибка подключения VK</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #4680C2 0%, #5181B8 100%);
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
        .error {
            background: #fee;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
            color: #c33;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Ошибка подключения</h1>
        <p>{{ error_message }}</p>
        <p>Попробуйте еще раз или обратитесь в поддержку.</p>
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
    print("\n" + "=" * 60)
    print("🔵 VK CALLBACK RECEIVED")
    print("=" * 60)
    
    # Получаем параметры
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    print(f"   Code: {code[:20] if code else None}...")
    print(f"   State: {state}")
    print(f"   Error: {error}")
    
    # Проверяем ошибку
    if error:
        error_description = request.args.get('error_description', 'Неизвестная ошибка')
        print(f"❌ VK OAuth error: {error} - {error_description}")
        return render_template_string(VK_ERROR_PAGE, error_message=error_description)
    
    # Проверяем наличие code
    if not code:
        print(f"❌ VK OAuth: отсутствует code")
        return render_template_string(VK_ERROR_PAGE, error_message="Отсутствует код авторизации")
    
    # Извлекаем telegram_user_id из state
    if not state or not state.startswith('tg_'):
        print(f"❌ VK OAuth: некорректный state")
        return render_template_string(VK_ERROR_PAGE, error_message="Некорректный state")
    
    try:
        telegram_user_id = int(state.replace('tg_', ''))
    except:
        print(f"❌ VK OAuth: не удалось извлечь telegram_user_id из state")
        return render_template_string(VK_ERROR_PAGE, error_message="Некорректный формат state")
    
    try:
        # Получаем свежее подключение к БД
        db = get_db()
        
        # Получаем VK App credentials из переменных окружения
        VK_APP_ID = os.getenv('VK_APP_ID', '54433963')
        VK_APP_SECRET = os.getenv('VK_APP_SECRET', '')
        VK_REDIRECT_URI = 'https://alexshylman-sudo-project.onrender.com/vk_callback'
        
        if not VK_APP_SECRET:
            print(f"❌ VK_APP_SECRET not set")
            return render_template_string(VK_ERROR_PAGE, error_message="VK_APP_SECRET not configured")
        
        # Обмениваем code на access_token
        print(f"🔄 Exchanging code for token...")
        
        token_response = requests.get(
            'https://oauth.vk.com/access_token',
            params={
                'client_id': VK_APP_ID,
                'client_secret': VK_APP_SECRET,
                'redirect_uri': VK_REDIRECT_URI,
                'code': code
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            print(f"❌ VK OAuth HTTP error: {token_response.status_code}")
            return render_template_string(VK_ERROR_PAGE, error_message="Ошибка получения токена")
        
        token_data = token_response.json()
        
        if 'error' in token_data:
            print(f"❌ VK OAuth error: {token_data.get('error_description', token_data['error'])}")
            return render_template_string(VK_ERROR_PAGE, error_message=token_data.get('error_description', 'Ошибка авторизации'))
        
        access_token = token_data.get('access_token')
        vk_user_id = token_data.get('user_id')
        email = token_data.get('email')
        
        print(f"✅ VK Token получен:")
        print(f"   User ID: {vk_user_id}")
        print(f"   Email: {email if email else 'не предоставлен'}")
        
        # Получаем информацию о пользователе VK
        user_response = requests.get(
            'https://api.vk.com/method/users.get',
            params={
                'access_token': access_token,
                'user_ids': vk_user_id,
                'fields': 'photo_200,photo_max_orig',
                'v': '5.131'
            },
            timeout=10
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            if 'response' in user_data and len(user_data['response']) > 0:
                vk_user_info = user_data['response'][0]
                first_name = vk_user_info.get('first_name', '')
                last_name = vk_user_info.get('last_name', '')
                photo = vk_user_info.get('photo_200', '')
                
                print(f"✅ VK User Info получена:")
                print(f"   Name: {first_name} {last_name}")
        else:
            first_name = ''
            last_name = ''
            photo = ''
        
        # Сохраняем подключение в БД
        if not db:
            print(f"❌ Database not connected")
            return render_template_string(VK_ERROR_PAGE, error_message="Database error")
        
        # Получаем пользователя
        db.cursor.execute("SELECT * FROM users WHERE id = %s", (telegram_user_id,))
        user = db.cursor.fetchone()
        
        if not user:
            print(f"❌ User {telegram_user_id} not found")
            return render_template_string(VK_ERROR_PAGE, error_message="Пользователь не найден в базе")
        
        # Получаем существующие подключения
        platform_connections = user.get('platform_connections', {}) if isinstance(user, dict) else {}
        if isinstance(platform_connections, str):
            platform_connections = json.loads(platform_connections)
        
        # Добавляем VK
        platform_connections['vk'] = {
            'user_id': vk_user_id,
            'access_token': access_token,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'photo': photo,
            'status': 'active'
        }
        
        # Сохраняем в БД
        db.cursor.execute("""
            UPDATE users
            SET platform_connections = %s::jsonb
            WHERE id = %s
        """, (json.dumps(platform_connections), telegram_user_id))
        
        db.conn.commit()
        
        # Закрываем соединение
        try:
            db.cursor.close()
            db.conn.close()
        except:
            pass
        
        print(f"✅ VK подключен для пользователя {telegram_user_id}")
        print(f"   VK ID: {vk_user_id}")
        print(f"   VK Name: {first_name} {last_name}")
        print("=" * 60 + "\n")
        
        # Отправляем уведомление в Telegram (опционально)
        try:
            from loader import bot
            bot.send_message(
                telegram_user_id,
                "✅ <b>VK успешно подключен!</b>\n\n"
                "Теперь вы можете публиковать посты в ВКонтакте.",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление в Telegram: {e}")
        
        # Показываем страницу успеха
        return render_template_string(VK_SUCCESS_PAGE)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("=" * 60 + "\n")
        
        # Закрываем соединение при ошибке
        try:
            if db:
                db.cursor.close()
                db.conn.close()
        except:
            pass
        
        return render_template_string(VK_ERROR_PAGE, error_message=str(e))


# ==========================================
# НОВЫЕ VK ROUTES С PKCE + REFRESH_TOKEN
# ==========================================

@app.route('/vk/auth')
def new_vk_auth():
    """VK OAuth - начало (PKCE + refresh_token)"""
    from vk_webhook import vk_auth
    return vk_auth()


@app.route('/vk/callback')  
def new_vk_callback():
    """VK OAuth callback (PKCE + refresh_token + auto-show connections)"""
    from vk_webhook import vk_callback
    return vk_callback()


print("✅ OAuth Server loaded with VK PKCE routes")
print("   /vk/auth - VK OAuth start")
print("   /vk/callback - VK OAuth callback with auto-refresh tokens")
print("   /pinterest/callback - Pinterest OAuth callback")
print("   /health - Health check")



