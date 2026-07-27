"""
Router pour les tests de positionnement adaptatifs.
- GET  /placement/tests?matiere=X&niveau=Y : lister les tests disponibles
- POST /placement/tests/{id}/submit        : soumettre les réponses et obtenir le niveau
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from app.db import get_db
from app.auth import get_current_user
from app.models import (
    User, PlacementTest, PlacementTestResult,
    NiveauEtude, Matiere, ChapterPathway, ProfilAssimilationEleve,
    SourceChangement, StatutValidationProfil,
)

router = APIRouter(prefix="/placement", tags=["Placement"])


@router.get("/tests")
def list_placement_tests(
    matiere: Optional[str] = None,
    niveau: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(PlacementTest).filter(PlacementTest.is_active == True)
    if matiere:
        query = query.filter(PlacementTest.matiere == matiere)
    if niveau:
        query = query.filter(PlacementTest.niveau == niveau)
    tests = query.all()
    return [
        {
            "id": t.id,
            "matiere": t.matiere,
            "niveau": t.niveau,
            "title": t.title,
            "num_questions": len(t.questions.get("questions", [])) if isinstance(t.questions, dict) else 0,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tests
    ]


@router.get("/tests/{test_id}")
def get_placement_test(
    test_id: int,
    db: Session = Depends(get_db),
):
    test = db.query(PlacementTest).filter(PlacementTest.id == test_id, PlacementTest.is_active == True).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test de positionnement introuvable")
    return {
        "id": test.id,
        "matiere": test.matiere,
        "niveau": test.niveau,
        "title": test.title,
        "questions": test.questions,
    }


@router.post("/tests/{test_id}/submit")
def submit_placement_test(
    test_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soumet les réponses et calcule le niveau de compétence.
    Logique adaptative simple : score normalisé → 3 niveaux.
    Body: {"answers": [{"question_index": 0, "selected": "A"}, ...]}
    """
    test = db.query(PlacementTest).filter(PlacementTest.id == test_id, PlacementTest.is_active == True).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test de positionnement introuvable")

    answers = body.get("answers", [])
    if not answers:
        raise HTTPException(status_code=400, detail="Aucune réponse fournie")

    questions = test.questions.get("questions", []) if isinstance(test.questions, dict) else []
    if not questions:
        raise HTTPException(status_code=500, detail="Test sans questions")

    # Calcul du score
    correct = 0
    total = len(answers)
    answer_details = []

    for ans in answers:
        q_idx = ans.get("question_index", -1)
        selected = ans.get("selected", "")
        if 0 <= q_idx < len(questions):
            q = questions[q_idx]
            is_correct = selected.upper() == q.get("correct", "").upper() if isinstance(q.get("correct"), str) else selected == q.get("correct")
            if is_correct:
                correct += 1
            answer_details.append({
                "question_index": q_idx,
                "selected": selected,
                "correct": is_correct,
                "difficulty": q.get("difficulty", 1),
            })

    score = correct / total if total > 0 else 0.0

    # Logique adaptative : 3 niveaux basés sur le score
    if score >= 0.7:
        competency_level = "avance"
    elif score >= 0.4:
        competency_level = "intermediaire"
    else:
        competency_level = "debutant"

    # Vérifier si un résultat existe déjà pour ce test/élève → mettre à jour
    existing = db.query(PlacementTestResult).filter(
        PlacementTestResult.user_id == current_user.id,
        PlacementTestResult.placement_test_id == test_id,
    ).first()

    if existing:
        existing.competency_level = competency_level
        existing.score = score
        existing.answers = {"answers": answer_details}
        existing.completed_at = __import__("datetime").datetime.utcnow()
        result = existing
    else:
        result = PlacementTestResult(
            user_id=current_user.id,
            placement_test_id=test_id,
            competency_level=competency_level,
            score=score,
            answers={"answers": answer_details},
        )
        db.add(result)

    db.commit()
    db.refresh(result)

    # --- Bridge: create ProfilAssimilationEleve for each chapter ---
    # Map placement competency_level to NiveauAssimilation
    level_map = {
        "debutant": "remediation",
        "intermediaire": "standard",
        "intermédiaire": "standard",
        "avance": "avance",
    }
    niveau_assim = level_map.get(competency_level, "standard")

    # Find matching NiveauEtude + Matiere + chapters
    niveau_etude = db.query(NiveauEtude).filter(
        NiveauEtude.nom.ilike(f"%{test.niveau}%")
    ).first()
    if niveau_etude:
        matiere = db.query(Matiere).filter(
            Matiere.niveau_etude_id == niveau_etude.id,
            Matiere.nom.ilike(f"%{test.matiere}%"),
        ).first()
        if matiere:
            chapters = db.query(ChapterPathway).filter(
                ChapterPathway.matiere_id == matiere.id,
            ).all()
            for chapter in chapters:
                # Only create if no profile exists yet
                existing_profile = db.query(ProfilAssimilationEleve).filter(
                    ProfilAssimilationEleve.eleve_id == current_user.id,
                    ProfilAssimilationEleve.chapitre_id == chapter.id,
                ).first()
                if not existing_profile:
                    profil = ProfilAssimilationEleve(
                        eleve_id=current_user.id,
                        chapitre_id=chapter.id,
                        niveau_assimilation_courant=niveau_assim,
                        source_changement=SourceChangement.TEST_INITIAL.value,
                        score_declencheur=score,
                        date=datetime.now(timezone.utc),
                        statut_validation=StatutValidationProfil.AUTO_APPLIQUE.value,
                    )
                    db.add(profil)
            db.commit()

    return {
        "result_id": result.id,
        "competency_level": competency_level,
        "score": round(score * 100, 1),
        "correct": correct,
        "total": total,
        "detail": f"{correct}/{total} correct — niveau: {competency_level}",
    }
