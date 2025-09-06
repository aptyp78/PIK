#!/usr/bin/env python3
"""
Draw.io Quality Demo - Comprehensive Testing System
==================================================

Демонстрация полной системы тестирования качества Draw.io файлов
включающей backend, frontend, semantic, performance и security тесты.
"""

import os
import time
import subprocess
import webbrowser
from pathlib import Path

def print_banner():
    """Красивый баннер"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   🔍 Draw.io Quality Testing System                  ║
║                                                                      ║
║  Комплексная система для тестирования качества Draw.io файлов        ║
║  ✅ Backend Tests: XML структура, валидность, сжатие                 ║
║  🎨 Frontend Tests: визуализация, стили, читаемость                  ║
║  🧠 Semantic Tests: соответствие PIK методологии                     ║
║  ⚡ Performance Tests: скорость парсинга, размер файлов               ║
║  🔒 Security Tests: XSS уязвимости, вредоносный код                  ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

def check_requirements():
    """Проверка требований"""
    print("🔧 Проверка системных требований...")
    
    venv_path = Path(".venv/bin/python")
    if not venv_path.exists():
        print("❌ Виртуальное окружение не найдено")
        return False
    
    drawio_dir = Path("output/drawio")
    if not drawio_dir.exists() or not list(drawio_dir.glob("*.drawio")):
        print("❌ Draw.io файлы не найдены в output/drawio/")
        return False
    
    print("✅ Все требования выполнены")
    return True

def run_quality_tests():
    """Запуск тестирования качества"""
    print("\n🚀 Запуск комплексного тестирования качества...")
    
    try:
        # Запускаем тестер качества
        result = subprocess.run([
            ".venv/bin/python", "drawio_quality_tester.py"
        ], capture_output=True, text=True, timeout=120)
        
        print("✅ Тестирование завершено")
        
        # Показываем краткие результаты
        lines = result.stdout.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ["Файлов протестировано", "Средний балл", "Всего проблем", "Критических"]):
                print(f"   {line.strip()}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⏰ Тестирование прервано по таймауту")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def generate_reports():
    """Генерация отчетов"""
    print("\n📄 Генерация отчетов...")
    
    try:
        # HTML отчет
        subprocess.run([".venv/bin/python", "generate_quality_report.py"], 
                      capture_output=True, timeout=30)
        print("✅ HTML отчет создан: drawio_quality_report.html")
        
        # Проверяем JSON отчет
        if Path("drawio_quality_report.json").exists():
            print("✅ JSON отчет создан: drawio_quality_report.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка генерации отчетов: {e}")
        return False

def start_web_interface():
    """Запуск веб-интерфейса"""
    print("\n🌐 Запуск веб-интерфейса...")
    
    try:
        # Запускаем сервер в фоне
        process = subprocess.Popen([
            ".venv/bin/python", "quality_test_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем запуска сервера
        time.sleep(3)
        
        if process.poll() is None:  # Процесс еще работает
            print("✅ Веб-сервер запущен на http://localhost:8002")
            return process
        else:
            print("❌ Ошибка запуска веб-сервера")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return None

def demonstrate_features():
    """Демонстрация возможностей"""
    print("\n🎯 Демонстрация ключевых возможностей:")
    
    features = [
        "🔧 Backend тестирование:",
        "   • XML валидность и структура",
        "   • Проверка кодировки файлов", 
        "   • Тестирование сжатых данных",
        "   • Валидация атрибутов элементов",
        "",
        "🎨 Frontend тестирование:",
        "   • Анализ визуальных размеров",
        "   • Проверка стилей и CSS",
        "   • Тестирование читаемости текста",
        "   • Обнаружение перекрывающихся элементов",
        "   • Анализ цветовой схемы",
        "",
        "🧠 Семантическое тестирование:",
        "   • Соответствие PIK методологии",
        "   • Проверка терминологии",
        "   • Анализ логической группировки",
        "   • Поиск центральных элементов",
        "",
        "⚡ Performance тестирование:",
        "   • Измерение времени парсинга",
        "   • Анализ размера файлов",
        "   • Подсчет сложности элементов",
        "",
        "🔒 Security тестирование:",
        "   • Поиск XSS уязвимостей",
        "   • Обнаружение вредоносного кода",
        "   • Проверка безопасности атрибутов",
        "",
        "🛠️ Автоматическое исправление:",
        "   • Экранирование HTML сущностей",
        "   • Удаление подозрительного кода",
        "   • Создание резервных копий",
        "",
        "📊 Отчетность:",
        "   • Интерактивный веб-интерфейс",
        "   • Красивые HTML отчеты",
        "   • JSON данные для интеграции",
        "   • Детальная статистика"
    ]
    
    for feature in features:
        print(feature)
        time.sleep(0.1)

def show_sample_results():
    """Показать примеры результатов"""
    print("\n📈 Примеры результатов тестирования:")
    
    # Читаем JSON отчет если есть
    json_file = Path("drawio_quality_report.json")
    if json_file.exists():
        import json
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data:
                total_files = len(data)
                avg_score = sum(r['overall_score'] for r in data) / total_files
                total_issues = sum(len(r['issues']) for r in data)
                
                print(f"   📁 Файлов протестировано: {total_files}")
                print(f"   📊 Средний балл качества: {avg_score:.1f}/100")
                print(f"   ⚠️  Всего проблем найдено: {total_issues}")
                
                # Показываем пример проблемы
                if data[0]['issues']:
                    issue = data[0]['issues'][0]
                    print(f"\n   🔍 Пример найденной проблемы:")
                    print(f"      Тип: {issue['issue_type']}")
                    print(f"      Описание: {issue['description']}")
                    print(f"      Серьезность: {issue['severity']}")
                    if issue['auto_fixable']:
                        print(f"      ✨ Может быть исправлено автоматически")
                
        except Exception as e:
            print(f"   ❌ Ошибка чтения отчета: {e}")
    else:
        print("   ℹ️  Запустите тестирование для получения результатов")

def interactive_menu():
    """Интерактивное меню"""
    while True:
        print("\n" + "="*70)
        print("🎮 Интерактивное меню:")
        print("1. 🚀 Запустить полное тестирование")
        print("2. 📄 Генерировать HTML отчет")
        print("3. 🌐 Открыть веб-интерфейс")
        print("4. 🔧 Автоисправление проблем")
        print("5. 📊 Показать статистику")
        print("6. 🎯 Демонстрация возможностей")
        print("0. ❌ Выход")
        print("="*70)
        
        choice = input("Выберите действие (0-6): ").strip()
        
        if choice == "1":
            if run_quality_tests():
                generate_reports()
        elif choice == "2":
            generate_reports()
        elif choice == "3":
            process = start_web_interface()
            if process:
                input("Нажмите Enter для остановки сервера...")
                process.terminate()
        elif choice == "4":
            auto_fix_issues()
        elif choice == "5":
            show_sample_results()
        elif choice == "6":
            demonstrate_features()
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")

def auto_fix_issues():
    """Автоисправление проблем"""
    print("\n🛠️ Запуск автоматического исправления...")
    
    try:
        from drawio_quality_tester import DrawIOQualityTester
        
        tester = DrawIOQualityTester()
        drawio_dir = Path("output/drawio")
        
        total_fixes = 0
        files_fixed = 0
        
        for drawio_file in drawio_dir.glob("*.drawio"):
            if ".backup" not in str(drawio_file):
                result = tester.auto_fix_issues(str(drawio_file))
                if result["success"] and result["fixes_applied"] > 0:
                    total_fixes += result["fixes_applied"]
                    files_fixed += 1
                    print(f"   ✅ {drawio_file.name}: {result['fixes_applied']} исправлений")
        
        print(f"\n📊 Итого исправлено: {total_fixes} проблем в {files_fixed} файлах")
        
    except Exception as e:
        print(f"❌ Ошибка автоисправления: {e}")

def main():
    """Главная функция демонстрации"""
    print_banner()
    
    if not check_requirements():
        print("\n❌ Демонстрация прервана из-за отсутствующих требований")
        return
    
    print("\n🎯 Добро пожаловать в систему тестирования качества Draw.io файлов!")
    print("\nЭта система поможет вам:")
    print("• Проанализировать качество Draw.io файлов PIK методологии")
    print("• Выявить проблемы в backend и frontend аспектах")
    print("• Автоматически исправить многие проблемы")
    print("• Получить красивые отчеты и статистику")
    
    mode = input("\nВыберите режим работы:\n1. Быстрая демонстрация\n2. Интерактивный режим\nВаш выбор (1 или 2): ").strip()
    
    if mode == "1":
        # Быстрая демонстрация
        print("\n🚀 Запуск быстрой демонстрации...")
        
        demonstrate_features()
        
        if run_quality_tests():
            generate_reports()
            show_sample_results()
            
            print("\n✅ Демонстрация завершена!")
            print("📄 Отчеты созданы:")
            print("   • drawio_quality_report.html - красивый HTML отчет")
            print("   • drawio_quality_report.json - данные для интеграции")
            
            open_report = input("\nОткрыть HTML отчет в браузере? (y/n): ").strip().lower()
            if open_report == 'y':
                html_path = Path("drawio_quality_report.html").absolute()
                webbrowser.open(f"file://{html_path}")
    
    elif mode == "2":
        # Интерактивный режим
        interactive_menu()
    
    else:
        print("❌ Неверный выбор режима")

if __name__ == "__main__":
    main()
