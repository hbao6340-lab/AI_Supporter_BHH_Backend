from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
d = Path('backend/knowledge/data')
files = [p for p in d.rglob('*') 
         if p.is_file() 
         and p.suffix.lower() in ['.txt','.pdf','.docx','.xlsx','']
         and 'readme' not in p.name.lower()
         and not p.name.startswith('~$')]
print(f'Scanned: {len(files)} files')
for p in sorted(files):
    print(p.name)
