"""Direct token overlap test on Excel chunks."""
from pathlib import Path
import sys, re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')
from knowledge.document_parser import parser as docparser
from knowledge.retriever import KnowledgeRetriever

DATA = Path('backend/knowledge/data')
parsed = docparser.parse_directory(str(DATA))
xlsx_doc = [d for d in parsed if 'TỔNG THỂ' in d['filename'] or 'HC)' in d['filename']][0]

content = xlsx_doc['content']
r = KnowledgeRetriever()
chunks = r._chunk_text(content, chunk_size=500, overlap=50)

query = "can bo co quan uy ban mat tran to quoc viet nam"
query_lower = query.lower()
query_words = set(re.findall(r'\w+', query_lower))

print(f"Query words: {query_words}")

# Test BOTH _simple_search AND \w+ token extraction
print("\n=== Testing token extraction on chunks ===")
for i, chunk in enumerate(chunks[:15]):  # first 15 chunks
    chunk_lower = chunk.lower()
    chunk_words = set(re.findall(r'\w+', chunk_lower))
    matches = query_words & chunk_words
    if matches:
        score = len(matches) / max(len(query_words), len(chunk_words))
        print(f"\nChunk {i} (score={score:.4f}, matches={matches}):")
        print(chunk[:300])

# Now test CHUNK 7 specifically (we know it has UBMTTQ)
print("\n=== Chunk 7 (has UBMTTQ) ===")
chunk7 = chunks[7]
chunk7_lower = chunk7.lower()
chunk7_words = set(re.findall(r'\w+', chunk7_lower))
matches7 = query_words & chunk7_words
score7 = len(matches7) / max(len(query_words), len(chunk7_words))
print(f"Score: {score7:.4f}, Matches: {matches7}")
print(f"Chunk 7 content:\n{chunk7}")
