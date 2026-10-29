"""Read Nathan's spreadsheet into data/sheet.parsed.json: one record per item row.

An .xlsx is a zip of XML, so this needs only the standard library. Each tab has a header row (the first
non-empty row) and one row per item, with the item's name in column B. Every non-empty column is kept under
its header, so the builders can read COST, INSTALL, HL, VENDOR, and so on by name.

Rows with nothing in column B are not items (the Apps tab's rules note sits in column I) and are recorded
under "notes" for their tab instead.
"""
import re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from common import dump_json

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "data/Nathans-Homebrew-Cyberpunk-Items.xlsx"
OUT = ROOT / "data/sheet.parsed.json"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _text(si):
    """A shared or inline string: plain <t>, or rich text split across <r><t> runs."""
    return "".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t"))


def _col(ref):
    """'C12' -> 2 (zero-based column index)"""
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def _value(c, shared):
    t, v = c.get("t"), c.find("m:v", NS)
    if t == "s":
        return shared[int(v.text)]
    if t == "inlineStr":
        return _text(c.find("m:is", NS))
    if v is None:
        return ""
    raw = v.text or ""
    # Numbers: the export stores 11 as "11", but some cells hold "1000.0"-style floats; keep integers clean.
    if t in (None, "n") and re.fullmatch(r"-?\d+\.0+", raw):
        return raw.split(".")[0]
    return raw


def read_workbook(path):
    """{tab name: [[cell text, ...], ...]} in tab order, rows padded to their widest cell."""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
            if r.tag == f"{REL}Relationship"}
    tabs = {}
    for s in wb.find("m:sheets", NS):
        target = rels[s.get(f"{{{NS['r']}}}id")].lstrip("/")
        target = target if target.startswith("xl/") else "xl/" + target
        rows = []
        for row in ET.fromstring(z.read(target)).iter(f"{{{NS['m']}}}row"):
            cells = {_col(c.get("r")): _value(c, shared) for c in row.findall("m:c", NS)}
            if not any(str(v).strip() for v in cells.values()):
                continue
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        tabs[s.get("name")] = rows
    return tabs


def parse(path=SHEET):
    records, notes = [], {}
    for tab, rows in read_workbook(path).items():
        if not rows:
            continue
        header = [h.strip() for h in rows[0]]
        for row in rows[1:]:
            fields = {header[i] if i < len(header) and header[i] else f"col{i}": v.strip()
                      for i, v in enumerate(row) if str(v).strip()}
            name = row[1].strip() if len(row) > 1 else ""
            if not name:
                notes.setdefault(tab.strip(), []).extend(fields.values())
                continue
            # Column B's header is the tab's own label for the name ("CYBERWARE NAME", "Weapon "), so drop it.
            fields.pop(header[1], None)
            records.append({"tab": tab.strip(), "name": name, "fields": fields})
    return records, notes


if __name__ == "__main__":
    records, notes = parse()
    dump_json(OUT, {"source": SHEET.name, "records": records, "notes": notes})
    tabs = {}
    for r in records:
        tabs[r["tab"]] = tabs.get(r["tab"], 0) + 1
    print(f"{len(records)} rows from {len(tabs)} tabs -> {OUT.relative_to(ROOT)}")
    for t, n in tabs.items():
        print(f"  {t}: {n}")
    sys.exit(0 if records else 1)
