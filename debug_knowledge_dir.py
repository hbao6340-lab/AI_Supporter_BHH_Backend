import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

os.chdir(str(Path(__file__).parent.parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

# Load without force reload to check file detection first
retriever2 = __import__('knowledge.retriever', fromlist=['KnowledgeRetriever']).KnowledgeRetriever()

# Check what knowledge directory is being used
print(f'Knowledge dir from retriever: {retriever2.knowledge_dir}')
print(f'Knowledge dir exists: {retriever2.knowledge_dir.exists()}')
print()

# List all files in knowledge dir
for child in sorted(retriever2.knowledge_dir.iterdir()):
    if child.is_file():
        print(f'  {child.name!r} [{child.stat().st_size} bytes]')
