# -*- coding: utf-8 -*-
"""
VK OAuth авторизация - основная логика
"""
import requests
import json
from typing import Optional, Dict
from .vk_config import (
    VK_APP_ID, VK_APP_SECRET, VK_REDIRECT_URI, 
    VK_API_VERSION, VK_OAUTH_TOKEN_URL, VK_API_BASE_URL
)


class VKOAuth:
    """Класс для работы с VK OAuth"""
    
    @staticmethod
    def exchange_code_for_token(code: str) -> Optional[Dict]:
        """
        Обменивает authorization code на access token
        
        Args:
            code: Authorization code от VK
            
        Returns:
            dict: {'access_token': '...', 'email': '...', 'user_id': 123}
            или None если ошибка
        """
        try:
            response = requests.get(
                VK_OAUTH_TOKEN_URL,
                params={
                    "client_id": VK_APP_ID,
                    "client_secret": VK_APP_SECRET,
                    "redirect_uri": VK_REDIRECT_URI,
                    "code": code
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем наличие ошибки
                if 'error' in data:
                    print(f"❌ VK OAuth error: {data.get('error_description', data['error'])}")
                    return None
                
                return data
            else:
                print(f"❌ VK OAuth HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ VK OAuth exception: {e}")
            return None
    
    @staticmethod
    def get_user_info(access_token: str, user_id: int) -> Optional[Dict]:
        """
        Получает информацию о пользователе VK
        
        Args:
            access_token: Access token пользователя
            user_id: VK user ID
            
        Returns:
            dict: {
                'id': 123,
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'photo_200': 'https://...',
                'email': 'user@example.com'
            }
        """
        try:
            response = requests.get(
                f"{VK_API_BASE_URL}/users.get",
                params={
                    "access_token": access_token,
                    "user_ids": user_id,
                    "fields": "photo_200,photo_max_orig",
                    "v": VK_API_VERSION
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and len(data['response']) > 0:
                    return data['response'][0]
                else:
                    print(f"❌ VK API error: {data}")
                    return None
            else:
                print(f"❌ VK API HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ VK API exception: {e}")
            return None
    
    @staticmethod
    def save_vk_connection(db, telegram_user_id: int, vk_data: Dict) -> bool:
        """
        Сохраняет подключение VK к пользователю Telegram
        
        Args:
            db: Database instance
            telegram_user_id: ID пользователя в Telegram
            vk_data: Данные от VK OAuth
            
        Returns:
            bool: True если успешно
        """
        try:
            # Получаем пользователя
            user = db.get_user(telegram_user_id)
            if not user:
                print(f"❌ Пользователь Telegram {telegram_user_id} не найден в БД")
                return False
            
            # Получаем информацию о пользователе VK
            vk_user_info = VKOAuth.get_user_info(
                vk_data['access_token'],
                vk_data['user_id']
            )
            
            if not vk_user_info:
                print(f"❌ Не удалось получить информацию о VK пользователе {vk_data['user_id']}")
                return False
            
            # Сохраняем подключение
            vk_connection = {
                'user_id': vk_data['user_id'],
                'access_token': vk_data['access_token'],
                'email': vk_data.get('email'),
                'first_name': vk_user_info.get('first_name'),
                'last_name': vk_user_info.get('last_name'),
                'photo': vk_user_info.get('photo_200'),
                'status': 'active',
                'connected_at': 'now()'
            }
            
            # Обновляем platform_connections пользователя
            platform_connections = user.get('platform_connections', {})
            if isinstance(platform_connections, str):
                platform_connections = json.loads(platform_connections)
            
            platform_connections['vk'] = vk_connection
            
            # Сохраняем в БД
            db.cursor.execute("""
                UPDATE users
                SET platform_connections = %s::jsonb
                WHERE id = %s
            """, (json.dumps(platform_connections), telegram_user_id))
            
            db.conn.commit()
            
            print(f"✅ VK подключен для пользователя {telegram_user_id}")
            print(f"   VK ID: {vk_data['user_id']}")
            print(f"   VK Name: {vk_user_info.get('first_name')} {vk_user_info.get('last_name')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения VK подключения: {e}")
            try:
                db.conn.rollback()
            except:
                pass
            return False


print("✅ VK OAuth Handler загружен")
