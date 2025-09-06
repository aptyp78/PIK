#!/usr/bin/env python3
"""
PIK Layout Enhancer
===================

Интеграция Smart PIK Parser с существующим OCR pipeline
для исправления проблем layout'а в Draw.io диаграммах.
"""

import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import argparse
from smart_pik_parser import SmartPIKParser, PIKElement
from datetime import datetime

class PIKLayoutEnhancer:
    """Улучшение layout'а существующих PIK диаграмм"""
    
    def __init__(self):
        self.parser = SmartPIKParser()
        
    def enhance_existing_analysis(self, analysis_file: Path) -> Dict[str, Any]:
        """Улучшение существующего анализа PIK"""
        
        # Загружаем существующий анализ
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        print(f"📊 Загружен анализ: {analysis_file.name}")
        
        # Проверяем структуру данных - новый формат или старый
        elements_data = []
        if 'elements' in analysis:
            # Новый формат - используем поле 'elements'
            elements_data = analysis['elements']
            print(f"📝 Найдено элементов (новый формат): {len(elements_data)}")
        elif 'extracted_elements' in analysis:
            # Старый формат - используем поле 'extracted_elements'
            elements_data = analysis['extracted_elements']
            print(f"📝 Найдено элементов (старый формат): {len(elements_data)}")
        else:
            print("❌ Элементы не найдены в анализе")
            return analysis
        
        # Загружаем исходное изображение
        source_image_path = analysis.get('source_image', '')
        
        # Если нет source_image, попробуем определить по ID
        if not source_image_path:
            analysis_id = analysis.get('id', '')
            if analysis_id:
                # Пытаемся найти соответствующее изображение
                possible_paths = [
                    f"_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Platform Business Model - ENG.png",
                    f"_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Platform Experience - ENG.png", 
                    f"_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Ecosystem Forces Scan - ENG.png",
                    f"_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - NFX Reinforcement Engines - ENG.png",
                    f"_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Platform Value Network Canvas - ENG.png"
                ]
                
                for path in possible_paths:
                    if Path(path).exists():
                        source_image_path = path
                        break
        
        if not source_image_path or not Path(source_image_path).exists():
            print(f"❌ Исходное изображение не найдено: {source_image_path}")
            # Используем фиктивное изображение для демонстрации алгоритма
            image = np.zeros((800, 1200, 3), dtype=np.uint8)  # Белое изображение
            print("🖼️ Используем фиктивное изображение для демонстрации")
        else:
            image = cv2.imread(source_image_path)
            if image is None:
                print(f"❌ Не удалось загрузить изображение: {source_image_path}")
                return analysis
            print(f"🖼️ Загружено изображение: {image.shape}")
        
        print(f"🖼️ Размер изображения: {image.shape}")
        
        # Определяем сетку PIK
        grid = self.parser.detect_pik_grid(image)
        print(f"📐 Определена сетка: {grid.rows}x{grid.cols}, ячейка: {grid.cell_width:.0f}x{grid.cell_height:.0f}")
        
        # Конвертируем элементы в PIKElement
        elements = []
        for elem in elements_data:
            # Поддерживаем оба формата данных
            if 'position' in elem:
                # Новый формат: position = [x, y, width, height]
                pos = elem['position']
                bbox = (pos[0], pos[1], pos[2], pos[3])
                text = elem.get('text', '')
            else:
                # Старый формат: отдельные поля x, y, width, height
                bbox = (
                    elem.get('x', 0),
                    elem.get('y', 0), 
                    elem.get('width', 100),
                    elem.get('height', 50)
                )
                text = elem.get('text', '')
            
            # Классифицируем с помощью Smart Parser
            pik_element = self.parser.classify_element(text, bbox, grid)
            elements.append(pik_element)
        
        # Фильтруем и улучшаем
        clean_elements = self.filter_and_improve_elements(elements)
        print(f"🧹 После очистки: {len(clean_elements)} элементов")
        print(f"🗑️ Удалено шума: {len(elements) - len(clean_elements)}")
        
        # Генерируем улучшенный Draw.io
        improved_drawio = self.parser.generate_structured_drawio(clean_elements, grid)
        
        # Обновляем анализ
        enhanced_analysis = analysis.copy()
        enhanced_analysis.update({
            'enhanced_timestamp': datetime.now().isoformat(),
            'enhanced_by': 'smart_pik_parser_v2',
            'grid_detection': {
                'rows': grid.rows,
                'cols': grid.cols,
                'cell_width': grid.cell_width,
                'cell_height': grid.cell_height,
                'canvas_bounds': grid.canvas_bounds
            },
            'element_classification': [
                {
                    'text': elem.text,
                    'category': elem.category,
                    'subcategory': elem.subcategory,
                    'grid_position': [elem.grid_row, elem.grid_col],
                    'confidence': elem.confidence,
                    'is_header': elem.is_header,
                    'is_noise': elem.is_noise
                }
                for elem in clean_elements
            ],
            'improved_drawio_xml': improved_drawio,
            'quality_metrics': self.calculate_quality_metrics(clean_elements)
        })
        
        return enhanced_analysis
    
    def filter_and_improve_elements(self, elements: List[PIKElement]) -> List[PIKElement]:
        """Фильтрация и улучшение элементов"""
        
        # Удаляем шум
        clean_elements = [e for e in elements if not e.is_noise and e.confidence > 0.2]
        
        # Группируем по позиции в сетке для устранения дубликатов
        grid_groups = {}
        for elem in clean_elements:
            key = (elem.grid_row, elem.grid_col)
            if key not in grid_groups:
                grid_groups[key] = []
            grid_groups[key].append(elem)
        
        # Выбираем лучший элемент из каждой группы или объединяем
        improved_elements = []
        for (row, col), group in grid_groups.items():
            if len(group) == 1:
                improved_elements.append(group[0])
            else:
                # Объединяем элементы в одной ячейке
                merged = self.merge_elements_in_cell(group)
                improved_elements.append(merged)
        
        return improved_elements
    
    def merge_elements_in_cell(self, elements: List[PIKElement]) -> PIKElement:
        """Объединение элементов в одной ячейке"""
        
        # Сортируем по уверенности
        elements.sort(key=lambda e: e.confidence, reverse=True)
        best_element = elements[0]
        
        # Объединяем текст
        texts = [e.text for e in elements if len(e.text.strip()) > 2]
        combined_text = " | ".join(texts)
        
        # Усредняем bbox
        avg_x = sum(e.bbox[0] for e in elements) / len(elements)
        avg_y = sum(e.bbox[1] for e in elements) / len(elements)
        max_w = max(e.bbox[2] for e in elements)
        max_h = max(e.bbox[3] for e in elements)
        
        return PIKElement(
            text=combined_text,
            category=best_element.category,
            subcategory=best_element.subcategory,
            grid_row=best_element.grid_row,
            grid_col=best_element.grid_col,
            bbox=(int(avg_x), int(avg_y), int(max_w), int(max_h)),
            confidence=best_element.confidence,
            is_header=any(e.is_header for e in elements)
        )
    
    def calculate_quality_metrics(self, elements: List[PIKElement]) -> Dict[str, Any]:
        """Расчет метрик качества"""
        
        total_elements = len(elements)
        if total_elements == 0:
            return {'score': 0, 'issues': ['No elements found']}
        
        # Подсчет по категориям
        categories = {}
        confidence_scores = []
        grid_coverage = set()
        
        for elem in elements:
            categories[elem.category] = categories.get(elem.category, 0) + 1
            confidence_scores.append(elem.confidence)
            grid_coverage.add((elem.grid_row, elem.grid_col))
        
        # Метрики
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        grid_coverage_pct = len(grid_coverage) / 18 * 100  # 18 ячеек в PIK Canvas
        category_balance = len(categories) / 6 * 100  # 6 основных категорий PIK
        
        # Итоговый скор
        score = (avg_confidence * 40 + grid_coverage_pct * 30 + category_balance * 30)
        
        return {
            'overall_score': round(score, 1),
            'avg_confidence': round(avg_confidence, 2),
            'grid_coverage_percent': round(grid_coverage_pct, 1),
            'category_balance_percent': round(category_balance, 1),
            'categories_found': list(categories.keys()),
            'total_elements': total_elements,
            'grid_cells_used': len(grid_coverage)
        }
    
    def enhance_all_analyses(self, analysis_dir: Path, output_dir: Path):
        """Улучшение всех анализов в директории"""
        
        analysis_files = list(analysis_dir.glob("*_analysis.json"))
        print(f"🔍 Найдено файлов анализа: {len(analysis_files)}")
        
        results = []
        
        for analysis_file in analysis_files:
            try:
                print(f"\n🚀 Обрабатываем: {analysis_file.name}")
                
                enhanced = self.enhance_existing_analysis(analysis_file)
                
                # Сохраняем улучшенный анализ
                output_file = output_dir / f"enhanced_{analysis_file.name}"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced, f, indent=2, ensure_ascii=False)
                
                # Сохраняем улучшенный Draw.io
                if 'improved_drawio_xml' in enhanced:
                    drawio_file = output_dir / f"enhanced_{analysis_file.stem}.drawio"
                    with open(drawio_file, 'w', encoding='utf-8') as f:
                        f.write(enhanced['improved_drawio_xml'])
                
                quality = enhanced.get('quality_metrics', {})
                results.append({
                    'file': analysis_file.name,
                    'score': quality.get('overall_score', 0),
                    'elements': quality.get('total_elements', 0),
                    'grid_coverage': quality.get('grid_coverage_percent', 0)
                })
                
                print(f"✅ Обработан: {analysis_file.name}")
                print(f"📊 Скор качества: {quality.get('overall_score', 0)}/100")
                
            except Exception as e:
                print(f"❌ Ошибка при обработке {analysis_file.name}: {e}")
                results.append({
                    'file': analysis_file.name,
                    'error': str(e)
                })
        
        # Сохраняем сводку результатов
        summary_file = output_dir / "enhancement_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(analysis_files),
                'results': results,
                'avg_score': sum(r.get('score', 0) for r in results) / len(results) if results else 0
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎯 ИТОГИ УЛУЧШЕНИЯ:")
        print(f"📁 Обработано файлов: {len(analysis_files)}")
        print(f"✅ Успешно: {len([r for r in results if 'error' not in r])}")
        print(f"❌ Ошибок: {len([r for r in results if 'error' in r])}")
        avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
        print(f"📊 Средний скор качества: {avg_score:.1f}/100")

def main():
    """CLI интерфейс"""
    parser = argparse.ArgumentParser(description='PIK Layout Enhancer')
    parser.add_argument('--input-dir', type=Path, default='data/output/analysis',
                       help='Директория с файлами анализа')
    parser.add_argument('--output-dir', type=Path, default='output/enhanced',
                       help='Директория для сохранения результатов')
    parser.add_argument('--single-file', type=Path,
                       help='Обработать один файл')
    
    args = parser.parse_args()
    
    enhancer = PIKLayoutEnhancer()
    
    # Создаем выходную директорию
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎨 PIK Layout Enhancer v2.0")
    print("============================")
    
    if args.single_file:
        # Обработка одного файла
        enhanced = enhancer.enhance_existing_analysis(args.single_file)
        output_file = args.output_dir / f"enhanced_{args.single_file.name}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Результат сохранен: {output_file}")
    else:
        # Обработка всей директории
        enhancer.enhance_all_analyses(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()
