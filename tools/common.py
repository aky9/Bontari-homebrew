"""Shared helpers for building the Bontari Homebrew item documents.

Copied from corgo-77-module's tools/common.py and cut down: the ID scheme and the description whitespace
rule are the same, the source line credits Nathan's spreadsheet instead of Corgo's document.
"""
import hashlib, html, json, re, sys

# Item names carry characters a legacy Windows console can't encode ("Hyōheki", "™", curly quotes), and Python
# raises UnicodeEncodeError rather than mangling them. Ask for UTF-8 and fall back to replacing what the
# console can't show: a progress line is never worth failing a build over.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # not a real stream (redirected, or already wrapped)
        pass

MODULE_ID = "bontari-homebrew"
SOURCE_BOOK = "Nathan's Homebrew Cyberpunk Items"
SOURCE_AUTHOR = "Nathan"
# Edition suffix for items that modify an existing core or Corgo's 77 item, so the two never share a name.
EDITION = " (Bontari Edition)"

_B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def doc_id(kind, key):
    """Deterministic 16-character Foundry ID, so rebuilding the module keeps the same IDs. The module ID is
    part of the hash, so an ID can never collide with one from corgo-77-collection."""
    n = int(hashlib.sha256(f"{MODULE_ID}:{kind}:{key}".encode()).hexdigest(), 16)
    out = ""
    for _ in range(16):
        n, r = divmod(n, 62)
        out += _B62[r]
    return out


def parse_cost(raw):
    """'1,250eb (Very Expensive)' -> (1250, 'Very Expensive'); '1000' -> (1000, None)"""
    m = re.match(r"([\d,]+)\s*(?:eb)?\s*(?:\((.*?)\))?", raw or "")
    if not m:
        return 0, None
    return int(m.group(1).replace(",", "")), m.group(2)


def html_escape(s):
    return html.escape(s, quote=False)


def text_html(text):
    """Nathan's cell text as HTML: a blank line starts a paragraph, a single line break is a <br>.

    A newline follows every block tag: Foundry strips tags for list summaries and tooltips, and a tag with no
    whitespace around it welds the words either side of it together.
    """
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.replace("\r", "")) if p.strip()]
    return "\n".join("<p>" + "<br>\n".join(html_escape(l.strip()) for l in p.split("\n")) + "</p>"
                     for p in paras)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data, ensure_ascii=False):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=ensure_ascii)


def description_html(stats, text, facts, notes, tab):
    """The item description: the sheet's stat columns, Nathan's text, the facts this module adds, the Foundry
    notes, and the source line."""
    parts = []
    if stats:
        parts.append("<p>" + "<br>\n".join(f"<strong>{html_escape(k)}:</strong> {html_escape(v)}"
                                           for k, v in stats) + "</p>")
    if text:
        parts.append(text_html(text))
    if facts:
        parts.append("<p>" + "<br>\n".join(f"<strong>{html_escape(k)}:</strong> {html_escape(v)}"
                                           for k, v in facts) + "</p>")
    if notes:
        parts.append("<p><strong>Foundry notes:</strong></p>\n<ul>\n" +
                     "\n".join(f"<li>{html_escape(n)}</li>" for n in notes) + "\n</ul>")
    parts.append(f"<p><em>From {html_escape(SOURCE_BOOK)} by {html_escape(SOURCE_AUTHOR)} "
                 f"({html_escape(tab)}).</em></p>")
    return "\n".join(parts)


def folder_doc(pack, name, sort):
    _id = doc_id(f"folder:{pack}", name)
    return {"_id": _id, "_key": f"!folders!{_id}", "name": name, "type": "Item", "folder": None,
            "sorting": "a", "sort": (sort + 1) * 100000, "color": None, "description": "", "flags": {}}
