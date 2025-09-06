#!/usr/bin/env python3
"""
Диагностика проблем с Draw.io файлами
====================================

Проверяет логику поиска файлов напрямую.
"""

from pathlib import Path
import json

def check_framework_files():
    """Проверяет соответствие между файлами анализа и Draw.io"""
    print("🔍 Диагностика файлов PIK фреймворков")
    print("=" * 50)
    
    # Пути к директориям
    analysis_dir = Path("output/analysis")
    drawio_dir = Path("output/drawio")
    
    print(f"📁 Анализ директории: {analysis_dir}")
    print(f"📁 Draw.io директория: {drawio_dir}")
    print()
    
    # Проверяем файлы анализа
    if analysis_dir.exists():
        analysis_files = list(analysis_dir.glob("*_analysis.json"))
        print(f"📊 Найдено файлов анализа: {len(analysis_files)}")
        
        for analysis_file in analysis_files:
            framework_id = analysis_file.stem.replace('_analysis', '')
            print(f"\n🎯 Фреймворк: {framework_id}")
            
            # Загружаем данные анализа
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                title = data.get('title', 'Unknown')
                elements_count = len(data.get('elements', []))
                print(f"   📋 Название: {title}")
                print(f"   📊 Элементов: {elements_count}")
            except Exception as e:
                print(f"   ❌ Ошибка чтения анализа: {e}")
            
            # Проверяем наличие Draw.io файла
            possible_drawio_files = [
                drawio_dir / f"{framework_id}_diagram.drawio",
                drawio_dir / f"{framework_id}.drawio",
            ]
            
            found_drawio = False
            for drawio_file in possible_drawio_files:
                if drawio_file.exists():
                    size = drawio_file.stat().st_size
                    print(f"   ✅ Draw.io файл: {drawio_file.name} ({size:,} байт)")
                    found_drawio = True
                    
                    # Проверяем содержимое
                    try:
                        with open(drawio_file, 'r', encoding='utf-8') as f:
                            content = f.read(200)  # Первые 200 символов
                        if content.startswith('<?xml') and 'mxfile' in content:
                            print(f"   ✅ XML валидный")
                        else:
                            print(f"   ❌ XML невалидный")
                    except Exception as e:
                        print(f"   ❌ Ошибка чтения XML: {e}")
                    
                    break
            
            if not found_drawio:
                print(f"   ❌ Draw.io файл не найден")
                print(f"      Ожидаемые имена:")
                for drawio_file in possible_drawio_files:
                    print(f"        - {drawio_file.name}")
        
    else:
        print("❌ Директория анализа не найдена")
    
    # Проверяем все Draw.io файлы
    print(f"\n📁 ВСЕ DRAW.IO ФАЙЛЫ:")
    print("-" * 30)
    if drawio_dir.exists():
        all_drawio = list(drawio_dir.glob("*.drawio"))
        for drawio_file in all_drawio:
            size = drawio_file.stat().st_size
            print(f"   📄 {drawio_file.name}: {size:,} байт")
    else:
        print("❌ Директория Draw.io не найдена")

def test_server_logic():
    """Тестирует логику сервера для поиска файлов"""
    print(f"\n🧪 ТЕСТИРОВАНИЕ ЛОГИКИ ПОИСКА:")
    print("-" * 40)
    
    # Имитируем логику сервера
    DRAWIO_DIR = Path("output/drawio")
    test_framework_id = "pik_20250906_164101_2ed9d0bf"
    
    print(f"🎯 Тестируем поиск для: {test_framework_id}")
    
    # Попробуем найти файл с различными суффиксами
    possible_files = [
        DRAWIO_DIR / f"{test_framework_id}_diagram.drawio",
        DRAWIO_DIR / f"{test_framework_id}.drawio",
    ]
    
    drawio_file = None
    for file_path in possible_files:
        print(f"   Проверяем: {file_path}")
        if file_path.exists():
            drawio_file = file_path
            print(f"   ✅ Найден: {file_path}")
            break
        else:
            print(f"   ❌ Не найден: {file_path}")
    
    if not drawio_file:
        # Попробуем найти любой файл, содержащий ID
        print(f"   🔍 Поиск файлов содержащих '{test_framework_id}' в {DRAWIO_DIR}")
        all_files = list(DRAWIO_DIR.glob("*.drawio"))
        print(f"   📁 Всего .drawio файлов: {len(all_files)}")
        
        for file in all_files:
            print(f"      Проверяем файл: {file.name}")
            if test_framework_id in file.name:
                drawio_file = file
                print(f"   ✅ Найден по содержимому ID: {file}")
                break
    
    if drawio_file:
        print(f"🎉 Итоговый найденный файл: {drawio_file}")
    else:
        print(f"❌ Файл не найден для {test_framework_id}")

if __name__ == "__main__":
    check_framework_files()
    test_server_logic()
