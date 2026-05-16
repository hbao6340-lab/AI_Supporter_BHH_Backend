import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

data_dir = Path('backend/knowledge/data')
all_files = sorted(data_dir.iterdir())

print('All files in knowledge/data:')
for f in all_files:
    size = f.stat().st_size
    print(f'  {f.name!r}  [{size:,} bytes]')
    sys.stdout.flush()
