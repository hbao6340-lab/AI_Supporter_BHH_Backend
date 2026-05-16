import sys
import os
import pickle
from pathlib import Path

# Use absolute paths
BASE_DIR = Path(__file__).parent.parent  # vn_testing root
sys.path.insert(0, str(BASE_DIR / 'backend'))
os.chdir(str(BASE_DIR))

sys.stdout.reconfigure(encoding='utf-8')

from knowledge.retriever import retriever

# Force reload
retriever.load_knowledge(force_reload=True)
print(f'Loaded docs: {len(retriever.documents)}')
print(f'Has knowledge: {retriever.has_knowledge()}')

# Search
query = 'cán bộ CƠ QUAN ỦY BAN MẶT TRẬN TỔ QUỐC VIỆT NAM'
print(f'\nQUERY: {query}')
print(f'min_similarity for get_answer_context: 0.005')

results = retriever.search(query, top_k=5, min_similarity=0.005)
print(f'Results: {len(results)}')
for r in results:
    print(f'  SIM={r["similarity"]:.4f} FILE={r["source"]["filename"]}')
    print(f'  TEXT={r["content"][:200]}')
    print()

ctx, found = retriever.get_answer_context(query, max_chars=5000)
print(f'FOUND: {found}')
print(f'CTX LEN: {len(ctx)}')
