#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматического обновления Git репозитория с VK OAuth
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, cwd=None):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def main():
    print("=" * 60)
    print("🚀 Автоматическое обновление Git репозитория")
    print("=" * 60)
    print()
    
    # Шаг 1: Проверка что мы в правильной директории
    print("📂 Шаг 1: Проверка директории проекта...")
    
    project_path = input("Введите путь к проекту (или нажмите Enter для текущей директории): ").strip()
    
    if not project_path:
        project_path = os.getcwd()
    
    if not os.path.exists(project_path):
        print(f"❌ Директория не найдена: {project_path}")
        sys.exit(1)
    
    os.chdir(project_path)
    print(f"✅ Рабочая директория: {project_path}")
    print()
    
    # Шаг 2: Проверка что это Git репозиторий
    print("🔍 Шаг 2: Проверка Git репозитория...")
    
    success, stdout, stderr = run_command("git status")
    if not success:
        print(f"❌ Это не Git репозиторий или Git не установлен")
        print(f"Ошибка: {stderr}")
        sys.exit(1)
    
    print("✅ Git репозиторий обнаружен")
    print()
    
    # Шаг 3: Проверка текущей ветки
    print("🌿 Шаг 3: Проверка текущей ветки...")
    
    success, stdout, stderr = run_command("git branch --show-current")
    current_branch = stdout.strip()
    
    if current_branch:
        print(f"✅ Текущая ветка: {current_branch}")
    else:
        current_branch = "main"
        print(f"⚠️  Не удалось определить ветку, используем: {current_branch}")
    print()
    
    # Шаг 4: Проверка изменений
    print("📝 Шаг 4: Проверка файлов для добавления...")
    
    files_to_add = [
        "oauth_server.py",
        "handlers/"
    ]
    
    existing_files = []
    missing_files = []
    
    for file in files_to_add:
        if os.path.exists(file):
            existing_files.append(file)
            print(f"   ✅ {file}")
        else:
            missing_files.append(file)
            print(f"   ❌ {file} - не найден")
    
    if missing_files:
        print()
        print(f"⚠️  Внимание! Некоторые файлы не найдены:")
        for f in missing_files:
            print(f"   - {f}")
        
        choice = input("\nПродолжить с существующими файлами? (y/n): ").strip().lower()
        if choice != 'y':
            print("❌ Отменено пользователем")
            sys.exit(1)
    
    print()
    
    # Шаг 5: Git add
    print("➕ Шаг 5: Добавление файлов в Git (git add)...")
    
    for file in existing_files:
        print(f"   Добавляем: {file}")
        success, stdout, stderr = run_command(f"git add {file}")
        if not success:
            print(f"   ❌ Ошибка: {stderr}")
        else:
            print(f"   ✅ Добавлено")
    
    print()
    
    # Шаг 6: Проверка изменений
    print("🔍 Шаг 6: Проверка изменений (git status)...")
    
    success, stdout, stderr = run_command("git status --short")
    if stdout.strip():
        print("Изменения:")
        print(stdout)
    else:
        print("⚠️  Нет изменений для коммита")
        choice = input("\nВсё равно продолжить? (y/n): ").strip().lower()
        if choice != 'y':
            print("✅ Завершено")
            sys.exit(0)
    
    print()
    
    # Шаг 7: Git commit
    print("💾 Шаг 7: Создание коммита (git commit)...")
    
    commit_message = input("Введите сообщение коммита (Enter = 'Add VK OAuth support'): ").strip()
    if not commit_message:
        commit_message = "Add VK OAuth support"
    
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if success:
        print(f"✅ Коммит создан: {commit_message}")
        print(stdout)
    else:
        if "nothing to commit" in stderr:
            print("⚠️  Нет изменений для коммита")
        else:
            print(f"❌ Ошибка коммита: {stderr}")
            sys.exit(1)
    
    print()
    
    # Шаг 8: Git push
    print(f"🚀 Шаг 8: Отправка в удаленный репозиторий (git push origin {current_branch})...")
    
    choice = input(f"\nОтправить изменения в origin/{current_branch}? (y/n): ").strip().lower()
    if choice != 'y':
        print("⚠️  Push отменен. Изменения закоммичены локально.")
        print("   Выполните вручную: git push origin " + current_branch)
        sys.exit(0)
    
    print("Отправка...")
    success, stdout, stderr = run_command(f"git push origin {current_branch}")
    
    if success:
        print("✅ Изменения успешно отправлены!")
        print(stdout)
    else:
        print(f"❌ Ошибка при push:")
        print(stderr)
        print()
        print("Возможные причины:")
        print("1. Нет прав доступа к репозиторию")
        print("2. Нужна авторизация (настрой SSH ключ или токен)")
        print("3. Конфликты с удаленной веткой")
        print()
        print("Попробуйте выполнить вручную:")
        print(f"   git push origin {current_branch}")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("🎉 ВСЁ ГОТОВО!")
    print("=" * 60)
    print()
    print("Следующие шаги:")
    print("1. Зайди на Render.com Dashboard")
    print("2. Твой сервис должен автоматически задеплоиться")
    print("3. Проверь логи на наличие ошибок")
    print("4. Проверь: https://alexshylman-sudo-project.onrender.com/health")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
