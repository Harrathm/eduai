"""
Règles de transition de statut pédagogique des cours.
UNIQUE source de vérité — appelé par TOUS les endpoints qui modifient pedagogical_status.
"""
from fastapi import HTTPException
from app.deps import get_user_role, check_school_access


# Matrice des transitions autorisées : (statut_courant, nouveau_statut) -> validateur
# Clé: (from_status, to_status), Valeur: callable(course, user) -> bool
TRANSITIONS = {
    ("draft", "pending_review"): "_check_author",
    ("pending_review", "approved_local"): "_check_pedagogical_lead",
    ("pending_review", "approved_for_b2b"): "_check_pedagogical_admin_only",
    ("pending_review", "needs_revision"): "_check_pedagogical_reviewer",
    ("needs_revision", "pending_review"): "_check_author",
    ("approved_local", "approved_for_b2b"): "_check_pedagogical_admin_only",
    ("approved_local", "archived"): "_check_archival",
    ("approved_for_b2b", "archived"): "_check_archival",
    ("draft", "archived"): "_check_archival",
    ("pending_review", "archived"): "_check_archival",
    ("needs_revision", "archived"): "_check_archival",
}


def _check_author(course, current_user):
    """Seul l'auteur du cours peut soumettre pour review."""
    return course.author_id == current_user.id


def _check_pedagogical_lead(course, current_user):
    """pedagogical_lead de la MÊME école, UNIQUEMENT pour owner_type='school'."""
    role = get_user_role(current_user)
    if role != "pedagogical_lead":
        return False
    if course.owner_type != "school":
        return False
    check_school_access(current_user, course.school_id)
    return True


def _check_pedagogical_reviewer(course, current_user):
    """pedagogical_lead (même école) OU pedagogical_admin (partout)."""
    role = get_user_role(current_user)
    if role == "pedagogical_admin":
        return True
    if role == "pedagogical_lead":
        if course.owner_type != "school":
            return False
        check_school_access(current_user, course.school_id)
        return True
    return False


def _check_pedagogical_admin_only(course, current_user):
    """UNIQUEMENT pedagogical_admin. JAMAIS pedagogical_lead."""
    role = get_user_role(current_user)
    if role != "pedagogical_admin":
        raise HTTPException(
            status_code=403,
            detail="Seul un resp. pédagogique (plateforme) peut approuver un cours pour la distribution B2B inter-écoles."
        )
    return True


def _check_archival(course, current_user):
    """pedagogical_admin, super_admin, ou l'auteur si le cours n'a jamais été B2B."""
    role = get_user_role(current_user)
    if role in ("pedagogical_admin", "super_admin"):
        return True
    # L'auteur peut archiver si le cours n'a jamais été approuvé pour B2B
    if course.author_id == current_user.id:
        if course.pedagogical_status != "approved_for_b2b":
            return True
    return False


def can_transition_status(course, new_status, current_user):
    """
    Vérifie si la transition de statut est autorisée.
    Lève HTTPException 403 si non autorisée.
    Retourne True si autorisée.
    """
    current_status = course.pedagogical_status or "draft"
    key = (current_status, new_status)

    if key not in TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Transition invalide: {current_status} -> {new_status}"
        )

    checker_name = TRANSITIONS[key]
    checker = globals()[checker_name]

    if not checker(course, current_user):
        raise HTTPException(
            status_code=403,
            detail=f"Vous n'avez pas les droits pour effectuer la transition {current_status} -> {new_status}"
        )

    return True
