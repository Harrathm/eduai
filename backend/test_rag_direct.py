#!/usr/bin/env python3
"""Script de diagnostic direct du RAG — contourne l'API web.

Lance :  python test_rag_direct.py [query] [school_id]
         python test_rag_direct.py  (requête par défaut, school_id=1)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def truncate(text: str, length: int = 200) -> str:
    return text[:length].replace("\n", " ")


def main():
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "اريد درس مكونات الوسط البيئي علوم الحياة والارض سنة سابعة اساسي"
    )
    school_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    index_path = str(Path(__file__).parent / "data" / "faiss_indexes")

    print("=" * 72)
    print("  DIAGNOSTIC DIRECT DU RAG")
    print("=" * 72)
    print(f"  Query      : {query}")
    print(f"  School ID  : {school_id}")
    print(f"  Index path : {index_path}")
    print()

    # ------------------------------------------------------------------
    # 1. Initialisation
    # ------------------------------------------------------------------
    from app.ai.embeddings_service import EmbeddingsService

    print("[1] Initialisation EmbeddingsService...")
    svc = EmbeddingsService(index_path=index_path)
    print(f"    Index path OK : {svc.index_path}")

    raw = svc._load_docs(school_id)
    if not raw:
        print(f"    [ERREUR] Aucun index pour school_id={school_id}")
        print(f"    Fichier attendu : {index_path}/school_{school_id}.json")
        sys.exit(1)

    n_total = len(raw)
    n_with_emb = sum(1 for d in raw if "embedding" in d)
    n_with_fallback = sum(
        1 for d in raw if (d.get("metadata") or {}).get("_fallback")
    )
    npy_file = Path(index_path) / f"school_{school_id}_embeddings.npy"
    npy_exists = npy_file.exists()
    if npy_exists:
        npy_size_mb = round(npy_file.stat().st_size / (1024 * 1024), 1)
        print(f"    .npy embeddings : present ({npy_size_mb} Mo)")
    else:
        print(f"    .npy embeddings : ABSENT")
    print(f"    Chunks charges  : {n_total}")
    print(f"    Embed in json   : {n_with_emb} (les vecteurs vivent dans le .npy)")
    print(f"    Avec _fallback  : {n_with_fallback}")
    print()

    # ------------------------------------------------------------------
    # 2. similarity_search (brute, avant _is_relevant)
    # ------------------------------------------------------------------
    print("[2] similarity_search (k=15, sans filtre de pertinence)...")
    raw_results = svc.similarity_search(school_id, query, k=15)
    print(f"    Chunks retournes : {len(raw_results)}")
    print()

    if raw_results:
        for i, doc in enumerate(raw_results, 1):
            m = doc.metadata or {}
            print(f"    [RAW {i}] sem={m.get('_semantic_score', '?')}"
                  f"  lex={m.get('_lexical_score', '?')}"
                  f"  fallback={m.get('_fallback', False)}")
            print(f"           source={m.get('source', '?')}"
                  f"  niveau={m.get('niveau_scolaire', '?')}"
                  f"  matiere={m.get('matiere', '?')}")
            print(f"           text : {truncate(doc.page_content)}")
            print()
    else:
        print("    Aucun chunk brut — similarity_search a echoue.")
        print()

    # ------------------------------------------------------------------
    # 3. retrieve_with_sources (filtre _is_relevant + rerank)
    # ------------------------------------------------------------------
    from app.ai.rag_service import RAGService

    print("[3] retrieve_with_sources (filtre _is_relevant + rerank)...")
    rag = RAGService(index_path=index_path)
    result = rag.retrieve_with_sources(school_id, query, k=5)
    sources = result.get("sources", [])
    contexts = result.get("contexts", [])
    n_sources = len(sources)
    print(f"    Chunks post-filtre : {n_sources}")
    print()

    if sources:
        for i, (src, ctx) in enumerate(zip(sources, contexts), 1):
            print(f"    [FILTERED {i}]")
            print(f"      file            = {src.get('file', '?')}")
            print(f"      chunk_index     = {src.get('chunk_index', '?')}")
            print(f"      niveau_scolaire = {src.get('niveau_scolaire', '?')}")
            print(f"      matiere         = {src.get('matiere', '?')}")
            print(f"      text (200c)     : {truncate(ctx)}")
            print()
    else:
        print("    Aucun chunk apres filtrage.")
        print()

    # ------------------------------------------------------------------
    # 4. Diagnostic si 0 contexte
    # ------------------------------------------------------------------
    if not sources:
        print("=" * 72)
        print("  DIAGNOSTIC")
        print("=" * 72)
        print()
        print("  Le RAG ne retourne aucun chunk.")
        print()
        print("  Causes possibles :")
        if n_with_emb == 0 and not npy_exists:
            print("    - Aucun embedding (ni .npy ni json) — index pas vectorises")
        if n_with_fallback > 0:
            print("    - Des chunks avec _fallback sont presents")
            print("      → _has_lexical_overlap a rejete tous les chunks")
            print("      → les mots de la requete ne sont pas dans les chunks")
        if not raw_results:
            print("    - similarity_search a echoue (torch + sklearn absents ?)")
            print("    - Le fallback Jaccard a ete declenche")
        print()
        sys.exit(1)
    else:
        print("=" * 72)
        print("  RESULTAT : RAG fonctionne —", n_sources, "chunks fournis au Tuteur")
        print("=" * 72)
        sys.exit(0)


if __name__ == "__main__":
    main()
