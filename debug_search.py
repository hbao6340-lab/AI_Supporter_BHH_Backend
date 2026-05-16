import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

# Force reload
retriever.load_knowledge(force_reload=True)

query = "cán bộ CƠ QUAN ỦY BAN MẶT TRẬN TỔ QUỐC VIỆT NAM"
print(f"\nQUERY: {query}", flush=True)

ctx, found = retriever.get_answer_context(query, max_chars=5000)
print(f"FOUND: {found}", flush=True)
print(f"CTX LENGTH: {len(ctx)}", flush=True)
print(f"CONTENT:\n{ctx}", flush=True)

# Also try search
results = retriever.search(query, top_k=5, min_similarity=0.005)
print(f"\nSEARCH RESULTS: {len(results)}", flush=True)
for r in results:
    print(f"  SIM={r['similarity']:.4f} SOURCE={r['source']['filename']}", flush=True)
    print(f"  CONTENT (first 200): {r['content'][:200]}", flush=True)
    print()
