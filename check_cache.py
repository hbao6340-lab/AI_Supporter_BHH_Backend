import sys
import pickle
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Check the cache file
cache_path = Path('backend/knowledge/.cache/knowledge_cache.pkl')
if cache_path.exists():
    with open(cache_path, 'rb') as f:
        cache = pickle.load(f)
    
    docs = cache.get('documents', [])
    sources = cache.get('sources', [])
    
    print(f'Cache: {len(docs)} chunks, {len(sources)} sources')
    
    # Find XLSX sources
    xlsx_sources = [s for s in sources if s['filename'].endswith('.xlsx')]
    xlsx_names = sorted(set(s['filename'] for s in xlsx_sources))
    print(f'XLSX files in cache: {len(xlsx_names)}')
    for name in xlsx_names:
        count = sum(1 for s in sources if s['filename'] == name)
        print(f'  [{count} chunks] {name}')
        
    # Find TỔNG THỂ chunk
    for i, (doc, src) in enumerate(zip(docs, sources)):
        fn = src['filename']
        if 'HC)' in fn or 'TỔNG' in fn or 'TONG' in fn.upper():
            print(f'\nCHUNK {i} from {fn} (id={src["chunk_id"]}):')
            print(f'  {doc[:200]}')
            break
else:
    print('No cache file found')

# Check the knowledge retriever
sys.path.insert(0, 'backend')
from knowledge.retriever import retriever
print(f'\nRetriever docs: {len(retriever.documents)}')
for src in retriever.document_sources:
    if 'HC)' in src['filename'] or 'TỔNG' in src['filename'] or 'TONG' in src['filename'].upper():
        doc = retriever.documents[retriever.document_sources.index(src)]
        print(f'  FOUND: {src["filename"]} id={src["chunk_id"]} len={len(doc)}')
