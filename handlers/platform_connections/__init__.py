# -*- coding: utf-8 -*-
"""
Модуль подключения платформ (Pinterest, Telegram, Instagram, VK, Website)
"""

# Импортируем модули
from . import utils
from . import main_menu
from . import website_menu
from . import website_cms
from . import website_add_start
from . import pinterest
from . import telegram
from . import instagram
from . import vk
from . import vk_selection  # Обработка выбора VK профиля/группы
from . import vk_direct  # Прямое подключение VK через токен
from . import management_websites
from . import management_social

print("✅ handlers/platform_connections/ загружен")
