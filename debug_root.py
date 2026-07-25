"""Trace why DANH SÁCH TỔNG THỂ (HC).xlsx is not loaded into the knowledge base."""
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
DATA = Path('backend/knowledge/data')

from knowledge.document_parser import parser as docparser
from knowledge.retriever import retriever, KnowledgeRetriever

# Show what the parser gets from EVERY file ending in .xlsx
print("=== PARSING ALL XLSX ===")
for p in sorted(DATA.iterdir()):
    if p.is_file() and p.suffix == '.xlsx':
        raw = p.name
        try:
            text = docparser.parse_file(str(p))
            print(f"OK  {raw!r}  ->  {len(text):,} chars")
            if text:
                print(f"     head: {text[:120]!r}")
        except Exception as e:
            print(f"ERR {raw!r}  ->  {e}")

print()

# Fresh retriever: no cache
print("=== FRESH RETRIEVER (no cache reuse) ===")
nr = KnowledgeRetriever()
ok = nr.load_knowledge(force_reload=True)

names = sorted(set(s['filename'] for s in nr.document_sources))
print(f"load_knowledge -> {ok}, {len(nr.documents)} chunks, {len(names)} files")

print("\nAll filenames:")
for n in names:
    cnt = sum(1 for s in nr.document_sources if s['filename'] == n)
    print(f"  [{cnt:3d}] {n}")

if nr.has_knowledge():
    q = "can bo uy ban mat tran to quoc viet nam"
    results = nr.search(q, top_k=10, min_similarity=0.001)
    print(f"\nSearch '{q}': {len(results)} results")
    for r in results:
        fn = r['source']['filename']
        sim = r['similarity']
        txt = r['content'][:200]
        print(f"  SIM={sim:.4f}  {fn}")
        print(f"    {txt}")
