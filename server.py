#!/usr/bin/env python3
"""
Local launcher script for markitdowninweb web application.
Runs Uvicorn dev server on http://localhost:8000
"""
import uvicorn
import os
import sys

# Ensure api directory is in sys.path
api_dir = os.path.join(os.path.dirname(__file__), "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from index import app

if __name__ == "__main__":
    print("=" * 65)
    print("  🚀 Starting MARKITDOWNINWEB Server...")
    print("  📍 Local Access:  http://localhost:8000")
    print("  📚 API Docs:      http://localhost:8000/docs")
    print("=" * 65)
    uvicorn.run(app, host="127.0.0.1", port=8000)
