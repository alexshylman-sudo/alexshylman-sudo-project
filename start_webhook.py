#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Запуск VK webhook сервера без импорта Telegram бота
"""
import os

if __name__ == '__main__':
    from vk_webhook import app
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting VK webhook server on 0.0.0.0:{port}")
    
    # Запуск с помощью Flask встроенного сервера
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
