"""
Генерация текстового контента с помощью Claude AI
"""
import anthropic
from config import ANTHROPIC_API_KEY


# Инициализация клиента
client = None
if ANTHROPIC_API_KEY:
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as e:
        print(f"⚠️ Ошибка инициализации Claude: {e}")


def generate_product_description(
    product_name,
    category,
    features,
    benefits,
    target_audience,
    tone='professional',
    length='medium'
):
    """
    Генерация описания товара/услуги
    
    Args:
        product_name: Название товара
        category: Категория
        features: Характеристики/особенности
        benefits: Преимущества
        target_audience: Целевая аудитория
        tone: Стиль ('professional', 'friendly', 'expert', 'casual')
        length: Длина ('short'=100 слов, 'medium'=300, 'long'=500)
    
    Returns:
        dict: {'success': bool, 'text': str, 'error': str}
    """
    if not ANTHROPIC_API_KEY or not client:
        return {
            'success': False,
            'text': '',
            'error': '⚠️ Claude API не настроен'
        }
    
    # Определяем длину
    word_counts = {
        'short': 100,
        'medium': 300,
        'long': 500
    }
    word_count = word_counts.get(length, 300)
    
    # Определяем стиль
    tone_descriptions = {
        'professional': 'Профессиональный, деловой стиль',
        'friendly': 'Дружелюбный, разговорный стиль',
        'expert': 'Экспертный, авторитетный стиль',
        'casual': 'Неформальный, простой стиль'
    }
    tone_desc = tone_descriptions.get(tone, 'Профессиональный стиль')
    
    system_prompt = f"""Ты — профессиональный копирайтер, специализирующийся на написании продающих описаний товаров и услуг.

СТИЛЬ НАПИСАНИЯ: {tone_desc}

ТРЕБОВАНИЯ К ТЕКСТУ:
1. Привлекательность — текст должен цеплять внимание
2. Убедительность — чёткое донесение ценности
3. Структурированность — логичное изложение
4. SEO-оптимизация — естественное использование ключевых слов
5. Призыв к действию — завершение призывом

ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО готовое описание, без заголовков и пояснений.
Объём: примерно {word_count} слов."""
    
    user_prompt = f"""Напиши продающее описание товара/услуги.

📦 ИНФОРМАЦИЯ О ТОВАРЕ:

Название: {product_name}
Категория: {category}

Характеристики/особенности:
{features}

Преимущества:
{benefits}

Целевая аудитория: {target_audience}

Напиши описание объёмом ~{word_count} слов в стиле "{tone_desc}"."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # Логируем затраты
        try:
            if hasattr(response, 'usage') and response.usage:
                from utils.api_cost_tracker import log_claude_usage
                log_claude_usage(
                    user_id=0,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model="claude-sonnet-4-20250514",
                    operation_type='text_generation'
                )
        except:
            pass
        
        if response and response.content:
            text = response.content[0].text.strip()
            return {
                'success': True,
                'text': text,
                'word_count': len(text.split())
            }
        else:
            return {
                'success': False,
                'text': '',
                'error': 'Claude вернул пустой ответ'
            }
            
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'error': f'Ошибка Claude AI: {str(e)[:200]}'
        }


def generate_meta_tags(page_title, page_content, keywords):
    """
    Генерация meta-тегов для SEO
    
    Args:
        page_title: Заголовок страницы
        page_content: Основной контент страницы
        keywords: Список ключевых слов
    
    Returns:
        dict: {
            'success': bool,
            'meta_title': str (до 60 символов),
            'meta_description': str (до 160 символов),
            'h1': str,
            'error': str
        }
    """
    if not ANTHROPIC_API_KEY or not client:
        return {
            'success': False,
            'error': '⚠️ Claude API не настроен'
        }
    
    keywords_str = ', '.join(keywords[:5]) if isinstance(keywords, list) else keywords
    
    system_prompt = """Ты — SEO-специалист, эксперт по созданию meta-тегов.

ТРЕБОВАНИЯ:
1. Meta Title: до 60 символов, включает главное ключевое слово
2. Meta Description: до 160 символов, побуждает к клику
3. H1: уникальный, отличается от Title, включает ключевое слово

ФОРМАТ ОТВЕТА (строго соблюдай):
TITLE: [текст meta title]
DESCRIPTION: [текст meta description]
H1: [текст заголовка H1]"""
    
    user_prompt = f"""Создай SEO-оптимизированные meta-теги.

ДАННЫЕ СТРАНИЦЫ:

Заголовок: {page_title}

Контент:
{page_content[:500]}...

Ключевые слова: {keywords_str}

Создай meta-теги в указанном формате."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        if response and response.content:
            text = response.content[0].text.strip()
            
            # Парсим ответ
            meta_title = ''
            meta_description = ''
            h1 = ''
            
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('TITLE:'):
                    meta_title = line.replace('TITLE:', '').strip()
                elif line.startswith('DESCRIPTION:'):
                    meta_description = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('H1:'):
                    h1 = line.replace('H1:', '').strip()
            
            return {
                'success': True,
                'meta_title': meta_title[:60],
                'meta_description': meta_description[:160],
                'h1': h1
            }
        else:
            return {
                'success': False,
                'error': 'Claude вернул пустой ответ'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Ошибка: {str(e)[:200]}'
        }


def generate_social_post(
    topic,
    platform,
    style='engaging',
    include_hashtags=True,
    include_emoji=True
):
    """
    Генерация поста для соцсетей
    
    Args:
        topic: Тема поста
        platform: Платформа ('instagram', 'vk', 'telegram', 'facebook')
        style: Стиль ('engaging', 'professional', 'funny', 'inspiring')
        include_hashtags: Добавить хештеги
        include_emoji: Использовать эмодзи
    
    Returns:
        dict: {'success': bool, 'post': str, 'hashtags': list, 'error': str}
    """
    if not ANTHROPIC_API_KEY or not client:
        return {
            'success': False,
            'post': '',
            'hashtags': [],
            'error': '⚠️ Claude API не настроен'
        }
    
    platform_specs = {
        'instagram': 'Instagram (до 2200 символов, визуальный контент)',
        'vk': 'ВКонтакте (до 15000 символов, разнообразный формат)',
        'telegram': 'Telegram (до 4096 символов, информативный стиль)',
        'facebook': 'Facebook (до 63206 символов, универсальный контент)'
    }
    
    style_desc = {
        'engaging': 'Вовлекающий, интерактивный стиль',
        'professional': 'Профессиональный, деловой стиль',
        'funny': 'Юмористический, лёгкий стиль',
        'inspiring': 'Вдохновляющий, мотивирующий стиль'
    }
    
    platform_desc = platform_specs.get(platform, platform_specs['instagram'])
    style_text = style_desc.get(style, style_desc['engaging'])
    
    system_prompt = f"""Ты — SMM-специалист, создающий вирусный контент для соцсетей.

ПЛАТФОРМА: {platform_desc}
СТИЛЬ: {style_text}

ТРЕБОВАНИЯ:
1. Цепляющее начало — привлекает внимание с первой строки
2. Ценность — даёт полезную информацию или эмоции
3. Призыв к действию — побуждает к взаимодействию
4. {'Эмодзи — используй умеренно и к месту' if include_emoji else 'Без эмодзи'}
5. {'Хештеги — 5-10 релевантных хештегов' if include_hashtags else 'Без хештегов'}

ФОРМАТ ОТВЕТА:
Верни готовый пост. {'Хештеги размести в конце поста.' if include_hashtags else ''}"""
    
    user_prompt = f"""Создай пост для {platform}.

ТЕМА: {topic}

Стиль: {style_text}
Эмодзи: {'Да' if include_emoji else 'Нет'}
Хештеги: {'Да' if include_hashtags else 'Нет'}

Создай вовлекающий пост."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        if response and response.content:
            post_text = response.content[0].text.strip()
            
            # Извлекаем хештеги если есть
            hashtags = []
            if include_hashtags:
                import re
                hashtags = re.findall(r'#\w+', post_text)
            
            return {
                'success': True,
                'post': post_text,
                'hashtags': hashtags,
                'char_count': len(post_text)
            }
        else:
            return {
                'success': False,
                'post': '',
                'hashtags': [],
                'error': 'Claude вернул пустой ответ'
            }
            
    except Exception as e:
        return {
            'success': False,
            'post': '',
            'hashtags': [],
            'error': f'Ошибка: {str(e)[:200]}'
        }


def generate_pinterest_description(
    topic,
    max_length=500,
    include_hashtags=True
):
    """
    Генерация описания для Pinterest пина
    
    Pinterest требования:
    - Текст до 500 символов (Pinterest лимит)
    - Без спецсимволов *"№#$ и т.д.
    - С хэштегами в конце через пробел
    - Без emoji (Pinterest плохо их поддерживает)
    - Простой язык, ключевые слова
    
    Args:
        topic: Тема пина
        max_length: Максимальная длина (по умолчанию 500)
        include_hashtags: Добавить хэштеги (по умолчанию True)
    
    Returns:
        dict: {'success': bool, 'description': str, 'hashtags': list, 'error': str}
    """
    if not ANTHROPIC_API_KEY or not client:
        return {
            'success': False,
            'description': '',
            'hashtags': [],
            'error': '⚠️ Claude API не настроен'
        }
    
    system_prompt = f"""Ты — эксперт по Pinterest контенту.

ТРЕБОВАНИЯ К ОПИСАНИЮ ДЛЯ PINTEREST:
1. Текст до {max_length} символов
2. БЕЗ спецсимволов — никаких *, ", №, $, %, &, @ в тексте
3. БЕЗ emoji — Pinterest не поддерживает их хорошо
4. ПРОСТОЙ язык — понятные фразы, ключевые слова
5. {'5-8 хештегов через пробел ПОСЛЕ пустой строки' if include_hashtags else 'Без хештегов'}

СТИЛЬ:
- Естественный текст (2-3 предложения)
- Понятно и информативно
- Хештеги ПОСЛЕ пустой строки, через пробел в одну строку

ФОРМАТ ОТВЕТА:
Верни описание в формате:
Текст описания. Ещё текст описания.

#хештег1 #хештег2 #хештег3 #хештег4 #хештег5

ВАЖНО: Между текстом и хештегами должна быть пустая строка!"""
    
    user_prompt = f"""Создай описание для Pinterest пина.

ТЕМА: {topic}

Требования:
- Максимум {max_length} символов
- Без спецсимволов *, ", №, $, %
- Без emoji
- 2-3 предложения текста
- Пустая строка
- 5-8 хештегов через пробел в одну строку

Формат:
Текст описания.

#хештеги

Создай описание."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        if response and response.content:
            description = response.content[0].text.strip()
            
            # Удаляем запрещенные спецсимволы на всякий случай
            forbidden_chars = ['*', '"', '№', '$', '%', '&', '@']
            for char in forbidden_chars:
                description = description.replace(char, '')
            
            # Убираем множественные пробелы и переносы строк
            import re
            # Нормализуем пробелы в каждой строке
            lines = description.split('\n')
            lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
            # Убираем пустые строки в начале и конце, но оставляем между текстом и хештегами
            description = '\n'.join(lines).strip()
            
            # Обрезаем если слишком длинный
            if len(description) > max_length:
                # Обрезаем по последнему пробелу перед лимитом
                description = description[:max_length].rsplit(' ', 1)[0]
            
            # Извлекаем хештеги
            hashtags = []
            if include_hashtags:
                hashtags = re.findall(r'#\w+', description)
            
            return {
                'success': True,
                'description': description,
                'hashtags': hashtags,
                'char_count': len(description)
            }
        else:
            return {
                'success': False,
                'description': '',
                'hashtags': [],
                'error': 'Claude вернул пустой ответ'
            }
            
    except Exception as e:
        return {
            'success': False,
            'description': '',
            'hashtags': [],
            'error': f'Ошибка: {str(e)[:200]}'
        }


print("✅ ai/text_generator.py загружен")
