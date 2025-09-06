#!/usr/bin/env python3
"""
Исправление конкретных XML ошибок в Draw.io файлах
==================================================

Находит и исправляет проблемные символы в XML.
"""

import re
from pathlib import Path

def escape_xml_content(text):
    """Экранирует специальные символы для XML"""
    # Порядок важен!
    text = text.replace('&', '&amp;')  # Сначала амперсанды
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

def fix_value_attributes(content):
    """Исправляет содержимое атрибутов value"""
    def replace_value(match):
        value_content = match.group(1)
        # Если уже экранировано, не трогаем
        if '&amp;' in value_content or '&lt;' in value_content or '&gt;' in value_content:
            return match.group(0)
        
        # Экранируем содержимое
        escaped_content = escape_xml_content(value_content)
        return f'value="{escaped_content}"'
    
    # Находим все атрибуты value и исправляем их содержимое
    content = re.sub(r'value="([^"]*)"', replace_value, content)
    return content

def fix_tooltip_attributes(content):
    """Исправляет содержимое атрибутов tooltip"""
    def replace_tooltip(match):
        tooltip_content = match.group(1)
        # Если уже экранировано, не трогаем
        if '&amp;' in tooltip_content or '&lt;' in tooltip_content or '&gt;' in tooltip_content:
            return match.group(0)
        
        # Экранируем содержимое (но не трогаем специальные символы вроде |, :)
        escaped_content = tooltip_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'tooltip="{escaped_content}"'
    
    # Находим все атрибуты tooltip и исправляем их содержимое
    content = re.sub(r'tooltip="([^"]*)"', replace_tooltip, content)
    return content

def validate_and_fix_file(file_path):
    """Валидирует и исправляет файл"""
    print(f"🔧 Обработка файла: {file_path.name}")
    
    try:
        # Читаем содержимое
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Проверяем наличие проблем
        problems = []
        
        # Ищем проблемные паттерны
        if re.search(r'value="[^"]*[&<>][^"]*"', original_content):
            # Исключаем уже экранированные
            unescaped = re.findall(r'value="([^"]*[&<>][^"]*)"', original_content)
            unescaped = [u for u in unescaped if not ('&amp;' in u or '&lt;' in u or '&gt;' in u)]
            if unescaped:
                problems.append(f"неэкранированные символы в value: {unescaped[:3]}")
        
        if problems:
            print(f"   ⚠️  Найдены проблемы: {', '.join(problems)}")
            
            # Создаем резервную копию
            backup_path = file_path.with_suffix('.drawio.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"   💾 Создана резервная копия: {backup_path.name}")
            
            # Исправляем содержимое
            fixed_content = original_content
            fixed_content = fix_value_attributes(fixed_content)
            fixed_content = fix_tooltip_attributes(fixed_content)
            
            # Сохраняем исправленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"   ✅ Файл исправлен")
            
            # Проверяем результат с помощью XML парсера
            try:
                import xml.etree.ElementTree as ET
                ET.fromstring(fixed_content)
                print(f"   ✅ XML валиден после исправления")
                return True
            except ET.ParseError as e:
                print(f"   ❌ XML все еще невалиден: {e}")
                return False
        else:
            # Проверяем валидность даже если проблем не найдено
            try:
                import xml.etree.ElementTree as ET
                ET.fromstring(original_content)
                print(f"   ✅ Файл уже валиден")
                return True
            except ET.ParseError as e:
                print(f"   ❌ XML невалиден: {e}")
                print(f"   🔍 Нужно ручное исправление")
                return False
            
    except Exception as e:
        print(f"   ❌ Ошибка обработки: {e}")
        return False

def main():
    """Основная функция"""
    print("🔧 Исправление XML ошибок в Draw.io файлах (расширенная версия)")
    print("=" * 70)
    
    drawio_dir = Path("output/drawio")
    
    if not drawio_dir.exists():
        print("❌ Директория output/drawio не найдена!")
        return
    
    # Находим все Draw.io файлы
    drawio_files = list(drawio_dir.glob("*.drawio"))
    drawio_files = [f for f in drawio_files if '.backup' not in f.name]
    
    if not drawio_files:
        print("❌ Draw.io файлы не найдены!")
        return
    
    print(f"📊 Найдено файлов: {len(drawio_files)}")
    print()
    
    fixed_count = 0
    valid_count = 0
    
    for drawio_file in drawio_files:
        if validate_and_fix_file(drawio_file):
            valid_count += 1
            # Проверяем, был ли создан backup (значит файл был исправлен)
            backup_file = drawio_file.with_suffix('.drawio.backup')
            if backup_file.exists():
                fixed_count += 1
    
    print()
    print("📊 РЕЗУЛЬТАТ:")
    print(f"   🔧 Исправлено файлов: {fixed_count}")
    print(f"   ✅ Валидных файлов: {valid_count}")
    print(f"   📁 Всего обработано: {len(drawio_files)}")
    
    if valid_count == len(drawio_files):
        print("\n🎉 Все файлы теперь валидны и готовы для использования в Draw.io!")

if __name__ == "__main__":
    main()
