#!/usr/bin/env python3
"""
Демонстрация улучшений OCR - финальная версия
    print("\n📋 Детали по категориям:")
    for cat, data in structure.get('subcategories', {}).items():
        if isinstance(data, dict) and data.get('items'):
            print(f"   {cat}: {len(data['items'])} элементов")
            for item in data['items'][:3]:
                print(f"     - {item}")
            if len(data['items']) > 3:
                print(f"     ... и еще {len(data['items']) - 3}")ort os
import re
from typing import Dict, List, Tuple

def demo_improvements_final():
    """Финальная демонстрация всех улучшений"""
    
    # Читаем реальный результат из нашей системы
    result_file = "OCR/PIK 5-0 - Ecosystem Forces Scan - ENG_result.md"
    
    if not os.path.exists(result_file):
        print("❌ Файл результата не найден")
        return
    
    with open(result_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем OCR текст
    ocr_pattern = r'## 🔍 OCR Страница \d+\n\n- (.+?)(?=\n##|\Z)'
    ocr_matches = re.findall(ocr_pattern, content, re.DOTALL)
    
    if not ocr_matches:
        # Попробуем другой паттерн
        ocr_pattern_alt = r'## 🔍 OCR Страница \d+\n\n(.+?)(?=\n##|\Z)'
        ocr_matches = re.findall(ocr_pattern_alt, content, re.DOTALL)
    
    if not ocr_matches:
        print("❌ OCR текст не найден в результате")
        print("📝 Доступные секции:")
        sections = re.findall(r'## (.+?)\n', content)
        for section in sections:
            print(f"   - {section}")
        return
    
    raw_ocr = " ".join(ocr_matches)
    
    print("🚀 ДЕМОНСТРАЦИЯ ФИНАЛЬНЫХ УЛУЧШЕНИЙ OCR")
    print("=" * 70)
    
    print("\n📝 Исходный OCR текст:")
    print("-" * 50)
    print(raw_ocr[:500] + "..." if len(raw_ocr) > 500 else raw_ocr)
    
    # Применяем наши улучшения
    from pik_ocr_enhanced import clean_ocr_text, extract_pik_structure, format_pik_output
    
    print("\n✅ После применения улучшений:")
    print("-" * 50)
    cleaned = clean_ocr_text(raw_ocr)
    print(cleaned[:500] + "..." if len(cleaned) > 500 else cleaned)
    
    print("\n🎯 Структурированный анализ:")
    print("-" * 50)
    structure = extract_pik_structure(cleaned)
    
    print(f"📊 Заголовок: {structure.get('title', 'Не найден')}")
    print(f"📊 Версия: {structure.get('version', 'Не найдена')}")
    print(f"📊 Основных категорий: {len(structure.get('main_categories', []))}")
    print(f"📊 Категории: {', '.join(structure.get('main_categories', []))}")
    
    total_subcats = 0
    subcategories = structure.get('subcategories', {})
    if isinstance(subcategories, dict):
        for data in subcategories.values():
            if isinstance(data, dict) and 'items' in data:
                total_subcats += len(data['items'])
    print(f"📊 Всего подкатегорий: {total_subcats}")
    
    print("\n📋 Детали по категориям:")
    for cat, data in structure.get('subcategories', {}).items():
        if data['items']:
            print(f"   {cat}: {len(data['items'])} элементов")
            for item in data['items'][:3]:
                print(f"     - {item}")
            if len(data['items']) > 3:
                print(f"     - ...и еще {len(data['items']) - 3}")
    
    print("\n📈 СРАВНЕНИЕ КАЧЕСТВА:")
    print("-" * 50)
    
    # Подсчет улучшений
    improvements = {
        "Исправлено TNEMNORIVNE → ENVIRONMENT": "ENVIRONMENT" in cleaned and "TNEMNORIVNE" not in cleaned,
        "Разделены слипшиеся слова": "of the" in cleaned and "ofthe" not in cleaned,
        "Извлечены основные категории": len(structure.get('main_categories', [])) > 0,
        "Найдены подкатегории": total_subcats > 0,
        "Определен тип документа": structure.get('title') is not None,
        "Извлечены метаданные": len(structure.get('metadata', {})) > 0
    }
    
    successful_improvements = sum(improvements.values())
    total_improvements = len(improvements)
    
    for desc, success in improvements.items():
        status = "✅" if success else "❌"
        print(f"{status} {desc}")
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {successful_improvements}/{total_improvements} улучшений")
    percentage = (successful_improvements / total_improvements) * 100
    print(f"📊 Успешность: {percentage:.1f}%")
    
    if percentage >= 80:
        print("🟢 ОТЛИЧНЫЙ РЕЗУЛЬТАТ!")
    elif percentage >= 60:
        print("🟡 ХОРОШИЙ РЕЗУЛЬТАТ!")
    elif percentage >= 40:
        print("🟠 СРЕДНИЙ РЕЗУЛЬТАТ")
    else:
        print("🔴 ТРЕБУЕТСЯ ДОРАБОТКА")
    
    print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("-" * 50)
    if percentage < 100:
        print("1. Расширить словарь PIK терминов")
        print("2. Улучшить алгоритмы разделения текста")
        print("3. Добавить предобработку изображений")
        print("4. Интегрировать ML-модели для лучшего распознавания")
    else:
        print("1. Интеграция в production систему")
        print("2. Обучение на большем количестве PIK документов")
        print("3. Добавление API для внешнего использования")


if __name__ == "__main__":
    demo_improvements_final()
