"""Run full_trace again and save output."""
from pathlib import Path
import sys, pickle, os
from collections import Counter

os.chdir(str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA = Path('backend/knowledge/data')

from knowledge.document_parser import parser as docparser
from knowledge.retriever import KnowledgeRetriever

# 1. scan
scanned = [p for p in sorted(DATA.rglob('*'))
           if p.is_file()
           and p.suffix.lower() in ['.txt','.pdf','.docx','.xlsx','']
           and 'readme' not in p.name.lower()
           and not p.name.startswith('~$')]
print(f"Scanned files: {len(scanned)}")
for p in scanned:
    print(f"  {p.name}")

print()

# 2. parse
parsed = docparser.parse_directory(str(DATA))
print(f"Parsed files: {len(parsed)}")
for d in parsed:
    print(f"  [{len(d['content']):>6,}]  {d['filename']}")
    if 'TỔNG' in d['filename'] or 'HC)' in d['filename']:
        print(f"     !! TỔNG THỀ content preview: {d['content'][:200]}")

print()

# 3. chunk & index
r = KnowledgeRetriever()
r.documents = []
r.document_sources = []
for doc in parsed:
    chunks = r._chunk_text(doc['content'], chunk_size=500, overlap=50)
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            r.documents.append(chunk)
            r.document_sources.append({
                'filename': doc['filename'],
                'chunk_id': i,
                'filepath': doc['filepath']
            })

fn_counts = Counter(s['filename'] for s in r.document_sources)
print(f"Total chunks: {len(r.documents)}, Unique files: {len(fn_counts)}")
for fn, cnt in sorted(fn_counts.items()):
    print(f"  [{cnt:3d}] {fn}")

# 4. build TF-IDF
if r.documents:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    r.vectorizer = TfidfVectorizer(
        lowercase=True, stop_words=None,
        ngram_range=(1, 2), max_features=10000, min_df=1
    )
    r.tfidf_matrix = r.vectorizer.fit_transform(r.documents)

    # 5. search - PROPERLY
if r.documents:
    import re
    q = "can bo co quan uy ban mat tran to quoc viet nam"
    
    # Test both search paths
    r_tfidf = r.search(q, top_k=20, min_similarity=0.001)  # uses TF-IDF or fallback
    
    # Also test pure _simple_search explicitly
    r_simple = r._simple_search(q, top_k=20, min_similarity=0.001)
    
    print(f"\nTF-IDF search: {len(r_tfidf)} results")
    for rs in r_tfidf[:15]:
        fn = rs['source']['filename']
        sim = rs['similarity']
        txt = rs['content'][:200]
        print(f"  SIM={sim:.4f}  {fn}  |  {txt}")

    print(f"\nSimple search: {len(r_simple)} results")  
    for rs in r_simple[:15]:
        fn = rs['source']['filename']
        sim = rs['similarity']
        txt = rs['content'][:200]
        print(f"  SIM={sim:.4f}  {fn}  |  {txt}")

    # Find XLSX chunks specifically
    print("\n=== XLSX chunks in top-15 results ===")
    for rs in r_tfidf[:15]:
        if 'TỔNG THỂ' in rs['source']['filename'] or 'HC)' in rs['source']['filename']:
            print(f"  XLSX FOUND: SIM={rs['similarity']:.4f}  CHUNK_ID={rs['source']['chunk_id']}")
            print(f"    {rs['content'][:200]}")
    for rs in r_simple[:15]:
        if 'TỔNG THỂ' in rs['source']['filename'] or 'HC)' in rs['source']['filename']:
            print(f"  XLSX FOUND (simple): SIM={rs['similarity']:.4f}  CHUNK_ID={rs['source']['chunk_id']}")
            print(f"    {rs['content'][:200]}")
