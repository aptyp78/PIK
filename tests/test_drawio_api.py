#!/usr/bin/env python3
"""
Тестирование API Draw.io файлов
===============================

Проверяет доступность всех Draw.io файлов через API.
"""

import requests
import json
from pathlib import Path

def test_api_endpoints():
    """Тестирует все API эндпоинты для Draw.io файлов"""
    base_url = "http://localhost:8001"
    
    print("🧪 Тестирование API Draw.io файлов")
    print("=" * 50)
    
    # Получаем список всех фреймворков
    try:
        response = requests.get(f"{base_url}/api/frameworks", timeout=5)
        if response.status_code == 200:
            frameworks = response.json()
            print(f"📊 Получено фреймворков: {len(frameworks)}")
            
            for framework in frameworks:
                framework_id = framework['id']
                title = framework['title']
                
                print(f"\n🎯 Тестирование фреймворка: {title} ({framework_id})")
                
                # Тестируем получение Draw.io XML
                try:
                    xml_response = requests.get(f"{base_url}/api/frameworks/{framework_id}/drawio", timeout=5)
                    if xml_response.status_code == 200:
                        xml_data = xml_response.json()
                        xml_content = xml_data.get('xml', '')
                        print(f"   ✅ XML получен: {len(xml_content)} символов")
                        
                        # Проверяем, что это валидный XML
                        if xml_content.startswith('<?xml') and 'mxfile' in xml_content:
                            print(f"   ✅ XML валидный")
                        else:
                            print(f"   ❌ XML невалидный")
                    else:
                        print(f"   ❌ Ошибка получения XML: {xml_response.status_code}")
                        print(f"      Ответ: {xml_response.text}")
                
                except Exception as e:
                    print(f"   ❌ Исключение при получении XML: {e}")
                
                # Тестируем скачивание Draw.io файла
                try:
                    download_response = requests.get(f"{base_url}/api/frameworks/{framework_id}/download/drawio", timeout=5)
                    if download_response.status_code == 200:
                        print(f"   ✅ Скачивание доступно: {len(download_response.content)} байт")
                    else:
                        print(f"   ❌ Ошибка скачивания: {download_response.status_code}")
                        print(f"      Ответ: {download_response.text}")
                
                except Exception as e:
                    print(f"   ❌ Исключение при скачивании: {e}")
                    
        else:
            print(f"❌ Ошибка получения списка фреймворков: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к серверу: {e}")
        print("🔧 Убедитесь, что сервер запущен: python pik_visualization_server.py")

def check_local_files():
    """Проверяет наличие локальных файлов"""
    print("\n📁 Проверка локальных файлов")
    print("=" * 30)
    
    drawio_dir = Path("output/drawio")
    analysis_dir = Path("output/analysis")
    
    if drawio_dir.exists():
        drawio_files = list(drawio_dir.glob("*.drawio"))
        print(f"📊 Draw.io файлов: {len(drawio_files)}")
        for file in drawio_files:
            size = file.stat().st_size
            print(f"   📄 {file.name}: {size:,} байт")
    else:
        print("❌ Директория output/drawio не найдена")
    
    if analysis_dir.exists():
        analysis_files = list(analysis_dir.glob("*_analysis.json"))
        print(f"📊 Файлов анализа: {len(analysis_files)}")
        for file in analysis_files:
            size = file.stat().st_size
            print(f"   📄 {file.name}: {size:,} байт")
    else:
        print("❌ Директория output/analysis не найдена")

if __name__ == "__main__":
    check_local_files()
    test_api_endpoints()
