from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, uuid
import pdfplumber, pytesseract
from PIL import Image, ImageOps, ImageFilter
import pypdfium2 as pdfium
import logging, time

try:
    import cv2  # optional, for better binarization
    import numpy as np
except Exception:
    cv2 = None
    np = None

app = FastAPI(title="ocr-ai", version="0.1.0")

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
async def log_requests(request: Request, call_next):
    t0 = time.time()
    ua = request.headers.get("user-agent", "")
    acc = request.headers.get("accept", "")
    ct = request.headers.get("content-type", "")
    resp = await call_next(request)
    dt = int((time.time() - t0) * 1000)
    try:
        logger.info(f"%s %s -> %s in %dms | UA=%s | Accept=%s | CT=%s",
                    request.method, request.url.path, resp.status_code, dt,
                    ua[:80], acc, ct)
    except Exception:
        pass
    return resp

@app.get("/")
def root():
    return {"status": "success", "service": "ocr-ai", "endpoints": ["/convert", "/health", "/version", "/docs"]}

def pdf_to_md(pdf_path: str, ocr_scale: float = 3.0, do_corner: bool = True,
              lang: str = "eng", psm: str = "6", angles = (0, 90, 270, 180, -15, 15)) -> str:
    """Extract markdown from PDF using a layered approach:
    1) text layer via pdfplumber
    2) page raster OCR (multi-angle)
    3) optional corner crops OCR to catch marginal labels
    """
    def _preprocess(img: Image.Image) -> Image.Image:
        g = img.convert("L")
        g = ImageOps.autocontrast(g)
        if cv2 is not None and np is not None:
            try:
                arr = np.array(g)
                arr = cv2.GaussianBlur(arr, (3, 3), 0)
                thr = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                             cv2.THRESH_BINARY, 31, 2)
                g = Image.fromarray(thr)
            except Exception:
                pass
        else:
            try:
                g = g.filter(ImageFilter.SHARPEN)
            except Exception:
                pass
        return g

    def _ocr_multi(img: Image.Image) -> str:
        pieces = []
        # build tesseract config
        config = f"--psm {psm}"
        for ang in angles:
            try:
                if ang in (0, 360):
                    im = img
                else:
                    im = img.rotate(ang, expand=True)
                txt = pytesseract.image_to_string(_preprocess(im), lang=lang, config=config)
                t = (txt or "").strip()
                if len(t) >= 3:
                    # de-dup simple: avoid adding if already seen ignoring spaces/case
                    low = " ".join(t.split()).lower()
                    if all(" ".join(p.split()).lower() != low for p in pieces):
                        pieces.append(t)
            except Exception:
                continue
        return "\n".join(pieces).strip()

    md_parts = []
    # 1) structured text via pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            md_parts.append(f"\n\n## Page {i}\n\n{text.rstrip()}\n")

    # 2) OCR layer via pdfium raster
    pdfdoc = pdfium.PdfDocument(pdf_path)
    for i, page in enumerate(pdfdoc, start=1):
        try:
            bitmap = page.render(scale=float(ocr_scale)).to_pil()
        except Exception:
            # fallback to default scale if parsing fails
            bitmap = page.render(scale=2.0).to_pil()

        full_ocr = _ocr_multi(bitmap)
        if full_ocr:
            md_parts.append(f"\n\n### OCR Page {i}\n\n{full_ocr}\n")

        # 3) corner crops (top-left, top-right, bottom-left, bottom-right)
        if do_corner:
            try:
                w, h = bitmap.size
                cw = int(0.40 * w)
                ch = int(0.40 * h)
                crops = [
                    ("top-left", (0, 0, cw, ch)),
                    ("top-right", (w - cw, 0, w, ch)),
                    ("bottom-left", (0, h - ch, cw, h)),
                    ("bottom-right", (w - cw, h - ch, w, h)),
                ]
                for label, box in crops:
                    crop = bitmap.crop(box)
                    txt = _ocr_multi(crop)
                    if txt:
                        md_parts.append(f"\n\n#### OCR Corner {label} Page {i}\n\n{txt}\n")
            except Exception:
                pass

    return "".join(md_parts).strip()

@app.post("/convert")
async def convert(request: Request, file: UploadFile = File(None)):
    """
    Accepts either:
    1) multipart/form-data with any field name that contains a file, or
    2) raw application/pdf in the request body.
    Returns Markdown as text/markdown.
    """
    tmp_path = None

    # Prefer bound UploadFile if client used field name 'file'
    picked_file = file

    # Otherwise, scan multipart form for any file-like field
    if picked_file is None:
        try:
            form = await request.form()
        except Exception:
            form = None
        if form is not None:
            for _, v in form.items():
                if hasattr(v, "filename") and hasattr(v, "read"):
                    picked_file = v
                    break

    try:
        if picked_file is not None:
            data = await picked_file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
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
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(raw)
                tmp_path = tmp.name

        # Tuning knobs from query
        qp = request.query_params
        mode = (qp.get("mode") or "").lower()
        scale = float(qp.get("scale") or (4.0 if mode in ("aggressive", "max") else 3.0))
        do_corner = (qp.get("corner") or "1") not in ("0", "false", "no")
        lang = qp.get("lang") or "eng"
        psm = qp.get("psm") or ("6" if mode not in ("sparse",) else "11")
        angles = qp.get("angles")
        if angles:
            try:
                angles = tuple(int(a.strip()) for a in angles.split(",") if a.strip())
            except Exception:
                angles = (0, 90, 270, 180, -15, 15)
        else:
            angles = (0, 90, 270, 180, -15, 15) if mode in ("aggressive", "max") else (0, 90, 270, 180)

        md = pdf_to_md(tmp_path, ocr_scale=scale, do_corner=do_corner, lang=lang, psm=psm, angles=angles) or "# Empty result"
        # Try to also provide a per-page array for Marker-like clients
        pages = []
        token = "\n\n## Page "
        if token in md:
            chunks = md.split(token)
            if chunks[0].strip():
                pages.append(chunks[0].strip())
            for c in chunks[1:]:
                pages.append(("## Page " + c).strip())
        else:
            pages = [md]

        accept = (request.headers.get("accept") or "").lower()
        out = (request.query_params.get("out") or "").lower()
        ua = (request.headers.get("user-agent") or "").lower()

        # Obsidian/Electron: always return JSON expected by plugins
        if out == "obsidian" or "obsidian" in ua or "electron" in ua:
            return JSONResponse({
                "ok": True,
                "success": True,
                "status": "success",
                "message": "success",
                "content": md,
                "markdown": md,
                "images": [],
            })

        # Raw markdown when explicitly requested by query/header
        if out == "markdown" or "text/markdown" in accept:
            return PlainTextResponse(md, media_type="text/markdown; charset=utf-8")

        # Default JSON with multiple aliases and nested objects (Marker-style)
        result_obj = {"markdown": md, "images": [], "pages": pages}
        payload = {
            "ok": True,
            "success": True,
            "status": "success",
            "code": 0,
            "message": "success",
            "format": "markdown",
            # flat aliases
            "markdown": md,
            "text": md,
            "content": md,
            "images": [],
            "markdown_pages": pages,
            # nested aliases
            "data": result_obj,
            "result": result_obj,
        }
        return JSONResponse(payload)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

# Aliases for Python API style clients
@app.post("/python/convert")
async def python_convert(request: Request):
    return await convert(request)

@app.post("/v1/convert")
async def v1_convert(request: Request):
    return await convert(request)

# ---------------- Marker-compatible API (Self-hosted) ----------------
@app.post("/api/v1/ocr")
async def ocr_stub(request: Request, file: UploadFile = File(None)):
    # This stub returns an empty OCR result but satisfies clients probing for the endpoint
    return JSONResponse({
        "status": "success",
        "success": True,
        "text": "",
        "markdown": "",
        "images": [],
        "error": None,
    })

@app.post("/api/v1/marker")
async def marker_submit(request: Request, file: UploadFile = File(None)):
    # Accept multipart with any field name or raw PDF (reuse logic from /convert)
    tmp_path = None
    picked_file = file
    if picked_file is None:
        try:
            form = await request.form()
        except Exception:
            form = None
        if form is not None:
            for _, v in form.items():
                if hasattr(v, "filename") and hasattr(v, "read"):
                    picked_file = v
                    break
    try:
        if picked_file is not None:
            data = await picked_file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(data)
                tmp_path = tmp.name
        else:
            raw = await request.body()
            if not raw:
                raise HTTPException(status_code=422, detail="Expected PDF file in multipart form or raw request body")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(raw)
                tmp_path = tmp.name

        # Use aggressive defaults for Self-hosted Marker calls, with optional overrides via query
        qp = request.query_params
        mode = (qp.get("mode") or "").lower()
        scale = float(qp.get("scale") or (4.0 if mode in ("", "aggressive", "max") else 3.0))
        do_corner = (qp.get("corner") or "1") not in ("0", "false", "no")
        lang = qp.get("lang") or "eng"
        psm = qp.get("psm") or ("6" if mode not in ("sparse",) else "11")
        angles = qp.get("angles")
        if angles:
            try:
                angles = tuple(int(a.strip()) for a in angles.split(",") if a.strip())
            except Exception:
                angles = (0, 90, 270, 180, -15, 15)
        else:
            angles = (0, 90, 270, 180, -15, 15)

        md = pdf_to_md(tmp_path, ocr_scale=scale, do_corner=do_corner, lang=lang, psm=psm, angles=angles) or "# Empty result"
        # Build pages same way as in /convert
        pages = []
        token = "\n\n## Page "
        if token in md:
            chunks = md.split(token)
            if chunks[0].strip():
                pages.append(chunks[0].strip())
            for c in chunks[1:]:
                pages.append(("## Page " + c).strip())
        else:
            pages = [md]

        # Create a request id and store the complete result immediately
        rid = uuid.uuid4().hex
        result_obj = {
            "output_format": "markdown",
            "markdown": md,
            "content": md,
            "status": "success",
            "state": "completed",
            "ok": True,
            "success": True,
            "images": [],
            "metadata": {},
            "error": "",
            "page_count": len(pages),
            "pages": pages,
        }
        TASKS[rid] = result_obj

        base = str(request.base_url).rstrip('/')
        check_url = f"{base}/api/v1/marker/{rid}"
        return JSONResponse({
            "success": True,
            "error": None,
            "request_id": rid,
            "request_check_url": check_url,
        })
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.get("/api/v1/marker/{rid}")
async def marker_check(rid: str):
    result = TASKS.get(rid)
    if result is not None:
        # normalize aliases for maximum compatibility
        result.setdefault("ok", True)
        if result.get("status") not in ("success", "completed", "complete"):
            result["status"] = "success"
        result.setdefault("state", "completed")
        if "content" not in result and "markdown" in result:
            result["content"] = result["markdown"]
    if result is None:
        # If not found, pretend it's still processing (some clients expect this)
        return JSONResponse({
            "status": "processing",
            "success": True,
            "error": None,
        })
    return JSONResponse(result)

# Catch-all POST path for plugin compatibility
@app.post("/{full_path:path}")
async def convert_catch_all(full_path: str, request: Request):
    # Delegate any POST path to the same convert logic for plugin compatibility
    return await convert(request)

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

@app.get("/health")
def health():
    return {"status": "success", "ok": True}