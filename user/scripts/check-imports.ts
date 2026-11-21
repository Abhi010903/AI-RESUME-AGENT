import { performance } from "node:perf_hooks";

async function test(name: string, fn: () => Promise<unknown>) {
    const start = performance.now();
    try {
        await fn();
        const elapsed = (performance.now() - start).toFixed(2);
        console.log(`[OK] ${name} (${elapsed}ms)`);
    } catch (err) {
        console.error(`[FAIL] ${name}:`, err);
    }
}

console.log("Checking individual imports...");
await test("env/server", async () => import("@reactive-resume/env/server"));
await test("db/client", async () => import("@reactive-resume/db/client"));
await test("auth/config", async () => import("@reactive-resume/auth/config"));
await test("api/routers", async () => import("@reactive-resume/api/routers"));
await test("mcp", async () => import("@reactive-resume/mcp"));
await test("apps/server/src/http/app", async () => import("../apps/server/src/http/app"));
console.log("All import tests completed!");
