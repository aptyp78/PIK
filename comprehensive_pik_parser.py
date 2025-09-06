#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
from typing import List, Dict, Tuple, Optional
import json
import re

class PIKDiagramParser:
    """
    Специализированный парсер для PIK диаграмм с улучшенным распознаванием
    иконок, углов и центральных элементов
    """
    
    def __init__(self):
        self.icon_patterns = {
            # PIK иконки и символы
            '🌍': ['environment', 'earth', 'globe', 'world'],
            '📊': ['market', 'chart', 'graph', 'data'],
            '⛓️': ['chain', 'link', 'connection', 'value'],
            '💰': ['money', 'economic', 'finance', 'macro'],
            '🔄': ['cycle', 'process', 'flow', 'forces'],
            '🏗️': ['platform', 'infrastructure', 'build'],
            '💡': ['innovation', 'idea', 'creative'],
            '👥': ['stakeholders', 'people', 'users', 'customers'],
            '📈': ['growth', 'trend', 'increase', 'business'],
            '🎯': ['target', 'goal', 'objective', 'focus'],
            # Часто встречающиеся символы в PIK
            '→': ['arrow', 'flow', 'direction', 'leads'],
            '←': ['back', 'return', 'reverse'],
            '↑': ['up', 'increase', 'growth'],
            '↓': ['down', 'decrease', 'reduction'],
            '§': ['section', 'paragraph', 'point'],
            '•': ['bullet', 'point', 'item'],
            '★': ['star', 'important', 'key'],
            '◆': ['diamond', 'element', 'component']
        }
        
        # Регионы PIK диаграммы
        self.diagram_regions = {
            'top_left': 'ENVIRONMENT',
            'top_right': 'MARKET', 
            'bottom_left': 'VALUE CHAIN',
            'bottom_right': 'MACROECONOMIC',
            'center': 'CORE ELEMENTS',
            'header': 'TITLE/VERSION',
            'footer': 'METADATA'
        }
    
    def enhance_image_for_ocr(self, image: np.ndarray, enhancement_type: str = 'general') -> List[np.ndarray]:
        """
        Продвинутое улучшение изображения для различных типов контента
        """
        enhanced_images = []
        
        # Базовая очистка
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. Оригинал
        enhanced_images.append(gray)
        
        if enhancement_type == 'icons':
            # Специальная обработка для иконок и символов
            
            # Увеличение контраста для символов
            enhanced = cv2.convertScaleAbs(gray, alpha=2.0, beta=50)
            enhanced_images.append(enhanced)
            
            # Морфологическое закрытие для соединения разорванных символов
            kernel = np.ones((2,2), np.uint8)
            closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            enhanced_images.append(closed)
            
            # Адаптивная бинаризация
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            enhanced_images.append(adaptive)
            
        elif enhancement_type == 'corners':
            # Специальная обработка для углов диаграммы
            
            # Увеличение резкости
            kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel_sharp)
            enhanced_images.append(sharpened)
            
            # Размытие с последующим увеличением контраста
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            contrast_enhanced = cv2.convertScaleAbs(blurred, alpha=1.8, beta=30)
            enhanced_images.append(contrast_enhanced)
            
        elif enhancement_type == 'center':
            # Специальная обработка для центральных элементов
            
            # CLAHE для улучшения локального контраста
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            clahe_enhanced = clahe.apply(gray)
            enhanced_images.append(clahe_enhanced)
            
            # Удаление фона через морфологию
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
            background = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            foreground = cv2.subtract(gray, background)
            enhanced_images.append(foreground)
            
        elif enhancement_type == 'small_text':
            # Для мелкого текста в блоках
            
            # Увеличение изображения
            scale_factor = 3
            height, width = gray.shape
            resized = cv2.resize(gray, (width * scale_factor, height * scale_factor), 
                               interpolation=cv2.INTER_CUBIC)
            enhanced_images.append(resized)
            
            # Денойзинг + резкость на увеличенном изображении
            denoised = cv2.fastNlMeansDenoising(resized)
            kernel_sharp = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            sharp_denoised = cv2.filter2D(denoised, -1, kernel_sharp)
            enhanced_images.append(sharp_denoised)
        
        return enhanced_images
    
    def extract_region_text(self, image: np.ndarray, region: Tuple[int, int, int, int], 
                           region_type: str = 'general') -> Dict:
        """
        Извлечение текста из определенного региона с оптимизацией по типу
        """
        x, y, w, h = region
        roi = image[y:y+h, x:x+w]
        
        if roi.size == 0:
            return {'text': '', 'confidence': 0, 'elements': []}
        
        # Определяем тип улучшения на основе региона
        if 'corner' in region_type:
            enhancement_type = 'corners'
        elif 'center' in region_type:
            enhancement_type = 'center'
        elif 'icon' in region_type:
            enhancement_type = 'icons'
        else:
            enhancement_type = 'small_text'
        
        # Улучшаем изображение региона
        enhanced_rois = self.enhance_image_for_ocr(roi, enhancement_type)
        
        best_result = {'text': '', 'confidence': 0, 'elements': []}
        
        for i, enhanced_roi in enumerate(enhanced_rois):
            try:
                # Различные конфигурации OCR для разных типов контента
                configs = [
                    '--psm 6 --oem 3',  # Единый блок текста
                    '--psm 8 --oem 3',  # Одно слово
                    '--psm 7 --oem 3',  # Одна строка
                    '--psm 11 --oem 3', # Разреженный текст
                    '--psm 13 --oem 3'  # Сырая строка (для символов)
                ]
                
                for config in configs:
                    # Получаем детальные данные OCR
                    data = pytesseract.image_to_data(
                        enhanced_roi, 
                        lang='eng+rus',
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Фильтруем слова с хорошим доверием
                    words = []
                    confidences = []
                    
                    for j in range(len(data['text'])):
                        word = data['text'][j].strip()
                        conf = int(data['conf'][j])
                        
                        if word and conf > 30:  # Минимальное доверие
                            words.append(word)
                            confidences.append(conf)
                    
                    if words:
                        text = ' '.join(words)
                        avg_conf = np.mean(confidences)
                        
                        # Проверяем, лучше ли этот результат
                        if avg_conf > best_result['confidence']:
                            best_result = {
                                'text': text,
                                'confidence': avg_conf,
                                'elements': words,
                                'enhancement_variant': i,
                                'ocr_config': config
                            }
                            
            except Exception as e:
                print(f"Ошибка OCR для региона {region_type}: {e}")
                continue
        
        return best_result
    
    def detect_diagram_regions(self, image: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Автоматическое определение регионов PIK диаграммы
        """
        h, w = image.shape[:2]
        
        # Стандартная разметка PIK диаграммы
        regions = {
            # Основные квадранты
            'top_left': (0, 0, w//2, h//2),
            'top_right': (w//2, 0, w//2, h//2),
            'bottom_left': (0, h//2, w//2, h//2),
            'bottom_right': (w//2, h//2, w//2, h//2),
            
            # Центральная область
            'center': (w//4, h//4, w//2, h//2),
            
            # Заголовки и метаданные
            'header': (0, 0, w, h//8),
            'footer': (0, 7*h//8, w, h//8),
            
            # Боковые области для дополнительной информации
            'left_side': (0, h//4, w//8, h//2),
            'right_side': (7*w//8, h//4, w//8, h//2),
            'top_center': (w//4, 0, w//2, h//8),
            'bottom_center': (w//4, 7*h//8, w//2, h//8),
            
            # Углы для иконок и символов
            'corner_tl': (0, 0, w//8, h//8),
            'corner_tr': (7*w//8, 0, w//8, h//8),
            'corner_bl': (0, 7*h//8, w//8, h//8),
            'corner_br': (7*w//8, 7*h//8, w//8, h//8)
        }
        
        return regions
    
    def parse_pik_diagram_comprehensive(self, image_path: str) -> Dict:
        """
        Комплексный парсинг PIK диаграммы с извлечением всех элементов
        """
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            return {'error': f'Не удалось загрузить изображение: {image_path}'}
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Определяем регионы
        regions = self.detect_diagram_regions(gray)
        
        # Результат парсинга
        result = {
            'source_image': image_path,
            'regions': {},
            'comprehensive_text': '',
            'detected_icons': [],
            'pik_structure': {
                'categories': {},
                'stakeholders': [],
                'metadata': {},
                'quality_indicators': {}
            }
        }
        
        print(f"🔍 Комплексный анализ: {os.path.basename(image_path)}")
        
        # Обрабатываем каждый регион
        for region_name, region_coords in regions.items():
            print(f"   📍 Анализ региона: {region_name}")
            
            region_result = self.extract_region_text(
                gray, region_coords, region_name
            )
            
            if region_result['text']:
                result['regions'][region_name] = region_result
                result['comprehensive_text'] += f"[{region_name.upper()}] {region_result['text']} "
                
                print(f"      ✅ Найден текст: {region_result['text'][:50]}...")
                print(f"      📊 Доверие: {region_result['confidence']:.1f}%")
                
                # Анализируем найденный текст
                self._analyze_region_content(region_name, region_result, result['pik_structure'])
            else:
                print(f"      ❌ Текст не найден")
        
        # Постобработка и структуризация
        self._post_process_results(result)
        
        return result
    
    def _analyze_region_content(self, region_name: str, region_result: Dict, structure: Dict):
        """
        Анализ содержимого региона и добавление в PIK структуру
        """
        text = region_result['text'].upper()
        elements = region_result['elements']
        
        # Определяем PIK категории по регионам
        region_to_category = {
            'top_left': 'ENVIRONMENT',
            'top_right': 'MARKET',
            'bottom_left': 'VALUE CHAIN',
            'bottom_right': 'MACROECONOMIC',
            'center': 'CORE FRAMEWORK'
        }
        
        if region_name in region_to_category:
            category = region_to_category[region_name]
            
            if category not in structure['categories']:
                structure['categories'][category] = {
                    'region': region_name,
                    'elements': [],
                    'confidence': region_result['confidence']
                }
            
            # Добавляем элементы
            structure['categories'][category]['elements'].extend(elements)
        
        # Ищем участников экосистемы
        stakeholder_keywords = [
            'competitors', 'incumbents', 'insurgents', 'new entrants',
            'capital markets', 'customers', 'suppliers', 'partners',
            'infrastructure', 'commodities', 'substitutes'
        ]
        
        for keyword in stakeholder_keywords:
            if keyword in text.lower():
                structure['stakeholders'].append({
                    'name': keyword,
                    'region': region_name,
                    'confidence': region_result['confidence']
                })
        
        # Метаданные
        if 'header' in region_name or 'footer' in region_name:
            if 'version' not in structure['metadata']:
                structure['metadata']['version'] = self._extract_version(text)
            if 'title' not in structure['metadata']:
                structure['metadata']['title'] = self._extract_title(text)
    
    def _extract_version(self, text: str) -> Optional[str]:
        """Извлечение версии из текста"""
        version_pattern = r'v\.?\s*(\d+(?:\.\d+)?)'
        match = re.search(version_pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Извлечение заголовка"""
        # Ищем PIK паттерны
        title_patterns = [
            r'(.*?(?:CANVAS|SCAN|FORCES|MODEL|EXPERIENCE).*?)(?:v\d|$)',
            r'(ECOSYSTEM\s+FORCES?\s+SCAN)',
            r'(PLATFORM.*?CANVAS)',
            r'(.*?INNOVATION.*?KIT)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _post_process_results(self, result: Dict):
        """Постобработка результатов"""
        
        # Объединяем дублирующиеся элементы
        for category_data in result['pik_structure']['categories'].values():
            category_data['elements'] = list(set(category_data['elements']))
        
        # Убираем дубликаты участников
        seen_stakeholders = set()
        unique_stakeholders = []
        for stakeholder in result['pik_structure']['stakeholders']:
            if stakeholder['name'] not in seen_stakeholders:
                unique_stakeholders.append(stakeholder)
                seen_stakeholders.add(stakeholder['name'])
        result['pik_structure']['stakeholders'] = unique_stakeholders
        
        # Вычисляем общие метрики качества
        total_regions = len(result['regions'])
        successful_regions = len([r for r in result['regions'].values() if r['confidence'] > 50])
        
        result['pik_structure']['quality_indicators'] = {
            'total_regions_analyzed': total_regions,
            'successful_extractions': successful_regions,
            'overall_confidence': successful_regions / max(total_regions, 1) * 100,
            'total_text_length': len(result['comprehensive_text']),
            'categories_found': len(result['pik_structure']['categories']),
            'stakeholders_found': len(result['pik_structure']['stakeholders'])
        }

def demo_comprehensive_parsing():
    """
    Демонстрация комплексного парсинга PIK диаграммы
    """
    print("🚀 ДЕМОНСТРАЦИЯ КОМПЛЕКСНОГО ПАРСИНГА PIK")
    print("=" * 60)
    
    parser = PIKDiagramParser()
    
    # Тестируем на всех извлеченных изображениях
    images_dir = "OCR/PIK 5-0 - Ecosystem Forces Scan - ENG/images"
    
    if not os.path.exists(images_dir):
        print(f"❌ Папка с изображениями не найдена: {images_dir}")
        return
    
    image_files = [f for f in os.listdir(images_dir) if f.endswith('.png')]
    
    for image_file in image_files:
        image_path = os.path.join(images_dir, image_file)
        
        print(f"\n📊 Анализ: {image_file}")
        print("-" * 40)
        
        result = parser.parse_pik_diagram_comprehensive(image_path)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            continue
        
        # Выводим результаты
        quality = result['pik_structure']['quality_indicators']
        print(f"📈 Качество анализа: {quality['overall_confidence']:.1f}%")
        print(f"📍 Успешных регионов: {quality['successful_extractions']}/{quality['total_regions_analyzed']}")
        print(f"🎯 Найдено категорий: {quality['categories_found']}")
        print(f"👥 Найдено участников: {quality['stakeholders_found']}")
        
        if result['pik_structure']['categories']:
            print("\n📋 Найденные категории:")
            for category, data in result['pik_structure']['categories'].items():
                print(f"   {category}: {len(data['elements'])} элементов")
                if data['elements'][:3]:  # Показываем первые 3
                    print(f"      {', '.join(data['elements'][:3])}")
        
        if result['pik_structure']['stakeholders']:
            print(f"\n👥 Участники: {', '.join([s['name'] for s in result['pik_structure']['stakeholders'][:5]])}")
        
        if result['pik_structure']['metadata']:
            metadata = result['pik_structure']['metadata']
            if metadata.get('title'):
                print(f"📄 Заголовок: {metadata['title']}")
            if metadata.get('version'):
                print(f"🔢 Версия: {metadata['version']}")
        
        # Сохраняем детальный результат
        output_file = f"OCR/comprehensive_analysis_{image_file.replace('.png', '.json')}"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Детальный анализ сохранен: {output_file}")

if __name__ == "__main__":
    demo_comprehensive_parsing()
