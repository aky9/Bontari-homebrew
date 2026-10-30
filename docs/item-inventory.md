# Bontari Homebrew Cyberpunk Items: what is new and what is modified

Source: `Bontari-Homebrew-Cyberpunk-Items.xlsx` in aky9/bontari-homebrew (export of Bontari's Google Sheet, last
edited 2026-10-28). 95 entries across 12 tabs; the "Fashionware & Cyberlimb Coverings" tab and "Sheet6" are empty.

Each name was matched against the 1,037 items Cyberpunk RED - Core 0.92.4 ships (`tools/cpr-0.92.4-items.json`),
the built Corgo's 77 packs (`src/packs/`), and the headings of Corgo's document. Close matches were then compared
by text, so a shared name with different rules counts as a modification and a different name with copied rules
counts as a copy.

## Tags

| Tag | Meaning | Count |
|---|---|---|
| **MOD-CORE** | Changes an official item. Where the Foundry system has it, it's named in the table. | 4 |
| **MOD-OFFICIAL** | Changes an official item (Edgerunners Mission Kit) that the Foundry system does not include. | 2 |
| **MOD-CORGO** | Same name as a Corgo's 77 item, with Bontari's own rules, cost, or Humanity Loss. | 5 |
| **COPY-CORGO** | Rules text is Corgo's, word for word. | 1 |
| **NEW (built on X)** | A new item that is an existing item plus changes (a branded Cyberarm, a TUped helmet). | 24 |
| **NEW** | Bontari's own item. | 49 |
| **LORE** | No mechanics: websites and free apps that are setting flavor. | 5 |
| **RULE** | Not an item: HQ upgrades. | 2 |
| **INCOMPLETE** | Missing the text needed to build it. | 3 |

Separately, ⚠ marks entries that can be built but have a gap or a probable copy-paste error to ask Bontari about.

## Official Items with Altered Rules (6)

| Item | Tag | Existing item | Notes |
|---|---|---|---|
| Gorilla Arms (Edgerunners) | MOD-OFFICIAL | none in Foundry; Corgo has his own **Gorilla Arm** | Bontari's change (Brawling ignores half armor, two arms = BODY 11 for Brawling damage) is close to Corgo's Gorilla Arm, which already uses Brawling. |
| Agents (Core) | MOD-CORE | `Agent` (gear, Core) | Becomes hackable (5 HP, a Control Node) and loses its +2 Library Search; adds Standard (100eb, DV 8) and Excellent (500eb, DV 10) tiers. |
| Cyberfingers (Black Chrome) | MOD-CORE | 14 `* Cyberfinger` items (BC) | Replaces individual cyberfingers with two cyberhand slots. This is a rule, not an item change. |
| Projectile Launch System (Edgerunners) | MOD-OFFICIAL | none in Foundry | Can take a Power Rebuild. Rule only. |
| Exotic Bodysculpting (Core) | MOD-CORE | none in Foundry | No max-Humanity loss; free at character creation. Rule only. |
| Medium Armorjack (Core) | MOD-CORE | `Medium Armorjack (Body)`, `(Head)` | Armor penalty reduced by 1. |

## Ammo (6)

| Item | Tag | Notes |
|---|---|---|
| HEAP | NEW | Rocket, ignores SP 13 or lower. |
| Bunker Buster | NEW | Rocket, +4d6 to cover. |
| Sabot Ammunition | NEW | Bullets and Slugs, ignores SP 11 or lower. Related to Corgo's HVAP Ammunition, but the rules differ. |
| Subsonic Ammunition | MOD-CORGO | Corgo's: Bullets and Slugs, −2 to hear a Single Shot. Bontari's: Bullets only, stealth kill on SP 11 or lower within 6 m. Same cost (40eb for 10). |
| Shrapnel Arrows | INCOMPLETE | No cost. |
| Grenade Arrows | INCOMPLETE | Name only. |

## Apps (12, plus a rules note)

The tab opens with a rule: apps run on a Neuroport or an Agent and do nothing without one.

| Item | Tag | Mechanic |
|---|---|---|
| Big SAAI | NEW | +2 Library Search |
| RunWay | NEW | +1 Wardrobe & Style (+2 conditional) |
| Rossetta Lens™ | NEW | Translation, no bonus |
| Ask Allen™ | NEW | +1 to every skill with "Tech" in its name |
| BlackMarketNC | NEW | +2 Streetwise, gated by Reputation |
| Anyware StudioPro | NEW | +2 Photography/Film; Image Enhance while still |
| DeeJay (Premium) | NEW | Reroll 1s on a party's Humanity roll |
| Night City Times | LORE | |
| bart.mos | LORE | A website, requires Netrunner Rank 1 |
| NightZooCity.web | LORE | |
| WayBack.archive/ButterflyCooking | LORE | |
| CandyVan | LORE | |

## Armor (4)

| Item | Tag | Notes |
|---|---|---|
| Spectre HUD Helmet | NEW | SP 11, bundles cybereye options and gear. The sheet spells it both "Spectre" and "Specture". |
| Specture Stealth Suit | NEW | SP 4, body only, optical cloak. |
| CyberMOD Helmet | NEW (built on Light Armorjack (Head)) | TUped to SP 12, plus 3 option slots. |
| NUSAF Pilot Helmet | NEW (built on Light Armorjack (Head)) | SP 12, 2 slots, pre-installed options, +2 Pilot Air Vehicle. |

## Attachments (6)

| Item | Tag | Notes |
|---|---|---|
| Bipod | MOD-CORGO | Corgo's: all ranged weapons, Mounted, +1 to all attacks. Bontari's: two-handed Shoulder Arms or Heavy Weapons guns only, +1 to Aimed Shot, Autofire, and Suppressive Fire. |
| Reflex Sight | COPY-CORGO | Same rules text and cost as Corgo's; only "Fits" narrows to non-thrown weapons. Don't rebuild it; point to Corgo's. |
| Flashlight Rail | NEW | Takes no attachment slot. |
| Superchrome Coating | NEW | A weapon version of the core's Superchrome® Covering; wording similar to Corgo's Fashionista mod. |
| Anti-Drone Smart Scope | NEW | |
| Militech SuperFlex Steel Limbs (WIP) | INCOMPLETE | Marked WIP, no cost. Depends on Corgo's Reinforced String and a "Kyudo Hassetsu" bonus that is not in Corgo's document. |

## Cyberware (31)

| Item | Tag | Notes |
|---|---|---|
| Zetatech Kyber Foundationware | NEW ⚠ | Cost "Varies". |
| Rosetta Stone PolyGlot | NEW | Chipware |
| Kiroshi Mk. II's | NEW (built on Cybereye + Image Enhance) | |
| Rocklin Audiomaster | NEW (built on Cyberaudio Suite + AudioVox) | 5 slots instead of the core's 3 |
| Syn-Lungs | MOD-CORGO | Corgo's: 250eb, Clinic, 1d6. Bontari's: 500eb, Hospital, 2d6, +1 MOVE when paired with Syn-Heart. |
| Syn-Heart | NEW | Pairs with Syn-Lungs |
| Lynx Paws | MOD-CORGO | Corgo's: 1,000eb, Clinic, 1d6, 2 slots, +2/+4. Bontari's: 500eb, Hospital, 2d6, +2 at half MOVE. |
| Advanced Neural Matrix | NEW | Different from Corgo's Advanced Neural Link. |
| NovelTech Corvette Cyberlegs | NEW (built on Cyberleg + Skate Foot) | |
| Arasaka Judoka Cyberarms | NEW (built on Cyberarm) | |
| Kendachi/Rocklin Kensei Cyberarms | NEW (built on Cyberarm) | |
| Rocklin Augmentics Skystrikers | NEW (built on Cyberarm) | The pairing bonus names Corgo's "Rocklin Aug. Skydrivers" (an alternative cyberleg in his document). |
| Rocklin Augmentics Skysmashers | NEW (built on Cyberarm) | Same text as Skystrikers apart from the skill and cost. |
| Carolli/Rocklin Tesoro Cyberarms | NEW (built on Cyberarm + Techscanner + Superchrome Covering) | |
| Panzer-fists | NEW | |
| Rocklin Wallcrawler MagLegs | NEW (built on Cyberleg + Grip Foot) | |
| Zhirafa/Rocklin Earthshaker Cyberlegs | NEW (built on Cyberleg) | |
| Militech Siege Legs | NEW (built on Cyberleg) | |
| Ballistic Coprocessor | MOD-CORGO | Same cost, install, and Humanity Loss as Corgo's. Corgo's: +1 to Ricochet Attacks from Power Rebuilds. Bontari's: the ricochet penalty drops from −4 to −2. Missed by the first name pass; caught by the build's name check. |
| Secondary Heart | NEW | Same idea as Corgo's Second Heart, different rules. |
| Daimler-Benz Nachtreiher Linear Frame | NEW | Two forms, external (gear) and internal (cyberware), like the core's frames. |
| Repair Nanites | NEW ⚠ | Humanity Loss "NA". |
| Arasaka Ozukumi Sx | NEW | |
| Self-ICE Pykrete Upgrade | NEW | Enhances Self-ICE, which Foundry lacks; Corgo's allowlist already covers it. Its first sentence matches Corgo's Firewall Port. |
| Self-ICE Canary Upgrade | NEW | |
| Self-ICE Hyōheki Upgrade | NEW | |
| Self-ICE Permafrost Upgrade | NEW | |
| Endocrine Regulator | NEW | |
| Popup Targeting Laser | NEW | |
| FBC Experimental Shimmer Coating | NEW ⚠ | No cost, install, or Humanity Loss. |
| Militech Fortress Popup Shield | NEW | A bigger version of the core's Popup Shield. |

## Sandevistans (11), all NEW (built on the core's Sandevistan)

Dynalar; Zetatech; Kendachi; Militech; QianT "Warp Dancer"; Fuyutsuki "Uzushio"; Militech "Falcon"; Arasaka
"Kagekaze"; Militech "Apogee"; Arasaka "Seiryu"; Militech Experimental "Zenith".

- **Name clashes with Corgo.** "Warp Dancer", "Falcon", and "Apogee" are also Corgo's Sandevistan *Operating
  Systems*. "Zenith" is also a Corgo weapon attachment.
- **Copied text.** Uzushio's second Secondary Effect is the action list from Corgo's QianT 'Warp Dancer' OS, word for word.
- ⚠ The Dynalar's note says "Zetatech Sandevistan". The Seiryu's note says "Apogee". One Uzushio line is
  unfinished ("Conditional, mostly for technical stuff?)"). The Zenith costs "LOL".

## Drugs (2)

Spice (NEW) and Nicotine (NEW, three quality tiers with one shared Secondary Effect).

## Invented Tech Upgrades (9), all NEW

Dual-Chip (Skill Chip); Ultra-light Furniture Kit; Optimized Popup; Tech Rebuild: Overcharge; Smart Rebuild:
Overclock; Power Rebuild: Overtuning; Auto-Doc Bodyweight Injector (on Bodyweight AutoInjector); Stun Bunny;
IR/UV Sniping Scope (Sniping Scope plus Infrared Nightvision Scope; Foundry has no UV scope).

These are processes applied to an existing item, not items you buy. Each one names the item it applies to.

## Gear (3), all NEW

Delayed Super-Biotoxin (poison); UV Flashlight; Electromagnetic Shield (25 HP shield).

## HQ Upgrades (2), RULE

Morale Boost X+: Outdoor Pet Area; Armory.

## Weapons (3), all NEW

| Item | Notes |
|---|---|
| Kinetic Impact Gauntlets | Brawling, minimum 3d6, uses its own blank shells. |
| Hello Cutie Kitty Bap | ⚠ An "Exotic shotgun" with a Power Rebuild, 5 rounds, but no damage, ROF, or hands listed. |
| Battleboot | ⚠ Listed as a weapon, but works as a worn container for 2 cyberleg options. |
