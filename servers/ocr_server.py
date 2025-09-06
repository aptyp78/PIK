from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, uuid
import pdfplumber, pytesseract
from PIL import Image, ImageOps, ImageFilter
import pypdfium2 as pdfium
import logging, time
from collections import defaultdict

try:
    import cv2
    import numpy as np
    from sklearn.cluster import DBSCAN  # для группировки текстовых блоков
    HAS_ADVANCED = True
except Exception:
    cv2 = None
    np = None
    DBSCAN = None
    HAS_ADVANCED = False

app = FastAPI(title="ocr-ai", version="0.1.0")

# Configuration constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # увеличиваем до 100MB для сложных PDF
SUPPORTED_FORMATS = {'.pdf'}

# Advanced OCR settings for complex documents
COMPLEX_OCR_SETTINGS = {
    "high_dpi": 4.0,        # высокое разрешение для деталей
    "detection_modes": [3, 6, 8, 11, 13],  # множественные PSM режимы
    "languages": ["eng", "rus"],  # поддержка русского языка
    "preprocessing_steps": ["denoise", "sharpen", "contrast", "binarize"],
    "table_detection": True,
    "diagram_analysis": True,
    "text_grouping": True
}

# Metrics collection
METRICS = defaultdict(int)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["app://obsidian.md", "http://localhost", "http://127.0.0.1", "null", "*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store for Marker-compatible polling
TASKS = {}

logger = logging.getLogger("ocr_server")
logging.basicConfig(level=logging.INFO)

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Limit file upload size for security"""
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            raise HTTPException(413, "File too large")
    return await call_next(request)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.time()
    ua = request.headers.get("user-agent", "")
    acc = request.headers.get("accept", "")
    ct = request.headers.get("content-type", "")
    
    resp = await call_next(request)
    
    dt = int((time.time() - t0) * 1000)
    
    # Collect metrics
    METRICS[f"{request.method}_{request.url.path}"] += 1
    METRICS["total_requests"] += 1
    METRICS["total_processing_time"] += (time.time() - t0)
    
    try:
        logger.info(f"%s %s -> %s in %dms | UA=%s | Accept=%s | CT=%s",
                    request.method, request.url.path, resp.status_code, dt,
                    ua[:80], acc, ct)
    except Exception:
        pass
    return resp

@app.get("/")
def root():
    return {"name": "ocr-ai", "version": "0.1.0", "status": "running"}

def advanced_preprocess(img: Image.Image, mode: str = "complex") -> list:
    """Продвинутая предобработка для сложных документов"""
    if not HAS_ADVANCED:
        return [img.convert("L")]
    
    processed_images = []
    
    try:
        # Конвертируем в numpy array
        img_array = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # 1. Оригинальное изображение с улучшением контраста
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        processed_images.append(Image.fromarray(enhanced))
        
        # 2. Адаптивная бинаризация для текста
        adaptive_thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )
        processed_images.append(Image.fromarray(adaptive_thresh))
        
        # 3. Морфологические операции для соединения разорванного текста
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        morph = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(Image.fromarray(morph))
        
        # 4. Удаление шума для диаграмм
        denoised = cv2.medianBlur(enhanced, 3)
        processed_images.append(Image.fromarray(denoised))
        
        # 5. Обработка для таблиц - выделение горизонтальных и вертикальных линий
        if mode == "table":
            # Горизонтальные линии
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Вертикальные линии  
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_OPEN, vertical_kernel)
            
            # Комбинируем линии
            table_structure = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            processed_images.append(Image.fromarray(table_structure))
        
    except Exception as e:
        logger.warning(f"Advanced preprocessing failed: {e}")
        processed_images = [img.convert("L")]
    
    return processed_images

def detect_layout_regions(img: Image.Image) -> dict:
    """Определение областей документа: текст, таблицы, диаграммы"""
    if not HAS_ADVANCED:
        return {"text": [(0, 0, img.width, img.height)]}
    
    try:
        img_array = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Находим контуры
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = {"text": [], "table": [], "diagram": []}
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / h if h > 0 else 0
            
            # Классификация по размеру и пропорциям
            if area > 10000:  # Большие области
                if 0.5 < aspect_ratio < 2.0:  # Квадратные - возможно диаграммы
                    regions["diagram"].append((x, y, x+w, y+h))
                else:  # Прямоугольные - возможно таблицы
                    regions["table"].append((x, y, x+w, y+h))
            elif area > 1000:  # Средние области - текст
                regions["text"].append((x, y, x+w, y+h))
        
        # Если не нашли ничего, возвращаем всю страницу как текст
        if not any(regions.values()):
            regions["text"] = [(0, 0, img.width, img.height)]
            
        return regions
        
    except Exception as e:
        logger.warning(f"Layout detection failed: {e}")
        return {"text": [(0, 0, img.width, img.height)]}

def clean_ocr_text(text: str) -> str:
    """Очистка и улучшение результатов OCR"""
    import re
    
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Исправляем частые ошибки OCR
    corrections = {
        r'\b1\b': 'I',  # Цифра 1 вместо I
        r'\b0\b': 'O',  # Цифра 0 вместо O
        r'([a-z])1([a-z])': r'\1l\2',  # 1 вместо l в середине слов
        r'rn': 'm',     # rn часто читается как m
        r'([A-Z])\s+([a-z])': r'\1\2',  # Склеиваем разорванные слова
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    
    return text.strip()

def similarity_ratio(s1: str, s2: str) -> float:
    """Простое вычисление похожести строк"""
    if not s1 or not s2:
        return 0.0
    
    # Простая метрика на основе общих слов
    words1 = set(s1.split())
    words2 = set(s2.split())
    
    if not words1 and not words2:
        return 1.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def deduplicate_text_results(results: list) -> str:
    """Дедупликация и объединение результатов OCR"""
    if not results:
        return ""
    
    # Удаляем дубликаты на основе сходства
    unique_results = []
    
    for result in results:
        normalized = ' '.join(result.lower().split())
        is_duplicate = False
        
        for existing in unique_results:
            existing_normalized = ' '.join(existing.lower().split())
            
            # Если тексты очень похожи (более 80% совпадения), считаем дубликатом
            if similarity_ratio(normalized, existing_normalized) > 0.8:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_results.append(result)
    
    return '\n'.join(unique_results)

def ocr_with_multiple_engines(img: Image.Image, lang: str = "eng", region_type: str = "text") -> str:
    """OCR с несколькими движками и настройками для разных типов контента"""
    results = []
    
    # Получаем предобработанные изображения
    processed_images = advanced_preprocess(img, mode=region_type)
    
    # Различные PSM режимы для разных типов контента
    psm_modes = {
        "text": [3, 6, 8],      # Для обычного текста
        "table": [6, 8, 11],   # Для таблиц
        "diagram": [6, 8, 13]  # Для диаграмм и схем
    }
    
    modes = psm_modes.get(region_type, [6])
    
    for processed_img in processed_images:
        for psm in modes:
            try:
                # Упрощенная конфигурация без проблемных символов
                config = f"--psm {psm}"
                
                text = pytesseract.image_to_string(processed_img, lang=lang, config=config)
                
                if text and len(text.strip()) > 2:
                    # Очистка и нормализация текста
                    cleaned_text = clean_ocr_text(text)
                    if cleaned_text:
                        results.append(cleaned_text)
                        
            except Exception as e:
                logger.warning(f"OCR attempt failed for PSM {psm}: {e}")
                continue
    
    # Объединяем и дедуплицируем результаты
    return deduplicate_text_results(results)

def validate_pdf_file(file_data: bytes) -> bool:
    """Validate that the file is a legitimate PDF"""
    try:
        # Check PDF magic number
        if len(file_data) < 4:
            return False
        
        # PDF files start with %PDF
        if file_data[:4] != b'%PDF':
            return False
        
        # Additional basic checks
        if len(file_data) > MAX_FILE_SIZE:
            return False
            
        return True
    except Exception as e:
        logger.warning(f"PDF validation failed: {e}")
        return False

def pdf_to_md(pdf_path: str, ocr_scale: float = 4.0, do_corner: bool = True,
              lang: str = "eng+rus", psm: str = "6", angles = (0, 90, 270, 180, -15, 15)) -> str:
    """Улучшенная функция для сложных PDF с диаграммами и таблицами"""
    if not os.path.exists(pdf_path):
        raise ValueError(f"PDF file not found: {pdf_path}")
    
    md_parts = []
    
    # 1) Структурированный текст через pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    # Извлекаем текст
                    text = page.extract_text() or ""
                    
                    # Пытаемся извлечь таблицы
                    tables = page.extract_tables()
                    table_text = ""
                    
                    if tables:
                        for j, table in enumerate(tables):
                            table_text += f"\n### Table {j+1} on Page {i}\n\n"
                            for row in table:
                                if row:
                                    # Очищаем None значения и соединяем
                                    clean_row = [str(cell or "") for cell in row]
                                    table_text += "| " + " | ".join(clean_row) + " |\n"
                    
                    combined_text = text + table_text
                    md_parts.append(f"\n\n## Page {i} (Structured)\n\n{combined_text.rstrip()}\n")
                    
                except Exception as e:
                    logger.warning(f"Structured extraction failed for page {i}: {e}")
                    md_parts.append(f"\n\n## Page {i} (Structured)\n\n[Extraction failed]\n")
    except Exception as e:
        logger.error(f"PDF structured extraction failed: {e}")
        # Не выбрасываем исключение, продолжаем с OCR

    # 2) Продвинутый OCR через pdfium с анализом областей
    try:
        pdfdoc = pdfium.PdfDocument(pdf_path)
        for i, page in enumerate(pdfdoc, start=1):
            try:
                # Рендерим страницу в высоком разрешении
                bitmap = page.render(scale=float(ocr_scale)).to_pil()
                
                # Определяем области документа
                regions = detect_layout_regions(bitmap)
                
                # OCR для каждого типа области отдельно
                for region_type, boxes in regions.items():
                    if not boxes:
                        continue
                        
                    for j, (x1, y1, x2, y2) in enumerate(boxes):
                        try:
                            # Вырезаем область
                            region_img = bitmap.crop((x1, y1, x2, y2))
                            
                            # Применяем специализированный OCR
                            ocr_text = ocr_with_multiple_engines(region_img, lang=lang, region_type=region_type)
                            
                            if ocr_text:
                                section_title = f"### OCR {region_type.title()} {j+1} Page {i}"
                                md_parts.append(f"\n\n{section_title}\n\n{ocr_text}\n")
                                
                        except Exception as e:
                            logger.warning(f"Region OCR failed for {region_type} {j} on page {i}: {e}")
                
                # Полностраничный OCR с поворотами для захвата всего
                full_ocr_results = []
                for angle in angles:
                    try:
                        if angle == 0:
                            rotated = bitmap
                        else:
                            rotated = bitmap.rotate(angle, expand=True)
                        
                        ocr_text = ocr_with_multiple_engines(rotated, lang=lang, region_type="text")
                        if ocr_text:
                            full_ocr_results.append(ocr_text)
                            
                    except Exception as e:
                        logger.warning(f"Full page OCR failed for angle {angle} on page {i}: {e}")
                
                if full_ocr_results:
                    combined_full = deduplicate_text_results(full_ocr_results)
                    md_parts.append(f"\n\n### OCR Full Page {i}\n\n{combined_full}\n")

            except Exception as e:
                logger.error(f"Page processing failed for page {i}: {e}")
                md_parts.append(f"\n\n### OCR Page {i}\n\n[Processing failed: {str(e)}]\n")

    except Exception as e:
        logger.error(f"PDF OCR processing failed: {e}")
        raise HTTPException(500, f"PDF OCR processing error: {str(e)}")

    result = "".join(md_parts).strip()
    return result if result else "# Document processing completed but no text was extracted"

@app.post("/convert")
async def convert(request: Request, file: UploadFile = File(None)):
    """Enhanced conversion for complex PDFs with diagrams and tables"""
    tmp_path = None
    picked_file = file

    if picked_file is None:
        # If multiple files, pick the first one
        form_data = await request.form()
        for _, value in form_data.items():
            if hasattr(value, "read"):
                picked_file = value
                break

    try:
        if picked_file is not None:
            data = await picked_file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            
            # Validate PDF file
            if not validate_pdf_file(data):
                raise HTTPException(status_code=400, detail="Invalid PDF file format")
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(data)
                tmp_path = tmp.name
        else:
            # Fallback: raw PDF in the request body
            raw = await request.body()
            if not raw:
                raise HTTPException(
                    status_code=422,
                    detail="Expected PDF file in multipart form or raw request body",
                )
            
            # Validate PDF file
            if not validate_pdf_file(raw):
                raise HTTPException(status_code=400, detail="Invalid PDF file format")
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(raw)
                tmp_path = tmp.name

        # Enhanced tuning for complex documents
        qp = request.query_params
        mode = (qp.get("mode") or "complex").lower()  # по умолчанию сложный режим
        
        # Повышенные настройки для сложных документов
        scale_map = {
            "simple": 2.0,
            "standard": 3.0, 
            "complex": 4.0,
            "max": 5.0
        }
        scale = float(qp.get("scale") or scale_map.get(mode, 4.0))
        
        do_corner = (qp.get("corner") or "1") not in ("0", "false", "no")
        lang = qp.get("lang") or "eng+rus"  # по умолчанию английский + русский
        psm = qp.get("psm") or "6"
        
        # Расширенные углы поворота для лучшего распознавания
        angles = qp.get("angles")
        if angles:
            try:
                angles = tuple(int(a.strip()) for a in angles.split(",") if a.strip())
            except Exception:
                angles = (0, 90, 270, 180, -15, 15, -30, 30)
        else:
            angle_map = {
                "simple": (0,),
                "standard": (0, 90, 270, 180),
                "complex": (0, 90, 270, 180, -15, 15),
                "max": (0, 90, 270, 180, -15, 15, -30, 30, -45, 45)
            }
            angles = angle_map.get(mode, (0, 90, 270, 180, -15, 15))

        md = pdf_to_md(tmp_path, ocr_scale=scale, do_corner=do_corner, lang=lang, psm=psm, angles=angles)

        user_agent = request.headers.get("user-agent", "")
        if "obsidian" in user_agent.lower():
            return PlainTextResponse(md, media_type="text/plain")
        
        return JSONResponse({
            "status": "success",
            "markdown": md,
            "metadata": {
                "mode": mode,
                "scale": scale,
                "language": lang,
                "angles": angles,
                "corner_detection": do_corner
            }
        })

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return JSONResponse(
            {"status": "error", "error": str(e)},
            status_code=500
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# Marker-compatible API endpoints
@app.post("/api/v1/marker")
async def marker_submit(request: Request, file: UploadFile = File(None)):
    """Marker-compatible endpoint for job submission"""
    picked_file = file
    if picked_file is None:
        form_data = await request.form()
        for _, value in form_data.items():
            if hasattr(value, "read"):
                picked_file = value
                break

    tmp_path = None
    try:
        if picked_file is not None:
            data = await picked_file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            
            # Validate PDF file
            if not validate_pdf_file(data):
                raise HTTPException(status_code=400, detail="Invalid PDF file format")
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(data)
                tmp_path = tmp.name
        else:
            raw = await request.body()
            if not raw:
                raise HTTPException(status_code=422, detail="Expected PDF file in multipart form or raw request body")
            
            # Validate PDF file
            if not validate_pdf_file(raw):
                raise HTTPException(status_code=400, detail="Invalid PDF file format")
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(raw)
                tmp_path = tmp.name

        qp = request.query_params
        mode = qp.get("mode") or "complex"
        scale = float(qp.get("scale") or "4.0")
        lang = qp.get("lang") or "eng+rus"

        request_id = str(uuid.uuid4())

        md = pdf_to_md(tmp_path, ocr_scale=scale, lang=lang)

        TASKS[request_id] = {
            "status": "complete",
            "result": {"markdown": md, "images": [], "metadata": {}},
            "error": None
        }

        return JSONResponse({"request_id": request_id})

    except Exception as e:
        logger.error(f"Marker submission failed: {e}")
        request_id = str(uuid.uuid4())
        TASKS[request_id] = {
            "status": "error",
            "result": None,
            "error": str(e)
        }
        return JSONResponse({"request_id": request_id})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

@app.get("/api/v1/marker/{request_id}")
def marker_status(request_id: str):
    """Marker-compatible endpoint for job status polling"""
    if request_id not in TASKS:
        raise HTTPException(status_code=404, detail="Request not found")

    task = TASKS[request_id]
    return JSONResponse({
        "status": task["status"],
        "result": task["result"],
        "error": task["error"]
    })

# Additional endpoints
@app.post("/python/convert")
async def python_convert(request: Request):
    return await convert(request)

@app.post("/v1/convert")
async def v1_convert(request: Request):
    return await convert(request)

@app.post("/api/v1/ocr")
async def ocr_stub(request: Request, file: UploadFile = File(None)):
    return JSONResponse({
        "status": "success",
        "pages": [],
        "metadata": {"note": "This is a stub endpoint"}
    })

@app.post("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    """Catch-all for plugin compatibility"""
    logger.info(f"Catch-all triggered for path: {full_path}")
    return await convert(request)

# Health and status endpoints
@app.get("/health")
def health():
    return {"status": "success", "ok": True}

@app.get("/metrics")
def get_metrics():
    """Get server metrics and statistics"""
    metrics_data = dict(METRICS)
    
    # Calculate average processing time if we have requests
    total_requests = metrics_data.get("total_requests", 0)
    total_time = metrics_data.get("total_processing_time", 0)
    avg_time = total_time / total_requests if total_requests > 0 else 0
    
    return {
        "status": "success",
        "metrics": metrics_data,
        "summary": {
            "total_requests": total_requests,
            "total_processing_time": round(total_time, 3),
            "average_processing_time": round(avg_time, 3),
            "uptime": time.time() - getattr(sys.modules[__name__], '_start_time', time.time())
        }
    }

@app.get("/status")
def status():
    return {"status": "success", "ok": True}

@app.get("/healthz")
def healthz():
    return {"status": "success", "ok": True}

@app.get("/ready")
def ready():
    return {"status": "success", "ok": True}

@app.get("/live")
def live():
    return {"status": "success", "ok": True}

@app.get("/version")
def version():
    return {"status": "success", "service": "ocr-ai", "version": "0.1.0"}

# Initialize start time for uptime calculation
import sys
if not hasattr(sys.modules[__name__], '_start_time'):
    sys.modules[__name__]._start_time = time.time()
