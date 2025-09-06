#!/usr/bin/env python3
"""
Улучшенный OCR скрипт с извлечением изображений для PIK документов
"""

import os
import sys
import io
import time
import base64
import re
from typing import Dict, List, Tuple, Optional
from PIL import Image
import pdfplumber
import pypdfium2 as pdfium
import pytesseract

def extract_images_from_pdf(pdf_path: str, output_dir: str = "extracted_images") -> list:
    """Извлечение изображений из PDF"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    image_paths = []
    
    try:
        print(f"🖼️  Извлечение изображений через pdfplumber...")
        # Через pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Извлекаем изображения со страницы
                if hasattr(page, 'images') and page.images:
                    print(f"   📄 Страница {page_num}: найдено {len(page.images)} изображений")
                    for img_num, img in enumerate(page.images):
                        try:
                            # Получаем координаты изображения
                            x0, y0, x1, y1 = img['x0'], img['top'], img['x1'], img['bottom']
                            
                            # Вырезаем область изображения из страницы
                            cropped_page = page.crop((x0, y0, x1, y1))
                            img_obj = cropped_page.to_image(resolution=300)
                            
                            # Сохраняем изображение
                            img_path = f"{output_dir}/page_{page_num}_img_{img_num}.png"
                            img_obj.save(img_path)
                            image_paths.append(img_path)
                            print(f"     ✅ Сохранено: {img_path}")
                            
                        except Exception as e:
                            print(f"     ❌ Ошибка извлечения изображения {img_num} со страницы {page_num}: {e}")
        
        print(f"🖼️  Рендеринг полных страниц через pdfium...")
        # Через pdfium - рендерим страницы целиком для диаграмм
        pdfdoc = pdfium.PdfDocument(pdf_path)
        for page_num, page in enumerate(pdfdoc, 1):
            try:
                # Рендерим страницу в высоком разрешении
                bitmap = page.render(scale=3.0).to_pil()
                
                # Сохраняем полную страницу
                page_path = f"{output_dir}/full_page_{page_num}.png"
                bitmap.save(page_path)
                image_paths.append(page_path)
                print(f"   ✅ Сохранена полная страница {page_num}: {page_path}")
                
            except Exception as e:
                print(f"   ❌ Ошибка рендеринга страницы {page_num}: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка извлечения изображений: {e}")
    
    return image_paths

def clean_ocr_text(text: str) -> str:
    """
    Улучшенная очистка OCR текста для PIK документов
    """
    if not text or len(text.strip()) < 5:
        return text
    
    # Исправление известных OCR ошибок для PIK терминов
    pik_corrections = {
        'TNEMNORIVNE': 'ENVIRONMENT',
        'TNEM': 'ENVIRONMENT', 
        '-NORIVNE': 'ENVIRONMENT',
        'MAKRET': 'MARKET',
        'MARKE': 'MARKET',
        'VALU CHAIN': 'VALUE CHAIN',
        'VLUE CHAIN': 'VALUE CHAIN',
        'ECOSYSTE': 'ECOSYSTEM',
        'PLATFOR': 'PLATFORM',
        'INNOVATIO': 'INNOVATION',
        'STAKEHOLDER': 'STAKEHOLDERS',
        'COMPETITO': 'COMPETITORS',
        'INCUMBEN': 'INCUMBENTS',
        'INSURGEN': 'INSURGENTS',
    }
    
    for wrong, correct in pik_corrections.items():
        text = text.replace(wrong, correct)
    
    # Разделение слипшихся слов
    common_splits = {
        'ofthe': 'of the',
        'forthe': 'for the', 
        'andthe': 'and the',
        'tothe': 'to the',
        'thetoolset': 'the toolset',
        'platformgeneration': 'platform generation',
        'PlatformInnovation': 'Platform Innovation',
    }
    
    for joined, separated in common_splits.items():
        text = text.replace(joined, separated)
    
    # Разделяем по заглавным буквам (осторожно)
    text = re.sub(r'(?<=[a-z])(?=[A-Z][a-z])', ' ', text)
    
    # Исправляем маркеры списков и убираем шум
    text = text.replace('§', '•')
    text = re.sub(r'[^\w\s\-\.,§•€£$%@&()]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    
    return text.strip()


def extract_pik_structure(text: str) -> Dict:
    """
    Умное извлечение структуры PIK диаграмм
    """
    structure = {
        'title': None,
        'version': None,
        'type': None,
        'main_categories': [],
        'subcategories': {},
        'metadata': {},
        'quality_score': 0
    }
    
    # Паттерны для различных типов PIK документов
    patterns = {
        'canvas_title': r'([A-Z\s]+(?:CANVAS|SCAN|MAP|FORCES|MODEL|EXPERIENCE))\s*v?[\d.]*',
        'version': r'v(\d+\.\d+)',
        'main_categories': r'\b(ENVIRONMENT|MARKET|VALUE\s+CHAIN|MACROECONOMIC|ECOSYSTEM\s+FORCES|PLATFORM|INNOVATION|EXPERIENCE|BUSINESS\s+MODEL)\b',
        'website': r'(www\.[a-zA-Z0-9\.-]+\.com)',
        'created_by': r'Created\s+by\s+([^\n\r]+)',
        'subcategory_marker': r'[§•★▪▫◦‣⁃]\s*([A-Za-z][^§•★▪▫◦‣⁃\n\r]{8,60})',
        'stakeholder_pattern': r'Examples?\s+of\s+stakeholders?:?\s*([^§•★▪▫◦‣⁃\n\r]+)',
    }
    
    # 1. Извлекаем заголовок и определяем тип
    title_match = re.search(patterns['canvas_title'], text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        structure['title'] = title
        
        # Определяем тип диаграммы
        if 'FORCES' in title or 'SCAN' in title:
            structure['type'] = 'ecosystem_analysis'
        elif 'CANVAS' in title:
            structure['type'] = 'business_canvas'
        elif 'EXPERIENCE' in title:
            structure['type'] = 'experience_design'
        elif 'MODEL' in title:
            structure['type'] = 'business_model'
        else:
            structure['type'] = 'general_pik'
    
    # 2. Извлекаем версию
    version_match = re.search(patterns['version'], text)
    if version_match:
        structure['version'] = version_match.group(1)
    
    # 3. Извлекаем основные категории с учетом контекста
    main_cats = re.findall(patterns['main_categories'], text, re.IGNORECASE)
    structure['main_categories'] = list(set([cat.upper().strip() for cat in main_cats]))
    
    # 4. Инициализируем подкатегории
    for cat in structure['main_categories']:
        structure['subcategories'][cat] = {
            'items': [],
            'stakeholders': [],
            'description': ''
        }
    
    # 5. Умное извлечение подкатегорий с контекстом
    lines = text.split('\n')
    current_category = None
    context_window = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Очищаем строку для анализа
        clean_line = clean_ocr_text(line)
        context_window.append(clean_line)
        if len(context_window) > 3:
            context_window.pop(0)
        
        # Определяем текущую категорию по контексту
        for cat in structure['main_categories']:
            if cat in clean_line.upper() or any(cat in ctx.upper() for ctx in context_window):
                current_category = cat
                break
        
        # Извлекаем подкатегории
        subcats = re.findall(patterns['subcategory_marker'], clean_line)
        if subcats and current_category:
            for subcat in subcats:
                clean_subcat = subcat.strip()
                if (len(clean_subcat) > 5 and 
                    clean_subcat not in structure['subcategories'][current_category]['items'] and
                    not any(word in clean_subcat.lower() for word in ['created', 'download', 'www', 'kit'])):
                    structure['subcategories'][current_category]['items'].append(clean_subcat)
        
        # Специальная обработка для stakeholders
        stakeholder_match = re.search(patterns['stakeholder_pattern'], clean_line, re.IGNORECASE)
        if stakeholder_match and current_category:
            stakeholder_text = stakeholder_match.group(1)
            stakeholder_items = re.findall(r'[§•★▪▫◦‣⁃]\s*([^§•★▪▫◦‣⁃\n\r]+)', stakeholder_text)
            for item in stakeholder_items:
                clean_item = item.strip()
                if len(clean_item) > 5:
                    structure['subcategories'][current_category]['stakeholders'].append(clean_item)
    
    # 6. Извлекаем метаданные
    website_match = re.search(patterns['website'], text)
    if website_match:
        structure['metadata']['website'] = website_match.group(1)
    
    created_by_match = re.search(patterns['created_by'], text, re.IGNORECASE)
    if created_by_match:
        structure['metadata']['created_by'] = created_by_match.group(1).strip()
    
    # 7. Вычисляем оценку качества
    quality_score = 0
    if structure['title']: quality_score += 20
    if structure['version']: quality_score += 10
    if structure['main_categories']: quality_score += len(structure['main_categories']) * 15
    if any(structure['subcategories'][cat]['items'] for cat in structure['subcategories']): quality_score += 30
    if structure['metadata']: quality_score += len(structure['metadata']) * 5
    
    structure['quality_score'] = min(quality_score, 100)
    
    return structure


def format_enhanced_output(text: str, structure: Dict, images: list, tables: list) -> str:
    """
    Улучшенное форматирование вывода с семантическим анализом
    """
    output = []
    
    # Заголовок с метаинформацией
    if structure.get('title'):
        output.append(f"# {structure['title']}")
        metadata_line = []
        if structure.get('version'):
            metadata_line.append(f"Версия: {structure['version']}")
        if structure.get('type'):
            type_names = {
                'ecosystem_analysis': 'Анализ экосистемы',
                'business_canvas': 'Бизнес-канвас',
                'experience_design': 'Дизайн опыта',
                'business_model': 'Бизнес-модель',
                'general_pik': 'PIK диаграмма'
            }
            metadata_line.append(f"Тип: {type_names.get(structure['type'], structure['type'])}")
        
        if metadata_line:
            output.append(f"*{' | '.join(metadata_line)}*")
        
        # Индикатор качества
        quality = structure.get('quality_score', 0)
        if quality >= 80:
            quality_indicator = "🟢 Отличное качество"
        elif quality >= 60:
            quality_indicator = "🟡 Хорошее качество"
        elif quality >= 40:
            quality_indicator = "🟠 Среднее качество"
        else:
            quality_indicator = "🔴 Требует улучшения"
        
        output.append(f"*Качество распознавания: {quality}% {quality_indicator}*")
        output.append("")
    
    # Краткая сводка
    if structure.get('main_categories'):
        output.append("## 📋 Краткая сводка")
        output.append(f"- **Основных категорий**: {len(structure['main_categories'])}")
        total_subcats = sum(len(data['items']) for data in structure['subcategories'].values())
        output.append(f"- **Подкатегорий**: {total_subcats}")
        output.append(f"- **Изображений**: {len(images)}")
        output.append(f"- **Таблиц**: {len(tables)}")
        output.append("")
    
    # Структурированные категории
    if structure.get('main_categories'):
        output.append("## 🎯 Структурированные данные")
        output.append("")
        
        for category in structure['main_categories']:
            cat_data = structure['subcategories'].get(category, {'items': [], 'stakeholders': []})
            
            # Эмодзи для категорий
            category_icons = {
                'ENVIRONMENT': '🌍',
                'MARKET': '📊',
                'VALUE CHAIN': '⛓️',
                'MACROECONOMIC': '💰',
                'ECOSYSTEM FORCES': '🔄',
                'PLATFORM': '🏗️',
                'INNOVATION': '💡',
                'EXPERIENCE': '👥',
                'BUSINESS MODEL': '📈'
            }
            
            icon = category_icons.get(category, '📌')
            output.append(f"### {icon} {category}")
            
            if cat_data['items']:
                for item in cat_data['items'][:10]:  # Ограничиваем количество
                    output.append(f"- {item}")
                if len(cat_data['items']) > 10:
                    output.append(f"- *...и еще {len(cat_data['items']) - 10} элементов*")
            
            if cat_data['stakeholders']:
                output.append("\n**Заинтересованные стороны:**")
                for stakeholder in cat_data['stakeholders'][:5]:
                    output.append(f"- {stakeholder}")
            
            if not cat_data['items'] and not cat_data['stakeholders']:
                output.append("- *Данные не извлечены*")
            
            output.append("")
    
    # Остальные секции (изображения, таблицы, etc.)
    if images:
        output.append("## 🖼️ Извлеченные изображения")
        output.append("")
        for img_path in images[:5]:  # Показываем первые 5
            img_name = os.path.basename(img_path)
            output.append(f"### {img_name}")
            output.append(f"![{img_name}]({img_path})")
            output.append("")
        
        if len(images) > 5:
            output.append(f"*...и еще {len(images) - 5} изображений*")
            output.append("")
    
    # Очищенный текст
    cleaned_text = clean_ocr_text(text)
    if cleaned_text and len(cleaned_text) > 50:
        output.append("## 📝 Очищенный текст")
        output.append("")
        output.append("```")
        # Показываем только первые 500 символов
        preview_text = cleaned_text[:500]
        if len(cleaned_text) > 500:
            preview_text += "\n\n[...текст обрезан...]"
        output.append(preview_text)
        output.append("```")
        output.append("")
    
    # Метаданные
    if structure.get('metadata'):
        output.append("## ℹ️ Метаданные")
        for key, value in structure['metadata'].items():
            if len(value) < 100:  # Избегаем очень длинных значений
                output.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        output.append("")
    
    return '\n'.join(output)
    """
    Улучшенная очистка OCR текста для PIK документов
    """
    if not text or len(text.strip()) < 5:
        return text
    
    # Исправление известных OCR ошибок для PIK терминов
    pik_corrections = {
        'TNEMNORIVNE': 'ENVIRONMENT',
        'TNEM': 'ENVIRONMENT', 
        '-NORIVNE': 'ENVIRONMENT',
        'MAKRET': 'MARKET',
        'MARKE': 'MARKET',
        'VALU CHAIN': 'VALUE CHAIN',
        'VLUE CHAIN': 'VALUE CHAIN',
        'ECOSYSTE': 'ECOSYSTEM',
        'PLATFOR': 'PLATFORM',
        'INNOVATIO': 'INNOVATION',
        'STAKEHOLDER': 'STAKEHOLDERS',
        'COMPETITO': 'COMPETITORS',
        'INCUMBEN': 'INCUMBENTS',
        'INSURGEN': 'INSURGENTS',
    }
    
    for wrong, correct in pik_corrections.items():
        text = text.replace(wrong, correct)
    
    # Разделение слипшихся слов
    common_splits = {
        'ofthe': 'of the',
        'forthe': 'for the', 
        'andthe': 'and the',
        'tothe': 'to the',
        'thetoolset': 'the toolset',
        'platformgeneration': 'platform generation',
        'PlatformInnovation': 'Platform Innovation',
    }
    
    for joined, separated in common_splits.items():
        text = text.replace(joined, separated)
    
    # Разделяем по заглавным буквам (осторожно)
    text = re.sub(r'(?<=[a-z])(?=[A-Z][a-z])', ' ', text)
    
    # Исправляем маркеры списков и убираем шум
    text = text.replace('§', '•')
    text = re.sub(r'[^\w\s\-\.,§•€£$%@&()]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    
    return text.strip()

def format_table_to_markdown(table) -> str:
    """Простое форматирование таблицы в Markdown"""
    if not table or len(table) == 0:
        return "*Пустая таблица*"
    
    md_table = []
    for i, row in enumerate(table[:10]):  # Ограничиваем 10 строками
        if row:
            clean_row = [str(cell).strip() if cell else "" for cell in row]
            md_table.append(f"| {' | '.join(clean_row)} |")
            # Добавляем разделитель после первой строки
            if i == 0 and len(clean_row) > 0:
                separator = "|" + "|".join(["---"] * len(clean_row)) + "|"
                md_table.append(separator)
    
    if len(table) > 10:
        md_table.append(f"| ... и еще {len(table) - 10} строк ... |")
    
    return "\n".join(md_table)


def extract_structured_content(pdf_path: str) -> Tuple[Dict, List]:
    """Извлечение структурированного контента и таблиц"""
    structured_content = {}
    tables_info = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Извлекаем текст
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    structured_content[page_num] = page_text
                
                # Извлекаем таблицы
                tables = page.extract_tables()
                if tables:
                    print(f"   📊 Страница {page_num}: найдено {len(tables)} таблиц")
                    for table_idx, table in enumerate(tables, 1):
                        table_info = {
                            'page': page_num,
                            'index': table_idx,
                            'data': table,
                            'markdown': format_table_to_markdown(table) if table else ""
                        }
                        tables_info.append(table_info)
    except Exception as e:
        print(f"❌ Ошибка извлечения структурированного контента: {e}")
    
    return structured_content, tables_info


def perform_ocr_on_pages(pdf_path: str) -> Dict:
    """Выполнение OCR для всех страниц"""
    ocr_content = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"   🔍 OCR страница {page_num}...")
                
                try:
                    # Используем pypdfium2 для качественного рендеринга
                    pdf_doc = pdfium.PdfDocument(pdf_path)
                    pdf_page = pdf_doc.get_page(page_num - 1)
                    
                    # Рендерим с высоким разрешением
                    bitmap = pdf_page.render(scale=2.0)
                    pil_image = bitmap.to_pil()
                    
                    # OCR с оптимизированными параметрами
                    ocr_text = pytesseract.image_to_string(
                        pil_image, 
                        lang='eng+rus', 
                        config='--psm 6 --oem 3'
                    )
                    
                    pdf_page.close()
                    pdf_doc.close()
                    
                    if ocr_text and len(ocr_text.strip()) > 10:
                        ocr_content[page_num] = ocr_text
                        print(f"   ✅ OCR страница {page_num}: {len(ocr_text)} символов")
                    else:
                        print(f"   ⚠️  OCR страница {page_num}: текст слишком короткий или пустой")
                
                except Exception as e:
                    print(f"   ❌ Ошибка OCR страницы {page_num}: {e}")
                    continue
    
    except Exception as e:
        print(f"❌ Ошибка OCR обработки: {e}")
    
    return ocr_content


def enhanced_pdf_to_md_with_images(pdf_path: str, output_base_dir: str = "OCR") -> str:
    """Улучшенная функция с извлечением изображений и организацией в папку OCR"""
    
    # Создаем базовую папку OCR
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    
    # Создаем подпапку для конкретного документа
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    doc_dir = os.path.join(output_base_dir, pdf_name)
    img_dir = os.path.join(doc_dir, "images")
    
    # Создаем структуру папок
    os.makedirs(doc_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    
    # Извлекаем изображения
    print(f"🖼️  Извлечение изображений из {pdf_name}...")
    image_paths = extract_images_from_pdf(pdf_path, img_dir)
    print(f"✅ Извлечено {len(image_paths)} изображений в {img_dir}")
    
    md_parts = []
    md_parts.append(f"# {pdf_name}\n\n")
    md_parts.append(f"*Обработано: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    
    # Добавляем ссылки на извлеченные изображения
    if image_paths:
        md_parts.append("## 🖼️ Извлеченные изображения\n\n")
        for img_path in image_paths:
            img_name = os.path.basename(img_path)
            # Создаем относительный путь от markdown файла к изображению
            rel_path = os.path.join("images", img_name)
            md_parts.append(f"### {img_name}\n\n![{img_name}]({rel_path})\n\n")
    
    # Структурированный текст
    try:
        print("📄 Извлечение структурированного текста...")
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text() or ""
                    
                    # Улучшенное извлечение таблиц
                    tables = page.extract_tables()
                    table_text = ""
                    
                    if tables:
                        print(f"   📊 Страница {i}: найдено {len(tables)} таблиц")
                        for j, table in enumerate(tables):
                            if table and len(table) > 1:  # Проверяем что таблица не пустая
                                table_text += f"\n### 📊 Таблица {j+1} на странице {i}\n\n"
                                
                                # Обрабатываем заголовки
                                headers = table[0] if table[0] else []
                                if headers and any(h for h in headers if h and str(h).strip()):
                                    clean_headers = [str(h or "").strip() for h in headers]
                                    table_text += "| " + " | ".join(clean_headers) + " |\n"
                                    table_text += "|" + "---|" * len(clean_headers) + "\n"
                                
                                # Обрабатываем строки данных
                                for row in table[1:]:
                                    if row and any(cell for cell in row if cell and str(cell).strip()):
                                        clean_row = [str(cell or "").strip() for cell in row]
                                        table_text += "| " + " | ".join(clean_row) + " |\n"
                                
                                table_text += "\n"
                    
                    if text.strip() or table_text.strip():
                        combined_text = text.strip()
                        if table_text.strip():
                            combined_text += "\n\n" + table_text.strip()
                        
                        md_parts.append(f"\n## 📄 Страница {i} (Структурированный текст)\n\n{combined_text}\n")
                    
                except Exception as e:
                    print(f"   ⚠️  Ошибка обработки страницы {i}: {e}")
                    md_parts.append(f"\n## 📄 Страница {i}\n\n❌ [Ошибка извлечения текста: {str(e)}]\n")
    
    except Exception as e:
        print(f"❌ Ошибка структурированного извлечения: {e}")
    
    # OCR для диаграмм и изображений
    try:
        print("🔍 OCR обработка страниц...")
        
        # Импортируем комплексный парсер
        try:
            from comprehensive_pik_parser import PIKDiagramParser
            comprehensive_parser = PIKDiagramParser()
            use_comprehensive = True
            print("   ✅ Загружен комплексный PIK парсер")
        except ImportError:
            use_comprehensive = False
            print("   ⚠️  Комплексный парсер недоступен, используем базовый OCR")
        
        pdfdoc = pdfium.PdfDocument(pdf_path)
        
        for i, page in enumerate(pdfdoc, start=1):
            try:
                print(f"   🔍 OCR страница {i}...")
                # Рендерим страницу для OCR
                bitmap = page.render(scale=4.0).to_pil()
                
                # OCR с русским языком и упрощенной конфигурацией
                ocr_text = pytesseract.image_to_string(
                    bitmap, 
                    lang='eng+rus',
                    config='--psm 6'
                )
                
                if ocr_text.strip():
                    # Очистка OCR текста
                    cleaned_text = clean_ocr_text(ocr_text)
                    if cleaned_text and len(cleaned_text) > 20:
                        md_parts.append(f"\n## 🔍 OCR Страница {i}\n\n{cleaned_text}\n")
                        print(f"   ✅ OCR страница {i}: {len(cleaned_text)} символов")
                    else:
                        print(f"   ⚠️  OCR страница {i}: текст слишком короткий или пустой")
                else:
                    print(f"   ⚠️  OCR страница {i}: не найден текст")
                
            except Exception as e:
                print(f"   ❌ OCR ошибка на странице {i}: {e}")
    
    except Exception as e:
        print(f"❌ OCR обработка не удалась: {e}")
    
    result = "".join(md_parts).strip()
    
    # Применяем семантический анализ PIK
    if result:
        print("🎯 Применение семантического анализа...")
        
        # Извлекаем все тексты для анализа
        all_text = ""
        for part in md_parts:
            if "##" in part and ("OCR" in part or "Страница" in part):
                # Извлекаем только текстовую часть без заголовков
                lines = part.split('\n')
                text_lines = [line for line in lines if not line.startswith('#') and line.strip()]
                all_text += " ".join(text_lines) + " "
        
        if all_text.strip():
            # Применяем PIK структурный анализ
            pik_structure = extract_pik_structure(all_text)
            
            if pik_structure and (pik_structure.get('main_categories') or pik_structure.get('stakeholders')):
                print(f"   ✅ Найдено категорий: {len(pik_structure.get('main_categories', []))}")
                print(f"   ✅ Найдено участников: {len(pik_structure.get('stakeholders', set()))}")
                
                # Добавляем структурированный анализ в результат
                analysis_section = format_pik_analysis(pik_structure)
                result = result + "\n\n" + analysis_section
    
    return result if result else "# Документ обработан, но текст не извлечен"


def format_pik_analysis(structure: dict) -> str:
    """Форматирование PIK анализа для markdown"""
    analysis = ["## 🎯 PIK Структурный Анализ\n"]
    
    if structure.get('title'):
        analysis.append(f"**Документ:** {structure['title']}\n")
    
    if structure.get('version'):
        analysis.append(f"**Версия:** {structure['version']}\n")
    
    # Основные категории
    categories = structure.get('main_categories', [])
    if categories:
        analysis.append(f"\n### 📋 Основные категории ({len(categories)})\n")
        for category in categories:
            analysis.append(f"- **{category}**\n")
    
    # Участники экосистемы
    stakeholders = structure.get('stakeholders', set())
    if stakeholders:
        analysis.append(f"\n### 👥 Участники экосистемы ({len(stakeholders)})\n")
        for stakeholder in sorted(list(stakeholders))[:10]:  # Первые 10
            analysis.append(f"- {stakeholder}\n")
        if len(stakeholders) > 10:
            analysis.append(f"- *... и еще {len(stakeholders) - 10} участников*\n")
    
    # Подкатегории
    subcategories = structure.get('subcategories', {})
    if subcategories:
        analysis.append(f"\n### 📊 Детализация по категориям\n")
        for category, data in subcategories.items():
            if isinstance(data, dict) and data.get('items'):
                analysis.append(f"\n**{category}:**\n")
                for item in data['items'][:5]:  # Первые 5
                    analysis.append(f"- {item}\n")
                if len(data['items']) > 5:
                    analysis.append(f"- *... и еще {len(data['items']) - 5} элементов*\n")
    
    return "".join(analysis)

def main():
    # Проверяем приложенное изображение или используем тестовые файлы
    test_files = [
        # Приложенное изображение (если есть)
        "attachment_image.png",
        # Тестовый PDF PIK Ecosystem Forces Scan (приоритет)
        "_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Ecosystem Forces Scan - ENG.pdf",
        # Альтернативный PIK PDF
        "_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Introduction - English.pdf"
    ]
    
    pdf_file = None
    for test_file in test_files:
        if os.path.exists(test_file):
            pdf_file = test_file
            break
    
    if not pdf_file:
        print(f"❌ Файлы не найдены. Проверьте:")
        for tf in test_files:
            print(f"   📄 {tf}")
        print("📁 Доступные файлы:")
        if os.path.exists("_Sources"):
            for root, dirs, files in os.walk("_Sources"):
                for file in files:
                    if file.endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                        print(f"   📄 {os.path.join(root, file)}")
        return
    
    print(f"🚀 Обработка файла: {pdf_file}")
    print("=" * 60)
    
    try:
        # Обрабатываем файл в зависимости от типа
        if pdf_file.endswith(('.png', '.jpg', '.jpeg')):
            result = process_single_image(pdf_file)
            file_name = os.path.splitext(os.path.basename(pdf_file))[0]
        else:
            result = enhanced_pdf_to_md_with_images(pdf_file)
            file_name = os.path.splitext(os.path.basename(pdf_file))[0]
        
        # Сохраняем результат в папку OCR
        output_dir = "OCR"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{file_name}_result.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print("=" * 60)
        print(f"✅ Результат сохранен в {output_file}")
        print(f"📊 Размер результата: {len(result):,} символов")
        
        # Подсчет секций
        sections = result.count("##")
        images = result.count("![")
        tables = result.count("📊 Таблица")
        
        print(f"📈 Статистика:")
        print(f"   📄 Секций: {sections}")
        print(f"   🖼️  Изображений: {images}")
        print(f"   📊 Таблиц: {tables}")
        
        # Показываем структуру папки OCR
        print(f"\n📁 Структура папки OCR:")
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Показываем первые 10 файлов
                print(f"{subindent}📄 {file}")
            if len(files) > 10:
                print(f"{subindent}... и еще {len(files) - 10} файлов")
        
        # Показываем начало результата
        print("\n📝 Начало результата:")
        print("-" * 40)
        preview = result[:800] + "\n\n[...продолжение в файле...]" if len(result) > 800 else result
        print(preview)
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        import traceback
        traceback.print_exc()

def process_single_image(image_path: str, output_base_dir: str = "OCR") -> str:
    """Обработка одного изображения"""
    import time
    
    # Создаем структуру папок
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    
    img_name = os.path.splitext(os.path.basename(image_path))[0]
    doc_dir = os.path.join(output_base_dir, img_name)
    processed_dir = os.path.join(doc_dir, "processed")
    
    os.makedirs(doc_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Копируем оригинальное изображение
    original_copy = os.path.join(doc_dir, f"original_{os.path.basename(image_path)}")
    
    try:
        from PIL import Image
        img = Image.open(image_path)
        img.save(original_copy)
        print(f"✅ Оригинал сохранен: {original_copy}")
    except Exception as e:
        print(f"⚠️ Ошибка копирования: {e}")
    
    md_parts = []
    md_parts.append(f"# Анализ изображения: {img_name}\n\n")
    md_parts.append(f"*Обработано: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    
    # Добавляем оригинальное изображение
    md_parts.append("## 🖼️ Оригинальное изображение\n\n")
    md_parts.append(f"![Original]({os.path.basename(original_copy)})\n\n")
    
    # OCR анализ
    try:
        print("🔍 Выполняем OCR анализ изображения...")
        
        # Различные варианты OCR
        ocr_results = []
        
        # Стандартный OCR
        try:
            text1 = pytesseract.image_to_string(img, lang='eng+rus', config='--psm 6')
            if text1.strip():
                ocr_results.append(("Стандартный OCR", clean_ocr_text(text1)))
        except Exception as e:
            print(f"⚠️ Стандартный OCR не удался: {e}")
        
        # OCR для диаграмм
        try:
            text2 = pytesseract.image_to_string(img, lang='eng+rus', config='--psm 11')
            if text2.strip():
                ocr_results.append(("OCR для диаграмм", clean_ocr_text(text2)))
        except Exception as e:
            print(f"⚠️ OCR для диаграмм не удался: {e}")
        
        # OCR без фильтрации символов
        try:
            text3 = pytesseract.image_to_string(img, lang='eng+rus', config='--psm 6 -c tessedit_char_blacklist=')
            if text3.strip():
                ocr_results.append(("OCR без фильтров", clean_ocr_text(text3)))
        except Exception as e:
            print(f"⚠️ OCR без фильтров не удался: {e}")
        
        # Добавляем результаты OCR
        if ocr_results:
            md_parts.append("## 🔍 Результаты OCR\n\n")
            for method, text in ocr_results:
                if text and len(text) > 10:
                    md_parts.append(f"### {method}\n\n```\n{text}\n```\n\n")
                    print(f"✅ {method}: {len(text)} символов")
        else:
            md_parts.append("## 🔍 Результаты OCR\n\n*OCR не смог извлечь текст из изображения*\n\n")
            print("⚠️ OCR не извлек текст")
        
        # Анализ изображения
        md_parts.append("## 📊 Анализ изображения\n\n")
        md_parts.append(f"- **Размер**: {img.size[0]} x {img.size[1]} пикселей\n")
        md_parts.append(f"- **Режим**: {img.mode}\n")
        md_parts.append(f"- **Формат**: {img.format}\n\n")
        
        # Пытаемся определить тип контента
        all_text = " ".join([text for _, text in ocr_results])
        if "ECOSYSTEM" in all_text.upper():
            md_parts.append("**Тип контента**: Диаграмма экосистемы\n\n")
        elif "PLATFORM" in all_text.upper():
            md_parts.append("**Тип контента**: Платформенная диаграмма\n\n")
        elif any(word in all_text.upper() for word in ["MARKET", "VALUE", "CHAIN"]):
            md_parts.append("**Тип контента**: Схема ценностной цепочки\n\n")
        else:
            md_parts.append("**Тип контента**: Общая диаграмма/схема\n\n")
            
    except Exception as e:
        print(f"❌ Ошибка OCR анализа: {e}")
        md_parts.append("## ❌ Ошибка анализа\n\n")
        md_parts.append(f"Произошла ошибка при анализе изображения: {str(e)}\n\n")
    
    result = "".join(md_parts).strip()
    return result if result else "# Обработка изображения завершена, но содержимое не извлечено"

if __name__ == "__main__":
    main()
