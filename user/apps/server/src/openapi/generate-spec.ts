import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

async function generateOpenApiDocumentation(
	target = fileURLToPath(new URL("../../../../docs/spec.json", import.meta.url)),
) {
	const packageJson = JSON.parse(await readFile(new URL("../../../../package.json", import.meta.url), "utf8")) as {
		version: string;
	};
	const appUrl = (process.env.APP_URL ?? "http://localhost:3000").replace(/\/+$/, "");
	process.env.APP_URL ??= appUrl;
	process.env.DATABASE_URL ??= "postgresql://resume_agent:resume_agent@localhost:5432/resume_agent";
	process.env.AUTH_SECRET ??= "documentation-generation-isolated-process-only";
	const { generateOpenApiSpec } = await import("./generator");
	const spec = await generateOpenApiSpec({ appUrl, version: packageJson.version });
	await writeFile(target, `${JSON.stringify(spec, null, "\t")}\n`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
	await generateOpenApiDocumentation(process.argv[2]);
}
