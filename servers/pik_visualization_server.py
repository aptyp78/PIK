#!/usr/bin/env python3
"""
Enhanced PIK Visualization Server
=================================

Веб-сервер для визуализации результатов интеллектуального PIK парсера.
Предоставляет REST API для доступа к результатам анализа и файлам.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="PIK Visualization Server",
    description="Сервер для визуализации результатов интеллектуального PIK парсера",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Пути к файлам
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ANALYSIS_DIR = OUTPUT_DIR / "analysis"
DRAWIO_DIR = OUTPUT_DIR / "drawio"
BATCH_DIR = OUTPUT_DIR / "batch_analysis"

class PIKDataManager:
    """Менеджер для работы с данными PIK анализа"""
    
    def __init__(self):
        self.frameworks_cache = {}
        self.batch_summary = None
        self._load_data()
    
    def _load_data(self):
        """Загружает все данные анализа"""
        try:
            # Загружаем сводку пакетного анализа
            summary_file = BATCH_DIR / "methodology_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    self.batch_summary = json.load(f)
            
            # Загружаем индекс фреймворков
            index_file = BATCH_DIR / "frameworks_index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    
                # Загружаем детальные данные каждого фреймворка
                for framework_info in index_data.get("frameworks", []):
                    framework_id = framework_info["id"]
                    analysis_file = ANALYSIS_DIR / f"{framework_id}_analysis.json"
                    
                    if analysis_file.exists():
                        with open(analysis_file, 'r', encoding='utf-8') as f:
                            framework_data = json.load(f)
                            self.frameworks_cache[framework_id] = framework_data
            
            print(f"✅ Загружено {len(self.frameworks_cache)} фреймворков")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводную информацию"""
        if not self.batch_summary:
            return {
                "total_frameworks": 0,
                "total_elements": 0,
                "total_relationships": 0,
                "avg_confidence": 0.0,
                "framework_types": {}
            }
        return self.batch_summary
    
    def get_frameworks_list(self) -> List[Dict[str, Any]]:
        """Возвращает список всех фреймворков"""
        frameworks = []
        
        for framework_id, data in self.frameworks_cache.items():
            frameworks.append({
                "id": framework_id,
                "type": data.get("type", "").replace("PIKFrameworkType.", ""),
                "title": data.get("title", "Unknown"),
                "elements_count": len(data.get("elements", [])),
                "relationships_count": len(data.get("relationships", [])),
                "confidence": data.get("metadata", {}).get("confidence_score", 0.0),
                "parsed_at": data.get("metadata", {}).get("parsed_at", ""),
                "completeness": data.get("semantic_analysis", {}).get("framework_completeness", {}).get("score", 0.0),
                "methodology_alignment": data.get("semantic_analysis", {}).get("methodology_alignment", {}).get("score", 0.0)
            })
        
        return frameworks
    
    def get_framework_details(self, framework_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает детальную информацию о фреймворке"""
        return self.frameworks_cache.get(framework_id)
    
    def get_elements_by_type(self, framework_id: str) -> Dict[str, List[Dict]]:
        """Группирует элементы фреймворка по типам"""
        framework = self.get_framework_details(framework_id)
        if not framework:
            return {}
        
        elements_by_type = {}
        for element in framework.get("elements", []):
            element_type = element.get("type", "").replace("ElementType.", "")
            if element_type not in elements_by_type:
                elements_by_type[element_type] = []
            
            elements_by_type[element_type].append({
                "id": element.get("id"),
                "text": element.get("text", ""),
                "confidence": element.get("confidence", 0.0),
                "position": element.get("position", [0, 0, 0, 0]),
                "relationships_count": len(element.get("relationships", []))
            })
        
        return elements_by_type
    
    def get_network_data(self, framework_id: str) -> Dict[str, Any]:
        """Создает данные для сетевой визуализации"""
        framework = self.get_framework_details(framework_id)
        if not framework:
            return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        
        # Создаем узлы из элементов
        for i, element in enumerate(framework.get("elements", [])[:20]):  # Ограничиваем для производительности
            element_type = element.get("type", "").replace("ElementType.", "")
            
            # Цвета для разных типов элементов
            color_map = {
                "stakeholder": "#d5e8d4",
                "force": "#fff2cc", 
                "value_proposition": "#f8cecc",
                "nfx_engine": "#e1d5e7",
                "process": "#dae8fc",
                "label": "#f5f5f5"
            }
            
            nodes.append({
                "id": i,
                "label": element.get("text", "")[:20] + ("..." if len(element.get("text", "")) > 20 else ""),
                "title": f"Type: {element_type}\nConfidence: {element.get('confidence', 0):.1%}",
                "color": color_map.get(element_type, "#f5f5f5"),
                "size": min(50, max(10, element.get("confidence", 0) * 50))
            })
        
        # Создаем связи
        for rel in framework.get("relationships", [])[:50]:  # Ограничиваем для производительности
            source_id = None
            target_id = None
            
            # Находим индексы узлов
            for i, element in enumerate(framework.get("elements", [])[:20]):
                if element.get("id") == rel.get("source"):
                    source_id = i
                if element.get("id") == rel.get("target"):
                    target_id = i
            
            if source_id is not None and target_id is not None:
                edges.append({
                    "from": source_id,
                    "to": target_id,
                    "label": rel.get("type", "related"),
                    "title": f"Strength: {rel.get('strength', 0):.2f}"
                })
        
        return {"nodes": nodes, "edges": edges}

# Создаем экземпляр менеджера данных
data_manager = PIKDataManager()

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница с веб-интерфейсом"""
    html_file = BASE_DIR / "web_interface_live.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(status_code=404, detail="Web interface not found")

@app.get("/api/summary")
async def get_summary():
    """Получить сводную информацию по всем фреймворкам"""
    return JSONResponse(data_manager.get_summary())

@app.get("/api/frameworks")
async def get_frameworks():
    """Получить список всех фреймворков"""
    return JSONResponse(data_manager.get_frameworks_list())

@app.get("/api/frameworks/{framework_id}")
async def get_framework(framework_id: str):
    """Получить детальную информацию о фреймворке"""
    framework = data_manager.get_framework_details(framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    return JSONResponse(framework)

@app.get("/api/frameworks/{framework_id}/elements")
async def get_framework_elements(framework_id: str):
    """Получить элементы фреймворка, сгруппированные по типам"""
    elements = data_manager.get_elements_by_type(framework_id)
    if not elements:
        raise HTTPException(status_code=404, detail="Framework not found")
    return JSONResponse(elements)

@app.get("/api/frameworks/{framework_id}/network")
async def get_framework_network(framework_id: str):
    """Получить данные для сетевой визуализации фреймворка"""
    network_data = data_manager.get_network_data(framework_id)
    return JSONResponse(network_data)

@app.get("/api/frameworks/{framework_id}/drawio")
async def get_framework_drawio(framework_id: str):
    """Получить Draw.io XML фреймворка"""
    print(f"🔍 Поиск Draw.io файла для: {framework_id}")
    
    # Попробуем найти файл с различными суффиксами
    possible_files = [
        DRAWIO_DIR / f"{framework_id}_diagram.drawio",
        DRAWIO_DIR / f"{framework_id}.drawio",
    ]
    
    drawio_file = None
    for file_path in possible_files:
        print(f"   Проверяем: {file_path}")
        if file_path.exists():
            drawio_file = file_path
            print(f"   ✅ Найден: {file_path}")
            break
    
    if not drawio_file:
        # Попробуем найти любой файл, содержащий ID
        print(f"   🔍 Поиск файлов содержащих '{framework_id}' в {DRAWIO_DIR}")
        all_files = list(DRAWIO_DIR.glob("*.drawio"))
        print(f"   📁 Всего .drawio файлов: {len(all_files)}")
        
        for file in all_files:
            print(f"      Проверяем файл: {file.name}")
            if framework_id in file.name:
                drawio_file = file
                print(f"   ✅ Найден по содержимому ID: {file}")
                break
    
    if not drawio_file:
        print(f"   ❌ Файл не найден для {framework_id}")
        print(f"   📁 Содержимое {DRAWIO_DIR}:")
        for file in DRAWIO_DIR.glob("*"):
            print(f"      - {file.name}")
        raise HTTPException(status_code=404, detail=f"Draw.io file not found for {framework_id}")
    
    try:
        with open(drawio_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"   ✅ Файл загружен: {len(content)} символов")
        return JSONResponse({"xml": content})
    except Exception as e:
        print(f"   ❌ Ошибка чтения файла: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

@app.get("/api/frameworks/{framework_id}/download/json")
async def download_framework_json(framework_id: str):
    """Скачать JSON анализ фреймворка"""
    json_file = ANALYSIS_DIR / f"{framework_id}_analysis.json"
    if not json_file.exists():
        raise HTTPException(status_code=404, detail="JSON file not found")
    
    return FileResponse(
        path=json_file,
        filename=f"{framework_id}_analysis.json",
        media_type="application/json"
    )

@app.get("/api/frameworks/{framework_id}/download/drawio")
async def download_framework_drawio(framework_id: str):
    """Скачать Draw.io файл фреймворка"""
    print(f"🔍 Скачивание Draw.io файла для: {framework_id}")
    
    # Попробуем найти файл с различными суффиксами
    possible_files = [
        DRAWIO_DIR / f"{framework_id}_diagram.drawio",
        DRAWIO_DIR / f"{framework_id}.drawio",
    ]
    
    drawio_file = None
    for file_path in possible_files:
        print(f"   Проверяем: {file_path}")
        if file_path.exists():
            drawio_file = file_path
            print(f"   ✅ Найден: {file_path}")
            break
    
    if not drawio_file:
        # Попробуем найти любой файл, содержащий ID
        print(f"   🔍 Поиск файлов содержащих '{framework_id}' в {DRAWIO_DIR}")
        for file in DRAWIO_DIR.glob("*.drawio"):
            print(f"      Проверяем файл: {file.name}")
            if framework_id in file.name:
                drawio_file = file
                print(f"   ✅ Найден по содержимому ID: {file}")
                break
    
    if not drawio_file:
        print(f"   ❌ Файл не найден для {framework_id}")
        raise HTTPException(status_code=404, detail=f"Draw.io file not found for {framework_id}")
    
    return FileResponse(
        path=drawio_file,
        filename=f"{framework_id}_diagram.drawio",
        media_type="application/xml"
    )

@app.get("/api/drawio/{filename}")
async def get_drawio_file(filename: str):
    """Скачать конкретный Draw.io файл"""
    print(f"🔍 Запрос Draw.io файла: {filename}")
    
    drawio_file = DRAWIO_DIR / filename
    if not drawio_file.exists():
        print(f"   ❌ Файл не найден: {drawio_file}")
        raise HTTPException(status_code=404, detail=f"Draw.io file {filename} not found")
    
    try:
        print(f"   ✅ Отправляем файл: {drawio_file}")
        return FileResponse(
            path=drawio_file,
            filename=filename,
            media_type="application/xml"
        )
    except Exception as e:
        print(f"   ❌ Ошибка отправки файла: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {e}")

@app.get("/test_drawio_files.html", response_class=HTMLResponse)
async def test_drawio_page():
    """Тестовая страница для проверки Draw.io файлов"""
    html_file = BASE_DIR / "test_drawio_files.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    raise HTTPException(status_code=404, detail="Test page not found")

@app.get("/api/insights")
async def get_insights():
    """Получить ключевые инсайты анализа"""
    summary = data_manager.get_summary()
    frameworks = data_manager.get_frameworks_list()
    
    insights = []
    
    if summary.get("total_elements", 0) > 0:
        insights.append({
            "type": "statistics",
            "icon": "📊",
            "text": f"Извлечено {summary['total_elements']:,} элементов из {summary['total_frameworks']} фреймворков"
        })
    
    if summary.get("total_relationships", 0) > 0:
        insights.append({
            "type": "network",
            "icon": "🔗", 
            "text": f"Обнаружено {summary['total_relationships']:,} связей между элементами экосистемы"
        })
    
    # Анализ по типам фреймворков
    framework_types = summary.get("framework_types", {})
    for fw_type, data in framework_types.items():
        if data.get("methodology_alignment", 0) == 1.0:
            insights.append({
                "type": "quality",
                "icon": "✅",
                "text": f"Фреймворк {fw_type} показывает 100% соответствие PIK методологии"
            })
    
    # Анализ покрытия жизненного цикла
    coverage = summary.get("coverage_analysis", {})
    if coverage.get("lifecycle_coverage", 0) > 0.7:
        insights.append({
            "type": "coverage",
            "icon": "🎯",
            "text": f"Покрытие PIK жизненного цикла: {coverage['lifecycle_coverage']:.0%}"
        })
    
    # Возможности автоматизации
    auto_opportunities = summary.get("automation_opportunities", {})
    if auto_opportunities:
        insights.append({
            "type": "automation",
            "icon": "🤖", 
            "text": f"Выявлено {len(auto_opportunities)} возможностей для автоматизации"
        })
    
    return JSONResponse(insights)

@app.get("/api/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "frameworks_loaded": len(data_manager.frameworks_cache),
        "data_available": data_manager.batch_summary is not None
    })

# Статические файлы (CSS, JS, изображения)
if (BASE_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Монтируем output директорию для доступа к файлам
if OUTPUT_DIR.exists():
    app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

def main():
    """Запуск сервера"""
    print("🚀 Запуск PIK Visualization Server...")
    print(f"📁 Базовая директория: {BASE_DIR}")
    print(f"📊 Загружено фреймворков: {len(data_manager.frameworks_cache)}")
    print(f"🌐 Веб-интерфейс будет доступен по адресу: http://localhost:8001")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
