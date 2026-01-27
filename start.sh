#!/bin/bash
# Скрипт запуска бота и webhook сервера

echo "🚀 Запуск VK Webhook сервера..."
python vk_webhook.py &

echo "⏳ Ожидание 3 секунды..."
sleep 3

echo "🤖 Запуск Telegram бота..."
python main.py
