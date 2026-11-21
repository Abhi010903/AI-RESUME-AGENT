import fs from "node:fs";
import path from "node:path";

const rootDir = "C:/Coding/Projects/AI-RESUME-AGENT/user";
const ignoreDirs = new Set(["node_modules", ".git", "dist", "dist-prerender", "reports", ".turbo", ".postgres18_data", "data"]);

const patterns = [
    { name: "rxresu.me", regex: /rxresu\.me/i },
    { name: "AmruthPillai GitHub / URLs", regex: /github\.com\/AmruthPillai/i },
    { name: "Discord links", regex: /discord\.gg/i },
    { name: "Crowdin links", regex: /crowdin\.com/i },
    { name: "App Store / Play Store", regex: /(apps\.apple\.com|play\.google\.com)/i },
    { name: "Reactive Resume in UI / text", regex: /Reactive[\s_-]*Resume/i },
];

const matches = [];

function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
        if (ignoreDirs.has(entry.name)) continue;
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            walk(fullPath);
        } else if (entry.isFile()) {
            // Only check text / source files
            const ext = path.extname(entry.name).toLowerCase();
            if ([".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".html", ".md", ".yml", ".yaml", ".svg", ".webmanifest"].includes(ext)) {
                try {
                    const content = fs.readFileSync(fullPath, "utf8");
                    const lines = content.split("\n");
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i];
                        for (const p of patterns) {
                            if (p.regex.test(line)) {
                                matches.push({
                                    pattern: p.name,
                                    file: path.relative(rootDir, fullPath).replace(/\\/g, "/"),
                                    line: i + 1,
                                    text: line.trim()
                                });
                            }
                        }
                    }
                } catch (e) {
                    // skip unreadable
                }
            }
        }
    }
}

walk(rootDir);

console.log(`Found ${matches.length} matching lines.`);
const byPattern = {};
for (const m of matches) {
    byPattern[m.pattern] = (byPattern[m.pattern] || 0) + 1;
}
console.log("By pattern:", byPattern);

// Group by file
const byFile = {};
for (const m of matches) {
    if (!byFile[m.file]) byFile[m.file] = [];
    byFile[m.file].push(m);
}

fs.writeFileSync("C:/Coding/Projects/AI-RESUME-AGENT/user/scripts/audit-report.json", JSON.stringify({ matches, byFile, byPattern }, null, 2));
console.log(`Report written to user/scripts/audit-report.json (total affected files: ${Object.keys(byFile).length})`);
