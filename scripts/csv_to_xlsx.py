#!/usr/bin/env python3
"""Convert the submission CSV to XLSX (identical rows/columns).

The bundle's validator requires CSV, but the portal upload widget accepts
excel/spreadsheet - we ship both, byte-equivalent in content.

Usage: python scripts/csv_to_xlsx.py the_last_commit.csv
"""
import csv, sys
from openpyxl import Workbook

src = sys.argv[1] if len(sys.argv) > 1 else "the_last_commit.csv"
dst = src.rsplit(".", 1)[0] + ".xlsx"

wb = Workbook()
ws = wb.active
ws.title = "ranking"
with open(src, encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        ws.append(row)
# rank/score as numbers (not text) for a clean sheet
for r in range(2, ws.max_row + 1):
    ws.cell(r, 2).value = int(ws.cell(r, 2).value)
    ws.cell(r, 3).value = float(ws.cell(r, 3).value)
for col, w in zip("ABCD", (16, 7, 10, 110)):
    ws.column_dimensions[col].width = w
wb.save(dst)
print(f"wrote {dst} ({ws.max_row - 1} data rows)")
