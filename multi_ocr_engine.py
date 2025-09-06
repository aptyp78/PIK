#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import pytesseract
from PIL import Image
import concurrent.futures
import logging
from typing import List, Dict, Optional, Tuple
import time

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️  EasyOCR не установлен. Установите: pip install easyocr")

class MultiOCREngine:
    """
    Ансамбль OCR движков для максимальной точности
    """
    
    def __init__(self):
        self.engines = {}
        self.confidence_weights = {
            'tesseract': 1.0,
            'easyocr': 1.2,  # Обычно лучше для сложных изображений
        }
        
        # Инициализация движков
        self._init_engines()
        
    def _init_engines(self):
        """Инициализация доступных OCR движков"""
        
        # Tesseract (всегда доступен)
        self.engines['tesseract'] = {
            'available': True,
            'configs': {
                'default': '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?-()[]{}:;',
                'diagram': '--psm 11 --oem 3',
                'table': '--psm 6 --oem 1',
                'single_block': '--psm 8'
            }
        }
        
        # EasyOCR
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['en', 'ru'], gpu=False)
                self.engines['easyocr'] = {'available': True}
                print("✅ EasyOCR инициализирован")
            except Exception as e:
                print(f"❌ Ошибка инициализации EasyOCR: {e}")
                self.engines['easyocr'] = {'available': False}
        else:
            self.engines['easyocr'] = {'available': False}
    
    def preprocess_for_ocr(self, image: np.ndarray, document_type: str = 'general') -> List[np.ndarray]:
        """
        Адаптивная предобработка на основе типа документа
        """
        preprocessed_variants = []
        
        if document_type == 'pik_diagram':
            # Специальная обработка для PIK диаграмм
            variants = self._preprocess_pik_diagram(image)
        elif document_type == 'table':
            # Специальная обработка для таблиц
            variants = self._preprocess_table(image)
        else:
            # Общая обработка
            variants = self._preprocess_general(image)
        
        return variants
    
    def _preprocess_pik_diagram(self, image: np.ndarray) -> List[np.ndarray]:
        """Предобработка PIK диаграмм"""
        variants = []
        
        # Оригинал
        variants.append(image.copy())
        
        # Увеличение контраста для текста в рамках
        enhanced = cv2.convertScaleAbs(image, alpha=1.5, beta=20)
        variants.append(enhanced)
        
        # Морфологическая обработка для выделения текста
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Адаптивная бинаризация
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        variants.append(cv2.cvtColor(adaptive, cv2.COLOR_GRAY2BGR))
        
        # Выделение горизонтальных и вертикальных линий (для структуры канваса)
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_horizontal)
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel_vertical)
        
        # Создаем маску без линий для лучшего распознавания текста
        lines_mask = cv2.add(horizontal_lines, vertical_lines)
        text_only = cv2.subtract(gray, lines_mask)
        variants.append(cv2.cvtColor(text_only, cv2.COLOR_GRAY2BGR))
        
        return variants
    
    def _preprocess_table(self, image: np.ndarray) -> List[np.ndarray]:
        """Предобработка таблиц"""
        variants = []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Оригинал
        variants.append(image.copy())
        
        # Увеличение DPI программно
        scale_factor = 2
        height, width = gray.shape
        resized = cv2.resize(gray, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)
        variants.append(cv2.cvtColor(resized, cv2.COLOR_GRAY2BGR))
        
        # Удаление шума
        denoised = cv2.medianBlur(gray, 3)
        variants.append(cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR))
        
        return variants
    
    def _preprocess_general(self, image: np.ndarray) -> List[np.ndarray]:
        """Общая предобработка"""
        variants = []
        
        # Оригинал
        variants.append(image.copy())
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Повышение резкости
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        variants.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl1 = clahe.apply(gray)
        variants.append(cv2.cvtColor(cl1, cv2.COLOR_GRAY2BGR))
        
        return variants
    
    def extract_text_ensemble(self, image: np.ndarray, document_type: str = 'general') -> Dict:
        """
        Ансамблевое извлечение текста с несколькими движками
        """
        results = {
            'texts': [],
            'confidences': [],
            'engines_used': [],
            'best_result': '',
            'consensus_score': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # Предобработка изображений
        preprocessed_images = self.preprocess_for_ocr(image, document_type)
        
        # Параллельная обработка всеми доступными движками
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for engine_name, engine_info in self.engines.items():
                if engine_info['available']:
                    for i, img_variant in enumerate(preprocessed_images):
                        future = executor.submit(
                            self._extract_with_engine, 
                            engine_name, 
                            img_variant, 
                            document_type,
                            variant_id=i
                        )
                        futures.append(future)
            
            # Собираем результаты
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    if result and result['text'].strip():
                        results['texts'].append(result['text'])
                        results['confidences'].append(result['confidence'])
                        results['engines_used'].append(result['engine'])
                except Exception as e:
                    logging.warning(f"OCR engine failed: {e}")
        
        # Определяем лучший результат
        if results['texts']:
            best_result = self._select_best_result(results)
            results['best_result'] = best_result['text']
            results['consensus_score'] = best_result['score']
        
        results['processing_time'] = time.time() - start_time
        return results
    
    def _extract_with_engine(self, engine_name: str, image: np.ndarray, 
                           document_type: str, variant_id: int = 0) -> Optional[Dict]:
        """Извлечение текста конкретным движком"""
        
        try:
            if engine_name == 'tesseract':
                return self._tesseract_extract(image, document_type, variant_id)
            elif engine_name == 'easyocr':
                return self._easyocr_extract(image, variant_id)
                
        except Exception as e:
            logging.warning(f"Engine {engine_name} failed: {e}")
            return None
    
    def _tesseract_extract(self, image: np.ndarray, document_type: str, variant_id: int) -> Dict:
        """Извлечение через Tesseract"""
        
        # Выбираем конфигурацию на основе типа документа
        configs = self.engines['tesseract']['configs']
        
        if document_type == 'pik_diagram':
            config = configs.get('diagram', configs['default'])
        elif document_type == 'table':
            config = configs.get('table', configs['default'])
        else:
            config = configs['default']
        
        # Конвертируем в PIL Image
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)
        
        # Извлекаем текст с данными о доверии
        data = pytesseract.image_to_data(pil_image, lang='eng+rus', config=config, output_type=pytesseract.Output.DICT)
        
        # Фильтруем слова с низким доверием
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 30]
        words = [data['text'][i] for i, conf in enumerate(data['conf']) if int(conf) > 30 and data['text'][i].strip()]
        
        text = ' '.join(words)
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            'text': text,
            'confidence': avg_confidence,
            'engine': f'tesseract_v{variant_id}',
            'word_count': len(words)
        }
    
    def _easyocr_extract(self, image: np.ndarray, variant_id: int) -> Dict:
        """Извлечение через EasyOCR"""
        
        results = self.easyocr_reader.readtext(image, detail=1)
        
        texts = []
        confidences = []
        
        for (bbox, text, conf) in results:
            if conf > 0.3:  # Фильтр по доверию
                texts.append(text)
                confidences.append(conf * 100)  # Конвертируем в проценты
        
        combined_text = ' '.join(texts)
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            'text': combined_text,
            'confidence': avg_confidence,
            'engine': f'easyocr_v{variant_id}',
            'word_count': len(texts)
        }
    
    def _select_best_result(self, results: Dict) -> Dict:
        """Выбор лучшего результата на основе ансамбля"""
        
        if not results['texts']:
            return {'text': '', 'score': 0}
        
        # Взвешиваем результаты
        weighted_scores = []
        
        for i, text in enumerate(results['texts']):
            confidence = results['confidences'][i]
            engine = results['engines_used'][i].split('_')[0]  # Убираем variant_id
            
            # Базовая оценка
            base_score = confidence
            
            # Вес движка
            engine_weight = self.confidence_weights.get(engine, 1.0)
            
            # Бонус за длину (более длинные тексты часто лучше)
            length_bonus = min(len(text.split()) / 10, 1.0) * 10
            
            # Бонус за количество PIK терминов
            pik_terms = ['ENVIRONMENT', 'MARKET', 'VALUE', 'CHAIN', 'ECOSYSTEM', 'PLATFORM', 'INNOVATION']
            pik_bonus = sum(1 for term in pik_terms if term in text.upper()) * 5
            
            total_score = (base_score * engine_weight) + length_bonus + pik_bonus
            weighted_scores.append((text, total_score, i))
        
        # Сортируем по оценке
        weighted_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_text, best_score, best_index = weighted_scores[0]
        
        return {
            'text': best_text,
            'score': best_score,
            'engine': results['engines_used'][best_index],
            'original_confidence': results['confidences'][best_index]
        }

# Демонстрация использования
def demo_multi_ocr():
    """Демонстрация мульти-OCR движка"""
    
    print("🚀 ДЕМОНСТРАЦИЯ МУЛЬТИ-OCR ДВИЖКА")
    print("=" * 50)
    
    ocr_engine = MultiOCREngine()
    
    # Загружаем тестовое изображение
    test_image_path = "OCR/PIK 5-0 - Ecosystem Forces Scan - ENG/images/page_1_img_0.png"
    
    if os.path.exists(test_image_path):
        image = cv2.imread(test_image_path)
        
        print(f"📊 Обработка: {test_image_path}")
        print(f"🔧 Доступные движки: {[name for name, info in ocr_engine.engines.items() if info['available']]}")
        
        # Тестируем разные типы документов
        document_types = ['general', 'pik_diagram', 'table']
        
        for doc_type in document_types:
            print(f"\n📋 Тип документа: {doc_type}")
            print("-" * 30)
            
            result = ocr_engine.extract_text_ensemble(image, doc_type)
            
            print(f"⏱️  Время обработки: {result['processing_time']:.2f}с")
            print(f"🎯 Движков использовано: {len(set(result['engines_used']))}")
            print(f"📊 Консенсус-оценка: {result['consensus_score']:.1f}")
            print(f"✅ Лучший результат ({len(result['best_result'])} символов):")
            print(f"   {result['best_result'][:100]}...")
            
            if len(result['texts']) > 1:
                print(f"📈 Альтернативные результаты:")
                for i, (text, conf, engine) in enumerate(zip(result['texts'][:3], result['confidences'][:3], result['engines_used'][:3])):
                    print(f"   {engine}: {conf:.1f}% - {text[:50]}...")
    
    else:
        print(f"❌ Тестовое изображение не найдено: {test_image_path}")

if __name__ == "__main__":
    import os
    demo_multi_ocr()
