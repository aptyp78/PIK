#!/usr/bin/env python3
"""
Детальный экстрактор ВСЕХ иконок и текста из PIK диаграмм.
Создает микро-сетку анализа и показывает ВСЕ найденные элементы.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import os
from pathlib import Path
import json
from datetime import datetime

def extract_all_elements_detailed(image_path: str, output_dir: str = "detailed_extraction"):
    """Детальное извлечение ВСЕХ элементов с иконками и текстом"""
    
    print(f"🚀 Запускаем детальный анализ: {Path(image_path).name}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Загружаем изображение
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Не удалось загрузить изображение: {image_path}")
        return []
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    
    print(f"🖼️ Размер изображения: {width}x{height}")
    
    # Создаем детальную сетку регионов (15x15 = 225 микрорегионов)
    regions = []
    grid_size = 15
    
    print(f"📊 Создаем сетку {grid_size}x{grid_size} = {grid_size*grid_size} микрорегионов...")
    
    for i in range(grid_size):
        for j in range(grid_size):
            x1 = int(j * width / grid_size)
            y1 = int(i * height / grid_size)
            x2 = int((j + 1) * width / grid_size)
            y2 = int((i + 1) * height / grid_size)
            
            # Минимальный размер региона
            if (x2 - x1) < 15 or (y2 - y1) < 15:
                continue
                
            regions.append({
                'name': f'micro_{i:02d}_{j:02d}',
                'coords': (x1, y1, x2, y2),
                'type': 'micro_region',
                'grid_pos': (i, j)
            })
    
    # Добавляем специальные важные регионы
    special_regions = [
        {'name': 'full_image', 'coords': (0, 0, width, height), 'type': 'full_scan'},
        {'name': 'center_focus', 'coords': (int(width*0.3), int(height*0.3), int(width*0.7), int(height*0.7)), 'type': 'center'},
        {'name': 'top_left_quarter', 'coords': (0, 0, int(width*0.5), int(height*0.5)), 'type': 'quadrant'},
        {'name': 'top_right_quarter', 'coords': (int(width*0.5), 0, width, int(height*0.5)), 'type': 'quadrant'},
        {'name': 'bottom_left_quarter', 'coords': (0, int(height*0.5), int(width*0.5), height), 'type': 'quadrant'},
        {'name': 'bottom_right_quarter', 'coords': (int(width*0.5), int(height*0.5), width, height), 'type': 'quadrant'},
        # Углы для иконок
        {'name': 'corner_tl', 'coords': (0, 0, int(width*0.15), int(height*0.15)), 'type': 'icon_corner'},
        {'name': 'corner_tr', 'coords': (int(width*0.85), 0, width, int(height*0.15)), 'type': 'icon_corner'},
        {'name': 'corner_bl', 'coords': (0, int(height*0.85), int(width*0.15), height), 'type': 'icon_corner'},
        {'name': 'corner_br', 'coords': (int(width*0.85), int(height*0.85), width, height), 'type': 'icon_corner'},
        # Центральные полосы
        {'name': 'horizontal_center', 'coords': (0, int(height*0.4), width, int(height*0.6)), 'type': 'center_band'},
        {'name': 'vertical_center', 'coords': (int(width*0.4), 0, int(width*0.6), height), 'type': 'center_band'},
    ]
    
    regions.extend(special_regions)
    
    print(f"🔍 Всего регионов для анализа: {len(regions)}")
    
    extracted_elements = []
    regions_processed = 0
    
    for region in regions:
        regions_processed += 1
        if regions_processed % 50 == 0:
            print(f"   📈 Обработано регионов: {regions_processed}/{len(regions)}")
            
        x1, y1, x2, y2 = region['coords']
        
        try:
            # Вырезаем регион
            roi = gray[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            # Множественные варианты обработки для каждого региона
            processing_variants = []
            
            # 1. Оригинальное изображение
            processing_variants.append(('original', roi))
            
            # 2. Увеличение контраста
            enhanced = cv2.equalizeHist(roi)
            processing_variants.append(('enhanced', enhanced))
            
            # 3. Адаптивная бинаризация
            binary = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            processing_variants.append(('binary', binary))
            
            # 4. Инверсия для темного текста на светлом фоне
            inverted = cv2.bitwise_not(roi)
            processing_variants.append(('inverted', inverted))
            
            # 5. Морфологическая обработка для соединения разорванных символов
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            processing_variants.append(('morphed', morph))
            
            # 6. Размытие по Гауссу для сглаживания
            blurred = cv2.GaussianBlur(roi, (3, 3), 0)
            processing_variants.append(('blurred', blurred))
            
            best_text = ""
            best_confidence = 0
            best_variant = ""
            best_config = ""
            
            # Тестируем каждый вариант обработки
            for variant_name, processed_roi in processing_variants:
                try:
                    # Конвертируем в PIL для tesseract
                    pil_img = Image.fromarray(processed_roi)
                    
                    # Увеличиваем изображение для лучшего распознавания
                    scale_factor = 4
                    new_width = max(int(pil_img.width * scale_factor), 40)
                    new_height = max(int(pil_img.height * scale_factor), 40)
                    pil_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # OCR с различными настройками
                    configs = [
                        '--psm 8 --oem 3',   # Одно слово
                        '--psm 7 --oem 3',   # Одна строка  
                        '--psm 6 --oem 3',   # Блок текста
                        '--psm 13 --oem 3',  # Сырая строка
                        '--psm 10 --oem 3',  # Отдельный символ
                        '--psm 9 --oem 3',   # Отдельное слово в круге
                    ]
                    
                    for config in configs:
                        try:
                            # Получаем данные с уверенностью
                            data = pytesseract.image_to_data(pil_img, config=config, lang='eng+rus', output_type=pytesseract.Output.DICT)
                            
                            # Собираем текст с достаточной уверенностью
                            words = []
                            confidences = []
                            
                            for i in range(len(data['text'])):
                                if int(data['conf'][i]) > 20:  # Снижаем порог для большего охвата
                                    text = data['text'][i].strip()
                                    if text and len(text) > 0:  # Принимаем даже отдельные символы
                                        words.append(text)
                                        confidences.append(int(data['conf'][i]))
                            
                            if words:
                                current_text = ' '.join(words)
                                avg_confidence = sum(confidences) / len(confidences)
                                
                                # Выбираем лучший результат
                                if (avg_confidence > best_confidence) or (avg_confidence == best_confidence and len(current_text) > len(best_text)):
                                    best_text = current_text
                                    best_confidence = avg_confidence
                                    best_variant = variant_name
                                    best_config = config
                                    
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
            
            # Сохраняем результат если что-то найдено
            if best_text and len(best_text.strip()) > 0:
                # Сохраняем изображение региона
                region_img_path = f"{output_dir}/{region['name']}_region.png"
                cv2.imwrite(region_img_path, roi)
                
                element = {
                    'region': region['name'],
                    'type': region['type'],
                    'coordinates': (x1, y1, x2, y2),
                    'coordinates_str': f"({x1},{y1}) -> ({x2},{y2})",
                    'text': best_text.strip(),
                    'confidence': round(best_confidence, 1),
                    'image_path': region_img_path,
                    'size': f"{x2-x1}x{y2-y1}",
                    'processing_variant': best_variant,
                    'ocr_config': best_config,
                    'grid_position': region.get('grid_pos', None)
                }
                
                extracted_elements.append(element)
                
                # Показываем найденные элементы в реальном времени
                if len(best_text.strip()) > 1:  # Показываем только значимые находки
                    print(f"✅ {region['name']}: '{best_text[:40]}...' ({best_confidence:.1f}%)")
        
        except Exception as e:
            continue
    
    print(f"\n📊 Анализ завершен!")
    print(f"   🎯 Найдено элементов: {len(extracted_elements)}")
    
    return extracted_elements

def create_detailed_report(elements, output_file="detailed_extraction_report.md"):
    """Создает детальный отчет со всеми найденными элементами"""
    
    print(f"📄 Создаем детальный отчет...")
    
    report = [
        "# 🔍 Детальный анализ извлечения ВСЕХ элементов\n\n",
        f"**Всего найдено элементов:** {len(elements)}\n",
        f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    ]
    
    if not elements:
        report.append("❌ **Элементы не найдены**\n")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(report))
        return output_file
    
    # Группируем по типам
    by_type = {}
    for element in elements:
        elem_type = element['type']
        if elem_type not in by_type:
            by_type[elem_type] = []
        by_type[elem_type].append(element)
    
    # Статистика
    confidences = [e['confidence'] for e in elements]
    report.append(f"## 📈 Общая статистика\n\n")
    report.append(f"- **Средняя уверенность:** {np.mean(confidences):.1f}%\n")
    report.append(f"- **Максимальная уверенность:** {max(confidences):.1f}%\n")
    report.append(f"- **Минимальная уверенность:** {min(confidences):.1f}%\n")
    report.append(f"- **Элементов с высокой уверенностью (>80%):** {len([c for c in confidences if c > 80])}\n")
    report.append(f"- **Элементов со средней уверенностью (50-80%):** {len([c for c in confidences if 50 <= c <= 80])}\n")
    report.append(f"- **Элементов с низкой уверенностью (<50%):** {len([c for c in confidences if c < 50])}\n\n")
    
    # Топ находки
    top_elements = sorted(elements, key=lambda x: x['confidence'], reverse=True)[:15]
    report.append(f"## 🏆 Топ-15 лучших находок\n\n")
    
    for i, element in enumerate(top_elements, 1):
        text_preview = element['text'][:80] + ('...' if len(element['text']) > 80 else '')
        report.append(f"{i:2d}. **{element['region']}** ({element['confidence']}%): `{text_preview}`\n")
        report.append(f"    📍 {element['coordinates_str']} | 📏 {element['size']} | 🔧 {element['processing_variant']}\n\n")
    
    # Отчет по типам регионов
    for elem_type, type_elements in by_type.items():
        report.append(f"## 📊 {elem_type.replace('_', ' ').title()} ({len(type_elements)} элементов)\n\n")
        
        # Сортируем по уверенности
        sorted_elements = sorted(type_elements, key=lambda x: x['confidence'], reverse=True)
        
        for element in sorted_elements[:20]:  # Показываем топ-20 для каждого типа
            report.append(f"### {element['region']}\n")
            report.append(f"- **Координаты:** {element['coordinates_str']}\n")
            report.append(f"- **Размер:** {element['size']}\n")
            report.append(f"- **Уверенность:** {element['confidence']}%\n")
            report.append(f"- **Метод обработки:** {element['processing_variant']}\n")
            report.append(f"- **OCR конфиг:** {element['ocr_config']}\n")
            report.append(f"- **Текст:** `{element['text']}`\n")
            
            # Добавляем изображение если файл существует
            if os.path.exists(element['image_path']):
                report.append(f"- **Изображение:** ![{element['region']}]({element['image_path']})\n")
            
            report.append("\n")
    
    # Карта находок
    report.append(f"## 🗺️ Карта находок по координатам\n\n")
    report.append("| Регион | Координаты | Размер | Уверенность | Текст |\n")
    report.append("|--------|------------|--------|-------------|-------|\n")
    
    for element in sorted(elements, key=lambda x: (x['coordinates'][1], x['coordinates'][0])):  # Сортировка по Y, потом X
        text_cell = element['text'][:30] + ('...' if len(element['text']) > 30 else '')
        report.append(f"| {element['region']} | {element['coordinates_str']} | {element['size']} | {element['confidence']}% | `{text_cell}` |\n")
    
    # Сохраняем отчет
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(report))
    
    print(f"   ✅ Отчет сохранен: {output_file}")
    return output_file

def save_elements_json(elements, output_file="detailed_extraction_data.json"):
    """Сохраняет все элементы в JSON формате для дальнейшего анализа"""
    
    json_data = {
        'extraction_timestamp': datetime.now().isoformat(),
        'total_elements': len(elements),
        'elements': elements
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"📊 JSON данные сохранены: {output_file}")
    return output_file

def main():
    """Основная функция"""
    
    # Ищем доступные изображения
    ocr_dirs = list(Path("OCR").glob("*/images/")) if Path("OCR").exists() else []
    
    if not ocr_dirs:
        print("❌ Не найдены OCR директории с изображениями")
        return
    
    # Находим последнюю обработанную директорию
    latest_dir = max(ocr_dirs, key=lambda x: x.stat().st_mtime)
    image_files = list(latest_dir.glob("*.png"))
    
    if not image_files:
        print(f"❌ Не найдены PNG файлы в {latest_dir}")
        return
    
    # Берем первое (обычно full_page_1.png)
    image_path = str(image_files[0])
    output_dir = "OCR/detailed_analysis"
    
    print(f"🎯 Анализируем: {image_path}")
    
    # Создаем директорию для результатов
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Извлекаем ВСЕ элементы
        elements = extract_all_elements_detailed(image_path, output_dir)
        
        if elements:
            # Создаем детальный отчет
            report_file = create_detailed_report(elements, f"{output_dir}/detailed_extraction_report.md")
            
            # Сохраняем JSON данные
            json_file = save_elements_json(elements, f"{output_dir}/detailed_extraction_data.json")
            
            print(f"\n🎉 Детальный анализ завершен!")
            print(f"   📊 Найдено элементов: {len(elements)}")
            print(f"   📄 Отчет: {report_file}")
            print(f"   📋 JSON данные: {json_file}")
            print(f"   🖼️ Изображения регионов: {output_dir}/*.png")
            
            # Показываем краткую статистику
            confidences = [e['confidence'] for e in elements]
            print(f"\n📈 Краткая статистика:")
            print(f"   🎯 Средняя уверенность: {np.mean(confidences):.1f}%")
            print(f"   🏆 Максимальная уверенность: {max(confidences):.1f}%")
            print(f"   📊 Элементов с высокой уверенностью (>80%): {len([c for c in confidences if c > 80])}")
            
            # Показываем топ-5 находок
            top_5 = sorted(elements, key=lambda x: x['confidence'], reverse=True)[:5]
            print(f"\n🏆 Топ-5 лучших находок:")
            for i, element in enumerate(top_5, 1):
                text_preview = element['text'][:50] + ('...' if len(element['text']) > 50 else '')
                print(f"   {i}. {element['region']}: '{text_preview}' ({element['confidence']}%)")
        
        else:
            print("❌ Не удалось извлечь элементы")
            
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
