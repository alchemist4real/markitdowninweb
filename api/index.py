import sys
import os
import io
import zipfile
import asyncio
import traceback
import base64
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

try:
    from markitdown import MarkItDown
except Exception as e:
    import traceback
    print(f"MarkItDown import error detail: {e}")
    traceback.print_exc()
    MarkItDown = None

try:
    from markitdown import StreamInfo
except Exception as e:
    StreamInfo = None

# Tier 1: PyMuPDF4LLM — native local PDF-to-Markdown
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

# Tier 2: Gemini Flash Vision — free API for scanned docs & images
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Image extensions for Tier 2 routing
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}

# Max concurrent batch conversions
BATCH_CONCURRENCY = 5

app = FastAPI(
    title="markitdowninweb API",
    description="3-Tier conversion engine: PyMuPDF4LLM (native) -> Gemini Flash (vision) -> MarkItDown (fallback)",
    version="2.0.0"
)

# Enable CORS for cross-origin web app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Tier 1: PyMuPDF4LLM Native PDF Conversion ──────────────────────────────

def _tier1_convert_pdf(stream: io.BytesIO, filename: str) -> Optional[str]:
    """Tier 1: Native local PDF-to-Markdown using PyMuPDF4LLM.
    Extracts text, tables, headers directly from PDF primitives.
    No API calls, no network, ~50ms/page."""
    if not PYMUPDF4LLM_AVAILABLE:
        return None
    try:
        stream.seek(0)
        # pymupdf4llm.to_markdown accepts file path or bytes
        pdf_bytes = stream.read()
        import pymupdf as fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        md_text = pymupdf4llm.to_markdown(doc)
        doc.close()
        if md_text and len(md_text.strip()) > 50:
            return md_text
        return None
    except Exception as e:
        print(f"Tier 1 (PyMuPDF4LLM) notice: {e}")
        return None


# ─── Tier 2: Gemini Flash Vision OCR ─────────────────────────────────────────

def _tier2_convert_with_gemini(stream: io.BytesIO, filename: str, api_key: str, is_pdf: bool = False) -> Optional[str]:
    """Tier 2: Gemini Flash vision for scanned PDFs and images.
    Returns structured Markdown. Free tier at aistudio.google.com."""
    if not GEMINI_AVAILABLE or not api_key:
        return None
    try:
        stream.seek(0)
        file_bytes = stream.read()

        client = genai.Client(api_key=api_key)

        ext = os.path.splitext(filename or "file")[1].lower()
        mime_map = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".bmp": "image/bmp", ".tiff": "image/tiff",
            ".gif": "image/gif", ".pdf": "application/pdf",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

        prompt = (
            "Extract ALL text content from this document into clean, well-structured Markdown. "
            "Preserve tables as Markdown tables, preserve headings hierarchy, preserve lists. "
            "If there are images with text, OCR and include the text. "
            "Output ONLY the Markdown content, no explanations."
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                genai.types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            ],
        )

        if response and response.text:
            md_text = response.text.strip()
            # Remove markdown code fences if Gemini wraps output in them
            if md_text.startswith("```markdown"):
                md_text = md_text[len("```markdown"):].strip()
            if md_text.startswith("```"):
                md_text = md_text[3:].strip()
            if md_text.endswith("```"):
                md_text = md_text[:-3].strip()
            if len(md_text) > 10:
                return md_text
        return None
    except Exception as e:
        print(f"Tier 2 (Gemini Flash) notice: {e}")
        return None


# ─── Tier 3: MarkItDown Classic Fallback ─────────────────────────────────────

def get_markitdown_instance(
    enable_plugins: bool = False,
    openai_api_key: Optional[str] = None,
    openai_base_url: Optional[str] = None,
    llm_model: Optional[str] = "gpt-4o",
    llm_prompt: Optional[str] = None,
    llm_provider: Optional[str] = "auto",
    docintel_endpoint: Optional[str] = None,
    cu_endpoint: Optional[str] = None,
    cu_analyzer_id: Optional[str] = None,
):
    if MarkItDown is None:
        raise HTTPException(status_code=500, detail="MarkItDown library is not installed or available.")

    kwargs = {}

    # Handle Vision API Providers
    api_key = openai_api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY") or "free-dummy-key"
    base_url = openai_base_url
    model = llm_model or "gpt-4o"

    if llm_provider == "openrouter":
        base_url = base_url or "https://openrouter.ai/api/v1"
        model = llm_model or "qwen/qwen-2.5-vl-72b-instruct:free"
    elif llm_provider == "gemini":
        base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        model = llm_model or "gemini-2.0-flash"
    elif llm_provider == "groq":
        base_url = base_url or "https://api.groq.com/openai/v1"
        model = llm_model or "llama-3.2-11b-vision-preview"
    elif llm_provider == "ollama":
        base_url = base_url or "http://localhost:11434/v1"
        model = llm_model or "llava"

    # Configure Vision client if key or provider is specified
    if api_key and (enable_plugins or openai_api_key or openai_base_url or llm_provider not in ("auto", "offline", "markitdown")):
        try:
            from openai import OpenAI
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            client = OpenAI(**client_kwargs)
            kwargs["llm_client"] = client
            kwargs["llm_model"] = model
            if llm_prompt:
                kwargs["llm_prompt"] = llm_prompt
        except Exception as e:
            print(f"Warning initializing Vision LLM client: {e}")

    if docintel_endpoint:
        kwargs["docintel_endpoint"] = docintel_endpoint
    if cu_endpoint:
        kwargs["cu_endpoint"] = cu_endpoint
    if cu_analyzer_id:
        kwargs["cu_analyzer_id"] = cu_analyzer_id

    return MarkItDown(enable_plugins=enable_plugins, **kwargs)


def _tier3_convert_stream(stream: io.BytesIO, filename: str, ext: str,
                          keep_data_uris: bool = False, mime_hint: Optional[str] = None,
                          **settings) -> str:
    """Tier 3: MarkItDown classic conversion as final safety net."""
    md = get_markitdown_instance(**settings)
    stream.seek(0)

    stream_info = None
    if ext or mime_hint:
        stream_info = StreamInfo(
            filename=filename,
            extension=ext if ext.startswith(".") else f".{ext}" if ext else None,
            mimetype=mime_hint
        )

    result = md.convert_stream(stream, stream_info=stream_info, keep_data_uris=keep_data_uris)
    return result.markdown


# ─── Smart 3-Tier Conversion Router ──────────────────────────────────────────

def _get_gemini_key(openai_api_key: Optional[str] = None, llm_provider: Optional[str] = None) -> Optional[str]:
    """Resolve Gemini API key from settings or environment."""
    if llm_provider == "gemini" and openai_api_key:
        return openai_api_key
    return os.getenv("GEMINI_API_KEY") or (openai_api_key if llm_provider in ("auto", "gemini", None) else None)


def _smart_convert_sync(stream: io.BytesIO, filename: str, ext: str,
                        keep_data_uris: bool = False, mime_hint: Optional[str] = None,
                        llm_provider: Optional[str] = "auto",
                        openai_api_key: Optional[str] = None,
                        **settings) -> str:
    """3-tier conversion engine (synchronous, runs in thread pool).
    
    Tier 1: PyMuPDF4LLM — native PDF extraction (~50ms/page, offline)
    Tier 2: Gemini Flash — vision OCR for scanned/image docs (free API)
    Tier 3: MarkItDown — classic library fallback
    """
    # If user explicitly chose a specific mode, honor it
    if llm_provider == "offline":
        # Offline mode: Tier 1 only for PDFs, Tier 3 for everything else
        if ext == ".pdf":
            result = _tier1_convert_pdf(stream, filename)
            if result:
                return result
        stream.seek(0)
        return _tier3_convert_stream(stream, filename, ext, keep_data_uris, mime_hint,
                                     llm_provider="auto", openai_api_key=openai_api_key, **settings)

    if llm_provider == "markitdown":
        # Force MarkItDown classic only
        stream.seek(0)
        return _tier3_convert_stream(stream, filename, ext, keep_data_uris, mime_hint,
                                     llm_provider="auto", openai_api_key=openai_api_key, **settings)

    # ── Auto / Gemini mode: full 3-tier cascade ──

    # Tier 1: Native PDF extraction (instant, no API)
    tier1_result = None
    if ext == ".pdf" and llm_provider in ("auto", "offline", None):
        tier1_result = _tier1_convert_pdf(stream, filename)
        if tier1_result:
            return tier1_result

    # Tier 2: Gemini Flash Vision (for images + scanned PDFs that Tier 1 missed)
    gemini_key = _get_gemini_key(openai_api_key, llm_provider)
    if gemini_key and llm_provider in ("auto", "gemini", None):
        if ext in IMAGE_EXTS or (ext == ".pdf" and tier1_result is None):
            stream.seek(0)
            tier2_result = _tier2_convert_with_gemini(stream, filename, gemini_key, is_pdf=(ext == ".pdf"))
            if tier2_result:
                return tier2_result

    # Tier 3: MarkItDown classic fallback
    stream.seek(0)
    return _tier3_convert_stream(stream, filename, ext, keep_data_uris, mime_hint,
                                 llm_provider=llm_provider, openai_api_key=openai_api_key, **settings)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_response(markdown_text: str, filename: str = "document", **extra):
    """Build standard JSON response with text statistics."""
    return {
        "success": True,
        "filename": filename,
        "title": extra.get("title") or filename,
        "markdown": markdown_text,
        "char_count": len(markdown_text),
        "word_count": len(markdown_text.split()),
        "estimated_tokens": int(len(markdown_text.split()) * 1.33),
        **{k: v for k, v in extra.items() if k != "title"}
    }


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "app": "markitdowninweb",
        "markitdown_available": MarkItDown is not None,
        "pymupdf4llm_available": PYMUPDF4LLM_AVAILABLE,
        "gemini_available": GEMINI_AVAILABLE,
        "engine": "3-tier (PyMuPDF4LLM -> Gemini Flash -> MarkItDown)",
        "version": "2.0.0"
    }


@app.get("/api/formats")
def get_supported_formats():
    return {
        "formats": [
            {"extension": ".pdf", "name": "PDF Document", "category": "Document", "features": ["Tables", "MasterFormat", "Native OCR", "Gemini Vision"]},
            {"extension": ".docx", "name": "Microsoft Word", "category": "Document", "features": ["Styles", "Tables", "Images"]},
            {"extension": ".xlsx", "name": "Microsoft Excel", "category": "Spreadsheet", "features": ["Multi-sheet", "HTML Tables"]},
            {"extension": ".xls", "name": "Excel (Legacy)", "category": "Spreadsheet", "features": ["Multi-sheet"]},
            {"extension": ".pptx", "name": "PowerPoint Presentation", "category": "Presentation", "features": ["Slide Titles", "Vision Alt-Text"]},
            {"extension": ".html", "name": "HTML Document", "category": "Web", "features": ["DOM Clean-up", "Markdownify"]},
            {"extension": ".csv", "name": "CSV Data", "category": "Data", "features": ["Table Alignment"]},
            {"extension": ".json", "name": "JSON Data", "category": "Data", "features": ["Syntax Formatting"]},
            {"extension": ".xml", "name": "XML Document", "category": "Data", "features": ["Structure Preservation"]},
            {"extension": ".epub", "name": "EPub eBook", "category": "eBook", "features": ["Chapter Extraction"]},
            {"extension": ".msg", "name": "Outlook Message", "category": "Email", "features": ["Headers", "Body Text"]},
            {"extension": ".zip", "name": "ZIP Archive", "category": "Archive", "features": ["Recursive Extraction"]},
            {"extension": ".png", "name": "PNG Image", "category": "Media", "features": ["Gemini Vision OCR", "LLM Captioning"]},
            {"extension": ".jpg", "name": "JPEG Image", "category": "Media", "features": ["Gemini Vision OCR", "LLM Captioning"]},
            {"extension": ".mp3", "name": "MP3 Audio", "category": "Audio", "features": ["EXIF Tags", "Speech Transcription"]},
            {"extension": ".wav", "name": "WAV Audio", "category": "Audio", "features": ["EXIF Tags", "Speech Transcription"]}
        ]
    }


@app.post("/api/convert/file")
async def convert_file(
    file: UploadFile = File(...),
    enable_plugins: bool = Form(False),
    keep_data_uris: bool = Form(False),
    openai_api_key: Optional[str] = Form(None),
    openai_base_url: Optional[str] = Form(None),
    llm_model: Optional[str] = Form("gpt-4o"),
    llm_prompt: Optional[str] = Form(None),
    llm_provider: Optional[str] = Form("auto"),
    docintel_endpoint: Optional[str] = Form(None),
    cu_endpoint: Optional[str] = Form(None),
    cu_analyzer_id: Optional[str] = Form(None),
    extension_hint: Optional[str] = Form(None),
    mime_hint: Optional[str] = Form(None),
):
    try:
        content = await file.read()
        stream = io.BytesIO(content)
        ext = (extension_hint or os.path.splitext(file.filename or "")[1]).lower()

        # Run conversion in thread pool to avoid blocking the event loop
        markdown_text = await asyncio.to_thread(
            _smart_convert_sync,
            stream, file.filename or "document", ext,
            keep_data_uris=keep_data_uris,
            mime_hint=mime_hint,
            llm_provider=llm_provider,
            openai_api_key=openai_api_key,
            enable_plugins=enable_plugins,
            openai_base_url=openai_base_url,
            llm_model=llm_model,
            llm_prompt=llm_prompt,
            docintel_endpoint=docintel_endpoint,
            cu_endpoint=cu_endpoint,
            cu_analyzer_id=cu_analyzer_id,
        )

        return _build_response(markdown_text, file.filename or "document",
                               title=file.filename or "Converted Document")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


class URLConvertRequest(BaseModel):
    url: str
    enable_plugins: bool = False
    keep_data_uris: bool = False
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    llm_model: Optional[str] = "gpt-4o"


@app.post("/api/convert/url")
async def convert_url(req: URLConvertRequest):
    try:
        def _convert():
            md = get_markitdown_instance(
                enable_plugins=req.enable_plugins,
                openai_api_key=req.openai_api_key,
                openai_base_url=req.openai_base_url,
                llm_model=req.llm_model
            )
            result = md.convert_uri(req.url, keep_data_uris=req.keep_data_uris)
            return result.markdown, result.title

        markdown_text, title = await asyncio.to_thread(_convert)

        return _build_response(markdown_text, req.url, title=title or req.url, url=req.url)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"URL conversion failed: {str(e)}")


class TextConvertRequest(BaseModel):
    text: str
    extension_hint: str = ".html"
    enable_plugins: bool = False


@app.post("/api/convert/text")
async def convert_text(req: TextConvertRequest):
    try:
        def _convert():
            md = get_markitdown_instance(enable_plugins=req.enable_plugins)
            stream = io.BytesIO(req.text.encode("utf-8"))
            stream_info = StreamInfo(extension=req.extension_hint)
            result = md.convert_stream(stream, stream_info=stream_info)
            return result.markdown

        markdown_text = await asyncio.to_thread(_convert)

        return _build_response(markdown_text, f"text{req.extension_hint}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Text conversion failed: {str(e)}")


@app.post("/api/convert/batch")
async def convert_batch(
    files: List[UploadFile] = File(...),
    enable_plugins: bool = Form(False),
    keep_data_uris: bool = Form(False),
    openai_api_key: Optional[str] = Form(None),
    llm_provider: Optional[str] = Form("auto"),
):
    # Read all file contents upfront (async)
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename or "file.bin", content))

    # Convert files concurrently with semaphore limit
    semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)

    async def convert_one(filename: str, content: bytes):
        async with semaphore:
            base_name, ext_part = os.path.splitext(filename)
            ext = ext_part.lower()
            md_filename = f"{base_name}.md"
            try:
                stream = io.BytesIO(content)
                markdown_text = await asyncio.to_thread(
                    _smart_convert_sync,
                    stream, filename, ext,
                    keep_data_uris=keep_data_uris,
                    llm_provider=llm_provider,
                    openai_api_key=openai_api_key,
                    enable_plugins=enable_plugins,
                )
                return md_filename, markdown_text, None
            except Exception as e:
                error_msg = f"# Conversion Error for {filename}\n\n```{str(e)}```"
                return f"{base_name}_error.md", error_msg, str(e)

    # Run all conversions concurrently (capped at BATCH_CONCURRENCY)
    tasks = [convert_one(fn, data) for fn, data in file_data]
    results = await asyncio.gather(*tasks)

    # Pack results into ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for md_filename, content, error in results:
            zip_file.writestr(md_filename, content)

    zip_buffer.seek(0)

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=markitdowninweb_export.zip"}
    )


# ─── Static File Serving ─────────────────────────────────────────────────────

public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))

@app.get("/")
def serve_index():
    index_file = os.path.join(public_dir, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {"status": "online", "app": "markitdowninweb"}

@app.get("/{filename:path}")
def serve_static(filename: str):
    if filename.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    target = os.path.abspath(os.path.join(public_dir, filename))
    if target.startswith(public_dir) and os.path.isfile(target):
        return FileResponse(target)
    index_file = os.path.join(public_dir, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)
