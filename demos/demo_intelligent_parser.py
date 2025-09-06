#!/usr/bin/env python3
"""
Демонстрация Intelligent PIK Parser
==================================

Демонстрационный скрипт для показа возможностей интеллектуального
парсера PIK методологии с генерацией draw.io диаграмм.

Функции демо:
1. Анализ PIK фреймворка с семантическим пониманием
2. Генерация интерактивной draw.io диаграммы
3. Создание подробного отчета
4. Выявление возможностей автоматизации
"""

import os
import sys
import time
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.append(str(Path(__file__).parent))

try:
    from intelligent_pik_parser import IntelligentPIKParser, PIKFrameworkType, ElementType
    import json
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Убедитесь, что все зависимости установлены: pip install -r requirements_intelligent.txt")
    sys.exit(1)

def demo_header():
    """Выводит заголовок демонстрации"""
    print("🧠 INTELLIGENT PIK PARSER - ДЕМОНСТРАЦИЯ")
    print("=" * 60)
    print("🎯 Цель: Интеллектуальный анализ PIK методологии")
    print("🔄 Трансформация: PIK Framework → Draw.io диаграмма")
    print("🤖 Автоматизация: Семантическое понимание + AI")
    print("=" * 60)
    print()

def find_test_images():
    """Находит доступные изображения для тестирования"""
    test_paths = [
        "OCR/attachment_image/original_attachment_image.png",
        "PIK_Source_Images/ecosystem_forces.png",
        "PIK_Source_Images/nfx_engines.png",
        "_Sources/Ontology PIK/PIK-5-Core-Kit/"
    ]
    
    available_images = []
    
    for path in test_paths:
        if os.path.exists(path):
            if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg')):
                available_images.append(path)
            elif os.path.isdir(path):
                # Ищем изображения в директории
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            available_images.append(os.path.join(root, file))
    
    return available_images

def analyze_image_with_details(parser, image_path):
    """Анализирует изображение с подробным выводом процесса"""
    print(f"📸 Анализируем: {os.path.basename(image_path)}")
    print(f"📁 Путь: {image_path}")
    
    start_time = time.time()
    
    try:
        # Этап 1: Парсинг
        print("🔍 Этап 1: Загрузка и предобработка изображения...")
        framework = parser.parse_pik_image(image_path)
        
        parsing_time = time.time() - start_time
        print(f"⏱️  Время парсинга: {parsing_time:.2f} секунд")
        
        # Этап 2: Анализ результатов
        print("\n📊 Этап 2: Результаты семантического анализа:")
        print(f"  🎯 Тип фреймворка: {framework.type.value}")
        print(f"  📝 Название: {framework.title}")
        print(f"  🔢 Элементов найдено: {len(framework.elements)}")
        print(f"  🔗 Связей найдено: {len(framework.relationships)}")
        print(f"  🎯 Общая уверенность: {framework.metadata['confidence_score']:.1%}")
        
        # Распределение элементов по типам
        element_types = {}
        for element in framework.elements:
            elem_type = element.type.value
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        print("\n📈 Распределение элементов:")
        for elem_type, count in element_types.items():
            print(f"  • {elem_type}: {count}")
        
        # Семантический анализ
        semantic = framework.semantic_analysis
        
        print(f"\n🧠 Семантическая оценка:")
        if 'framework_completeness' in semantic:
            completeness = semantic['framework_completeness']['score']
            print(f"  📋 Полнота фреймворка: {completeness:.1%}")
        
        if 'methodology_alignment' in semantic:
            alignment = semantic['methodology_alignment']['score']
            print(f"  🎯 Соответствие PIK: {alignment:.1%}")
        
        if 'quality_metrics' in semantic:
            quality = semantic['quality_metrics']['overall']
            print(f"  ⭐ Качество анализа: {quality:.1%}")
        
        # Ключевые инсайты
        if semantic.get('key_insights'):
            print(f"\n💡 Ключевые инсайты:")
            for insight in semantic['key_insights']:
                print(f"  • {insight}")
        
        # Возможности автоматизации
        if semantic.get('automation_opportunities'):
            print(f"\n🤖 Возможности автоматизации:")
            for opportunity in semantic['automation_opportunities']:
                print(f"  • {opportunity['description']} (Влияние: {opportunity['impact']})")
        
        return framework
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {str(e)}")
        return None

def save_and_show_results(parser, framework):
    """Сохраняет результаты и показывает созданные файлы"""
    if not framework:
        return
    
    print(f"\n💾 Этап 3: Сохранение результатов...")
    
    try:
        # Сохраняем результаты
        files = parser.save_analysis_results(framework)
        
        print(f"✅ Файлы успешно созданы:")
        for file_type, path in files.items():
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  📄 {file_type.upper()}: {path} ({size:,} байт)")
            else:
                print(f"  ❌ {file_type.upper()}: {path} (не создан)")
        
        # Показываем содержимое draw.io файла
        if 'drawio' in files and os.path.exists(files['drawio']):
            print(f"\n🎨 Превью Draw.io XML (первые 500 символов):")
            with open(files['drawio'], 'r', encoding='utf-8') as f:
                content = f.read()
                print("─" * 50)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("─" * 50)
        
        return files
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {str(e)}")
        return None

def show_methodology_insights(framework):
    """Показывает инсайты о методологии PIK"""
    print(f"\n🔬 Этап 4: Анализ соответствия PIK методологии")
    
    # Определяем место фреймворка в жизненном цикле PIK
    lifecycle_position = {
        PIKFrameworkType.ECOSYSTEM_FORCES: "1️⃣ Этап сканирования экосистемы",
        PIKFrameworkType.NFX_ENGINES: "2️⃣ Этап проектирования сетевых эффектов", 
        PIKFrameworkType.BUSINESS_MODEL: "3️⃣ Этап создания бизнес-модели",
        PIKFrameworkType.PLATFORM_EXPERIENCE: "4️⃣ Этап дизайна пользовательского опыта",
        PIKFrameworkType.VALUE_NETWORK: "5️⃣ Этап построения сети ценности"
    }
    
    position = lifecycle_position.get(framework.type, "❓ Неопределенная позиция")
    print(f"📍 Позиция в PIK жизненном цикле: {position}")
    
    # Рекомендации по развитию
    recommendations = {
        PIKFrameworkType.ECOSYSTEM_FORCES: [
            "Следующий шаг: Проектирование двигателей сетевых эффектов (NFX Engines)",
            "Фокус: Определите ключевые силы для усиления в сетевых эффектах"
        ],
        PIKFrameworkType.NFX_ENGINES: [
            "Следующий шаг: Разработка платформенной бизнес-модели",
            "Фокус: Монетизация выявленных сетевых эффектов"
        ],
        PIKFrameworkType.BUSINESS_MODEL: [
            "Следующий шаг: Дизайн пользовательского опыта платформы",
            "Фокус: Воплощение бизнес-модели в интерфейсах"
        ]
    }
    
    if framework.type in recommendations:
        print(f"\n🎯 Рекомендации по развитию:")
        for rec in recommendations[framework.type]:
            print(f"  • {rec}")

def create_automation_roadmap(framework):
    """Создает дорожную карту автоматизации"""
    print(f"\n🚀 Этап 5: Дорожная карта автоматизации PIK")
    
    automation_levels = [
        "📊 Уровень 1: Автоматическое извлечение элементов (ГОТОВО)",
        "🔗 Уровень 2: Автоматическая идентификация связей (ГОТОВО)", 
        "🧠 Уровень 3: Семантическое понимание методологии (ГОТОВО)",
        "🎨 Уровень 4: Генерация интерактивных диаграмм (ГОТОВО)",
        "🔄 Уровень 5: Автоматическая трансформация между фреймворками",
        "🤖 Уровень 6: ИИ-ассистент для PIK методологии",
        "📈 Уровень 7: Предиктивная аналитика экосистем"
    ]
    
    print("Прогресс автоматизации:")
    for level in automation_levels:
        print(f"  {level}")
    
    # Конкретные возможности для текущего фреймворка
    if framework.semantic_analysis.get('automation_opportunities'):
        print(f"\n🎯 Приоритетные возможности для данного фреймворка:")
        for opp in framework.semantic_analysis['automation_opportunities']:
            impact_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}
            complexity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            
            impact = impact_emoji.get(opp['impact'], "❓")
            complexity = complexity_emoji.get(opp['complexity'], "❓")
            
            print(f"  {impact} {complexity} {opp['description']}")

def interactive_demo():
    """Интерактивная демонстрация парсера"""
    demo_header()
    
    # Инициализируем парсер
    print("🚀 Инициализация Intelligent PIK Parser...")
    try:
        parser = IntelligentPIKParser()
        print("✅ Парсер успешно инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return
    
    # Находим доступные изображения
    print(f"\n🔍 Поиск доступных PIK диаграмм...")
    available_images = find_test_images()
    
    if not available_images:
        print("❌ Изображения PIK фреймворков не найдены")
        print("💡 Разместите .png/.jpg файлы в одной из папок:")
        print("   • OCR/attachment_image/")
        print("   • PIK_Source_Images/")
        print("   • _Sources/Ontology PIK/PIK-5-Core-Kit/")
        return
    
    print(f"✅ Найдено {len(available_images)} изображений:")
    for i, img in enumerate(available_images, 1):
        print(f"  {i}. {os.path.basename(img)}")
    
    # Выбираем первое доступное изображение для демо
    selected_image = available_images[0]
    print(f"\n🎯 Выбрано для демонстрации: {os.path.basename(selected_image)}")
    
    # Анализируем изображение
    framework = analyze_image_with_details(parser, selected_image)
    
    if framework:
        # Сохраняем результаты
        files = save_and_show_results(parser, framework)
        
        # Показываем методологические инсайты
        show_methodology_insights(framework)
        
        # Создаем дорожную карту автоматизации
        create_automation_roadmap(framework)
        
        print(f"\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print(f"📊 Проанализирован фреймворк: {framework.type.value}")
        print(f"📁 Результаты сохранены в папке: output/")
        
        if files and 'drawio' in files:
            print(f"🎨 Draw.io диаграмма: {files['drawio']}")
            print("💡 Откройте файл .drawio в app.diagrams.net для просмотра")
    
    else:
        print(f"\n❌ Демонстрация не удалась")
        print("🔧 Проверьте настройки и попробуйте снова")

def main():
    """Главная функция демонстрации"""
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
