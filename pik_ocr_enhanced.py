#!/usr/bin/env python3
"""
Интеграция улучшений OCR в основную систему
"""

import re
import difflib
from typing import Dict, List, Tuple

def clean_ocr_text(text: str) -> str:
    """
    Улучшенная очистка OCR текста специально для PIK документов
    """
    if not text or len(text.strip()) < 5:
        return text
    
    # 1. Базовая очистка
    # Удаляем явный мусор
    text = re.sub(r'[^\w\s\-\.,§•€£$%@&()]', ' ', text)
    
    # 2. Исправление известных OCR ошибок для PIK терминов
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
    
    # 3. Разделение слипшихся слов
    common_splits = {
        'ofthe': 'of the',
        'forthe': 'for the', 
        'andthe': 'and the',
        'tothe': 'to the',
        'inthe': 'in the',
        'onthe': 'on the',
        'thetoolset': 'the toolset',
        'platformgeneration': 'platform generation',
        'PlatformInnovation': 'Platform Innovation',
    }
    
    for joined, separated in common_splits.items():
        text = text.replace(joined, separated)
    
    # 4. Разделяем по заглавным буквам (осторожно)
    text = re.sub(r'(?<=[a-z])(?=[A-Z][a-z])', ' ', text)
    
    # 5. Исправляем маркеры списков
    text = text.replace('§', '•')
    
    # 6. Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    
    # 7. Исправляем пунктуацию
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    
    return text.strip()


def extract_pik_structure(text: str) -> Dict:
    """
    Извлечение структуры PIK диаграмм
    """
    structure = {
        'title': None,
        'version': None,
        'main_categories': [],
        'subcategories': {},
        'metadata': {}
    }
    
    # Паттерны для PIK документов
    patterns = {
        'canvas_title': r'([A-Z\s]+(?:CANVAS|SCAN|MAP|FORCES))\s*v?[\d.]*',
        'version': r'v(\d+\.\d+)',
        'main_categories': r'\b(ENVIRONMENT|MARKET|VALUE CHAIN|MACROECONOMIC|ECOSYSTEM FORCES)\b',
        'website': r'(www\.[a-zA-Z0-9\.-]+\.com)',
        'created_by': r'Created by\s+([^\n\r]+)',
        'subcategory_marker': r'[§•]\s*([A-Za-z][^§•\n\r]{5,50})',
    }
    
    # Извлекаем заголовок
    title_match = re.search(patterns['canvas_title'], text, re.IGNORECASE)
    if title_match:
        structure['title'] = title_match.group(1).strip()
    
    # Извлекаем версию
    version_match = re.search(patterns['version'], text)
    if version_match:
        structure['version'] = version_match.group(1)
    
    # Извлекаем основные категории
    main_cats = re.findall(patterns['main_categories'], text, re.IGNORECASE)
    structure['main_categories'] = list(set([cat.upper() for cat in main_cats]))
    
    # Инициализируем подкатегории
    for cat in structure['main_categories']:
        structure['subcategories'][cat] = []
    
    # Извлекаем подкатегории с контекстом
    lines = text.split('\n')
    current_category = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Ищем основную категорию в строке
        for cat in structure['main_categories']:
            if cat in line.upper():
                current_category = cat
                break
        
        # Ищем подкатегории
        subcats = re.findall(patterns['subcategory_marker'], line)
        if subcats and current_category:
            for subcat in subcats:
                clean_subcat = subcat.strip()
                if len(clean_subcat) > 3 and clean_subcat not in structure['subcategories'][current_category]:
                    structure['subcategories'][current_category].append(clean_subcat)
    
    # Извлекаем метаданные
    website_match = re.search(patterns['website'], text)
    if website_match:
        structure['metadata']['website'] = website_match.group(1)
    
    created_by_match = re.search(patterns['created_by'], text)
    if created_by_match:
        structure['metadata']['created_by'] = created_by_match.group(1).strip()
    
    return structure


def format_pik_output(text: str, structure: Dict) -> str:
    """
    Форматирование улучшенного вывода для PIK документов
    """
    output = []
    
    # Заголовок
    if structure.get('title'):
        output.append(f"# {structure['title']}")
        if structure.get('version'):
            output.append(f"*Версия: {structure['version']}*")
        output.append("")
    
    # Основные категории с подкатегориями
    if structure.get('main_categories'):
        output.append("## 🎯 Основные категории")
        output.append("")
        
        for category in structure['main_categories']:
            output.append(f"### {category}")
            
            subcats = structure['subcategories'].get(category, [])
            if subcats:
                for subcat in subcats:
                    output.append(f"- {subcat}")
            else:
                output.append("- *(подкатегории не найдены)*")
            output.append("")
    
    # Очищенный текст
    cleaned_text = clean_ocr_text(text)
    if cleaned_text != text:
        output.append("## 📝 Очищенный текст")
        output.append("")
        output.append("```")
        output.append(cleaned_text)
        output.append("```")
        output.append("")
    
    # Метаданные
    if structure.get('metadata'):
        output.append("## ℹ️ Метаданные")
        for key, value in structure['metadata'].items():
            output.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        output.append("")
    
    return '\n'.join(output)


def demo_improvements():
    """Демонстрация улучшений на реальном примере"""
    
    # Используем реальный плохой OCR из нашего результата
    real_bad_ocr = """
    TNEMNORIVNE
    ECOSYSTEM FORCES SCAN v5.0
    Part of the Platform Innovation Kit -the toolset for the platform generation
    Download at www.platforminnovationkit.com
    Created by fastbreak.one TITLE
    -NORIVNE
    TNEM
    ENVIRONMENT MARKET
    § Societal and cultural forces § Regulatory trends
    § Socialeconomic forces § Key technology trends
    § Naturalforces § Market issues
    VALUE CHAIN MACROECONOMIC
    Forces from other value chain actors Forces from global market conditions:
    Examples of stakeholders: § Capital markets
    § Competitors (Incumbents) § Economic infrastructure
    § New entrants (Insurgents) § Commodities and other resources
    § Substitute product & services
    """
    
    print("🔍 ДЕМОНСТРАЦИЯ УЛУЧШЕНИЙ OCR ДЛЯ PIK ДОКУМЕНТОВ")
    print("=" * 70)
    
    print("\n📝 Исходный плохой OCR текст:")
    print("-" * 40)
    print(real_bad_ocr)
    
    print("\n✅ После очистки:")
    print("-" * 40)
    cleaned = clean_ocr_text(real_bad_ocr)
    print(cleaned)
    
    print("\n📊 Извлеченная структура:")
    print("-" * 40)
    structure = extract_pik_structure(cleaned)
    for key, value in structure.items():
        print(f"{key}: {value}")
    
    print("\n📋 Финальный отформатированный результат:")
    print("-" * 40)
    formatted = format_pik_output(real_bad_ocr, structure)
    print(formatted)


if __name__ == "__main__":
    demo_improvements()
