"""Build the Cyberware pack from the sheet's Cyberware tab and text/cyberware.json.

The conventions are corgo-77-module's (its tools/build_cyberware.py docstring has the 0.92.4 reasoning):

- A foundational piece has `isFoundational: true` and `installedItems.slots` = the Option Slots it provides;
  an option has `isFoundational: false` and `size` = the Option Slots it uses. 0.92.4 only offers install
  targets whose cyberware `type` matches the option's (`cpr-actor.js installCyberware`).
- Passive ware is `usage: "installed"` with a plain effect, so it applies exactly while installed. Activated
  ware is `usage: "toggled"` with the change flagged situational, so it shows as a toggle in the roll dialog.
- `humanityLoss.roll` must be a plain dice formula: 0.92.4 reads `roll.terms[0].results`, which only a
  DiceTerm has.

A spec entry is keyed by the item's name in the sheet. `type` is required; `size`, `slots`, `foundational`,
`usage`, `effects`, `name`, `icon`, and `notes` are optional. Cost, Install, and Humanity Loss come from the
sheet's columns.
"""
import copy, re
from pathlib import Path
from common import doc_id, parse_cost, description_html, folder_doc, load_json, SOURCE_BOOK

ROOT = Path(__file__).resolve().parent.parent
ICONS = "systems/cyberpunk-red-core/icons/compendium/"
DEFAULT_ICON = "default/Default_Cyberware.svg"

CYBERWARE_TEMPLATE = {  # key set of CPR 0.92.4 core cyberware (e.g. Cyberarm, Big Knucks)
    "ammoVariety": [], "attackmod": 0, "brand": "", "canIgnoreArmor": True,
    "concealable": {"concealable": False, "isConcealed": False}, "core": False, "critFailEffect": "jammed",
    "damage": "1d6", "description": {"value": ""}, "dvTable": "", "favorite": False,
    "fireModes": {"autoFire": 0, "suppressiveFire": False}, "humanityLoss": {"roll": "1d6", "static": 3},
    "ignoreArmorPercent": 50, "ignoreBelowSP": 0, "installLocation": "mall",
    "installedItems": {"allowed": False, "allowedTypes": ["itemUpgrade"], "list": [], "slots": 0, "usedSlots": 0},
    "isElectronic": True, "isFoundational": False, "isRanged": False, "isWeapon": False,
    "magazine": {"ammoData": None, "max": 0, "value": 0}, "price": {"market": 0}, "providesHardening": False,
    "revealed": True, "rof": 1, "size": 1, "source": {"book": SOURCE_BOOK, "page": 0}, "type": "cyberwareInternal",
    "unarmedAutomaticCalculation": True, "usage": "installed", "usesType": "magazine", "weaponSkill": "Archery",
    "weaponType": "assaultRifle",
}

TYPE_LABEL = {"fashionware": "Fashionware", "neuralWare": "Neuralware", "cyberEye": "Cybereye",
              "cyberAudioSuite": "Cyberaudio Suite", "cyberArm": "Cyberarm", "cyberLeg": "Cyberleg",
              "cyberwareInternal": "Internal Body Cyberware", "cyberwareExternal": "External Body Cyberware",
              "borgware": "Borgware"}
INSTALL_LABEL = {"mall": "Mall", "clinic": "Clinic", "hospital": "Hospital", "notApplicable": "N/A"}
# Active Effect key -> the category flag CPR stores alongside the change (see CPR.activeEffectKeys).
COMBAT_KEYS = {"bonuses.initiative", "bonuses.maxHp", "bonuses.maxHumanity", "bonuses.deathSavePenalty",
               "bonuses.aimedShot", "bonuses.singleShot", "bonuses.melee", "bonuses.ranged", "bonuses.autofire",
               "bonuses.suppressive", "bonuses.hands", "bonuses.run", "bonuses.walk",
               "bonuses.universalAttack", "bonuses.universalDamage", "bonuses.universalDamageReduction"}


def icon_path(stem):
    if not stem:
        return ICONS + DEFAULT_ICON
    return ICONS + (stem if "/" in stem else f"cyberware/{stem}") + ".svg"


def _key(k):
    return k if "." in k else f"system.stats.{k}.value"


def effect(item_id, name, img, changes, situational=False, on_by_default=False):
    """changes: [key, value] or [key, value, mode] (2 = add, 3 = cap at, 4 = raise to at least, 5 = set)."""
    eid = doc_id("effect", f"{item_id}:{name}")
    cats, sit, out = {}, {}, []
    for i, ch in enumerate(changes):
        key, value, mode = _key(ch[0]), ch[1], (ch[2] if len(ch) > 2 else 2)
        out.append({"key": key, "mode": mode, "priority": None, "value": str(value)})
        cats[str(i)] = "stat" if key.startswith("system.stats.") else "combat" if key in COMBAT_KEYS else "skill"
        sit[str(i)] = {"isSituational": situational, "onByDefault": on_by_default}
    return {"_id": eid, "_key": f"!items.effects!{item_id}.{eid}", "name": name, "img": img, "changes": out,
            "description": "", "disabled": False,
            "duration": {k: None for k in ("combat", "rounds", "seconds", "startRound", "startTime", "startTurn",
                                           "turns")},
            "flags": {"cyberpunk-red-core": {"changes": {"cats": cats, "situational": sit}}},
            "statuses": [], "system": {}, "transfer": True, "type": "base"}


def parse_hl(raw):
    """'14 (4d6)' -> (14, '4d6'); '0' -> (0, '0'); 'NA' or blank -> None"""
    m = re.fullmatch(r"(\d+)\s*(?:\((\d*d\d+)\))?", (raw or "").strip())
    if not m:
        return None
    return int(m.group(1)), m.group(2) or m.group(1)


def cyberware_item(rec, spec, folder):
    f = rec["fields"]
    s = copy.deepcopy(CYBERWARE_TEMPLATE)
    name = spec.get("name") or rec["name"]
    price = spec.get("price", parse_cost(f.get("COST"))[0])
    hl = spec.get("hl") or parse_hl(f.get("HL"))
    if hl is None:
        raise SystemExit(f"{rec['name']}: Humanity Loss {f.get('HL')!r} is not 'N (XdY)'; give \"hl\" in the spec")
    install = spec.get("install") or (f.get("INSTALL") or "mall").strip().lower()
    if install not in INSTALL_LABEL:
        raise SystemExit(f"{rec['name']}: install {install!r} is not one of {sorted(INSTALL_LABEL)}")
    s["price"]["market"] = price
    s["humanityLoss"] = {"static": hl[0], "roll": str(hl[1])}
    s["type"] = spec["type"]
    s["size"] = spec.get("size", 1)
    s["isFoundational"] = spec.get("foundational", False)
    s["installLocation"] = install
    s["usage"] = spec.get("usage", "installed")
    s["installedItems"]["slots"] = spec.get("slots", 0)
    s["installedItems"]["allowed"] = bool(spec.get("slots"))

    stats = [("Cost", f.get("COST", "")), ("Install", f.get("INSTALL", "")), ("Humanity Loss", f.get("HL", ""))]
    if f.get("VENDOR"):
        stats.append(("Vendor", f["VENDOR"]))
    facts = [("Type", TYPE_LABEL[spec["type"]] + (" (Foundational)" if s["isFoundational"] else "")),
             ("Option Slots", f"uses {s['size']}" + (f", provides {spec['slots']}" if spec.get("slots") else ""))]
    s["description"]["value"] = description_html(
        stats=[(k, v) for k, v in stats if v], text=f.get("DESCRIPTION", ""), facts=facts,
        notes=spec.get("notes", []), tab=rec["tab"])

    _id = doc_id("cyberware", rec["name"])
    img = icon_path(spec.get("icon"))
    effects = [effect(_id, e.get("name", name), img, e["changes"], situational=e.get("situational", False),
                      on_by_default=e.get("on_by_default", False)) for e in spec.get("effects", [])]
    return {"_id": _id, "_key": f"!items!{_id}", "name": name, "type": "cyberware", "img": img, "system": s,
            "effects": effects, "folder": folder, "sort": 0, "ownership": {"default": 0}, "flags": {}}


def build_all(records):
    spec = load_json(ROOT / "text/cyberware.json")["items"]
    rows = {r["name"]: r for r in records if r["tab"] == "Cyberware"}
    docs, folders = [], {}
    for key, sp in spec.items():
        if key not in rows:
            raise SystemExit(f"text/cyberware.json: {key!r} is not a row in the Cyberware tab")
        label = TYPE_LABEL[sp["type"]]
        if label not in folders:
            fd = folder_doc("cyberware", label, len(folders))
            folders[label] = fd["_id"]
            docs.append(fd)
        docs.append(cyberware_item(rows[key], sp, folders[label]))
    return {"cyberware": docs}, set(spec)
