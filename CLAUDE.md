# Developing the Bontari Homebrew module

A Foundry VTT module, `bontari-homebrew`, for the Cyberpunk RED - Core 0.92.4 system, built from Nathan's
spreadsheet of homebrew items. Nathan asked for it; he is credited as the author of the content.

The tooling is adapted from `aky9/corgo-77-module`, whose CLAUDE.md records the 0.92.4 conventions (cyberware
typing, Active Effect usage, Humanity Loss dice, armor penalty, description whitespace). They apply here
unchanged: read that file's "Conventions taken from the 0.92.4 source" before adding a new item type.

`docs/item-inventory.md` tags every row of the sheet (new, modified, lore, incomplete), and
`docs/module-plan.md` is the plan: which pack each row goes in and the order of work.

## Commands

Python 3 (standard library only) and Node 18 or newer. `./setup.sh` runs everything below. By hand:

    npm ci
    npm run parse      # data/Nathans-Homebrew-Cyberpunk-Items.xlsx -> data/sheet.parsed.json (git-ignored)
    npm run build      # parsed rows + text/*.json -> src/packs -> dist/bontari-homebrew
    npm run validate   # reads the compiled packs back and checks them against the 0.92.4 snapshot

To take in a newer version of Nathan's sheet, download it from Google Drive as .xlsx over
`data/Nathans-Homebrew-Cyberpunk-Items.xlsx` and run `npm run parse` and `npm run build`.

## How the build works

1. **Parse.** `tools/parse_sheet.py` reads the .xlsx (a zip of XML) with the standard library. Each tab's
   first non-empty row is its header; every later row with a name in column B is one record, with its
   other columns under their headers. Rows with no name are kept as that tab's notes (the Apps rule).
2. **Build.** `tools/build.py` runs each `tools/build_<pack>.py`. A builder joins a sheet row with its
   automation data in `text/<pack>.json`, keyed by the row's name, and writes one JSON document per item or
   folder to `src/packs/<pack>/`. A spec with no matching row fails the build.
3. **Compile.** `tools/compile.mjs` compiles each pack `module/module.json` lists into LevelDB in
   `dist/bontari-homebrew/`, with `module/` copied in beside it.
4. **Validate.** `tools/validate.mjs`.

`src/packs/` is committed and is what ships; CI fails if a build changes it. IDs are stable:
`common.doc_id` hashes the module ID with the item's sheet name, so rebuilding never changes an ID, and no ID
can collide with one from Corgo's module.

## Rules for item content

- **Every item carries Nathan's text in full**: the sheet's stat columns, his description, then the facts
  the module adds (Type, Option Slots), then the Foundry notes, then the source line. Do not rewrite his text;
  typos included, it is his.
- **Foundry guidance goes in a spec's `notes`**: what is automated and what has to be applied by hand.
- **Modifications get " (Bontari Edition)"** (`common.EDITION`) at the end of their name: any item that
  changes an existing core or Corgo's 77 item. The validator fails on any item whose name is already a
  0.92.4 item (`tools/cpr-0.92.4-reference.json`) or a Corgo's 77 item (`tools/corgo-77-names.json`).
  Regenerate the Corgo list when that module adds items; its header says from which commit it was taken.
- **New items**, including ones built on an existing item (a branded Cyberarm), keep their own name.
- **Rule changes with no item** (Gorilla Arms, the Projectile Launch System, Cyberfingers, Exotic
  Bodysculpting, the HQ Upgrades) go in a House Rules journal, not an item. Never copy official R. Talsorian
  text the sheet does not contain to build an item it only modifies.
- **Rows with a gap** (no cost, a probable copy-paste error) are built from what the sheet gives, with a
  Foundry note naming the gap. **Incomplete rows** (Shrapnel Arrows, Grenade Arrows, SuperFlex Steel Limbs)
  are not built until Nathan fills them in.

## Releases

Bump `version` in `module/module.json` and merge to `main`. `.github/workflows/release.yml` runs on every push
to `main`; when no release `v<version>` exists yet it runs the full setup, pins the manifest's `download` to
that release's zip, and publishes the release (creating its tag) marked latest. A push that keeps the version
releases nothing. Releasing does not need a tag push, which this repository's Claude sessions cannot do (the
git proxy refuses tag refs). The install URL follows the latest release:

    https://github.com/aky9/bontari-homebrew/releases/latest/download/module.json

Foundry downloads it without logging in, so the repository has to stay public.

## Known gaps

- Nothing has been opened in Foundry yet; the packs have only been compiled and read back.
- `validate.mjs` checks cyberware only so far. Each new item type needs its field-set check, copied from
  corgo's validator, before its first item ships; until then the validator fails on it by design.
- `tools/build.py` reports the rows not yet built but does not fail on them. Once every pack is in, an
  unbuilt row that is not on a skip list should fail the build.
