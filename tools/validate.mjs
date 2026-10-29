// Read the compiled LevelDB packs back and check every item against a snapshot of the CPR 0.92.4 schema
// (tools/cpr-0.92.4-reference.json, copied from corgo-77-module), so no CPR checkout is needed.
// Usage: node tools/validate.mjs dist/bontari-homebrew
import { ClassicLevel } from "classic-level";
import fs from "node:fs";

const DIST = process.argv[2];
if (!DIST) throw new Error("usage: node tools/validate.mjs <module dist>");
const REF = JSON.parse(fs.readFileSync(new URL("./cpr-0.92.4-reference.json", import.meta.url)));
const CORGO = JSON.parse(fs.readFileSync(new URL("./corgo-77-names.json", import.meta.url)));

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

// An item named like a core or Corgo's 77 item would be mistaken for it, which is what the
// "(Bontari Edition)" suffix is for.
const taken = new Map([...REF.itemNames.map((n) => [n.toLowerCase(), "Cyberpunk RED - Core 0.92.4"]),
                       ...CORGO.itemNames.map((n) => [n.toLowerCase(), "Corgo's 77 Collection"])]);
const cwRef = new Set(REF.cyberwareKeys), bonusKeys = new Set(REF.bonusKeys);
const errors = [], counts = {}, seen = new Map();
const manifest = JSON.parse(fs.readFileSync(`${DIST}/module.json`));

for (const pack of manifest.packs.filter((p) => p.type === "Item")) {
  const docs = await readPack(`${DIST}/${pack.path}`);
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

    if (d.type !== "cyberware") { e(`no checks for type ${d.type} yet`); continue; }
    const keys = new Set(flat(s));
    for (const k of cwRef) if (!keys.has(k)) e(`missing ${k}`);
    for (const k of keys) if (!cwRef.has(k)) e(`unexpected field ${k}`);
    if (!REF.cyberwareTypes.includes(s.type)) e(`cyberware type ${s.type}`);
    if (!REF.cyberwareInstallList.includes(s.installLocation)) e(`installLocation ${s.installLocation}`);
    if (!["always", "toggled", "installed"].includes(s.usage)) e(`usage ${s.usage} (cyberware allows always/toggled/installed)`);
    if (s.installedItems.slots > 0 && !s.installedItems.allowed) e("provides slots but installs are not allowed");
    for (const n of [s.size, s.installedItems.slots, s.humanityLoss.static])
      if (!Number.isInteger(n) || n < 0) e(`bad number ${n}`);
    // A plain dice formula or a number only: CPR reads roll.terms[0].results to draw the humanity-loss roll
    // card, and a function term (ceil(), floor()) has no .results and throws.
    if (!/^(\d+|\d*d\d+)$/.test(s.humanityLoss.roll)) e(`HL roll ${s.humanityLoss.roll} is not a plain dice formula`);
    for (const eid of d.effects) {
      const ef = effects.get(`!items.effects!${d._id}.${eid}`);
      if (!ef) { e(`effect ${eid} not stored`); continue; }
      for (const k of REF.effectKeys) if (!(k in ef) && k !== "_key") e(`effect missing ${k}`);
      ef.changes.forEach((c, i) => {
        if (!bonusKeys.has(c.key) && !/^system\.stats\.\w+\.value$/.test(c.key)) e(`effect key ${c.key}`);
        if (![2, 3, 4, 5].includes(c.mode) || Number.isNaN(Number(c.value))) e(`effect change ${c.key} mode/value`);
        if (!ef.flags["cyberpunk-red-core"]?.changes?.cats?.[i]) e(`effect change ${i} has no category`);
      });
      const sit = Object.values(ef.flags["cyberpunk-red-core"]?.changes?.situational ?? {});
      if (s.usage === "toggled" && !sit.every((x) => x.isSituational)) e("toggled cyberware's effect should be situational");
    }
  }
}
console.log(`checked: ${JSON.stringify(counts)}`);
console.log(`names checked against ${REF.itemNames.length} core and ${CORGO.itemNames.length} Corgo's 77 items`);
console.log(errors.length ? errors.join("\n") : "no schema problems found");
process.exit(errors.length ? 1 : 0);
