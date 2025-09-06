#!/usr/bin/env python3
"""
Валидация XML файлов Draw.io
============================

Проверяет валидность XML и совместимость с Draw.io.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def validate_xml_file(file_path):
    """Валидирует XML файл"""
    print(f"🔍 Проверка файла: {file_path.name}")
    
    try:
        # Читаем содержимое
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем базовую структуру
        if not content.startswith('<?xml'):
            print(f"   ❌ Не начинается с XML декларации")
            return False
        
        if 'mxfile' not in content:
            print(f"   ❌ Не содержит mxfile элемент")
            return False
        
        # Пытаемся парсить XML
        try:
            root = ET.fromstring(content)
            print(f"   ✅ XML валиден")
            
            # Проверяем структуру Draw.io
            if root.tag == 'mxfile':
                diagrams = root.findall('diagram')
                print(f"   📊 Найдено диаграмм: {len(diagrams)}")
                
                for i, diagram in enumerate(diagrams):
                    name = diagram.get('name', f'Диаграмма {i+1}')
                    print(f"      - {name}")
                
                return True
            else:
                print(f"   ❌ Корневой элемент не mxfile: {root.tag}")
                return False
                
        except ET.ParseError as e:
            print(f"   ❌ Ошибка парсинга XML: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Ошибка чтения файла: {e}")
        return False

def create_minimal_drawio_example():
    """Создает минимальный рабочий пример Draw.io"""
    minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2025-09-06T17:30:00.000Z" agent="PIK-Parser" version="21.1.2" etag="test">
  <diagram name="Test" id="test-diagram">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="Test Element" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="280" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="3" value="&amp; Symbol Test" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="340" y="380" width="120" height="60" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    
    test_file = Path("test_minimal.drawio")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(minimal_xml)
    
    print(f"✅ Создан тестовый файл: {test_file}")
    return test_file

def main():
    """Основная функция"""
    print("🔍 Валидация XML файлов Draw.io")
    print("=" * 40)
    
    # Создаем минимальный пример для сравнения
    test_file = create_minimal_drawio_example()
    print()
    
    # Проверяем тестовый файл
    print("🧪 ТЕСТОВЫЙ ФАЙЛ:")
    validate_xml_file(test_file)
    print()
    
    # Проверяем наши файлы
    drawio_dir = Path("output/drawio")
    
    if drawio_dir.exists():
        drawio_files = list(drawio_dir.glob("*.drawio"))
        if '.backup' in str(drawio_files):
            drawio_files = [f for f in drawio_files if '.backup' not in f.name]
        
        print("📁 НАШИ ФАЙЛЫ:")
        print("-" * 20)
        
        valid_count = 0
        for drawio_file in drawio_files:
            if validate_xml_file(drawio_file):
                valid_count += 1
            print()
        
        print(f"📊 РЕЗУЛЬТАТ: {valid_count}/{len(drawio_files)} файлов валидны")
    else:
        print("❌ Директория output/drawio не найдена")

if __name__ == "__main__":
    main()
