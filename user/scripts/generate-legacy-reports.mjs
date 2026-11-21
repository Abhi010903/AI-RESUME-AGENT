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
  "company", // Boundary
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
      if (['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.docx', '.map', '.zip', '.woff', '.woff2', '.ttf'].includes(ext)) {
        continue;
      }
      // Skip our own scan/report output files to avoid self-counting
      if (entry.name.startsWith("scan_") || entry.name.startsWith("report_") || entry.name === "audit-report.json") {
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

function categorizeReactive(m) {
  const f = m.file;
  const t = m.text;

  // Legal Attribution
  if (f === "README.md" || f === "user/README.md" || f === "user/LICENSE" || f === "user/SECURITY.md" || f.includes("legal/license") || f.includes("legal/privacy-page.tsx") || (f.includes("sections.tsx") && t.includes("MIT License"))) {
    return { category: "F", name: "Legal Attribution & MIT License", rationale: "Legally required MIT copyright attribution and open source license preservation" };
  }

  // Format Compatibility
  if (t.includes("reactive-resume-json") || t.includes("reactive-resume-v4-json") || t.includes("reactive-resume-cover-letter") || t.includes("Reactive Resume or JSON Resume file") || t.includes("Reactive Resume export") || t.includes("Reactive Resume JSON")) {
    return { category: "E", name: "Import/Export Format Compatibility", rationale: "Required to allow users to import legacy Reactive Resume JSON files and exports" };
  }

  // Internal Package Namespace
  if (t.includes("@reactive-resume/")) {
    return { category: "C", name: "Internal Package Namespace", rationale: "Internal pnpm workspace package identifiers (@reactive-resume/*) preserved per architectural safety rules" };
  }

  // Database Schema & Storage
  if (f.includes("migrations/") || f.includes("schema/") || t.includes("reactive-resume:unsaved:") || t.includes("reactive-resume:account")) {
    return { category: "D", name: "Database Schema & Internal Storage Keys", rationale: "Drizzle migrations, schema constants, and localStorage keys to prevent session/draft corruption" };
  }

  // Lockfiles & Dependencies
  if (f.endsWith("pnpm-lock.yaml") || f.includes("package.json") && t.includes("workspace:*")) {
    return { category: "G", name: "Dependencies & Workspace Lockfiles", rationale: "pnpm lockfile resolution and dependency tree mapping" };
  }

  // Repository & Container Metadata
  if (f === "user/package.json" || f.includes("Dockerfile") || f.includes(".github/") || f.includes("cloudron/")) {
    return { category: "B", name: "Repository & Build Metadata", rationale: "Root package name, git repository references, or container build metadata" };
  }

  // Translations / Catalogs
  if (f.endsWith(".po")) {
    return { category: "T", name: "Localization Catalogs", rationale: "Lingui message extraction references or historical locale definitions" };
  }

  return { category: "A", name: "Other / User-Facing", rationale: "Under review" };
}

function categorizeAmruth(m) {
  const f = m.file;
  const t = m.text;

  // Legal Attribution
  if (f === "README.md" || f === "user/README.md" || f === "user/LICENSE" || f === "user/SECURITY.md" || f.includes("legal/license") || f.includes("legal/privacy-page.tsx") || (f.includes("sections.tsx") && t.includes("MIT License")) || (f.includes("seo.ts") && t.includes("MIT License"))) {
    return { category: "F", name: "Legal Attribution & MIT License", rationale: "Mandatory MIT copyright attribution to original author Amruth Pillai (legally required)" };
  }

  // Test Fixtures & Sample data
  if (f.includes(".test.") || f.includes("tests/")) {
    return { category: "T", name: "Test Fixtures", rationale: "Historical test cases / assertions for domain suggestions or catalog diffs" };
  }

  // Technical runbooks or changelogs
  if (f.includes("changelog/") || f.includes("runbooks/")) {
    return { category: "H", name: "Historical Documentation & Runbooks", rationale: "Archived upstream release history and maintainer runbooks" };
  }

  return { category: "F", name: "Legal Attribution", rationale: "Original upstream creator credit preserved under MIT license" };
}

const reactiveCategorized = {};
for (const m of reactiveMatches) {
  const cat = categorizeReactive(m);
  reactiveCategorized[cat.name] = reactiveCategorized[cat.name] || [];
  reactiveCategorized[cat.name].push({ ...m, rationale: cat.rationale });
}

const amruthCategorized = {};
for (const m of amruthMatches) {
  const cat = categorizeAmruth(m);
  amruthCategorized[cat.name] = amruthCategorized[cat.name] || [];
  amruthCategorized[cat.name].push({ ...m, rationale: cat.rationale });
}

fs.writeFileSync("user/scripts/report_reactive_categorized.json", JSON.stringify(reactiveCategorized, null, 2));
fs.writeFileSync("user/scripts/report_amruth_categorized.json", JSON.stringify(amruthCategorized, null, 2));

console.log("=== COMPLETED CATEGORIZATION ===");
console.log("Reactive Resume categories:");
for (const [k, v] of Object.entries(reactiveCategorized)) {
  console.log(`- ${k}: ${v.length} occurrences across ${new Set(v.map(x => x.file)).size} files`);
}
console.log("\nAmruth Pillai categories:");
for (const [k, v] of Object.entries(amruthCategorized)) {
  console.log(`- ${k}: ${v.length} occurrences across ${new Set(v.map(x => x.file)).size} files`);
}
