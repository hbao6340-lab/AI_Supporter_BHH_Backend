import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

# Parse
project_root = Path(__file__).parent.parent
knowledge_dir = project_root / 'backend' / 'knowledge' / 'data'
docs = parser.parse_directory(str(knowledge_dir))
print(f'Total files: {len(docs)}')

# Find the xlsx file
for d in docs:
    if 'DANH SÁCH TỔNG THỂ (HC)' in d['filename'] or 'DANH SACH TONG THE' in d['filename'].upper():
        print(f"\nFILE: {d['filename']}")
        print(f"SIZE: {len(d['content'])}")
        # Print ALL content to see what the full text looks like
        print(d['content'])
        print("---END---")
