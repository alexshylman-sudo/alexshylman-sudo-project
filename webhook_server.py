"""
Flask Webhook Server для Pinterest OAuth callback
Запускается отдельно от Telegram бота
"""
from flask import Flask, request, render_template_string
import requests
import json
import os
from database.database import Database
from config import (
    PINTEREST_APP_ID, 
    PINTEREST_APP_SECRET, 
    PINTEREST_REDIRECT_URI,
    DATABASE_URL
)

app = Flask(__name__)
db = Database()

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
            background: linear-gradient(135deg, #E60023 0%, #c9001f 100%);
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
            color: #E60023;
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
            background: #E60023;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }
        .button:hover {
            background: #c9001f;
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
            background: #E60023;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 20px;
            transition: background 0.3s;
        }
        .button:hover {
            background: #c9001f;
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


@app.route('/pinterest/callback')
def pinterest_callback():
    """
    Обработчик OAuth callback от Pinterest
    
    Pinterest перенаправляет сюда после авторизации с параметрами:
    - code: код авторизации
    - state: user_id для идентификации пользователя
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
    
    # Если пользователь отклонил доступ
    if error:
        print(f"❌ User denied access: {error}")
        return render_template_string(
            ERROR_PAGE,
            error=f"Доступ отклонен: {error}",
            bot_username=os.getenv('BOT_USERNAME', 'yourbot')
        )
    
    # Проверяем наличие обязательных параметров
    if not code or not state:
        print("❌ Missing code or state parameter")
        return render_template_string(
            ERROR_PAGE,
            error="Отсутствует код авторизации или state параметр",
            bot_username=os.getenv('BOT_USERNAME', 'yourbot')
        )
    
    try:
        # State содержит user_id
        user_id = int(state)
        print(f"👤 User ID: {user_id}")
        
        # Получаем сохраненный state из БД для проверки
        user = db.get_user(user_id)
        if not user:
            raise Exception(f"Пользователь {user_id} не найден")
        
        connections = user.get('platform_connections', {})
        oauth_state = connections.get('_pinterest_oauth_state')
        
        if not oauth_state:
            raise Exception("OAuth state не найден в БД")
        
        saved_state = oauth_state.get('state')
        if saved_state != state:
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
        
        print("✅ Pinterest connected successfully!")
        print("=" * 60)
        
        # Показываем страницу успеха
        return render_template_string(
            SUCCESS_PAGE,
            username=pinterest_username,
            account_type=account_type,
            bot_username=os.getenv('BOT_USERNAME', 'yourbot')
        )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("=" * 60)
        
        return render_template_string(
            ERROR_PAGE,
            error=str(e),
            bot_username=os.getenv('BOT_USERNAME', 'yourbot')
        )


@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'pinterest-oauth-webhook'}


@app.route('/')
def index():
    """Главная страница"""
    return """
    <h1>Pinterest OAuth Webhook Server</h1>
    <p>This server handles Pinterest OAuth callbacks for the Telegram bot.</p>
    <p>Status: Running ✅</p>
    """


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting Pinterest OAuth Webhook Server on port {port}")
    print(f"📌 Callback URL: {PINTEREST_REDIRECT_URI}")
    app.run(host='0.0.0.0', port=port, debug=False)
