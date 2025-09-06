#!/usr/bin/env python3
"""
Draw.io Files Downloader
========================

Создает архив со всеми Draw.io файлами для удобного скачивания
"""

import os
import zipfile
import shutil
from pathlib import Path
import json

def create_drawio_package():
    """Создает пакет со всеми Draw.io файлами"""
    print("📦 Создание пакета Draw.io файлов...")
    
    # Пути
    drawio_dir = Path("output/drawio")
    analysis_dir = Path("output/analysis")
    package_dir = Path("PIK_DrawIO_Package")
    
    # Создаем временную папку
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Создаем структуру
    (package_dir / "drawio_files").mkdir()
    (package_dir / "analysis_reports").mkdir()
    (package_dir / "instructions").mkdir()
    
    # Копируем Draw.io файлы
    print("📄 Копирование Draw.io файлов...")
    copied_files = []
    
    if drawio_dir.exists():
        for drawio_file in drawio_dir.glob("*.drawio"):
            if not drawio_file.name.endswith('.backup'):
                dest = package_dir / "drawio_files" / drawio_file.name
                shutil.copy2(drawio_file, dest)
                copied_files.append(drawio_file.name)
                print(f"   ✅ {drawio_file.name}")
    
    # Копируем анализы
    print("📊 Копирование отчетов анализа...")
    if analysis_dir.exists():
        for analysis_file in analysis_dir.glob("*_analysis.json"):
            dest = package_dir / "analysis_reports" / analysis_file.name
            shutil.copy2(analysis_file, dest)
            print(f"   ✅ {analysis_file.name}")
    
    # Создаем инструкцию
    create_instructions(package_dir / "instructions", copied_files)
    
    # Создаем архив
    print("🗜️ Создание ZIP архива...")
    zip_path = "PIK_DrawIO_Complete_Package.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir.parent)
                zipf.write(file_path, arcname)
    
    # Удаляем временную папку
    shutil.rmtree(package_dir)
    
    # Показываем результат
    zip_size = os.path.getsize(zip_path) / 1024 / 1024  # MB
    print(f"\n🎉 ПАКЕТ СОЗДАН УСПЕШНО!")
    print(f"📁 Файл: {zip_path}")
    print(f"💾 Размер: {zip_size:.1f} MB")
    print(f"📄 Включено {len(copied_files)} Draw.io файлов")
    
    return zip_path

def create_instructions(instructions_dir, file_list):
    """Создает подробные инструкции"""
    
    # README файл
    readme_content = f"""# PIK Framework Draw.io Files

## 📋 Содержимое пакета

### 🎨 Draw.io файлы ({len(file_list)} штук):
"""
    
    framework_info = {
        "pik_20250906_192036_2ed9d0bf_diagram.drawio": {
            "name": "TOUCHPOINTS",
            "type": "Business Model Canvas",
            "elements": 545,
            "connections": 4490,
            "accuracy": "86.4%"
        },
        "pik_20250906_192040_9f20687b_diagram.drawio": {
            "name": "MOTIVATION", 
            "type": "Ecosystem Forces",
            "elements": 346,
            "connections": 2760,
            "accuracy": "86.6%"
        },
        "pik_20250906_192042_43f6d2f9_diagram.drawio": {
            "name": "SUSTAINABILITY",
            "type": "NFX Reinforcement",
            "elements": 80,
            "connections": 207,
            "accuracy": "80.5%"
        },
        "pik_20250906_192045_fab9493e_diagram.drawio": {
            "name": "ENVIRONMENT",
            "type": "Forces Scan", 
            "elements": 191,
            "connections": 1420,
            "accuracy": "82.5%"
        },
        "pik_20250906_192047_d4b8a70e_diagram.drawio": {
            "name": "CONSUMERS",
            "type": "Value Network",
            "elements": 71,
            "connections": 175,
            "accuracy": "79.1%"
        }
    }
    
    for file in file_list:
        if file in framework_info:
            info = framework_info[file]
            readme_content += f"""
- **{info['name']}** ({info['type']})
  - Файл: `{file}`
  - Элементов: {info['elements']}
  - Связей: {info['connections']} 
  - Точность: {info['accuracy']}
"""
    
    readme_content += """

### 📊 Отчеты анализа:
- JSON файлы с детальными результатами анализа
- Статистика по каждому фреймворку
- Данные о связях и элементах

## 🚀 Как открыть файлы

### Метод 1: Простая загрузка (рекомендуется)

1. Откройте [Draw.io](https://app.diagrams.net/?splash=0) в браузере
2. Нажмите "Open Existing Diagram" 
3. Выберите "Device"
4. Загрузите нужный .drawio файл из папки `drawio_files/`

### Метод 2: Drag & Drop

1. Откройте [Draw.io](https://app.diagrams.net/) 
2. Просто перетащите .drawio файл в окно браузера

### Метод 3: Прямая ссылка

```
https://app.diagrams.net/?splash=0&url=file:///path/to/your/file.drawio
```

## 🎯 Описание фреймворков

### TOUCHPOINTS (Business Model Canvas)
- Самый крупный фреймворк с 545 элементами
- Полная модель бизнес-платформы
- Ключевые разделы: поставщики, ресурсы, ценности, клиенты, партнеры

### MOTIVATION (Ecosystem Forces) 
- Анализ движущих сил экосистемы
- 346 элементов мотивационных факторов
- Высокая точность анализа 86.6%

### SUSTAINABILITY (NFX Reinforcement)
- Механизмы усиления сетевых эффектов
- Компактный, но важный фреймворк
- Фокус на долгосрочной устойчивости

### ENVIRONMENT (Forces Scan)
- Сканирование внешних факторов
- 191 элемент анализа среды
- Стратегический контекст платформы

### CONSUMERS (Value Network)
- Сетевая модель создания ценности
- Фокус на потребительские сегменты
- Анализ цепочек ценности

## ✨ Особенности файлов

- ✅ Высокое качество (75.4/100)
- ✅ Правильная XML структура  
- ✅ Совместимость со всеми версиями Draw.io
- ✅ Интеллектуальное размещение элементов
- ✅ Цветовая кодировка по типам элементов

## 🆘 Поддержка

Если возникнут проблемы:
1. Убедитесь, что используете файлы из папки `drawio_files/`
2. Попробуйте разные методы открытия
3. Проверьте, что файл не поврежден

---
*Создано PIK Framework Management System v2.0*
"""
    
    # Сохраняем README
    with open(instructions_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Создаем HTML инструкцию
    html_instructions = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>PIK Draw.io Files - Instructions</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .file {{ background: #f0f8ff; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .method {{ background: #f5f5f5; padding: 20px; margin: 15px 0; border-radius: 8px; }}
        h1, h2 {{ color: #2c3e50; }}
        .btn {{ background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>🎨 PIK Framework Draw.io Files</h1>
    
    <div class="method">
        <h2>🚀 Быстрый старт</h2>
        <ol>
            <li>Откройте <a href="https://app.diagrams.net/?splash=0" target="_blank" class="btn">Draw.io</a></li>
            <li>Нажмите "Open Existing Diagram"</li>
            <li>Выберите "Device"</li>
            <li>Загрузите любой .drawio файл</li>
        </ol>
    </div>
    
    <h2>📁 Ваши файлы:</h2>
"""
    
    for file in file_list:
        if file in framework_info:
            info = framework_info[file]
            html_instructions += f"""
    <div class="file">
        <strong>{info['name']}</strong> ({info['type']})<br>
        📄 Файл: {file}<br>
        📊 {info['elements']} элементов, {info['connections']} связей<br>
        🎯 Точность: {info['accuracy']}
    </div>
"""
    
    html_instructions += """
    <div class="method">
        <h2>💡 Советы</h2>
        <ul>
            <li>Все файлы работают без авторизации Google</li>
            <li>Для лучшего качества используйте настольную версию Draw.io</li>
            <li>Файлы можно редактировать и сохранять локально</li>
        </ul>
    </div>
</body>
</html>
"""
    
    with open(instructions_dir / "instructions.html", 'w', encoding='utf-8') as f:
        f.write(html_instructions)

def main():
    """Главная функция"""
    print("""
📦 PIK Draw.io Package Creator
==============================

Создает ZIP архив со всеми Draw.io файлами
и подробными инструкциями по использованию.
""")
    
    try:
        zip_path = create_drawio_package()
        
        print(f"""
✅ ГОТОВО! 

📂 Создан архив: {zip_path}
🎯 Содержит все PIK фреймворки в формате Draw.io
📋 Включены подробные инструкции

💡 Теперь вы можете:
1. Скачать архив 
2. Распаковать его
3. Открывать файлы в Draw.io без авторизации

🌐 Или используйте веб-интерфейс: drawio_viewer_no_auth.html
""")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
