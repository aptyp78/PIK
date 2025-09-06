#!/usr/bin/env python3
"""
Draw.io Quality Tester
======================

Комплексная система тестирования качества Draw.io файлов.
Проверяет backend (XML, структура) и frontend (визуализация, UX) аспекты.
"""

import os
import json
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
import base64
import urllib.parse
import zlib
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import re
from pathlib import Path
import math

@dataclass
class DrawIOQualityIssue:
    """Структура для описания проблемы качества Draw.io"""
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "xml", "structure", "visual", "semantic", "performance", "security"
    issue_type: str
    description: str
    location: str
    suggestion: str
    auto_fixable: bool = False

@dataclass
class DrawIOQualityReport:
    """Отчет о качестве Draw.io файла"""
    filename: str
    overall_score: float  # 0-100
    issues: List[DrawIOQualityIssue]
    stats: Dict
    backend_tests: Dict
    frontend_tests: Dict
    performance_metrics: Dict
    test_timestamp: str

class DrawIOQualityTester:
    """Комплексная система тестирования качества Draw.io файлов"""
    
    def __init__(self):
        self.test_results = []
        self.quality_standards = {
            "min_elements": 5,
            "max_file_size_mb": 10,
            "min_score": 70,
            "required_attributes": ["id", "value", "style"],
            "forbidden_patterns": ["<script", "javascript:", "eval(", "onclick="],
            "encoding_standards": ["UTF-8"],
            "visual_standards": {
                "min_diagram_width": 100,
                "min_diagram_height": 100,
                "max_overlapping_elements": 5,
                "min_font_size": 8,
                "max_font_size": 72
            },
            "pik_keywords": [
                "core value", "stakeholder", "ecosystem", "platform",
                "demand", "supply", "network effects", "value proposition", 
                "experience", "sustainability", "innovation"
            ]
        }
    
    def run_comprehensive_test(self, file_path: str) -> DrawIOQualityReport:
        """Запуск всестороннего тестирования Draw.io файла"""
        print(f"\n🔍 Тестирование: {os.path.basename(file_path)}")
        
        # Backend тесты
        backend_results = self._run_backend_tests(file_path)
        
        # Frontend тесты  
        frontend_results = self._run_frontend_tests(file_path)
        
        # Семантические тесты
        semantic_results = self._run_semantic_tests(file_path)
        
        # Performance тесты
        performance_results = self._run_performance_tests(file_path)
        
        # Безопасность
        security_results = self._run_security_tests(file_path)
        
        # Сбор всех проблем
        all_issues = []
        all_issues.extend(backend_results.get("issues", []))
        all_issues.extend(frontend_results.get("issues", []))
        all_issues.extend(semantic_results.get("issues", []))
        all_issues.extend(performance_results.get("issues", []))
        all_issues.extend(security_results.get("issues", []))
        
        # Расчет общего счета качества
        overall_score = self._calculate_quality_score(all_issues, file_path)
        
        # Статистика
        stats = self._collect_file_stats(file_path)
        
        report = DrawIOQualityReport(
            filename=os.path.basename(file_path),
            overall_score=overall_score,
            issues=all_issues,
            stats=stats,
            backend_tests=backend_results,
            frontend_tests=frontend_results,
            performance_metrics=performance_results,
            test_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return report
    
    def _run_backend_tests(self, file_path: str) -> Dict:
        """Backend тестирование: XML, структура, данные"""
        results = {"status": "unknown", "issues": [], "tests": {}}
        
        print("  🔧 Backend тесты...")
        
        # Тест 1: XML валидность
        xml_test = self._test_xml_validity(file_path)
        results["tests"]["xml_validity"] = xml_test
        if not xml_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="critical",
                category="xml",
                issue_type="xml_invalid",
                description=xml_test["error"],
                location="file_root",
                suggestion="Исправить XML синтаксис",
                auto_fixable=True
            ))
        
        # Тест 2: Кодировка файла
        encoding_test = self._test_file_encoding(file_path)
        results["tests"]["encoding"] = encoding_test
        if not encoding_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="structure",
                issue_type="encoding_issue",
                description=f"Проблема с кодировкой: {encoding_test['detected']}",
                location="file_header",
                suggestion="Конвертировать в UTF-8"
            ))
        
        # Тест 3: Draw.io специфичная структура
        structure_test = self._test_drawio_structure(file_path)
        results["tests"]["structure"] = structure_test
        if not structure_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="high",
                category="structure", 
                issue_type="invalid_structure",
                description=structure_test["error"],
                location="mxfile_root",
                suggestion="Исправить структуру mxfile/diagram"
            ))
        
        # Тест 4: Compressed data тест
        compression_test = self._test_compressed_data(file_path)
        results["tests"]["compression"] = compression_test
        if not compression_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="structure",
                issue_type="compression_issue", 
                description=compression_test["error"],
                location="mxGraphModel",
                suggestion="Проверить сжатие данных диаграммы"
            ))
        
        # Тест 5: Элементы и атрибуты
        elements_test = self._test_diagram_elements(file_path)
        results["tests"]["elements"] = elements_test
        if not elements_test["passed"]:
            results["issues"].extend(elements_test["issues"])
        
        results["status"] = "passed" if len(results["issues"]) == 0 else "failed"
        return results
    
    def _run_frontend_tests(self, file_path: str) -> Dict:
        """Frontend тестирование: визуализация, UI/UX"""
        results = {"status": "unknown", "issues": [], "tests": {}}
        
        print("  🎨 Frontend тесты...")
        
        # Тест 1: Визуальные размеры
        visual_test = self._test_visual_dimensions(file_path)
        results["tests"]["visual_dimensions"] = visual_test
        if not visual_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="visual",
                issue_type="dimension_issue",
                description=visual_test["error"],
                location="diagram_geometry",
                suggestion="Проверить размеры диаграммы"
            ))
        
        # Тест 2: Стили и CSS
        style_test = self._test_element_styles(file_path)
        results["tests"]["styles"] = style_test
        if not style_test["passed"]:
            results["issues"].extend(style_test["issues"])
        
        # Тест 3: Читаемость текста
        readability_test = self._test_text_readability(file_path)
        results["tests"]["readability"] = readability_test
        if not readability_test["passed"]:
            results["issues"].extend(readability_test["issues"])
        
        # Тест 4: Overlapping элементы
        overlap_test = self._test_element_overlapping(file_path)
        results["tests"]["overlapping"] = overlap_test
        if not overlap_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="low",
                category="visual",
                issue_type="overlapping_elements",
                description=f"Найдено {overlap_test['count']} перекрывающихся элементов",
                location="diagram_layout",
                suggestion="Переместить элементы для лучшей читаемости"
            ))
        
        # Тест 5: Связность диаграммы
        connectivity_test = self._test_diagram_connectivity(file_path)
        results["tests"]["connectivity"] = connectivity_test
        if not connectivity_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="visual",
                issue_type="poor_connectivity",
                description=connectivity_test["error"],
                location="diagram_connections",
                suggestion="Добавить больше связей между элементами"
            ))
        
        # Тест 6: Цветовая схема
        color_test = self._test_color_scheme(file_path)
        results["tests"]["color_scheme"] = color_test
        if not color_test["passed"]:
            results["issues"].extend(color_test["issues"])
        
        results["status"] = "passed" if len(results["issues"]) == 0 else "failed"
        return results
    
    def _run_semantic_tests(self, file_path: str) -> Dict:
        """Семантические тесты: соответствие PIK методологии"""
        results = {"status": "unknown", "issues": [], "tests": {}}
        
        print("  🧠 Семантические тесты...")
        
        # Тест 1: PIK элементы
        pik_test = self._test_pik_compliance(file_path)
        results["tests"]["pik_compliance"] = pik_test
        if not pik_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="high",
                category="semantic",
                issue_type="pik_non_compliance",
                description=pik_test["error"],
                location="diagram_content",
                suggestion="Добавить недостающие PIK элементы"
            ))
        
        # Тест 2: Наличие центрального элемента
        center_test = self._test_central_element(file_path)
        results["tests"]["central_element"] = center_test
        if not center_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="high",
                category="semantic",
                issue_type="missing_center",
                description="Не найден центральный элемент диаграммы",
                location="diagram_center",
                suggestion="Добавить центральный элемент (Core Value, Stakeholders и т.д.)"
            ))
        
        # Тест 3: Логические группы
        grouping_test = self._test_logical_grouping(file_path)
        results["tests"]["logical_grouping"] = grouping_test
        if not grouping_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium", 
                category="semantic",
                issue_type="poor_grouping",
                description=grouping_test["error"],
                location="diagram_structure",
                suggestion="Улучшить логическую группировку элементов"
            ))
        
        # Тест 4: Терминология PIK
        terminology_test = self._test_pik_terminology(file_path)
        results["tests"]["pik_terminology"] = terminology_test
        if not terminology_test["passed"]:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="semantic",
                issue_type="incorrect_terminology",
                description=terminology_test["error"],
                location="text_content",
                suggestion="Использовать корректную PIK терминологию"
            ))
        
        results["status"] = "passed" if len(results["issues"]) == 0 else "failed"
        return results
    
    def _run_performance_tests(self, file_path: str) -> Dict:
        """Performance тесты: скорость загрузки, размер файла"""
        results = {"status": "unknown", "issues": [], "metrics": {}}
        
        print("  ⚡ Performance тесты...")
        
        # Метрики файла
        file_size = os.path.getsize(file_path)
        results["metrics"]["file_size_bytes"] = file_size
        results["metrics"]["file_size_mb"] = round(file_size / (1024*1024), 2)
        
        # Тест размера файла
        if file_size > self.quality_standards["max_file_size_mb"] * 1024 * 1024:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="performance",
                issue_type="large_file_size",
                description=f"Файл слишком большой: {results['metrics']['file_size_mb']} MB",
                location="file_size",
                suggestion="Оптимизировать размер файла или разбить на части"
            ))
        
        # Тест времени парсинга
        start_time = time.time()
        try:
            tree = ET.parse(file_path)
            parse_time = time.time() - start_time
            results["metrics"]["parse_time_seconds"] = round(parse_time, 3)
            
            if parse_time > 2.0:  # Больше 2 секунд
                results["issues"].append(DrawIOQualityIssue(
                    severity="medium",
                    category="performance",
                    issue_type="slow_parsing",
                    description=f"Медленный парсинг: {parse_time:.2f} сек",
                    location="xml_structure",
                    suggestion="Упростить структуру XML"
                ))
        except Exception as e:
            results["metrics"]["parse_time_seconds"] = None
            results["issues"].append(DrawIOQualityIssue(
                severity="critical",
                category="performance", 
                issue_type="parse_failure",
                description=f"Ошибка парсинга: {str(e)}",
                location="xml_root",
                suggestion="Исправить XML структуру"
            ))
        
        # Подсчет элементов
        try:
            tree = ET.parse(file_path)
            element_count = len(tree.findall(".//mxCell"))
            results["metrics"]["element_count"] = element_count
            
            if element_count > 1000:
                results["issues"].append(DrawIOQualityIssue(
                    severity="low",
                    category="performance",
                    issue_type="too_many_elements",
                    description=f"Слишком много элементов: {element_count}",
                    location="diagram_content",
                    suggestion="Рассмотреть разбиение на несколько диаграмм"
                ))
        except:
            results["metrics"]["element_count"] = 0
        
        results["status"] = "passed" if len(results["issues"]) == 0 else "failed"
        return results
    
    def _run_security_tests(self, file_path: str) -> Dict:
        """Тесты безопасности: XSS, инъекции"""
        results = {"status": "unknown", "issues": [], "tests": {}}
        
        print("  🔒 Security тесты...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Тест на вредоносный код
            for pattern in self.quality_standards["forbidden_patterns"]:
                if pattern.lower() in content.lower():
                    results["issues"].append(DrawIOQualityIssue(
                        severity="critical",
                        category="security",
                        issue_type="malicious_code",
                        description=f"Найден подозрительный паттерн: {pattern}",
                        location="file_content",
                        suggestion="Удалить вредоносный код",
                        auto_fixable=True
                    ))
            
            # Тест на XSS в value атрибутах
            xss_patterns = ["<script", "javascript:", "onclick=", "onerror=", "onload="]
            for pattern in xss_patterns:
                if pattern.lower() in content.lower():
                    results["issues"].append(DrawIOQualityIssue(
                        severity="high",
                        category="security",
                        issue_type="xss_vulnerability",
                        description=f"Потенциальная XSS уязвимость: {pattern}",
                        location="element_attributes",
                        suggestion="Экранировать пользовательский ввод"
                    ))
            
            results["tests"]["malicious_code"] = {"passed": len([i for i in results["issues"] if i.category == "security"]) == 0}
            
        except Exception as e:
            results["issues"].append(DrawIOQualityIssue(
                severity="medium",
                category="security",
                issue_type="read_error",
                description=f"Ошибка чтения файла: {str(e)}",
                location="file_access",
                suggestion="Проверить права доступа к файлу"
            ))
        
        results["status"] = "passed" if len(results["issues"]) == 0 else "failed"
        return results
    
    def _test_xml_validity(self, file_path: str) -> Dict:
        """Тест валидности XML"""
        try:
            ET.parse(file_path)
            return {"passed": True, "error": None}
        except ET.ParseError as e:
            return {"passed": False, "error": f"XML Parse Error: {str(e)}"}
        except Exception as e:
            return {"passed": False, "error": f"Unexpected error: {str(e)}"}
    
    def _test_file_encoding(self, file_path: str) -> Dict:
        """Тест кодировки файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return {"passed": True, "detected": "UTF-8"}
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    f.read()
                return {"passed": False, "detected": "Latin-1"}
            except:
                return {"passed": False, "detected": "Unknown"}
    
    def _test_drawio_structure(self, file_path: str) -> Dict:
        """Тест структуры Draw.io файла"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Проверяем основные элементы
            if root.tag != "mxfile":
                return {"passed": False, "error": "Root element должен быть 'mxfile'"}
            
            diagrams = root.findall("diagram")
            if len(diagrams) == 0:
                return {"passed": False, "error": "Не найдены элементы 'diagram'"}
            
            # Проверяем mxGraphModel
            for diagram in diagrams:
                graph_model = diagram.find("mxGraphModel")
                if graph_model is None:
                    return {"passed": False, "error": "Не найден элемент 'mxGraphModel'"}
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"Structure test failed: {str(e)}"}
    
    def _test_compressed_data(self, file_path: str) -> Dict:
        """Тест сжатых данных в диаграмме"""
        try:
            tree = ET.parse(file_path)
            diagrams = tree.findall(".//diagram")
            
            for diagram in diagrams:
                content = diagram.text
                if content and content.strip():
                    try:
                        # Попытка декодировать base64 и разжать
                        decoded = base64.b64decode(content)
                        decompressed = zlib.decompress(decoded, -15).decode('utf-8')
                        
                        # Проверяем, что это валидный XML
                        ET.fromstring(decompressed)
                    except Exception as e:
                        return {"passed": False, "error": f"Compression test failed: {str(e)}"}
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"Compression test error: {str(e)}"}
    
    def _test_diagram_elements(self, file_path: str) -> Dict:
        """Тест элементов диаграммы"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell")
            
            issues = []
            
            if len(cells) < self.quality_standards["min_elements"]:
                issues.append(DrawIOQualityIssue(
                    severity="medium",
                    category="structure",
                    issue_type="insufficient_elements",
                    description=f"Мало элементов: {len(cells)}",
                    location="diagram_content",
                    suggestion="Добавить больше элементов"
                ))
            
            # Проверяем атрибуты элементов
            for i, cell in enumerate(cells):
                for required_attr in ["id"]:
                    if required_attr not in cell.attrib:
                        issues.append(DrawIOQualityIssue(
                            severity="high",
                            category="structure",
                            issue_type="missing_attribute",
                            description=f"Элемент {i} не имеет атрибута '{required_attr}'",
                            location=f"mxCell[{i}]",
                            suggestion=f"Добавить атрибут {required_attr}"
                        ))
            
            return {
                "passed": len(issues) == 0,
                "issues": issues,
                "element_count": len(cells)
            }
        except Exception as e:
            return {
                "passed": False,
                "issues": [DrawIOQualityIssue(
                    severity="critical",
                    category="structure",
                    issue_type="element_test_failed",
                    description=f"Ошибка тестирования элементов: {str(e)}",
                    location="diagram_parsing",
                    suggestion="Проверить структуру файла"
                )],
                "element_count": 0
            }
    
    def _test_visual_dimensions(self, file_path: str) -> Dict:
        """Тест визуальных размеров"""
        try:
            tree = ET.parse(file_path)
            geometries = tree.findall(".//mxGeometry")
            
            if len(geometries) == 0:
                return {"passed": False, "error": "Не найдены элементы с геометрией"}
            
            # Вычисляем границы диаграммы
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            for geom in geometries:
                try:
                    x = float(geom.get('x', 0))
                    y = float(geom.get('y', 0))
                    width = float(geom.get('width', 0))
                    height = float(geom.get('height', 0))
                    
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x + width)
                    max_y = max(max_y, y + height)
                except (ValueError, TypeError):
                    continue
            
            diagram_width = max_x - min_x
            diagram_height = max_y - min_y
            
            standards = self.quality_standards["visual_standards"]
            if diagram_width < standards["min_diagram_width"] or diagram_height < standards["min_diagram_height"]:
                return {
                    "passed": False,
                    "error": f"Диаграмма слишком маленькая: {diagram_width}x{diagram_height}"
                }
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"Visual test failed: {str(e)}"}
    
    def _test_element_styles(self, file_path: str) -> Dict:
        """Тест стилей элементов"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell[@style]")
            
            issues = []
            style_problems = 0
            
            for cell in cells:
                style = cell.get('style', '')
                
                # Проверяем на пустые стили
                if not style.strip():
                    style_problems += 1
                
                # Проверяем на некорректные CSS значения
                if 'color=' in style and 'color=;' in style:
                    issues.append(DrawIOQualityIssue(
                        severity="low",
                        category="visual",
                        issue_type="empty_color",
                        description="Найдены пустые значения цвета",
                        location=f"mxCell[id={cell.get('id')}]",
                        suggestion="Установить корректные значения цвета"
                    ))
            
            if style_problems > len(cells) * 0.3:  # Больше 30% элементов без стилей
                issues.append(DrawIOQualityIssue(
                    severity="medium",
                    category="visual",
                    issue_type="insufficient_styling",
                    description=f"{style_problems} элементов без стилей",
                    location="diagram_styling",
                    suggestion="Добавить стили для улучшения внешнего вида"
                ))
            
            return {"passed": len(issues) == 0, "issues": issues}
        except Exception as e:
            return {"passed": False, "issues": []}
    
    def _test_text_readability(self, file_path: str) -> Dict:
        """Тест читаемости текста"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell[@value]")
            
            issues = []
            
            for cell in cells:
                value = cell.get('value', '')
                if value:
                    # Проверяем длину текста
                    if len(value) > 100:
                        issues.append(DrawIOQualityIssue(
                            severity="low",
                            category="visual",
                            issue_type="long_text",
                            description=f"Слишком длинный текст: {len(value)} символов",
                            location=f"mxCell[id={cell.get('id')}]",
                            suggestion="Сократить текст или разбить на части"
                        ))
                    
                    # Проверяем HTML entities
                    if '&' in value and '&amp;' not in value and '&lt;' not in value:
                        issues.append(DrawIOQualityIssue(
                            severity="medium",
                            category="visual",
                            issue_type="unescaped_entities",
                            description="Неэкранированные HTML сущности",
                            location=f"mxCell[id={cell.get('id')}]",
                            suggestion="Экранировать HTML сущности",
                            auto_fixable=True
                        ))
            
            return {"passed": len(issues) == 0, "issues": issues}
        except Exception as e:
            return {"passed": False, "issues": []}
    
    def _test_element_overlapping(self, file_path: str) -> Dict:
        """Тест перекрывающихся элементов"""
        try:
            tree = ET.parse(file_path)
            geometries = []
            
            cells = tree.findall(".//mxCell")
            for cell in cells:
                geom = cell.find("mxGeometry")
                if geom is not None:
                    try:
                        x = float(geom.get('x', 0))
                        y = float(geom.get('y', 0))
                        width = float(geom.get('width', 0))
                        height = float(geom.get('height', 0))
                        geometries.append((x, y, width, height))
                    except (ValueError, TypeError):
                        continue
            
            overlapping_count = 0
            for i, (x1, y1, w1, h1) in enumerate(geometries):
                for j, (x2, y2, w2, h2) in enumerate(geometries[i+1:], i+1):
                    # Проверяем пересечение прямоугольников
                    if (x1 < x2 + w2 and x1 + w1 > x2 and 
                        y1 < y2 + h2 and y1 + h1 > y2):
                        overlapping_count += 1
            
            max_overlapping = self.quality_standards["visual_standards"]["max_overlapping_elements"]
            
            return {
                "passed": overlapping_count <= max_overlapping,
                "count": overlapping_count
            }
        except Exception as e:
            return {"passed": True, "count": 0}
    
    def _test_diagram_connectivity(self, file_path: str) -> Dict:
        """Тест связности диаграммы"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell")
            
            # Подсчитываем вершины и рёбра
            vertices = []
            edges = []
            
            for cell in cells:
                if cell.get('edge') == '1':
                    edges.append(cell)
                elif cell.get('vertex') == '1':
                    vertices.append(cell)
            
            if len(vertices) == 0:
                return {"passed": False, "error": "Нет вершин в диаграмме"}
            
            # Простая проверка: должно быть хотя бы несколько связей
            connectivity_ratio = len(edges) / len(vertices) if len(vertices) > 0 else 0
            
            if connectivity_ratio < 0.2:  # Меньше 20% связности
                return {"passed": False, "error": f"Низкая связность: {connectivity_ratio:.1%}"}
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"Connectivity test failed: {str(e)}"}
    
    def _test_color_scheme(self, file_path: str) -> Dict:
        """Тест цветовой схемы"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell[@style]")
            
            issues = []
            colors_used = set()
            
            for cell in cells:
                style = cell.get('style', '')
                
                # Извлекаем цвета из стилей
                color_patterns = [
                    r'fillColor=([^;]+)',
                    r'strokeColor=([^;]+)',
                    r'fontColor=([^;]+)'
                ]
                
                for pattern in color_patterns:
                    matches = re.findall(pattern, style)
                    for match in matches:
                        if match and match != 'none':
                            colors_used.add(match.lower())
            
            # Проверяем контрастность (упрощенно)
            if '#ffffff' in colors_used and '#ffff00' in colors_used:
                issues.append(DrawIOQualityIssue(
                    severity="low",
                    category="visual",
                    issue_type="low_contrast",
                    description="Низкий контраст между белым и желтым",
                    location="color_scheme",
                    suggestion="Использовать более контрастные цвета"
                ))
            
            # Слишком много цветов
            if len(colors_used) > 10:
                issues.append(DrawIOQualityIssue(
                    severity="low",
                    category="visual",
                    issue_type="too_many_colors",
                    description=f"Слишком много цветов: {len(colors_used)}",
                    location="color_scheme",
                    suggestion="Ограничить палитру до 5-8 основных цветов"
                ))
            
            return {"passed": len(issues) == 0, "issues": issues}
        except Exception as e:
            return {"passed": False, "issues": []}
    
    def _test_pik_compliance(self, file_path: str) -> Dict:
        """Тест соответствия PIK методологии"""
        try:
            tree = ET.parse(file_path)
            content = ET.tostring(tree.getroot(), encoding='unicode').lower()
            
            # PIK ключевые слова
            pik_keywords = self.quality_standards["pik_keywords"]
            
            found_keywords = sum(1 for keyword in pik_keywords if keyword in content)
            coverage = found_keywords / len(pik_keywords)
            
            if coverage < 0.3:  # Меньше 30% покрытия PIK
                return {"passed": False, "error": f"Низкое соответствие PIK: {coverage:.1%}"}
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"PIK test failed: {str(e)}"}
    
    def _test_central_element(self, file_path: str) -> Dict:
        """Тест наличия центрального элемента"""
        try:
            tree = ET.parse(file_path)
            
            # Ищем элементы в центральной области
            geometries = []
            cells = tree.findall(".//mxCell")
            
            for cell in cells:
                geom = cell.find("mxGeometry")
                if geom is not None:
                    try:
                        x = float(geom.get('x', 0))
                        y = float(geom.get('y', 0))
                        geometries.append((x, y, cell))
                    except (ValueError, TypeError):
                        continue
            
            if not geometries:
                return {"passed": False}
            
            # Вычисляем центр диаграммы
            avg_x = sum(x for x, y, _ in geometries) / len(geometries)
            avg_y = sum(y for x, y, _ in geometries) / len(geometries)
            
            # Ищем элементы рядом с центром
            center_threshold = 100  # пиксели
            central_elements = [
                cell for x, y, cell in geometries
                if abs(x - avg_x) < center_threshold and abs(y - avg_y) < center_threshold
            ]
            
            return {"passed": len(central_elements) > 0}
        except Exception as e:
            return {"passed": False}
    
    def _test_logical_grouping(self, file_path: str) -> Dict:
        """Тест логической группировки элементов"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell")
            
            # Простой тест: проверяем наличие групп или контейнеров
            groups = [cell for cell in cells if cell.get('style', '').find('group') != -1]
            containers = [cell for cell in cells if cell.get('style', '').find('container') != -1]
            
            total_grouping_elements = len(groups) + len(containers)
            total_elements = len([cell for cell in cells if cell.get('vertex') == '1'])
            
            if total_elements > 10 and total_grouping_elements == 0:
                return {"passed": False, "error": "Нет логической группировки для большой диаграммы"}
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"Grouping test failed: {str(e)}"}
    
    def _test_pik_terminology(self, file_path: str) -> Dict:
        """Тест корректности PIK терминологии"""
        try:
            tree = ET.parse(file_path)
            cells = tree.findall(".//mxCell[@value]")
            
            # Проверяем использование корректной терминологии
            incorrect_terms = {
                "пользователь": "stakeholder",
                "клиент": "demand-side user",
                "продавец": "supply-side participant",
                "товар": "value proposition"
            }
            
            found_incorrect = []
            for cell in cells:
                value = cell.get('value', '').lower()
                for incorrect, correct in incorrect_terms.items():
                    if incorrect in value:
                        found_incorrect.append((incorrect, correct))
            
            if found_incorrect:
                terms_list = ", ".join([f"'{inc}' → '{cor}'" for inc, cor in found_incorrect])
                return {"passed": False, "error": f"Некорректная терминология: {terms_list}"}
            
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": f"Terminology test failed: {str(e)}"}
    
    def _calculate_quality_score(self, issues: List[DrawIOQualityIssue], file_path: str) -> float:
        """Расчет общего балла качества (0-100)"""
        base_score = 100.0
        
        # Штрафы за проблемы
        severity_penalties = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3
        }
        
        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 5)
            base_score -= penalty
        
        # Бонусы за хорошие практики
        try:
            file_size = os.path.getsize(file_path)
            if file_size < 1024 * 1024:  # Меньше 1MB - бонус
                base_score += 5
            
            tree = ET.parse(file_path)
            element_count = len(tree.findall(".//mxCell"))
            if 10 <= element_count <= 50:  # Оптимальное количество элементов
                base_score += 5
        except:
            pass
        
        return max(0.0, min(100.0, base_score))
    
    def _collect_file_stats(self, file_path: str) -> Dict:
        """Сбор статистики файла"""
        stats = {}
        
        try:
            # Основная информация
            stats["file_size"] = os.path.getsize(file_path)
            stats["file_name"] = os.path.basename(file_path)
            
            # XML статистика
            tree = ET.parse(file_path)
            stats["total_elements"] = len(tree.findall(".//*"))
            stats["diagram_count"] = len(tree.findall(".//diagram"))
            stats["cell_count"] = len(tree.findall(".//mxCell"))
            stats["vertex_count"] = len(tree.findall(".//mxCell[@vertex='1']"))
            stats["edge_count"] = len(tree.findall(".//mxCell[@edge='1']"))
            
            # Текстовая статистика
            all_text = ""
            for cell in tree.findall(".//mxCell[@value]"):
                all_text += cell.get('value', '') + " "
            
            stats["total_text_length"] = len(all_text)
            stats["word_count"] = len(all_text.split())
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def run_batch_test(self, directory_path: str) -> List[DrawIOQualityReport]:
        """Пакетное тестирование всех Draw.io файлов в директории"""
        reports = []
        
        drawio_files = [
            f for f in os.listdir(directory_path) 
            if f.endswith('.drawio') or f.endswith('.xml')
        ]
        
        print(f"\n🚀 Запуск пакетного тестирования {len(drawio_files)} файлов...")
        
        for filename in drawio_files:
            file_path = os.path.join(directory_path, filename)
            try:
                report = self.run_comprehensive_test(file_path)
                reports.append(report)
            except Exception as e:
                print(f"❌ Ошибка тестирования {filename}: {e}")
        
        return reports
    
    def auto_fix_issues(self, file_path: str) -> Dict:
        """Автоматическое исправление проблем"""
        fixes_applied = 0
        fixed_issues = []
        
        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Исправление 1: Экранирование HTML сущностей
            if '&' in content and '&amp;' not in content:
                # Простое экранирование (нужно быть осторожным с уже экранированными)
                import re
                # Заменяем & на &amp;, но не трогаем уже экранированные
                content = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', content)
                if content != original_content:
                    fixes_applied += 1
                    fixed_issues.append("Экранированы HTML сущности")
                    original_content = content
            
            # Исправление 2: Удаление вредоносного кода
            for pattern in self.quality_standards["forbidden_patterns"]:
                if pattern.lower() in content.lower():
                    content = content.replace(pattern, '')
                    fixes_applied += 1
                    fixed_issues.append(f"Удален подозрительный код: {pattern}")
            
            # Сохраняем исправленный файл
            if content != original_content:
                # Создаем резервную копию
                backup_path = file_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Сохраняем исправленную версию
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return {
                "success": True,
                "fixes_applied": fixes_applied,
                "fixed_issues": fixed_issues,
                "backup_created": content != original_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fixes_applied": 0
            }

def main():
    """Главная функция для запуска тестирования"""
    tester = DrawIOQualityTester()
    
    # Путь к директории с Draw.io файлами
    drawio_dir = "./output/drawio"
    
    if not os.path.exists(drawio_dir):
        print(f"❌ Директория {drawio_dir} не найдена")
        return
    
    # Запуск пакетного тестирования
    reports = tester.run_batch_test(drawio_dir)
    
    if not reports:
        print("❌ Нет файлов для тестирования")
        return
    
    # Сохранение JSON отчета
    json_report_path = "drawio_quality_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(report) for report in reports], f, indent=2, ensure_ascii=False)
    
    # Вывод краткой статистики
    print(f"\n📊 Результаты тестирования:")
    print(f"   Файлов протестировано: {len(reports)}")
    
    avg_score = sum(r.overall_score for r in reports) / len(reports)
    print(f"   Средний балл качества: {avg_score:.1f}/100")
    
    total_issues = sum(len(r.issues) for r in reports)
    print(f"   Всего проблем найдено: {total_issues}")
    
    critical_issues = sum(sum(1 for issue in r.issues if issue.severity == 'critical') for r in reports)
    print(f"   Критических проблем: {critical_issues}")
    
    auto_fixable = sum(sum(1 for issue in r.issues if issue.auto_fixable) for r in reports)
    print(f"   Автоисправимых проблем: {auto_fixable}")
    
    print(f"\n📄 JSON отчет сохранен: {json_report_path}")
    
    # Рекомендации
    if avg_score < 70:
        print(f"\n⚠️  Качество ниже нормы. Рекомендуется исправить критические проблемы.")
    elif avg_score >= 90:
        print(f"\n🎉 Отличное качество Draw.io файлов!")
    else:
        print(f"\n✅ Хорошее качество, есть возможности для улучшения.")

if __name__ == "__main__":
    main()
