#!/usr/bin/env python3
"""
Smart PIK Parser v2.0
====================

Улучшенный парсер для корректной обработки PIK Business Model Canvas
и создания структурированных Draw.io диаграмм.

Основные улучшения:
- Grid Detection: определение табличной структуры PIK
- Visual Noise Filtering: отфильтровка артефактов OCR  
- Semantic Positioning: логичное размещение элементов
- PIK-Aware Layout Engine: понимание специфики PIK фреймворков
"""

import cv2
import numpy as np
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from datetime import datetime

@dataclass
class PIKElement:
    """Элемент PIK фреймворка"""
    text: str
    category: str  # 'stakeholder', 'core', 'network', 'value', 'support'
    subcategory: str  # конкретный тип блока
    grid_row: int
    grid_col: int
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    is_header: bool = False
    is_noise: bool = False

@dataclass
class PIKGrid:
    """Структура PIK Canvas"""
    rows: int = 6
    cols: int = 3
    cell_width: float = 0
    cell_height: float = 0
    canvas_bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)

class SmartPIKParser:
    """Умный парсер PIK структур"""
    
    def __init__(self):
        # PIK терминология и классификация
        self.pik_categories = {
            'stakeholders': {
                'keywords': ['SUPPLIERS', 'INVESTORS', 'SUPPORTERS', 'PARTNERS'],
                'position': 'left_column',
                'color': '#f4f4f4'
            },
            'capabilities': {
                'keywords': ['KEY PEOPLE', 'KEY DATA', 'KEY INFRASTRUCTURE', 'SKILLS'],
                'position': 'left_center',
                'color': '#e6f3ff'
            },
            'core_services': {
                'keywords': ['CORE SERVICES', 'VALUE PROPOSITION', 'CORE VALUE'],
                'position': 'center',
                'color': '#e6f7ff'
            },
            'touchpoints': {
                'keywords': ['TOUCHPOINTS', 'EXPERIENCE', 'MISSION'],
                'position': 'right_center', 
                'color': '#fff2e6'
            },
            'network_effects': {
                'keywords': ['CONSUMERS', 'PRODUCERS', 'NETWORK EFFECTS'],
                'position': 'right_column',
                'color': '#f0f8e6'
            },
            'economics': {
                'keywords': ['COST STRUCTURE', 'VALUE CAPTURE', 'ECOSYSTEM IMPACT'],
                'position': 'bottom_row',
                'color': '#fff9e6'
            }
        }
        
        # Шаблоны для фильтрации шума
        self.noise_patterns = [
            r'^[^\w\s]{1,3}$',  # Только символы
            r'^\s*$',  # Пустые строки
            r'^[0-9]{1,2}$',  # Одиночные числа
            r'^[a-zA-Z]{1,2}$',  # Одиночные буквы
            r'arrow|line|shape|connector',  # Артефакты рисования
            r'png|jpg|jpeg|pdf',  # Расширения файлов
        ]
        
    def detect_pik_grid(self, image: np.ndarray) -> PIKGrid:
        """Определение табличной структуры PIK Canvas"""
        height, width = image.shape[:2]
        
        # Конвертируем в grayscale для анализа
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Определяем границы таблицы через контуры
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Найти горизонтальные и вертикальные линии
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
        
        # Объединяем линии
        table_structure = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
        
        # Находим контуры таблицы
        contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Берем самый большой контур как границы таблицы
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            canvas_bounds = (x, y, w, h)
        else:
            # Fallback: используем всё изображение
            canvas_bounds = (0, 0, width, height)
            
        # Рассчитываем размеры ячеек
        cell_width = canvas_bounds[2] / 3  # 3 колонки
        cell_height = canvas_bounds[3] / 6  # 6 строк
        
        return PIKGrid(
            rows=6,
            cols=3, 
            cell_width=cell_width,
            cell_height=cell_height,
            canvas_bounds=canvas_bounds
        )
    
    def classify_element(self, text: str, bbox: Tuple[int, int, int, int], grid: PIKGrid) -> PIKElement:
        """Классификация элемента по PIK категориям"""
        
        # Фильтрация шума
        is_noise = self.is_noise(text)
        if is_noise:
            return PIKElement(
                text=text,
                category='noise',
                subcategory='artifact',
                grid_row=-1,
                grid_col=-1,
                bbox=bbox,
                confidence=0.0,
                is_noise=True
            )
        
        # Определение позиции в сетке
        x, y, w, h = bbox
        if grid.cell_width > 0 and grid.cell_height > 0:
            grid_col = min(int((x - grid.canvas_bounds[0]) / grid.cell_width), 2)
            grid_row = min(int((y - grid.canvas_bounds[1]) / grid.cell_height), 5)
        else:
            # Fallback для случая когда сетка не определена
            grid_col = min(int(x / 300), 2)  # Предполагаем ширину ячейки 300px
            grid_row = min(int(y / 120), 5)  # Предполагаем высоту ячейки 120px
        
        # Классификация по содержанию
        category, subcategory, confidence = self.classify_by_content(text)
        
        # Корректировка на основе позиции
        if confidence < 0.7:
            category, subcategory = self.classify_by_position(grid_row, grid_col)
            confidence = 0.6
            
        # Определение заголовков
        is_header = self.is_header_text(text)
        
        return PIKElement(
            text=text.strip(),
            category=category,
            subcategory=subcategory,
            grid_row=grid_row,
            grid_col=grid_col,
            bbox=bbox,
            confidence=confidence,
            is_header=is_header
        )
    
    def is_noise(self, text: str) -> bool:
        """Проверка на визуальный шум"""
        if not text or len(text.strip()) < 2:
            return True
            
        for pattern in self.noise_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        return False
    
    def classify_by_content(self, text: str) -> Tuple[str, str, float]:
        """Классификация по содержанию текста"""
        text_upper = text.upper()
        
        best_match = None
        best_score = 0.0
        
        for category, info in self.pik_categories.items():
            for keyword in info['keywords']:
                if keyword in text_upper:
                    score = len(keyword) / len(text_upper)  # Относительная длина совпадения
                    if score > best_score:
                        best_score = score
                        best_match = (category, keyword.lower().replace(' ', '_'))
        
        if best_match:
            return best_match[0], best_match[1], best_score
        else:
            return 'unknown', 'unclassified', 0.0
    
    def classify_by_position(self, row: int, col: int) -> Tuple[str, str]:
        """Классификация по позиции в сетке"""
        # PIK Business Model Canvas layout
        position_map = {
            # Левая колонка (col=0)
            (0, 0): ('stakeholders', 'suppliers'),
            (1, 0): ('stakeholders', 'investors'), 
            (2, 0): ('stakeholders', 'supporters'),
            (5, 0): ('economics', 'cost_structure'),
            
            # Центральная колонка (col=1)
            (0, 1): ('capabilities', 'key_people'),
            (1, 1): ('capabilities', 'key_data'),
            (2, 1): ('capabilities', 'key_infrastructure'),
            (3, 1): ('core_services', 'mission'),
            (4, 1): ('core_services', 'core_value'),
            (5, 1): ('economics', 'ecosystem_impact'),
            
            # Правая колонка (col=2)
            (0, 2): ('core_services', 'core_services'),
            (1, 2): ('core_services', 'value_proposition'),
            (2, 2): ('touchpoints', 'touchpoints'),
            (3, 2): ('network_effects', 'consumers'),
            (4, 2): ('network_effects', 'network_effects'),
            (5, 2): ('economics', 'value_capture'),
        }
        
        return position_map.get((row, col), ('unknown', 'unclassified'))
    
    def is_header_text(self, text: str) -> bool:
        """Определение заголовков"""
        # Заголовки обычно короткие и состоят из заглавных букв
        if len(text) > 50:
            return False
            
        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        return uppercase_ratio > 0.6
    
    def generate_structured_drawio(self, elements: List[PIKElement], grid: PIKGrid) -> str:
        """Генерация структурированного Draw.io XML"""
        
        # Фильтруем шум
        clean_elements = [e for e in elements if not e.is_noise and e.confidence > 0.3]
        
        # Создаем XML структуру
        mxfile = ET.Element('mxfile', host='app.diagrams.net', modified='2025-09-06T12:00:00.000Z')
        diagram = ET.SubElement(mxfile, 'diagram', id='PIK_Canvas', name='PIK Business Model')
        mxGraphModel = ET.SubElement(diagram, 'mxGraphModel', dx='1426', dy='827', grid='1', 
                                   gridSize='10', guides='1', tooltips='1', connect='1',
                                   arrows='1', fold='1', page='1', pageScale='1', pageWidth='1169',
                                   pageHeight='827', background='#ffffff')
        
        root = ET.SubElement(mxGraphModel, 'root')
        ET.SubElement(root, 'mxCell', id='0')
        ET.SubElement(root, 'mxCell', id='1', parent='0')
        
        # Параметры для позиционирования
        start_x = 40
        start_y = 40
        cell_width = 300
        cell_height = 120
        margin = 20
        
        # Группируем элементы по позиции в сетке
        grid_elements = {}
        for element in clean_elements:
            if element.grid_row >= 0 and element.grid_col >= 0:
                key = (element.grid_row, element.grid_col)
                if key not in grid_elements:
                    grid_elements[key] = []
                grid_elements[key].append(element)
        
        cell_id = 2
        
        # Создаем ячейки для каждой позиции в сетке
        for row in range(6):
            for col in range(3):
                elements_in_cell = grid_elements.get((row, col), [])
                
                if elements_in_cell:
                    # Вычисляем позицию
                    x = start_x + col * (cell_width + margin)
                    y = start_y + row * (cell_height + margin)
                    
                    # Определяем цвет на основе категории
                    main_element = max(elements_in_cell, key=lambda e: e.confidence)
                    color = self.get_color_for_category(main_element.category)
                    
                    # Объединяем текст элементов
                    combined_text = self.combine_cell_text(elements_in_cell)
                    
                    # Создаем ячейку
                    cell = ET.SubElement(root, 'mxCell', 
                                       id=str(cell_id),
                                       value=self.escape_xml(combined_text),
                                       style=f'rounded=1;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#d6b656;fontStyle=1;fontSize=11;',
                                       vertex='1',
                                       parent='1')
                    
                    geometry = ET.SubElement(cell, 'mxGeometry',
                                           x=str(x), y=str(y),
                                           width=str(cell_width), height=str(cell_height),
                                           **{'as': 'geometry'})
                    
                    cell_id += 1
        
        # Добавляем заголовок
        title_cell = ET.SubElement(root, 'mxCell',
                                 id=str(cell_id),
                                 value='PLATFORM BUSINESS MODEL v5.0',
                                 style='text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontStyle=1;',
                                 vertex='1',
                                 parent='1')
        
        title_geometry = ET.SubElement(title_cell, 'mxGeometry',
                                     x='340', y='10',
                                     width='400', height='30',
                                     **{'as': 'geometry'})
        
        # Конвертируем в строку
        ET.indent(mxfile, space='  ')
        return ET.tostring(mxfile, encoding='unicode', xml_declaration=True)
    
    def combine_cell_text(self, elements: List[PIKElement]) -> str:
        """Объединение текста элементов в ячейке"""
        # Сортируем: заголовки вверх, потом по уверенности
        elements.sort(key=lambda e: (not e.is_header, -e.confidence))
        
        lines = []
        for element in elements:
            if element.is_header:
                lines.append(f"<b>{element.text}</b>")
            else:
                lines.append(element.text)
        
        return "<br/>".join(lines)
    
    def get_color_for_category(self, category: str) -> str:
        """Получение цвета для категории"""
        color_map = {
            'stakeholders': '#f4f4f4',
            'capabilities': '#e6f3ff', 
            'core_services': '#e6f7ff',
            'touchpoints': '#fff2e6',
            'network_effects': '#f0f8e6',
            'economics': '#fff9e6',
            'unknown': '#ffffff'
        }
        return color_map.get(category, '#ffffff')
    
    def escape_xml(self, text: str) -> str:
        """Экранирование XML сущностей"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))

def main():
    """Демонстрация улучшенного парсера"""
    print("🚀 Smart PIK Parser v2.0")
    print("========================")
    
    parser = SmartPIKParser()
    
    # Пример использования
    sample_elements = [
        ("SUPPLIERS", (50, 50, 200, 80)),
        ("INVESTORS", (50, 150, 200, 80)),
        ("KEY PEOPLE & SKILLS", (300, 50, 200, 80)),
        ("CORE SERVICES", (550, 50, 200, 80)),
        ("arrow_artifact", (100, 100, 20, 20)),  # Шум
        ("CONSUMERS", (550, 250, 200, 80)),
    ]
    
    # Создаем фиктивную сетку
    grid = PIKGrid(
        rows=6, 
        cols=3,
        cell_width=300,
        cell_height=120,
        canvas_bounds=(0, 0, 900, 720)
    )
    
    # Классифицируем элементы
    classified = []
    for text, bbox in sample_elements:
        element = parser.classify_element(text, bbox, grid)
        classified.append(element)
        print(f"📊 {element.text}: {element.category}/{element.subcategory} "
              f"(confidence: {element.confidence:.2f}, noise: {element.is_noise})")
    
    # Генерируем Draw.io
    drawio_xml = parser.generate_structured_drawio(classified, grid)
    
    # Сохраняем результат
    output_path = Path("output/drawio/smart_pik_demo.drawio")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(drawio_xml)
    
    print(f"✅ Структурированная диаграмма сохранена: {output_path}")
    print(f"📊 Обработано элементов: {len(classified)}")
    print(f"🗑️ Отфильтровано шума: {sum(1 for e in classified if e.is_noise)}")

if __name__ == "__main__":
    main()
