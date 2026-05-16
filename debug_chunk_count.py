"""Trace WHY some files are not in the knowledge base after force reload."""
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
DATA = Path('backend/knowledge/data')

# Add parent to path so "knowledge.xxx" imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# fresh retriever
from knowledge.retriever import KnowledgeRetriever
from knowledge.document_parser import parser as docparser

nr = KnowledgeRetriever()
print(f"knowledge_dir: {nr.knowledge_dir}")
print(f"Exists: {nr.knowledge_dir.exists()}")
print()

# Parse directory manually
print("=== MANUAL PARSE ===")
parsed = docparser.parse_directory(str(nr.knowledge_dir))
parsed_map = {d['filename']: d for d in parsed}
print(f"Parser returned {len(parsed)} files")
for d in parsed:
    print(f"  [{len(d['content']):6,}] {d['filename']}")
print()

# Now run _chunk_text for each and count resulting chunks
print("=== CHUNK COUNT ===")
for d in parsed:
    chunks = nr._chunk_text(d['content'], chunk_size=500, overlap=50)
    print(f"  [{len(chunks):3d}] {d['filename']}")
 
