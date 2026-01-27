"""
Генерация изображений через Google Gemini Nano Banana Pro
"""
import os
import base64
from typing import Optional


class ImageGenerator:
    """Генератор изображений через Nano Banana Pro"""
    
    def __init__(self, api_key: str = None):
        """
        Инициализация генератора
        
        Args:
            api_key: Google API ключ
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("⚠️ Google API ключ не найден")
            self.client = None
            return
        
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.client = None
            print("✅ Nano Banana Pro готов к работе")
        except ImportError:
            print("⚠️ Установите: pip install google-genai")
            self.client = None
    
    def _get_client(self):
        """Получить или создать клиент"""
        if self.client is None and self.api_key:
            self.client = self.genai.Client(api_key=self.api_key)
        return self.client
    
    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1"
    ) -> dict:
        """
        Генерация изображения
        
        Args:
            prompt: Описание изображения на английском
            aspect_ratio: Соотношение сторон (1:1, 16:9, 9:16, 4:3, 3:4)
            
        Returns:
            dict: {
                'success': bool,
                'image_bytes': bytes,
                'error': str
            }
        """
        if not self.api_key:
            return {
                'success': False,
                'image_bytes': None,
                'error': '⚠️ Google API ключ не настроен. Добавьте GOOGLE_API_KEY в .env'
            }
        
        try:
            client = self._get_client()
            
            print(f"🍌 Nano Banana Pro генерация...")
            print(f"   Промпт: {prompt[:100]}...")
            print(f"   Формат: {aspect_ratio}")
            
            # Конфигурация генерации
            generation_config = self.types.GenerateContentConfig(
                temperature=1.0,
                top_p=0.95,
                top_k=40,
                candidate_count=1,
                max_output_tokens=8192,
                response_modalities=["IMAGE"],
            )
            
            # Улучшаем промпт с соотношением сторон
            enhanced_prompt = f"{prompt}, aspect ratio {aspect_ratio}, high quality, detailed"
            
            # Генерация
            response = client.models.generate_content(
                model="models/nano-banana-pro-preview",
                contents=enhanced_prompt,
                config=generation_config
            )
            
            # Диагностика ответа
            print(f"📊 Response получен:")
            print(f"   Type: {type(response)}")
            print(f"   Has candidates: {hasattr(response, 'candidates')}")
            if hasattr(response, 'candidates'):
                print(f"   Candidates: {response.candidates}")
                if response.candidates:
                    print(f"   Candidates count: {len(response.candidates)}")
            
            # Извлекаем изображение
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Проверяем что content и parts существуют
                if not hasattr(candidate, 'content') or not candidate.content:
                    print(f"⚠️ У candidate нет content")
                    return {
                        'success': False,
                        'image_bytes': None,
                        'error': 'Кандидат не содержит content'
                    }
                
                if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                    print(f"⚠️ У content нет parts")
                    return {
                        'success': False,
                        'image_bytes': None,
                        'error': 'Content не содержит parts'
                    }
                
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        
                        # Декодируем base64 если нужно
                        if isinstance(image_data, str):
                            image_bytes = base64.b64decode(image_data)
                        else:
                            image_bytes = image_data
                        
                        print(f"✅ Изображение сгенерировано! Размер: {len(image_bytes)} байт")
                        
                        return {
                            'success': True,
                            'image_bytes': image_bytes,
                            'size': len(image_bytes)
                        }
                
                return {
                    'success': False,
                    'image_bytes': None,
                    'error': 'Изображение не найдено в ответе'
                }
            else:
                return {
                    'success': False,
                    'image_bytes': None,
                    'error': 'Нет результатов генерации'
                }
                
        except Exception as e:
            error_msg = str(e)[:200]
            print(f"❌ Ошибка генерации: {error_msg}")
            
            return {
                'success': False,
                'image_bytes': None,
                'error': f'Ошибка Gemini: {error_msg}'
            }
    
    def generate_for_product(
        self,
        product_name: str,
        category: str,
        style: str = "professional",
        aspect_ratio: str = "1:1"
    ) -> dict:
        """
        Генерация изображения для товара
        
        Args:
            product_name: Название товара
            category: Категория
            style: Стиль (professional, artistic, minimalist, vibrant)
            aspect_ratio: Соотношение сторон
            
        Returns:
            dict: результат генерации
        """
        # Формируем промпт на английском
        style_prompts = {
            'professional': 'professional product photography, studio lighting, clean background',
            'artistic': 'artistic composition, creative angle, beautiful lighting',
            'minimalist': 'minimalist style, simple clean design, white background',
            'vibrant': 'vibrant colors, dynamic composition, eye-catching'
        }
        
        style_text = style_prompts.get(style, style_prompts['professional'])
        
        prompt = f"{product_name} in {category} category, {style_text}"
        
        return self.generate(prompt=prompt, aspect_ratio=aspect_ratio)


# Глобальный экземпляр
_generator = None


def get_generator():
    """Получить глобальный экземпляр генератора"""
    global _generator
    if _generator is None:
        try:
            _generator = ImageGenerator()
        except:
            pass
    return _generator


def generate_image(prompt: str, aspect_ratio: str = "1:1") -> dict:
    """
    Быстрая генерация изображения
    
    Args:
        prompt: Описание изображения
        aspect_ratio: Соотношение сторон
        
    Returns:
        dict: результат генерации
    """
    generator = get_generator()
    if generator:
        return generator.generate(prompt, aspect_ratio)
    else:
        return {
            'success': False,
            'image_bytes': None,
            'error': 'Генератор не инициализирован'
        }


print("✅ ai/image_generator.py загружен")
