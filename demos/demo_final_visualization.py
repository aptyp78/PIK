#!/usr/bin/env python3
"""
PIK Intelligent Parser - Финальная Демонстрация
================================================

Демонстрация полной системы визуального анализа PIK фреймворков.
"""

import os
import sys
import json
import time
import webbrowser
from pathlib import Path

def print_header():
    """Печатает заголовок демонстрации"""
    print("=" * 80)
    print("🧠 PIK INTELLIGENT PARSER - ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ")
    print("=" * 80)
    print()

def print_stats():
    """Печатает статистику анализа"""
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("❌ Результаты анализа не найдены!")
        print("📋 Сначала запустите: python batch_pik_analysis.py")
        return False
    
    # Загружаем сводку
    summary_file = output_dir / "batch_analysis" / "methodology_summary.json"
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        print("📊 РЕЗУЛЬТАТЫ СЕМАНТИЧЕСКОГО АНАЛИЗА:")
        print("-" * 50)
        print(f"🎯 Проанализировано фреймворков: {summary.get('total_frameworks', 0)}")
        print(f"🔍 Извлечено элементов: {summary.get('total_elements', 0):,}")
        print(f"🔗 Обнаружено связей: {summary.get('total_relationships', 0):,}")
        print(f"🎲 Средняя уверенность: {summary.get('avg_confidence', 0)*100:.1f}%")
        print(f"📈 Покрытие PIK жизненного цикла: {summary.get('coverage_analysis', {}).get('lifecycle_coverage', 0)*100:.0f}%")
        print()
        
        # Статистика по типам
        print("🎨 АНАЛИЗ ПО ТИПАМ ФРЕЙМВОРКОВ:")
        print("-" * 50)
        for fw_type, data in summary.get('framework_types', {}).items():
            print(f"📋 {fw_type.replace('_', ' ').title()}: {data.get('elements', 0)} элементов, {data.get('relationships', 0)} связей")
        print()
        
        return True
    
    return False

def check_server_status():
    """Проверяет статус сервера"""
    try:
        import requests
        response = requests.get("http://localhost:8001/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_visualization_server():
    """Запускает сервер визуализации"""
    print("🚀 ЗАПУСК СИСТЕМЫ ВИЗУАЛИЗАЦИИ:")
    print("-" * 50)
    
    if check_server_status():
        print("✅ Сервер уже запущен на порту 8001")
        return True
    
    print("🔧 Запускаем веб-сервер...")
    
    # Создаем скрипт запуска
    import subprocess
    import threading
    
    def run_server():
        venv_python = Path(".venv/bin/python")
        if venv_python.exists():
            subprocess.run([str(venv_python), "pik_visualization_server.py"])
        else:
            subprocess.run(["python", "pik_visualization_server.py"])
    
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Ждем запуска сервера
    print("⏳ Ожидание запуска сервера...")
    for i in range(10):
        time.sleep(1)
        if check_server_status():
            print("✅ Сервер успешно запущен!")
            return True
        print(f"   Попытка {i+1}/10...")
    
    print("❌ Не удалось запустить сервер автоматически")
    print("📋 Запустите вручную: python pik_visualization_server.py")
    return False

def open_web_interface():
    """Открывает веб-интерфейс"""
    print("🌐 ОТКРЫТИЕ ВЕБ-ИНТЕРФЕЙСА:")
    print("-" * 50)
    
    url = "http://localhost:8001"
    print(f"🔗 URL: {url}")
    
    try:
        webbrowser.open(url)
        print("✅ Веб-интерфейс открыт в браузере")
        return True
    except Exception as e:
        print(f"❌ Ошибка открытия браузера: {e}")
        print(f"🔗 Откройте вручную: {url}")
        return False

def show_features():
    """Показывает возможности системы"""
    print("🎯 ВОЗМОЖНОСТИ СИСТЕМЫ:")
    print("-" * 50)
    
    features = [
        "📊 Интерактивный дашборд с реальными данными анализа",
        "🎯 Детальный просмотр каждого проанализированного фреймворка",
        "📈 Сетевая визуализация связей между элементами экосистемы",
        "💡 Автоматические инсайты и рекомендации по результатам",
        "🎨 Скачивание Draw.io диаграмм для дальнейшего редактирования",
        "📄 Экспорт JSON данных для интеграции с другими системами",
        "🔍 Семантический поиск и фильтрация элементов",
        "📈 Аналитика покрытия PIK методологии"
    ]
    
    for feature in features:
        print(f"  {feature}")
    print()

def show_navigation_guide():
    """Показывает руководство по навигации"""
    print("🧭 НАВИГАЦИЯ ПО ИНТЕРФЕЙСУ:")
    print("-" * 50)
    
    guide = [
        "1️⃣ Вкладка 'Обзор' - общая статистика и графики",
        "2️⃣ Вкладка 'Фреймворки' - карточки всех проанализированных фреймворков",
        "3️⃣ Вкладка 'Анализ' - интерактивная сетевая визуализация",
        "4️⃣ Вкладка 'Инсайты' - ключевые находки и рекомендации",
        "🎨 Кнопка 'Draw.io' - скачать диаграмму для редактирования",
        "📄 Кнопка 'JSON' - скачать детальные данные анализа",
        "📊 Кнопка 'Анализ' - просмотр детальной информации"
    ]
    
    for item in guide:
        print(f"  {item}")
    print()

def main():
    """Основная функция демонстрации"""
    print_header()
    
    # Проверяем результаты анализа
    if not print_stats():
        return
    
    # Показываем возможности
    show_features()
    
    # Запускаем сервер
    if start_visualization_server():
        time.sleep(2)  # Даем серверу время полностью запуститься
        
        # Открываем веб-интерфейс
        open_web_interface()
        
        # Показываем руководство
        show_navigation_guide()
        
        print("🎉 ДЕМОНСТРАЦИЯ ГОТОВА!")
        print("-" * 50)
        print("🌐 Веб-интерфейс открыт в браузере")
        print("🔍 Исследуйте результаты семантического анализа PIK фреймворков")
        print("⏹️  Для остановки сервера нажмите Ctrl+C в терминале")
        print()
        print("=" * 80)
        
        # Оставляем сервер работающим
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Демонстрация завершена")
    
    else:
        print("❌ Не удалось запустить демонстрацию")
        print("📋 Попробуйте запустить сервер вручную:")
        print("   python pik_visualization_server.py")

if __name__ == "__main__":
    main()
