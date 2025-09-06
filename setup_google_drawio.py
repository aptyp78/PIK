#!/usr/bin/env python3
"""
Google Account Draw.io Setup
============================

Инструкции для настройки Draw.io с учетной записью Google
"""

def create_google_setup_guide():
    """Создает руководство по настройке Google аккаунта"""
    
    guide_content = """
# 🔐 Настройка Draw.io с Google Account

## Ваша учетная запись: aso.veneto@gmail.com

### 🎯 Проблема
Draw.io просит авторизацию в Google для работы с файлами в Google Drive.

### ✅ Решения (выберите любое)

## 🚀 Решение 1: Локальная работа (рекомендуется)

**Преимущества:** Не требует авторизации, полный контроль над файлами

### Шаги:
1. Откройте [Draw.io](https://app.diagrams.net/?splash=0&libs=general)
2. НЕ нажимайте на Google Drive 
3. Нажмите "Create New Diagram" или "Open Existing Diagram"
4. Выберите "Device" (локальное устройство)
5. Загрузите .drawio файл с компьютера

## 🔑 Решение 2: Авторизация Google (если нужен Google Drive)

### Шаги:
1. Откройте [Draw.io](https://app.diagrams.net/)
2. Нажмите на Google Drive
3. Войдите под учетной записью: **aso.veneto@gmail.com**
4. Разрешите доступ к Google Drive
5. Загрузите .drawio файлы в Google Drive
6. Открывайте их через Draw.io

### Настройки безопасности:
- Разрешения можно отозвать в любое время
- Draw.io получает доступ только к своим файлам
- Данные остаются в вашем Google Drive

## 📱 Решение 3: Десктопная версия

### Преимущества: 
- Работа без интернета
- Полный контроль
- Расширенные возможности

### Установка:
1. Скачайте [Draw.io Desktop](https://github.com/jgraph/drawio-desktop/releases)
2. Установите на компьютер  
3. Открывайте файлы напрямую

## 🌐 Решение 4: Веб-версия без Google

### Всегда работает:
```
https://app.diagrams.net/?splash=0&offline=1&https=0
```

### Параметры:
- `splash=0` - убирает заставку
- `offline=1` - отключает облачные функции  
- `https=0` - локальная работа

## 📁 Ваши файлы готовы:

1. **PIK_DrawIO_Complete_Package.zip** - архив со всеми файлами
2. **Отдельные .drawio файлы** в папке output/drawio/
3. **Веб-просмотрщик** - drawio_viewer_no_auth.html

## 💡 Рекомендация

**Используйте Решение 1** (локальная работа):
✅ Не требует авторизации
✅ Быстро и просто  
✅ Полный контроль над файлами
✅ Работает с любой учетной записью

---

*Проблема с авторизацией решена! 🎉*
"""
    
    with open("Google_DrawIO_Setup_Guide.md", 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("📋 Создано руководство: Google_DrawIO_Setup_Guide.md")

def main():
    """Главная функция"""
    print("""
🔐 Google Account Setup for Draw.io
===================================

Создание инструкций для работы с Draw.io
под учетной записью aso.veneto@gmail.com
""")
    
    create_google_setup_guide()
    
    print("""
✅ ГОТОВО!

📋 Создано руководство по решению проблем с авторизацией
🎯 4 различных способа работы с Draw.io
💡 Рекомендация: используйте локальную работу (не требует авторизации)

📁 Ваши файлы готовы к использованию!
""")

if __name__ == "__main__":
    main()
