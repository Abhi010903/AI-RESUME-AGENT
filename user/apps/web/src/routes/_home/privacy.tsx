import { createFileRoute } from "@tanstack/react-router";
import { PrivacyPage } from "@/features/legal/privacy-page";
import { getPageTitle } from "@/libs/seo";

export const Route = createFileRoute("/_home/privacy")({
	component: PrivacyPage,
	head: () => ({
		meta: [
			{ title: getPageTitle("Privacy Policy") },
			{
				name: "description",
				content:
					"Privacy Policy for AI Resume Agent — transparent candidate data ownership, local storage, security, and AI model integration policies.",
			},
		],
	}),
});
