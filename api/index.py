import sys
import os
import io
import zipfile
import traceback
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Ensure markitdown package from local monorepo or sys.path is importable
repo_packages_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "markitdown", "packages", "markitdown", "src")
)
if os.path.exists(repo_packages_path) and repo_packages_path not in sys.path:
    sys.path.insert(0, repo_packages_path)

try:
    from markitdown import MarkItDown, StreamInfo
except ImportError:
    # Fallback to local import attempt
    MarkItDown = None
    StreamInfo = None

app = FastAPI(
    title="markitdowninweb API",
    description="Full-featured REST API for Microsoft MarkItDown document conversion",
    version="1.0.0"
)

# Enable CORS for cross-origin web app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    # Handle Free and Custom Vision API Providers
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
    if api_key and (enable_plugins or openai_api_key or openai_base_url or llm_provider != "auto"):
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


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "app": "markitdowninweb",
        "markitdown_available": MarkItDown is not None,
        "version": "1.0.0"
    }


@app.get("/api/formats")
def get_supported_formats():
    return {
        "formats": [
            {"extension": ".pdf", "name": "PDF Document", "category": "Document", "features": ["Tables", "MasterFormat", "OCR"]},
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
            {"extension": ".png", "name": "PNG Image", "category": "Media", "features": ["EXIF Tags", "LLM Vision Captioning"]},
            {"extension": ".jpg", "name": "JPEG Image", "category": "Media", "features": ["EXIF Tags", "LLM Vision Captioning"]},
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
        
        md = get_markitdown_instance(
            enable_plugins=enable_plugins,
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            llm_model=llm_model,
            llm_prompt=llm_prompt,
            llm_provider=llm_provider,
            docintel_endpoint=docintel_endpoint,
            cu_endpoint=cu_endpoint,
            cu_analyzer_id=cu_analyzer_id
        )

        stream_info = None
        ext = extension_hint or os.path.splitext(file.filename or "")[1]
        if ext or mime_hint:
            stream_info = StreamInfo(
                filename=file.filename,
                extension=ext if ext.startswith(".") else f".{ext}" if ext else None,
                mimetype=mime_hint
            )

        result = md.convert_stream(
            stream,
            stream_info=stream_info,
            keep_data_uris=keep_data_uris
        )

        markdown_text = result.markdown
        title = result.title or file.filename or "Converted Document"

        return {
            "success": True,
            "filename": file.filename,
            "title": title,
            "markdown": markdown_text,
            "char_count": len(markdown_text),
            "word_count": len(markdown_text.split()),
            "estimated_tokens": int(len(markdown_text.split()) * 1.33)
        }
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
def convert_url(req: URLConvertRequest):
    try:
        md = get_markitdown_instance(
            enable_plugins=req.enable_plugins,
            openai_api_key=req.openai_api_key,
            openai_base_url=req.openai_base_url,
            llm_model=req.llm_model
        )

        result = md.convert_uri(req.url, keep_data_uris=req.keep_data_uris)
        markdown_text = result.markdown

        return {
            "success": True,
            "url": req.url,
            "title": result.title or req.url,
            "markdown": markdown_text,
            "char_count": len(markdown_text),
            "word_count": len(markdown_text.split()),
            "estimated_tokens": int(len(markdown_text.split()) * 1.33)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"URL conversion failed: {str(e)}")


class TextConvertRequest(BaseModel):
    text: str
    extension_hint: str = ".html"
    enable_plugins: bool = False


@app.post("/api/convert/text")
def convert_text(req: TextConvertRequest):
    try:
        md = get_markitdown_instance(enable_plugins=req.enable_plugins)
        stream = io.BytesIO(req.text.encode("utf-8"))
        stream_info = StreamInfo(extension=req.extension_hint)

        result = md.convert_stream(stream, stream_info=stream_info)
        markdown_text = result.markdown

        return {
            "success": True,
            "markdown": markdown_text,
            "char_count": len(markdown_text),
            "word_count": len(markdown_text.split()),
            "estimated_tokens": int(len(markdown_text.split()) * 1.33)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Text conversion failed: {str(e)}")


@app.post("/api/convert/batch")
async def convert_batch(
    files: List[UploadFile] = File(...),
    enable_plugins: bool = Form(False),
    keep_data_uris: bool = Form(False),
    openai_api_key: Optional[str] = Form(None),
):
    md = get_markitdown_instance(
        enable_plugins=enable_plugins,
        openai_api_key=openai_api_key
    )

    zip_buffer = io.BytesIO()
    results = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            filename = file.filename or "file.bin"
            base_name, _ = os.path.splitext(filename)
            md_filename = f"{base_name}.md"

            try:
                content = await file.read()
                stream = io.BytesIO(content)
                ext = os.path.splitext(filename)[1]
                stream_info = StreamInfo(filename=filename, extension=ext)

                res = md.convert_stream(stream, stream_info=stream_info, keep_data_uris=keep_data_uris)
                zip_file.writestr(md_filename, res.markdown)
                results.append({
                    "filename": filename,
                    "status": "success",
                    "markdown_file": md_filename,
                    "char_count": len(res.markdown)
                })
            except Exception as e:
                error_msg = f"# Conversion Error for {filename}\n\n```{str(e)}```"
                zip_file.writestr(f"{base_name}_error.md", error_msg)
                results.append({
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })

    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=markitdowninweb_export.zip"}
    )

# Serve public directory static files
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

