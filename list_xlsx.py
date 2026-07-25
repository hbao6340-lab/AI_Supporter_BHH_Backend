import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

os.chdir(str(Path(__file__).parent.parent))

# List all xlsx files
data_dir = Path('backend/knowledge/data')
files = list(data_dir.iterdir())
xlsx_files = [f for f in files if f.suffix.lower() == '.xlsx']

print('All XLSX files in knowledge/data:')
for f in sorted(xlsx_files):
    size = f.stat().st_size
    print(f'  {f.name!r} ({size} bytes)')
    
# Check for DANH SÁCH TỔNG THỂ variants
print('\nSearching for DANH SÁCH files:')
for f in files:
    if 'DANH' in f.name.upper() or 'SÁCH' in f.name.upper() or 'TỔNG' in f.name.upper():
        print(f'  {f.name!r} ({f.stat().st_size} bytes)')
