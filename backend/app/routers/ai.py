from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.db import get_db
from app.auth import get_current_user
from app.models import User, AIUsageLog, Lesson, Module, Course, BillableFeature
from app.schemas import AIQuery, AIResult
from app.models_ai_conversations import AIConversation, AIChatMessage
from app.services.wallet import (
    estimate_cost as wallet_estimate_cost,
    tokens_to_credits,
    get_total_balance,
    consume_credits,
    check_low_balance_alert,
    InsufficientCreditsError,
)
from app.services.student_tier import get_ai_feature_level
from app.core.rate_limiter import check_ai_rate_limit
import os
import logging
import uuid

router = APIRouter(tags=["AI"])


def _validate_school_id(user: User) -> int:
    """Valide et retourne le school_id de l'utilisateur."""
    if not user.school_id or user.school_id <= 0:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Compte non associé à une école. Contactez votre administrateur."
        )
    return user.school_id


def log_ai_usage(db: Session, user: User, action: str, tokens: int = 0, cost: float = 0.0):
    log = AIUsageLog(
        user_id=user.id,
        action=action,
        tokens_used=tokens,
        cost_usd=cost,
        school_id=user.school_id or 0,
    )
    db.add(log)
    db.commit()


def estimate_cost(model: str, tokens: int) -> float:
    rates = {"gpt-4o": 0.015, "gpt-4o-mini": 0.003, "gpt-4-turbo": 0.01, "gpt-3.5-turbo": 0.002}
    return (tokens / 1000) * rates.get(model, 0.003)


def _detect_language(text: str) -> str:
    """Détecte la langue dominante d'un texte : 'ar', 'fr', 'en'."""
    import re
    if not text:
        return "fr"
    arabic = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
    latin = len(re.findall(r'[a-zA-ZÀ-ÿ]', text))
    total = arabic + latin
    if total == 0:
        return "fr"
    return "ar" if arabic / total > 0.3 else "fr"


def _save_chat_message(db: Session, conversation_id: int, role: str, content: str, user_id: int) -> AIChatMessage:
    """Sauvegarde un message dans une conversation IA avec détection de langue."""
    from app.models_ai_conversations import AIConversation
    conv = db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    if conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé à cette conversation")
    detected = _detect_language(content)
    msg = AIChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        detected_language=detected,
    )
    db.add(msg)
    from datetime import datetime, timezone
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(msg)
    return msg


def _get_or_create_conversation(db: Session, user_id: int, title: str) -> AIConversation:
    """Crée une nouvelle conversation ou retourne une existante."""
    conv = AIConversation(user_id=user_id, title=title[:255])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _load_conversation_history(db: Session, conversation_id: int, max_messages: int = 20) -> list:
    """Charge l'historique des messages d'une conversation pour le contexte RAG.
    Limite aux derniers `max_messages` pour éviter de dépasser les limites OpenAI."""
    messages = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.conversation_id == conversation_id)
        .order_by(AIChatMessage.created_at.desc())
        .limit(max_messages)
        .all()
    )
    messages.reverse()
    return [{"role": m.role, "content": m.content} for m in messages]


@router.post("/ask", response_model=AIResult)
def ask_tutor(
    query: AIQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.ai import RAGService

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_ask")

    # Validate school_id
    school_id = _validate_school_id(current_user)

    # Pre-check: verify sufficient credits
    feature = BillableFeature.AI_ASK
    estimated = wallet_estimate_cost(feature, len(query.question))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}. "
                   "Rechargez votre portefeuille ou contactez votre école.",
        )

    # Consume credits before AI call
    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        rag = RAGService(db=db)

        # Auto-créer la conversation si aucune fournie
        conv_id = query.conversation_id
        if not conv_id:
            conv = _get_or_create_conversation(db, current_user.id, query.question[:255])
            conv_id = conv.id

        # Charger l'historique pour le contexte RAG
        history = _load_conversation_history(db, conv_id)

        answer = rag.ask_tutor(
            school_id=school_id,
            question=query.question,
            conversation_history=history,
        )
        tokens = len(answer) // 4
        cost_usd = estimate_cost(rag.model, tokens)
        log_ai_usage(db, current_user, "ask_tutor", tokens, cost_usd)

        # Sauvegarder les messages avec détection de langue
        _save_chat_message(db, conv_id, "user", query.question, current_user.id)
        _save_chat_message(db, conv_id, "assistant", answer, current_user.id)

        # Check low balance alert after consumption
        alert = check_low_balance_alert(db, current_user.id)

        result = AIResult(answer=answer, sources=[], conversation_id=conv_id)
        return result
    except Exception as e:
        # Refund on failure
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/explain", response_model=AIResult)
def explain_concept(
    query: AIQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.ai import RAGService

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_explain")

    # Pre-check
    feature = BillableFeature.AI_EXPLAIN
    estimated = wallet_estimate_cost(feature, len(query.question))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        rag = RAGService(db=db)
        answer = rag.explain_concept(school_id=current_user.school_id, concept=query.question)
        tokens = len(answer) // 4
        cost_usd = estimate_cost(rag.model, tokens)
        log_ai_usage(db, current_user, "explain_concept", tokens, cost_usd)
        return AIResult(answer=answer, sources=[])
    except Exception as e:
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/correct", response_model=dict)
def correct_assignment(
    assignment_text: str,
    question: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.ai import RAGService

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_correct")

    # Pre-check
    feature = BillableFeature.AI_CORRECT
    estimated = wallet_estimate_cost(feature, len(assignment_text) + len(question))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        rag = RAGService(db=db)
        result = rag.auto_correct(
            school_id=current_user.school_id,
            assignment_text=assignment_text,
            question=question,
        )
        tokens = len(str(result)) // 4
        cost_usd = estimate_cost(rag.model, tokens)
        log_ai_usage(db, current_user, "auto_correct", tokens, cost_usd)
        return result
    except Exception as e:
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/quiz", response_model=list[dict])
def generate_quiz(
    topic: str,
    num_questions: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.ai import RAGService

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_quiz")

    # Pre-check
    feature = BillableFeature.AI_QUIZ
    estimated = wallet_estimate_cost(feature, len(topic))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        rag = RAGService(db=db)
        questions = rag.generate_quiz(
            school_id=current_user.school_id,
            topic=topic,
            num_questions=num_questions,
        )
        tokens = num_questions * 200
        cost_usd = estimate_cost(rag.model, tokens)
        log_ai_usage(db, current_user, "generate_quiz", tokens, cost_usd)
        return questions
    except Exception as e:
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/exercises", response_model=list[dict])
def generate_exercises(
    topic: str,
    num_exercises: int = 5,
    difficulty: str = "medium",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.ai import RAGService

    # Tier check: exercises require adaptive+ (excellence/etablissement)
    ai_level = get_ai_feature_level(current_user, db)
    if ai_level == "basic":
        raise HTTPException(
            status_code=403,
            detail="Génération d'exercices réservée aux paliers Excellence et Établissement. Passez à un pack supérieur.",
        )

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_generate")

    # Pre-check
    feature = BillableFeature.AI_GENERATE
    estimated = wallet_estimate_cost(feature, len(topic))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        rag = RAGService(db=db)
        exercises = rag.generate_exercises(
            school_id=current_user.school_id,
            topic=topic,
            num_exercises=num_exercises,
            difficulty=difficulty,
        )
        tokens = num_exercises * 150
        cost_usd = estimate_cost(rag.model, tokens)
        log_ai_usage(db, current_user, "generate_exercises", tokens, cost_usd)
        return exercises
    except Exception as e:
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/ingest/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can ingest content")

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_ingest")

    # Pre-check
    feature = BillableFeature.AI_INGEST
    estimated = wallet_estimate_cost(feature, 0)
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        from app.ai.pdf_processor import PDFProcessor
        from app.ai.embeddings_service import EmbeddingsService

        processor = PDFProcessor()
        contents = await file.read()
        chunks = processor.process_pdf_bytes(contents, file.filename or "upload")
        texts = [c["content"] for c in chunks]
        metadatas = [
            {"source": c["source"], "chunk_index": c["index"], "school_id": current_user.school_id}
            for c in chunks
        ]
        es = EmbeddingsService()
        es.add_to_index(current_user.school_id, texts, metadatas)
        log_ai_usage(db, current_user, "ingest_pdf", 0, 0.0)
        return {"chunks_added": len(texts), "school_id": current_user.school_id}
    except Exception as e:
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/ingest/text")
def ingest_text(
    text: str,
    source: str = "manual",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can ingest content")

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_ingest")

    # Pre-check
    feature = BillableFeature.AI_INGEST
    estimated = wallet_estimate_cost(feature, len(text))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    try:
        from app.ai.pdf_processor import PDFProcessor
        from app.ai.embeddings_service import EmbeddingsService

        processor = PDFProcessor()
        chunks = processor.chunk_text(text)
        metadatas = [
            {"source": source, "chunk_index": i, "school_id": current_user.school_id}
            for i in range(len(chunks))
        ]
        es = EmbeddingsService()
        es.add_to_index(current_user.school_id, chunks, metadatas)

        log_ai_usage(db, current_user, "ingest_text", len(text) // 4, 0.0)
        return {"chunks_added": len(chunks), "school_id": current_user.school_id}
    except Exception as e:
        for d in debits:
            from app.services.wallet import add_credits
            from app.models import WalletPool
            add_credits(db, current_user.id, d["pool"], d["amount"])
        raise


@router.post("/ingest/lesson/{lesson_id}")
def ingest_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("admin_school", "teacher", "pedagogical_admin", "pedagogical_lead", "super_admin"):
        raise HTTPException(status_code=403, detail="Only teachers or admins can ingest content")

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_ingest")

    lesson = db.query(Lesson).join(Module).join(Course).filter(
        Lesson.id == lesson_id,
        Course.school_id == current_user.school_id,
    ).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    from app.ai.pdf_processor import PDFProcessor
    from app.ai.embeddings_service import EmbeddingsService

    processor = PDFProcessor()
    content = lesson.content or ""
    if not content:
        raise HTTPException(status_code=400, detail="Lesson has no content to ingest")

    chunks = processor.chunk_text(content)
    metadatas = [
        {"source": f"lesson_{lesson_id}: {lesson.title}", "chunk_index": i, "school_id": current_user.school_id}
        for i in range(len(chunks))
    ]
    es = EmbeddingsService()
    es.add_to_index(current_user.school_id, chunks, metadatas)
    log_ai_usage(db, current_user, "ingest_lesson", len(content) // 4, 0.0)
    return {"chunks_added": len(chunks), "school_id": current_user.school_id}


@router.get("/usage", response_model=list[dict])
def get_ai_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = db.query(AIUsageLog).filter(
        AIUsageLog.school_id == current_user.school_id,
        AIUsageLog.user_id == current_user.id,
    ).order_by(AIUsageLog.created_at.desc()).limit(50).all()

    return [
        {
            "action": log.action,
            "tokens": log.tokens_used,
            "cost": log.cost_usd,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/stats")
def get_index_stats(
    current_user: User = Depends(get_current_user),
):
    import os
    idx_path = os.path.join("data", "faiss_indexes", f"school_{current_user.school_id}")
    has_index = os.path.exists(f"{idx_path}.index") and os.path.exists(f"{idx_path}.pkl")
    import pickle
    doc_count = 0
    if has_index:
        try:
            with open(f"{idx_path}.pkl", "rb") as f:
                docs = pickle.load(f)
                doc_count = len(docs)
        except Exception:
            doc_count = 0
    return {"has_index": has_index, "indexed_docs": doc_count}


@router.post("/generate")
def generate_content(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.ai import RAGService

    # Tier check: generate requires curriculum_aligned (etablissement only)
    ai_level = get_ai_feature_level(current_user, db)
    if ai_level != "curriculum_aligned":
        raise HTTPException(
            status_code=403,
            detail="Génération de contenu personnalisé réservée au palier Établissement. Contactez votre admin d'école.",
        )

    # Rate limit check
    check_ai_rate_limit(current_user.id, "ai_generate")

    # Pre-check: verify sufficient credits
    feature = BillableFeature.AI_GENERATE
    prompt = body.get("prompt", "")
    estimated = wallet_estimate_cost(feature, len(prompt))
    balance = get_total_balance(db, current_user.id)
    if balance < estimated:
        raise HTTPException(
            status_code=402,
            detail=f"Crédits insuffisants. Requis: ~{estimated}, disponible: {balance}.",
        )

    request_id = str(uuid.uuid4())
    debits = consume_credits(db, current_user.id, estimated, feature, request_id)

    content_type = body.get("type", "homework")
    subject = body.get("subject", "")
    level = body.get("level", "")
    trimester = body.get("trimester", "")

    if not prompt:
        raise HTTPException(status_code=400, detail="Le prompt est requis")

    type_labels = {
        "homework": "Devoir",
        "lesson": "Leçon",
        "lesson_plan": "Plan de leçon",
        "outline": "Plan annuel",
        "quiz": "Quiz",
        "summary": "Résumé",
    }
    type_label = type_labels.get(content_type, content_type)

    system_prompt = (
        f"Tu es un professeur {subject} niveau {level}. "
        f"Génère un {type_label} en français pour des élèves de {level} ({trimester}). "
        "Utilise un format clair et structuré."
    )

    # Check if any provider is configured
    from app.ai.provider_client import get_enabled_provider
    try:
        pid, pconf = get_enabled_provider(db)
        if not pid or not pconf:
            # Refund on early return
            for d in debits:
                from app.services.wallet import add_credits
                add_credits(db, current_user.id, d["pool"], d["amount"])
            return {"content": "Aucun fournisseur IA Configurez un fournisseur dans Parametres -> Fournisseurs IA."}
    except Exception:
        for d in debits:
            from app.services.wallet import add_credits
            add_credits(db, current_user.id, d["pool"], d["amount"])
        return {"content": "Aucun fournisseur IA Configurez un fournisseur dans Parametres -> Fournisseurs IA."}

    try:
        rag = RAGService(db=db)
        content = rag.generate_text(system_prompt=system_prompt, user_prompt=prompt)
        tokens = len(content) // 4
        cost = estimate_cost(rag.model, tokens)
        log_ai_usage(db, current_user, f"ai_studio_{content_type}", tokens, cost)

        # Sauvegarde dans la conversation si conversation_id fourni
        conversation_id = body.get("conversation_id")
        if conversation_id:
            _save_chat_message(db, conversation_id, "user", prompt, current_user.id)
            _save_chat_message(db, conversation_id, "assistant", content, current_user.id)

        return {"content": content}
    except Exception as e:
        # Refund on failure
        for d in debits:
            from app.services.wallet import add_credits
            add_credits(db, current_user.id, d["pool"], d["amount"])
        logger = logging.getLogger(__name__)
        logger.error(f"AI generate error: {e}")
        raise HTTPException(status_code=503, detail=f"Service IA temporairement indisponible : {str(e)}")


@router.get("/history")
def get_generation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = db.query(AIUsageLog).filter(
        AIUsageLog.user_id == current_user.id,
        AIUsageLog.action.like("ai_studio_%"),
    ).order_by(AIUsageLog.created_at.desc()).limit(20).all()

    return [
        {
            "id": log.id,
            "prompt": log.description or "Génération",
            "type": log.action.replace("ai_studio_", ""),
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]