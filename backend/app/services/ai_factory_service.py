"""AI Pedagogical Factory - Course bundle generation using LLMs with RAG integration."""

import json
import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import User

logger = logging.getLogger(__name__)

AI_AVAILABLE = False
try:
    from openai import OpenAI
    AI_AVAILABLE = True
except ImportError:
    OpenAI = None

settings = get_settings()

SYSTEM_PROMPTS = {
    "plan_generator": (
        "You are an expert curriculum designer. Generate a comprehensive course plan as JSON. "
        "The JSON must have: title, subtitle, description, level (beginner/intermediate/advanced), "
        "category, estimated_duration_hours, and modules array. Each module has: title, description, "
        "order, and lessons array. Each lesson has: title, description, order, duration_minutes. "
        "Generate 3-5 modules with 3-5 lessons each."
    ),
    "lesson_generator": (
        "You are an expert teacher. Write detailed, engaging lesson content in French. "
        "Include learning objectives, key concepts, examples, exercises, and a summary. "
        "Format with clear headings and paragraphs."
    ),
    "quiz_generator": (
        "You are an expert assessment designer. Generate a quiz as JSON with: "
        "title, description, passing_score (percentage), and questions array. "
        "Each question has: question_text, type (multiple_choice/true_false/short_answer), "
        "options (array for multiple_choice), correct_answer, explanation, points. "
        "Generate 5 relevant questions."
    ),
    "media_prompt_generator": (
        "You are a creative director. Generate prompts for educational media content. "
        "Return JSON with: image_prompt (detailed DALL-E prompt for educational illustration), "
        "video_prompt (detailed video scene description)."
    ),
}


class AIFactoryService:
    """AI-powered course content generation service."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        api_key = settings.openai_api_key or ""
        self.available = AI_AVAILABLE and bool(api_key)
        self._api_key = api_key
        self._client: Optional[OpenAI] = None
        self._rag_service = None

    @property
    def client(self) -> OpenAI:
        if self._client is None and self.available:
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def _get_rag_context(self, school_id: int, query: str, k: int = 5) -> str:
        try:
            from app.ai.rag_service import RAGService
            if self._rag_service is None:
                self._rag_service = RAGService()
            docs = self._rag_service.retrieve_context(school_id, query, k=k)
            if docs:
                return "\n\n".join(docs)
        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
        return ""

    def _call_llm(self, messages: list, temperature: float = 0.7, max_tokens: int = 4000) -> str:
        # Use multi-provider client if db is available
        if self.db is not None:
            try:
                from app.ai.provider_client import generate_chat
                return generate_chat(
                    self.db, messages,
                    model=None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.warning(f"Provider client failed in AIFactory: {e}")
                raise RuntimeError(f"AI provider error: {e}") from e
        if not self.available or not self.client:
            raise RuntimeError("AI service not available - no provider configured")
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def _parse_json(self, content: str) -> dict:
        content = content.strip()
        for marker in ["```json", "```JSON", "```"]:
            if marker in content:
                parts = content.split(marker)
                content = "".join(parts[1:])
                if marker != "```":
                    content = content.replace("```", "", 1)
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        first_brace = content.find("{")
        if first_brace != -1:
            depth = 0
            for i in range(first_brace, len(content)):
                if content[i] == "{":
                    depth += 1
                elif content[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(content[first_brace : i + 1])
                        except json.JSONDecodeError:
                            break
        return {"error": "Failed to parse JSON", "raw": content[:500]}

    def generate_course_plan(self, topic: str, school_id: int = 0, use_rag: bool = False) -> dict:
        context = ""
        if use_rag and school_id:
            context = self._get_rag_context(school_id, topic)
        system_prompt = SYSTEM_PROMPTS["plan_generator"]
        user_prompt = f"Generate a comprehensive course plan about: {topic}"
        if context:
            user_prompt = f"""Based on the following reference materials, generate a comprehensive course plan about: {topic}

REFERENCE MATERIALS:
{context}

Use these materials to inform the course structure and content."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = self._call_llm(messages, temperature=0.7, max_tokens=4000)
        return self._parse_json(raw)

    def generate_lesson_content_stream(
        self, topic: str, lesson_title: str, lesson_description: str,
        module_title: str = "", school_id: int = 0, use_rag: bool = False
    ) -> AsyncGenerator[str, None]:
        context = ""
        if use_rag and school_id:
            context = self._get_rag_context(school_id, f"{topic} {lesson_title}")

        system_prompt = SYSTEM_PROMPTS["lesson_generator"]
        user_prompt = f"""Course Topic: {topic}
Module: {module_title}
Lesson Title: {lesson_title}
Lesson Description: {lesson_description}

Write comprehensive, engaging lesson content for this lesson."""
        if context:
            user_prompt = f"""Course Topic: {topic}
Module: {module_title}
Lesson Title: {lesson_title}
Lesson Description: {lesson_description}

REFERENCE MATERIALS:
{context}

Write comprehensive, engaging lesson content for this lesson, incorporating insights from the reference materials."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Use provider client if db is available
            if self.db is not None:
                try:
                    from app.ai.provider_client import generate_chat_stream
                    for chunk_text, error in generate_chat_stream(
                        self.db, messages, model=None, temperature=0.7, max_tokens=4000,
                    ):
                        if error:
                            yield "data: " + json.dumps({"error": error}) + "\n\n"
                        elif chunk_text:
                            yield "data: " + json.dumps({"chunk": chunk_text}) + "\n\n"
                    yield "data: [DONE]\n\n"
                    return
                except Exception as e:
                    logger.warning(f"Provider client stream failed, falling back: {e}")

            # Fallback to OpenAI client
            if not self.available or not self.client:
                yield "data: " + json.dumps({"error": "AI service not available"}) + "\n\n"
                yield "data: [DONE]\n\n"
                return

            stream = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield "data: " + json.dumps({"chunk": delta.content}) + "\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield "data: " + json.dumps({"error": str(e)}) + "\n\n"
            yield "data: [DONE]\n\n"

    def generate_quiz(
        self, topic: str, lesson_title: str, lesson_content: str = ""
    ) -> dict:
        system_prompt = SYSTEM_PROMPTS["quiz_generator"]
        user_prompt = f"""Course Topic: {topic}
Lesson: {lesson_title}"""
        if lesson_content:
            user_prompt += f"\n\nLesson Content:\n{lesson_content[:2000]}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = self._call_llm(messages, temperature=0.5, max_tokens=2000)
        parsed = self._parse_json(raw)
        return self._normalize_quiz(parsed)

    def _normalize_quiz(self, quiz: dict) -> dict:
        """Normalize quiz data to ensure consistent structure."""
        if not isinstance(quiz, dict) or "error" in quiz:
            return {"title": "", "description": "", "passing_score": 70, "questions": []}
        questions = quiz.get("questions", [])
        if not isinstance(questions, list):
            questions = []
        normalized = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            qn = {
                "question_text": q.get("question_text", q.get("question", "")),
                "type": q.get("type", "multiple_choice"),
                "points": q.get("points", 1),
                "explanation": q.get("explanation", ""),
                "options": [],
                "correct_answer": q.get("correct_answer", ""),
            }
            options = q.get("options", [])
            if isinstance(options, list):
                for opt in options:
                    if isinstance(opt, str):
                        is_correct = opt.lower() == qn["correct_answer"].lower() if qn["correct_answer"] else False
                        qn["options"].append({"option_text": opt, "is_correct": is_correct})
                    elif isinstance(opt, dict):
                        qn["options"].append({
                            "option_text": opt.get("option_text", opt.get("text", "")),
                            "is_correct": opt.get("is_correct", False),
                        })
            normalized.append(qn)
        quiz["questions"] = normalized
        return quiz

    def generate_media_prompts(self, topic: str, lesson_title: str, lesson_description: str = "") -> dict:
        system_prompt = SYSTEM_PROMPTS["media_prompt_generator"]
        user_prompt = f"""Course Topic: {topic}
Lesson: {lesson_title}
Description: {lesson_description}"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = self._call_llm(messages, temperature=0.8, max_tokens=2000)
        return self._parse_json(raw)

    def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "standard") -> dict:
        """Generate an image using DALL-E 3 and return the URL."""
        if not self.available or not self.client:
            raise RuntimeError("AI service not available - OpenAI client required for DALL-E")
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            return {
                "url": response.data[0].url,
                "revised_prompt": response.data[0].revised_prompt,
            }
        except Exception as e:
            logger.error(f"DALL-E image generation failed: {e}")
            raise RuntimeError(f"Image generation failed: {str(e)}") from e

    def generate_course_bundle(
        self, topic: str, plan: dict, school_id: int = 0, use_rag: bool = False
    ) -> dict:
        """Generate all lesson content, quizzes, and media prompts for a course plan."""
        bundle = {"plan": plan, "lessons": {}, "quizzes": {}, "media_prompts": {}}
        for module in plan.get("modules", []):
            for lesson in module.get("lessons", []):
                key = f"{module['title']}::{lesson['title']}"
                try:
                    lesson_content = self._call_llm([
                        {"role": "system", "content": SYSTEM_PROMPTS["lesson_generator"]},
                        {"role": "user", "content": f"Course: {topic}\nModule: {module['title']}\nLesson: {lesson['title']}\nDescription: {lesson.get('description', '')}\n\nWrite comprehensive lesson content."},
                    ], temperature=0.7, max_tokens=3000)
                    bundle["lessons"][key] = lesson_content
                except Exception as e:
                    logger.warning(f"Failed to generate lesson {key}: {e}")
                    bundle["lessons"][key] = ""
                try:
                    quiz = self.generate_quiz(topic, lesson["title"], bundle["lessons"].get(key, ""))
                    bundle["quizzes"][key] = quiz
                except Exception as e:
                    logger.warning(f"Failed to generate quiz {key}: {e}")
                    bundle["quizzes"][key] = {"questions": []}
                try:
                    media = self.generate_media_prompts(topic, lesson["title"], lesson.get("description", ""))
                    bundle["media_prompts"][key] = media
                except Exception as e:
                    logger.warning(f"Failed to generate media prompts {key}: {e}")
                    bundle["media_prompts"][key] = {"image_prompt": "", "video_prompt": ""}
        return bundle

    def publish_course(self, bundle: dict, author: User, school_id: int, db) -> dict:
        """Publish the generated course bundle to the database."""
        from app.models import Course, Module as CourseModule, Lesson, Quiz, QuizQuestion, QuizOption, CourseStatus
        from datetime import datetime, timezone

        plan = bundle.get("plan", {})
        title = plan.get("title", "Untitled Course")
        slug = title.lower().replace(" ", "-").replace("'", "")[:200]
        course = Course(
            title=title,
            description=plan.get("description", ""),
            short_description=plan.get("description", "")[:500] if plan.get("description") else "",
            level=plan.get("level", "beginner"),
            category=plan.get("category", "general"),
            status=CourseStatus.PUBLISHED,
            is_published=True,
            published_at=datetime.now(timezone.utc),
            author_id=author.id,
            school_id=school_id or author.school_id,
            total_duration_minutes=int(plan.get("estimated_duration_hours", 10) * 60),
            slug=slug,
            total_modules=len(plan.get("modules", [])),
            total_lessons=sum(len(m.get("lessons", [])) for m in plan.get("modules", [])),
            visibility="public",
            enrollment_type="open",
        )
        db.add(course)
        db.flush()

        media_assets = bundle.get("media_assets", {})
        media_prompts = bundle.get("media_prompts", {})
        quizzes = bundle.get("quizzes", {})

        module_order = 0
        for mod in plan.get("modules", []):
            db_module = CourseModule(
                course_id=course.id,
                title=mod.get("title", ""),
                description=mod.get("description", ""),
                order=module_order,
            )
            db.add(db_module)
            db.flush()

            lesson_order = 0
            for les in mod.get("lessons", []):
                key = f"{mod['title']}::{les['title']}"
                image_url = media_assets.get(key, {}).get("image_url", "") if isinstance(media_assets.get(key), dict) else ""
                prompts = media_prompts.get(key, {}) if isinstance(media_prompts.get(key), dict) else {}
                quiz_data = quizzes.get(key, {}) if isinstance(quizzes.get(key), dict) else {}

                db_lesson = Lesson(
                    module_id=db_module.id,
                    school_id=school_id or author.school_id,
                    teacher_id=author.id,
                    title=les.get("title", ""),
                    description=les.get("description", ""),
                    order=lesson_order,
                    content_text=bundle.get("lessons", {}).get(key, ""),
                    duration_minutes=les.get("duration_minutes", 45),
                    lesson_type="text",
                    image_urls=image_url if image_url else None,
                    ai_image_prompt=prompts.get("image_prompt", ""),
                    ai_video_prompt=prompts.get("video_prompt", ""),
                )
                db.add(db_lesson)
                db.flush()

                # Save quiz if generated
                if quiz_data and isinstance(quiz_data.get("questions"), list) and quiz_data.get("questions"):
                    db_quiz = Quiz(
                        lesson_id=db_lesson.id,
                        title=quiz_data.get("title", f"Quiz: {les.get('title', '')}"),
                        description=quiz_data.get("description", ""),
                        passing_score_percent=quiz_data.get("passing_score", 70),
                        total_points=sum(q.get("points", 1) for q in quiz_data.get("questions", [])),
                    )
                    db.add(db_quiz)
                    db.flush()

                    for qi, q in enumerate(quiz_data.get("questions", [])):
                        if not isinstance(q, dict):
                            continue
                        db_question = QuizQuestion(
                            quiz_id=db_quiz.id,
                            question_text=q.get("question_text", ""),
                            question_type=q.get("type", "mcq"),
                            points=q.get("points", 1),
                            explanation=q.get("explanation", ""),
                            order_index=qi,
                        )
                        db.add(db_question)
                        db.flush()

                        for oi, opt in enumerate(q.get("options", [])):
                            if isinstance(opt, str):
                                opt_text = opt
                                is_correct = opt.lower() == q.get("correct_answer", "").lower()
                            elif isinstance(opt, dict):
                                opt_text = opt.get("option_text", opt.get("text", ""))
                                is_correct = opt.get("is_correct", False)
                            else:
                                continue
                            db_option = QuizOption(
                                question_id=db_question.id,
                                option_text=opt_text,
                                is_correct=is_correct,
                                order_index=oi,
                            )
                            db.add(db_option)

                    db_lesson.quiz_id = db_quiz.id

                lesson_order += 1
            module_order += 1

        db.commit()
        db.refresh(course)

        return {
            "course_id": course.id,
            "title": course.title,
            "slug": course.slug,
            "status": "published",
        }
