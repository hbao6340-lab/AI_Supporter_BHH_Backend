import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

os.chdir(str(Path(__file__).parent.parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

retriever.load_knowledge(force_reload=True)
filenames = sorted(set(s['filename'] for s in retriever.document_sources))
print(f'Total unique filenames in DB: {len(filenames)}')

# Look for TỔNG THỂ
for fn in filenames:
    if 'TỔNG' in fn or 'TONG' in fn.upper() or 'Tß╗öNG' in fn or 'DANH S' in fn:
        print(f'MATCH: {fn!r}')
    if 'HC)' in fn or '.HC' in fn:
        print(f'MATCH HC: {fn!r}')
        
print('\nFull list:')        
for fn in filenames:
    print(f'  {fn}')
