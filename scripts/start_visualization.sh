#!/bin/bash

# PIK Intelligent Parser - Система визуализации
# Быстрый запуск веб-интерфейса для анализа результатов

echo "🧠 PIK Intelligent Parser - Система визуализации"
echo "=================================================="

# Проверяем, существуют ли результаты анализа
if [ ! -d "output/analysis" ] || [ -z "$(ls -A output/analysis)" ]; then
    echo "❌ Результаты анализа не найдены!"
    echo "📋 Сначала запустите анализ:"
    echo "   python batch_pik_analysis.py"
    exit 1
fi

# Подсчитываем количество проанализированных фреймворков
framework_count=$(ls output/analysis/*.json 2>/dev/null | wc -l)
echo "📊 Найдено $framework_count проанализированных фреймворков"

# Проверяем зависимости
echo "🔍 Проверка зависимостей..."
.venv/bin/python -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "❌ Не установлены веб-зависимости!"
    echo "📦 Устанавливаем..."
    .venv/bin/pip install fastapi uvicorn[standard]
}

# Запускаем сервер
echo "🚀 Запуск веб-сервера..."
echo "🌐 Интерфейс будет доступен по адресу: http://localhost:8001"
echo "⏹️  Для остановки нажмите Ctrl+C"
echo ""

.venv/bin/python pik_visualization_server.py
