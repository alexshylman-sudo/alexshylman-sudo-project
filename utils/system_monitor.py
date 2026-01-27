"""
Утилита мониторинга систем - проверка API и серверных ресурсов
"""
import os
from config import ANTHROPIC_API_KEY


def check_claude_api():
    """Проверить статус Claude API"""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("your_"):
        return {
            'status': 'not_configured',
            'message': 'API ключ не настроен'
        }
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Простой тестовый запрос
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        
        return {
            'status': 'ok',
            'model': 'claude-sonnet-4-20250514',
            'message': 'API работает'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def check_gemini_api():
    """Проверить статус Gemini API"""
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not google_key or google_key.startswith("your_"):
        return {
            'status': 'not_configured',
            'model': 'Not configured',
            'message': 'API ключ не настроен'
        }
    
    try:
        from google import genai
        client = genai.Client(api_key=google_key)
        
        # Проверяем доступность модели
        return {
            'status': 'ok',
            'model': 'nano-banana-pro-preview',
            'message': 'API работает'
        }
    except Exception as e:
        return {
            'status': 'error',
            'model': 'Error',
            'message': str(e)[:100]
        }


def check_database():
    """Проверить статус базы данных"""
    try:
        from database.database import db
        
        # Проверяем подключение
        db.cursor.execute("SELECT 1")
        
        # Получаем версию PostgreSQL
        db.cursor.execute("SELECT version()")
        version = db.cursor.fetchone()[0]
        version_short = version.split('PostgreSQL')[1].split('on')[0].strip() if 'PostgreSQL' in version else 'Unknown'
        
        return {
            'status': 'ok',
            'message': 'Подключена',
            'version': version_short
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)[:100],
            'version': 'N/A'
        }


def check_telegram(bot):
    """Проверить статус Telegram API"""
    try:
        bot_info = bot.get_me()
        
        return {
            'status': 'ok',
            'message': 'Подключен',
            'username': bot_info.username,
            'bot_id': bot_info.id
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)[:100],
            'username': 'Unknown',
            'bot_id': 'N/A'
        }


def get_full_system_status():
    """Получить полный статус всех систем"""
    status = {
        'claude': check_claude_api(),
        'gemini': check_gemini_api(),
    }
    
    # Проверка БД
    try:
        from database.database import db
        db.cursor.execute("SELECT 1")
        status['database'] = {'status': 'ok', 'message': 'БД работает'}
    except Exception as e:
        status['database'] = {'status': 'error', 'message': str(e)}
    
    return status


def format_status_message(status):
    """Форматировать сообщение о статусе систем"""
    claude = status.get('claude', {})
    gemini = status.get('gemini', {})
    database = status.get('database', {})
    
    # Эмодзи для статусов
    def get_emoji(s):
        if s == 'ok':
            return '✅'
        elif s == 'error':
            return '❌'
        else:
            return '⚪️'
    
    text = (
        "🖥 <b>МОНИТОРИНГ СИСТЕМ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "<b>🤖 AI СЕРВИСЫ:</b>\n"
        f"   ├─ Claude: {get_emoji(claude.get('status'))} <code>{claude.get('model', 'N/A')}</code>\n"
        f"   │   {claude.get('message', '')}\n"
        f"   └─ Gemini: {get_emoji(gemini.get('status'))} <code>{gemini.get('message', '')}</code>\n\n"
        
        "<b>💾 БАЗА ДАННЫХ:</b>\n"
        f"   └─ PostgreSQL: {get_emoji(database.get('status'))} {database.get('message', '')}\n\n"
    )
    
    return text


print("✅ utils/system_monitor.py загружен")
