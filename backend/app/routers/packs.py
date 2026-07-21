"""
Router pour les packs d'étude — catalogue public + achat individuel.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.models import (
    User, StudyPack, PackPurchase, PackStatus, PackPurchaseStatus,
    PurchaserType, Course, Transaction, TransactionType, Currency,
    School,
)
from app.schemas import StudyPackRead, PackPurchaseRead

router = APIRouter(tags=["Study Packs"])


def require_authenticated(current_user: User = Depends(get_current_user)):
    return current_user


# ============================================================
# CATALOGUE PUBLIC
# ============================================================

@router.get("/packs")
def list_published_packs(
    niveau_scolaire: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Catalogue public des packs publiés, filtrable par niveau scolaire.
    Si authentifié, ajoute already_included_by_school pour chaque pack."""
    query = db.query(StudyPack).filter(StudyPack.status == PackStatus.PUBLISHED.value)

    if niveau_scolaire:
        query = query.filter(StudyPack.niveau_scolaire == niveau_scolaire)

    total = query.count()
    packs = query.order_by(StudyPack.created_at.desc()).offset(skip).limit(limit).all()

    # Step 6: Vérifier quels packs sont déjà couverts par l'école de l'utilisateur
    school_pack_niveaux = set()
    if current_user and current_user.school_id:
        now = datetime.now(timezone.utc)
        active_school_packs = db.query(PackPurchase).filter(
            PackPurchase.school_id == current_user.school_id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).join(StudyPack).all()
        school_pack_niveaux = {sp.niveau_scolaire for sp in active_school_packs}

    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "niveau_scolaire": p.niveau_scolaire,
                "matieres": p.matieres,
                "price": p.price,
                "currency": p.currency,
                "validity_duration_days": p.validity_duration_days,
                "owner_type": p.owner_type or "eduai_catalog",
                "already_included_by_school": p.niveau_scolaire in school_pack_niveaux if school_pack_niveaux else False,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in packs
        ],
    }


@router.get("/packs/{pack_id}")
def get_pack_detail(pack_id: int, db: Session = Depends(get_db)):
    """Détail d'un pack publié."""
    pack = db.query(StudyPack).filter(
        StudyPack.id == pack_id,
        StudyPack.status == PackStatus.PUBLISHED.value,
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    # Compter le nombre de cours couverts par ce pack
    course_query = db.query(Course).filter(
        Course.niveau_scolaire == pack.niveau_scolaire,
        Course.is_published == True,
    )
    if pack.matieres:
        course_query = course_query.filter(Course.category.in_(pack.matieres))
    covered_count = course_query.count()

    return {
        "id": pack.id,
        "name": pack.name,
        "description": pack.description,
        "niveau_scolaire": pack.niveau_scolaire,
        "matieres": pack.matieres,
        "price": pack.price,
        "currency": pack.currency,
        "validity_duration_days": pack.validity_duration_days,
        "covered_courses_count": covered_count,
        "created_at": pack.created_at.isoformat() if pack.created_at else None,
    }


# ============================================================
# ACHAT INDIVIDUEL (STUDENT)
# ============================================================

@router.post("/packs/{pack_id}/purchase")
def purchase_pack(
    pack_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_authenticated),
):
    """
    Achat individuel d'un pack par un student.
    Vérifie que le niveau du pack correspond au niveau de l'élève.
    """
    # Vérifier que l'utilisateur est un student
    role = str(user.role.value).lower() if hasattr(user.role, "value") else str(user.role).lower()
    if role != "student":
        raise HTTPException(status_code=403, detail="Seuls les étudiants peuvent acheter un pack individuellement")

    # Vérifier que le pack existe et est publié
    pack = db.query(StudyPack).filter(
        StudyPack.id == pack_id,
        StudyPack.status == PackStatus.PUBLISHED.value,
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found or not published")

    # Vérifier que le niveau du pack correspond au niveau de l'élève
    if not user.niveau_scolaire:
        raise HTTPException(
            status_code=400,
            detail="Votre niveau scolaire n'est pas défini. Veuillez le renseigner dans votre profil."
        )
    if user.niveau_scolaire != pack.niveau_scolaire:
        raise HTTPException(
            status_code=400,
            detail=f"Ce pack est pour le niveau '{pack.niveau_scolaire}', mais votre niveau est '{user.niveau_scolaire}'."
        )

    # Vérifier qu'il n'a pas déjà un pack actif pour ce niveau
    now = datetime.now(timezone.utc)
    existing = db.query(PackPurchase).filter(
        PackPurchase.student_id == user.id,
        PackPurchase.purchaser_type == PurchaserType.STUDENT.value,
        PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
        PackPurchase.valid_until > now,
    ).join(StudyPack).filter(StudyPack.niveau_scolaire == pack.niveau_scolaire).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Vous avez déjà un pack actif pour le niveau '{pack.niveau_scolaire}' (expire le {existing.valid_until.strftime('%d/%m/%Y')})."
        )

    # Step 5: Bloquer l'achat individuel si l'école a déjà un pack actif pour ce niveau
    if user.school_id:
        school_has_pack = db.query(PackPurchase).filter(
            PackPurchase.school_id == user.school_id,
            PackPurchase.purchaser_type == PurchaserType.SCHOOL.value,
            PackPurchase.status == PackPurchaseStatus.ACTIVE.value,
            PackPurchase.valid_until > now,
        ).join(StudyPack).filter(StudyPack.niveau_scolaire == pack.niveau_scolaire).first()

        if school_has_pack:
            raise HTTPException(
                status_code=400,
                detail=f"Votre école dispose déjà d'un pack actif pour le niveau '{pack.niveau_scolaire}' (expire le {school_has_pack.valid_until.strftime('%d/%m/%Y')}). Vous n'avez pas besoin de l'acheter individuellement."
            )

    # Vérifier le solde
    if user.dt_balance < pack.price:
        raise HTTPException(
            status_code=400,
            detail=f"Solde insuffisant. Solde actuel: {user.dt_balance} {pack.currency}, prix du pack: {pack.price} {pack.currency}"
        )

    # Débiter
    user.dt_balance -= pack.price

    # Créer la transaction
    transaction = Transaction(
        school_id=user.school_id or 1,
        user_id=user.id,
        type=TransactionType.COURSE_PURCHASE,
        amount=pack.price,
        currency=Currency.DT,
        description=f"Achat pack: {pack.name}",
        reference_id=f"pack_{pack_id}",
        status="completed",
    )
    db.add(transaction)

    # Créer l'achat de pack
    valid_from = now
    valid_until = now + timedelta(days=pack.validity_duration_days)

    purchase = PackPurchase(
        pack_id=pack_id,
        purchaser_type=PurchaserType.STUDENT.value,
        student_id=user.id,
        school_id=None,
        valid_from=valid_from,
        valid_until=valid_until,
        status=PackPurchaseStatus.ACTIVE.value,
        amount_paid=pack.price,
        currency=pack.currency,
        transaction_id=str(transaction.id),
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    return {
        "id": purchase.id,
        "pack_id": purchase.pack_id,
        "pack_name": pack.name,
        "valid_from": valid_from.isoformat(),
        "valid_until": valid_until.isoformat(),
        "amount_paid": purchase.amount_paid,
        "currency": purchase.currency,
        "remaining_balance": user.dt_balance,
        "message": f"Pack '{pack.name}' acheté avec succès. Accès valide jusqu'au {valid_until.strftime('%d/%m/%Y')}."
    }
