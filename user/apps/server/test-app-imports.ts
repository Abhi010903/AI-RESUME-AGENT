import { performance } from "node:perf_hooks";

const modules = [
    "hono",
    "hono/body-limit",
    "hono/compress",
    "@hono/node-server/conninfo",
    "@reactive-resume/api/features/storage/transport",
    "@reactive-resume/env/server",
    "@reactive-resume/mcp",
    "@reactive-resume/utils/app-paths",
    "./src/mcp/handler",
    "./src/openapi/handler",
    "./src/openapi/metadata",
    "./src/rpc/handler",
    "./src/static/agent-skills",
    "./src/static/resume-card",
    "./src/static/resume-page",
    "./src/static/schema",
    "./src/static/seo",
    "./src/static/uploads",
    "./src/static/web",
    "./src/http/alias",
    "./src/http/app-links",
    "./src/http/auth",
    "./src/http/career-jobs",
    "./src/http/custom-domain",
    "./src/http/health",
    "./src/http/public-resume-download",
    "./src/http/resume-pdf",
];

for (const mod of modules) {
    const t0 = performance.now();
    process.stdout.write(`Importing ${mod}... `);
    try {
        await import(mod);
        const elapsed = (performance.now() - t0).toFixed(0);
        console.log(`OK (${elapsed}ms)`);
    } catch (err: any) {
        console.log(`FAIL: ${err.message}`);
    }
}
console.log("All modules checked!");
