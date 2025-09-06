#!/usr/bin/env python3
"""
Тестовый скрипт для OCR сервера
Протестирует один из PDF файлов из папки PIK
"""

import requests
import os
import time
from pathlib import Path

# Настройки
SERVER_URL = "http://localhost:8003"
TEST_PDF_PATH = "_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Introduction - English.pdf"

def test_server_health():
    """Проверяем, что сервер запущен"""
    try:
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            print("✅ Сервер запущен и отвечает")
            return True
        else:
            print(f"❌ Сервер вернул код {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу")
        print(f"Убедитесь, что сервер запущен: uvicorn ocr_server:app --host 0.0.0.0 --port 8000")
        return False

def test_pdf_conversion():
    """Тестируем конвертацию PDF"""
    if not os.path.exists(TEST_PDF_PATH):
        print(f"❌ Тестовый файл не найден: {TEST_PDF_PATH}")
        return False
    
    print(f"📄 Тестируем конвертацию файла: {TEST_PDF_PATH}")
    
    # Параметры для сложных документов PIK
    params = {
        "mode": "complex",
        "lang": "eng+rus", 
        "scale": "4.0"
    }
    
    try:
        with open(TEST_PDF_PATH, 'rb') as file:
            files = {'file': file}
            
            print("🔄 Отправляем файл на сервер...")
            start_time = time.time()
            
            response = requests.post(
                f"{SERVER_URL}/convert",
                files=files,
                params=params,
                timeout=300  # 5 минут таймаут
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                markdown_text = result.get("markdown", "")
                
                print(f"✅ Конвертация успешна за {duration:.1f} секунд")
                print(f"📊 Размер результата: {len(markdown_text)} символов")
                
                # Сохраняем результат
                output_file = "test_result.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                print(f"💾 Результат сохранен в {output_file}")
                
                # Показываем первые 500 символов
                preview = markdown_text[:500] + "..." if len(markdown_text) > 500 else markdown_text
                print(f"\n📝 Превью результата:\n{preview}")
                
                return True
            else:
                print(f"❌ Ошибка конвертации: {response.status_code}")
                print(f"Ответ сервера: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("⏰ Таймаут запроса (более 5 минут)")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_metrics():
    """Проверяем метрики сервера"""
    try:
        response = requests.get(f"{SERVER_URL}/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print("📈 Метрики сервера:")
            print(f"  Всего запросов: {metrics.get('summary', {}).get('total_requests', 0)}")
            print(f"  Среднее время обработки: {metrics.get('summary', {}).get('average_processing_time', 0):.2f}с")
            print(f"  Время работы: {metrics.get('summary', {}).get('uptime', 0):.1f}с")
            return True
        else:
            print(f"❌ Не удалось получить метрики: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка получения метрик: {e}")
        return False

def main():
    print("🚀 Тестирование OCR сервера для PIK документов")
    print("=" * 50)
    
    # Проверяем здоровье сервера
    if not test_server_health():
        return
    
    # Проверяем метрики
    test_metrics()
    print()
    
    # Тестируем конвертацию
    if test_pdf_conversion():
        print("\n✅ Все тесты прошли успешно!")
        print("\n🎯 Рекомендации для PIK документов:")
        print("  • Используйте mode=complex или mode=max")
        print("  • Добавьте lang=eng+rus для многоязычных документов")
        print("  • Установите scale=4.0-5.0 для высокого качества")
        print("  • Проверьте результат в test_result.md")
    else:
        print("\n❌ Тестирование не прошло")
    
    print("\n📚 Проверьте README.md для подробной документации")

if __name__ == "__main__":
    main()
