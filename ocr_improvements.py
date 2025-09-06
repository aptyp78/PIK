#!/usr/bin/env python3
"""
Улучшения для OCR системы PIK документов
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
from typing import Dict, List, Tuple, Optional
import difflib

class AdvancedImagePreprocessor:
    """Продвинутая предобработка изображений для улучшения OCR"""
    
    def __init__(self):
        self.debug = False
    
    def enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """Улучшение качества изображения"""
        # Повышение резкости
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Удаление шума
        denoised = cv2.bilateralFilter(sharpened, 9, 75, 75)
        
        # Улучшение контраста
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        if len(denoised.shape) == 3:
            lab = cv2.cvtColor(denoised, cv2.COLOR_RGB2LAB)
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        else:
            enhanced = clahe.apply(denoised)
        
        return enhanced
    
    def correct_skew(self, image: np.ndarray) -> np.ndarray:
        """Исправление наклона документа"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # Детекция линий для определения угла наклона
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:10]:  # Берем первые 10 линий
                angle = theta * 180 / np.pi - 90
                if -45 < angle < 45:  # Фильтруем разумные углы
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                if abs(median_angle) > 0.5:  # Корректируем только если наклон значительный
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    corrected = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), 
                                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                    return corrected
        
        return image
    
    def segment_text_regions(self, image: np.ndarray) -> List[Tuple[np.ndarray, str]]:
        """Сегментация изображения на текстовые регионы"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Морфологические операции для выделения текстовых областей
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        
        # Поиск контуров
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 50 and h > 20:  # Фильтруем мелкие области
                region = image[y:y+h, x:x+w]
                
                # Классификация региона
                aspect_ratio = w / h
                if aspect_ratio > 3:
                    region_type = "header"
                elif aspect_ratio > 1.5:
                    region_type = "paragraph"
                elif w > h:
                    region_type = "table_row"
                else:
                    region_type = "column"
                
                regions.append((region, region_type))
        
        return regions


class PIKTerminologyCorrector:
    """Коррекция терминологии и постобработка OCR для PIK документов"""
    
    def __init__(self):
        # Словарь бизнес-терминов PIK
        self.business_terms = {
            'ENVIRONMENT': ['TNEMNORIVNE', 'ENVIRONMEN', 'ENVIRONMNT'],
            'MARKET': ['MARKE', 'MAKRET', 'MARET'],
            'VALUE CHAIN': ['VALUE CHAI', 'VALU CHAIN', 'VLUE CHAIN'],
            'MACROECONOMIC': ['MACROECONOMI', 'MACROECNOMIC', 'MACROECNOMI'],
            'ECOSYSTEM': ['ECOSYSTE', 'ECOSYSEM', 'ECOSYSYTEM'],
            'PLATFORM': ['PLATFOR', 'PLATFROM', 'PLTFORM'],
            'INNOVATION': ['INNOVATIO', 'INOVATION', 'INNVATION'],
            'STAKEHOLDERS': ['STAKEHOLDER', 'STAKEHOLDE', 'STAKEHODER'],
            'COMPETITORS': ['COMPETITO', 'COMPETITRS', 'COMPETTORS'],
            'INSURGENTS': ['INSURGEN', 'INSURGENT', 'INSERGENTS'],
            'INCUMBENTS': ['INCUMBEN', 'INCUMBENT', 'INCOMBENTS'],
        }
        
        # Паттерны для очистки
        self.noise_patterns = [
            r'[^\w\s\-\.,§•]',  # Удаляем спецсимволы кроме списков
            r'\s+',  # Множественные пробелы
            r'(?<=[a-z])(?=[A-Z])',  # Разделяем слипшиеся слова
        ]
    
    def correct_text(self, text: str) -> str:
        """Основная функция коррекции текста"""
        # Базовая очистка
        cleaned = self._clean_text(text)
        
        # Коррекция терминов
        corrected = self._correct_business_terms(cleaned)
        
        # Разделение слипшихся слов
        separated = self._separate_words(corrected)
        
        # Финальная очистка
        final = self._final_cleanup(separated)
        
        return final
    
    def _clean_text(self, text: str) -> str:
        """Базовая очистка текста"""
        # Удаляем очевидный мусор
        text = re.sub(r'[^\w\s\-\.,§•€£$%@&]', ' ', text)
        
        # Исправляем кодировку
        text = text.replace('§', '•')  # Нормализуем маркеры списков
        
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _correct_business_terms(self, text: str) -> str:
        """Коррекция бизнес-терминологии"""
        for correct_term, variations in self.business_terms.items():
            for variation in variations:
                # Прямая замена
                text = text.replace(variation, correct_term)
                
                # Нечеткое сопоставление для похожих слов
                words = text.split()
                corrected_words = []
                
                for word in words:
                    best_match = difflib.get_close_matches(word.upper(), 
                                                         [correct_term] + variations, 
                                                         n=1, cutoff=0.6)
                    if best_match and best_match[0] != word.upper():
                        corrected_words.append(correct_term)
                    else:
                        corrected_words.append(word)
                
                text = ' '.join(corrected_words)
        
        return text
    
    def _separate_words(self, text: str) -> str:
        """Разделение слипшихся слов"""
        # Простая эвристика - разделяем по заглавным буквам
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
        
        # Разделяем известные комбинации
        text = re.sub(r'ofthe', 'of the', text)
        text = re.sub(r'forthe', 'for the', text)
        text = re.sub(r'andthe', 'and the', text)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Финальная очистка"""
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Исправляем пунктуацию
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        
        return text.strip()


class StructuredDataExtractor:
    """Извлечение структурированных данных из PIK диаграмм"""
    
    def __init__(self):
        self.diagram_patterns = {
            'canvas_title': r'([A-Z\s]+(?:CANVAS|SCAN|MAP))\s*v?[\d.]+',
            'main_categories': r'(ENVIRONMENT|MARKET|VALUE CHAIN|MACROECONOMIC|ECOSYSTEM)',
            'subcategories': r'•\s*([A-Za-z\s]+)',
            'version': r'v(\d+\.\d+)',
            'created_by': r'Created by\s+([^\n]+)',
            'website': r'(www\.[^\s]+)',
        }
    
    def extract_structure(self, text: str) -> Dict:
        """Извлечение структурированных данных"""
        structure = {
            'title': None,
            'version': None,
            'categories': {},
            'metadata': {}
        }
        
        # Извлекаем заголовок
        title_match = re.search(self.diagram_patterns['canvas_title'], text, re.IGNORECASE)
        if title_match:
            structure['title'] = title_match.group(1).strip()
        
        # Извлекаем версию
        version_match = re.search(self.diagram_patterns['version'], text)
        if version_match:
            structure['version'] = version_match.group(1)
        
        # Извлекаем основные категории и подкатегории
        categories = re.findall(self.diagram_patterns['main_categories'], text)
        for category in categories:
            structure['categories'][category] = []
        
        # Извлекаем подкатегории
        subcategories = re.findall(self.diagram_patterns['subcategories'], text)
        
        # Простая эвристика привязки подкатегорий к категориям
        current_category = None
        lines = text.split('\n')
        
        for line in lines:
            # Проверяем, есть ли основная категория в строке
            for category in structure['categories'].keys():
                if category in line:
                    current_category = category
                    break
            
            # Ищем подкатегории в текущей секции
            if current_category:
                subcats = re.findall(r'•\s*([A-Za-z\s]+)', line)
                for subcat in subcats:
                    if subcat.strip() not in structure['categories'][current_category]:
                        structure['categories'][current_category].append(subcat.strip())
        
        # Извлекаем метаданные
        created_by_match = re.search(self.diagram_patterns['created_by'], text)
        if created_by_match:
            structure['metadata']['created_by'] = created_by_match.group(1).strip()
        
        website_match = re.search(self.diagram_patterns['website'], text)
        if website_match:
            structure['metadata']['website'] = website_match.group(1).strip()
        
        return structure
    
    def format_structured_output(self, structure: Dict) -> str:
        """Форматирование структурированного вывода"""
        output = []
        
        if structure['title']:
            output.append(f"# {structure['title']}")
            if structure['version']:
                output.append(f"*Версия: {structure['version']}*")
            output.append("")
        
        # Категории и подкатегории
        for category, subcategories in structure['categories'].items():
            output.append(f"## {category}")
            for subcat in subcategories:
                output.append(f"- {subcat}")
            output.append("")
        
        # Метаданные
        if structure['metadata']:
            output.append("## Метаданные")
            for key, value in structure['metadata'].items():
                output.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        return '\n'.join(output)


def demonstrate_improvements():
    """Демонстрация улучшений OCR"""
    
    # Пример плохого OCR текста
    bad_ocr_text = """
    TNEMNORIVNE ENVIRONMENT MARKET
    Part ofthePlatformInnovation Kit -thetoolsetfortheplatformgeneration
    § Societal and cultural forces § Regulatory trends
    -NORIVNE TNEM
    Created by fastbreak.one
    """
    
    print("🔍 Демонстрация улучшений OCR")
    print("=" * 60)
    
    print("\n📝 Исходный OCR текст:")
    print(bad_ocr_text)
    
    # Коррекция текста
    corrector = PIKTerminologyCorrector()
    corrected_text = corrector.correct_text(bad_ocr_text)
    
    print("\n✅ После коррекции терминологии:")
    print(corrected_text)
    
    # Структурированное извлечение
    extractor = StructuredDataExtractor()
    structure = extractor.extract_structure(corrected_text)
    
    print("\n📊 Извлеченная структура:")
    print(structure)
    
    formatted_output = extractor.format_structured_output(structure)
    print("\n📋 Форматированный вывод:")
    print(formatted_output)


if __name__ == "__main__":
    demonstrate_improvements()
