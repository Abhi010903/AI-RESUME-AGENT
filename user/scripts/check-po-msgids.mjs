import fs from "node:fs";
import path from "node:path";

function getDistinctMsgids(dir) {
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.po'));
  const msgids = new Map();
  for (const f of files) {
    const content = fs.readFileSync(path.join(dir, f), 'utf8');
    const singleMatches = content.matchAll(/^msgid\s+"([^"]+)"/gm);
    for (const m of singleMatches) {
      const text = m[1];
      if (/reactive\s*resume|amruth/i.test(text)) {
        msgids.set(text, (msgids.get(text) || 0) + 1);
      }
    }
    const multiMatches = content.matchAll(/^msgid\s+""\r?\n((?:^"[^"]*"\r?\n)+)/gm);
    for (const m of multiMatches) {
      const text = m[1].split(/\r?\n/).filter(Boolean).map(l => l.replace(/^"|"$/g, '')).join('');
      if (/reactive\s*resume|amruth/i.test(text)) {
        msgids.set(text, (msgids.get(text) || 0) + 1);
      }
    }
  }
  return msgids;
}

console.log("=== WEB DISTINCT MSGIDS ===");
for (const [id, count] of getDistinctMsgids("user/apps/web/locales")) {
  console.log(`(${count} files): ${id}`);
}

console.log("\n=== MOBILE DISTINCT MSGIDS ===");
for (const [id, count] of getDistinctMsgids("user/apps/mobile/locales")) {
  console.log(`(${count} files): ${id}`);
}
