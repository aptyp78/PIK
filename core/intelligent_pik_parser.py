#!/usr/bin/env python3
"""
Intelligent PIK Methodology Parser
=================================

Интеллектуальный парсер методологии Platform Innovation Kit (PIK)
с пониманием семантики фреймворков и трансформацией в draw.io

Автор: GitHub Copilot
Версия: 1.0
Дата: 2024

Основные возможности:
- Семантическое понимание PIK методологии (25+ фреймворков)
- Идентификация типов фреймворков и их роли в жизненном цикле
- Извлечение стейкхолдеров, сил, сетевых эффектов, ценностных предложений
- Генерация интерактивных draw.io диаграмм с сохранением логики методологии
- Подготовка к автоматизации и интеллектуализации PIK процессов
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import os
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PIKFrameworkType(Enum):
    """Типы PIK фреймворков в методологии"""
    ECOSYSTEM_FORCES = "ecosystem_forces"  # Сканирование экосистемных сил
    NFX_ENGINES = "nfx_engines"  # Двигатели сетевых эффектов
    BUSINESS_MODEL = "business_model"  # Бизнес-модель платформы
    PLATFORM_EXPERIENCE = "platform_experience"  # Пользовательский опыт
    VALUE_NETWORK = "value_network"  # Сеть создания ценности
    STAKEHOLDER_MAP = "stakeholder_map"  # Карта стейкхолдеров
    COMPETITIVE_ANALYSIS = "competitive_analysis"  # Конкурентный анализ
    INNOVATION_MAP = "innovation_map"  # Карта инноваций
    UNKNOWN = "unknown"  # Неопределенный тип

class ElementType(Enum):
    """Типы элементов в PIK диаграммах"""
    STAKEHOLDER = "stakeholder"  # Стейкхолдер
    FORCE = "force"  # Сила/фактор
    NFX_ENGINE = "nfx_engine"  # Двигатель сетевых эффектов
    VALUE_PROPOSITION = "value_proposition"  # Ценностное предложение
    CONNECTION = "connection"  # Связь/отношение
    PROCESS = "process"  # Процесс
    RESOURCE = "resource"  # Ресурс
    OUTCOME = "outcome"  # Результат
    ICON = "icon"  # Иконка
    LABEL = "label"  # Подпись

@dataclass
class PIKElement:
    """Базовый элемент PIK диаграммы"""
    id: str
    type: ElementType
    text: str
    position: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    properties: Dict[str, Any]
    relationships: List[str]  # ID связанных элементов

@dataclass
class PIKFramework:
    """PIK фреймворк с семантическим пониманием"""
    id: str
    type: PIKFrameworkType
    title: str
    elements: List[PIKElement]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    semantic_analysis: Dict[str, Any]

class IntelligentPIKParser:
    """
    Интеллектуальный парсер PIK методологии
    
    Понимает семантику фреймворков и преобразует их в интерактивные
    draw.io диаграммы с сохранением методологической логики.
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """Инициализация парсера"""
        self.cache_dir = cache_dir
        self.frameworks_cache = {}
        self.semantic_patterns = self._load_semantic_patterns()
        self.drawio_templates = self._load_drawio_templates()
        
        # Создаем директории
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs("output/drawio", exist_ok=True)
        os.makedirs("output/analysis", exist_ok=True)
        
        logger.info("🧠 Intelligent PIK Parser инициализирован")
    
    def _load_semantic_patterns(self) -> Dict[str, Any]:
        """Загружает паттерны для семантического анализа PIK"""
        return {
            "framework_indicators": {
                PIKFrameworkType.ECOSYSTEM_FORCES: [
                    "ecosystem", "forces", "scan", "environment", "market",
                    "экосистема", "силы", "сканирование", "окружение"
                ],
                PIKFrameworkType.NFX_ENGINES: [
                    "network", "effects", "engines", "viral", "data",
                    "сетевые", "эффекты", "двигатели", "вирусные"
                ],
                PIKFrameworkType.BUSINESS_MODEL: [
                    "business", "model", "revenue", "platform", "monetization",
                    "бизнес", "модель", "доходы", "платформа", "монетизация"
                ],
                PIKFrameworkType.PLATFORM_EXPERIENCE: [
                    "experience", "user", "journey", "interface", "interaction",
                    "опыт", "пользователь", "путешествие", "интерфейс"
                ],
                PIKFrameworkType.VALUE_NETWORK: [
                    "value", "network", "creation", "exchange", "flow",
                    "ценность", "сеть", "создание", "обмен", "поток"
                ]
            },
            "element_patterns": {
                ElementType.STAKEHOLDER: [
                    "user", "customer", "partner", "supplier", "developer",
                    "пользователь", "клиент", "партнер", "поставщик"
                ],
                ElementType.FORCE: [
                    "force", "pressure", "trend", "driver", "factor",
                    "сила", "давление", "тренд", "фактор"
                ],
                ElementType.VALUE_PROPOSITION: [
                    "value", "benefit", "proposition", "advantage",
                    "ценность", "выгода", "предложение", "преимущество"
                ]
            }
        }
    
    def _load_drawio_templates(self) -> Dict[str, str]:
        """Загружает шаблоны draw.io для разных типов фреймворков"""
        return {
            "base_template": """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{timestamp}" agent="PIK-Parser" version="21.1.2">
  <diagram name="{framework_name}" id="{diagram_id}">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {elements}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>""",
            "stakeholder_style": 'shape=ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=12;',
            "force_style": 'shape=hexagon;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=11;',
            "value_style": 'shape=process;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;fontSize=11;',
            "connection_style": 'shape=connector;curved=1;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#666666;'
        }
    
    def parse_pik_image(self, image_path: str) -> PIKFramework:
        """
        Главный метод парсинга PIK изображения
        
        Args:
            image_path: Путь к изображению PIK фреймворка
            
        Returns:
            PIKFramework: Распознанный и семантически проанализированный фреймворк
        """
        logger.info(f"🔍 Начинаем интеллектуальный анализ PIK: {image_path}")
        
        # 1. Загружаем и предобрабатываем изображение
        image = self._load_and_preprocess_image(image_path)
        
        # 2. Определяем тип фреймворка
        framework_type = self._detect_framework_type(image, image_path)
        
        # 3. Извлекаем элементы с учетом семантики
        elements = self._extract_semantic_elements(image, framework_type)
        
        # 4. Анализируем связи и отношения
        relationships = self._analyze_relationships(elements, framework_type)
        
        # 5. Проводим семантический анализ
        semantic_analysis = self._perform_semantic_analysis(elements, relationships, framework_type)
        
        # 6. Создаем объект фреймворка
        framework = PIKFramework(
            id=self._generate_framework_id(image_path),
            type=framework_type,
            title=self._extract_framework_title(image, elements),
            elements=elements,
            relationships=relationships,
            metadata={
                "source_image": image_path,
                "parsed_at": datetime.now().isoformat(),
                "parser_version": "1.0",
                "total_elements": len(elements),
                "confidence_score": self._calculate_confidence(elements)
            },
            semantic_analysis=semantic_analysis
        )
        
        logger.info(f"✅ PIK фреймворк успешно проанализирован: {framework.type.value}")
        return framework
    
    def _load_and_preprocess_image(self, image_path: str) -> np.ndarray:
        """Загружает и предобрабатывает изображение для анализа"""
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Не удалось загрузить изображение: {image_path}")
        
        # Увеличиваем разрешение для лучшего OCR
        height, width = image.shape[:2]
        scale_factor = max(2.0, 2000 / max(width, height))
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Улучшаем качество для OCR
        # Конвертируем в RGB для PIL
        image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Улучшаем контрастность
        enhancer = ImageEnhance.Contrast(image_pil)
        image_pil = enhancer.enhance(1.3)
        
        # Улучшаем резкость
        enhancer = ImageEnhance.Sharpness(image_pil)
        image_pil = enhancer.enhance(1.2)
        
        # Возвращаем как numpy array
        return cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    
    def _detect_framework_type(self, image: np.ndarray, image_path: str) -> PIKFrameworkType:
        """Определяет тип PIK фреймворка на основе контента"""
        # Извлекаем весь текст для анализа
        text = pytesseract.image_to_string(image, lang='eng+rus', config='--psm 6')
        text_lower = text.lower()
        
        # Проверяем также имя файла
        filename_lower = os.path.basename(image_path).lower()
        combined_text = text_lower + " " + filename_lower
        
        # Подсчитываем совпадения для каждого типа
        type_scores = {}
        for framework_type, keywords in self.semantic_patterns["framework_indicators"].items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                type_scores[framework_type] = score
        
        # Возвращаем тип с максимальным счетом
        if type_scores:
            detected_type = max(type_scores, key=type_scores.get)
            logger.info(f"🎯 Определен тип фреймворка: {detected_type.value} (уверенность: {type_scores[detected_type]})")
            return detected_type
        
        logger.warning("⚠️ Не удалось определить тип фреймворка, используем UNKNOWN")
        return PIKFrameworkType.UNKNOWN
    
    def _extract_semantic_elements(self, image: np.ndarray, framework_type: PIKFrameworkType) -> List[PIKElement]:
        """Извлекает элементы с учетом семантики конкретного типа фреймворка"""
        elements = []
        
        # Извлекаем текстовые области
        text_elements = self._extract_text_elements(image)
        
        # Извлекаем иконки и графические элементы
        visual_elements = self._extract_visual_elements(image)
        
        # Объединяем и классифицируем элементы
        all_elements = text_elements + visual_elements
        
        for element_data in all_elements:
            element = self._classify_element(element_data, framework_type)
            if element:
                elements.append(element)
        
        logger.info(f"📊 Извлечено {len(elements)} семантических элементов")
        return elements
    
    def _extract_text_elements(self, image: np.ndarray) -> List[Dict]:
        """Извлекает текстовые элементы с позиционированием"""
        # Используем pytesseract для получения подробной информации
        data = pytesseract.image_to_data(image, lang='eng+rus', 
                                       config='--psm 6', output_type=pytesseract.Output.DICT)
        
        elements = []
        current_text = ""
        current_bbox = None
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = data['conf'][i]
            
            if text and conf > 30:  # Минимальная уверенность
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                
                # Группируем близкие текстовые блоки
                if current_bbox and self._are_close(current_bbox, (x, y, w, h)):
                    current_text += " " + text
                    current_bbox = self._merge_bboxes(current_bbox, (x, y, w, h))
                else:
                    if current_text:
                        elements.append({
                            'type': 'text',
                            'text': current_text,
                            'bbox': current_bbox,
                            'confidence': conf / 100.0
                        })
                    current_text = text
                    current_bbox = (x, y, w, h)
        
        # Добавляем последний элемент
        if current_text:
            elements.append({
                'type': 'text',
                'text': current_text,
                'bbox': current_bbox,
                'confidence': conf / 100.0
            })
        
        return elements
    
    def _extract_visual_elements(self, image: np.ndarray) -> List[Dict]:
        """Извлекает визуальные элементы (иконки, фигуры)"""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Детекция кругов (стейкхолдеры)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50,
                                 param1=50, param2=30, minRadius=20, maxRadius=100)
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                elements.append({
                    'type': 'circle',
                    'text': '',
                    'bbox': (x-r, y-r, 2*r, 2*r),
                    'confidence': 0.8,
                    'properties': {'radius': r, 'center': (x, y)}
                })
        
        # Детекция прямоугольников (процессы, ценности)
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 5000:  # Фильтруем по размеру
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                if 0.3 < aspect_ratio < 3.0:  # Разумное соотношение сторон
                    elements.append({
                        'type': 'rectangle',
                        'text': '',
                        'bbox': (x, y, w, h),
                        'confidence': 0.7,
                        'properties': {'area': area, 'aspect_ratio': aspect_ratio}
                    })
        
        return elements
    
    def _classify_element(self, element_data: Dict, framework_type: PIKFrameworkType) -> Optional[PIKElement]:
        """Классифицирует элемент на основе его характеристик и контекста фреймворка"""
        text = element_data.get('text', '').lower()
        visual_type = element_data.get('type', '')
        bbox = element_data['bbox']
        confidence = element_data['confidence']
        
        # Определяем тип элемента
        element_type = ElementType.LABEL  # По умолчанию
        
        # Классификация на основе визуального типа
        if visual_type == 'circle':
            element_type = ElementType.STAKEHOLDER
        elif visual_type == 'rectangle':
            element_type = ElementType.PROCESS
        
        # Уточняем классификацию на основе текста
        for elem_type, keywords in self.semantic_patterns["element_patterns"].items():
            if any(keyword in text for keyword in keywords):
                element_type = elem_type
                break
        
        # Контекстная классификация для конкретных фреймворков
        if framework_type == PIKFrameworkType.ECOSYSTEM_FORCES:
            if any(word in text for word in ['сила', 'фактор', 'тренд', 'force', 'factor']):
                element_type = ElementType.FORCE
        elif framework_type == PIKFrameworkType.NFX_ENGINES:
            if any(word in text for word in ['эффект', 'двигатель', 'engine', 'effect']):
                element_type = ElementType.NFX_ENGINE
        
        # Создаем элемент
        return PIKElement(
            id=str(uuid.uuid4()),
            type=element_type,
            text=element_data.get('text', ''),
            position=bbox,
            confidence=confidence,
            properties=element_data.get('properties', {}),
            relationships=[]
        )
    
    def _analyze_relationships(self, elements: List[PIKElement], framework_type: PIKFrameworkType) -> List[Dict[str, Any]]:
        """Анализирует связи между элементами"""
        relationships = []
        
        # Анализируем пространственную близость
        for i, elem1 in enumerate(elements):
            for j, elem2 in enumerate(elements[i+1:], i+1):
                distance = self._calculate_distance(elem1.position, elem2.position)
                
                if distance < 200:  # Пороговое расстояние для связи
                    relationship = {
                        'id': str(uuid.uuid4()),
                        'source': elem1.id,
                        'target': elem2.id,
                        'type': self._determine_relationship_type(elem1, elem2, framework_type),
                        'strength': max(0.1, 1.0 - distance / 200.0),
                        'properties': {}
                    }
                    relationships.append(relationship)
                    
                    # Добавляем взаимные ссылки
                    elem1.relationships.append(elem2.id)
                    elem2.relationships.append(elem1.id)
        
        logger.info(f"🔗 Найдено {len(relationships)} связей между элементами")
        return relationships
    
    def _determine_relationship_type(self, elem1: PIKElement, elem2: PIKElement, framework_type: PIKFrameworkType) -> str:
        """Определяет тип связи между элементами"""
        type1, type2 = elem1.type, elem2.type
        
        # Стандартные типы связей
        if type1 == ElementType.STAKEHOLDER and type2 == ElementType.VALUE_PROPOSITION:
            return "provides_value"
        elif type1 == ElementType.FORCE and type2 == ElementType.STAKEHOLDER:
            return "influences"
        elif type1 == ElementType.PROCESS and type2 == ElementType.OUTCOME:
            return "produces"
        
        # Контекстные связи для разных фреймворков
        if framework_type == PIKFrameworkType.NFX_ENGINES:
            if type1 == ElementType.NFX_ENGINE and type2 == ElementType.STAKEHOLDER:
                return "engages"
        
        return "related"
    
    def _perform_semantic_analysis(self, elements: List[PIKElement], 
                                 relationships: List[Dict[str, Any]], 
                                 framework_type: PIKFrameworkType) -> Dict[str, Any]:
        """Проводит семантический анализ фреймворка"""
        analysis = {
            "framework_completeness": self._assess_completeness(elements, framework_type),
            "key_insights": self._extract_insights(elements, relationships, framework_type),
            "methodology_alignment": self._check_methodology_alignment(elements, framework_type),
            "automation_opportunities": self._identify_automation_opportunities(elements, relationships),
            "quality_metrics": self._calculate_quality_metrics(elements, relationships)
        }
        
        return analysis
    
    def _assess_completeness(self, elements: List[PIKElement], framework_type: PIKFrameworkType) -> Dict[str, Any]:
        """Оценивает полноту фреймворка"""
        expected_elements = {
            PIKFrameworkType.ECOSYSTEM_FORCES: [ElementType.FORCE, ElementType.STAKEHOLDER],
            PIKFrameworkType.NFX_ENGINES: [ElementType.NFX_ENGINE, ElementType.STAKEHOLDER],
            PIKFrameworkType.BUSINESS_MODEL: [ElementType.VALUE_PROPOSITION, ElementType.STAKEHOLDER],
            PIKFrameworkType.PLATFORM_EXPERIENCE: [ElementType.PROCESS, ElementType.STAKEHOLDER],
            PIKFrameworkType.VALUE_NETWORK: [ElementType.VALUE_PROPOSITION, ElementType.CONNECTION]
        }
        
        expected = expected_elements.get(framework_type, [])
        found_types = set(elem.type for elem in elements)
        
        completeness = len(found_types.intersection(expected)) / len(expected) if expected else 1.0
        
        return {
            "score": completeness,
            "expected_elements": [et.value for et in expected],
            "found_elements": [et.value for et in found_types],
            "missing_elements": [et.value for et in set(expected) - found_types]
        }
    
    def _extract_insights(self, elements: List[PIKElement], relationships: List[Dict[str, Any]], 
                         framework_type: PIKFrameworkType) -> List[str]:
        """Извлекает ключевые инсайты из фреймворка"""
        insights = []
        
        # Подсчитываем элементы по типам
        type_counts = {}
        for elem in elements:
            type_counts[elem.type] = type_counts.get(elem.type, 0) + 1
        
        # Генерируем инсайты на основе анализа
        if ElementType.STAKEHOLDER in type_counts:
            insights.append(f"Идентифицировано {type_counts[ElementType.STAKEHOLDER]} стейкхолдеров в экосистеме")
        
        if len(relationships) > 0:
            insights.append(f"Обнаружено {len(relationships)} связей между элементами экосистемы")
        
        # Специфичные инсайты для каждого типа фреймворка
        if framework_type == PIKFrameworkType.ECOSYSTEM_FORCES:
            if ElementType.FORCE in type_counts:
                insights.append(f"Выявлено {type_counts[ElementType.FORCE]} экосистемных сил, влияющих на платформу")
        
        return insights
    
    def _check_methodology_alignment(self, elements: List[PIKElement], framework_type: PIKFrameworkType) -> Dict[str, Any]:
        """Проверяет соответствие методологии PIK"""
        # Проверяем наличие ключевых элементов методологии
        alignment_score = 0.0
        issues = []
        
        # Базовые проверки для всех фреймворков
        if not any(elem.type == ElementType.STAKEHOLDER for elem in elements):
            issues.append("Отсутствуют стейкхолдеры - ключевой элемент PIK методологии")
        else:
            alignment_score += 0.3
        
        # Специфичные проверки для типов фреймворков
        if framework_type == PIKFrameworkType.ECOSYSTEM_FORCES:
            if not any(elem.type == ElementType.FORCE for elem in elements):
                issues.append("В фреймворке сканирования сил отсутствуют экосистемные силы")
            else:
                alignment_score += 0.4
        
        if len(issues) == 0:
            alignment_score = 1.0
        
        return {
            "score": alignment_score,
            "issues": issues,
            "recommendations": self._generate_alignment_recommendations(issues, framework_type)
        }
    
    def _identify_automation_opportunities(self, elements: List[PIKElement], relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Выявляет возможности для автоматизации"""
        opportunities = []
        
        # Автоматизация связей
        if len(relationships) > 5:
            opportunities.append({
                "type": "relationship_automation",
                "description": "Автоматическое выявление и визуализация связей между элементами",
                "impact": "high",
                "complexity": "medium"
            })
        
        # Автоматизация классификации
        stakeholder_count = sum(1 for elem in elements if elem.type == ElementType.STAKEHOLDER)
        if stakeholder_count > 3:
            opportunities.append({
                "type": "stakeholder_segmentation",
                "description": "Автоматическая сегментация и приоритизация стейкхолдеров",
                "impact": "medium",
                "complexity": "low"
            })
        
        return opportunities
    
    def _calculate_quality_metrics(self, elements: List[PIKElement], relationships: List[Dict[str, Any]]) -> Dict[str, float]:
        """Вычисляет метрики качества анализа"""
        if not elements:
            return {"overall": 0.0}
        
        # Средняя уверенность распознавания
        avg_confidence = sum(elem.confidence for elem in elements) / len(elements)
        
        # Плотность связей
        max_connections = len(elements) * (len(elements) - 1) / 2
        connection_density = len(relationships) / max_connections if max_connections > 0 else 0
        
        # Разнообразие типов элементов
        unique_types = len(set(elem.type for elem in elements))
        type_diversity = min(1.0, unique_types / 5)  # Нормализуем к 5 основным типам
        
        # Общая оценка качества
        overall_quality = (avg_confidence * 0.4 + connection_density * 0.3 + type_diversity * 0.3)
        
        return {
            "overall": overall_quality,
            "recognition_confidence": avg_confidence,
            "connection_density": connection_density,
            "type_diversity": type_diversity,
            "element_count": len(elements),
            "relationship_count": len(relationships)
        }
    
    def generate_drawio_xml(self, framework: PIKFramework) -> str:
        """Генерирует XML для draw.io с интерактивными элементами"""
        logger.info(f"🎨 Генерируем draw.io диаграмму для {framework.type.value}")
        
        # Создаем элементы XML
        elements_xml = []
        cell_id = 2  # Начинаем с 2 (0 и 1 зарезервированы)
        
        # Добавляем заголовок
        title_xml = f'''
        <mxCell id="{cell_id}" value="{framework.title}" style="text;strokeColor=none;fillColor=none;html=1;fontSize=16;fontStyle=1;verticalAlign=middle;align=center;" vertex="1" parent="1">
          <mxGeometry x="50" y="20" width="300" height="30" as="geometry"/>
        </mxCell>'''
        elements_xml.append(title_xml)
        cell_id += 1
        
        # Добавляем элементы фреймворка
        element_positions = {}
        
        for element in framework.elements:
            x, y, w, h = element.position
            
            # Масштабируем позиции для draw.io
            draw_x = max(50, x // 3)
            draw_y = max(80, y // 3)
            draw_w = max(80, w // 3)
            draw_h = max(40, h // 3)
            
            # Выбираем стиль на основе типа элемента
            style = self._get_drawio_style(element.type)
            
            # Создаем tooltip с дополнительной информацией
            tooltip = self._create_element_tooltip(element)
            
            # Экранируем текст для XML
            escaped_text = element.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            
            element_xml = f'''
        <mxCell id="{cell_id}" value="{escaped_text}" style="{style}" vertex="1" parent="1">
          <mxGeometry x="{draw_x}" y="{draw_y}" width="{draw_w}" height="{draw_h}" as="geometry"/>
        </mxCell>'''
            
            elements_xml.append(element_xml)
            element_positions[element.id] = cell_id
            cell_id += 1
        
        # Добавляем связи
        for relationship in framework.relationships:
            source_id = element_positions.get(relationship['source'])
            target_id = element_positions.get(relationship['target'])
            
            if source_id and target_id:
                connection_xml = f'''
        <mxCell id="{cell_id}" style="{self.drawio_templates['connection_style']}" edge="1" parent="1" source="{source_id}" target="{target_id}">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>'''
                elements_xml.append(connection_xml)
                cell_id += 1
        
        # Собираем полный XML
        timestamp = datetime.now().isoformat()
        diagram_id = str(uuid.uuid4())
        
        xml_content = self.drawio_templates["base_template"].format(
            timestamp=timestamp,
            framework_name=framework.title,
            diagram_id=diagram_id,
            elements=''.join(elements_xml)
        )
        
        # Форматируем XML для красивого вывода
        dom = minidom.parseString(xml_content)
        formatted_xml = dom.toprettyxml(indent="  ")
        
        # Убираем лишние пустые строки
        lines = [line for line in formatted_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def _get_drawio_style(self, element_type: ElementType) -> str:
        """Возвращает стиль draw.io для типа элемента"""
        styles = {
            ElementType.STAKEHOLDER: self.drawio_templates['stakeholder_style'],
            ElementType.FORCE: self.drawio_templates['force_style'],
            ElementType.VALUE_PROPOSITION: self.drawio_templates['value_style'],
            ElementType.NFX_ENGINE: 'shape=cloud;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;',
            ElementType.PROCESS: 'shape=process;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;',
            ElementType.OUTCOME: 'shape=step;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;'
        }
        
        return styles.get(element_type, 'shape=rectangle;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;')
    
    def _create_element_tooltip(self, element: PIKElement) -> str:
        """Создает tooltip с информацией об элементе"""
        tooltip_parts = [
            f"Тип: {element.type.value}",
            f"Уверенность: {element.confidence:.2f}",
            f"Связи: {len(element.relationships)}"
        ]
        
        if element.properties:
            for key, value in element.properties.items():
                tooltip_parts.append(f"{key}: {value}")
        
        return " | ".join(tooltip_parts)
    
    def save_analysis_results(self, framework: PIKFramework, output_dir: str = "output") -> Dict[str, str]:
        """Сохраняет результаты анализа в различных форматах"""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/analysis", exist_ok=True)
        os.makedirs(f"{output_dir}/drawio", exist_ok=True)
        
        results = {}
        
        # Сохраняем JSON анализ
        json_path = f"{output_dir}/analysis/{framework.id}_analysis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(framework), f, ensure_ascii=False, indent=2, default=str)
        results['json'] = json_path
        
        # Генерируем и сохраняем draw.io XML
        drawio_xml = self.generate_drawio_xml(framework)
        xml_path = f"{output_dir}/drawio/{framework.id}_diagram.drawio"
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(drawio_xml)
        results['drawio'] = xml_path
        
        # Создаем отчет в Markdown
        markdown_report = self._generate_markdown_report(framework)
        md_path = f"{output_dir}/analysis/{framework.id}_report.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        results['report'] = md_path
        
        logger.info(f"💾 Результаты сохранены: JSON={json_path}, Draw.io={xml_path}, Report={md_path}")
        return results
    
    def _generate_markdown_report(self, framework: PIKFramework) -> str:
        """Генерирует подробный отчет в формате Markdown"""
        report = f"""# PIK Framework Analysis Report

## Основная информация
- **ID фреймворка**: {framework.id}
- **Тип**: {framework.type.value}
- **Название**: {framework.title}
- **Дата анализа**: {framework.metadata['parsed_at']}
- **Версия парсера**: {framework.metadata['parser_version']}

## Статистика элементов
- **Всего элементов**: {framework.metadata['total_elements']}
- **Общая уверенность**: {framework.metadata['confidence_score']:.2f}

### Распределение по типам:
"""
        
        # Подсчитываем элементы по типам
        type_counts = {}
        for element in framework.elements:
            type_counts[element.type.value] = type_counts.get(element.type.value, 0) + 1
        
        for elem_type, count in type_counts.items():
            report += f"- **{elem_type}**: {count}\n"
        
        report += f"\n## Семантический анализ\n"
        
        # Добавляем результаты семантического анализа
        semantic = framework.semantic_analysis
        
        if 'framework_completeness' in semantic:
            completeness = semantic['framework_completeness']
            report += f"\n### Полнота фреймворка: {completeness['score']:.2f}\n"
            
            if completeness.get('missing_elements'):
                report += "**Отсутствующие элементы:**\n"
                for missing in completeness['missing_elements']:
                    report += f"- {missing}\n"
        
        if 'key_insights' in semantic:
            report += "\n### Ключевые инсайты:\n"
            for insight in semantic['key_insights']:
                report += f"- {insight}\n"
        
        if 'methodology_alignment' in semantic:
            alignment = semantic['methodology_alignment']
            report += f"\n### Соответствие методологии: {alignment['score']:.2f}\n"
            
            if alignment.get('issues'):
                report += "**Проблемы:**\n"
                for issue in alignment['issues']:
                    report += f"- {issue}\n"
        
        if 'automation_opportunities' in semantic:
            report += "\n### Возможности автоматизации:\n"
            for opportunity in semantic['automation_opportunities']:
                report += f"- **{opportunity['type']}**: {opportunity['description']} (Влияние: {opportunity['impact']}, Сложность: {opportunity['complexity']})\n"
        
        # Добавляем детали элементов
        report += "\n## Детали элементов\n\n"
        
        for i, element in enumerate(framework.elements, 1):
            report += f"### {i}. {element.text or 'Элемент без текста'}\n"
            report += f"- **Тип**: {element.type.value}\n"
            report += f"- **Позиция**: ({element.position[0]}, {element.position[1]}) {element.position[2]}x{element.position[3]}\n"
            report += f"- **Уверенность**: {element.confidence:.2f}\n"
            
            if element.relationships:
                report += f"- **Связи**: {len(element.relationships)} элементов\n"
            
            if element.properties:
                report += "- **Свойства**:\n"
                for key, value in element.properties.items():
                    report += f"  - {key}: {value}\n"
            
            report += "\n"
        
        return report
    
    # Вспомогательные методы
    def _are_close(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int], threshold: int = 50) -> bool:
        """Проверяет близость двух bounding box"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        center1 = (x1 + w1//2, y1 + h1//2)
        center2 = (x2 + w2//2, y2 + h2//2)
        
        distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
        return distance < threshold
    
    def _merge_bboxes(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """Объединяет два bounding box"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1 + w1, x2 + w2)
        bottom = max(y1 + h1, y2 + h2)
        
        return (left, top, right - left, bottom - top)
    
    def _calculate_distance(self, pos1: Tuple[int, int, int, int], pos2: Tuple[int, int, int, int]) -> float:
        """Вычисляет расстояние между центрами элементов"""
        x1, y1, w1, h1 = pos1
        x2, y2, w2, h2 = pos2
        
        center1 = (x1 + w1//2, y1 + h1//2)
        center2 = (x2 + w2//2, y2 + h2//2)
        
        return ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
    
    def _generate_framework_id(self, image_path: str) -> str:
        """Генерирует уникальный ID для фреймворка"""
        filename = os.path.basename(image_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"pik_{timestamp}_{hash_part}"
    
    def _extract_framework_title(self, image: np.ndarray, elements: List[PIKElement]) -> str:
        """Извлекает заголовок фреймворка"""
        # Ищем самый верхний и крупный текстовый элемент
        title_candidates = []
        
        for element in elements:
            if element.text and len(element.text) > 5:  # Минимальная длина заголовка
                x, y, w, h = element.position
                score = h * w / (y + 1)  # Больше очков за размер и высокое положение
                title_candidates.append((score, element.text))
        
        if title_candidates:
            title_candidates.sort(reverse=True)
            return title_candidates[0][1]
        
        return "PIK Framework"
    
    def _calculate_confidence(self, elements: List[PIKElement]) -> float:
        """Вычисляет общую уверенность анализа"""
        if not elements:
            return 0.0
        
        return sum(elem.confidence for elem in elements) / len(elements)
    
    def _generate_alignment_recommendations(self, issues: List[str], framework_type: PIKFrameworkType) -> List[str]:
        """Генерирует рекомендации по улучшению соответствия методологии"""
        recommendations = []
        
        if "Отсутствуют стейкхолдеры" in str(issues):
            recommendations.append("Добавьте ключевых стейкхолдеров экосистемы для полноты анализа")
        
        if framework_type == PIKFrameworkType.ECOSYSTEM_FORCES and "силы" in str(issues):
            recommendations.append("Идентифицируйте и добавьте основные экосистемные силы, влияющие на платформу")
        
        if not recommendations:
            recommendations.append("Фреймворк соответствует стандартам PIK методологии")
        
        return recommendations

def main():
    """Демонстрация работы интеллектуального PIK парсера"""
    print("🧠 Intelligent PIK Parser v1.0")
    print("=" * 50)
    
    # Инициализируем парсер
    parser = IntelligentPIKParser()
    
    # Пример использования
    image_path = "OCR/attachment_image/original_attachment_image.png"
    
    if os.path.exists(image_path):
        try:
            # Парсим PIK фреймворк
            framework = parser.parse_pik_image(image_path)
            
            # Выводим краткую информацию
            print(f"\n📊 Результаты анализа:")
            print(f"Тип фреймворка: {framework.type.value}")
            print(f"Элементов найдено: {len(framework.elements)}")
            print(f"Связей найдено: {len(framework.relationships)}")
            print(f"Общая уверенность: {framework.metadata['confidence_score']:.2f}")
            
            # Сохраняем результаты
            files = parser.save_analysis_results(framework)
            print(f"\n💾 Файлы сохранены:")
            for file_type, path in files.items():
                print(f"  {file_type}: {path}")
            
            # Выводим ключевые инсайты
            if framework.semantic_analysis.get('key_insights'):
                print(f"\n🔍 Ключевые инсайты:")
                for insight in framework.semantic_analysis['key_insights']:
                    print(f"  • {insight}")
        
        except Exception as e:
            print(f"❌ Ошибка анализа: {str(e)}")
            logger.exception("Детали ошибки:")
    
    else:
        print(f"❌ Файл не найден: {image_path}")
        print("📝 Поместите PIK диаграмму в указанную папку для анализа")

if __name__ == "__main__":
    main()
