#!/usr/bin/env python3
"""Pipeline d'ingestion intelligent du corpus scolaire tunisien vers l'index RAG backend.

- Scan récursif de CORPUS_PATH (défaut: D:\\RAG_APP_new\\Docs\\Documents).
- Filtre les fichiers parasites (.exe, .apk, .crdownload, .zip, temporaires ~$...).
- Extrait niveau_scolaire / matiere depuis l'arborescence des dossiers
  (noms français ET arabes), avec repli optionnel sur le nom de fichier.
- Ingestion via RAGService.ingest_pdf / ingest_text (métadonnées incluses).
- Idempotent : manifeste MD5 dans data/faiss_indexes/_ingest_manifest.json ;
  --reset vide l'index avant réinjection complète.

Usage:
    python ingest_corpus.py                       # ingestion incrémentale
    python ingest_corpus.py --reset               # purge + réindexation totale
    python ingest_corpus.py --dry-run             # simulation sans écriture
    python ingest_corpus.py --school-id 1 --limit 5
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

CORPUS_PATH = Path(os.environ.get("CORPUS_PATH", r"D:\RAG_APP_new\Docs\Documents"))
INDEX_PATH = BACKEND_DIR / "data" / "faiss_indexes"
MANIFEST_FILE = INDEX_PATH / "_ingest_manifest.json"

TEMP_PREFIX = "~$"
IGNORED_EXTENSIONS = {".exe", ".apk", ".crdownload", ".zip", ".mdb", ".part", ".tmp"}
PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx"}

# Répertoires techniques/dérivés jamais parcourus (code, caches, téléchargements)
PRUNE_DIRS = {
    "__pycache__", ".git", "venv", "eduai_env", "node_modules", ".dart_tool",
    "vector_db", "downloads", "extracted_zips", "processed", "raw",
    "generated", "registry", "models", "easyocr", "__MACOSX",
}

# ---------------------------------------------------------------------------
# Dictionnaires de reconnaissance (français + arabe tunisien)
# ---------------------------------------------------------------------------
NIVEAU_ALIASES = {
    # Baccalauréat
    "baccalaureat": "baccalaureat",
    "bac": "baccalaureat",
    "الباكالوريا": "baccalaureat",
    "باكالوريا": "baccalaureat",
    "4eme annee secondaire": "baccalaureat",
    # Enseignement secondaire (1ère → 3ème)
    "1ere annee secondaire": "1ere_secondaire",
    "1ere secondaire": "1ere_secondaire",
    "2eme annee secondaire": "2eme_secondaire",
    "2eme secondaire": "2eme_secondaire",
    "3eme annee secondaire": "3eme_secondaire",
    "3eme secondaire": "3eme_secondaire",
    "الاولى ثانوي": "1ere_secondaire",
    "الثانية ثانوي": "2eme_secondaire",
    "الثالثة ثانوي": "3eme_secondaire",
    # Collège (7ème → 9ème année de base)
    # Formes nues (usage fréquent dans les noms de devoirs tunisiens :
    # « 1ère année » = secondaire, « 4ème » = année du Bac)
    "1ere": "1ere_secondaire",
    "2eme": "2eme_secondaire",
    "3eme": "3eme_secondaire",
    "4eme": "baccalaureat",
    "5eme": "5eme_primary",
    "1ere annee": "1ere_secondaire",
    "2eme annee": "2eme_secondaire",
    "3eme annee": "3eme_secondaire",
    "4eme annee": "baccalaureat",
    "7eme": "7eme_base",
    "7eme annee": "7eme_base",
    "7eme base": "7eme_base",
    "7eme college": "7eme_base",
    "8eme": "8eme_base",
    "8eme annee": "8eme_base",
    "8eme base": "8eme_base",
    "8eme college": "8eme_base",
    "9eme": "9eme_base",
    "9eme annee": "9eme_base",
    "9eme base": "9eme_base",
    "9eme college": "9eme_base",
    "التاسعة اساسي": "9eme_base",
    "تاسعة اساسي": "9eme_base",
    "الثامنة اساسي": "8eme_base",
    "السابعة اساسي": "7eme_base",
    # Noms de dossiers Manuels_scolaires (7_base, 8_base, 9_base)
    # NB : _norm() convertit "7_base" -> "7 base", d'où les variantes espacées.
    "7_base": "7eme_base",
    "8_base": "8eme_base",
    "9_base": "9eme_base",
    "7 base": "7eme_base",
    "8 base": "8eme_base",
    "9 base": "9eme_base",
    # Primaire (1ère → 6ème)
    "6eme": "6eme_base",
    "6eme primaire": "6eme_base",
    "6eme initiation": "6eme_base",
    "السادسة ابتدائي": "6eme_base",
    "سادسة ابتدائي": "6eme_base",
    "الخامسة ابتدائي": "5eme_primary",
    "الرابعة ابتدائي": "4eme_primary",
    "الثالثة ابتدائي": "3eme_primary",
    "الثانية ابتدائي": "2eme_primary",
    "الاولى ابتدائي": "1ere_primary",
}

MATIERE_ALIASES = {
    "mathematiques": "mathematiques",
    "mathematique": "mathematiques",
    "maths": "mathematiques",
    "math": "mathematiques",
    "رياضيات": "mathematiques",
    "svt": "svt",
    "sciences naturelles": "svt",
    "sciences de la vie et de la terre": "svt",
    "sciences": "svt",
    "علوم": "svt",
    "علوم طبيعية": "svt",
    "physique": "physique_chimie",
    "physique chimie": "physique_chimie",
    "physique-chimie": "physique_chimie",
    "chimie": "physique_chimie",
    "فيزياء": "physique_chimie",
    "arabe": "arabe",
    "العربية": "arabe",
    "لغة عربية": "arabe",
    "francais": "francais",
    "français": "francais",
    "anglais": "anglais",
    "english": "anglais",
    "انجليزية": "anglais",
    "informatique": "informatique",
    "infos": "informatique",
    "info": "informatique",
    "إعلامية": "informatique",
    "الاعلامية": "informatique",
    "histoire geographie": "histoire_geographie",
    "histoire": "histoire_geographie",
    "geographie": "histoire_geographie",
    "تاريخ جغرافيا": "histoire_geographie",
    "philosophie": "philosophie",
    "فلسفة": "philosophie",
    "economie": "economie",
    "économie": "economie",
    "اقتصاد": "economie",
    "technologie": "technologie",
    "تكنولوجيا": "technologie",
    "education islamique": "education_islamique",
    "تربية اسلامية": "education_islamique",
    "education technique": "education_technique",
}

STOPWORDS_FICHIERS = {"devoir", "devoirs", "serie", "series", "examen", "examens",
                      "controle", "controles", "correction", "manuel", "manuels",
                      "concours", "documents", "document"}


def _norm(text: str) -> str:
    """Normalise : minuscules, sans accents, séparateurs unifiés."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[_\-]+", " ", text).strip()


def _lookup(mapping: dict, value_norm: str):
    """Recherche exacte puis par sous-chaîne dans un dictionnaire d'alias."""
    if value_norm in mapping:
        return mapping[value_norm]
    for alias, canonical in mapping.items():
        if alias and alias in value_norm:
            return canonical
    return None


def extract_metadata(rel_parts: list[str], filename_stem: str,
                     scan_filenames: bool = True) -> tuple[str | None, str | None]:
    """Extrait (niveau_scolaire, matiere) depuis les dossiers parents,
    puis repli sur le nom de fichier pour les valeurs manquantes."""
    niveau, matiere = None, None
    folder_tokens = [_norm(p) for p in rel_parts]
    file_token = _norm(filename_stem)

    for token in reversed(folder_tokens):          # le dossier le plus profond gagne
        if niveau is None:
            found = _lookup(NIVEAU_ALIASES, token)
            if found:
                niveau = found
        if matiere is None:
            found = _lookup(MATIERE_ALIASES, token)
            if found:
                matiere = found

    if scan_filenames:
        clean = " ".join(w for w in file_token.split() if w not in STOPWORDS_FICHIERS)
        if niveau is None:
            niveau = _lookup(NIVEAU_ALIASES, clean)
        if matiere is None:
            matiere = _lookup(MATIERE_ALIASES, clean)

    return niveau, matiere


def md5_of_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


def extract_docx_text(path: Path) -> str | None:
    """Extraction .docx si une librairie est disponible, sinon None (ignoré proprement)."""
    try:
        import docx2txt  # type: ignore
        try:
            return docx2txt.process(str(path)) or ""
        except Exception:
            return ""  # fichier corrompu / illisible
    except ImportError:
        pass
    try:
        import docx  # type: ignore  # python-docx
        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs)
    except ImportError:
        return None
    except Exception:
        return ""


def main() -> int:
    # Console Windows (charmap) : force UTF-8 sinon tout print arabe/flèche crashe
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass

    parser = argparse.ArgumentParser(description="Ingestion du corpus EDUAI vers l'index RAG backend")
    parser.add_argument("--corpus-path", type=Path, default=CORPUS_PATH,
                        help="Racine du corpus (défaut: $CORPUS_PATH ou D:\\RAG_APP_new\\Docs\\Documents)")
    parser.add_argument("--school-id", type=int, default=1, help="École cible (défaut: 1)")
    parser.add_argument("--index-path", type=Path, default=None,
                        help="Chemin de l'index (défaut: backend/data/faiss_indexes)")
    parser.add_argument("--reset", action="store_true",
                        help="Vider l'index de l'école avant réinjection totale")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulation : liste les actions sans rien écrire")
    parser.add_argument("--no-filename-scan", action="store_true",
                        help="Désactiver la détection métadonnées via nom de fichier")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limiter le nombre de fichiers traités (tests)")
    parser.add_argument("--target-folder", type=Path, default=None,
                        help="Ingestion ciblée : répertoire relatif au corpus (ex: Manuels_scolaires/7_base)")
    args = parser.parse_args()

    global INDEX_PATH, MANIFEST_FILE
    if args.index_path:
        INDEX_PATH = args.index_path
        MANIFEST_FILE = INDEX_PATH / "_ingest_manifest.json"

    corpus_root: Path = args.corpus_path
    if not corpus_root.exists():
        print(f"[ERREUR] Corpus introuvable : {corpus_root}")
        return 2

    from app.ai.rag_service import RAGService

    rag = RAGService(index_path=str(INDEX_PATH))
    if rag.embeddings_service is None:
        print("[ERREUR] EmbeddingsService indisponible (dépendances sklearn manquantes ?)")
        return 2

    stats = {
        "ingestes": 0, "chunks_total": 0, "doublons_skip": 0,
        "parasites_skip": 0, "docx_sans_lib": 0, "vides": 0, "erreurs": 0,
    }
    niveaux_trouves: dict[str, int] = {}
    matieres_trouvees: dict[str, int] = {}

    if args.reset and not args.dry_run:
        rag.embeddings_service.delete_index(args.school_id)
        manifest = {}
        print(f"[RESET] Index school_{args.school_id} purgé.")
    else:
        manifest = load_manifest()

    candidates: list[Path] = []
    # Si --target-folder est défini, on ne scanne que ce sous-dossier
    scan_root = corpus_root
    if args.target_folder:
        scan_root = corpus_root / args.target_folder
        if not scan_root.exists():
            print(f"[ERREUR] Dossier cible introuvable : {scan_root}")
            return 2
        print(f"[TARGET] Scan ciblé : {scan_root}")

    for dirpath, dirnames, filenames in os.walk(scan_root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS and not d.startswith((".","__"))]
        for name in sorted(filenames):
            p = Path(dirpath) / name
            ext = p.suffix.lower()
            if name.startswith(TEMP_PREFIX) or ext in IGNORED_EXTENSIONS or ext == "":
                stats["parasites_skip"] += 1
                continue
            if ext in PDF_EXTENSIONS or ext in DOCX_EXTENSIONS:
                candidates.append(p)
            else:
                stats["parasites_skip"] += 1

    print(f"[SCAN] {len(candidates)} fichiers valides trouvés dans {scan_root}")
    if args.dry_run:
        print("[DRY-RUN] Aucune ingestion ne sera effectuée.\n")

    start = time.time()
    processed = 0
    for path in candidates:
        if args.limit is not None and processed >= args.limit:
            break

        rel_parts = path.relative_to(corpus_root).parts[:-1]
        niveau, matiere = extract_metadata(
            list(rel_parts), path.stem, scan_filenames=not args.no_filename_scan
        )

        try:
            fingerprint = md5_of_file(path)
        except OSError as e:
            print(f"  [ERREUR] lecture {path.name}: {e}")
            stats["erreurs"] += 1
            continue

        key = str(path.relative_to(corpus_root))
        prev = manifest.get(key)
        if (not args.reset) and prev and prev.get("md5") == fingerprint \
                and prev.get("school_id") == args.school_id:
            stats["doublons_skip"] += 1
            continue

        rel_display = " / ".join(path.relative_to(corpus_root).parts)
        tag = f"niveau={niveau or '—'} matiere={matiere or '—'}"

        if args.dry_run:
            print(f"  [WOULD INGEST] {rel_display} ({tag})")
            processed += 1
            continue

        try:
            ext = path.suffix.lower()
            if ext in PDF_EXTENSIONS:
                result = rag.ingest_pdf(
                    args.school_id, str(path),
                    niveau_scolaire=niveau, matiere=matiere,
                )
            else:  # .docx
                text = extract_docx_text(path)
                if text is None:
                    stats["docx_sans_lib"] += 1
                    print(f"  [SKIP DOCX] librairie absente (pip install docx2txt) : {rel_display}")
                    continue
                if not text.strip():
                    stats["vides"] += 1
                    print(f"  [VIDE DOCX] aucun texte extrait (images/scan ?) : {rel_display}")
                    continue
                result = rag.ingest_text(
                    args.school_id, text, source=path.name,
                    niveau_scolaire=niveau, matiere=matiere,
                )

            chunks = result.get("chunks_added", 0)
            if chunks == 0:
                stats["vides"] += 1
                print(f"  [VIDE] 0 chunk extrait (PDF scanné ?) : {rel_display}")
            else:
                stats["ingestes"] += 1
                stats["chunks_total"] += chunks
                print(f"  [OK] {rel_display} ({tag}) -> {chunks} chunks")

            manifest[key] = {
                "md5": fingerprint, "size": path.stat().st_size,
                "school_id": args.school_id, "chunks_added": chunks,
                "niveau_scolaire": niveau, "matiere": matiere,
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            if niveau:
                niveaux_trouves[niveau] = niveaux_trouves.get(niveau, 0) + 1
            if matiere:
                matieres_trouvees[matiere] = matieres_trouvees.get(matiere, 0) + 1

        except Exception as e:
            print(f"  [ERREUR] {rel_display}: {type(e).__name__}: {e}")
            stats["erreurs"] += 1

        processed += 1

    if not args.dry_run:
        save_manifest(manifest)

    total_docs = rag.embeddings_service.get_stats(args.school_id)
    elapsed = time.time() - start
    print("\n========== RAPPORT D'INGESTION ==========")
    print(f"Corpus           : {corpus_root}")
    print(f"Fichiers valides : {len(candidates)} | traités : {processed}")
    print(f"Ingestés         : {stats['ingestes']} ({stats['chunks_total']} chunks)")
    print(f"Doublons skippés : {stats['doublons_skip']}")
    print(f"Parasites filtrés: {stats['parasites_skip']}")
    print(f"Vides (0 chunk)  : {stats['vides']} | DOCX sans lib : {stats['docx_sans_lib']} | Erreurs : {stats['erreurs']}")
    print(f"Index school_{args.school_id} : {total_docs.get('indexed_docs', 0)} chunks au total")
    print(f"Niveaux détectés : {json.dumps(niveaux_trouves, ensure_ascii=False)}")
    print(f"Matières détectées: {json.dumps(matieres_trouvees, ensure_ascii=False)}")
    print(f"Durée : {elapsed:.1f}s")
    return 0 if stats["erreurs"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
