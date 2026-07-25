"""
Complete fix: Smart Excel chunking by sections + records + passage building
for DANH SÁCH TỔNG THỂ (HC).xlsx and similar tabular files
"""
from pathlib import Path
import sys, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')

from knowledge.document_parser import parser as docparser
from knowledge.retriever import KnowledgeRetriever
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA = Path('backend/knowledge/data')
parsed = docparser.parse_directory(str(DATA))
xlsx_doc = [d for d in parsed if 'TỔNG THỂ' in d['filename'] or 'HC)' in d['filename']]
if not xlsx_doc:
    print("XLSX NOT FOUND!")
    exit(1)
xlsx_doc = xlsx_doc[0]
full_text = xlsx_doc['content']
print(f"File: {xlsx_doc['filename']}, len: {len(full_text)}")

# ─── SMART PARSER ──────────────────────────────────────────────────────────────
# Identify sheets, section markers, and records

SECTION_HEADER_RE = re.compile(r'^\s*[IVX]+[\s\.]+')
# Section title patterns in the Excel
SECTION_RE = re.compile(
    r'^(?:=|I{1,3}V?X?[\s\.])[\s\S]*?(?:UBND|ỦY BAN|MẶT TRẬN|TỔ QUỐC|'
    r'TRƯỞNG|VĂN PHÒNG|PHÒNG|BAN|TRUNG TÂM|TRƯỜNG)[\s\S]*$',
    re.MULTILINE
)

def smart_chunk_xlsx(text: str) -> list[str]:
    """
    Chunk Excel text respecting section headers and row boundaries.
    Each chunk = section header + all following rows until next section.
    """
    lines = text.split('\n')
    chunks = []
    current_section_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            continue
            
        # Detect section headers (I., II., III., IV., V., VI., etc.)
        if SECTION_HEADER_RE.match(stripped):
            # Save previous section if it exists and has content
            if current_section_lines:
                sections_text = '\n'.join(current_section_lines).strip()
                if sections_text:
                    chunks.append(sections_text)
            # Start new section
            current_section_lines = [stripped]
        elif current_section_lines and '|' in stripped:
            # Data row - add to current section
            # Avoid adding rows that are mostly empty
            non_empty = [c for c in stripped.split('|') if c.strip()]
            if non_empty:
                # Add row to current section
                current_section_lines.append(stripped)
        elif current_section_lines:
            # Non-data, non-section line - maybe keep it
            current_section_lines.append(stripped)
    
    # Don't forget the last section
    if current_section_lines:
        sections_text = '\n'.join(current_section_lines).strip()
        if sections_text:
            chunks.append(sections_text)
    
    return chunks

xlsx_chunks = smart_chunk_xlsx(full_text)
print(f"\nSmart chunks: {len(xlsx_chunks)}")

# Also chunk the non-sheet content separately (titles, headers)
header_lines = []
rest_lines = []
in_sheet = False

for line in full_text.split('\n'):
    if line.startswith('===') or in_sheet:
        in_sheet = True
        continue
    header_lines.append(line)
    in_sheet = True

header_text = '\n'.join(header_lines)

# Build final chunks: header + xlsx section chunks
all_text_chunks = []
for chunk in xlsx_chunks:
    for sub in r._chunk_text(chunk, chunk_size=1000, overlap=100):
        if sub.strip():
            all_text_chunks.append(sub)

print(f"Total smart chunks: {len(all_text_chunks)}")

# ─── SCORING TEST ────────────────────────────────────────────────────────────
query = "can bo co quan uy ban mat tran to quoc viet nam"
query_lower = query.lower()
query_words = set(re.findall(r'\w+', query_lower))

print(f"\nQuery: {query}")
print(f"Query tokens: {query_words}\n")

results = []
for i, chunk in enumerate(all_text_chunks):
    chunk_lower = chunk.lower()
    chunk_words = set(re.findall(r'\w+', chunk_lower))
    matches = query_words & chunk_words
    if matches:
        score = len(matches) / max(len(query_words), len(chunk_words))
        results.append((score, i, chunk, matches))

results.sort(reverse=True)
print(f"Chunks with matches: {len(results)}")
for score, idx, chunk, matches in results[:15]:
    print(f"\n  Chunk {idx} (SIM={score:.4f}, matches={len(matches)}/{len(query_words)})")
    print(f"  {chunk[:250]}")
