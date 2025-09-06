#!/usr/bin/env python3
"""
Исправление XML ошибок в Draw.io файлах
=======================================

Исправляет неэкранированные символы в XML файлах.
"""

import re
from pathlib import Path

def fix_xml_entities(content):
    """Исправляет неэкранированные символы в XML"""
    # Заменяем неэкранированные амперсанды, но не трогаем уже экранированные
    content = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', content)
    
    # Исправляем другие проблемные символы в значениях атрибутов
    # Ищем value="..." и исправляем содержимое
    def fix_value_content(match):
        value_content = match.group(1)
        # Исправляем символы внутри value
        value_content = value_content.replace('<', '&lt;').replace('>', '&gt;')
        return f'value="{value_content}"'
    
    # Применяем исправления к атрибутам value
    content = re.sub(r'value="([^"]*)"', fix_value_content, content)
    
    return content

def fix_drawio_file(file_path):
    """Исправляет один Draw.io файл"""
    print(f"🔧 Исправление файла: {file_path.name}")
    
    try:
        # Читаем содержимое
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие проблем
        problems_found = []
        if 'value="&"' in content:
            problems_found.append('неэкранированный &')
        if 'value="<' in content:
            problems_found.append('неэкранированный <')
        if 'value=">"' in content:
            problems_found.append('неэкранированный >')
        
        if problems_found:
            print(f"   ⚠️  Найдены проблемы: {', '.join(problems_found)}")
            
            # Исправляем содержимое
            fixed_content = fix_xml_entities(content)
            
            # Создаем резервную копию
            backup_path = file_path.with_suffix('.drawio.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 Создана резервная копия: {backup_path.name}")
            
            # Сохраняем исправленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"   ✅ Файл исправлен")
            
            # Проверяем результат
            test_problems = []
            if 'value="&"' in fixed_content:
                test_problems.append('&')
            if 'value="<' in fixed_content:
                test_problems.append('<')
            if 'value=">"' in fixed_content:
                test_problems.append('>')
            
            if test_problems:
                print(f"   ❌ Остались проблемы: {', '.join(test_problems)}")
            else:
                print(f"   ✅ Все проблемы исправлены")
        else:
            print(f"   ✅ Проблем не найдено")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

def main():
    """Основная функция"""
    print("🔧 Исправление XML ошибок в Draw.io файлах")
    print("=" * 50)
    
    drawio_dir = Path("output/drawio")
    
    if not drawio_dir.exists():
        print("❌ Директория output/drawio не найдена!")
        return
    
    # Находим все Draw.io файлы
    drawio_files = list(drawio_dir.glob("*.drawio"))
    
    if not drawio_files:
        print("❌ Draw.io файлы не найдены!")
        return
    
    print(f"📊 Найдено файлов: {len(drawio_files)}")
    print()
    
    fixed_count = 0
    problem_count = 0
    
    for drawio_file in drawio_files:
        # Пропускаем резервные копии
        if '.backup' in drawio_file.name:
            continue
            
        fix_drawio_file(drawio_file)
        
        # Проверяем, были ли проблемы
        with open(drawio_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'value="&"' not in content:
            fixed_count += 1
        else:
            problem_count += 1
    
    print()
    print("📊 РЕЗУЛЬТАТ:")
    print(f"   ✅ Исправлено файлов: {fixed_count}")
    print(f"   ❌ Файлов с проблемами: {problem_count}")
    print(f"   📁 Всего обработано: {len([f for f in drawio_files if '.backup' not in f.name])}")

if __name__ == "__main__":
    main()
