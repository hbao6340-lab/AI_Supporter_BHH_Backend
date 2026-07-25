import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

os.chdir(str(Path(__file__).parent.parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

retriever.load_knowledge(force_reload=True)

# Get all unique filenames from document_sources
filenames = sorted(set(s['filename'] for s in retriever.document_sources))
print(f'Total unique filenames: {len(filenames)}')
print()
for fn in filenames:
    # Count chunks
    chunk_count = sum(1 for s in retriever.document_sources if s['filename'] == fn)
    print(f'[{chunk_count:3d}] {fn}')
