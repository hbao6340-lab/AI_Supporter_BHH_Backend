"""Directly test search correctness on DANH SÁCH chunks."""
from pathlib import Path
import sys, re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')
from knowledge.document_parser import parser as docparser
from knowledge.retriever import KnowledgeRetriever

DATA = Path('backend/knowledge/data')
parsed = docparser.parse_directory(str(DATA))
xlsx_doc = [d for d in parsed if 'TỔNG THỂ' in d['filename'] or 'HC)' in d['filename']]
if not xlsx_doc:
    print("TỔNG THỂ XLSX not found!")
    # Show all filenames
    for d in parsed:
        print(f"  Available: {d['filename']}")
    exit(1)
    
xlsx_doc = xlsx_doc[0]
content = xlsx_doc['content']
print(f"File: {xlsx_doc['filename']}, len: {len(content)}")
print()

r = KnowledgeRetriever()
chunks = r._chunk_text(content, chunk_size=500, overlap=50)
print(f"Chunks: {len(chunks)}")

# Simulate simple search on query
query = "can bo co quan uy ban mat tran to quoc viet nam"
query_lower = query.lower()
query_words = set(re.findall(r'\w+', query_lower))
print(f"Query tokens: {query_words}")
print()

# Search each chunk manually
results = []
for i, chunk in enumerate(chunks):
    chunk_lower = chunk.lower()
    chunk_words = set(re.findall(r'\w+', chunk_lower))
    matches = query_words & chunk_words
    if matches:
        score = len(matches) / max(len(query_words), len(chunk_words))
        results.append((score, i, chunk, matches))
        
results.sort(reverse=True)
print(f"Chunks with overlap: {len(results)}")
for score, idx, chunk, matches in results[:20]:
    print(f"\n  Chunk {idx} (score={score:.4f}, matches={matches})")
    print(f"  Content: {chunk[:200]}")
    print(f"  ...{chunk[-150:]}")
