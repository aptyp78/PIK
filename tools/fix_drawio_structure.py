#!/usr/bin/env python3
"""
Draw.io Structure Fixer
========================

Автоматическое исправление структурных проблем в Draw.io файлах
"""

import os
import xml.etree.ElementTree as ET
import uuid
import re
from pathlib import Path

class DrawIOStructureFixer:
    """Инструмент для исправления структурных проблем Draw.io"""
    
    def __init__(self):
        self.fixes_applied = 0
        self.files_fixed = 0
    
    def fix_missing_ids(self, file_path: str) -> dict:
        """Исправление отсутствующих ID атрибутов"""
        print(f"🔧 Исправление {os.path.basename(file_path)}...")
        
        try:
            # Читаем файл как текст (так как ET может ломать структуру)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_count = 0
            
            # Создаем бэкап
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Исправляем вложенные mxCell без id
            pattern = r'<mxCell\s+tooltip="[^"]*"/>'
            matches = re.findall(pattern, content)
            
            for match in matches:
                # Заменяем на корректную структуру
                new_id = str(uuid.uuid4())[:8]
                # Просто удаляем некорректные вложенные элементы
                content = content.replace(match, '')
                fixes_count += 1
            
            # Исправляем элементы без ID (но это сложнее, требует парсинга)
            try:
                tree = ET.fromstring(content)
                self._fix_missing_ids_recursive(tree)
                content = ET.tostring(tree, encoding='unicode')
                fixes_count += self._count_fixes_needed(original_content, content)
            except ET.ParseError:
                # Если XML невалидный, применяем regex исправления
                print("   ⚠️ XML невалидный, применяем базовые исправления")
            
            # Сохраняем исправленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ Применено {fixes_count} исправлений")
            self.fixes_applied += fixes_count
            
            if fixes_count > 0:
                self.files_fixed += 1
            
            return {
                "success": True,
                "fixes_applied": fixes_count,
                "backup_created": True
            }
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return {
                "success": False,
                "error": str(e),
                "fixes_applied": 0
            }
    
    def _fix_missing_ids_recursive(self, element):
        """Рекурсивно исправляем отсутствующие ID"""
        if element.tag == 'mxCell' and 'id' not in element.attrib:
            # Добавляем уникальный ID
            element.set('id', str(uuid.uuid4())[:8])
        
        # Обрабатываем дочерние элементы
        for child in element:
            self._fix_missing_ids_recursive(child)
    
    def _count_fixes_needed(self, original: str, fixed: str) -> int:
        """Подсчет количества исправлений"""
        # Простой подсчет разницы в структуре
        original_cells = len(re.findall(r'<mxCell', original))
        fixed_cells = len(re.findall(r'<mxCell', fixed))
        return abs(original_cells - fixed_cells)
    
    def regenerate_drawio_files(self):
        """Перегенерация Draw.io файлов с исправленной структурой"""
        print("🔄 Перегенерация Draw.io файлов...")
        
        try:
            from intelligent_pik_parser import IntelligentPIKParser
            
            # Инициализируем парсер
            parser = IntelligentPIKParser()
            
            # Ищем анализы для регенерации
            analysis_dir = Path("output/analysis")
            if not analysis_dir.exists():
                print("❌ Папка анализов не найдена")
                return False
            
            regenerated = 0
            for analysis_file in analysis_dir.glob("*_analysis.json"):
                try:
                    print(f"   📄 Обрабатываем {analysis_file.name}")
                    
                    # Загружаем анализ
                    import json
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                    
                    # Создаем объект фреймворка
                    from intelligent_pik_parser import PIKFramework, PIKElement, ElementType
                    
                    framework = PIKFramework(
                        title=analysis_data.get("framework_type", "PIK Framework"),
                        framework_type=analysis_data.get("framework_type", "unknown"),
                        elements=[],
                        relationships=analysis_data.get("relationships", [])
                    )
                    
                    # Добавляем элементы
                    for elem_data in analysis_data.get("elements", []):
                        element = PIKElement(
                            id=elem_data.get("id"),
                            text=elem_data.get("text", ""),
                            element_type=ElementType.label,  # Простое значение по умолчанию
                            position=elem_data.get("position", [100, 100, 100, 50]),
                            confidence=elem_data.get("confidence", 0.8)
                        )
                        framework.elements.append(element)
                    
                    # Генерируем новый Draw.io файл
                    drawio_content = parser.generate_drawio_xml(framework)
                    
                    # Сохраняем
                    framework_id = analysis_file.stem.replace("_analysis", "")
                    output_path = Path("output/drawio") / f"{framework_id}_fixed.drawio"
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(drawio_content)
                    
                    print(f"   ✅ Создан {output_path.name}")
                    regenerated += 1
                    
                except Exception as e:
                    print(f"   ❌ Ошибка обработки {analysis_file.name}: {e}")
            
            print(f"🎉 Перегенерировано {regenerated} файлов")
            return regenerated > 0
            
        except Exception as e:
            print(f"❌ Ошибка перегенерации: {e}")
            return False
    
    def fix_all_files(self, directory: str):
        """Исправление всех Draw.io файлов в директории"""
        print(f"🚀 Исправление файлов в {directory}")
        
        drawio_dir = Path(directory)
        if not drawio_dir.exists():
            print(f"❌ Директория {directory} не найдена")
            return
        
        # Находим все draw.io файлы (исключая бэкапы)
        drawio_files = [
            f for f in drawio_dir.glob("*.drawio") 
            if not f.name.endswith('.backup')
        ]
        
        if not drawio_files:
            print("❌ Draw.io файлы не найдены")
            return
        
        print(f"📁 Найдено {len(drawio_files)} файлов для исправления")
        
        for file_path in drawio_files:
            self.fix_missing_ids(str(file_path))
        
        print(f"\n📊 ИТОГИ ИСПРАВЛЕНИЯ:")
        print(f"   Файлов обработано: {len(drawio_files)}")
        print(f"   Файлов исправлено: {self.files_fixed}")
        print(f"   Всего исправлений: {self.fixes_applied}")

def main():
    """Главная функция"""
    print("""
🔧 Draw.io Structure Fixer
==========================

Автоматическое исправление структурных проблем:
• Добавление отсутствующих ID атрибутов
• Удаление некорректных вложенных элементов  
• Перегенерация файлов с правильной структурой
""")
    
    fixer = DrawIOStructureFixer()
    
    print("Выберите действие:")
    print("1. Исправить существующие файлы")
    print("2. Перегенерировать файлы из анализов")
    print("3. Оба действия")
    
    choice = input("Ваш выбор (1-3): ").strip()
    
    if choice in ["1", "3"]:
        # Исправляем существующие файлы
        drawio_dir = "output/drawio"
        fixer.fix_all_files(drawio_dir)
    
    if choice in ["2", "3"]:
        # Перегенерируем файлы
        fixer.regenerate_drawio_files()
    
    if choice not in ["1", "2", "3"]:
        print("❌ Неверный выбор")
        return
    
    print("\n✅ Исправление завершено!")
    print("💡 Теперь можно повторно запустить тестирование качества")

if __name__ == "__main__":
    main()
