# -*- coding: utf-8 -*-
"""
Генератор SEO-статей для сайтов с продвинутыми промптами
Включает: Yoast SEO оптимизацию, Schema.org, адаптацию под цвета сайта
"""
import anthropic
from config import ANTHROPIC_API_KEY
from datetime import datetime


# Инициализация клиента
client = None
if ANTHROPIC_API_KEY:
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print("✅ Claude API для генерации статей инициализирован")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации Claude: {e}")


def get_adaptive_colors(site_colors=None):
    """
    Получает адаптивные цвета для блоков статьи
    
    Args:
        site_colors: dict с цветами сайта (если известны)
        
    Returns:
        dict: Набор цветов для использования в статье
    """
    if not site_colors:
        # Цвета по умолчанию
        return {
            'bg': '#ffffff',
            'text': '#333333',
            'accent': '#0066cc',
            'block_bg': '#f8f9fa',
            'block_text': '#212529',
            'block_border': '#0066cc',
            'is_dark_theme': False
        }
    
    # Определяем тёмная ли тема
    bg = site_colors.get('background', '#ffffff').lower()
    is_dark = False
    
    # Проверка на тёмный фон
    if bg.startswith('#'):
        # Конвертируем hex в RGB и вычисляем яркость
        hex_color = bg.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            is_dark = brightness < 128
    
    # Для тёмной темы
    if is_dark:
        return {
            'bg': bg,
            'text': site_colors.get('text', '#e0e0e0'),
            'accent': site_colors.get('accent', '#4dabf7'),
            'block_bg': '#2b2b2b',  # Чуть светлее основного фона
            'block_text': '#ffffff',
            'block_border': site_colors.get('accent', '#4dabf7'),
            'is_dark_theme': True
        }
    
    # Для светлой темы
    return {
        'bg': bg,
        'text': site_colors.get('text', '#333333'),
        'accent': site_colors.get('accent', '#0066cc'),
        'block_bg': '#f8f9fa',
        'block_text': '#212529',
        'block_border': site_colors.get('accent', '#0066cc'),
        'is_dark_theme': False
    }


def generate_website_article(
    keyword,
    category_name,
    category_description="",
    company_data=None,
    prices=None,
    reviews=None,
    external_links=None,
    internal_links=None,
    text_style="professional",
    html_style="creative",
    site_colors=None,
    min_words=1500,
    max_words=2500,
    h2_list=None,
    author_data=None
):
    """
    Генерирует SEO-статью для сайта с полной оптимизацией
    
    Args:
        keyword: Основное ключевое слово
        category_name: Название категории
        category_description: Описание категории для контекста
        company_data: dict с данными компании
        prices: list с ценами
        reviews: list с отзывами клиентов (3 штуки)
        external_links: list внешних ссылок (соцсети)
        internal_links: list внутренних ссылок сайта
        text_style: стиль текста (professional, conversational, informative, motivational)
        html_style: стиль HTML (creative, news, minimalistic)
        site_colors: dict с цветами сайта {'background': '#fff', 'text': '#333', 'accent': '#0066cc'}
        min_words: Минимум слов
        max_words: Максимум слов
        h2_list: Список подзаголовков H2 (или None для автогенерации)
        author_data: dict с данными автора {'id': int, 'name': str, 'avatar_url': str, 'bio': str}
        
    Returns:
        dict: {
            'success': True/False,
            'html': 'HTML статьи',
            'seo_title': 'SEO заголовок',
            'meta_description': 'Мета описание',
            'word_count': 1234,
            'error': 'текст ошибки' (если success=False)
        }
    """
    
    if not client:
        return {
            'success': False,
            'error': 'Claude API не инициализирован'
        }
    
    # Получаем адаптивные цвета
    colors = get_adaptive_colors(site_colors)
    
    # Дефолтные данные компании
    if not company_data:
        company_data = {}
    
    # Текущая дата
    now = datetime.now()
    current_year = now.year
    current_date = now.strftime("%B %Y")
    
    # Извлекаем данные компании
    company_name = company_data.get('company_name', 'Наша компания')
    company_city = company_data.get('company_city', '')
    company_address = company_data.get('company_address', '')
    company_phone = company_data.get('company_phone', '')
    company_email = company_data.get('company_email', '')
    
    # Формируем блок с данными компании
    company_section = f"""
═══════════════════════════════════════════════════════════════
🏢 ДАННЫЕ КОМПАНИИ (ОБЯЗАТЕЛЬНО ИСПОЛЬЗУЙ!)
═══════════════════════════════════════════════════════════════
НАЗВАНИЕ: {company_name}
"""
    
    if company_city:
        company_section += f"\nГОРОД: {company_city}"
    if company_address:
        company_section += f"\nАДРЕС: {company_address}"
    if company_phone:
        company_section += f"\nТЕЛЕФОН: {company_phone}"
    
    # Цены
    if prices:
        company_section += "\n\nЦЕНЫ (используй эти РЕАЛЬНЫЕ цены из прайс-листа):\n"
        company_section += "ВАЖНО: Это таблица с ценами, используй ВСЕ столбцы!\n\n"
        
        for price_item in prices:
            # Формируем строку со ВСЕМИ данными из таблицы
            line_parts = []
            for key, value in price_item.items():
                if value and str(value).strip():  # Только непустые значения
                    line_parts.append(f"{key}: {value}")
            
            if line_parts:
                company_section += f"• {' | '.join(line_parts)}\n"
    else:
        company_section += "\n\nЦЕНЫ: Не указаны. Пиши 'Уточняйте стоимость по телефону'"
    
    # Блок с данными автора
    author_section = ""
    if author_data:
        author_name = author_data.get('name', '')
        author_avatar = author_data.get('avatar_url', '')
        author_bio = author_data.get('bio', '')
        
        author_section = f"""

═══════════════════════════════════════════════════════════════
✍️ ДАННЫЕ АВТОРА СТАТЬИ (ОБЯЗАТЕЛЬНО ДОБАВЬ В КОНЕЦ!)
═══════════════════════════════════════════════════════════════
ИМЯ: {author_name}
ФОТО (Gravatar): {author_avatar}
БИОГРАФИЯ: {author_bio if author_bio else 'Эксперт компании'}

⚠️ ВАЖНО: В КОНЦЕ статьи (после блока "О компании") ОБЯЗАТЕЛЬНО добавь РАСШИРЕННУЮ карточку автора!

СТРУКТУРА РАСШИРЕННОЙ КАРТОЧКИ АВТОРА:

<div style="background-color: #f8f9fa !important; padding: 30px; margin: 30px 0 0 0; border-radius: 12px; border: 2px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
    
    <!-- Заголовок и фото -->
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 25px; padding-bottom: 20px; border-bottom: 2px solid #dee2e6;">
        <img src="{author_avatar}" alt="{author_name}" style="width: 90px; height: 90px; border-radius: 50%; border: 3px solid {colors['accent']}; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
        <div>
            <h3 style="margin: 0 0 8px 0; color: #333333 !important; font-size: 1.4em; font-weight: 600;">Автор статьи: {author_name}</h3>
            <p style="margin: 0; color: {colors['accent']} !important; font-size: 1em; font-weight: 500;">
                [Должность: придумай подходящую должность в компании {company_name} по теме статьи]
            </p>
        </div>
    </div>
    
    <!-- Профессиональная информация -->
    <div style="background-color: #ffffff !important; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 15px 0; color: #333333 !important; font-size: 1.1em; border-bottom: 2px solid {colors['accent']}; padding-bottom: 8px;">
            📋 Профессиональная информация
        </h4>
        <ul style="margin: 0; padding-left: 20px; color: #333333 !important; line-height: 1.8;">
            <li style="color: #333333 !important; margin: 8px 0;">
                <strong>Опыт работы:</strong> [N лет в индустрии, связанной с темой статьи]
            </li>
            <li style="color: #333333 !important; margin: 8px 0;">
                <strong>Специализация:</strong> [Специализация по теме статьи: например "Сравнительный анализ отделочных материалов" для WPC панелей, или "Селекция и разведение породистых собак" для статьи о животных]
            </li>
            <li style="color: #333333 !important; margin: 8px 0;">
                <strong>Реализовано проектов/клиентов:</strong> [Число проектов/клиентов: например "300+ объектов", "150+ довольных владельцев"]
            </li>
            <li style="color: #333333 !important; margin: 8px 0;">
                <strong>Профессиональные достижения:</strong>
                <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                    <li style="color: #333333 !important;">[Достижение 1: сертификация, награда, публикация - должно быть по теме]</li>
                    <li style="color: #333333 !important;">[Достижение 2: авторство статей, консультации]</li>
                    <li style="color: #333333 !important;">[Достижение 3: экспертиза, опыт]</li>
                </ul>
            </li>
        </ul>
    </div>
    
    <!-- Личное мнение -->
    <div style="background-color: #fff3e0 !important; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800;">
        <h4 style="margin: 0 0 12px 0; color: #333333 !important; font-size: 1.1em;">
            💭 Личное мнение эксперта
        </h4>
        <p style="margin: 0; color: #333333 !important; line-height: 1.7; font-style: italic; font-size: 0.95em;">
            [Напиши личное мнение автора о теме статьи (3-5 предложений):
            - Должно отражать реальный опыт работы
            - Непредвзятый взгляд (не только плюсы, но и реалистичная оценка)
            - Практические инсайты из опыта
            - Помощь клиентам в выборе оптимального решения
            
            Пример для WPC панелей: "За N лет работы я перестал смотреть на материалы как на 'хорошие' или 'плохие'. Каждый материал имеет свою зону применения. Моя задача - помочь клиенту найти баланс между бюджетом, сроками и желаемым результатом. WPC панели - не панацея, но для влажных помещений и быстрого ремонта они действительно вне конкуренции."
            
            Адаптируй под ТЕМУ СТАТЬИ!]
        </p>
    </div>
    
    <!-- Контакт (только если указан реальный email) -->
    {f'''<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
        <p style="margin: 0; color: #666666 !important; font-size: 0.9em;">
            📧 Контакт для профессиональных консультаций: {company_email}
        </p>
    </div>''' if company_email else ''}
    
</div>

⚠️ КРИТИЧНО: 
- ВСЯ информация должна быть РЕАЛИСТИЧНОЙ и соответствовать ТЕМЕ СТАТЬИ
- Придумай конкретные цифры (годы опыта, количество проектов)
- Достижения должны быть связаны с темой (не пиши про WPC если статья про собак!)
- Личное мнение должно быть КОНКРЕТНЫМ и показывать ЭКСПЕРТИЗУ

Это ПОСЛЕДНИЙ блок в статье перед закрывающим </div>!
"""
    
    # Маппинг стилей текста на описания
    text_style_descriptions = {
        'professional': 'Профессиональный, деловой, экспертный. Используй термины, факты, цифры.',
        'conversational': 'Разговорный, дружелюбный, простой язык. Пиши как будто общаешься с другом.',
        'informative': 'Информативный, образовательный, детальный. Объясняй подробно, давай примеры.',
        'motivational': 'Мотивационный, вдохновляющий, энергичный. Воодушевляй читателя к действию.'
    }
    
    # Маппинг HTML стилей на описания
    html_style_descriptions = {
        'creative': 'Креативный дизайн: цветные блоки, выделения, иконки, разнообразное форматирование.',
        'news': 'Новостной стиль: четкие параграфы, списки, таблицы, минимум оформления.',
        'minimalistic': 'Минималистичный: простой текст, минимум блоков, только необходимое форматирование.'
    }
    
    # Формируем секцию стилей
    style_section = f"""
═══════════════════════════════════════════════════════════════
📝 СТИЛЬ ТЕКСТА И HTML ОФОРМЛЕНИЕ
═══════════════════════════════════════════════════════════════

⚠️ СТИЛЬ ТЕКСТА: {text_style.upper()}
{text_style_descriptions.get(text_style, 'Профессиональный стиль')}

⚠️ HTML СТИЛЬ: {html_style.upper()}
{html_style_descriptions.get(html_style, 'Креативный дизайн')}

ВАЖНО:
- Пиши в указанном стиле текста на протяжении ВСЕЙ статьи
- Используй указанное HTML оформление
- Сохраняй единообразие стиля от начала до конца
"""
    
    # Формируем блок с отзывами
    reviews_section = ""
    if reviews and len(reviews) > 0:
        reviews_section = f"""
═══════════════════════════════════════════════════════════════
💬 ОТЗЫВЫ КЛИЕНТОВ (КРИТИЧЕСКИ ВАЖНО!)
═══════════════════════════════════════════════════════════════
⚠️⚠️⚠️ БЕЗ ОТЗЫВОВ СТАТЬЯ БУДЕТ УДАЛЕНА! ⚠️⚠️⚠️

У тебя есть {len(reviews)} РЕАЛЬНЫХ отзыва клиентов. Ты ОБЯЗАН включить их в статью!

📍 ГДЕ РАЗМЕСТИТЬ:
Создай отдельный раздел <h2>Отзывы наших клиентов</h2> 
СРАЗУ ПЕРЕД разделом FAQ или Заключением.

🎨 КАК ОФОРМИТЬ (адаптивные стили):

ВАЖНО: Используй РЕАЛЬНЫЕ даты из отзывов ниже!

<div style="background-color: #f8f9fa !important; padding: 20px; margin: 20px 0; border-left: 4px solid {colors['accent']}; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
    <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 1.1em; color: {colors['accent']} !important;">
        ★★★★★ <span style="color: #333333 !important;">Имя клиента</span>
    </p>
    <p style="margin: 0 0 10px 0; color: #666666 !important; font-size: 0.9em;">[ДАТА ИЗ ОТЗЫВА НИЖЕ]</p>
    <p style="margin: 10px 0; line-height: 1.6; color: #333333 !important;">
        Текст отзыва клиента...
    </p>
</div>

ВАЖНО ДЛЯ ОТЗЫВОВ:
- Фон: #f8f9fa (светло-серый) с !important
- Звезды и имя: {colors['accent']} с !important для яркости
- Текст отзыва: #333333 (темно-серый) с !important
- Дата: #666666 (серый) с !important
- ОБЯЗАТЕЛЬНО используй РЕАЛЬНЫЕ даты из отзывов ниже (не выдумывай!)
- Box-shadow для визуального отделения от фона
- Это гарантирует видимость на любой WordPress теме!

РЕАЛЬНЫЕ ОТЗЫВЫ ДЛЯ СТАТЬИ:
"""
        for i, review in enumerate(reviews, 1):
            stars = '★' * review.get('rating', 5) + '☆' * (5 - review.get('rating', 5))
            
            # Форматируем дату из отзыва
            review_date = review.get('date', '')
            if review_date:
                try:
                    # datetime уже импортирован глобально
                    if isinstance(review_date, str):
                        # Пытаемся разные форматы
                        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d']:
                            try:
                                date_obj = datetime.strptime(review_date, fmt)
                                # Русские названия месяцев
                                months_ru = {
                                    1: 'январь', 2: 'февраль', 3: 'март', 4: 'апрель',
                                    5: 'май', 6: 'июнь', 7: 'июль', 8: 'август',
                                    9: 'сентябрь', 10: 'октябрь', 11: 'ноябрь', 12: 'декабрь'
                                }
                                review_date = f"{months_ru[date_obj.month]} {date_obj.year}"
                                break
                            except:
                                continue
                except:
                    review_date = review_date  # Оставляем как есть
            else:
                review_date = f"декабрь {current_year}"  # Только если даты вообще нет
            
            reviews_section += f"\n━━━ ОТЗЫВ {i} ━━━\n"
            reviews_section += f"👤 Автор: {review.get('author', 'Клиент')}\n"
            reviews_section += f"⭐ Рейтинг: {stars}\n"
            reviews_section += f"📅 ДАТА: {review_date} (ИСПОЛЬЗУЙ ЭТУ ДАТУ!)\n"
            reviews_section += f"💬 Текст: {review.get('text', 'Отличная работа!')}\n"
    
    # Формируем секцию ссылок
    links_section = ""
    
    # Внешние ссылки (соцсети)
    if external_links and len(external_links) > 0:
        links_section += f"""
═══════════════════════════════════════════════════════════════
🌐 ВНЕШНИЕ ССЫЛКИ (СОЦСЕТИ)
═══════════════════════════════════════════════════════════════

У тебя есть {len(external_links)} внешних ссылок (соцсети, мессенджеры).

📍 ГДЕ РАЗМЕСТИТЬ:
В конце статьи, в разделе "Контакты" или "Связаться с нами".

🎨 КАК ОФОРМИТЬ:
<div style="background-color: #f0f7ff !important; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
    <h3 style="margin: 0 0 15px 0; color: {colors['accent']} !important;">Мы в соцсетях</h3>
"""
        for link in external_links:
            # Извлекаем URL из словаря
            link_url = link.get('url', '') if isinstance(link, dict) else str(link)
            link_title = link.get('title', link_url) if isinstance(link, dict) else link_url
            
            # Определяем тип ссылки
            if 'telegram' in link_url.lower() or 't.me' in link_url.lower():
                icon = '📱'
                name = 'Telegram'
            elif 'vk.com' in link_url.lower() or 'vk.ru' in link_url.lower():
                icon = '🔵'
                name = 'ВКонтакте'
            elif 'instagram' in link_url.lower():
                icon = '📷'
                name = 'Instagram'
            elif 'youtube' in link_url.lower():
                icon = '📺'
                name = 'YouTube'
            elif 'whatsapp' in link_url.lower() or 'wa.me' in link_url.lower():
                icon = '💬'
                name = 'WhatsApp'
            else:
                icon = '🔗'
                name = link_title or 'Ссылка'
            
            links_section += f"""    <p style="margin: 10px 0;">
        <a href="{link_url}" target="_blank" rel="noopener noreferrer" style="color: {colors['accent']} !important; text-decoration: none; font-weight: 500;">
            {icon} {name}
        </a>
    </p>"""
        
        links_section += """</div>

⚠️ ВАЖНО:
- Все внешние ссылки должны иметь rel="nofollow noopener"
- target="_blank" для открытия в новой вкладке
- НЕ используй эти ссылки в основном тексте статьи!
"""
    
    # Внутренние ссылки
    if internal_links and len(internal_links) > 0:
        # Фильтруем по приоритету (поддержка как строк, так и чисел)
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for l in internal_links:
            priority = l.get('priority')
            # Преобразуем числовой приоритет в текстовый
            if isinstance(priority, (int, float)):
                if priority >= 3:
                    priority = 'high'
                elif priority >= 2:
                    priority = 'medium'
                else:
                    priority = 'low'
            
            # Фильтруем по приоритету
            if priority == 'high' or priority == 3:
                high_priority.append(l)
            elif priority == 'medium' or priority == 2:
                medium_priority.append(l)
            else:
                low_priority.append(l)
        
        links_section += f"""
═══════════════════════════════════════════════════════════════
🔗 ВНУТРЕННИЕ ССЫЛКИ (ПЕРЕЛИНКОВКА)
═══════════════════════════════════════════════════════════════

У тебя есть {len(internal_links)} внутренних ссылок на страницы сайта.

📊 ПРИОРИТЕТЫ:
🔴 Высокий приоритет: {len(high_priority)} ссылок (добавить в 80% случаев)
🟡 Средний приоритет: {len(medium_priority)} ссылок (добавить в 50% случаев)

📍 КАК ИСПОЛЬЗОВАТЬ:
Естественно вставляй эти ссылки в текст статьи:

ПРИМЕРЫ:
- "Также рекомендуем ознакомиться с <a href='URL'>анкор</a>"
- "Подробнее о [теме] читайте в нашей статье <a href='URL'>анкор</a>"
- "Для сравнения посмотрите <a href='URL'>анкор</a>"

⚠️ ВАЖНО:
- ОБЯЗАТЕЛЬНО используй 2-4 внутренних ссылки на статью
- Ссылки должны быть релевантны контексту
- НЕ перегружай статью ссылками
- Анкор должен быть естественным (не "здесь" или "ссылка")
- БЕЗ ВНУТРЕННИХ ССЫЛОК СТАТЬЯ БУДЕТ ОТКЛОНЕНА!

ФОРМАТ ССЫЛОК:
<a href="https://site.ru/page">естественный анкор текст</a>

ДОСТУПНЫЕ ССЫЛКИ ДЛЯ СТАТЬИ:
"""
        
        # Добавляем высокоприоритетные ссылки
        for i, link in enumerate(high_priority, 1):
            links_section += f"\n🔴 ВЫСОКИЙ ПРИОРИТЕТ #{i}:\n"
            links_section += f"   URL: {link.get('url', '')}\n"
            links_section += f"   Анкор: {link.get('title', '')}\n"
        
        # Добавляем среднеприоритетные ссылки
        for i, link in enumerate(medium_priority, 1):
            links_section += f"\n🟡 СРЕДНИЙ ПРИОРИТЕТ #{i}:\n"
            links_section += f"   URL: {link.get('url', '')}\n"
            links_section += f"   Анкор: {link.get('title', '')}\n"
    
    # Формируем структуру H2
    h2_structure = ""
    if h2_list and len(h2_list) > 0:
        h2_structure = f"""
═══════════════════════════════════════════════════════════════
📑 СТРУКТУРА СТАТЬИ (ОБЯЗАТЕЛЬНЫЕ ПОДЗАГОЛОВКИ H2)
═══════════════════════════════════════════════════════════════
{chr(10).join([f'{i+1}. <h2>{h2}</h2>' for i, h2 in enumerate(h2_list)])}

⚠️ Эти подзаголовки ОБЯЗАТЕЛЬНЫ! Используй их в указанном порядке.
"""
    
    # Адаптивные цвета для промпта
    theme_type = "ТЁМНАЯ" if colors['is_dark_theme'] else "СВЕТЛАЯ"
    
    colors_info = f"""
═══════════════════════════════════════════════════════════════
🎨 ЦВЕТОВАЯ СХЕМА САЙТА ({theme_type} ТЕМА)
═══════════════════════════════════════════════════════════════
Фон сайта: {colors['bg']}
Цвет текста: {colors['text']}
Акцентный цвет: {colors['accent']}

⚠️ КРИТИЧЕСКИ ВАЖНО ДЛЯ БЛОКОВ:
Для выделяющихся блоков (blockquote, важные заметки) используй:

ПРИМЕР ПРАВИЛЬНОГО БЛОКА (адаптивный под любую тему):
<blockquote style="background-color: #f8f9fa !important; border-left: 4px solid {colors['accent']}; padding: 15px; color: #333333 !important; border-radius: 4px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
<strong style="color: {colors['accent']} !important;">Важный момент:</strong> <span style="color: #333333 !important;">Текст важной заметки...</span>
</blockquote>

КРИТИЧЕСКИ ВАЖНО:
- ВСЕГДА используй !important для color и background-color
- Фон блока: #f8f9fa (светло-серый) с !important
- Текст: #333333 (темно-серый) с !important  
- Акценты (заголовки): {colors['accent']} с !important
- Добавляй box-shadow для визуального отделения
- Это гарантирует видимость на ЛЮБОМ фоне WordPress темы
"""
    
    # Промпт для Claude
    system_prompt = """Ты — профессиональный SEO-копирайтер с опытом в E-E-A-T и AEO оптимизации.
Твоя задача — писать статьи, которые:
1. Ранжируются в Google и Яндекс (SEO)
2. Попадают в голосовые ответы и AI-ассистенты (AEO)
3. Получают Featured Snippets (избранные сниппеты)
4. Конвертируют читателей в клиентов"""
    
    user_prompt = f"""Напиши ИДЕАЛЬНУЮ статью для Google, Yoast SEO и AEO (Answer Engine Optimization).

═══════════════════════════════════════════════════════════════
🎯 AEO ОПТИМИЗАЦИЯ (Answer Engine Optimization)
═══════════════════════════════════════════════════════════════

⚠️ КРИТИЧНО! Статья должна быть оптимизирована для:
- Google Featured Snippets (избранные сниппеты)
- Google Assistant / Siri / Alexa (голосовой поиск)
- ChatGPT / Claude / Gemini (AI-ассистенты)
- "People Also Ask" блоки Google

📋 СТРУКТУРА ДЛЯ AEO:

1️⃣ КРАТКОЕ РЕЗЮМЕ В НАЧАЛЕ (30-50 слов)
Сразу после H1 дай ПРЯМОЙ ОТВЕТ на главный вопрос:

<div style="background-color: #f0f7ff !important; border-left: 4px solid {colors['accent']}; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
<p style="margin: 0; font-size: 1.1em; line-height: 1.6; color: #333333 !important;"><strong style="color: {colors['accent']} !important;">Краткий ответ:</strong> <span style="color: #333333 !important;">{keyword} — это [прямой ответ на вопрос 30-50 слов]. Цена от [X] руб. Установка занимает [Y] дней.</span></p>
</div>

⚠️ Этот блок ОБЯЗАТЕЛЕН! Он попадёт в Featured Snippet!
ВАЖНО: Используй светло-голубой фон (#f0f7ff) для выделения, текст #333333 с !important

2️⃣ ЧЕТКАЯ ИЕРАРХИЯ ЗАГОЛОВКОВ

H1: {keyword} (главный вопрос)
└─ H2: Что такое {keyword}? (определение)
└─ H2: Виды {keyword} (классификация)
└─ H2: Как выбрать {keyword}? (практический совет)
└─ H2: Цены на {keyword} (таблица)
└─ H2: Этапы установки {keyword} (пошаговая инструкция)
└─ H2: Отзывы наших клиентов
└─ H2: Часто задаваемые вопросы (FAQ)

3️⃣ ПРЯМЫЕ ОТВЕТЫ НА ВОПРОСЫ

Используй формат "Вопрос → Ответ":

<h3>Сколько стоит {keyword}?</h3>
<p>Стоимость {keyword} начинается от [X] рублей за [единицу]. Цена зависит от [факторы].</p>

<h3>Как долго устанавливается {keyword}?</h3>
<p>Установка {keyword} занимает от [X] до [Y] дней в зависимости от [факторы].</p>

4️⃣ СПИСКИ И ТАБЛИЦЫ

✅ Используй маркированные списки для:
- Преимущества / недостатки
- Этапы работы
- Советы и рекомендации
- Виды и типы

✅ Используй таблицы для:
- Сравнение вариантов
- Цены и характеристики
- Сроки и гарантии

ПРИМЕР ТАБЛИЦЫ ЦЕН:
<table style="width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #ffffff !important; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background-color: {colors['accent']} !important; color: #ffffff !important;">
<th style="padding: 12px; text-align: left; border: 1px solid {colors['accent']}; font-weight: 600; color: #ffffff !important;">Услуга</th>
<th style="padding: 12px; text-align: left; border: 1px solid {colors['accent']}; font-weight: 600; color: #ffffff !important;">Цена</th>
<th style="padding: 12px; text-align: left; border: 1px solid {colors['accent']}; font-weight: 600; color: #ffffff !important;">Срок</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #ffffff !important;">
<td style="padding: 12px; border: 1px solid #ddd; color: #333333 !important;">Консультация</td>
<td style="padding: 12px; border: 1px solid #ddd; color: #333333 !important;">Бесплатно</td>
<td style="padding: 12px; border: 1px solid #ddd; color: #333333 !important;">30 мин</td>
</tr>
<tr style="background-color: #f9f9f9 !important;">
<td style="padding: 12px; border: 1px solid #ddd; color: #333333 !important;">Дополнительная услуга</td>
<td style="padding: 12px; border: 1px solid #ddd; color: #333333 !important;">От 5000₽</td>
<td style="padding: 12px; border: 1px solid #ddd; color: #333333 !important;">1-3 дня</td>
</tr>
</tbody>
</table>

КРИТИЧЕСКИ ВАЖНО ДЛЯ ТАБЛИЦ:
- ВСЕГДА используй !important для цветов: "color: #333333 !important;" и "background-color: #ffffff !important;"
- Это гарантирует видимость на любом фоне WordPress темы
- Фон ячеек: белый (#ffffff) или светло-серый (#f9f9f9)
- Текст: темно-серый (#333333) для максимальной читаемости
- Заголовок: белый текст (#ffffff) на акцентном фоне
- Добавляй box-shadow для визуального отделения от фона страницы

5️⃣ LONG-TAIL КЛЮЧЕВЫЕ ФРАЗЫ

Используй длинные вопросительные фразы:
- "Сколько стоит {keyword} в {company_city if company_city else 'городе'}?"
- "Как правильно выбрать {keyword} для дома?"
- "Какие бывают виды {keyword}?"
- "Что лучше: [вариант 1] или [вариант 2]?"

6️⃣ PEOPLE ALSO ASK (Связанные вопросы)

Отвечай на связанные вопросы в FAQ разделе:
- "Можно ли установить {keyword} самостоятельно?"
- "Сколько прослужит {keyword}?"
- "Нужно ли разрешение на {keyword}?"
- "Как ухаживать за {keyword}?"

7️⃣ ФАКТЫ, ДАННЫЕ, СТАТИСТИКА

Используй конкретные данные:
✅ "В 2024 году спрос на {keyword} вырос на 35%"
✅ "Средний срок службы — 15-20 лет"
✅ "Экономия электроэнергии до 40%"
✅ "Окупаемость за 3-5 лет"

8️⃣ ЕСТЕСТВЕННЫЙ ЯЗЫК

Пиши как живой человек {f"от лица {author_data.get('name', '')} или компании {company_name}" if author_data else f"от лица компании {company_name}"}:
✅ "Давайте разберёмся, что такое {keyword}"
✅ "Вы наверняка задаётесь вопросом..."
✅ "{f'По моему опыту' if author_data else 'По нашему опыту'}, лучше всего..."
✅ "{f'Я рекомендую' if author_data else 'Мы рекомендуем'}..."
❌ "Данный товар представляет собой..." (слишком формально)

{f'''
⚠️ ВАЖНО ДЛЯ СКЛОНЕНИЯ ИМЕНИ АВТОРА:
Имя автора: {author_data.get('name', '')}

При использовании имени автора ОБЯЗАТЕЛЬНО склоняй его правильно:
- "Совет от [имя в родительном падеже]" (от Александра, от Марии, от Игоря)
- "Из опыта [имя в родительном падеже]" (опыта Александра, опыта Марии)
- "По мнению [имя в родительном падеже]" (мнению Александра, мнению Марии)

ПРАВИЛЬНО:
✅ Совет от Александра (родительный падеж)
✅ Из опыта Марии (родительный падеж)
✅ По словам Игоря (родительный падеж)

НЕПРАВИЛЬНО:
❌ Совет от Александр (именительный падеж)
❌ Из опыта Мария (именительный падеж)
''' if author_data else ''}

═══════════════════════════════════════════════════════════════
🚨 КРИТИЧНО! БЕЗ ЭТОГО СТАТЬЯ НЕ БУДЕТ ОПУБЛИКОВАНА!
═══════════════════════════════════════════════════════════════

⚠️⚠️⚠️ ОБЯЗАТЕЛЬНЫЕ ЭЛЕМЕНТЫ В САМОМ КОНЦЕ СТАТЬИ ⚠️⚠️⚠️

После ВСЕХ блоков (FAQ, Заключение, О компании, Автор) добавь:

SEO_TITLE: [Заголовок СТРОГО 50-60 символов]
META_DESC: [Описание СТРОГО 120-160 символов]

🔴 КРИТИЧЕСКИ ВАЖНО:
- SEO_TITLE и META_DESC должны быть ПОСЛЕДНИМИ строками в ответе
- Они НЕ должны быть внутри HTML тегов
- Формат СТРОГО: "SEO_TITLE: текст" и "META_DESC: текст"
- БЕЗ них статья НЕ БУДЕТ опубликована!

Пример правильного конца статьи:

</div>
[блок автора закрывается]

SEO_TITLE: {keyword}{f' в {company_city}' if company_city else ''} — цены, виды | {company_name[:25] if len(company_name) <= 25 else company_name[:22] + '...'}
META_DESC: {keyword}{f' в {company_city}' if company_city else ''} — профессиональная установка. Цены от [X] руб. {f'☎ {company_phone}' if company_phone else 'Бесплатная консультация'}. Быстрый монтаж.

⚠️ КРИТИЧЕСКИ ВАЖНО ДЛЯ SEO_TITLE:
- МАКСИМУМ 60 символов - это ЖЕСТКИЙ ЛИМИТ!
- Оптимально: 50-58 символов
- Если название компании длинное - СОКРАТИ его
- Примеры ПРАВИЛЬНЫХ заголовков:
  ✅ "WPC панели — цены, виды | ЭКОстены" (40 символов)
  ✅ "Панели в Симферополе — каталог | Компания" (45 символов)
  ❌ "Стеновые панели WPC в Симферополе — большой выбор, низкие цены" (66 - СЛИШКОМ ДЛИННО!)

⚠️ ВАЖНО ДЛЯ META_DESC:
- 120-160 символов, содержит ПРЯМОЙ ОТВЕТ
- Должно быть законченное предложение, не обрывать на полуслове

═══════════════════════════════════════════════════════════════

⚠️ ФОРМАТ ОТВЕТА:

ОБЯЗАТЕЛЬНО:
✅ Возвращай ЧИСТЫЙ HTML без markdown
✅ Заголовок H1: <h1>{keyword}</h1>
✅ Краткое резюме СРАЗУ после H1 (30-50 слов)
✅ НЕ используй markdown: *, **, #, ##, ```
✅ Для выделения используй HTML: <strong>, <em>, <h2>, <h3>
✅ В конце ОБЯЗАТЕЛЬНО: SEO_TITLE и META_DESC

ЗАПРЕЩЕНО:
❌ Markdown заголовки: ## Заголовок
❌ Markdown жирный текст: **текст**
❌ Блоки кода: ```html
❌ Отсутствие краткого резюме после H1
❌ Отсутствие SEO_TITLE или META_DESC

═══════════════════════════════════════════════════════════════
📋 ИСХОДНЫЕ ДАННЫЕ
═══════════════════════════════════════════════════════════════
ТЕМА: "{keyword}"
КАТЕГОРИЯ: {category_name}
ОБЪЁМ: {min_words}-{max_words} слов
ГОД: {current_year}

{style_section}

{company_section}

{author_section}

{reviews_section}

{links_section}

{colors_info}

{h2_structure}

{f'═══════════════════════════════════════════════════════════════\\n📋 КОНТЕКСТ КАТЕГОРИИ\\n═══════════════════════════════════════════════════════════════\\n' + category_description + '\\n' if category_description else ''}
═══════════════════════════════════════════════════════════════
🎯 ИДЕАЛЬНАЯ СТРУКТУРА СТАТЬИ
═══════════════════════════════════════════════════════════════

⚠️⚠️⚠️ КРИТИЧНО - ОБЕРТКА ДЛЯ ВСЕГО КОНТЕНТА ⚠️⚠️⚠️

СТАТЬЯ ДОЛЖНА НАЧИНАТЬСЯ С ЭТОГО:
<div style="background-color: #ffffff !important; padding: 40px; margin: 0; border-radius: 0;">

И ЗАКАНЧИВАТЬСЯ ЭТИМ:
</div>

ВСЁ содержимое статьи (H1, резюме, все H2, все блоки) должно быть ВНУТРИ этого div!
Это гарантирует читаемость на любом фоне сайта (темном или светлом).

⚠️⚠️⚠️ КРИТИЧЕСКИ ВАЖНО ДЛЯ H1 ⚠️⚠️⚠️

НЕ ИСПОЛЬЗУЙ "{keyword}" КАК ЕСТЬ В ЗАГОЛОВКЕ H1!

ПЛОХИЕ H1 (❌ ЗАПРЕЩЕНО):
<h1>стеновые панели wpc кабинет домашний</h1>
<h1>{keyword}</h1>

ХОРОШИЕ H1 (✅ ПРАВИЛЬНО):
<h1>Стеновые панели WPC для домашнего кабинета: выбор и установка</h1>
<h1>WPC панели в интерьере кабинета — полное руководство 2026</h1>
<h1>Как выбрать стеновые панели для домашнего офиса</h1>

ПРАВИЛА H1:
✅ Естественный человеческий язык
✅ Может содержать ключевые слова, но в НОРМАЛЬНОЙ форме
✅ Добавляй контекст: ": виды, цены" или "— руководство"
✅ Длина 50-70 символов
✅ Без переспама ключей!

📊 ОБЯЗАТЕЛЬНАЯ СТРУКТУРА:

⚠️ НАЧАЛО СТАТЬИ:
<div style="background-color: #ffffff !important; padding: 40px; margin: 0; border-radius: 0;">

1. <h1 style="color: #333333 !important;">[ЧЕЛОВЕЧЕСКИЙ ЗАГОЛОВОК по правилам выше]</h1>

2. КРАТКОЕ РЕЗЮМЕ (блок с прямым ответом 30-50 слов)
   → Этот блок попадёт в Featured Snippet Google!

3. <h2 style="color: #333333 !important;">Что такое {keyword}?</h2>
   - Определение простыми словами
   - 2-3 абзаца с примерами
   
4. <h2 style="color: #333333 !important;">Виды {keyword}</h2>
   - Маркированный список с описанием каждого вида
   - Таблица сравнения (если уместно)

5. <h2 style="color: #333333 !important;">Как выбрать {keyword}?</h2>
   - Пошаговая инструкция (Шаг 1, Шаг 2, Шаг 3...)
   - Практические советы {f"от автора (склони имя '{author_data.get('name', '')}' в родительный падеж!)" if author_data else f"от специалистов {company_name}"}
   - На что обратить внимание
   - 💡 Блок "Совет" от автора или компании (цитата с фоном)

6. <h2>Цены на {keyword}</h2>
   - Таблица с РЕАЛЬНЫМИ ценами из прайс-листа выше
   - Факторы влияющие на стоимость
   - Информация о скидках

7. <h2>Этапы установки {keyword}</h2>
   - Пошаговая инструкция с указанием ВРЕМЕНИ на каждый этап
   - Формат: "**1. Подготовка поверхности (1 день)**"
   - Формат: "**2. Монтаж каркаса (1 день)**"
   - ОБЯЗАТЕЛЬНО укажи время для каждого этапа!

8. <h2>Частые ошибки при установке</h2>
   - 3-5 распространенных ошибок
   - Как их избежать
   - Последствия неправильного монтажа
   
⚠️ ОБОРАЧИВАЙ СПИСОК В БЛОК:
<div style="background-color: #fff3e0 !important; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #ff9800;">
<ul style="color: #333333 !important; line-height: 1.8;">
<li style="color: #333333 !important; margin: 10px 0;"><strong>Ошибка:</strong> описание и как избежать</li>
</ul>
</div>

9. <h2>Отзывы клиентов</h2>
   - ОБЯЗАТЕЛЬНЫЙ раздел если есть отзывы!
   - Размести ВСЕ отзывы из данных выше
   - ИСПОЛЬЗУЙ ТОЧНЫЕ СТИЛИ из раздела "ОТЗЫВЫ КЛИЕНТОВ" выше!

10. <h2>Часто задаваемые вопросы</h2>
    - МИНИМУМ 5-7 вопросов с ответами
    - Используй H3 для каждого вопроса
    - Прямые короткие ответы (2-3 предложения)

11. <h2 style="color: #333333 !important;">Заключение</h2>
    - Краткое резюме статьи
    - Призыв к действию
    - Контактная информация

12. Блок "О компании" (обязательно!)

13. Блок автора с фото (обязательно!)

⚠️ КОНЕЦ СТАТЬИ - ЗАКРЫВАЮЩИЙ ТЕГ:
</div>

ПОСЛЕ закрывающего </div> должны идти только SEO_TITLE и META_DESC!

═══════════════════════════════════════════════════════════════
📐 ДОПОЛНИТЕЛЬНЫЕ ЭЛЕМЕНТЫ (добавь если уместно)
═══════════════════════════════════════════════════════════════

🧮 КАЛЬКУЛЯТОР РАСЧЕТА (опиши логику):
Добавь раздел с простым расчетом стоимости:

<div style="background-color: #e3f2fd !important; padding: 25px; margin: 25px 0; border-radius: 12px; border-left: 5px solid {colors['accent']}; box-shadow: 0 3px 8px rgba(0,0,0,0.1);">
<h3 style="margin-top: 0; color: {colors['accent']} !important;">🧮 Примерный расчет стоимости</h3>
<p style="color: #333333 !important; margin: 15px 0;"><strong>Площадь:</strong> 20 м²</p>
<p style="color: #333333 !important; margin: 15px 0;"><strong>Материал:</strong> [название] × [цена за единицу]</p>
<p style="color: #333333 !important; margin: 15px 0;"><strong>Работа:</strong> [стоимость монтажа]</p>
<p style="color: #333333 !important; margin: 20px 0 0 0; font-size: 1.3em; font-weight: bold;"><strong>Итого: от [сумма] ₽</strong></p>
<p style="color: #666666 !important; font-size: 0.9em; margin: 10px 0 0 0;">* Точную стоимость рассчитаем после замера</p>
</div>

📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА (3-4 варианта):
Обязательно создай таблицу сравнения минимум 3 вариантов продукта/услуги:
- Бюджетный вариант
- Стандартный вариант
- Премиум вариант
Включи: цену, характеристики, гарантию, срок службы

📍 ЛОКАЛЬНОЕ SEO (если указан город):
- Упомяни город {company_city if company_city else '[город]'} 5-7 раз естественно
- Добавь раздел "Где купить {keyword}{f' в {company_city}' if company_city else ''}"
- Укажи адрес: {company_address if company_address else '[адрес не указан]'}
- Локальные примеры: "В {company_city if company_city else '[городе]'} популярны..."

💡 БЛОК "СОВЕТ" (от автора или компании):
<blockquote style="background-color: #fff3e0 !important; border-left: 5px solid #ff9800; padding: 20px; margin: 25px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
<p style="margin: 0 0 10px 0; font-weight: bold; color: #ff9800 !important; font-size: 1.1em;">💡 Совет {f"от [склони имя '{author_data.get('name', '')}' в родительный падеж!]" if author_data else f"специалистов {company_name}"}</p>
<p style="margin: 0; color: #333333 !important; line-height: 1.6; font-style: italic;">
[Практический совет с конкретным примером]
</p>
</blockquote>

⚠️ БЛОК "ВАЖНО ЗНАТЬ":
<div style="background-color: #ffebee !important; border-left: 5px solid #f44336; padding: 20px; margin: 25px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
<p style="margin: 0 0 10px 0; font-weight: bold; color: #f44336 !important; font-size: 1.1em;">⚠️ Важно знать</p>
<p style="margin: 0; color: #333333 !important; line-height: 1.6;">
[Критически важная информация, предупреждение]
</p>
</div>

═══════════════════════════════════════════════════════════════
✍️ СТИЛЬ НАПИСАНИЯ
═══════════════════════════════════════════════════════════════

ДЕЛАЙ:
✅ Пиши абзацы по 3-5 предложений
✅ Используй конкретные цифры и факты
✅ Добавляй эмодзи в заголовки блоков (💡, ⚠️, ✅, 📊, 🎯)
✅ Используй маркированные списки для перечислений
✅ Каждое утверждение подкрепляй фактом или примером
✅ Пиши микро-CTA в конце каждого раздела
✅ Читабельность: простой язык, короткие предложения

НЕ ДЕЛАЙ:
❌ "Как известно", "в современном мире", "на сегодняшний день"
❌ "Данный продукт представляет собой..."
❌ Вода и общие фразы без конкретики
❌ Длинные параграфы больше 7 предложений
❌ Абстрактные утверждения без цифр/фактов

МИКРО-CTA (в конце разделов):
- "Нужна консультация? Звоните {company_phone if company_phone else '[телефон]'}"
- "Узнайте точную стоимость - оставьте заявку"
- "Закажите бесплатный замер прямо сейчас"

ОСНОВНОЙ CTA (в заключении):
<div style="background-color: {colors['accent']} !important; color: #ffffff !important; padding: 30px; margin: 30px 0; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
<h3 style="margin: 0 0 15px 0; color: #ffffff !important; font-size: 1.5em;">Готовы заказать?</h3>
<p style="margin: 0 0 20px 0; color: #ffffff !important; font-size: 1.1em;">Бесплатная консультация и расчет стоимости</p>
<p style="margin: 0; font-size: 1.3em; font-weight: bold; color: #ffffff !important;">☎ {company_phone if company_phone else '[телефон]'}</p>
</div>

⚠️⚠️⚠️ КРИТИЧНО - ЦВЕТА И КОНТРАСТНОСТЬ ⚠️⚠️⚠️

ВАЖНО: Весь контент уже обернут в белый контейнер (см. структуру выше).
Внутри контейнера используй темный текст на светлом фоне:

ПРАВИЛА ЦВЕТОВ:
✅ Все заголовки H1, H2, H3: color: #333333 !important;
✅ Весь текст в параграфах: color: #333333 !important;
✅ Цветные блоки: светлый фон (#f8f9fa, #e3f2fd, #fff3e0, #e8f5e9) + темный текст
✅ Таблицы: background-color: #ffffff !important; + color: #333333 !important;

Любой <div> блок:
<div style="background-color: #ffffff !important; color: #333333 !important; padding: 20px; ...">

Любой <p> параграф:
<p style="color: #333333 !important; ...">

Любой <h2>, <h3> заголовок:
<h2 style="color: #333333 !important; ...">

Любая таблица:
<table style="background-color: #ffffff !important; ...">
<td style="color: #333333 !important; background-color: #ffffff !important; ...">

Любой список:
<ul style="color: #333333 !important; background-color: #ffffff !important; ...">
<li style="color: #333333 !important; ...">

БЛОК "ИЗ ОПЫТА" (используй автора или компанию):
<blockquote style="background-color: #e8f5e9 !important; border-left: 5px solid #4caf50; padding: 20px; margin: 25px 0; border-radius: 8px;">
<p style="margin: 0; color: #333333 !important; line-height: 1.6;">
<strong style="color: #2e7d32 !important;">Из {f"опыта [склони имя '{author_data.get('name', '')}' в родительный падеж!]" if author_data else f"нашего опыта ({company_name})"}</strong> текст...
</p>
</blockquote>

ТАБЛИЦЫ (ОБЯЗАТЕЛЬНО СВЕТЛЫЙ ФОН):
<table style="width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #ffffff !important;">
<thead>
<tr style="background-color: {colors['accent']} !important;">
<th style="padding: 12px; text-align: left; color: #ffffff !important; border: 1px solid #dee2e6;">Заголовок</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #ffffff !important;">
<td style="padding: 10px; color: #333333 !important; border: 1px solid #dee2e6;">Текст</td>
</tr>
</tbody>
</table>

СПИСКИ В БЛОКАХ (ОБЯЗАТЕЛЬНО СВЕТЛЫЙ ФОН):
<div style="background-color: #f8f9fa !important; padding: 20px; margin: 20px 0; border-radius: 8px;">
<ol style="color: #333333 !important; line-height: 1.8;">
<li style="color: #333333 !important; margin: 10px 0;">Текст пункта</li>
</ol>
</div>

⚠️⚠️⚠️ EMOJI - СТРОГИЕ ОГРАНИЧЕНИЯ ⚠️⚠️⚠️

ЗАПРЕЩЕНО:
❌ Emoji в H2 заголовках (💬, 🎯, ✅, ❓)
❌ Больше 2-3 emoji на всю статью

РАЗРЕШЕНО:
✅ 1-2 emoji в блоках "Совет эксперта" (💡)
✅ 1 emoji в блоке "Важно" (⚠️)
✅ Телефон в CTA (☎)

ПРИМЕРЫ:
❌ <h2>💬 Отзывы наших клиентов</h2>
✅ <h2>Отзывы наших клиентов</h2>

❌ <h2>🎯 Как выбрать панели</h2>
✅ <h2>Как выбрать панели</h2>

═══════════════════════════════════════════════════════════════
📑 ОГЛАВЛЕНИЕ (Table of Contents) - ОБЯЗАТЕЛЬНО!
═══════════════════════════════════════════════════════════════

После краткого резюме добавь ОГЛАВЛЕНИЕ со ссылками на разделы:

<div style="background-color: #f8f9fa !important; padding: 25px; margin: 25px 0; border-radius: 8px; border: 1px solid #dee2e6;">
<h2 style="margin: 0 0 15px 0; font-size: 1.3em; color: #333333 !important;">Содержание статьи</h2>
<ol style="margin: 0; padding-left: 20px; color: #333333 !important; line-height: 1.8;">
<li><a href="#section-1" style="color: {colors['accent']} !important; text-decoration: none;">Что такое [тема]</a></li>
<li><a href="#section-2" style="color: {colors['accent']} !important; text-decoration: none;">Виды [темы]</a></li>
<li><a href="#section-3" style="color: {colors['accent']} !important; text-decoration: none;">Как выбрать</a></li>
<li><a href="#section-4" style="color: {colors['accent']} !important; text-decoration: none;">Цены</a></li>
<li><a href="#section-5" style="color: {colors['accent']} !important; text-decoration: none;">Этапы установки</a></li>
<li><a href="#section-6" style="color: {colors['accent']} !important; text-decoration: none;">Отзывы клиентов</a></li>
<li><a href="#section-7" style="color: {colors['accent']} !important; text-decoration: none;">Часто задаваемые вопросы</a></li>
</ol>
</div>

И добавь id к каждому H2:
<h2 id="section-1">Что такое [тема]</h2>
<h2 id="section-2">Виды [темы]</h2>
...и так далее

═══════════════════════════════════════════════════════════════
🔍 SEO ДЕТАЛИ
═══════════════════════════════════════════════════════════════

ПЛОТНОСТЬ КЛЮЧЕЙ:
- Основной ключ "{keyword}": 3-5 вхождений естественно
- Плотность ключей: 1-2% от общего текста
- LSI-ключи (синонимы): используй вариации и связанные фразы

ALT-ТЕКСТ ДЛЯ ИЗОБРАЖЕНИЙ:
После каждого раздела укажи где нужно изображение:
📸 [ИЗОБРАЖЕНИЕ: {keyword} - процесс установки | alt="установка {keyword}{f' в {company_city}' if company_city else ''}"]

ВНУТРЕННИЕ ССЫЛКИ:
- ОБЯЗАТЕЛЬНО используй 2-4 внутренних ссылки из списка выше
- Вставляй естественно в контекст
- Используй анкоры с ключевыми словами

6. <h2>Цены на {keyword}{f' в {company_city}' if company_city else ''}</h2>
   - Таблица с ценами (используй реальные цены из данных)
   - Факторы, влияющие на стоимость
   - Как сэкономить

7. <h2>Этапы установки</h2>
   - Нумерованный список этапов
   - Сроки выполнения
   - Что входит в работу
   
⚠️ ВАЖНО ДЛЯ ЭТАПОВ: оберни список в блок со светлым фоном!
<div style="background-color: #ffffff !important; padding: 20px; margin: 20px 0; border-radius: 8px; border: 1px solid #e0e0e0;">
<ol style="color: #333333 !important; line-height: 1.8; padding-left: 20px;">
<li style="color: #333333 !important; margin: 15px 0;"><strong>Шаг 1:</strong> Описание (срок: X дней)</li>
<li style="color: #333333 !important; margin: 15px 0;"><strong>Шаг 2:</strong> Описание (срок: X дней)</li>
</ol>
</div>

8. <h2>Отзывы наших клиентов</h2>
   - 3 реальных отзыва в красивых блоках
   - (если отзывы предоставлены)

9. <h2>Часто задаваемые вопросы</h2>
   - Минимум 5 вопросов в формате FAQ
   - Каждый вопрос = H3
   - Прямые короткие ответы
   - С Schema.org разметкой FAQPage

10. <h2>Заключение</h2>
    - Резюме статьи (3-4 предложения)
    - Призыв к действию
    - Контакты компании

11. <h2>О компании {company_name}</h2>
    - ОБЯЗАТЕЛЬНЫЙ раздел о компании в конце статьи
    - Краткое описание компании (50-80 слов)
    - Преимущества работы с {company_name}
    - Полные контакты в удобном формате
    
    СТРУКТУРА БЛОКА О КОМПАНИИ (ОБЯЗАТЕЛЬНО):
    <div style="background-color: #f8f9fa !important; padding: 30px; margin: 30px 0; border-radius: 12px; border: 2px solid {colors['accent']};">
    <h2 style="margin: 0 0 15px 0; color: {colors['accent']} !important;">О компании {company_name}</h2>
    <p style="color: #333333 !important; line-height: 1.8; margin-bottom: 20px;">
    Компания <strong>{company_name}</strong> — ваш надежный партнер в сфере [описание деятельности]. 
    Мы предлагаем качественные решения, профессиональный монтаж и гарантию на все виды работ. 
    Наши специалисты помогут выбрать оптимальный вариант и реализуют проект любой сложности.
    </p>
    <div style="background-color: #ffffff !important; padding: 20px; border-radius: 8px; margin-top: 15px;">
    <h3 style="margin: 0 0 15px 0; color: #333333 !important; font-size: 1.2em;">Наши преимущества:</h3>
    <ul style="color: #333333 !important; line-height: 1.8; margin: 0; padding-left: 20px;">
    <li style="color: #333333 !important;">Опыт работы более X лет</li>
    <li style="color: #333333 !important;">Гарантия на материалы и работу</li>
    <li style="color: #333333 !important;">Бесплатный замер и консультация</li>
    <li style="color: #333333 !important;">Собственное производство</li>
    <li style="color: #333333 !important;">Прозрачное ценообразование</li>
    </ul>
    </div>
    <div style="background-color: {colors['accent']} !important; color: #ffffff !important; padding: 20px; margin-top: 15px; border-radius: 8px;">
    <h3 style="margin: 0 0 10px 0; color: #ffffff !important; font-size: 1.2em;">Контакты:</h3>
    <p style="margin: 5px 0; color: #ffffff !important; font-size: 1.1em;">
    {f'📍 Адрес: <strong>{company_address}</strong>' if company_address else ''}
    </p>
    <p style="margin: 5px 0; color: #ffffff !important; font-size: 1.1em;">
    {f'📞 Телефон: <strong>{company_phone}</strong>' if company_phone else ''}
    </p>
    {f'<p style="margin: 5px 0; color: #ffffff !important; font-size: 1.1em;">✉️ Email: <strong>{company_email}</strong></p>' if company_email else ''}
    </div>
    </div>

12. SCHEMA.ORG РАЗМЕТКА
    - FAQPage для вопросов
    - LocalBusiness для компании

12. SEO_TITLE и META_DESC (в самом конце)

═══════════════════════════════════════════════════════════════
⚠️ YOAST SEO + AEO ТРЕБОВАНИЯ
═══════════════════════════════════════════════════════════════

✅ Title: 50-60 символов (включает ключевое слово в начале)
✅ Meta Description: 120-156 символов (включает ПРЯМОЙ ОТВЕТ + контакты)
✅ H1: Один раз, НО в человеческой форме (не копируй "{keyword}" дословно!)
✅ Ключевое слово: МАКСИМУМ 3-5 раз в ЕСТЕСТВЕННОЙ форме
✅ Краткое резюме: 30-50 слов сразу после H1 (для Featured Snippet)
✅ Подзаголовки H2: 6-8 штук, логичная структура
✅ H3: Для вопросов в FAQ (каждый вопрос = отдельный H3)
✅ Списки: Маркированные и нумерованные
✅ Таблицы: Для цен и сравнений
✅ Жирный текст: Для важных моментов (<strong>)
✅ Естественный язык: Пиши как живой человек
✅ Прямые ответы: На конкретные вопросы (Что? Сколько? Как? Когда?)
✅ Данные: Конкретные цифры, сроки, факты

⚠️⚠️⚠️ КРИТИЧНО - ПЛОТНОСТЬ КЛЮЧЕЙ ⚠️⚠️⚠️

ЗАПРЕЩЕНО:
❌ Использовать "{keyword}" больше 5 раз
❌ Неестественные вхождения ключа
❌ Копировать "{keyword}" дословно в H1
❌ Плотность ключей выше 1.5%
❌ Keyword stuffing (переспам)

ПРАВИЛЬНО:
✅ Используй ВАРИАЦИИ и СИНОНИМЫ
✅ Естественные формы слов
✅ Плотность 1-1.5% максимум
✅ Читабельность > SEO

ПРИМЕРЫ ВАРИАЦИЙ для "{keyword}":
- панели WPC
- стеновые панели
- композитные панели
- отделочные материалы
- настенные покрытия

🎨 ОФОРМЛЕНИЕ БЛОКОВ:

Используй ТОЛЬКО указанные цвета для блоков!

Краткое резюме (ОБЯЗАТЕЛЬНО):
<div style="background-color: #f0f7ff !important; border-left: 4px solid {colors['accent']}; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
<p style="margin: 0; font-size: 1.1em; line-height: 1.6; color: #333333 !important;"><strong style="color: {colors['accent']} !important;">Краткий ответ:</strong> <span style="color: #333333 !important;">Текст 30-50 слов...</span></p>
</div>

Важный совет (используй имя автора если есть):
<blockquote style="background-color: #f8f9fa !important; border-left: 4px solid {colors['accent']}; padding: 15px; border-radius: 4px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
<strong style="color: {colors['accent']} !important;">💡 Совет {f"от [склони имя '{author_data.get('name', '')}' в родительный падеж!]" if author_data else f"специалистов {company_name}"}:</strong> <span style="color: #333333 !important;">Текст...</span>
</blockquote>

📐 SCHEMA.ORG РАЗМЕТКА (ОБЯЗАТЕЛЬНО):

В конце статьи (после заключения) добавь JSON-LD схемы:

1. FAQPage (для раздела вопросов):
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {{
      "@type": "Question",
      "name": "Вопрос 1?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "Прямой ответ на вопрос"
      }}
    }},
    {{
      "@type": "Question",
      "name": "Вопрос 2?",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "Прямой ответ на вопрос"
      }}
    }}
  ]
}}
</script>

2. LocalBusiness (данные компании):
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{company_name}",
  "telephone": "{company_phone}"{f',\\n  "address": {{\\n    "@type": "PostalAddress",\\n    "addressLocality": "{company_city}"\\n  }}' if company_city else ''}{f',\\n  "priceRange": "$$"' if company_phone else ''}
}}
</script>

3. Article (метаданные статьи) - РАСШИРЕННАЯ ВЕРСИЯ:
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{keyword}",
  "description": "SEO-описание статьи",
  "datePublished": "{current_year}-01-01",
  "dateModified": "{current_year}-01-01",
  "author": {{
    "@type": "Organization",
    "name": "{company_name}"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "{company_name}"
  }},
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "URL статьи"
  }}
}}
</script>

4. Product (если упоминается товар/услуга):
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{keyword}",
  "description": "Описание товара/услуги",
  "offers": {{
    "@type": "Offer",
    "price": "XXXX",
    "priceCurrency": "RUB",
    "availability": "https://schema.org/InStock"
  }}
}}
</script>

5. BreadcrumbList (хлебные крошки):
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{
      "@type": "ListItem",
      "position": 1,
      "name": "Главная",
      "item": "URL главной"
    }},
    {{
      "@type": "ListItem",
      "position": 2,
      "name": "Категория",
      "item": "URL категории"
    }},
    {{
      "@type": "ListItem",
      "position": 3,
      "name": "{keyword}"
    }}
  ]
}}
</script>

═══════════════════════════════════════════════════════════════
✅ ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД ОТПРАВКОЙ
═══════════════════════════════════════════════════════════════

AEO ОПТИМИЗАЦИЯ:
1. ✅ Есть краткое резюме после H1 (30-50 слов)?
2. ✅ Прямые ответы на вопросы (Что? Сколько? Как?)?
3. ✅ Используются списки и таблицы?
4. ✅ Есть FAQ раздел (минимум 5 вопросов)?
5. ✅ Естественный разговорный язык?
6. ✅ Конкретные факты и данные?

YOAST SEO:
7. ✅ Есть H1 с ключевым словом?
8. ✅ Есть 6-8 подзаголовков H2?
9. ✅ Объём {min_words}-{max_words} слов?
10. ✅ Ключевое слово 3-5 раз в тексте?

КОНТЕНТ:
11. ✅ Включены отзывы клиентов (если есть)?
12. ✅ Есть таблица цен?
13. ✅ Есть пошаговая инструкция?
14. ✅ Есть раздел "О компании" с контактами в конце?
15. ✅ Есть блок автора с фото и биографией?

ТЕХНИЧЕСКОЕ:
16. ✅ Есть Schema.org разметка (FAQPage, LocalBusiness, Article)?
17. ✅ Есть SEO_TITLE (50-60 символов)?
18. ✅ Есть META_DESC (120-156 символов с прямым ответом)?
19. ✅ Используются правильные цвета для блоков?
20. ✅ Нет markdown символов (**, ##, ```)?
21. ✅ Статья заканчивается блоком автора?

Если хотя бы один пункт НЕТ — статья будет отклонена!

⚠️ КРИТИЧЕСКИ ВАЖНО! ОБЯЗАТЕЛЬНО ЗАВЕРШЕНИЕ СТАТЬИ:
═══════════════════════════════════════════════════════════════

🔴 СТАТЬЯ ДОЛЖНА БЫТЬ ПОЛНОСТЬЮ ЗАВЕРШЕНА!

✅ Заключение должно содержать:
   - Краткий итог (2-3 предложения)
   - Призыв к действию (CTA)
   - Контактные данные компании

✅ Последний блок - АВТОР (если есть):
   <div class="author-box">
   [информация об авторе]
   </div>

⚠️ НЕ ОБРЫВАЙ СТАТЬЮ НА ПОЛУСЛОВЕ!
⚠️ НЕ ОСТАНАВЛИВАЙСЯ ПОСЕРЕДИНЕ ПРЕДЛОЖЕНИЯ!
⚠️ ОБЯЗАТЕЛЬНО ЗАКОНЧИ ВСЕ РАЗДЕЛЫ!

Если места не хватает - сократи вступление или описания,
но ЗАКЛЮЧЕНИЕ И АВТОР должны быть ПОЛНОСТЬЮ написаны!

═══════════════════════════════════════════════════════════════

НАЧИНАЙ ГЕНЕРАЦИЮ ИДЕАЛЬНОЙ СТАТЬИ:"""
    
    # Логирование для проверки
    print("\n" + "="*80)
    print("📝 \033[96mПРОМПТ ДЛЯ ГЕНЕРАЦИИ ТЕКСТА (CLAUDE)\033[0m")
    print("="*80)
    print("\n\033[93m1. ОСНОВНЫЕ ПАРАМЕТРЫ:\033[0m")
    print(f"   • Ключевое слово: \033[92m{keyword}\033[0m")
    print(f"   • Категория: \033[92m{category_name}\033[0m")
    if category_description:
        if len(category_description) > 200:
            print(f"   • Описание категории: {category_description[:200]}...")
            print(f"     (полное описание: {len(category_description)} символов)")
        else:
            print(f"   • Описание категории: {category_description}")
    else:
        print(f"   • Описание категории: нет")
    print(f"   • Количество слов: \033[92m{min_words}-{max_words}\033[0m")
    print(f"   • Стиль текста: \033[92m{text_style}\033[0m")
    print(f"   • HTML стиль: \033[92m{html_style}\033[0m")
    
    print("\n\033[93m2. ДАННЫЕ КОМПАНИИ:\033[0m")
    if company_data:
        name = company_data.get('name') or company_data.get('company_name') or company_data.get('title')
        city = company_data.get('city', '')
        address = company_data.get('address', '')
        phone = company_data.get('phone', '')
        email = company_data.get('email', '')
        
        print(f"   • Название: {name if name else '\033[91mНЕ ЗАПОЛНЕНО\033[0m'}")
        print(f"   • Город: {city if city else 'не указан'}")
        print(f"   • Адрес: {address if address else 'не указан'}")
        print(f"   • Телефон: {phone if phone else 'не указан'}")
        print(f"   • Email: {email if email else 'не указан'}")
    else:
        print("   • Данные компании отсутствуют")
    
    print("\n\033[93m3. ПРАЙС-ЛИСТ:\033[0m")
    if prices:
        print(f"   • Количество позиций: \033[92m{len(prices)}\033[0m")
        for i, price in enumerate(prices[:3], 1):
            # Проверяем разные варианты структуры данных (включая русские ключи)
            if isinstance(price, dict):
                name = (price.get('name') or price.get('title') or price.get('service') or 
                       price.get('наименование') or price.get('товар') or price.get('продукт'))
                price_value = (price.get('price') or price.get('cost') or price.get('value') or 
                              price.get('цена') or price.get('стоимость'))
                
                if not name:
                    name = '\033[91mБЕЗ НАЗВАНИЯ\033[0m'
                if not price_value:
                    price_value = '\033[91mЦЕНА НЕ УКАЗАНА\033[0m'
                
                print(f"   {i}. {name}: {price_value}")
                # Показываем структуру первого элемента для отладки
                if i == 1:
                    print(f"      \033[90m[Структура: {list(price.keys())}]\033[0m")
            else:
                print(f"   {i}. \033[91mНекорректный формат данных: {type(price)}\033[0m")
        if len(prices) > 3:
            print(f"   ... и еще {len(prices) - 3} позиций")
    else:
        print("   • \033[91mПрайс-лист отсутствует\033[0m")
    
    print("\n\033[93m4. ОТЗЫВЫ:\033[0m")
    if reviews:
        print(f"   • Количество отзывов: \033[92m{len(reviews)}\033[0m")
        for i, review in enumerate(reviews[:2], 1):
            print(f"   {i}. Автор: {review.get('author', 'Аноним')}, Рейтинг: {review.get('rating', '?')}/5")
            print(f"      Текст: {review.get('text', '')[:80]}...")
        if len(reviews) > 2:
            print(f"   ... и еще {len(reviews) - 2} отзывов")
    else:
        print("   • Отзывы отсутствуют")
    
    print("\n\033[93m5. ВНЕШНИЕ ССЫЛКИ:\033[0m")
    if external_links:
        print(f"   • Количество ссылок: \033[92m{len(external_links)}\033[0m")
        for i, link in enumerate(external_links[:3], 1):
            print(f"   {i}. {link.get('title', 'Без названия')}")
            print(f"      URL: {link.get('url', 'нет')}")
    else:
        print("   • Внешние ссылки отсутствуют")
    
    print("\n\033[93m6. ВНУТРЕННИЕ ССЫЛКИ:\033[0m")
    if internal_links:
        print(f"   • Количество ссылок: \033[92m{len(internal_links)}\033[0m")
        for i, link in enumerate(internal_links[:3], 1):
            priority = link.get('priority', 'нет')
            priority_color = '\033[91m' if priority == 'high' else '\033[93m' if priority == 'medium' else '\033[92m'
            print(f"   {i}. [{priority_color}{priority}\033[0m] {link.get('title', 'Без названия')[:60]}")
            print(f"      URL: {link.get('url', 'нет')}")
        if len(internal_links) > 3:
            print(f"   ... и еще {len(internal_links) - 3} ссылок")
    else:
        print("   • Внутренние ссылки отсутствуют")
    
    print("\n\033[93m7. ЦВЕТА САЙТА:\033[0m")
    if site_colors:
        print(f"   • Фон: {colors['bg']}")
        print(f"   • Текст: {colors['text']}")
        print(f"   • Акцент: {colors['accent']}")
        print(f"   • Тёмная тема: {'Да' if colors['is_dark_theme'] else 'Нет'}")
    else:
        print("   • Используются цвета по умолчанию")
    
    print("\n\033[93m8. H2 ЗАГОЛОВКИ:\033[0m")
    if h2_list:
        print(f"   • Количество H2: \033[92m{len(h2_list)}\033[0m")
        for i, h2 in enumerate(h2_list, 1):
            print(f"   {i}. {h2}")
    else:
        print("   • Генерируются автоматически")
    
    print("\n" + "="*80)
    print("\033[96mОТПРАВКА ЗАПРОСА В CLAUDE API...\033[0m")
    print("="*80 + "\n")
    
    # Увеличенный таймаут для больших запросов
    max_retries = 3
    retry_delay = 10  # секунды (увеличено с 2 до 10)
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Попытка {attempt + 1}/{max_retries}...")
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16384,  # Максимум для Claude Sonnet 4
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=300.0  # Увеличенный таймаут до 300 секунд (5 минут)
            )
            
            if response and response.content:
                print("✅ Ответ получен успешно!")
                
                # Проверяем причину остановки
                stop_reason = getattr(response, 'stop_reason', None)
                if stop_reason == 'max_tokens':
                    print("⚠️  ВНИМАНИЕ! Статья обрезана - достигнут лимит max_tokens")
                    print("    Рекомендация: увеличьте max_tokens или сократите промпт")
                elif stop_reason == 'end_turn':
                    print("✅ Статья завершена корректно (end_turn)")
                elif stop_reason:
                    print(f"ℹ️  Причина остановки: {stop_reason}")
                
                article_html = response.content[0].text.strip()
                
                # Извлекаем SEO_TITLE и META_DESC
                seo_title = ""
                meta_desc = ""
                
                import re
                
                # Ищем SEO_TITLE
                title_match = re.search(r'SEO_TITLE:\s*(.+?)(?:\n|$)', article_html, re.IGNORECASE)
                if title_match:
                    seo_title = title_match.group(1).strip()
                    # Удаляем из HTML
                    article_html = re.sub(r'SEO_TITLE:\s*.+?(?:\n|$)', '', article_html, flags=re.IGNORECASE)
                
                # ФОЛЛБЭК: если SEO_TITLE пустой, генерируем из keyword
                if not seo_title:
                    company_name_short = company_name[:30] if company_name else "Наша компания"
                    if company_city:
                        seo_title = f"{keyword} в {company_city} | {company_name_short}"
                    else:
                        seo_title = f"{keyword} — виды, цены | {company_name_short}"
                    print(f"⚠️ SEO_TITLE не найден в ответе, создан автоматически: {seo_title}")
                
                # Ищем META_DESC
                desc_match = re.search(r'META_DESC:\s*(.+?)(?:\n|$)', article_html, re.IGNORECASE)
                if desc_match:
                    meta_desc = desc_match.group(1).strip()
                    # Удаляем из HTML
                    article_html = re.sub(r'META_DESC:\s*.+?(?:\n|$)', '', article_html, flags=re.IGNORECASE)
                
                # ФОЛЛБЭК: если META_DESC пустой, генерируем из keyword
                if not meta_desc:
                    meta_desc = f"{keyword} — профессиональная установка и монтаж"
                    if company_city:
                        meta_desc += f" в {company_city}"
                    if company_phone:
                        meta_desc += f". ☎ {company_phone}"
                    else:
                        meta_desc += ". Бесплатная консультация"
                    print(f"⚠️ META_DESC не найден в ответе, создан автоматически: {meta_desc}")
                
                # Очищаем лишние пустые строки в конце
                article_html = article_html.strip()
                
                return {
                    'success': True,
                    'html': article_html,
                    'seo_title': seo_title,
                    'meta_description': meta_desc,
                    'word_count': len(article_html.split())
                }
            else:
                # Если ответ пустой - пробуем еще раз
                if attempt < max_retries - 1:
                    print(f"⚠️ Пустой ответ, повтор через {retry_delay} сек...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Экспоненциальная задержка
                    continue
                else:
                    return {
                        'success': False,
                        'html': '',
                        'seo_title': '',
                        'meta_description': '',
                        'error': 'Claude вернул пустой ответ после всех попыток'
                    }
                
        except Exception as e:
            error_msg = str(e)
            
            # Проверяем специфичные ошибки
            if '520' in error_msg or 'Cloudflare' in error_msg:
                print(f"⚠️ Ошибка 520 (сервер перегружен)")
                if attempt < max_retries - 1:
                    print(f"   Повтор через {retry_delay} сек...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    error_msg = "API Anthropic временно недоступен (ошибка 520). Попробуйте через несколько минут."
            
            elif 'timeout' in error_msg.lower():
                print(f"⚠️ Таймаут запроса")
                if attempt < max_retries - 1:
                    print(f"   Повтор через {retry_delay} сек...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    error_msg = "Превышено время ожидания ответа от API. Попробуйте уменьшить размер статьи."
            
            # Последняя попытка или другая ошибка
            return {
                'success': False,
                'html': '',
                'seo_title': '',
                'meta_description': '',
                'error': f'Ошибка Claude AI: {error_msg[:200]}'
            }


print("✅ ai/website_article_generator.py загружен")