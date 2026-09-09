"""FastAPI backend for the iOS Shortcut and other clients.

    uvicorn api.main:app --port 8000

    GET  /health            -> {"status": "ok", "model": ..., "ocr": bool}
    POST /scan-text  JSON   {"text": "..."} -> verdict JSON
    POST /scan       multipart form field "file" (screenshot) -> verdict JSON (+ "text")
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline  # noqa: E402

app = FastAPI(title="DoppelCheck API", version="0.1")


class TextIn(BaseModel):
    text: str


def _ocr_ready() -> bool:
    try:
        import ocr
        return ocr.ocr_available()
    except Exception:
        return False


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": pipeline.get_classifier().name, "ocr": _ocr_ready()}


@app.post("/scan-text")
def scan_text(body: TextIn) -> dict:
    return pipeline.analyze(body.text)


@app.post("/scan")
async def scan(file: UploadFile = File(...)) -> dict:
    try:
        image = Image.open(io.BytesIO(await file.read()))
    except Exception:
        raise HTTPException(status_code=400, detail="Datei ist kein lesbares Bild")
    try:
        import ocr
        text = ocr.extract_text(image)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"OCR nicht verfügbar: {type(e).__name__}: {e}")
    result = pipeline.analyze(text)
    result["text"] = text
    return result
