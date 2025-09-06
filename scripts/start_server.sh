#!/bin/bash

# Скрипт запуска OCR сервера для PIK документов
echo "🚀 Запуск OCR сервера для обработки PIK документов"
echo "================================================"

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверяем Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract не найден. Установите Tesseract OCR:"
    echo "  macOS: brew install tesseract tesseract-lang"
    echo "  Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-rus"
    exit 1
fi

echo "✅ Python и Tesseract найдены"

# Устанавливаем зависимости если нужно
if [ ! -d "venv" ]; then
    echo "📦 Создаем виртуальное окружение..."
    python3 -m venv venv
fi

echo "🔧 Активируем виртуальное окружение..."
source venv/bin/activate

echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

echo "🏃‍♂️ Запускаем OCR сервер..."
echo "Сервер будет доступен по адресу: http://localhost:8000"
echo "Для остановки нажмите Ctrl+C"
echo ""

# Запускаем сервер
uvicorn ocr_server:app --host 0.0.0.0 --port 8000 --reload
