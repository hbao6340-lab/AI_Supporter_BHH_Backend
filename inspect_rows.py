"""Inspect raw openpyxl rows to understand structure."""
from pathlib import Path
import sys, re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')

import openpyxl

DATA = Path('backend/knowledge/data')
XLSX = DATA / 'DANH SÁCH TỔNG THỂ (HC).xlsx'

wb = openpyxl.load_workbook(str(XLSX), data_only=True)
ws = wb['LĨNH VỰC']

print("First 50 data rows:")
for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
    row = list(row)
    # Get first 8 non-None values
    vals = [str(v).strip() if v is not None else '' for v in row[:8]]
    non_empty = [v for v in vals if v]
    if non_empty:
        print(f"  Row {row_idx:3d}: {vals[:6]}")
