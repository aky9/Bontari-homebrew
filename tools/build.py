"""Build every pack source under src/packs/ from the parsed sheet and the automation data in text/.
Run `npm run parse` first, and `node tools/compile.mjs` afterwards (npm run build does both)."""
import re, shutil, sys
from pathlib import Path
import build_cyberware
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
    records = load_json(PARSED)["records"]
    handled = set()
    for builder in (build_cyberware,):
        packs, names = builder.build_all(records)
        handled |= names
        for name, docs in packs.items():
            write_pack(name, docs)
    pending = [r for r in records if r["name"] not in handled]
    print(f"{len(handled)} of {len(records)} sheet rows built; {len(pending)} not built yet")
