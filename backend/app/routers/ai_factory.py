"""AI Pedagogical Factory - API routes for AI-powered course content generation."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.routers.admin import require_admin, require_platform_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/ai-factory", tags=["AI Factory"])


class GeneratePlanRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    use_rag: bool = False


class GeneratePlanResponse(BaseModel):
    plan: dict


class GenerateContentStreamRequest(BaseModel):
    topic: str
    lesson_title: str
    lesson_description: str
    module_title: str = ""
    use_rag: bool = False


class GenerateQuizRequest(BaseModel):
    topic: str
    lesson_title: str
    lesson_content: str = ""


class GenerateQuizResponse(BaseModel):
    quiz: dict


class GenerateMediaPromptsRequest(BaseModel):
    topic: str
    lesson_title: str
    lesson_description: str = ""


class GenerateMediaPromptsResponse(BaseModel):
    image_prompt: str
    video_prompt: str


class GenerateImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"


class GenerateImageResponse(BaseModel):
    url: str
    revised_prompt: str


class SaveImageToBundleRequest(BaseModel):
    bundle: dict
    lesson_key: str
    image_url: str
    image_prompt: str = ""


class SaveImageToBundleResponse(BaseModel):
    bundle: dict


class PublishCourseRequest(BaseModel):
    bundle: dict


class PublishCourseResponse(BaseModel):
    course_id: int
    title: str
    slug: str = ""
    status: str


class PreviewCourseRequest(BaseModel):
    bundle: dict


class PreviewCourseResponse(BaseModel):
    preview: dict


@router.post("/generate-plan", response_model=GeneratePlanResponse)
def generate_plan(
    req: GeneratePlanRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Step 1: Generate a course plan from a topic."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)
    try:
        plan = factory.generate_course_plan(
            topic=req.topic,
            school_id=current_user.school_id or 0,
            use_rag=req.use_rag,
        )
        return GeneratePlanResponse(plan=plan)
    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")


@router.post("/generate-content-stream")
def generate_content_stream(
    req: GenerateContentStreamRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Step 3 (streaming): Generate lesson content via SSE."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)

    return StreamingResponse(
        factory.generate_lesson_content_stream(
            topic=req.topic,
            lesson_title=req.lesson_title,
            lesson_description=req.lesson_description,
            module_title=req.module_title,
            school_id=current_user.school_id or 0,
            use_rag=req.use_rag,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate-quiz", response_model=GenerateQuizResponse)
def generate_quiz(
    req: GenerateQuizRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Generate quiz questions for a lesson."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)
    try:
        quiz = factory.generate_quiz(
            topic=req.topic,
            lesson_title=req.lesson_title,
            lesson_content=req.lesson_content,
        )
        return GenerateQuizResponse(quiz=quiz)
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.post("/generate-media-prompts", response_model=GenerateMediaPromptsResponse)
def generate_media_prompts(
    req: GenerateMediaPromptsRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Generate DALL-E image and video prompts for a lesson."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)
    try:
        prompts = factory.generate_media_prompts(
            topic=req.topic,
            lesson_title=req.lesson_title,
            lesson_description=req.lesson_description,
        )
        return GenerateMediaPromptsResponse(
            image_prompt=prompts.get("image_prompt", ""),
            video_prompt=prompts.get("video_prompt", ""),
        )
    except Exception as e:
        logger.error(f"Media prompt generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Media prompt generation failed: {str(e)}")


@router.post("/generate-image", response_model=GenerateImageResponse)
def generate_image(
    req: GenerateImageRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Generate an image using DALL-E 3 from a prompt."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)
    try:
        result = factory.generate_image(
            prompt=req.prompt,
            size=req.size,
            quality=req.quality,
        )
        return GenerateImageResponse(
            url=result["url"],
            revised_prompt=result.get("revised_prompt", ""),
        )
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/save-image-to-bundle", response_model=SaveImageToBundleResponse)
def save_image_to_bundle(
    req: SaveImageToBundleRequest,
    current_user: User = Depends(require_platform_admin),
):
    """Save a generated image URL to the course bundle for later publishing."""
    bundle = req.bundle
    if "media_assets" not in bundle:
        bundle["media_assets"] = {}
    bundle["media_assets"][req.lesson_key] = {
        "image_url": req.image_url,
        "image_prompt": req.image_prompt,
    }
    return SaveImageToBundleResponse(bundle=bundle)


@router.post("/generate-bundle")
def generate_full_bundle(
    req: GeneratePlanRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Generate complete course bundle (plan + all content) in one call."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)
    try:
        plan = factory.generate_course_plan(
            topic=req.topic,
            school_id=current_user.school_id or 0,
            use_rag=req.use_rag,
        )
        bundle = factory.generate_course_bundle(
            topic=req.topic,
            plan=plan,
            school_id=current_user.school_id or 0,
            use_rag=req.use_rag,
        )
        return bundle
    except Exception as e:
        logger.error(f"Bundle generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bundle generation failed: {str(e)}")


@router.post("/publish", response_model=PublishCourseResponse)
def publish_course(
    req: PublishCourseRequest,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Publish the generated course bundle as a draft course in the database."""
    from app.services.ai_factory_service import AIFactoryService
    factory = AIFactoryService(db=db)
    try:
        result = factory.publish_course(
            bundle=req.bundle,
            author=current_user,
            school_id=current_user.school_id,
            db=db,
        )
        return PublishCourseResponse(**result)
    except Exception as e:
        logger.error(f"Publish failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Publish failed: {str(e)}")


@router.post("/preview", response_model=PreviewCourseResponse)
def preview_course(
    req: PreviewCourseRequest,
    current_user: User = Depends(require_platform_admin),
):
    """Preview the generated course bundle (no DB write)."""
    bundle = req.bundle
    plan = bundle.get("plan", {})
    modules = plan.get("modules", [])
    total_lessons = sum(len(m.get("lessons", [])) for m in modules)
    lessons_detail = []
    for mod in modules:
        for les in mod.get("lessons", []):
            key = f"{mod['title']}::{les['title']}"
            lessons_detail.append({
                "module_title": mod["title"],
                "lesson_title": les["title"],
                "description": les.get("description", ""),
                "has_content": key in bundle.get("lessons", {}),
                "has_quiz": key in bundle.get("quizzes", {}),
                "has_media_prompts": key in bundle.get("media_prompts", {}),
            })
    return PreviewCourseResponse(preview={
        "title": plan.get("title", ""),
        "subtitle": plan.get("subtitle", ""),
        "description": plan.get("description", ""),
        "level": plan.get("level", "beginner"),
        "category": plan.get("category", ""),
        "total_modules": len(modules),
        "total_lessons": total_lessons,
        "lessons": lessons_detail,
    })


@router.get("/rag-debug")
def rag_debug(
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Debug: check RAG index status for current user's school."""
    from app.ai.embeddings_service import EmbeddingsService
    es = EmbeddingsService()
    effective_school_id = current_user.school_id or 0
    stats = es.get_stats(effective_school_id)

    docs_preview = []
    existing = es.load_index(effective_school_id)
    if existing:
        _, docs = existing
        for d in docs[:5]:
            docs_preview.append({
                "content_preview": d.page_content[:200],
                "source": d.metadata.get("source", "unknown"),
                "chunk_index": d.metadata.get("chunk_index", -1),
            })

    return {
        "school_id": effective_school_id,
        "user_school_id": current_user.school_id,
        "stats": stats,
        "docs_preview": docs_preview,
    }
