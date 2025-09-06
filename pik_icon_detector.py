#!/usr/bin/env python3
"""
Система распознавания и идентификации иконок в PIK диаграммах.
Находит, извлекает и классифицирует иконки как отдельные объекты.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import json
from datetime import datetime
import math

class PIKIconDetector:
    """Детектор и классификатор иконок в PIK диаграммах"""
    
    def __init__(self):
        self.icon_templates = self._load_icon_templates()
        self.detected_icons = []
        
    def _load_icon_templates(self):
        """Загружает шаблоны известных PIK иконок"""
        # Определяем базовые типы PIK иконок
        templates = {
            'arrow': {
                'description': 'Стрелка направления',
                'category': 'navigation',
                'shapes': ['triangle', 'pointed']
            },
            'circle': {
                'description': 'Круглая иконка',
                'category': 'container',
                'shapes': ['circle', 'ellipse']
            },
            'rectangle': {
                'description': 'Прямоугольная рамка',
                'category': 'container',
                'shapes': ['rectangle', 'square']
            },
            'diamond': {
                'description': 'Ромб/алмаз',
                'category': 'decision',
                'shapes': ['diamond', 'rhombus']
            },
            'star': {
                'description': 'Звезда/важность',
                'category': 'emphasis',
                'shapes': ['star', 'cross']
            },
            'gear': {
                'description': 'Шестеренка/процесс',
                'category': 'process',
                'shapes': ['gear', 'cog']
            },
            'person': {
                'description': 'Человек/стейкхолдер',
                'category': 'stakeholder',
                'shapes': ['person', 'figure']
            },
            'building': {
                'description': 'Здание/организация',
                'category': 'organization',
                'shapes': ['building', 'structure']
            },
            'network': {
                'description': 'Сеть/связи',
                'category': 'connection',
                'shapes': ['network', 'web']
            },
            'money': {
                'description': 'Деньги/финансы',
                'category': 'financial',
                'shapes': ['dollar', 'coin', 'money']
            }
        }
        return templates
    
    def detect_geometric_shapes(self, image_path):
        """Детектирует геометрические фигуры как потенциальные иконки"""
        
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        # Конвертируем в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Применяем различные методы детекции
        shapes = []
        
        # 1. Детекция кругов (Hough Circle Transform)
        circles = self._detect_circles(gray)
        shapes.extend(circles)
        
        # 2. Детекция прямоугольников и квадратов
        rectangles = self._detect_rectangles(gray)
        shapes.extend(rectangles)
        
        # 3. Детекция треугольников и стрелок
        triangles = self._detect_triangles(gray)
        shapes.extend(triangles)
        
        # 4. Детекция сложных форм (контуры)
        complex_shapes = self._detect_complex_shapes(gray)
        shapes.extend(complex_shapes)
        
        # 5. Детекция символов и иконок через анализ контуров
        symbols = self._detect_symbols(gray)
        shapes.extend(symbols)
        
        return shapes
    
    def _detect_circles(self, gray):
        """Детектирует круглые иконки"""
        circles_found = []
        
        # Применяем размытие для лучшего детектирования
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Hough Circle Transform с различными параметрами
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            for (x, y, r) in circles:
                # Извлекаем область вокруг круга
                roi = gray[max(0, y-r-5):min(gray.shape[0], y+r+5), 
                          max(0, x-r-5):min(gray.shape[1], x+r+5)]
                
                if roi.size > 0:
                    icon_data = {
                        'type': 'circle',
                        'description': 'Круглая иконка',
                        'category': 'container',
                        'coordinates': (x-r, y-r, x+r, y+r),
                        'center': (x, y),
                        'radius': r,
                        'confidence': self._calculate_circle_confidence(roi),
                        'roi': roi
                    }
                    circles_found.append(icon_data)
        
        return circles_found
    
    def _detect_rectangles(self, gray):
        """Детектирует прямоугольные иконки"""
        rectangles_found = []
        
        # Детекция краев
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Найти контуры
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Аппроксимация контура
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Проверяем, является ли это прямоугольником
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                
                # Фильтруем по размеру (иконки должны быть разумного размера)
                if 10 <= w <= 200 and 10 <= h <= 200:
                    # Проверяем соотношение сторон
                    aspect_ratio = float(w) / h
                    area = cv2.contourArea(contour)
                    rect_area = w * h
                    extent = float(area) / rect_area
                    
                    # Извлекаем ROI
                    roi = gray[y:y+h, x:x+w]
                    
                    if roi.size > 0:
                        icon_type = 'square' if 0.8 <= aspect_ratio <= 1.2 else 'rectangle'
                        
                        icon_data = {
                            'type': icon_type,
                            'description': f'{"Квадратная" if icon_type == "square" else "Прямоугольная"} иконка',
                            'category': 'container',
                            'coordinates': (x, y, x+w, y+h),
                            'dimensions': (w, h),
                            'aspect_ratio': aspect_ratio,
                            'extent': extent,
                            'confidence': min(100, extent * 100),
                            'roi': roi
                        }
                        rectangles_found.append(icon_data)
        
        return rectangles_found
    
    def _detect_triangles(self, gray):
        """Детектирует треугольные иконки и стрелки"""
        triangles_found = []
        
        # Детекция краев
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Найти контуры
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Аппроксимация контура
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Проверяем, является ли это треугольником
            if len(approx) == 3:
                x, y, w, h = cv2.boundingRect(approx)
                
                # Фильтруем по размеру
                if 8 <= w <= 150 and 8 <= h <= 150:
                    area = cv2.contourArea(contour)
                    
                    if area > 50:  # Минимальная площадь
                        # Извлекаем ROI
                        roi = gray[y:y+h, x:x+w]
                        
                        if roi.size > 0:
                            # Определяем тип треугольника
                            aspect_ratio = float(w) / h
                            icon_type = 'arrow' if aspect_ratio > 1.5 or aspect_ratio < 0.67 else 'triangle'
                            
                            icon_data = {
                                'type': icon_type,
                                'description': f'{"Стрелка" if icon_type == "arrow" else "Треугольная иконка"}',
                                'category': 'navigation' if icon_type == 'arrow' else 'geometric',
                                'coordinates': (x, y, x+w, y+h),
                                'dimensions': (w, h),
                                'area': area,
                                'confidence': min(100, (area / (w * h)) * 100),
                                'roi': roi
                            }
                            triangles_found.append(icon_data)
        
        return triangles_found
    
    def _detect_complex_shapes(self, gray):
        """Детектирует сложные формы (звезды, ромбы, etc.)"""
        complex_shapes = []
        
        # Детекция краев
        edges = cv2.Canny(gray, 30, 100)
        
        # Найти контуры
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Аппроксимация контура
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Анализируем сложные формы
            if 5 <= len(approx) <= 20:  # Сложные многоугольники
                x, y, w, h = cv2.boundingRect(approx)
                
                if 10 <= w <= 100 and 10 <= h <= 100:
                    area = cv2.contourArea(contour)
                    hull = cv2.convexHull(contour)
                    hull_area = cv2.contourArea(hull)
                    
                    # Определяем тип по количеству углов и выпуклости
                    if area > 0 and hull_area > 0:
                        solidity = float(area) / hull_area
                        
                        # Извлекаем ROI
                        roi = gray[y:y+h, x:x+w]
                        
                        if roi.size > 0:
                            # Классифицируем форму
                            if len(approx) == 4 and solidity < 0.8:
                                shape_type = 'diamond'
                                description = 'Ромб'
                                category = 'decision'
                            elif len(approx) >= 8 and solidity < 0.6:
                                shape_type = 'star'
                                description = 'Звезда'
                                category = 'emphasis'
                            elif len(approx) >= 6:
                                shape_type = 'complex_polygon'
                                description = 'Сложная форма'
                                category = 'special'
                            else:
                                continue
                            
                            icon_data = {
                                'type': shape_type,
                                'description': description,
                                'category': category,
                                'coordinates': (x, y, x+w, y+h),
                                'vertices': len(approx),
                                'solidity': solidity,
                                'confidence': min(100, solidity * 100),
                                'roi': roi
                            }
                            complex_shapes.append(icon_data)
        
        return complex_shapes
    
    def _detect_symbols(self, gray):
        """Детектирует специфические символы и иконки"""
        symbols_found = []
        
        # Создаем различные структурирующие элементы для морфологических операций
        kernel_cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
        kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        
        # Применяем пороговую обработку
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Инвертируем если нужно (темные символы на светлом фоне)
        if np.mean(binary) > 127:
            binary = cv2.bitwise_not(binary)
        
        # Морфологические операции для выделения символов
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_cross)
        
        # Найти контуры
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Фильтруем по размеру (символы должны быть компактными)
            if 8 <= w <= 80 and 8 <= h <= 80:
                area = cv2.contourArea(contour)
                
                if area > 30:
                    # Извлекаем ROI
                    roi = gray[y:y+h, x:x+w]
                    roi_binary = binary[y:y+h, x:x+w]
                    
                    if roi.size > 0:
                        # Анализируем плотность символа
                        density = np.sum(roi_binary > 0) / (w * h)
                        
                        # Анализируем моменты для классификации
                        moments = cv2.moments(contour)
                        
                        if moments['m00'] > 0:
                            # Центроид
                            cx = int(moments['m10'] / moments['m00'])
                            cy = int(moments['m01'] / moments['m00'])
                            
                            # Классифицируем символ по характеристикам
                            symbol_type = self._classify_symbol(roi_binary, density, w, h)
                            
                            icon_data = {
                                'type': symbol_type['type'],
                                'description': symbol_type['description'],
                                'category': symbol_type['category'],
                                'coordinates': (x, y, x+w, y+h),
                                'centroid': (cx, cy),
                                'density': density,
                                'confidence': symbol_type['confidence'],
                                'roi': roi
                            }
                            symbols_found.append(icon_data)
        
        return symbols_found
    
    def _classify_symbol(self, roi_binary, density, width, height):
        """Классифицирует символ по его характеристикам"""
        
        aspect_ratio = float(width) / height
        
        # Анализ плотности и формы
        if 0.1 <= density <= 0.3:
            if 0.8 <= aspect_ratio <= 1.2:
                return {
                    'type': 'ring',
                    'description': 'Кольцо/окружность',
                    'category': 'container',
                    'confidence': 75
                }
            else:
                return {
                    'type': 'frame',
                    'description': 'Рамка',
                    'category': 'container',
                    'confidence': 70
                }
        
        elif 0.3 <= density <= 0.6:
            if aspect_ratio > 2:
                return {
                    'type': 'line',
                    'description': 'Линия/разделитель',
                    'category': 'separator',
                    'confidence': 80
                }
            elif 0.8 <= aspect_ratio <= 1.2:
                return {
                    'type': 'dot',
                    'description': 'Точка/маркер',
                    'category': 'marker',
                    'confidence': 85
                }
            else:
                return {
                    'type': 'symbol',
                    'description': 'Специальный символ',
                    'category': 'special',
                    'confidence': 65
                }
        
        elif density > 0.6:
            if 0.8 <= aspect_ratio <= 1.2:
                return {
                    'type': 'filled_circle',
                    'description': 'Заполненный круг',
                    'category': 'marker',
                    'confidence': 90
                }
            else:
                return {
                    'type': 'filled_shape',
                    'description': 'Заполненная форма',
                    'category': 'emphasis',
                    'confidence': 85
                }
        
        else:
            return {
                'type': 'unknown_symbol',
                'description': 'Неизвестный символ',
                'category': 'unknown',
                'confidence': 40
            }
    
    def _calculate_circle_confidence(self, roi):
        """Вычисляет уверенность для круглых объектов"""
        if roi.size == 0:
            return 0
        
        # Применяем пороговую обработку
        _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Находим контуры
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return 30
        
        # Берем самый большой контур
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Проверяем "круглость"
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            return min(100, circularity * 100)
        
        return 30
    
    def analyze_image(self, image_path, output_dir="icon_detection_results"):
        """Основная функция анализа изображения для поиска иконок"""
        
        print(f"🔍 Анализ иконок в изображении: {Path(image_path).name}")
        
        # Создаем директорию для результатов
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Детектируем все типы фигур
        all_icons = self.detect_geometric_shapes(image_path)
        
        # Фильтруем и сортируем по уверенности
        filtered_icons = [icon for icon in all_icons if icon['confidence'] > 40]
        filtered_icons.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Сохраняем найденные иконки как отдельные изображения
        self._save_detected_icons(filtered_icons, image_path, output_dir)
        
        # Создаем аннотированное изображение
        annotated_image = self._create_annotated_image(image_path, filtered_icons, output_dir)
        
        # Создаем детальный отчет
        report = self._create_detection_report(filtered_icons, image_path, output_dir)
        
        print(f"✅ Найдено иконок: {len(filtered_icons)}")
        print(f"📁 Результаты сохранены в: {output_dir}")
        
        return {
            'total_icons': len(filtered_icons),
            'icons': filtered_icons,
            'annotated_image': annotated_image,
            'report_file': report
        }
    
    def _save_detected_icons(self, icons, source_image_path, output_dir):
        """Сохраняет каждую найденную иконку как отдельное изображение"""
        
        source_img = cv2.imread(source_image_path)
        
        for i, icon in enumerate(icons):
            x1, y1, x2, y2 = icon['coordinates']
            
            # Добавляем небольшой отступ
            padding = 5
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(source_img.shape[1], x2 + padding)
            y2 = min(source_img.shape[0], y2 + padding)
            
            # Извлекаем иконку
            icon_img = source_img[y1:y2, x1:x2]
            
            if icon_img.size > 0:
                # Сохраняем
                icon_filename = f"icon_{i:03d}_{icon['type']}_{icon['confidence']:.0f}pct.png"
                icon_path = Path(output_dir) / icon_filename
                cv2.imwrite(str(icon_path), icon_img)
                
                icon['saved_path'] = str(icon_path)
    
    def _create_annotated_image(self, source_image_path, icons, output_dir):
        """Создает изображение с аннотациями найденных иконок"""
        
        img = cv2.imread(source_image_path)
        
        # Рисуем рамки вокруг найденных иконок
        for i, icon in enumerate(icons):
            x1, y1, x2, y2 = icon['coordinates']
            
            # Цвет рамки в зависимости от типа
            color_map = {
                'circle': (0, 255, 0),      # Зеленый
                'rectangle': (255, 0, 0),   # Красный
                'square': (255, 0, 0),      # Красный
                'triangle': (0, 0, 255),    # Синий
                'arrow': (0, 255, 255),     # Желтый
                'diamond': (255, 0, 255),   # Магента
                'star': (255, 255, 0),      # Циан
                'symbol': (128, 128, 128),  # Серый
            }
            
            color = color_map.get(icon['type'], (255, 255, 255))
            
            # Рисуем рамку
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # Добавляем подпись
            label = f"{icon['type']} ({icon['confidence']:.0f}%)"
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Сохраняем аннотированное изображение
        annotated_path = Path(output_dir) / f"annotated_{Path(source_image_path).stem}.png"
        cv2.imwrite(str(annotated_path), img)
        
        return str(annotated_path)
    
    def _create_detection_report(self, icons, source_image_path, output_dir):
        """Создает детальный отчет о найденных иконках"""
        
        report_lines = [
            "# 🎯 Отчет по детекции иконок в PIK диаграмме\n\n",
            f"**Исходное изображение:** {Path(source_image_path).name}\n",
            f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**Всего найдено иконок:** {len(icons)}\n\n"
        ]
        
        if not icons:
            report_lines.append("❌ Иконки не найдены\n")
        else:
            # Статистика по типам
            type_counts = {}
            for icon in icons:
                icon_type = icon['type']
                type_counts[icon_type] = type_counts.get(icon_type, 0) + 1
            
            report_lines.append("## 📊 Статистика по типам иконок\n\n")
            for icon_type, count in sorted(type_counts.items()):
                report_lines.append(f"- **{icon_type}**: {count} шт.\n")
            
            report_lines.append("\n## 🔍 Детальный список найденных иконок\n\n")
            
            # Группируем по категориям
            by_category = {}
            for icon in icons:
                category = icon['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(icon)
            
            for category, category_icons in by_category.items():
                report_lines.append(f"### 📂 Категория: {category.title()}\n\n")
                
                for i, icon in enumerate(category_icons, 1):
                    x1, y1, x2, y2 = icon['coordinates']
                    
                    report_lines.append(f"#### {i}. {icon['description']}\n")
                    report_lines.append(f"- **Тип:** {icon['type']}\n")
                    report_lines.append(f"- **Координаты:** ({x1}, {y1}) → ({x2}, {y2})\n")
                    report_lines.append(f"- **Размер:** {x2-x1}×{y2-y1} px\n")
                    report_lines.append(f"- **Уверенность:** {icon['confidence']:.1f}%\n")
                    
                    if 'dimensions' in icon:
                        w, h = icon['dimensions']
                        report_lines.append(f"- **Размеры:** {w}×{h} px\n")
                    
                    if 'aspect_ratio' in icon:
                        report_lines.append(f"- **Соотношение сторон:** {icon['aspect_ratio']:.2f}\n")
                    
                    if 'saved_path' in icon:
                        report_lines.append(f"- **Сохранено:** {Path(icon['saved_path']).name}\n")
                    
                    report_lines.append("\n")
        
        # Сохраняем отчет
        report_path = Path(output_dir) / "icon_detection_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report_lines))
        
        return str(report_path)

def main():
    """Основная функция для запуска детекции иконок"""
    
    print("🚀 ЗАПУСК СИСТЕМЫ ДЕТЕКЦИИ ИКОНОК В PIK ДИАГРАММАХ")
    print("=" * 60)
    
    # Создаем детектор
    detector = PIKIconDetector()
    
    # Ищем изображения для анализа
    image_files = []
    
    # Проверяем OCR директории
    ocr_dirs = list(Path("OCR").glob("*/images/")) if Path("OCR").exists() else []
    
    for ocr_dir in ocr_dirs:
        image_files.extend(list(ocr_dir.glob("*.png")))
    
    if not image_files:
        print("❌ Не найдены изображения для анализа")
        return
    
    # Анализируем каждое изображение
    all_results = {}
    
    for image_file in image_files[:3]:  # Ограничиваем для демонстрации
        print(f"\n📋 Анализируем: {image_file.name}")
        
        try:
            result = detector.analyze_image(
                str(image_file), 
                f"OCR/icon_detection_{image_file.stem}"
            )
            
            all_results[str(image_file)] = result
            
            print(f"   ✅ Найдено иконок: {result['total_icons']}")
            
        except Exception as e:
            print(f"   ❌ Ошибка анализа: {e}")
    
    # Создаем общую сводку
    total_icons = sum(r['total_icons'] for r in all_results.values())
    
    print(f"\n🎉 АНАЛИЗ ЗАВЕРШЕН!")
    print(f"📊 Всего проанализировано изображений: {len(all_results)}")
    print(f"🎯 Всего найдено иконок: {total_icons}")
    
    if total_icons > 0:
        print(f"📁 Результаты сохранены в директориях: OCR/icon_detection_*")
        
        # Показываем топ найденных иконок
        all_icons = []
        for result in all_results.values():
            all_icons.extend(result['icons'])
        
        top_icons = sorted(all_icons, key=lambda x: x['confidence'], reverse=True)[:5]
        
        print(f"\n🏆 Топ-5 лучших находок:")
        for i, icon in enumerate(top_icons, 1):
            print(f"   {i}. {icon['description']} ({icon['confidence']:.1f}% уверенности)")

if __name__ == "__main__":
    main()
