# -*- coding: utf-8 -*-
"""
fix_niveaux_scolaires.py - Unify niveau_scolaire to official Tunisian tree.
Idempotent. Tables: users, courses, pack_definitions
"""
import sys, io, os, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import User, Course, PackDefinition

OFFICIAL_SET = {
    "1ère Année Base", "2ème Année Base", "3ème Année Base",
    "4ème Année Base", "5ème Année Base", "6ème Année Base",
    "7ème Année Base", "8ème Année Base", "9ème Année Base",
    "1ère Année Secondaire",
    "2ème Lettres", "2ème Sciences", "2ème Technologie", "2ème Économie et Services",
    "3ème Lettres", "3ème Mathématiques", "3ème Sciences Expérimentales",
    "3ème Économie et Gestion", "3ème Sciences de l'Informatique", "3ème Sciences Techniques",
    "Bac Lettres", "Bac Mathématiques", "Bac Sciences Expérimentales",
    "Bac Économie et Gestion", "Bac Sciences de l'Informatique", "Bac Sciences Techniques",
}

OFFICIAL_NORM = {}
for v in OFFICIAL_SET:
    nfkd = unicodedata.normalize("NFKD", v)
    key = "".join(c for c in nfkd if not unicodedata.combining(c)).strip().lower()
    OFFICIAL_NORM[key] = v

def normalize(val):
    if not val:
        return val
    nfkd = unicodedata.normalize("NFKD", val)
    ascii_val = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_val.strip().lower()

ARABIC_MAP = {
    "سابعة اساسي": "7ème Année Base",
    "ثامنة اساسي": "8ème Année Base",
    "تاسعة اساسي": "9ème Année Base",
}

def resolve(value):
    if not value:
        return None
    if value in OFFICIAL_SET:
        return None
    norm = normalize(value)
    if norm in OFFICIAL_NORM:
        return OFFICIAL_NORM[norm]
    if norm in ARABIC_MAP:
        return ARABIC_MAP[norm]
    return None

db = SessionLocal()
try:
    total_u, total_c, total_p = 0, 0, 0

    users = db.query(User).filter(User.niveau_scolaire.isnot(None)).all()
    for u in users:
        new = resolve(u.niveau_scolaire)
        if new:
            old = u.niveau_scolaire
            u.niveau_scolaire = new
            total_u += 1
            print(f"  USER {u.id} ({u.full_name}): {repr(old)} -> {repr(new)}")

    courses = db.query(Course).filter(Course.niveau_scolaire.isnot(None)).all()
    for c in courses:
        new = resolve(c.niveau_scolaire)
        if new:
            old = c.niveau_scolaire
            c.niveau_scolaire = new
            total_c += 1

    packs = db.query(PackDefinition).filter(PackDefinition.niveau_scolaire.isnot(None)).all()
    for p in packs:
        new = resolve(p.niveau_scolaire)
        if new:
            old = p.niveau_scolaire
            p.niveau_scolaire = new
            total_p += 1

    db.commit()
    print(f"\nDone: {total_u} users, {total_c} courses, {total_p} packs updated.")

    from sqlalchemy import func
    print("\n=== POST-MIGRATION USER NIVEAUX ===")
    for val, cnt in db.query(User.niveau_scolaire, func.count()).filter(User.niveau_scolaire.isnot(None)).group_by(User.niveau_scolaire).order_by(func.count().desc()).all():
        is_off = val in OFFICIAL_SET
        mark = '' if is_off else ' *** NOT OFFICIAL ***'
        print(f"  [{cnt}] {val}{mark}")

    print("\n=== POST-MIGRATION COURSE NIVEAUX (non-official only) ===")
    for val, cnt in db.query(Course.niveau_scolaire, func.count()).filter(Course.niveau_scolaire.isnot(None)).group_by(Course.niveau_scolaire).order_by(func.count().desc()).all():
        is_off = val in OFFICIAL_SET
        if not is_off:
            print(f"  [{cnt}] {val} *** NOT OFFICIAL ***")

finally:
    db.close()
