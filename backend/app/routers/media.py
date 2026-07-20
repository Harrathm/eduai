"""Media upload and management for courses."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.deps import require_admin
from app.models import User

router = APIRouter(tags=["Media"])


ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}
ALLOWED_VIDEO = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
ALLOWED_DOCUMENT = {"application/pdf"}
ALLOWED_AUDIO = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3"}

ALLOWED_ALL = ALLOWED_IMAGE | ALLOWED_VIDEO | ALLOWED_DOCUMENT | ALLOWED_AUDIO

MAX_IMAGE_SIZE = 10 * 1024 * 1024      # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024     # 500 MB
MAX_DOC_SIZE = 50 * 1024 * 1024        # 50 MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024      # 50 MB

UPLOAD_DIR = "uploads"


def get_max_size(mime_type: str) -> int:
    if mime_type in ALLOWED_IMAGE: return MAX_IMAGE_SIZE
    if mime_type in ALLOWED_VIDEO: return MAX_VIDEO_SIZE
    if mime_type in ALLOWED_DOCUMENT: return MAX_DOC_SIZE
    if mime_type in ALLOWED_AUDIO: return MAX_AUDIO_SIZE
    return MAX_IMAGE_SIZE


def get_upload_subdir(mime_type: str) -> str:
    if mime_type in ALLOWED_IMAGE: return "images"
    if mime_type in ALLOWED_VIDEO: return "videos"
    if mime_type in ALLOWED_DOCUMENT: return "documents"
    if mime_type in ALLOWED_AUDIO: return "audio"
    return "misc"


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    lesson_id: Optional[int] = Form(None),
    course_id: Optional[int] = Form(None),
    admin: User = Depends(require_admin),
):
    if file.size and file.size > get_max_size(file.content_type):
        raise HTTPException(status_code=413, detail=f"File too large for type {file.content_type}")

    if file.content_type not in ALLOWED_ALL:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    subdir = get_upload_subdir(file.content_type)
    dated_dir = os.path.join(UPLOAD_DIR, subdir, datetime.now(timezone.utc).strftime("%Y/%m"))
    os.makedirs(dated_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "file")[1] or ""
    if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
                           ".mp4", ".webm", ".ogg", ".mov",
                           ".pdf", ".mp3", ".wav"]:
        ext = ""

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(dated_dir, unique_name)
    url_path = file_path.replace("\\", "/")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_size = len(content)
    mime = file.content_type

    return {
        "url": f"/{url_path}",
        "filename": file.filename or unique_name,
        "size": file_size,
        "mime_type": mime,
        "type": subdir.rstrip("s"),
    }


@router.get("/files")
def list_uploads(
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    allowed_types = {"images", "videos", "documents", "audio"}
    if type and type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid type")

    results = []
    search_dir = UPLOAD_DIR
    if type:
        search_dir = os.path.join(UPLOAD_DIR, type)

    if os.path.exists(search_dir):
        for root, dirs, files in os.walk(search_dir):
            for fname in files:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, ".")
                stat = os.stat(full_path)
                ext = os.path.splitext(fname)[1].lower()
                mime = "application/octet-stream"
                if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]:
                    mime = f"image/{ext[1:]}"
                elif ext in [".mp4", ".webm", ".ogg", ".mov"]:
                    mime = f"video/{ext[1:]}"
                elif ext == ".pdf":
                    mime = "application/pdf"
                elif ext in [".mp3", ".wav"]:
                    mime = f"audio/{ext[1:]}"

                results.append({
                    "path": f"/{rel_path.replace(chr(92), '/')}",
                    "filename": fname,
                    "size": stat.st_size,
                    "mime_type": mime,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })

    return sorted(results, key=lambda x: x["modified"], reverse=True)[skip : skip + limit]


@router.get("/{path:path}")
def serve_upload(path: str, admin: User = Depends(require_admin)):
    safe_path = os.path.normpath(os.path.join(UPLOAD_DIR, path))
    if not safe_path.startswith(UPLOAD_DIR) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(safe_path)


@router.delete("/files")
def delete_file(
    path: str,
    admin: User = Depends(require_admin),
):
    safe_path = os.path.normpath(os.path.join(UPLOAD_DIR, path.lstrip("/")))
    if not safe_path.startswith(os.path.normpath(UPLOAD_DIR)) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(safe_path)
    return {"success": True}