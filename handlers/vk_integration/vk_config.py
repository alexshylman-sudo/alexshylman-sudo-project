# -*- coding: utf-8 -*-
"""
Конфигурация VK OAuth авторизации (VK ID с PKCE)
"""
import os
import hashlib
import base64
import secrets

# VK Application credentials
VK_APP_ID = os.getenv("VK_APP_ID", "54435352")  # Новое VK ID приложение
VK_APP_SECRET = os.getenv("VK_APP_SECRET", "")  # Не используется в VK ID

# Redirect URI для OAuth callback
VK_REDIRECT_URI = "https://alexshylman-sudo-project.onrender.com/vk_callback"

# VK API версия
VK_API_VERSION = "5.131"

# Права доступа (scope) для VK ID
VK_OAUTH_SCOPE = "email"

# URLs - VK ID (новый тип приложений)
VK_OAUTH_AUTHORIZE_URL = "https://id.vk.com/authorize"
VK_OAUTH_TOKEN_URL = "https://id.vk.com/oauth2/auth"
VK_API_BASE_URL = "https://api.vk.com/method"

# Временное хранилище для PKCE verifiers
_pkce_storage = {}


def generate_pkce_pair():
    """
    Генерирует PKCE code_verifier и code_challenge
    
    Returns:
        tuple: (code_verifier, code_challenge)
    """
    # Генерируем случайный code_verifier (43-128 символов)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Генерируем code_challenge (SHA256 хеш от verifier)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge


def get_vk_auth_url(telegram_user_id: int) -> str:
    """
    Генерирует URL для авторизации через VK ID с PKCE
    
    Args:
        telegram_user_id: ID пользователя в Telegram
        
    Returns:
        str: URL для авторизации
    """
    state = f"tg_{telegram_user_id}"
    
    # Генерируем PKCE пару
    code_verifier, code_challenge = generate_pkce_pair()
    
    # Сохраняем verifier для использования при обмене code на token
    _pkce_storage[telegram_user_id] = code_verifier
    
    return (
        f"{VK_OAUTH_AUTHORIZE_URL}"
        f"?client_id={VK_APP_ID}"
        f"&redirect_uri={VK_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={VK_OAUTH_SCOPE}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=s256"
    )


def get_pkce_verifier(telegram_user_id: int) -> str:
    """
    Получает сохраненный PKCE verifier для пользователя
    
    Args:
        telegram_user_id: ID пользователя в Telegram
        
    Returns:
        str: code_verifier или None
    """
    return _pkce_storage.pop(telegram_user_id, None)


print("✅ VK Config загружен (VK ID + PKCE)")
