# Plan: a Foundry module for Nathan's homebrew items

**Goal.** A Foundry VTT module, `bontari-homebrew`, for the Cyberpunk RED - Core 0.92.4 system. It ships Nathan's
items as compendiums, built from his spreadsheet, and installs from one manifest URL. The tagged list of every
entry is in `item-inventory.md`, next to this file.

## Decisions (settled 2026-10-29)

1. **Permission.** Nathan asked for this module. He is credited as the author of the content.
2. **Where it lives.** Its own repository, `aky9/bontari-homebrew`, as a separate module with its own
   version and releases. The build tools are copied from `corgo-77-module`.
3. **Corgo's module is recommended, not required.**
4. **Modifications get "(Bontari Edition)".** An item that modifies an existing core or Corgo's 77 item is
   built as described below, with " (Bontari Edition)" at the end of its name. Item IDs come from the name,
   so the ID differs too. New items, including the "built on X" variants, are built the way the corgo
   module builds its items, with no suffix.
5. **The ⚠ entries** are built from what the sheet gives, with a Foundry note naming the gap. **The
   INCOMPLETE entries** are left out and listed by name in the build output until Nathan fills them in.

## How the module installs

- The manifest is `https://github.com/aky9/bontari-homebrew/releases/latest/download/module.json`. The
  repository ships one module, so GitHub's own "latest release" link is enough; corgo needed rolling
  releases only because it ships two modules from one repository.
- Foundry downloads the manifest and zip without logging in, so **the repository has to stay public**. A
  private repository's release assets return 404 to Foundry.

## Pipeline

The steps are the same as corgo's, cut down to fit a spreadsheet:

1. **Source.** The `.xlsx` stays committed as the source of truth. Refreshing it means downloading a new
   export over it, which is what I did this time.
2. **Parse.** `tools/parse_sheet.py` reads the `.xlsx` with only the standard library (an `.xlsx` is a zip of
   XML), which keeps corgo's no-dependencies rule. One row becomes one record: name, tab, cost, install,
   Humanity Loss, vendor, and full description. Header rows, blank rows, and the empty tabs are skipped.
   The output is `data/sheet.parsed.json`, git-ignored.
3. **Automation data.** Hand-written in `text/<pack>.json`, keyed by item name, as corgo does it. The sheet is
   prose, so the numbers Foundry needs are written once here: SP, armor penalty, slot counts, damage,
   effects, `enhances`, and the item a variant is built on. The build fails on a spec with no row and on a
   row with no spec or entry on a skip list. That way a new row in Nathan's sheet can't go missing quietly.
4. **Build.** `tools/build.py` writes `src/packs/<pack>/*.json`. Each item's description is Nathan's text
   word for word, then "Foundry notes", then a line naming the source.
5. **Compile.** `tools/compile.mjs` runs the Foundry CLI to make LevelDB packs in `dist/bontari-homebrew/`.
6. **Validate.** `tools/validate.mjs` checks against the 0.92.4 snapshot: allowed values, field sets, the
   whitespace around block tags, `enhances` targets, and installs.

### Copied from corgo-77-module

These are tested and carry the 0.92.4 conventions CLAUDE.md lists:

- `tools/common.py`: stable IDs (salted with the new module's id, so they never collide with corgo's), cost
  parsing, `description_html`, folder documents.
- `tools/cpr-0.92.4-reference.json` and `tools/cpr-0.92.4-items.json`: allowed values, and the core items to
  copy from for the "built on X" variants and the Altered Official Items.
- `tools/compile.mjs`, the schema parts of `tools/validate.mjs`, and `setup.sh`, `ci.yml`, and `release.yml`
  with the names changed.
- The relevant parts of `CLAUDE.md`'s 0.92.4 conventions, carried into a new CLAUDE.md for this repository:
  cyberware typing, toggled effects, Humanity Loss dice, the armor penalty, and the description whitespace.

Builders are written fresh but follow corgo's patterns. Corgo's tools are built around his document's
headings and stat blocks, so they won't fit a spreadsheet as they are.

## Packs

| Pack | Contents | Type in Foundry |
|---|---|---|
| Weapons | Kinetic Impact Gauntlets, Hello Cutie Kitty Bap | `weapon` |
| Ammo | HEAP, Bunker Buster, Sabot, Subsonic | `ammo` (one item per caliber where the sheet says "Bullets", as corgo does) |
| Armor & Shields | 4 helmets and suits, Electromagnetic Shield | `armor` (the shield as a shield, like the core's Bullet Proof Shield) |
| Weapon Attachments | Bipod, Flashlight Rail, Superchrome Coating, Anti-Drone Smart Scope | `itemUpgrade` (weapon) |
| Cyberware | 27 cyberware items plus 11 Sandevistans | `cyberware`; the branded limbs as Cyberarms and Cyberlegs with their slots and pre-installed options, following corgo's Cyberware Alternatives |
| Cyberware Enhancements | 4 Self-ICE upgrades | `itemUpgrade` (cyberware), `enhances: Self-ICE`, no Active Effects (corgo's rule) |
| Tech Upgrades | 9 invented upgrades | `itemUpgrade` on the item type each applies to, with the DV and both costs in its description |
| Gear, Apps & Drugs | 7 apps with effects, 5 lore apps, Spice, Nicotine (3 tiers), Biotoxin, UV Flashlight, Battleboot | `gear`; drugs follow the core's Primary and Addiction effect pattern |
| Altered Official Items | Agent (Standard, Excellent), Medium Armorjack (Body, Head) | Copies of the core items with Nathan's change applied, named "<name> (Bontari Edition)". Used *in place of* the core ones. |
| House Rules | Gorilla Arms, PLS, Cyberfingers, Exotic Bodysculpting, the Agent and App rules, HQ Upgrades | `JournalEntry`, one page each |

### How each tag is handled

- **MOD-CORE with an item in Foundry** (Agent, Medium Armorjack). Copy the item from the 0.92.4 snapshot and
  change only what Nathan changes. A module can't edit the system's own compendiums, so the GM uses these.
- **MOD-CORE or MOD-OFFICIAL that change a rule** (Gorilla Arms, PLS, Cyberfingers, Exotic Bodysculpting).
  These go in the House Rules journal. I won't build Gorilla Arms or the PLS as items. Foundry has neither,
  and the sheet gives only the change, so building them would mean copying Edgerunners Mission Kit text.
- **MOD-CORGO** (Subsonic, Bipod, Syn-Lungs, Lynx Paws). Full items carrying Nathan's rules, named
  "<name> (Bontari Edition)". Each notes which Corgo item it replaces, so a world with both modules knows which one to use.
- **COPY-CORGO** (Reflex Sight). Not built. The README points to Corgo's.
- **NEW (built on X).** Built as full items. The base core item is named in the Foundry notes, and the base
  item's slots and options are carried over where Foundry models them.
- **Sandevistans.** Like the core Sandevistan: `usage: "toggled"`, with the Primary Effects as situational
  changes (Initiative, Evasion, Stealth, Perception, MOVE). The Secondary Effects and the Humanity Loss per
  activation can't be automated, so they stay in the text with a note. The three names that clash with
  Corgo's OSes get a note, not a rename, unless you want them renamed.

## Order of work

1. Set up the repository: copy the tools, add `module.json`, the README, `package.json`, `setup.sh`, and CI.
   Then build one item from end to end (Syn-Heart) and install it in Foundry from a test release. That proves
   the manifest URL before the bulk of the work.
2. Parser and the skip list, with a test that fails if the sheet gains a row nothing handles.
3. Packs in order of how much they automate: Gear, Apps & Drugs; Armor; Ammo; Attachments; Weapons;
   Cyberware with the variants; Sandevistans; Enhancements; Tech Upgrades; Altered Official Items; House Rules.
4. Validation, then tag `v0.1.0`.
5. Check in Foundry: import an item from each pack onto a character, and confirm the Sandevistan toggles, the
   armor penalty on the altered Medium Armorjack, and the branded limbs' slots. Like corgo's NPCs, this module
   isn't verified until someone opens it in Foundry.

## Questions for Nathan

- Shrapnel Arrows and Grenade Arrows: cost and rules. SuperFlex Steel Limbs: cost, and what Kyudo Hassetsu is.
- Hello Cutie Kitty Bap: damage, ROF, hands, and which shotgun line it uses.
- Kyber Foundationware's cost, Repair Nanites' Humanity Loss, and FBC Shimmer Coating's cost, install, and
  Humanity Loss.
- Sandevistans: the Dynalar and Seiryu notes name the wrong model; the unfinished Uzushio line; the Zenith's cost.
- Is Battleboot meant to be a weapon? It reads as a worn container for cyberleg options.
- Is "Spectre" or "Specture" the intended spelling?
- Should the lore apps (Night City Times, bart.mos, and the rest) be items at all, or just journal entries?
