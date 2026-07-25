"""Find where "V. CŨ QUAN ỦY BAN MẶT TRẬN" appears in the Excel content."""
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')

from knowledge.document_parser import parser as docparser
from knowledge.retriever import KnowledgeRetriever
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

DATA = Path('backend/knowledge/data')
parsed = docparser.parse_directory(str(DATA))
xlsx_doc = [d for d in parsed if 'TỔNG THỂ' in d['filename']][0]
print(f"File: {xlsx_doc['filename']}, content len: {len(xlsx_doc['content'])}")
content = xlsx_doc['content']

# Find position of "V. CŨ QUAN" or "V. C╞á QUAN"
for pattern in ['V. C', 'C╞á QUAN', 'CŨ QUAN', 'C컛 QUAN', 'C├í QUAN']:
    pos = content.find(pattern)
    if pos >= 0:
        print(f"Found '{pattern}' at position {pos}")
        print(f"Context: {content[max(0,pos-50):pos+200]}")
        print()

# Find specific staff names
for name in ['Phß║ím Thß╗ï Hß║ính T', 'Kh╞░u Thi├¬n', 'L├¬ ─Éß╗⌐c']:
    pos = content.find(name)
    if pos >= 0:
        print(f"Found '{name}' at position {pos}")
        print(f"Context: {content[max(0,pos-100):pos+100]}")
        print()

# Now chunk and find Excel chunks
r = KnowledgeRetriever()
chunks = r._chunk_text(content, chunk_size=500, overlap=50)
print(f"Total chunks: {len(chunks)}")

# Find chunks around position 3100 (V. section start)
for i, chunk in enumerate(chunks):
    if 'C' in chunk and ('QUAN' in chunk or 'quan' in chunk.lower()):
        cumlen = sum(len(c) for c in chunks[:i])
        print(f"\nChunk {i} (pos ~{cumlen}), len={len(chunk)}:")
        print(chunk[:300])
        print("...")
        print(chunk[-200:])
