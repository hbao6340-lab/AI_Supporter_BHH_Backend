"""Quick check: are there 2 different XLSX files or 1?"""
from pathlib import Path

data = Path('backend/knowledge/data')
for p in sorted(data.iterdir()):
    if p.is_file() and p.suffix == '.xlsx':
        print(f'{p.name!r}  {p.stat().st_size:,} bytes')
