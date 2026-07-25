"""Test \w+ tokenization on Vietnamese text."""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

text = 'cán bộ Ủy ban Mặt trận Tổ quốc Việt Nam cơ quan'
tokens = re.findall(r'\w+', text.lower())
print(f"Text: {text}")
print(f"Tokens: {tokens}")

# Also test on Excel content
test_chunk = 'V. CŨ QUAN ỦY BAN MẶT TRẬN TỔ QUỐC VIỆT NAM | | | | | | | | | | | | | | | | | | | 11 | 1 | Phạm Thị Hạnh Tư | 31 | 7 | 1975'
tokens2 = re.findall(r'\w+', test_chunk.lower())
print(f"\nTest chunk: {test_chunk}")
print(f"Tokens: {tokens2}")

query = "can bo co quan uy ban mat tran to quoc viet nam"
query_tokens = set(re.findall(r'\w+', query.lower()))
chunk_tokens = set(re.findall(r'\w+', test_chunk.lower()))
matches = query_tokens & chunk_tokens
score = len(matches) / max(len(query_tokens), len(chunk_tokens))
print(f"\nQuery tokens: {query_tokens}")
print(f"Chunk tokens: {chunk_tokens}")
print(f"Overlap: {matches}")
print(f"Score: {score:.4f}")
