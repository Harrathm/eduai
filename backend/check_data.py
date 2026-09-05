import unicodedata
from app.db import SessionLocal
from app.models import Matiere, NiveauEtude, Course

def _strip_accents(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower().strip()

db = SessionLocal()

# Check matiere IDs from abonnement
for mid in [662, 669]:
    m = db.query(Matiere).filter(Matiere.id == mid).first()
    if m:
        niv = db.query(NiveauEtude).filter(NiveauEtude.id == m.niveau_etude_id).first()
        print(f"  Matiere id={mid} nom='{m.nom}' niveau='{niv.nom if niv else '?'}' (niveau_id={m.niveau_etude_id})")
    else:
        print(f"  Matiere id={mid}: NOT FOUND")

# Check all matieres
print("\nAll matieres:")
all_m = db.query(Matiere).all()
for m in all_m:
    niv = db.query(NiveauEtude).filter(NiveauEtude.id == m.niveau_etude_id).first()
    print(f"  id={m.id} nom='{m.nom}' type={m.type_matiere} niveau='{niv.nom if niv else '?'}'")

# Check all published courses
print("\nAll published courses:")
courses = db.query(Course).filter(Course.status == "published").all()
for c in courses:
    print(f"  id={c.id} title='{c.title}' category='{c.category}' niveau='{c.niveau_scolaire}'")

db.close()
