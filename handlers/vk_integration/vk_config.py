# -*- coding: utf-8 -*-
"""
Конфигурация VK OAuth авторизации
"""
import os

# VK Application credentials
VK_APP_ID = os.getenv("VK_APP_ID", "54433963")  # Новый App ID от VK ID
VK_APP_SECRET = os.getenv("VK_APP_SECRET", "")  # Добавь в переменные окружения Render.com

# Redirect URI для OAuth callback
VK_REDIRECT_URI = "https://alexshylman-sudo-project.onrender.com/vk_callback"

# VK API версия
VK_API_VERSION = "5.131"

# Права доступа (scope)
VK_OAUTH_SCOPE = "wall,photos,email,offline"  # wall и photos для публикации

# URLs
VK_OAUTH_AUTHORIZE_URL = "https://oauth.vk.com/authorize"
VK_OAUTH_TOKEN_URL = "https://oauth.vk.com/access_token"
VK_API_BASE_URL = "https://api.vk.com/method"


def get_vk_auth_url(telegram_user_id: int) -> str:
    """
    Генерирует URL для авторизации через VK
    
    Args:
        telegram_user_id: ID пользователя в Telegram
        
    Returns:
        str: URL для авторизации
    """
    # State содержит telegram user_id чтобы знать кого авторизовать
    state = f"tg_{telegram_user_id}"
    
    return (
        f"{VK_OAUTH_AUTHORIZE_URL}"
        f"?client_id={VK_APP_ID}"
        f"&redirect_uri={VK_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={VK_OAUTH_SCOPE}"
        f"&state={state}"
        f"&v={VK_API_VERSION}"
    )


print("✅ VK Config загружен")
