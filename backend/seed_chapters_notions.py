"""Seed idempotent : peuplement de l'arborescence pédagogique officielle.

Pour chaque Matiere :
  - 3 ChapterPathway génériques (Notions Fondamentales / Approfondissement /
    Évaluation et Synthèse)
  - pour chaque chapitre : 3 Notion génériques (Introduction / Développement /
    Applications)

Idempotent : un chapitre (matiere_id, nom) ou une notion (chapitre_id, nom)
déjà présent n'est pas recréé.

Usage : python seed_chapters_notions.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from app.db import SessionLocal
from app.models import Matiere, ChapterPathway, Notion

CHAPTERS = [
    ("Chapitre 1: Notions Fondamentales", ["Introduction", "Développement", "Applications"]),
    ("Chapitre 2: Approfondissement", ["Introduction", "Développement", "Applications"]),
    ("Chapitre 3: Évaluation et Synthèse", ["Introduction", "Développement", "Applications"]),
]


def main():
    db = SessionLocal()
    try:
        matieres = db.query(Matiere).all()
        print(f"Matières trouvées : {len(matieres)}")

        chapitres_crees = 0
        chapitres_existants = 0
        notions_creees = 0
        notions_existantes = 0

        for matiere in matieres:
            for idx, (nom_chapitre, notions_noms) in enumerate(CHAPTERS, start=1):
                chapitre = (
                    db.query(ChapterPathway)
                    .filter(
                        ChapterPathway.matiere_id == matiere.id,
                        ChapterPathway.nom == nom_chapitre,
                    )
                    .first()
                )
                if chapitre is None:
                    chapitre = ChapterPathway(
                        matiere_id=matiere.id, nom=nom_chapitre, ordre=idx
                    )
                    db.add(chapitre)
                    db.flush()  # obtient chapitre.id avant d'ajouter les notions
                    chapitres_crees += 1
                else:
                    chapitres_existants += 1

                for j, suffixe in enumerate(notions_noms, start=1):
                    nom_notion = f"Notion {idx}.{j}: {suffixe}"
                    exists = (
                        db.query(Notion)
                        .filter(
                            Notion.chapitre_id == chapitre.id,
                            Notion.nom == nom_notion,
                        )
                        .first()
                    )
                    if exists is None:
                        db.add(
                            Notion(
                                chapitre_id=chapitre.id, nom=nom_notion, ordre=j
                            )
                        )
                        notions_creees += 1
                    else:
                        notions_existantes += 1

            # commit par matière : reprise possible après interruption
            db.commit()

        total_chapitres = db.query(ChapterPathway).count()
        total_notions = db.query(Notion).count()

        print(f"\nChapitres créés      : {chapitres_crees}")
        print(f"Chapitres existants  : {chapitres_existants}")
        print(f"Notions créées       : {notions_creees}")
        print(f"Notions existantes   : {notions_existantes}")
        print(f"\nTotaux en base       : {total_chapitres} chapitres, {total_notions} notions")
    finally:
        db.close()


if __name__ == "__main__":
    main()
