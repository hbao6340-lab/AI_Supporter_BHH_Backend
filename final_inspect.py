"""Inspect cache and retriever state."""
from pathlib import Path
import sys, pickle, os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Inspect cache file
cache_path = Path('backend/knowledge/.cache/knowledge_cache.pkl')
if cache_path.exists():
    with open(cache_path, 'rb') as f:
        cache = pickle.load(f)
    sources = cache.get('sources', [])
    from collections import Counter
    fn_counts = Counter(s['filename'] for s in sources)
    print(f"CACHE: {len(sources)} sources, {len(fn_counts)} unique filenames")
    for fn, cnt in sorted(fn_counts.items()):
        print(f"  [{cnt:3d}] {fn}")

print()

# Now check fresh retriever
from knowledge.retriever import KnowledgeRetriever
nr = KnowledgeRetriever()
nr.load_knowledge(force_reload=True)
filenames = sorted(set(s['filename'] for s in nr.document_sources))
print(f"RETRIEVER: {len(nr.documents)} docs, {len(filenames)} unique filenames")
for fn in filenames:
    cnt = sum(1 for s in nr.document_sources if s['filename'] == fn)
    print(f"  [{cnt:3d}] {fn}")
