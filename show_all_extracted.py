#!/usr/bin/env python3
"""
Визуализатор извлеченных иконок и текста из PIK диаграмм.
Показывает ВСЕ найденные элементы из существующих результатов анализа.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def load_comprehensive_results():
    """Загружает результаты комплексного анализа"""
    
    results = []
    ocr_dir = Path("OCR")
    
    print("🔍 Поиск результатов комплексного анализа...")
    
    # Ищем все JSON файлы с результатами
    json_files = list(ocr_dir.rglob("comprehensive_analysis_*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source_file'] = str(json_file)
                results.append(data)
                print(f"   ✅ Загружен: {json_file.name}")
        except Exception as e:
            print(f"   ❌ Ошибка загрузки {json_file}: {e}")
    
    return results

def extract_all_text_and_icons(results):
    """Извлекает ВСЕ найденные иконки и текст из результатов"""
    
    all_elements = []
    
    for result in results:
        source_image = result.get('source_image', 'Unknown')
        
        # Обрабатываем регионы
        regions = result.get('regions', {})
        
        for region_name, region_data in regions.items():
            if region_data.get('text'):
                element = {
                    'source_image': source_image,
                    'region': region_name,
                    'text': region_data['text'],
                    'confidence': region_data.get('confidence', 0),
                    'elements': region_data.get('elements', []),
                    'enhancement_variant': region_data.get('enhancement_variant', 0),
                    'ocr_config': region_data.get('ocr_config', ''),
                    'type': 'text_region'
                }
                all_elements.append(element)
        
        # Обрабатываем иконки если есть
        icons = result.get('detected_icons', [])
        for icon in icons:
            element = {
                'source_image': source_image,
                'region': icon.get('location', 'unknown'),
                'text': f"ICON: {icon.get('description', 'Unknown icon')}",
                'confidence': icon.get('confidence', 0),
                'elements': [icon.get('description', 'icon')],
                'type': 'icon'
            }
            all_elements.append(element)
        
        # Обрабатываем PIK структуру
        pik_structure = result.get('pik_structure', {})
        categories = pik_structure.get('categories', {})
        
        for category_name, category_data in categories.items():
            if category_data.get('elements'):
                element = {
                    'source_image': source_image,
                    'region': category_data.get('region', category_name),
                    'text': f"PIK CATEGORY: {category_name} - {', '.join(category_data['elements'][:10])}",
                    'confidence': category_data.get('confidence', 0),
                    'elements': category_data['elements'],
                    'type': 'pik_category'
                }
                all_elements.append(element)
    
    return all_elements

def create_comprehensive_visualization(elements, output_file="all_extracted_elements.md"):
    """Создает полную визуализацию всех найденных элементов"""
    
    print(f"📊 Создаем полную визуализацию...")
    
    report = [
        "# 🎯 ВСЕ ИЗВЛЕЧЕННЫЕ ИКОНКИ И ТЕКСТ\n\n",
        f"**Дата создания:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Всего найдено элементов:** {len(elements)}\n\n"
    ]
    
    if not elements:
        report.append("❌ **Элементы не найдены**\n")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(report))
        return output_file
    
    # Группируем по изображениям
    by_image = {}
    for element in elements:
        img = element['source_image']
        if img not in by_image:
            by_image[img] = []
        by_image[img].append(element)
    
    # Группируем по типам
    by_type = {}
    for element in elements:
        elem_type = element['type']
        if elem_type not in by_type:
            by_type[elem_type] = []
        by_type[elem_type].append(element)
    
    # Общая статистика
    report.append("## 📈 Общая статистика\n\n")
    report.append(f"- **Обработано изображений:** {len(by_image)}\n")
    
    for elem_type, type_elements in by_type.items():
        report.append(f"- **{elem_type.replace('_', ' ').title()}:** {len(type_elements)} элементов\n")
    
    if elements:
        confidences = [e['confidence'] for e in elements if e['confidence'] > 0]
        if confidences:
            report.append(f"- **Средняя уверенность:** {sum(confidences)/len(confidences):.1f}%\n")
            report.append(f"- **Максимальная уверенность:** {max(confidences):.1f}%\n")
    
    report.append("\n")
    
    # Топ находки
    top_elements = sorted([e for e in elements if e['confidence'] > 0], 
                         key=lambda x: x['confidence'], reverse=True)[:20]
    
    report.append("## 🏆 Топ-20 лучших находок\n\n")
    
    for i, element in enumerate(top_elements, 1):
        text_preview = element['text'][:100] + ('...' if len(element['text']) > 100 else '')
        report.append(f"**{i:2d}.** `{element['region']}` ({element['confidence']:.1f}%)\n")
        report.append(f"```\n{text_preview}\n```\n\n")
    
    # Детальный анализ по изображениям
    for img_path, img_elements in by_image.items():
        img_name = Path(img_path).name
        report.append(f"## 🖼️ {img_name}\n\n")
        report.append(f"**Найдено элементов:** {len(img_elements)}\n\n")
        
        # Сортируем по уверенности
        sorted_elements = sorted(img_elements, key=lambda x: x['confidence'], reverse=True)
        
        # Показываем все регионы
        for element in sorted_elements:
            report.append(f"### 📍 {element['region']}\n")
            report.append(f"- **Тип:** {element['type']}\n")
            report.append(f"- **Уверенность:** {element['confidence']:.1f}%\n")
            if element.get('ocr_config'):
                report.append(f"- **OCR конфиг:** {element['ocr_config']}\n")
            if element.get('enhancement_variant') is not None:
                report.append(f"- **Вариант обработки:** {element['enhancement_variant']}\n")
            
            report.append(f"\n**Извлеченный текст:**\n")
            report.append(f"```\n{element['text']}\n```\n")
            
            # Показываем элементы если есть
            if element.get('elements') and len(element['elements']) > 1:
                report.append(f"\n**Детальные элементы:**\n")
                elements_str = ", ".join([f"`{elem}`" for elem in element['elements'][:20]])
                if len(element['elements']) > 20:
                    elements_str += f" ... (всего {len(element['elements'])})"
                report.append(f"{elements_str}\n")
            
            report.append("\n---\n\n")
    
    # Анализ по типам элементов
    report.append("## 📊 Анализ по типам элементов\n\n")
    
    for elem_type, type_elements in by_type.items():
        report.append(f"### {elem_type.replace('_', ' ').title()} ({len(type_elements)} элементов)\n\n")
        
        # Сортируем по уверенности
        sorted_type_elements = sorted(type_elements, key=lambda x: x['confidence'], reverse=True)
        
        for element in sorted_type_elements[:10]:  # Топ-10 для каждого типа
            text_preview = element['text'][:80] + ('...' if len(element['text']) > 80 else '')
            report.append(f"- **{element['region']}** ({element['confidence']:.1f}%): `{text_preview}`\n")
        
        if len(type_elements) > 10:
            report.append(f"- ... и еще {len(type_elements) - 10} элементов\n")
        
        report.append("\n")
    
    # Карта всех найденных текстов
    report.append("## 🗺️ Полная карта найденных текстов\n\n")
    report.append("| Изображение | Регион | Тип | Уверенность | Текст |\n")
    report.append("|-------------|--------|-----|-------------|-------|\n")
    
    for element in sorted(elements, key=lambda x: x['confidence'], reverse=True):
        img_name = Path(element['source_image']).name
        text_cell = element['text'].replace('\n', ' ')[:50] + ('...' if len(element['text']) > 50 else '')
        text_cell = text_cell.replace('|', '&#124;')  # Экранируем pipe для markdown
        
        report.append(f"| {img_name} | {element['region']} | {element['type']} | {element['confidence']:.1f}% | `{text_cell}` |\n")
    
    # Сохраняем отчет
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    return output_file

def main():
    """Основная функция"""
    
    print("🚀 Анализ всех найденных иконок и текста")
    print("=" * 50)
    
    # Загружаем результаты
    results = load_comprehensive_results()
    
    if not results:
        print("❌ Не найдены результаты комплексного анализа")
        print("Убедитесь, что запускали comprehensive_pik_parser.py")
        return
    
    print(f"✅ Загружено результатов: {len(results)}")
    
    # Извлекаем все элементы
    all_elements = extract_all_text_and_icons(results)
    
    print(f"📊 Всего найдено элементов: {len(all_elements)}")
    
    if all_elements:
        # Создаем полную визуализацию
        output_file = "OCR/all_extracted_elements.md"
        report_file = create_comprehensive_visualization(all_elements, output_file)
        
        print(f"\n🎉 Полная визуализация создана!")
        print(f"📄 Отчет: {report_file}")
        
        # Краткая статистика
        by_type = {}
        for element in all_elements:
            elem_type = element['type']
            if elem_type not in by_type:
                by_type[elem_type] = 0
            by_type[elem_type] += 1
        
        print(f"\n📈 Краткая статистика:")
        for elem_type, count in by_type.items():
            print(f"   {elem_type.replace('_', ' ').title()}: {count}")
        
        # Показываем топ-5
        top_5 = sorted([e for e in all_elements if e['confidence'] > 0], 
                      key=lambda x: x['confidence'], reverse=True)[:5]
        
        print(f"\n🏆 Топ-5 лучших находок:")
        for i, element in enumerate(top_5, 1):
            text_preview = element['text'][:60] + ('...' if len(element['text']) > 60 else '')
            print(f"   {i}. {element['region']}: '{text_preview}' ({element['confidence']:.1f}%)")
    
    else:
        print("❌ Элементы не найдены")

if __name__ == "__main__":
    main()
