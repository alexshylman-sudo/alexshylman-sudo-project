# -*- coding: utf-8 -*-
"""
Генерация изображений через Nano Banana Pro API
"""
import os
import requests
import time
from typing import Optional, Dict

# API конфигурация
NANO_BANANA_API_URL = "https://api.nanobanana.pro/v1/images/generations"

def _get_api_key():
    """Получить API ключ из config или переменных окружения"""
    try:
        from config import NANO_BANANA_API_KEY
        return NANO_BANANA_API_KEY
    except:
        return os.getenv("NANO_BANANA_API_KEY", "")


def generate_image(prompt: str, aspect_ratio: str = "1:1") -> Optional[Dict]:
    """
    Генерирует изображение по текстовому промпту
    
    Args:
        prompt: Описание изображения на английском
        aspect_ratio: Соотношение сторон (1:1, 16:9, 9:16, 4:3, 3:4)
        
    Returns:
        dict: {'image_url': '...', 'image_path': '...'} или None при ошибке
    """
    NANO_BANANA_API_KEY = _get_api_key()
    
    if not NANO_BANANA_API_KEY:
        print("❌ NANO_BANANA_API_KEY не задан в .env")
        return None
    
    try:
        # Параметры запроса
        payload = {
            "model": "flux-pro",  # Или "flux-1.1-pro", "flux-schnell"
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "safety_tolerance": 2,
            "output_format": "png"
        }
        
        headers = {
            "Authorization": f"Bearer {NANO_BANANA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"🎨 Генерация изображения: {prompt[:50]}...")
        
        # Отправляем запрос
        response = requests.post(
            NANO_BANANA_API_URL,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return None
        
        result = response.json()
        
        # Nano Banana возвращает URL изображения
        image_url = result.get('data', [{}])[0].get('url')
        
        if not image_url:
            print(f"❌ URL изображения не получен: {result}")
            return None
        
        # Скачиваем изображение
        image_response = requests.get(image_url, timeout=30)
        
        if image_response.status_code != 200:
            print(f"❌ Не удалось скачать изображение")
            return None
        
        # Сохраняем локально
        timestamp = int(time.time())
        filename = f"generated_image_{timestamp}.png"
        filepath = os.path.join("/tmp", filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_response.content)
        
        print(f"✅ Изображение сохранено: {filepath}")
        
        return {
            'image_url': image_url,
            'image_path': filepath,
            'filename': filename
        }
        
    except requests.exceptions.Timeout:
        print("❌ Таймаут генерации изображения")
        return None
    except Exception as e:
        print(f"❌ Ошибка генерации изображения: {e}")
        import traceback
        traceback.print_exc()
        return None


def translate_to_english(text: str) -> str:
    """
    Переводит русский текст в английский промпт для изображения
    Упрощённая версия - извлекает ключевые слова
    
    Args:
        text: Текст поста на русском
        
    Returns:
        str: Промпт на английском
    """
    # TODO: Интеграция с Claude для качественного перевода
    # Пока используем простое извлечение ключевых слов
    
    # Словарь популярных тем
    keywords_map = {
        'панели': 'wall panels',
        'дерево': 'wood',
        'интерьер': 'interior',
        'дизайн': 'design',
        'ремонт': 'renovation',
        'современный': 'modern',
        'роскошный': 'luxury',
        'уютный': 'cozy',
        'стильный': 'stylish',
        'минимализм': 'minimalist',
        'классический': 'classic',
        'мрамор': 'marble',
        'кожа': 'leather',
        'текстура': 'texture'
    }
    
    text_lower = text.lower()
    found_keywords = []
    
    for ru, en in keywords_map.items():
        if ru in text_lower:
            found_keywords.append(en)
    
    if found_keywords:
        prompt = f"professional photography of {', '.join(found_keywords[:3])}, high quality, 8k, detailed"
    else:
        prompt = "modern interior design, professional photography, high quality, 8k"
    
    return prompt


print("✅ utils/image_generator.py загружен")
