"""Full trace of doc parsing and index building."""
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).parent.parent
DATA = ROOT / 'backend' / 'knowledge' / 'data'
sys.path.insert(0, str(ROOT))

from knowledge.document_parser import parser as docparser
from knowledge.retriever import KnowledgeRetriever

# 1. How many files does the scanner find on disk?
scanned = [p for p in sorted(DATA.rglob('*'))
           if p.is_file()
           and p.suffix.lower() in docparser.SUPPORTED_EXTENSIONS
           and not ('readme' in p.name.lower())
           and not p.name.startswith('~$')]
print(f"Files the scanner iterates over: {len(scanned)}")
for p in scanned:
    print(f"  {p.name!r}")

print()

# 2. What does parse_directory return?
parsed = docparser.parse_directory(str(DATA))
print(f"parse_directory returns: {len(parsed)} files")
for d in parsed:
    print(f"  [{len(d['content']):6,]}]  {d['filename']}")

print()

# 3. Build the retriever exactly like the real code does
r = KnowledgeRetriever()
print(f"knowledge_dir used: {r.knowledge_dir}")
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

from collections import Counter
fn_counts = Counter(s['filename'] for s in r.document_sources)
print(f"After chunking: {len(r.documents)} chunks, {len(fn_counts)} files")
for fn, cnt in sorted(fn_counts.items()):
    print(f"  [{cnt:3d}] {fn}")
