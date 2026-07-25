import sys
import os
from pathlib import Path

print(f"CWD: {Path.cwd()}", flush=True)
print(f"__file__: {__file__}", flush=True)

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.document_parser import parser

# Parse from the correct path
project_root = Path(__file__).parent.parent
knowledge_dir = project_root / 'backend' / 'knowledge' / 'data'
print(f"Knowledge dir: {knowledge_dir}", flush=True)
print(f"Knowledge dir exists: {knowledge_dir.exists()}", flush=True)

docs = parser.parse_directory(str(knowledge_dir))
print(f'Total files parsed: {len(docs)}')
sys.stdout.reconfigure(encoding='utf-8')

for d in docs:
    print(f"\nFILE: {d['filename']}", flush=True)
    print(f"SIZE: {len(d['content'])}", flush=True)
    print(f"FIRST 500: {d['content'][:500]}", flush=True)
    print("---", flush=True)
