#!/usr/bin/env python3
"""
Интегрированная система OCR с комплексным анализом PIK диаграмм.
Включает базовый OCR + комплексный региональный анализ для максимального извлечения данных.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import traceback

# OCR и обработка изображений
from PIL import Image
import pdfplumber
import pypdfium2 as pdfium
import pytesseract

# Импорт комплексного парсера если доступен
try:
    from comprehensive_pik_parser import PIKDiagramParser
    COMPREHENSIVE_PARSER_AVAILABLE = True
except ImportError:
    COMPREHENSIVE_PARSER_AVAILABLE = False
    print("⚠️  Комплексный PIK парсер недоступен - используется базовый OCR")

def clean_ocr_text(text: str) -> str:
    """Очистка и нормализация OCR текста с учетом PIK терминологии."""
    if not text:
        return ""
    
    # PIK-специфичные исправления
    pik_corrections = {
        'Ecosystern': 'Ecosystem',
        'Platforrm': 'Platform',
        'Stakeholdern': 'Stakeholder',
        'Custormer': 'Customer',
        'Partnern': 'Partner',
        'Suppliern': 'Supplier',
        'Developern': 'Developer',
        'Architecturn': 'Architecture',
        'Strategyn': 'Strategy',
        'Businessn': 'Business',
        'Processr': 'Process',
        'Servicer': 'Service',
        'Productr': 'Product',
        'Marketr': 'Market',
        'Valuer': 'Value',
        'Netvork': 'Network',
        'Netv\\/ork': 'Network',
        'Platforrm': 'Platform',
        'Busmess': 'Business',
        'Strateglc': 'Strategic'
    }
    
    # Базовая очистка
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-.,;:()!?"\'\n]', ' ', text)
    
    # Применяем PIK исправления
    for error, correction in pik_corrections.items():
        text = re.sub(error, correction, text, flags=re.IGNORECASE)
    
    # Удаляем короткие строки-артефакты
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if len(line) > 2 and not re.match(r'^[^\w]*$', line):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def extract_pik_structure(text: str) -> Dict:
    """Извлечение PIK структурных элементов из текста."""
    pik_keywords = {
        'ecosystem': ['ecosystem', 'экосистема', 'network effects', 'platform'],
        'stakeholders': ['customer', 'partner', 'supplier', 'developer', 'user', 'stakeholder'],
        'forces': ['forces', 'силы', 'trends', 'тренды', 'regulatory', 'технологические'],
        'strategy': ['strategy', 'стратегия', 'positioning', 'позиционирование'],
        'architecture': ['architecture', 'архитектура', 'technical', 'технический'],
        'business_model': ['business model', 'бизнес-модель', 'revenue', 'доходы', 'costs', 'затраты']
    }
    
    structure = {}
    text_lower = text.lower()
    
    for category, keywords in pik_keywords.items():
        matches = []
        for keyword in keywords:
            if keyword in text_lower:
                # Извлекаем контекст вокруг ключевого слова
                pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                context_matches = re.findall(pattern, text, re.IGNORECASE)
                matches.extend([match.strip() for match in context_matches])
        
        if matches:
            structure[category] = list(set(matches))
    
    return structure

def format_enhanced_output(text_data: str, table_data: List[Dict], 
                         image_data: str, pik_structure: Dict,
                         comprehensive_results: Optional[Dict] = None) -> str:
    """Форматирование расширенного вывода с интеграцией комплексного анализа."""
    
    output_parts = []
    
    # Заголовок
    output_parts.append("# 📊 PIK Document Analysis Report")
    output_parts.append(f"*Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Результаты комплексного анализа (если доступны)
    if comprehensive_results:
        output_parts.append("## 🔬 Комплексный Региональный Анализ")
        output_parts.append("*Специализированный анализ PIK диаграмм с региональным разбором*\n")
        
        # Общая статистика
        stats = []
        if 'total_images' in comprehensive_results:
            stats.append(f"📸 Изображений проанализировано: {comprehensive_results['total_images']}")
        if 'total_regions' in comprehensive_results:
            stats.append(f"🗺️ Регионов обработано: {comprehensive_results['total_regions']}")
        if 'average_quality' in comprehensive_results:
            stats.append(f"🎯 Средняя точность: {comprehensive_results['average_quality']:.1f}%")
        
        if stats:
            output_parts.append("\n".join(stats) + "\n")
        
        # Детализированные результаты по изображениям
        if 'image_results' in comprehensive_results:
            for img_result in comprehensive_results['image_results']:
                output_parts.append(f"### 📋 {img_result.get('image_name', 'Изображение')}")
                
                if 'regions_found' in img_result:
                    output_parts.append(f"**Регионов найдено:** {img_result['regions_found']}")
                if 'overall_quality' in img_result:
                    output_parts.append(f"**Качество:** {img_result['overall_quality']:.1f}%")
                
                # PIK категории
                if img_result.get('pik_categories'):
                    output_parts.append(f"**PIK Категории:** {', '.join(img_result['pik_categories'])}")
                
                # Стейкхолдеры
                if img_result.get('stakeholders'):
                    output_parts.append(f"**Стейкхолдеры:** {', '.join(img_result['stakeholders'])}")
                
                # Региональный текст
                if img_result.get('regions'):
                    output_parts.append("**Региональный контент:**")
                    for region in img_result['regions']:
                        if region.get('text'):
                            text_preview = region['text'][:100]
                            if len(region['text']) > 100:
                                text_preview += "..."
                            output_parts.append(f"- *{region.get('name', 'Регион')}*: {text_preview}")
                
                # Улучшенный текст
                if img_result.get('enhanced_text'):
                    output_parts.append("**Полный извлеченный текст:**")
                    output_parts.append(f"```\n{img_result['enhanced_text']}\n```")
                
                output_parts.append("")
    
    # PIK структурный анализ
    if pik_structure:
        output_parts.append("## 🏗️ PIK Структурный Анализ")
        for category, items in pik_structure.items():
            if items:
                category_name = category.replace('_', ' ').title()
                output_parts.append(f"### {category_name}")
                for item in items[:5]:  # Ограничиваем количество
                    output_parts.append(f"- {item}")
                output_parts.append("")
    
    # Основной текстовый контент
    if text_data:
        output_parts.append("## 📝 Основной Текстовый Контент")
        output_parts.append(text_data)
        output_parts.append("")
    
    # Таблицы
    if table_data:
        output_parts.append("## 📊 Извлеченные Таблицы")
        for i, table in enumerate(table_data, 1):
            output_parts.append(f"### Таблица {i}")
            if 'data' in table:
                # Форматируем как markdown таблицу
                rows = table['data']
                if rows:
                    # Заголовок
                    header = " | ".join(str(cell) for cell in rows[0])
                    separator = " | ".join("---" for _ in rows[0])
                    output_parts.append(f"| {header} |")
                    output_parts.append(f"| {separator} |")
                    
                    # Данные
                    for row in rows[1:]:
                        row_text = " | ".join(str(cell) for cell in row)
                        output_parts.append(f"| {row_text} |")
            output_parts.append("")
    
    # OCR изображений (базовый)
    if image_data:
        output_parts.append("## 🖼️ Базовый OCR Изображений")
        output_parts.append(image_data)
    
    return "\n".join(output_parts)

def process_pdf_enhanced(pdf_path: str, output_dir: Optional[str] = None) -> Dict:
    """
    Расширенная обработка PDF с интеграцией комплексного анализа.
    
    Args:
        pdf_path: Путь к PDF файлу
        output_dir: Директория для сохранения результатов
    
    Returns:
        Dict с результатами анализа
    """
    print(f"🚀 Начинаем расширенную обработку: {Path(pdf_path).name}")
    
    # Подготовка директорий
    if not output_dir:
        output_dir = Path("OCR") / Path(pdf_path).stem
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    images_dir = output_path / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Инициализация результатов
    results = {
        'text_data': '',
        'table_data': [],
        'image_data': '',
        'pik_structure': {},
        'comprehensive_results': None,
        'processing_stats': {
            'start_time': datetime.now(),
            'pages_processed': 0,
            'images_extracted': 0,
            'tables_found': 0
        }
    }
    
    # Инициализация комплексного парсера
    comprehensive_parser = None
    if COMPREHENSIVE_PARSER_AVAILABLE:
        try:
            comprehensive_parser = PIKDiagramParser()
            print("✅ Комплексный PIK парсер инициализирован")
        except Exception as e:
            print(f"⚠️  Ошибка инициализации комплексного парсера: {e}")
    
    try:
        # 1. Извлечение текста через pdfplumber
        print("📄 Извлечение текста...")
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    cleaned_text = clean_ocr_text(page_text)
                    if cleaned_text:
                        text_parts.append(f"=== СТРАНИЦА {page_num + 1} ===\n{cleaned_text}")
                
                # Извлечение таблиц
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        results['table_data'].append({
                            'page': page_num + 1,
                            'data': table
                        })
                        results['processing_stats']['tables_found'] += 1
                
                results['processing_stats']['pages_processed'] += 1
            
            results['text_data'] = '\n\n'.join(text_parts)
            print(f"   ✅ Извлечено {len(text_parts)} страниц текста, {len(results['table_data'])} таблиц")
        
        # 2. OCR и комплексный анализ изображений
        print("🔍 OCR и комплексный анализ изображений...")
        
        comprehensive_results = {
            'total_images': 0,
            'total_regions': 0,
            'average_quality': 0.0,
            'image_results': []
        }
        
        pdfdoc = pdfium.PdfDocument(pdf_path)
        ocr_parts = []
        total_quality = 0
        total_images = 0
        
        for page_num, page in enumerate(pdfdoc):
            try:
                print(f"   📋 Обработка страницы {page_num + 1}...")
                
                # Рендерим страницу
                pil_image = page.render(
                    scale=2.0, rotation=0, crop=None, colorspace="rgb", 
                    color=None, alpha=True, password=None
                ).to_pil()
                
                image_path = images_dir / f"full_page_{page_num + 1}.png"
                pil_image.save(str(image_path))
                results['processing_stats']['images_extracted'] += 1
                
                page_text = ""
                image_result = {
                    'image_name': f"full_page_{page_num + 1}.png",
                    'page_number': page_num + 1
                }
                
                # Комплексный анализ если доступен
                if comprehensive_parser:
                    print(f"      🔬 Комплексный региональный анализ...")
                    try:
                        comp_result = comprehensive_parser.analyze_pik_image(str(image_path))
                        
                        if comp_result:
                            page_text = comp_result.get('enhanced_text', '')
                            image_result.update(comp_result)
                            
                            comprehensive_results['total_regions'] += comp_result.get('regions_found', 0)
                            total_quality += comp_result.get('overall_quality', 0)
                            total_images += 1
                            
                            if comp_result.get('regions_found', 0) > 0:
                                print(f"         ✅ {comp_result['regions_found']} регионов, {comp_result.get('overall_quality', 0):.1f}% качество")
                            else:
                                print(f"         ⚠️  Регионы не обнаружены")
                        else:
                            print(f"         ❌ Комплексный анализ не дал результатов")
                            
                    except Exception as e:
                        print(f"         ❌ Ошибка комплексного анализа: {e}")
                
                # Базовый OCR как дополнение/fallback
                if not page_text.strip():
                    print(f"      🔤 Базовый OCR...")
                    try:
                        ocr_text = pytesseract.image_to_string(
                            pil_image, 
                            lang='eng+rus', 
                            config='--psm 1 --oem 3'
                        )
                        page_text = clean_ocr_text(ocr_text)
                        
                        if page_text.strip():
                            print(f"         ✅ Базовый OCR: {len(page_text)} символов")
                        else:
                            print(f"         ⚠️  Базовый OCR не дал результатов")
                    except Exception as e:
                        print(f"         ❌ Ошибка базового OCR: {e}")
                
                # Добавляем результат страницы
                if page_text.strip():
                    ocr_parts.append(f"=== СТРАНИЦА {page_num + 1} ===\n{page_text}")
                    
                    if not image_result.get('enhanced_text'):
                        image_result['enhanced_text'] = page_text
                
                comprehensive_results['image_results'].append(image_result)
                
            except Exception as e:
                print(f"   ❌ Ошибка обработки страницы {page_num + 1}: {e}")
                continue
        
        # Финализация статистики комплексного анализа
        comprehensive_results['total_images'] = total_images
        if total_images > 0:
            comprehensive_results['average_quality'] = total_quality / total_images
        
        results['image_data'] = '\n\n'.join(ocr_parts)
        results['comprehensive_results'] = comprehensive_results
        
        print(f"   ✅ Обработано {total_images} изображений с комплексным анализом")
        
        # 3. PIK структурный анализ
        print("🏗️ PIK структурный анализ...")
        all_text = results['text_data'] + '\n' + results['image_data']
        results['pik_structure'] = extract_pik_structure(all_text)
        
        structure_count = sum(len(items) for items in results['pik_structure'].values())
        print(f"   ✅ Найдено {structure_count} PIK элементов")
        
        # 4. Сохранение результатов
        print("💾 Сохранение результатов...")
        
        # Основной результат
        enhanced_output = format_enhanced_output(
            results['text_data'],
            results['table_data'],
            results['image_data'],
            results['pik_structure'],
            results['comprehensive_results']
        )
        
        result_file = output_path / f"{Path(pdf_path).stem}_result.md"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_output)
        
        # JSON с детальными данными
        json_result = {
            'metadata': {
                'source_file': str(pdf_path),
                'processing_time': str(datetime.now() - results['processing_stats']['start_time']),
                'pages_processed': results['processing_stats']['pages_processed'],
                'images_extracted': results['processing_stats']['images_extracted'],
                'tables_found': results['processing_stats']['tables_found']
            },
            'pik_structure': results['pik_structure'],
            'comprehensive_analysis': results['comprehensive_results']
        }
        
        json_file = output_path / f"{Path(pdf_path).stem}_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        # Финальная статистика
        end_time = datetime.now()
        processing_time = end_time - results['processing_stats']['start_time']
        
        print(f"\n🎉 Обработка завершена!")
        print(f"   📁 Результаты сохранены в: {output_path}")
        print(f"   📄 Основной отчет: {result_file.name}")
        print(f"   📊 JSON данные: {json_file.name}")
        print(f"   ⏱️  Время обработки: {processing_time}")
        print(f"   📈 Статистика:")
        print(f"      • Страниц обработано: {results['processing_stats']['pages_processed']}")
        print(f"      • Изображений извлечено: {results['processing_stats']['images_extracted']}")
        print(f"      • Таблиц найдено: {results['processing_stats']['tables_found']}")
        
        if comprehensive_results['total_images'] > 0:
            print(f"      • Комплексный анализ: {comprehensive_results['total_images']} изображений")
            print(f"      • Средняя точность: {comprehensive_results['average_quality']:.1f}%")
            print(f"      • Всего регионов: {comprehensive_results['total_regions']}")
        
        return {
            'success': True,
            'output_path': str(output_path),
            'result_file': str(result_file),
            'json_file': str(json_file),
            'stats': results['processing_stats'],
            'comprehensive_stats': comprehensive_results
        }
        
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при обработке: {e}"
        print(error_msg)
        print(f"Детали ошибки:\n{traceback.format_exc()}")
        
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

def main():
    """Основная функция для CLI использования."""
    if len(sys.argv) < 2:
        print("Использование: python integrated_enhanced_ocr.py <путь_к_PDF>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Файл не найден: {pdf_path}")
        sys.exit(1)
    
    # Обработка
    result = process_pdf_enhanced(pdf_path)
    
    if result['success']:
        print(f"\n✅ Успешно! Результаты в: {result['output_path']}")
    else:
        print(f"\n❌ Ошибка: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
