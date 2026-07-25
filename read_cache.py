"""Trace WHY some files are not in the knowledge base after force reload."""
from pathlib import Path
import sys, pickle

sys.stdout.reconfigure(encoding='utf-8')

# Load cache directly to inspect
cache_path = Path('backend/knowledge/.cache/knowledge_cache.pkl')
print(f"Cache exists: {cache_path.exists()}")

if cache_path.exists():
    with open(cache_path, 'rb') as f:
        cache = pickle.load(f)
    docs = cache.get('documents', [])
    sources = cache.get('sources', [])
    print(f"Cache: {len(docs)} chunks, {len(sources)} sources")
    
    # Unique filenames
    from collections import Counter
    fn_counts = Counter(s['filename'] for s in sources)
    print(f"Unique filenames: {len(fn_counts)}")
    for fn, cnt in sorted(fn_counts.items()):
        print(f"  [{cnt:3d}] {fn}")
