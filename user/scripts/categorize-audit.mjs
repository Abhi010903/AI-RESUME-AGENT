import fs from "node:fs";
import path from "node:path";

const root = "C:/Coding/Projects/AI-RESUME-AGENT/user";
const ignore = new Set(["node_modules", ".git", "dist", "dist-prerender", ".postgres18_data", "reports", ".turbo"]);

const patterns = {
  reactive_resume_title: /Reactive\s+Resume/i,
  reactive_resume_hyphen: /reactive-resume/i,
  rxresume_domain: /rxresu\.me/i,
  rxcv_domain: /rx\.cv/i,
  github_upstream: /github\.com\/(reactive-resume|AmruthPillai)/i,
  discord_upstream: /discord\.gg/i,
  docs_upstream: /docs\.rxresu\.me/i,
  email_upstream: /amruth@rxresu\.me/i,
};

const results = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ignore.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase();
      if (['.ts', '.tsx', '.js', '.jsx', '.json', '.html', '.md', '.yml', '.yaml', '.toml', '.env', '.example', '.webmanifest', '.css'].includes(ext) || entry.name.startsWith('.')) {
        try {
          const content = fs.readFileSync(full, 'utf8');
          const lines = content.split('\n');
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            for (const [pname, p] of Object.entries(patterns)) {
              if (p.test(line)) {
                results.push({
                  file: path.relative(root, full).replace(/\\/g, '/'),
                  line: i + 1,
                  type: pname,
                  text: line.trim()
                });
                break;
              }
            }
          }
        } catch (e) {}
      }
    }
  }
}

walk(root);

console.log("Total repository occurrences found:", results.length);

const catA = [];
const catB = [];
const catC = [];
const catD = [];

for (const r of results) {
  const f = r.file.toLowerCase();
  const t = r.text;

  // A: Legally required notices & author attribution
  if (
    f === "license" ||
    f.endsWith("/license") ||
    f.includes("security.md") ||
    t.includes("Amruth Pillai") ||
    t.includes("originally developed as Reactive Resume") ||
    t.includes("Copyright (c) 2026 Amruth Pillai") ||
    (f.includes("privacy") && t.includes("Reactive Resume"))
  ) {
    catA.push(r);
    continue;
  }

  // C: Third-party dependencies & registries & lockfiles & docker / CI & root package.json
  if (
    f.includes("pnpm-lock.yaml") ||
    f.includes("dockerfile") ||
    f.includes("compose") ||
    f.includes("cloudron") ||
    f.includes(".github/") ||
    f.includes("context7.json") ||
    f.includes("crowdin.yml") ||
    (f.endsWith("package.json") && (t.includes('"name":') || t.includes('"repository":') || t.includes('"description":') || t.includes('"email":') || t.includes('"url":') || t.includes("@reactive-resume/") || t.includes("./reactive-resume")))
  ) {
    catC.push(r);
    continue;
  }

  // B: Internal technical identifiers & compatibility references:
  // - Internal package imports: @reactive-resume/*
  // - Database schemas, tables, migrations, storage keys, IndexedDB, BroadcastChannel
  // - Import file format compatibility (support for importing Reactive Resume JSON / v4 files)
  // - Agent skills plugin paths and internal developer instructions
  // - Test fixtures, mocks, e2e test files
  // - Legacy mobile app configs / locales
  // - Upstream docs directory (Mintlify documentation files)
  if (
    t.includes("@reactive-resume/") ||
    f.startsWith("docs/") ||
    f.includes("plugins/reactive-resume/") ||
    f.includes("migrations/") ||
    f.includes(".test.") ||
    f.includes(".spec.") ||
    f.includes("test-fixtures") ||
    f.includes("tool-annotations.md") ||
    f.includes("audit-report") ||
    f.includes("scripts/") ||
    f.includes("tests/e2e/") ||
    f.includes("apps/mobile/") ||
    f.includes("packages/dsh-plugin/") ||
    f.includes("tooling/") ||
    f.includes("knip.json") ||
    f.includes("turbo.json") ||
    f.includes("tsconfig") ||
    f.includes("playwright.config") ||
    f.includes(".claude-plugin/") ||
    f.includes(".agents/") ||
    f.includes("patches/") ||
    f.startsWith(".git") ||
    f.endsWith("design.md") ||
    f.endsWith("product.md") ||
    f.endsWith("agents.md") ||
    f.endsWith("glossary.md") ||
    f.endsWith("coding_standards.md") ||
    f.includes("capture-helper/popup.js") ||
    f.includes("packages/api/src/features/statistics/") ||
    f.includes("packages/api/src/features/resume/fixtures/") ||
    t.includes('"reactive-resume-json"') ||
    t.includes("'reactive-resume-json'") ||
    t.includes('"reactive-resume-v4-json"') ||
    t.includes("'reactive-resume-v4-json'") ||
    t.includes("parseReactiveResumeV4JSON") ||
    t.includes("reactive-resume:unsaved") ||
    t.includes("reactive-resume:account") ||
    t.includes("reactive-resume:email") ||
    t.includes("reactive-resume:pending-request") ||
    t.includes("reactive-resume:feedback-link") ||
    t.includes("reactive-resume:pdf-download") ||
    t.includes("me.rxresu") ||
    t.includes("rxresu.me/auth/native-callback") ||
    t.includes("The Reactive Resume apps register their own client") ||
    t.includes("reactive-resume-application-packet") ||
    t.includes("reactive-resume-cover-letter") ||
    t.includes("const DB = \"reactive-resume\"") ||
    t.includes("enum: [\"reactive-resume\"]") ||
    t.includes("plugins/reactive-resume/skills") ||
    t.includes("FIRST_PARTY_APP_CALLBACK") ||
    t.includes("domains.rx.cv") ||
    t.includes("https://rx.cv") ||
    t.includes("rx.cv/john") ||
    t.includes("docs.rxresu.me/guides") ||
    (f.includes("import") && t.includes("Reactive Resume")) ||
    (f.includes("seo.ts") && t.includes("Reactive Resume JSON")) ||
    (f.includes("email-text.ts") && t.includes("Reactive Resume")) ||
    (f.includes("data.ts") && t.includes("Made with Reactive Resume")) ||
    (f.includes("applications.ts") && t.includes("// A tracked job application")) ||
    (f.includes("redis.ts") && t.includes('"reactive-resume"')) ||
    (f.includes("firecrawl.ts") && t.includes('"_reactive-resume"')) ||
    (f.includes("kit.tsx") && t.includes("rxresu.me/alex/product-designer")) ||
    (f.includes("document.ts") && t.includes("/** The Reactive Resume mark")) ||
    (f.includes("access.ts") && t.includes("reactive-resume:")) ||
    (f.includes("tool-meta.ts") && t.includes("AI Resume Agent or Reactive Resume"))
  ) {
    catB.push(r);
    continue;
  }

  // Anything remaining is candidate for D
  catD.push(r);
}

console.log("Category A (Legally required):", catA.length);
console.log("Category B (Internal technical & compatibility):", catB.length);
console.log("Category C (Dependencies & lockfile):", catC.length);
console.log("Category D (Remaining candidate files to inspect):", catD.length);

if (catD.length > 0) {
  console.log("\n--- Items in Category D: ---");
  for (const item of catD) {
    console.log(`${item.file}:${item.line} [${item.type}] -> ${item.text}`);
  }
} else {
  console.log("\n✅ Zero remaining user-facing Reactive Resume references in Category D!");
}
