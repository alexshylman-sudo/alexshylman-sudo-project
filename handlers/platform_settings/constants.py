"""
Константы для настроек изображений платформ
"""

# ═══════════════════════════════════════════════════════════════
# ФОРМАТЫ ИЗОБРАЖЕНИЙ
# ═══════════════════════════════════════════════════════════════

PLATFORM_FORMATS = {
    'pinterest': [
        ('2:3', '📱 2:3 (портрет)'),
        ('1:1', '⬜ 1:1 (квадрат)'),
        ('4:5', '📱 4:5 (портрет)'),
        ('9:16', '📱 9:16 (сторис)'),
        ('3:4', '📱 3:4 (портрет)'),
        ('16:9', '📺 16:9 (широкий)'),
        ('21:9', '📺 21:9 (ультра-широкий)'),
        ('24:9', '📺 24:9 (панорама)'),
    ],
    'telegram': [
        ('16:9', '📺 16:9 (широкий)'),
        ('1:1', '⬜ 1:1 (квадрат)'),
        ('4:3', '📺 4:3 (стандарт)'),
        ('3:2', '📺 3:2 (фото)'),
        ('21:9', '📺 21:9 (ультра-широкий)'),
        ('24:9', '📺 24:9 (панорама)'),
    ],
    'website': [
        ('16:9', '📺 16:9 (широкий)'),
        ('4:3', '📺 4:3 (стандарт)'),
        ('1:1', '⬜ 1:1 (квадрат)'),
        ('3:2', '📺 3:2 (фото)'),
        ('21:9', '📺 21:9 (ультра-широкий)'),
        ('24:9', '📺 24:9 (панорама)'),
    ],
    'instagram': [
        ('1:1', '⬜ 1:1 (feed-пост)'),
        ('4:5', '📱 4:5 (feed-портрет)'),
        ('9:16', '📱 9:16 (stories/reels)'),
        ('16:9', '📺 16:9 (IGTV)'),
        ('4:3', '📺 4:3 (стандарт)'),
        ('2:3', '📱 2:3 (портрет)'),
    ],
    'vk': [
        ('16:9', '📺 16:9 (стандарт)'),
        ('1:1', '⬜ 1:1 (квадрат)'),
        ('4:3', '📺 4:3 (фото)'),
        ('3:2', '📺 3:2 (фото)'),
        ('9:16', '📱 9:16 (клипы)'),
        ('21:9', '📺 21:9 (широкий)'),
        ('24:9', '📺 24:9 (панорама)'),
    ]
}

# ═══════════════════════════════════════════════════════════════
# СТИЛИ ИЗОБРАЖЕНИЙ
# ═══════════════════════════════════════════════════════════════

IMAGE_STYLES = {
    'photorealistic': {
        'name': '📸 Фотореалистичный',
        'prompt': 'photorealistic, high quality, detailed, professional photography, 8k'
    },
    'anime': {
        'name': '🌸 Anime',
        'prompt': 'anime style, manga art, vibrant colors, detailed eyes, Japanese animation'
    },
    'oil_painting': {
        'name': '🎨 Масляная живопись',
        'prompt': 'oil painting, artistic, brush strokes, canvas texture, classical art style'
    },
    'watercolor': {
        'name': '🖌 Акварель',
        'prompt': 'watercolor painting, soft colors, flowing paint, artistic, delicate'
    },
    'cartoon': {
        'name': '🎬 Мультяшный',
        'prompt': 'cartoon style, vibrant colors, simplified shapes, animated look, fun'
    },
    'sketch': {
        'name': '✏️ Набросок',
        'prompt': 'pencil sketch, hand-drawn, artistic, monochrome, detailed linework'
    },
    '3d_render': {
        'name': '🎭 3D рендер',
        'prompt': '3d render, cgi, realistic lighting, high detail, modern graphics'
    },
    'pixel_art': {
        'name': '🎮 Пиксель-арт',
        'prompt': 'pixel art, retro gaming, 8-bit style, blocky, nostalgic'
    },
    'minimalism': {
        'name': '⚪ Минимализм',
        'prompt': 'minimalist, simple, clean lines, modern, elegant, white space, geometric'
    },
    'cyberpunk': {
        'name': '🔮 Киберпанк',
        'prompt': 'cyberpunk style, neon lights, futuristic, dark atmosphere, high tech, dystopian'
    }
}

# ═══════════════════════════════════════════════════════════════
# ТОНАЛЬНОСТЬ
# ═══════════════════════════════════════════════════════════════

TONE_PRESETS = {
    'bw': {
        'name': '⬛ Черно-белое',
        'prompt': 'black and white, high contrast, dramatic shadows'
    },
    'golden_hour': {
        'name': '🌅 Золотой час',
        'prompt': 'golden hour, warm sunset lighting, orange and pink tones'
    },
    'blue_hour': {
        'name': '🌃 Синий час',
        'prompt': 'blue hour, cool twilight atmosphere, deep blue tones'
    },
    'light_airy': {
        'name': '☁️ Светлое и воздушное',
        'prompt': 'bright and airy, soft natural light, pastel colors'
    },
    'dark_moody': {
        'name': '🌑 Темное и мрачное',
        'prompt': 'dark and moody, low key lighting, deep shadows'
    },
    'vibrant': {
        'name': '🌈 Яркие цвета',
        'prompt': 'vibrant and saturated, bold colors, high contrast'
    },
    'cinematic': {
        'name': '🎬 Кинематограф',
        'prompt': 'cinematic color grading, teal and orange color palette'
    },
    'vintage': {
        'name': '📼 Винтажная пленка',
        'prompt': 'vintage film, faded colors, light leaks, grain'
    }
}

# ═══════════════════════════════════════════════════════════════
# КАМЕРЫ
# ═══════════════════════════════════════════════════════════════

CAMERA_PRESETS = {
    'canon_r5': {
        'name': '📷 Canon EOS R5',
        'prompt': 'Canon EOS R5, 50mm f/1.2 lens, shallow depth of field'
    },
    'sony_a7r': {
        'name': '📷 Sony A7R IV',
        'prompt': 'Sony A7R IV, 85mm f/1.4 lens, portrait photography'
    },
    'nikon_d850': {
        'name': '📷 Nikon D850',
        'prompt': 'Nikon D850, 24-70mm f/2.8 lens, wide angle view'
    },
    'iphone_15': {
        'name': '📱 iPhone 15 Pro',
        'prompt': 'iPhone 15 Pro Max, ultra-wide lens, mobile photography'
    },
    'gopro_12': {
        'name': '🎬 GoPro Hero 12',
        'prompt': 'GoPro Hero 12, fisheye lens, action shot perspective'
    },
    'dji_mavic': {
        'name': '🚁 DJI Mavic 3',
        'prompt': 'DJI Mavic 3, aerial perspective, drone shot from above'
    },
    'hasselblad': {
        'name': '📷 Hasselblad H6D',
        'prompt': 'Hasselblad H6D-400c, 80mm lens, medium format, ultra high resolution'
    },
    'polaroid': {
        'name': '📸 Polaroid SX-70',
        'prompt': 'Polaroid SX-70, instant camera, vintage aesthetic'
    }
}

# ═══════════════════════════════════════════════════════════════
# РАКУРСЫ И УГЛЫ ОБЗОРА
# ═══════════════════════════════════════════════════════════════

ANGLE_PRESETS = {
    'macro': {
        'name': '🔬 Макро (крупный план)',
        'prompt': 'extreme close-up, macro photography, detailed texture, shallow depth of field'
    },
    'close_up': {
        'name': '👁 Ближний план',
        'prompt': 'close-up shot, detailed view, focused subject'
    },
    'medium': {
        'name': '👤 Средний план',
        'prompt': 'medium shot, waist-level view, balanced composition'
    },
    'full': {
        'name': '🧍 Общий план',
        'prompt': 'full shot, full body view, complete scene'
    },
    'wide': {
        'name': '🏞 Дальний план',
        'prompt': 'wide shot, landscape view, environmental context'
    },
    'extreme_wide': {
        'name': '🌄 Сверх-дальний план',
        'prompt': 'extreme wide shot, panoramic view, vast landscape'
    },
    'aerial': {
        'name': '🚁 Вид сверху (aerial)',
        'prompt': 'aerial view, top-down perspective, bird eye view, drone shot'
    },
    'top_down': {
        'name': '⬇️ Вид сверху (flat lay)',
        'prompt': 'top-down view, flat lay, overhead shot, 90 degree angle'
    },
    'low_angle': {
        'name': '⬆️ Снизу вверх',
        'prompt': 'low angle shot, looking up, dramatic perspective from below'
    },
    'high_angle': {
        'name': '⬇️ Сверху вниз',
        'prompt': 'high angle shot, looking down, overhead perspective'
    },
    'eye_level': {
        'name': '👁 На уровне глаз',
        'prompt': 'eye level shot, neutral perspective, straight on view'
    },
    'dutch_angle': {
        'name': '🎭 Голландский угол',
        'prompt': 'dutch angle, tilted camera, dynamic diagonal composition'
    },
    'over_shoulder': {
        'name': '👥 Через плечо',
        'prompt': 'over the shoulder shot, perspective from behind subject'
    },
    'pov': {
        'name': '👀 От первого лица (POV)',
        'prompt': 'point of view shot, first person perspective, subjective camera'
    }
}

# ═══════════════════════════════════════════════════════════════
# УРОВЕНЬ ДЕТАЛИЗАЦИИ И КАЧЕСТВО
# ═══════════════════════════════════════════════════════════════

QUALITY_PRESETS = {
    'standard': {
        'name': '📷 Стандарт',
        'prompt': 'good quality, clear image, standard resolution'
    },
    'high_detail': {
        'name': '🔍 Высокая детализация',
        'prompt': 'highly detailed, intricate details, fine texture, sharp focus'
    },
    'ultra_detail': {
        'name': '💎 Ультра детализация',
        'prompt': 'ultra detailed, extremely intricate, microscopic details, professional grade'
    },
    'hd': {
        'name': '📺 HD качество',
        'prompt': 'HD quality, 1080p, high definition, crisp and clear'
    },
    '4k': {
        'name': '🎬 4K Ultra HD',
        'prompt': '4K resolution, ultra high definition, 3840x2160, exceptional clarity'
    },
    '8k': {
        'name': '🖥 8K качество',
        'prompt': '8K resolution, 7680x4320, extreme detail, professional cinema quality'
    },
    'hyperrealistic': {
        'name': '✨ Гиперреализм',
        'prompt': 'hyperrealistic, photorealistic perfection, lifelike, indistinguishable from reality'
    },
    'ultra_quality': {
        'name': '👑 Ультра качество',
        'prompt': 'ultra quality, masterpiece, award winning, professional studio quality'
    },
    'studio': {
        'name': '🎥 Студийное качество',
        'prompt': 'studio quality lighting, professional photography, commercial grade'
    },
    'raw': {
        'name': '📸 RAW качество',
        'prompt': 'RAW format quality, uncompressed, maximum dynamic range, professional'
    },
    'cinematic': {
        'name': '🎞 Кинематографическое',
        'prompt': 'cinematic quality, film grade, Hollywood production value, epic detail'
    },
    'sharp': {
        'name': '⚡ Максимальная резкость',
        'prompt': 'ultra sharp, tack sharp, crystal clear, perfect focus, razor sharp details'
    }
}

# ═══════════════════════════════════════════════════════════════
# РЕКОМЕНДАЦИИ ПО ПЛАТФОРМАМ
# ═══════════════════════════════════════════════════════════════

RECOMMENDED_FORMATS = {
    'pinterest': '2:3',
    'telegram': '16:9',
    'website': '16:9',
    'instagram': '1:1',    # Квадрат для feed
    'vk': '16:9'           # Широкий стандарт
}

# Названия платформ для отображения
PLATFORM_NAMES = {
    'pinterest': 'Pinterest',
    'telegram': 'Telegram',
    'website': 'Website',
    'instagram': 'Instagram',
    'vk': 'VK'
}


# ═══════════════════════════════════════════════════════════════
# ТЕКСТ НА ИЗОБРАЖЕНИИ
# ═══════════════════════════════════════════════════════════════

TEXT_ON_IMAGE_PRESETS = {
    '0': '🚫 Никогда (0%)',
    '10': '📝 Редко (10%)',
    '20': '📝 Иногда (20%)',
    '30': '📝 Часто (30%)',
    '50': '📝 Половина (50%)',
    '70': '📝 Большинство (70%)',
    '100': '📝 Всегда (100%)'
}

TEXT_STYLES_DESCRIPTION = """
📝 <b>Текст на изображении</b>

Процент показывает, как часто на изображениях будет текст:
• 0% - текст никогда не добавляется
• 10% - каждое 10-е изображение с текстом
• 50% - половина изображений с текстом
• 100% - все изображения с текстом

<b>Стиль текста:</b> журнальные надписи, заголовки, подписи
<i>Пример: "НОВИНКА 2024", "TOP 5", "Exclusive"</i>
"""


# ═══════════════════════════════════════════════════════════════
# КОЛЛАЖ ИЛИ ЦЕЛЬНОЕ ИЗОБРАЖЕНИЕ
# ═══════════════════════════════════════════════════════════════

COLLAGE_PRESETS = {
    '0': '🖼️ Всегда цельное (0%)',
    '10': '🎨 Редко коллаж (10%)',
    '20': '🎨 Иногда коллаж (20%)',
    '30': '🎨 Часто коллаж (30%)',
    '50': '🎨 Половина коллажей (50%)',
    '70': '🎨 Много коллажей (70%)',
    '100': '🎨 Всегда коллаж (100%)'
}

COLLAGE_DESCRIPTION = """
🎨 <b>Коллаж или цельное изображение</b>

Процент показывает, как часто будет создаваться коллаж:
• 0% - всегда цельное изображение
• 10% - каждое 10-е изображение коллаж
• 50% - половина изображений коллажи
• 100% - все изображения коллажи

<b>Коллаж:</b> несколько элементов на одном изображении
<b>Цельное:</b> одна композиция, один объект
"""


print("✅ platform_settings/constants.py загружен")

