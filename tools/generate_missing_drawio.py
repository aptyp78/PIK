#!/usr/bin/env python3
"""
Генератор недостающих Draw.io файлов
====================================

Создает Draw.io диаграммы для всех проанализированных фреймворков.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_analysis_file(file_path):
    """Загружает файл анализа"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки {file_path}: {e}")
        return None

def generate_drawio_xml(framework_data):
    """Генерирует Draw.io XML из данных фреймворка"""
    framework_id = framework_data.get('id', 'unknown')
    title = framework_data.get('title', 'Unknown Framework')
    elements = framework_data.get('elements', [])
    relationships = framework_data.get('relationships', [])
    
    # Начало XML
    xml_content = f"""<?xml version="1.0" ?>
<mxfile host="app.diagrams.net" modified="{datetime.now().isoformat()}" agent="PIK-Parser" version="21.1.2">
  <diagram name="{title}" id="{framework_id}">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="{title}" style="text;strokeColor=none;fillColor=none;html=1;fontSize=16;fontStyle=1;verticalAlign=middle;align=center;" vertex="1" parent="1">
          <mxGeometry x="50" y="20" width="300" height="30" as="geometry"/>
        </mxCell>"""
    
    # Добавляем элементы
    cell_id = 3
    element_positions = {}
    
    for element in elements:
        element_id = element.get('id', '')
        text = element.get('text', '').replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        element_type = element.get('type', '').replace('ElementType.', '').lower()
        confidence = element.get('confidence', 0)
        position = element.get('position', [100, 100, 100, 40])
        relationships_count = len(element.get('relationships', []))
        
        # Определяем цвет по типу элемента
        color_map = {
            'stakeholder': '#d5e8d4',
            'force': '#fff2cc',
            'value_proposition': '#f8cecc',
            'nfx_engine': '#e1d5e7',
            'process': '#dae8fc',
            'label': '#f5f5f5'
        }
        fill_color = color_map.get(element_type, '#f5f5f5')
        
        # Позиция элемента
        x, y, width, height = position
        
        # Создаем tooltip
        tooltip = f"Тип: {element_type} | Уверенность: {confidence:.2f} | Связи: {relationships_count}"
        
        xml_content += f"""
        <mxCell id="{cell_id}" value="{text}" style="shape=rectangle;whiteSpace=wrap;html=1;fillColor={fill_color};strokeColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry"/>
          <mxCell tooltip="{tooltip}"/>
        </mxCell>"""
        
        element_positions[element_id] = cell_id
        cell_id += 1
    
    # Добавляем связи между элементами
    for relationship in relationships[:50]:  # Ограничиваем количество связей для читаемости
        source_id = relationship.get('source', '')
        target_id = relationship.get('target', '')
        rel_type = relationship.get('type', 'related')
        strength = relationship.get('strength', 0)
        
        if source_id in element_positions and target_id in element_positions:
            source_cell = element_positions[source_id]
            target_cell = element_positions[target_id]
            
            xml_content += f"""
        <mxCell id="{cell_id}" value="{rel_type}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="{source_cell}" target="{target_cell}">
          <mxGeometry relative="1" as="geometry">
            <mxPoint as="sourcePoint"/>
            <mxPoint as="targetPoint"/>
          </mxGeometry>
        </mxCell>"""
            cell_id += 1
    
    # Закрытие XML
    xml_content += """
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
    
    return xml_content

def main():
    """Основная функция"""
    print("🎨 Генератор недостающих Draw.io файлов")
    print("=" * 50)
    
    # Пути к директориям
    analysis_dir = Path("output/analysis")
    drawio_dir = Path("output/drawio")
    
    if not analysis_dir.exists():
        print("❌ Директория анализа не найдена!")
        return
    
    # Создаем директорию draw.io если её нет
    drawio_dir.mkdir(parents=True, exist_ok=True)
    
    # Находим все файлы анализа
    analysis_files = list(analysis_dir.glob("*_analysis.json"))
    print(f"📊 Найдено файлов анализа: {len(analysis_files)}")
    
    generated_count = 0
    skipped_count = 0
    
    for analysis_file in analysis_files:
        # Извлекаем ID фреймворка из имени файла
        framework_id = analysis_file.stem.replace('_analysis', '')
        drawio_file = drawio_dir / f"{framework_id}_diagram.drawio"
        
        if drawio_file.exists():
            print(f"⏭️  Пропускаем {framework_id} - файл уже существует")
            skipped_count += 1
            continue
        
        # Загружаем данные анализа
        framework_data = load_analysis_file(analysis_file)
        if not framework_data:
            continue
        
        # Генерируем Draw.io XML
        try:
            xml_content = generate_drawio_xml(framework_data)
            
            # Сохраняем файл
            with open(drawio_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"✅ Создан {framework_id}_diagram.drawio")
            generated_count += 1
            
        except Exception as e:
            print(f"❌ Ошибка генерации {framework_id}: {e}")
    
    print("-" * 50)
    print(f"🎯 Результат:")
    print(f"   ✅ Создано новых файлов: {generated_count}")
    print(f"   ⏭️  Пропущено существующих: {skipped_count}")
    print(f"   📁 Всего Draw.io файлов: {len(list(drawio_dir.glob('*.drawio')))}")

if __name__ == "__main__":
    main()
