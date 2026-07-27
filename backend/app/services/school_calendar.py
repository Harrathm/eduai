"""
Calendrier scolaire tunisien — utilitaires pour calculer les périodes.
Le calendrier officiel tunisien suit 3 trimestres :
  - Trimestre 1 : ~mi-septembre à mi-décembre
  - Trimestre 2 : ~janvier à mars
  - Trimestre 3 : ~avril à mi-juin

ATTENTION : Les dates exactes varient chaque année scolaire.
Ces dates par défaut doivent être ajustées selon le bulletin officiel du Ministère
de l'Éducation nationale tunisien pour l'année scolaire en cours.
"""
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class TrimesterInfo:
    number: int  # 1, 2 ou 3
    start: date
    end: date
    school_year_start: date
    school_year_end: date


# ============================================================
# DATES PAR DÉFAUT — Calendrier scolaire tunisien 2025-2026
# Source : bulletin officiel Ministère de l'Éducation nationale
# ============================================================

SCHOOL_YEAR_START = date(2025, 9, 15)
SCHOOL_YEAR_END = date(2026, 6, 19)

# Trimestre 1 : 15 septembre – 19 décembre
TRIMESTER_1_START = date(2025, 9, 15)
TRIMESTER_1_END = date(2025, 12, 19)

# Trimestre 2 : 5 janvier – 27 mars
TRIMESTER_2_START = date(2026, 1, 5)
TRIMESTER_2_END = date(2026, 3, 27)

# Trimestre 3 : 6 avril – 19 juin
TRIMESTER_3_START = date(2026, 4, 6)
TRIMESTER_3_END = date(2026, 6, 19)

TRIMESTERS = [
    (1, TRIMESTER_1_START, TRIMESTER_1_END),
    (2, TRIMESTER_2_START, TRIMESTER_2_END),
    (3, TRIMESTER_3_START, TRIMESTER_3_END),
]


def get_current_trimester(ref_date: Optional[date] = None) -> Optional[TrimesterInfo]:
    """
    Retourne le trimestre actuel (1, 2 ou 3) et ses dates.
    Retourne None si on est en dehors des trimestres (vacances, été).
    """
    d = ref_date or date.today()
    for num, start, end in TRIMESTERS:
        if start <= d <= end:
            return TrimesterInfo(
                number=num,
                start=start,
                end=end,
                school_year_start=SCHOOL_YEAR_START,
                school_year_end=SCHOOL_YEAR_END,
            )
    return None


def get_current_school_year(ref_date: Optional[date] = None) -> dict:
    """Retourne les dates de début/fin de l'année scolaire en cours."""
    d = ref_date or date.today()
    return {
        "start": SCHOOL_YEAR_START,
        "end": SCHOOL_YEAR_END,
        "label": f"{SCHOOL_YEAR_START.year}-{SCHOOL_YEAR_END.year}",
    }


def get_period_for_horizon(horizon: str, ref_date: Optional[date] = None) -> tuple[date, date]:
    """
    Calcule period_start et period_end pour un horizon donné.
    Utilisé pour initialiser les LearningGoal.
    """
    d = ref_date or date.today()

    if horizon == "daily":
        return d, d

    if horizon == "weekly":
        # Semaine : lundi à dimanche
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    if horizon == "monthly":
        start = d.replace(day=1)
        if d.month == 12:
            end = d.replace(day=31)
        else:
            end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
        return start, end

    if horizon == "quarterly":
        tri = get_current_trimester(d)
        if tri:
            return tri.start, tri.end
        # Hors trimestre : retourner le trimestre le plus proche
        for num, start, end in TRIMESTERS:
            if d < start:
                return start, end
        return TRIMESTER_3_START, TRIMESTER_3_END

    if horizon == "annual":
        return SCHOOL_YEAR_START, SCHOOL_YEAR_END

    raise ValueError(f"Horizon inconnu : {horizon}")
