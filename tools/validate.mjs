// Read the compiled LevelDB packs back and check every document against a snapshot of the CPR 0.92.4 schema
// (tools/cpr-0.92.4-reference.json, copied from corgo-77-module), so no CPR checkout is needed. The per-type
// checks are corgo-77-module's.
// Usage: node tools/validate.mjs dist/bontari-homebrew
import { ClassicLevel } from "classic-level";
import fs from "node:fs";

const DIST = process.argv[2];
if (!DIST) throw new Error("usage: node tools/validate.mjs <module dist>");
const REF = JSON.parse(fs.readFileSync(new URL("./cpr-0.92.4-reference.json", import.meta.url)));
const CORE = JSON.parse(fs.readFileSync(new URL("./cpr-0.92.4-items.json", import.meta.url)));
const CORGO = JSON.parse(fs.readFileSync(new URL("./corgo-77-names.json", import.meta.url)));
const ABSENT = new Set(Object.keys(JSON.parse(fs.readFileSync(new URL("../text/enhance_targets.json", import.meta.url))).absent));

async function readPack(dir) {
  const db = new ClassicLevel(dir, { valueEncoding: "json" });
  const out = [];
  for await (const [k, v] of db.iterator()) out.push([k, v]);
  await db.close();
  return out;
}
const flat = (o, p = "") => Object.entries(o).flatMap(([k, v]) => k === "description" ? [] :
  v && typeof v === "object" && !Array.isArray(v) && Object.keys(v).length && k !== "ammoData" ? flat(v, `${p}${k}.`) : [p + k]);

// Foundry strips tags to build item-list summaries, tooltips and chat previews, and a block-level tag with no
// whitespace around it welds the words either side of it ("(Very Expensive)Type: Neuralware").
const BLOCK_TAG = /<\/?(?:br|p|div|ul|ol|li|table|thead|tbody|tr|td|th|h[1-6])\b[^>]*>/gi;
function weldedText(html) {
  const out = [];
  for (const m of html.matchAll(BLOCK_TAG)) {
    const before = html[m.index - 1] ?? " ";
    const after = html[m.index + m[0].length] ?? " ";
    if (!/\s/.test(before) && !/\s/.test(after)) out.push(`${before}${m[0]}${after}`);
  }
  return out;
}

// Field sets per item type: the reference snapshot's, which were read from the 0.92.4 data models.
const KEYS = { cyberware: REF.cyberwareKeys, weapon: REF.weaponKeys, itemUpgrade: REF.upgradeKeys, ammo: REF.ammoKeys,
               armor: REF.armorKeys, gear: REF.gearKeys, drug: REF.drugKeys };
// Effect keys: the reference list plus every key the system's own items use (it lacks a few, such as
// bonuses.playInstrument on the core AudioVox).
const bonusKeys = new Set([...REF.bonusKeys, ...CORE.items.flatMap((i) => i.effects.flatMap((e) => e.changes.map((c) => c.key)))]);
const skills = new Set(REF.skills);
// An item named like a core or Corgo's 77 item would be mistaken for it, which is what the
// "(Bontari Edition)" suffix is for.
const taken = new Map([...REF.itemNames.map((n) => [n.toLowerCase(), "Cyberpunk RED - Core 0.92.4"]),
                       ...CORGO.itemNames.map((n) => [n.toLowerCase(), "Corgo's 77 Collection"])]);
const errors = [], counts = {}, seen = new Map(), enhances = [];
const manifest = JSON.parse(fs.readFileSync(`${DIST}/module.json`));

function checkEffects(d, effects, e, s) {
  for (const eid of d.effects) {
    const ef = effects.get(`!items.effects!${d._id}.${eid}`);
    if (!ef) { e(`effect ${eid} not stored`); continue; }
    for (const k of REF.effectKeys) if (!(k in ef) && k !== "_key") e(`effect missing ${k}`);
    ef.changes.forEach((c, i) => {
      if (!bonusKeys.has(c.key) && !/^system\.stats\.(int|ref|dex|tech|cool|will|luck|move|body|emp)\.value$/.test(c.key)) e(`effect key ${c.key}`);
      if (![2, 3, 4, 5].includes(c.mode) || Number.isNaN(Number(c.value))) e(`effect change ${c.key} mode/value`);
      if (!ef.flags["cyberpunk-red-core"]?.changes?.cats?.[i]) e(`effect change ${i} has no category`);
    });
    // A permanent effect must apply exactly while the item is installed; an activated one is a toggle.
    const sit = Object.values(ef.flags["cyberpunk-red-core"]?.changes?.situational ?? {});
    if (d.type === "cyberware" && s.usage === "toggled" && !sit.every((x) => x.isSituational))
      e("toggled cyberware's effect should be situational");
  }
}

for (const pack of manifest.packs) {
  const docs = await readPack(`${DIST}/${pack.path}`);
  if (pack.type === "JournalEntry") {
    for (const [key, j] of docs) {
      if (!key.startsWith("!journal!")) continue;
      counts[`${pack.name}/journal`] = (counts[`${pack.name}/journal`] || 0) + 1;
      const pages = docs.filter(([k]) => k.startsWith(`!journal.pages!${j._id}.`)).map(([, p]) => p);
      if (!pages.length || pages.length !== j.pages.length) errors.push(`${pack.name}/${j.name}: pages not stored`);
      for (const p of pages) {
        const welds = weldedText(p.text?.content ?? "");
        if (welds.length) errors.push(`${pack.name}/${j.name}/${p.name}: text welds when tags are stripped: ${welds[0]}`);
      }
    }
    continue;
  }
  const effects = new Map(docs.filter(([k]) => k.startsWith("!items.effects!")));
  for (const [key, d] of docs) {
    if (!key.startsWith("!items!")) continue;
    const s = d.system, e = (m) => errors.push(`${pack.name}/${d.name}: ${m}`);
    counts[`${pack.name}/${d.type}`] = (counts[`${pack.name}/${d.type}`] || 0) + 1;
    if (key !== `!items!${d._id}`) e("key mismatch");
    if (taken.has(d.name.toLowerCase())) e(`name is already an item in ${taken.get(d.name.toLowerCase())}`);
    if (seen.has(d.name)) e(`name also used in ${seen.get(d.name)}`);
    seen.set(d.name, pack.name);
    const welds = weldedText(s.description?.value ?? "");
    if (welds.length) e(`text welds when tags are stripped: ${welds[0]}`);
    if (!Number.isInteger(s.price.market) || s.price.market < 0) e(`price ${s.price.market}`);
    const ref = KEYS[d.type];
    if (!ref) { e(`unexpected type ${d.type}`); continue; }
    const keys = new Set(flat(s)), refSet = new Set(ref);
    for (const k of refSet) if (!keys.has(k)) e(`missing ${k}`);
    for (const k of keys) if (!refSet.has(k)) e(`unexpected field ${k}`);
    checkEffects(d, effects, e, s);
    const m = /<strong>Enhances:<\/strong>\s*([^<]+)/.exec(s.description.value);
    if (m) enhances.push([`${pack.name}/${d.name}`, m[1].trim()]);

    if (d.type === "cyberware") {
      if (!REF.cyberwareTypes.includes(s.type)) e(`cyberware type ${s.type}`);
      if (!REF.cyberwareInstallList.includes(s.installLocation)) e(`installLocation ${s.installLocation}`);
      if (!["always", "toggled", "installed"].includes(s.usage)) e(`usage ${s.usage} (cyberware allows always/toggled/installed)`);
      if (s.installedItems.slots > 0 && !s.installedItems.allowed) e("provides slots but installs are not allowed");
      if (s.installedItems.allowed && !s.installedItems.allowedTypes.length) e("installs allowed but no allowed types");
      for (const n of [s.size, s.installedItems.slots, s.humanityLoss.static])
        if (!Number.isInteger(n) || n < 0) e(`bad number ${n}`);
      // A plain dice formula or a number only: CPR reads roll.terms[0].results to draw the humanity-loss roll
      // card, and a function term (ceil(), floor()) has no .results and throws.
      if (!/^(\d+|\d*d\d+)$/.test(s.humanityLoss.roll)) e(`HL roll ${s.humanityLoss.roll} is not a plain dice formula`);
    } else if (d.type === "weapon") {
      if (!REF.weaponTypes.includes(s.weaponType)) e(`weaponType ${s.weaponType}`);
      if (!REF.itemQuality.includes(s.quality)) e(`quality ${s.quality}`);
      if (!REF.critFailEffects.includes(s.critFailEffect)) e(`critFailEffect ${s.critFailEffect}`);
      if (!skills.has(s.weaponSkill)) e(`skill ${s.weaponSkill}`);
      if (!/^\d+d6$|^0$/.test(s.damage)) e(`damage ${s.damage}`);
      if (s.dvTable && !REF.coreDvTables.includes(s.dvTable)) e(`dvTable ${s.dvTable}`);
      for (const a of s.ammoVariety) if (!REF.ammoVarieties.includes(a)) e(`ammo ${a}`);
      for (const n of [s.rof, s.handsReq, s.magazine.max]) if (!Number.isInteger(n) || n < 0) e(`bad number ${n}`);
    } else if (d.type === "ammo") {
      if (!REF.ammoVarieties.includes(s.variety)) e(`variety ${s.variety}`);
      if (!REF.ammoTypes.includes(s.type)) e(`ammo type ${s.type}`);
    } else if (d.type === "itemUpgrade") {
      if (!Number.isInteger(s.size) || s.size < 0) e(`size ${s.size}`);
      for (const [k, mod] of Object.entries(s.modifiers)) {
        if (k === "secondaryWeapon") { if (mod.configured) e("unexpected secondary weapon"); continue; }
        if (mod.value !== null && !Number.isInteger(mod.value)) e(`modifier ${k} value ${mod.value}`);
      }
      // An upgrade's effects apply from the inventory whether or not it is installed, so a cyberware
      // enhancement carries none and takes no Option Slot.
      if (s.type === "cyberware" && (s.size !== 0 || d.effects.length)) e("a cyberware enhancement takes no slot and has no effects");
    } else if (d.type === "armor") {
      if (!Number.isInteger(s.penalty) || s.penalty < 0) e(`penalty ${s.penalty}`);
      if (s.isShield ? (s.isBodyLocation || s.isHeadLocation || s.shieldHitPoints.max <= 0) : !(s.isBodyLocation || s.isHeadLocation)) e("location flags");
      if (s.isBodyLocation !== s.bodyLocation.sp > 0 || s.isHeadLocation !== s.headLocation.sp > 0) e("SP doesn't match covered locations");
    } else if (d.type === "gear" || d.type === "drug") {
      if (!REF.usages.includes(s.usage)) e(`usage ${s.usage}`);
      if (d.type === "drug") {
        const names = d.effects.map((id) => effects.get(`!items.effects!${d._id}.${id}`)?.name);
        if (s.consumed !== "None" && !names.includes(s.consumed)) e(`consumed effect ${s.consumed} missing`);
      }
    }
  }
}

// Every "Enhances: X" fact must name something a player can install: a 0.92.4 item, one of this module's or
// Corgo's items, or a parent listed in text/enhance_targets.json as absent from the system.
const known = new Set([...REF.itemNames, ...CORGO.itemNames, ...seen.keys()].map((n) => n.toLowerCase()));
for (const [where, target] of enhances)
  if (!ABSENT.has(target) && !known.has(target.toLowerCase()))
    errors.push(`${where}: enhances "${target}", which is not an item in 0.92.4, Corgo's 77, or this module, and is not in text/enhance_targets.json`);

console.log(`checked: ${JSON.stringify(counts)}`);
console.log(`names checked against ${REF.itemNames.length} core and ${CORGO.itemNames.length} Corgo's 77 items; ${enhances.length} enhancement targets resolved`);
console.log(errors.length ? errors.join("\n") : "no schema problems found");
process.exit(errors.length ? 1 : 0);
