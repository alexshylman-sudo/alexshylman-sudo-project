"""
Pinterest API Client
Документация: https://developers.pinterest.com/docs/api/v5/
"""
import requests
import json
from typing import Optional, Dict, List


class PinterestClient:
    """Клиент для работы с Pinterest API v5"""
    
    BASE_URL = "https://api.pinterest.com/v5"
    
    def __init__(self, access_token: str):
        """
        Инициализация клиента
        
        Args:
            access_token: Pinterest Access Token
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """
        Тест подключения к Pinterest
        
        Returns:
            dict: {'status': 'ok/error', 'message': str, 'user_info': dict}
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/user_account",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'ok',
                    'message': 'Подключение успешно',
                    'user_info': {
                        'username': data.get('username'),
                        'account_type': data.get('account_type'),
                        'profile_image': data.get('profile_image')
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Ошибка {response.status_code}: {response.text}'
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка подключения: {str(e)}'
            }
    
    def get_boards(self) -> List[Dict]:
        """
        Получить список досок пользователя
        
        Returns:
            list: Список досок с информацией
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/boards",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                return []
        
        except Exception as e:
            print(f"Ошибка получения досок: {e}")
            return []
    
    def create_pin(self, board_id: str, title: str, description: str = "", 
                   image_url: str = None, image_base64: str = None,
                   link: str = None) -> Dict:
        """
        Создать новый Pin
        
        Args:
            board_id: ID доски
            title: Заголовок пина
            description: Описание
            image_url: URL изображения
            image_base64: Base64 изображение
            link: Ссылка на сайт
        
        Returns:
            dict: Информация о созданном пине
        """
        try:
            payload = {
                'board_id': board_id,
                'title': title,
                'description': description or title
            }
            
            # Добавляем изображение
            if image_url:
                payload['media_source'] = {
                    'source_type': 'image_url',
                    'url': image_url
                }
            elif image_base64:
                payload['media_source'] = {
                    'source_type': 'image_base64',
                    'data': image_base64,
                    'content_type': 'image/jpeg'
                }
            
            # Добавляем ссылку
            if link:
                payload['link'] = link
            
            response = requests.post(
                f"{self.BASE_URL}/pins",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                pin_id = data.get('id', '')
                
                # Формируем URL пина
                pin_url = f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else None
                
                return {
                    'status': 'ok',
                    'pin_id': pin_id,
                    'url': pin_url,
                    'message': 'Pin создан успешно'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Ошибка {response.status_code}: {response.text}'
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка создания пина: {str(e)}'
            }
    
    def get_user_info(self) -> Dict:
        """Получить информацию о пользователе"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/user_account",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        
        except Exception as e:
            print(f"Ошибка получения информации: {e}")
            return {}


print("✅ platforms/pinterest/client.py загружен")
