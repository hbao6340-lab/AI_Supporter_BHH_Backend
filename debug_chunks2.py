import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

os.chdir(str(Path(__file__).parent.parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

retriever.load_knowledge(force_reload=True)

# Find all chunks from the Excel file
print(f'Total documents: {len(retriever.documents)}')
print(f'Total sources: {len(retriever.document_sources)}')

# Find unique filenames
filenames = set()
for s in retriever.document_sources[:100]:
    filenames.add(s['filename'])

print('\nAll filenames in retriever (first 100 sources):')
for f in sorted(filenames):
    print(f'  {f!r}')

# Also check where the XLSX appears
print('\nSearching for XLSX in ALL sources:')
for i, s in enumerate(retriever.document_sources):
    fn = s['filename']
    if 'DANH' in fn.upper() or 'SÁCH' in fn or 'TỔNG' in fn or 'XLSX' in fn.upper():
        doc = retriever.documents[i]
        print(f'  idx={i} FILE={fn!r} CHUNK={s["chunk_id"]} DOC_LEN={len(doc)}')
        print(f'    First 100 chars: {doc[:100]}')
