#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import uvicorn
import asyncio
import aiofiles
import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel
import uuid
import logging
from pathlib import Path

# Импорты наших модулей
try:
    from enhanced_ocr import enhanced_pdf_to_md_with_images
    from smart_cache import SmartCache
    from multi_ocr_engine import MultiOCREngine
except ImportError as e:
    print(f"⚠️  Предупреждение импорта: {e}")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели данных
class OCRRequest(BaseModel):
    engine: str = "multi"
    document_type: str = "pik_diagram"
    quality_level: int = 2
    use_cache: bool = True
    extract_images: bool = True
    semantic_analysis: bool = True
    language: str = "eng+rus"

class OCRResult(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None

class BatchRequest(BaseModel):
    files: List[str]
    ocr_config: OCRRequest
    output_format: str = "markdown"

# Глобальные переменные
app = FastAPI(
    title="PIK OCR API",
    description="Интеллектуальная система распознавания PIK документов",
    version="2.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилища задач и кэш
tasks_storage: Dict[str, OCRResult] = {}
cache = SmartCache(cache_dir="OCR/cache", max_cache_size_mb=500)

# Создание необходимых директорий
os.makedirs("uploads", exist_ok=True)
os.makedirs("OCR", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# API ключ (простая аутентификация)
API_KEY = "pik-ocr-2024-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """Простая проверка API ключа"""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Маршруты

@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Возвращает веб-интерфейс"""
    try:
        with open("web_interface.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html><body>
        <h1>PIK OCR API</h1>
        <p>Веб-интерфейс не найден. Используйте API напрямую:</p>
        <ul>
            <li><a href="/docs">API документация</a></li>
            <li><a href="/health">Проверка здоровья</a></li>
            <li><a href="/stats">Статистика</a></li>
        </ul>
        </body></html>
        """)

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "components": {}
    }
    
    # Проверяем компоненты
    try:
        # Tesseract
        import pytesseract
        pytesseract.get_tesseract_version()
        health_status["components"]["tesseract"] = "available"
    except Exception:
        health_status["components"]["tesseract"] = "unavailable"
    
    try:
        # EasyOCR
        import easyocr
        health_status["components"]["easyocr"] = "available"
    except Exception:
        health_status["components"]["easyocr"] = "unavailable"
    
    try:
        # Кэш
        cache_stats = cache.get_cache_stats()
        health_status["components"]["cache"] = {
            "status": "available",
            "entries": cache_stats["total_entries"],
            "size_mb": round(cache_stats["cache_size_mb"], 1)
        }
    except Exception as e:
        health_status["components"]["cache"] = f"error: {str(e)}"
    
    # Активные задачи
    active_tasks = len([t for t in tasks_storage.values() if t.status == "processing"])
    health_status["active_tasks"] = active_tasks
    
    return health_status

@app.get("/stats")
async def get_system_stats():
    """Получение статистики системы"""
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "tasks": {
            "total": len(tasks_storage),
            "completed": len([t for t in tasks_storage.values() if t.status == "completed"]),
            "failed": len([t for t in tasks_storage.values() if t.status == "failed"]),
            "processing": len([t for t in tasks_storage.values() if t.status == "processing"])
        },
        "cache": cache.get_cache_stats(),
        "system": {
            "uptime_hours": (time.time() - start_time) / 3600,
            "upload_dir_size_mb": sum(
                f.stat().st_size for f in Path("uploads").glob("**/*") if f.is_file()
            ) / 1024 / 1024 if os.path.exists("uploads") else 0,
            "ocr_results_count": len(list(Path("OCR").glob("**/*.md"))) if os.path.exists("OCR") else 0
        }
    }
    
    return stats

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка файла"""
    
    # Проверки
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Поддерживаются только PDF файлы")
    
    if file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=400, detail="Файл слишком большой (максимум 100MB)")
    
    # Сохранение файла
    file_id = str(uuid.uuid4())
    file_path = f"uploads/{file_id}_{file.filename}"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "path": file_path
    }

@app.post("/process")
async def process_document(
    background_tasks: BackgroundTasks,
    file_path: str,
    config: OCRRequest,
    api_key: str = Depends(verify_api_key)
):
    """Запуск обработки документа"""
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Создание задачи
    task_id = str(uuid.uuid4())
    task = OCRResult(
        task_id=task_id,
        status="queued",
        progress=0.0,
        message="Задача добавлена в очередь",
        created_at=datetime.now().isoformat()
    )
    
    tasks_storage[task_id] = task
    
    # Запуск фоновой обработки
    background_tasks.add_task(process_document_background, task_id, file_path, config)
    
    return {"task_id": task_id, "status": "queued"}

async def process_document_background(task_id: str, file_path: str, config: OCRRequest):
    """Фоновая обработка документа"""
    
    task = tasks_storage[task_id]
    start_time = time.time()
    
    try:
        # Обновляем статус
        task.status = "processing"
        task.progress = 10.0
        task.message = "Начинаем обработку..."
        
        # Проверяем кэш
        if config.use_cache:
            cache_key_config = config.dict()
            if cache.is_cached(file_path, cache_key_config):
                cached_result = cache.get_cached_result(file_path, cache_key_config)
                if cached_result:
                    task.status = "completed"
                    task.progress = 100.0
                    task.message = "Результат получен из кэша"
                    task.result = cached_result
                    task.processing_time = time.time() - start_time
                    task.completed_at = datetime.now().isoformat()
                    return
        
        # Инициализация OCR движка
        task.progress = 20.0
        task.message = "Инициализация OCR движка..."
        
        if config.engine == "multi":
            ocr_engine = MultiOCREngine()
        
        # Обработка документа
        task.progress = 30.0
        task.message = "Извлечение изображений..."
        
        # Используем существующую функцию
        result_md = enhanced_pdf_to_md_with_images(file_path)
        
        task.progress = 70.0
        task.message = "Применение семантического анализа..."
        
        # Дополнительная обработка на основе конфигурации
        if config.semantic_analysis:
            # Здесь можно добавить дополнительный семантический анализ
            pass
        
        task.progress = 90.0
        task.message = "Формирование результатов..."
        
        # Подготовка результата
        processing_time = time.time() - start_time
        
        result = {
            "text": result_md,
            "metadata": {
                "file_path": file_path,
                "processing_time": processing_time,
                "engine": config.engine,
                "document_type": config.document_type,
                "timestamp": datetime.now().isoformat()
            },
            "statistics": {
                "text_length": len(result_md),
                "sections": result_md.count("##"),
                "images": result_md.count("!["),
                "tables": result_md.count("📊 Таблица")
            }
        }
        
        # Сохранение в кэш
        if config.use_cache:
            cache.cache_result(
                file_path, 
                cache_key_config, 
                result,
                processing_time=processing_time,
                quality_score=85.0,  # Можно вычислить реальную оценку
                document_type=config.document_type
            )
        
        # Завершение задачи
        task.status = "completed"
        task.progress = 100.0
        task.message = "Обработка завершена успешно"
        task.result = result
        task.processing_time = processing_time
        task.completed_at = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"Ошибка обработки задачи {task_id}: {e}")
        task.status = "failed"
        task.error = str(e)
        task.message = f"Ошибка: {str(e)}"
        task.completed_at = datetime.now().isoformat()

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Получение статуса задачи"""
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return tasks_storage[task_id]

@app.get("/tasks")
async def list_tasks(limit: int = 50, status: Optional[str] = None):
    """Список всех задач"""
    
    tasks = list(tasks_storage.values())
    
    if status:
        tasks = [t for t in tasks if t.status == status]
    
    # Сортировка по дате создания (новые первые)
    tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "tasks": tasks[:limit],
        "total": len(tasks_storage),
        "filtered": len(tasks)
    }

@app.post("/batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    request: BatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """Пакетная обработка файлов"""
    
    batch_id = str(uuid.uuid4())
    
    # Создаем задачи для каждого файла
    task_ids = []
    for file_path in request.files:
        if os.path.exists(file_path):
            task_id = str(uuid.uuid4())
            task = OCRResult(
                task_id=task_id,
                status="queued",
                progress=0.0,
                message=f"Файл в пакете {batch_id}",
                created_at=datetime.now().isoformat()
            )
            
            tasks_storage[task_id] = task
            task_ids.append(task_id)
            
            # Запуск фоновой обработки
            background_tasks.add_task(
                process_document_background, 
                task_id, 
                file_path, 
                request.ocr_config
            )
    
    return {
        "batch_id": batch_id,
        "task_ids": task_ids,
        "total_files": len(request.files),
        "queued_files": len(task_ids)
    }

@app.get("/download/{task_id}")
async def download_result(task_id: str, format: str = "markdown"):
    """Скачивание результата задачи"""
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    task = tasks_storage[task_id]
    
    if task.status != "completed" or not task.result:
        raise HTTPException(status_code=400, detail="Результат не готов")
    
    if format == "json":
        content = json.dumps(task.result, ensure_ascii=False, indent=2)
        media_type = "application/json"
        filename = f"ocr_result_{task_id}.json"
    else:  # markdown
        content = task.result.get("text", "")
        media_type = "text/markdown"
        filename = f"ocr_result_{task_id}.md"
    
    # Сохраняем временный файл
    temp_path = f"temp_{filename}"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return FileResponse(
        temp_path,
        media_type=media_type,
        filename=filename
    )

@app.delete("/task/{task_id}")
async def delete_task(task_id: str, api_key: str = Depends(verify_api_key)):
    """Удаление задачи"""
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    del tasks_storage[task_id]
    return {"message": "Задача удалена"}

@app.post("/cache/clear")
async def clear_cache(older_than_hours: Optional[int] = None, api_key: str = Depends(verify_api_key)):
    """Очистка кэша"""
    
    try:
        cache.clear_cache(older_than_hours)
        return {"message": f"Кэш очищен (старше {older_than_hours}ч)" if older_than_hours else "Кэш полностью очищен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {str(e)}")

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Глобальная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Внутренняя ошибка сервера", "detail": str(exc)}
    )

# Запуск сервера
start_time = time.time()

if __name__ == "__main__":
    print("🚀 Запуск PIK OCR API Server v2.0")
    print("=" * 50)
    print("📄 Веб-интерфейс: http://localhost:8000")
    print("📋 API документация: http://localhost:8000/docs")
    print("🏥 Проверка здоровья: http://localhost:8000/health")
    print("📊 Статистика: http://localhost:8000/stats")
    print("🔑 API ключ: pik-ocr-2024-secret-key")
    print("=" * 50)
    
    uvicorn.run(
        "advanced_ocr_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
