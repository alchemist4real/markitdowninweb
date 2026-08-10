# markitdowninweb ⚡

> **MARKITDOWNINWEB // DOCUMENT & MULTIMODAL CONVERSION LAB**
> Convert PDF, Word, Excel, PowerPoint, Audio, Images, EPub, Outlook MSG, YouTube Transcripts, and Web URIs into clean, LLM-ready Markdown — powered by [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

---

## 👥 Credits & Acknowledgments

- **Core Conversion Engine**: Powered by [Microsoft MarkItDown](https://github.com/microsoft/markitdown)
- **Web Application & UI Architecture**: Designed, Crafted & Maintained by [alchemist4real](https://github.com/alchemist4real)

---

## 🌟 About `markitdowninweb`

`markitdowninweb` is a modern, enterprise-grade web application and REST API server that wraps Microsoft's `markitdown` engine into an intuitive multi-format converter. Designed with the minimalist brutalist aesthetic of `alchemist4real` (`Cormorant Garamond` serif headers, `DM Mono` monospace body, animated pipeline matrix, and fractal noise texture), it provides instant conversion for single files, multi-file batch queues, remote web URIs, and pasted snippets.

---

## ✨ Features & Capabilities

- **100% Microsoft MarkItDown Coverage**:
  - **Documents**: PDF (`.pdf`), Word (`.docx`), EPub (`.epub`), Outlook Messages (`.msg`).
  - **Spreadsheets**: Excel (`.xlsx`, `.xls`), CSV (`.csv`).
  - **Presentations**: PowerPoint (`.pptx`) with shape iteration and slide title extraction.
  - **Data & Text**: JSON (`.json`), XML (`.xml`), HTML (`.html`), Plain Text (`.txt`).
  - **Media & Audio**: Images (`.png`, `.jpg` EXIF tags + LLM Vision), Audio (`.mp3`, `.wav` EXIF + Speech Transcription).
  - **Archives**: ZIP archives (`.zip`) with recursive content extraction.
  - **Special URIs**: HTTP/HTTPS URLs, YouTube video transcripts, Wikipedia articles, Bing SERP, Data URIs.
- **Batch Processing & ZIP Exporter**: Drag and drop up to 20 files at once, convert in parallel, and export all converted Markdown files in a single `.zip` bundle.
- **LLM Vision & `markitdown-ocr`**: Native vision support (`llm_client` / `llm_model` e.g., `gpt-4o`) for image captioning and full-page 300 DPI OCR fallback for scanned PDFs.
- **Enterprise Cloud Engine Routing**: Optional routing to Azure Document Intelligence and Azure Content Understanding with YAML front-matter field extraction.
- **User Workbench**: Dual-pane split-screen editor (Raw Markdown Source vs Live Rendered HTML Preview with code syntax highlighting).
- **Real-Time Token Estimator**: Character count, word count, and estimated OpenAI/Claude LLM token usage.
- **Mobile & Android Optimized**: PWA manifest, touch-friendly tab navigation, sliding settings drawer, and responsive mobile layouts.

---

## 🚀 One-Click Deploy to Vercel

`markitdowninweb` is pre-configured for zero-setup deployment on **Vercel** via Serverless Python Functions (`@vercel/python`) and static assets.

### Deploying via Vercel CLI

1. Install Vercel CLI (if not installed):
   ```bash
   npm i -g vercel
   ```

2. Deploy directly from the `markitdowninweb` directory:
   ```bash
   cd markitdowninweb
   vercel
   ```

3. For production deployment:
   ```bash
   vercel --prod
   ```

---

## 💻 Local Development Setup

To run `markitdowninweb` locally on your machine:

1. **Clone or Navigate to Repository**:
   ```bash
   cd d:\DOWNLOAD\markitdowninweb
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Local Development Server**:
   ```bash
   python server.py
   ```
   Or using `uvicorn` directly:
   ```bash
   uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
   ```

4. Open your browser at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.

---

## 🔌 Unified Model Context Protocol (MCP) Gateway

`markitdowninweb` provides a **single unified MCP entrypoint link** for AI Agents (Claude, Antigravity, Cursor, LangChain):

- **Unified MCP Link**: `https://markitdowninweb.vercel.app/api/mcp`
- **Protocol Standard**: JSON-RPC 2.0 & REST MCP Tool Server
- **Supported Actions**: `tools/list` (Tool Discovery), `tools/call` (Dynamic Tool Execution), `ping` (Health Check), `convert_url`, `convert_text`, `convert_file`, `convert_batch`.

---

## 📡 REST & MCP API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET / POST` | `/api/mcp` | **Unified MCP Gateway** (Universal tool discovery & JSON-RPC document processing for AI agents) |
| `POST` | `/api/convert/file` | Converts an uploaded file stream (supports `enable_plugins`, `openai_api_key`, `keep_data_uris`, etc.) |
| `POST` | `/api/convert/url` | Fetches and converts a remote URL, YouTube link, or Wikipedia article |
| `POST` | `/api/convert/text` | Converts raw HTML or text snippets to Markdown |
| `POST` | `/api/convert/batch` | Accepts multiple files and returns an in-memory `.zip` archive containing `.md` files |
| `GET` | `/api/formats` | Returns a JSON list of supported file extensions and capabilities |
| `GET` | `/api/health` | System health check and engine status |

---

## 🎨 Design Philosophy (`alchemist4real`)

- **Typography**: Dual typography pairing `Cormorant Garamond` (editorial serif) for headings and `DM Mono` (monospaced) for interface labels, metrics, code, and logs.
- **Color Tokens**: High contrast `#FAFAFA` (light) / `#0D0D0D` (dark) base with sharp 1px borders (`#E5E5E5` / `#2A2A2A`), green live status dots (`#22C55E`), and blue flow accents (`#2563eb`).
- **Interactive Pipeline Matrix**: SVG fractal noise texture (`opacity: 0.025`) combined with animated wire-flow dashes depicting data flow across conversion stages.

---

## 📄 License & Trademarks

This project is open-source under the MIT License. Microsoft and MarkItDown are trademarks of Microsoft Corporation.
