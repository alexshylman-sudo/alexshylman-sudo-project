"""
Telegram Channel Client
"""
import requests
from typing import Optional, Dict


class TelegramChannelClient:
    """Клиент для публикации в Telegram каналы"""
    
    def __init__(self, bot_token: str, channel_id: str):
        """
        Инициализация клиента
        
        Args:
            bot_token: Токен бота от @BotFather
            channel_id: ID канала (с -100 в начале)
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def test_connection(self) -> Dict:
        """Тест подключения"""
        try:
            # Проверяем бота
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            
            if response.status_code != 200:
                return {
                    'status': 'error',
                    'error': 'Неверный токен бота',
                    'details': response.text
                }
            
            bot_info = response.json()['result']
            
            # Проверяем права в канале
            chat_response = requests.get(
                f"{self.base_url}/getChat",
                params={'chat_id': self.channel_id},
                timeout=10
            )
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                
                if not chat_data.get('ok'):
                    return {
                        'status': 'error',
                        'error': chat_data.get('description', 'Неизвестная ошибка'),
                        'details': str(chat_data)
                    }
                
                chat_info = chat_data['result']
                
                return {
                    'status': 'ok',
                    'message': 'Подключение успешно',
                    'bot_info': {
                        'username': bot_info.get('username'),
                        'first_name': bot_info.get('first_name')
                    },
                    'channel_info': {
                        'title': chat_info.get('title', 'Unknown'),
                        'type': chat_info.get('type'),
                        'username': chat_info.get('username')
                    }
                }
            else:
                error_data = chat_response.json()
                error_msg = error_data.get('description', 'Бот не имеет доступа к каналу')
                
                return {
                    'status': 'error',
                    'error': error_msg,
                    'details': str(error_data)
                }
        
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error': 'Превышено время ожидания ответа от Telegram API'
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'error': 'Ошибка подключения к Telegram API'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Неизвестная ошибка: {str(e)}',
                'details': str(type(e).__name__)
            }
    
    def send_message(self, text: str, parse_mode: str = 'HTML',
                    disable_web_page_preview: bool = False) -> Dict:
        """
        Отправить текстовое сообщение
        
        Args:
            text: Текст сообщения
            parse_mode: HTML или Markdown
            disable_web_page_preview: Отключить превью ссылок
        
        Returns:
            dict: Результат отправки
        """
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    'chat_id': self.channel_id,
                    'text': text,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': disable_web_page_preview
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()['result']
                return {
                    'status': 'ok',
                    'message_id': data.get('message_id'),
                    'message': 'Сообщение отправлено'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Ошибка: {response.text}'
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка отправки: {str(e)}'
            }
    
    def send_photo(self, photo_url: str = None, photo_file = None,
                  caption: str = "", parse_mode: str = 'HTML') -> Dict:
        """
        Отправить фото
        
        Args:
            photo_url: URL фото
            photo_file: Файл фото
            caption: Подпись
            parse_mode: HTML или Markdown
        
        Returns:
            dict: Результат отправки
        """
        try:
            data = {
                'chat_id': self.channel_id,
                'caption': caption,
                'parse_mode': parse_mode
            }
            
            if photo_url:
                data['photo'] = photo_url
                response = requests.post(
                    f"{self.base_url}/sendPhoto",
                    json=data,
                    timeout=30
                )
            else:
                files = {'photo': photo_file}
                response = requests.post(
                    f"{self.base_url}/sendPhoto",
                    data=data,
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                return {
                    'status': 'ok',
                    'message': 'Фото отправлено'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Ошибка: {response.text}'
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка отправки: {str(e)}'
            }


print("✅ platforms/telegram_channel/client.py загружен")
