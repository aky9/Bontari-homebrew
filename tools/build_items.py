"""Build every Item pack from the sheet rows and the specs in text/<pack>.json.

Each item starts as a copy of a Cyberpunk RED - Core 0.92.4 item (`tools/cpr-0.92.4-items.json`, copied from
corgo-77-module), named by the spec's `base`. Copying the system's own document gives every item exactly the
field set 0.92.4 expects for its type, so the conventions below only decide which values change. They are
corgo-77-module's (see its CLAUDE.md, "Conventions taken from the 0.92.4 source"):

- Cyberware: a foundational piece has `isFoundational: true` and `installedItems.slots` = the slots it
  provides; an option has `size` = the slots it uses. Options install only into a foundational piece of the
  same cyberware `type`. Passive ware is `usage: "installed"` with a plain effect; activated ware is
  `usage: "toggled"` with its changes flagged situational, so they show as toggles in the roll dialog.
- `humanityLoss.roll` must be a plain dice formula (0.92.4 reads `roll.terms[0].results`).
- Enhancements (itemUpgrade, type "cyberware") take no slot and carry no Active Effects, because an
  upgrade's effects apply from the inventory whether or not it is installed.
- Armor has one penalty for REF, DEX, and MOVE; only the worst among worn pieces counts.
- Drugs follow the core's pattern: "X Primary" is the `consumed` effect, "X Addiction" is switched on by hand.

A spec is keyed by the row's name in the sheet:

    base             core item to copy (required); "base_type" picks between same-named items
    name             item name (default: the row's name); "edition": true appends " (Bontari Edition)"
    replaces         for an edition item, the item it replaces (shown as a fact)
    enhances         for an enhancement, the item it enhances (shown as a fact, resolved by validate.mjs)
    folder           folder in the pack
    set              {"dotted.path": value} changes to the copied system data
    price            eurodollar price (default: parsed from the row's COST)
    hl               [static, roll] (default: parsed from the row's HL, for cyberware)
    install          cyberware install location (default: the row's INSTALL)
    effects          [{name, changes: [[key, value, mode?]], situational, on_by_default, disabled}]
    keep_effects     keep the base item's own Active Effects
    consumed         a drug's consumed effect name
    img              icon path under the system's compendium icons, or a full path
    notes            Foundry notes
    split            [{name, price, set, effects, notes}]: one item per entry instead of one for the row
"""
import copy, re
from pathlib import Path
from common import (doc_id, parse_cost, description_html, folder_doc, load_json, html_escape, text_html,
                    SOURCE_BOOK, EDITION)

ROOT = Path(__file__).resolve().parent.parent
ICONS = "systems/cyberpunk-red-core/icons/compendium/"
TEXT_COLUMNS = ("DESCRIPTION", "Description", "CHANGES")
COLUMN_LABEL = {"HL": "Humanity Loss", "SP": "SP", "UPGRADE DV": "Upgrade DV",
                "AMMO TYPES AVAILABLE:": "Ammo Types Available", "NERF, BUFF, or SIDE-GRADE?": "Nerf, Buff, or Side-Grade"}
TYPE_LABEL = {"fashionware": "Fashionware", "neuralWare": "Neuralware", "cyberEye": "Cybereye",
              "cyberAudioSuite": "Cyberaudio Suite", "cyberArm": "Cyberarm", "cyberLeg": "Cyberleg",
              "cyberwareInternal": "Internal Body Cyberware", "cyberwareExternal": "External Body Cyberware",
              "borgware": "Borgware"}
INSTALL = {"mall": "mall", "clinic": "clinic", "hospital": "hospital", "n/a": "notApplicable"}
# Active Effect key -> the category flag CPR stores alongside the change (see CPR.activeEffectKeys).
COMBAT_KEYS = {"bonuses.initiative", "bonuses.maxHp", "bonuses.maxHumanity", "bonuses.deathSavePenalty",
               "bonuses.aimedShot", "bonuses.singleShot", "bonuses.melee", "bonuses.ranged", "bonuses.autofire",
               "bonuses.suppressive", "bonuses.hands", "bonuses.run", "bonuses.walk", "bonuses.attack",
               "bonuses.universalAttack", "bonuses.universalDamage", "bonuses.universalDamageReduction"}

_CORE = None


def core_item(name, itype=None):
    global _CORE
    if _CORE is None:
        _CORE = {}
        for i in load_json(ROOT / "tools/cpr-0.92.4-items.json")["items"]:
            _CORE.setdefault(i["name"], []).append(i)
    found = [i for i in _CORE.get(name, []) if itype in (None, i["type"])]
    if len(found) != 1:
        raise SystemExit(f"base {name!r} ({itype or 'any type'}) matches {len(found)} core items; set base_type")
    return found[0]


def column_label(h):
    return COLUMN_LABEL.get(h, h.strip().rstrip(":").title() if h.isupper() else h.strip())


def _key(k):
    return k if "." in k else f"system.stats.{k}.value"


def effect(item_id, name, img, changes, situational=False, on_by_default=False, disabled=False):
    """changes: [key, value] or [key, value, mode] (2 = add, 3 = cap at, 4 = raise to at least, 5 = set)."""
    eid = doc_id("effect", f"{item_id}:{name}")
    cats, sit, out = {}, {}, []
    for i, ch in enumerate(changes):
        key, value, mode = _key(ch[0]), ch[1], (ch[2] if len(ch) > 2 else 2)
        out.append({"key": key, "mode": mode, "priority": None, "value": str(value)})
        cats[str(i)] = "stat" if key.startswith("system.stats.") else "combat" if key in COMBAT_KEYS else "skill"
        sit[str(i)] = {"isSituational": situational, "onByDefault": on_by_default}
    return {"_id": eid, "_key": f"!items.effects!{item_id}.{eid}", "name": name, "img": img, "changes": out,
            "description": "", "disabled": disabled,
            "duration": {k: None for k in ("combat", "rounds", "seconds", "startRound", "startTime", "startTurn",
                                           "turns")},
            "flags": {"cyberpunk-red-core": {"changes": {"cats": cats, "situational": sit}}},
            "statuses": [], "system": {}, "transfer": True, "type": "base"}


def _set(system, path, value):
    *head, last = path.split(".")
    node = system
    for p in head:
        if p not in node:
            raise SystemExit(f"set: {path!r} is not a field of the base item")
        node = node[p]
    if last not in node:
        raise SystemExit(f"set: {path!r} is not a field of the base item")
    node[last] = copy.deepcopy(value)


def parse_hl(raw):
    """'14 (4d6)' -> (14, '4d6'); '0' -> (0, '0'); 'NA' or blank -> None"""
    m = re.fullmatch(r"(\d+)\s*(?:\((\d*d\d+)\))?", (raw or "").strip())
    return (int(m.group(1)), m.group(2) or m.group(1)) if m else None


def item_doc(pack, key, name, spec, rec, folder):
    """One item from a sheet row (`rec`, or None for an item with no row) and its spec."""
    base = core_item(spec["base"], spec.get("base_type"))
    s = copy.deepcopy(base["system"])
    s["source"] = {"book": SOURCE_BOOK, "page": 0}
    if "installedItems" in s:
        s["installedItems"].update(list=[], usedSlots=0)
    if "equipped" in s:
        s["equipped"] = "owned"
    if base["type"] == "itemUpgrade":  # start from a neutral upgrade: the base's own bonuses and weapon are its own
        for k, m in s["modifiers"].items():
            if k == "secondaryWeapon":
                s["modifiers"][k] = {"configured": False}
            else:
                m.update(value=None, isSituational=False, onByDefault=False)
        s.update(damage="0", canIgnoreArmor=False, ignoreArmorPercent=0)
    f = rec["fields"] if rec else {}
    price = spec["price"] if "price" in spec else parse_cost(f.get("COST"))[0]
    s["price"]["market"] = price

    facts, notes = [], list(spec.get("notes", []))
    if base["type"] == "cyberware":
        hl = spec.get("hl") or parse_hl(f.get("HL"))
        if hl is None:
            raise SystemExit(f"{key}: Humanity Loss {f.get('HL')!r} is not 'N (XdY)'; give \"hl\" in the spec")
        s["humanityLoss"] = {"static": hl[0], "roll": str(hl[1])}
        install = spec.get("install") or INSTALL.get((f.get("INSTALL") or "").strip().lower())
        if install:
            s["installLocation"] = install
    if base["type"] == "cyberware":
        # The system's source JSON leaves these at their data-model defaults; the reference field set has them.
        s.setdefault("critFailEffect", "jammed")
        s.setdefault("ignoreBelowSP", 0)
    for path, value in spec.get("set", {}).items():
        _set(s, path, value)
    if base["type"] == "cyberware":
        if not s["installedItems"]["allowed"]:
            s["installedItems"]["slots"] = 0  # core options carry a leftover 3 that nothing can use
        if any(not e.get("situational") for e in spec.get("effects", [])) and "usage" not in spec.get("set", {}):
            # A passive bonus applies exactly while installed; "toggled" is for activated ware (see docstring).
            s["usage"] = "installed"
    if base["type"] == "cyberware":
        facts.append(("Type", TYPE_LABEL[s["type"]] + (" (Foundational)" if s["isFoundational"] else "")))
        if s["isFoundational"]:
            facts.append(("Option Slots", f"provides {s['installedItems']['slots']}"))
        else:
            facts.append(("Option Slots", f"uses {s['size']}" +
                          (f", provides {s['installedItems']['slots']}" if s["installedItems"]["allowed"]
                           and s["installedItems"]["slots"] else "")))
    if spec.get("enhances"):
        facts.append(("Enhances", spec["enhances"]))
    if spec.get("replaces"):
        facts.append(("Replaces", spec["replaces"]))
    for k, v in spec.get("facts", []):
        facts.append((k, v))

    text_col = next((c for c in TEXT_COLUMNS if c in f), None)
    stats = [(column_label(k), v) for k, v in f.items() if k != text_col and not k.startswith("col")]
    s["description"] = {"value": description_html(stats=stats, text=f.get(text_col, "") if text_col else "",
                                                  facts=facts, notes=notes, tab=rec["tab"] if rec else "")}
    if spec.get("rules"):  # the module's own text, for an item the sheet does not describe on its own
        s["description"]["value"] = text_html(spec["rules"]) + "\n" + s["description"]["value"]
    if "consumed" in spec:
        s["consumed"] = spec["consumed"]

    _id = doc_id(pack, key)
    img = spec.get("img") or base["img"]
    if not img.startswith(("systems/", "icons/", "modules/")):
        img = ICONS + img
    effects = []
    if spec.get("keep_effects"):
        for e in base["effects"]:
            ne = effect(_id, e["name"] if e["name"] != base["name"] else name, img, [], False)
            ne.update(changes=copy.deepcopy(e["changes"]), flags=copy.deepcopy(e["flags"]), disabled=e["disabled"])
            effects.append(ne)
    for e in spec.get("effects", []):
        effects.append(effect(_id, e.get("name", name), img, e["changes"], situational=e.get("situational", False),
                              on_by_default=e.get("on_by_default", False), disabled=e.get("disabled", False)))
    return {"_id": _id, "_key": f"!items!{_id}", "name": name, "type": base["type"], "img": img, "system": s,
            "effects": effects, "folder": folder, "sort": 0, "ownership": {"default": 0}, "flags": {}}


def build_pack(pack, rows):
    """Returns (documents, sheet row names used)."""
    spec = load_json(ROOT / f"text/{pack}.json")
    docs, folders, used = [], {}, set()

    def folder(label):
        if label not in folders:
            fd = folder_doc(pack, label, len(folders))
            folders[label] = fd["_id"]
            docs.append(fd)
        return folders[label]

    for label in spec.get("folders", []):
        folder(label)
    for key, sp in spec["items"].items():
        row = sp.get("row", key)
        if row is not None and row not in rows:
            raise SystemExit(f"text/{pack}.json: {row!r} is not a row in the sheet")
        rec = rows.get(row) if row is not None else None
        if row is not None:
            used.add(row)
        fid = folder(sp["folder"]) if sp.get("folder") else None
        base_name = sp.get("name") or key
        for variant in sp.get("split") or [None]:
            v = {**sp, **(variant or {})}
            if variant:
                v["set"] = {**sp.get("set", {}), **variant.get("set", {})}
                v["notes"] = list(sp.get("notes", [])) + list(variant.get("notes", []))
                v["effects"] = variant.get("effects", sp.get("effects", []))
            name = (v["name"] if variant else base_name) + (EDITION if sp.get("edition") else "")
            docs.append(item_doc(pack, key if not variant else f"{key}:{v['name']}", name, v, rec, fid))
    return docs, used


def build_journal(pack, rows):
    """JournalEntry documents, one page per sheet row (or per spec'd text)."""
    spec = load_json(ROOT / f"text/{pack}.json")
    docs, used = [], set()
    for i, entry in enumerate(spec["entries"]):
        jid = doc_id(f"journal:{pack}", entry["name"])
        pages = []
        for j, p in enumerate(entry["pages"]):
            rec = rows.get(p.get("row")) if p.get("row") else None
            if p.get("row") and rec is None:
                raise SystemExit(f"text/{pack}.json: {p['row']!r} is not a row in the sheet")
            if rec:
                used.add(p["row"])
            f = rec["fields"] if rec else {}
            text_col = next((c for c in TEXT_COLUMNS if c in f), None)
            stats = [(column_label(k), v) for k, v in f.items() if k != text_col and not k.startswith("col")]
            body = description_html(stats=stats, text=(p.get("text") or "") + (f.get(text_col, "") if text_col else ""),
                                    facts=[], notes=p.get("notes", []), tab=rec["tab"] if rec else entry["name"])
            pid = doc_id(f"page:{pack}", f"{entry['name']}:{p['name']}")
            pages.append({"_id": pid, "_key": f"!journal.pages!{jid}.{pid}", "name": p["name"], "type": "text",
                          "title": {"show": True, "level": 1}, "text": {"format": 1, "content": body},
                          "sort": (j + 1) * 100000, "ownership": {"default": -1}, "flags": {}, "system": {}})
        docs.append({"_id": jid, "_key": f"!journal!{jid}", "name": entry["name"], "pages": pages, "folder": None,
                     "sort": (i + 1) * 100000, "ownership": {"default": 0}, "flags": {}})
    return docs, used
