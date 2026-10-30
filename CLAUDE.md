# Developing the Bontari Homebrew module

A Foundry VTT module, `bontari-homebrew`, for the Cyberpunk RED - Core 0.92.4 system, built from Bontari's
spreadsheet of homebrew items. Bontari asked for it and is credited as the author of the content.

The tooling is adapted from `aky9/corgo-77-module`, whose CLAUDE.md records the 0.92.4 conventions (cyberware
typing, Active Effect usage, Humanity Loss dice, armor penalty, description whitespace). They apply here
unchanged: read that file's "Conventions taken from the 0.92.4 source" before adding a new item type.

`docs/item-inventory.md` tags every row of the sheet (new, modified, lore, incomplete), and
`docs/module-plan.md` is the plan: which pack each row goes in and the order of work.

## Commands

Python 3 (standard library only) and Node 18 or newer. `./setup.sh` runs everything below. By hand:

    npm ci
    npm run parse      # data/Bontari-Homebrew-Cyberpunk-Items.xlsx -> data/sheet.parsed.json (git-ignored)
    npm run build      # parsed rows + text/*.json -> src/packs -> dist/bontari-homebrew
    npm run validate   # reads the compiled packs back and checks them against the 0.92.4 snapshot

To take in a newer version of Bontari's sheet, download it from Google Drive as .xlsx over
`data/Bontari-Homebrew-Cyberpunk-Items.xlsx` and run `npm run parse` and `npm run build`.

## How the build works

1. **Parse.** `tools/parse_sheet.py` reads the .xlsx (a zip of XML) with the standard library. Each tab's
   first non-empty row is its header; every later row with a name in column B is one record, with its
   other columns under their headers. Rows with no name are kept as that tab's notes (the Apps rule).
2. **Build.** `tools/build.py` builds each pack `module/module.json` lists with `tools/build_items.py`: an
   Item pack from `text/<pack>.json`, a JournalEntry pack (`house-rules`) from its entries. Each spec is keyed
   by a sheet row's name and names a 0.92.4 item to copy as its `base`, so every item has exactly the field
   set the system expects; the spec only changes values (`set`), adds effects, and adds Foundry notes. The
   docstring of `build_items.py` lists the spec fields and the conventions. One JSON document per item,
   folder, or journal goes to `src/packs/<pack>/`.
   The build fails on a spec whose row is not in the sheet, and on a sheet row that no pack uses and that is
   not in `text/skip.json` with a reason, so a row added to the sheet can't go missing quietly.
3. **Compile.** `tools/compile.mjs` compiles each pack `module/module.json` lists into LevelDB in
   `dist/bontari-homebrew/`, with `module/` copied in beside it.
4. **Validate.** `tools/validate.mjs`.

`src/packs/` is committed and is what ships; CI fails if a build changes it. IDs are stable:
`common.doc_id` hashes the module ID, the pack, and the item's sheet name (plus the variant name for a
`split`), so rebuilding never changes an ID, and no ID can collide with one from Corgo's module. Moving an
item to another pack changes its ID.

The snapshots in `tools/` come from corgo-77-module: `cpr-0.92.4-reference.json` (allowed values and field
sets), `cpr-0.92.4-items.json` (the system's own items, the bases; regenerate it there with
`tools/snapshot_core_items.mjs`), and `corgo-77-names.json` (Corgo's item names, for the name check).

## Rules for item content

- **Every item carries Bontari's text in full**: the sheet's stat columns, Bontari's description, then the facts
  the module adds (Type, Option Slots), then the Foundry notes, then the source line. Do not rewrite that text;
  typos included, it is Bontari's.
- **Foundry guidance goes in a spec's `notes`**: what is automated and what has to be applied by hand.
- **Modifications get " (Bontari Edition)"** (`common.EDITION`) at the end of their name: any item that
  changes an existing core or Corgo's 77 item. The validator fails on any item whose name is already a
  0.92.4 item (`tools/cpr-0.92.4-reference.json`) or a Corgo's 77 item (`tools/corgo-77-names.json`).
  Regenerate the Corgo list when that module adds items; its header says from which commit it was taken.
  Edition items live in the `bontari-editions` pack (`text/bontari-editions.json`), each with a `replaces`
  fact naming the item it replaces.
- **New items**, including ones built on an existing item (a branded Cyberarm), keep their own name.
- **Rule changes with no item** (Gorilla Arms, the Projectile Launch System, Cyberfingers, Exotic
  Bodysculpting, the HQ Upgrades) go in a House Rules journal, not an item. Never copy official R. Talsorian
  text the sheet does not contain to build an item it only modifies.
- **Rows with a gap** (no cost, a probable copy-paste error) are built from what the sheet gives, with a
  Foundry note naming the gap. **Incomplete rows** (Shrapnel Arrows, Grenade Arrows, SuperFlex Steel Limbs)
  are not built until Bontari fills them in.

## Releases

Bump `version` in `module/module.json` and merge to `main`. `.github/workflows/release.yml` runs on every push
to `main`; when no release `v<version>` exists yet it runs the full setup, pins the manifest's `download` to
that release's zip, and publishes the release (creating its tag) marked latest. A push that keeps the version
releases nothing. Releasing does not need a tag push, which this repository's Claude sessions cannot do (the
git proxy refuses tag refs). The install URL follows the latest release:

    https://github.com/aky9/bontari-homebrew/releases/latest/download/module.json

Foundry downloads it without logging in, so the repository has to stay public.

## Known gaps

- Only v0.0.1 (Syn-Heart alone) has been installed in Foundry. The full set of packs has been compiled and
  read back, not opened in Foundry. Worth checking first: a Sandevistan's toggles in the roll dialog, Spice's
  consumed effect, the House Rules journal, and a paired cyberarm with an option installed in it.
- Paired cyberlimbs (the branded Cyberarms and Cyberlegs) are one item for both limbs, with the per-limb
  slot count. Whether that reads well at the table is untested.
- Several Cyberware entries need slots in two categories (the Sandevistans' Internal Option Slots, the
  Militech Fortress's two arms). Foundry tracks one category per item; the item's notes state the rest.
