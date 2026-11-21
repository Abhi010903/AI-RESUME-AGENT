import type { IconName } from "@reactive-resume/ui/components/icon";
import { t } from "@lingui/core/macro";

/** The project's own pages, under Settings on desktop and as rows on the phone's Settings root. */
export const getProjectLinks = (): { href: string; label: string; icon: IconName }[] => [
	{ href: "/resume-templates", label: t`Templates`, icon: "files" },
	{ href: "/ats-checker", label: t`ATS Checker`, icon: "check-circle" },
];
