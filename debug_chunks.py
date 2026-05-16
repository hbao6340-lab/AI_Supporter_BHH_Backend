import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

os.chdir(str(Path(__file__).parent.parent))

from knowledge.document_parser import parser
from knowledge.retriever import retriever

retriever.load_knowledge(force_reload=True)

# Find all chunks from the Excel file
xlsx_chunks = []
for i, (doc, source) in enumerate(zip(retriever.documents, retriever.document_sources)):
    if 'DANH SÁCH TỔNG THỂ (HC)' in source['filename'] or 'DANH SACH TONG THE' in source['filename'].upper():
        xlsx_chunks.append((i, doc, source))

print(f'XLSX Chunks: {len(xlsx_chunks)}')
print()

# Find chunks around "Mat tran" or "Mat tran" in xlsx
for idx, doc, source in xlsx_chunks:
    lower = doc.lower()
    if 'mat tran' in lower or 'mê·∫±t tr·∫°n' in lower or 'mặt trận' in lower:
        print(f'Chunk {idx} (chunk_id={source["chunk_id"]}), len={len(doc)}:')
        print(f'  {doc[:300]}')
        print()
