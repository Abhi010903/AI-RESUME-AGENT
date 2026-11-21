import fs from "node:fs";
import path from "node:path";

const root = "C:/Coding/Projects/AI-RESUME-AGENT";
const ignoreDirs = new Set([
  "node_modules",
  ".git",
  ".turbo",
  "dist",
  "dist-prerender",
  ".postgres18_data",
  ".vite-temp",
  "company", // Strict boundary: NEVER modify or touch company/
]);

const reactivePatterns = [
  { name: "Reactive Resume", regex: /Reactive\s+Resume/i },
  { name: "reactive-resume", regex: /reactive-resume/i },
  { name: "reactive_resume", regex: /reactive_resume/i },
  { name: "reactive.resume", regex: /reactive\.resume/i },
  { name: "rxresu.me", regex: /rxresu\.me/i },
  { name: "rx.cv", regex: /rx\.cv/i },
  { name: "github-upstream", regex: /github\.com\/reactive-resume/i },
  { name: "discord-upstream", regex: /discord\.(gg|com\/invite)\/[a-z0-9]+/i },
  { name: "docs-upstream", regex: /docs\.rxresu\.me/i },
];

const amruthPatterns = [
  { name: "Amruth Pillai", regex: /Amruth\s+Pillai/i },
  { name: "amruth@rxresu.me", regex: /amruth@rxresu\.me/i },
  { name: "amruthpillai.com", regex: /amruthpillai\.com/i },
  { name: "amruth", regex: /\bamruth\b/i },
  { name: "github-amruth", regex: /github\.com\/AmruthPillai/i },
];

const reactiveMatches = [];
const amruthMatches = [];

function walk(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    return;
  }
  for (const entry of entries) {
    if (ignoreDirs.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      // Skip binary media or map files
      if (['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.docx', '.map', '.zip', '.woff', '.woff2', '.ttf'].includes(ext)) {
        continue;
      }
      try {
        const content = fs.readFileSync(full, "utf8");
        const lines = content.split("\n");
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          for (const p of reactivePatterns) {
            if (p.regex.test(line)) {
              reactiveMatches.push({
                file: path.relative(root, full).replace(/\\/g, "/"),
                line: i + 1,
                matchedTerm: p.name,
                text: line.trim()
              });
              break;
            }
          }
          for (const p of amruthPatterns) {
            if (p.regex.test(line)) {
              amruthMatches.push({
                file: path.relative(root, full).replace(/\\/g, "/"),
                line: i + 1,
                matchedTerm: p.name,
                text: line.trim()
              });
              break;
            }
          }
        }
      } catch (err) {}
    }
  }
}

walk(root);

console.log("=== SCAN RESULTS ===");
console.log(`Total Reactive Resume Matches: ${reactiveMatches.length}`);
console.log(`Total Amruth Matches: ${amruthMatches.length}`);

// Group by file
const reactiveByFile = {};
for (const m of reactiveMatches) {
  reactiveByFile[m.file] = (reactiveByFile[m.file] || 0) + 1;
}

const amruthByFile = {};
for (const m of amruthMatches) {
  amruthByFile[m.file] = (amruthByFile[m.file] || 0) + 1;
}

fs.writeFileSync("user/scripts/scan_reactive_raw.json", JSON.stringify(reactiveMatches, null, 2));
fs.writeFileSync("user/scripts/scan_amruth_raw.json", JSON.stringify(amruthMatches, null, 2));
fs.writeFileSync("user/scripts/scan_summary.json", JSON.stringify({
  totalReactive: reactiveMatches.length,
  totalAmruth: amruthMatches.length,
  reactiveFilesCount: Object.keys(reactiveByFile).length,
  amruthFilesCount: Object.keys(amruthByFile).length,
  reactiveByFile,
  amruthByFile
}, null, 2));

console.log(`Unique files with Reactive matches: ${Object.keys(reactiveByFile).length}`);
console.log(`Unique files with Amruth matches: ${Object.keys(amruthByFile).length}`);
