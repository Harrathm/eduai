import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# school_1.json
with open('data/faiss_indexes/school_1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== school_1.json ===")
print("Total chunks:", len(data))
for i in range(min(3, len(data))):
    meta = data[i].get('metadata', {})
    content = data[i].get('page_content', '')
    ns = meta.get('niveau_scolaire', 'MISSING')
    mat = meta.get('matiere', 'MISSING')
    src = meta.get('source', 'UNKNOWN')
    print(f"Chunk {i}: niveau={ns}, matiere={mat}")
    print(f"  source={src[:80]}")
    print(f"  content[:80]={content[:80]}")

# Manifest
with open('data/faiss_indexes/_ingest_manifest.json', 'r', encoding='utf-8') as f:
    manifest = json.load(f)
print(f"\n=== Manifest: {len(manifest)} entries ===")
seven_base_entries = {k: v for k, v in manifest.items() if '7_base' in str(k)}
print(f"7_base entries: {len(seven_base_entries)}")
for k, v in list(seven_base_entries.items())[:3]:
    print(f"  {k}: {v}")

# Check if the 7_base PDF exists
pdf_path = os.path.join('..', 'Docs', 'Documents', 'Manuels_scolaires', '7_base', 'eleve', '\u0639\u0644\u0648\u0645_\u0627\u0644\u062d\u064a\u0627\u0629_\u0648\u0627\u0644\u0623\u0631\u0636.pdf')
print(f"\n7_base PDF exists: {os.path.exists(pdf_path)}")

# Check ingest output
ingest_output = os.path.join('..', 'ingest_output.txt')
if os.path.exists(ingest_output):
    with open(ingest_output, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"\n=== Ingest output: {len(lines)} lines ===")
    for line in lines[-20:]:
        print(line.rstrip())
