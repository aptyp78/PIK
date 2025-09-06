#!/usr/bin/env python3
"""
Простой тест OCR функций без веб-сервера
"""
import os
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_ocr():
    try:
        # Импортируем функции из нашего сервера
        from ocr_server import pdf_to_md, validate_pdf_file
        
        # Путь к тестовому PDF
        test_pdf = "_Sources/Ontology PIK/PIK-5-Core-Kit/PIK 5-0 - Introduction - English.pdf"
        
        if not os.path.exists(test_pdf):
            print(f"❌ Файл не найден: {test_pdf}")
            return False
        
        print(f"📄 Тестируем файл: {test_pdf}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(test_pdf)
        print(f"📊 Размер файла: {file_size/1024/1024:.1f} MB")
        
        # Валидируем PDF
        with open(test_pdf, 'rb') as f:
            pdf_data = f.read()
        
        if not validate_pdf_file(pdf_data):
            print("❌ PDF файл не прошел валидацию")
            return False
        
        print("✅ PDF файл валиден")
        
        # Пробуем извлечь текст
        print("🔄 Запускаем OCR (это может занять несколько минут)...")
        
        # Используем простые настройки для первого теста
        markdown_text = pdf_to_md(
            test_pdf, 
            ocr_scale=2.0,  # Низкое разрешение для быстрого теста
            do_corner=False,  # Отключаем углы для ускорения
            lang="eng",  # Только английский
            angles=(0,)  # Только прямой угол
        )
        
        print(f"✅ OCR завершен! Извлечено {len(markdown_text)} символов")
        
        # Сохраняем результат
        output_file = "test_result_simple.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        print(f"💾 Результат сохранен в {output_file}")
        
        # Показываем первые 300 символов
        preview = markdown_text[:300] + "..." if len(markdown_text) > 300 else markdown_text
        print(f"\n📝 Превью результата:\n{'-'*50}")
        print(preview)
        print('-'*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Простой тест OCR функций")
    print("="*40)
    
    if test_pdf_ocr():
        print("\n✅ Тест прошел успешно!")
    else:
        print("\n❌ Тест провален")
