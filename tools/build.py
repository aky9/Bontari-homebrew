"""Build every pack source under src/packs/ from the parsed sheet and the specs in text/.
Run `npm run parse` first, and `node tools/compile.mjs` afterwards (npm run build does both).

The packs are the ones module/module.json lists: an Item pack is built from text/<pack>.json by
build_items.build_pack, a JournalEntry pack by build_items.build_journal. Every sheet row has to be used by
some pack or listed in text/skip.json with a reason, so a row added to the sheet can't go missing quietly.
"""
import re, shutil, sys
from pathlib import Path
import build_items
from common import dump_json, load_json

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "src/packs"
PARSED = ROOT / "data/sheet.parsed.json"


def write_pack(name, docs):
    out = PACKS / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for d in docs:
        slug = re.sub(r"[^a-z0-9]+", "-", d["name"].lower()).strip("-")
        dump_json(out / f"{slug}.{d['_id']}.json", d)
    print(f"{name}: {len(docs)} documents")


if __name__ == "__main__":
    if not PARSED.is_file():
        sys.exit(f"{PARSED.relative_to(ROOT)} is missing; run `npm run parse` first")
    rows = {r["name"]: r for r in load_json(PARSED)["records"]}
    used = set()
    for pack in load_json(ROOT / "module/module.json")["packs"]:
        build = build_items.build_journal if pack["type"] == "JournalEntry" else build_items.build_pack
        docs, names = build(pack["name"], rows)
        used |= names
        write_pack(pack["name"], docs)

    skip = load_json(ROOT / "text/skip.json")["rows"]
    problems = [f"text/skip.json lists {n!r}, which is not a row in the sheet" for n in skip if n not in rows]
    problems += [f"text/skip.json lists {n!r}, which is also built" for n in skip if n in used]
    problems += [f"sheet row {n!r} ({r['tab']}) is not built and not in text/skip.json"
                 for n, r in rows.items() if n not in used and n not in skip]
    print(f"{len(used)} of {len(rows)} sheet rows built; {len(skip)} skipped on purpose")
    if problems:
        sys.exit("\n".join(problems))
