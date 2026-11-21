import { Link } from "@tanstack/react-router";

export function PrivacyPage() {
	return (
		<main id="main-content" className="flex-1 px-(--gutter) py-12 md:py-20">
			<div className="mx-auto max-w-[840px]">
				<header className="mb-12 border-b border-line pb-8">
					<span className="font-mono text-xs uppercase tracking-wider text-accent-text">Legal &amp; Data Governance</span>
					<h1 className="mt-2 font-display text-[clamp(32px,4vw,52px)] font-bold tracking-tight text-ink">
						Privacy Policy
					</h1>
					<p className="mt-3 font-ui text-sm text-ink-3">
						Last updated: November 2026 · AI Resume Agent Platform
					</p>
				</header>

				<article className="space-y-10 font-ui text-[15px] leading-relaxed text-ink-2">
					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">1. Overview &amp; Product Identity</h2>
						<p>
							AI Resume Agent (&ldquo;we&rdquo;, &ldquo;our&rdquo;, or &ldquo;the platform&rdquo;) is an intelligent career and
							resume management platform designed for precision resume architecture, ATS readability optimization, candidate profile
							management, and job application tracking.
						</p>
						<p>
							This Privacy Policy provides a transparent, factual statement of how candidate information is collected, processed,
							stored, and protected when you use our web application, API, and Model Context Protocol (MCP) integrations.
						</p>
						<p className="rounded-lg border border-line bg-surface p-4 text-xs text-ink-3">
							<strong>Open-Source Licensing Disclosure:</strong> AI Resume Agent candidate software is derived from and builds upon
							software originally developed as Reactive Resume by Amruth Pillai, licensed under the MIT License. All original copyright
							notices and licensing obligations are strictly maintained.
						</p>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">2. Information We Collect</h2>
						<p>We collect and store only the information necessary to provide resume building, document generation, and application tracking services:</p>
						<ul className="list-disc space-y-2 ps-6">
							<li>
								<strong className="text-ink">Account &amp; Authentication Credentials:</strong> Your name, email address, salted and hashed passwords (via Better Auth argon2/scrypt), optional passkeys (WebAuthn credentials), and two-factor authentication (TOTP) secret keys.
							</li>
							<li>
								<strong className="text-ink">Candidate Resume Content:</strong> Personal contact information (phone number, location, portfolio and professional profile links), employment history, education, certifications, skills, projects, custom sections, and styling preferences.
							</li>
							<li>
								<strong className="text-ink">Job Application Tracking Data:</strong> Job posting details, target companies, roles, interview dates, contact notes, salary offers, and tailored application records.
							</li>
							<li>
								<strong className="text-ink">Uploaded Files &amp; Media:</strong> Profile photographs, uploaded resume PDFs, and imported documents processed for format conversion.
							</li>
						</ul>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">3. Data Storage &amp; Infrastructure</h2>
						<p>
							Candidate accounts, resumes, cover letters, and application records are stored in a relational PostgreSQL database.
							Uploaded media files and temporary document rendering artifacts are stored in local or S3-compatible object storage
							configured for your specific instance.
						</p>
						<p>
							Data is stored strictly in accordance with the host deployment configuration. We do not sell, rent, or trade candidate
							data to data brokers or third-party marketing networks.
						</p>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">4. Document Generation &amp; Processing</h2>
						<p>
							Document export (vector PDF and DOCX Word documents) is processed on-demand using internal rendering engines
							(Forme and docx). The ATS checker evaluates font encodings, character streams, and document hierarchy.
							Files checked in the browser-based ATS evaluator are analyzed in your browser session and are not uploaded or
							shared with external reviewers without your explicit confirmation.
						</p>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">5. AI Services &amp; Third-Party LLM Integrations</h2>
						<p>
							AI features—such as content refinement, job description tailoring, career coaching, and writing reviews—are
							entirely optional.
						</p>
						<div className="rounded-lg border border-line bg-surface p-4 space-y-2 text-sm">
							<p className="font-semibold text-ink">Bring-Your-Own-Key (BYOK) Architecture:</p>
							<p>
								AI Resume Agent connects to language model providers (including OpenAI, Anthropic, Google Gemini, OpenRouter,
								Ollama, or self-hosted endpoints) using credentials configured by the user or system administrator.
							</p>
							<p>
								When you initiate an AI prompt or document action, only the specific document fragment, resume context, or job
								description required for that task is transmitted to your configured AI provider. Transmission is subject to
								that third-party provider&rsquo;s privacy terms and data retention policies.
							</p>
							<p>
								If no AI provider key is configured, no candidate resume data is ever transmitted to an artificial intelligence service.
							</p>
						</div>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">6. Visibility &amp; Public Sharing</h2>
						<p>
							All resumes and cover letters are private by default, accessible only to authenticated account owners.
						</p>
						<p>
							If you choose to enable the public sharing feature for a resume, a public link is generated. You may optionally
							protect public links with a password, and you can revoke, change, or disable public access at any time from the
							Share menu in the resume editor.
						</p>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">7. Candidate Rights &amp; Data Control</h2>
						<p>Candidates retain full control over their personal data:</p>
						<ul className="list-disc space-y-2 ps-6">
							<li>
								<strong className="text-ink">Complete Export:</strong> You can download a complete ZIP archive of your account data (including all resumes in JSON format, cover letters, and uploaded media) at any time under <Link to="/dashboard/settings/account" className="text-accent-text underline">Settings &rarr; Account</Link>.
							</li>
							<li>
								<strong className="text-ink">Account Deletion:</strong> You can permanently delete your account at any time. Account deletion cascades through the database, permanently deleting your profile, resumes, cover letters, job applications, and active sessions.
							</li>
							<li>
								<strong className="text-ink">Data Portability:</strong> Resumes can be downloaded in standard JSON Resume, Reactive Resume compatible JSON, PDF, and Word DOCX formats to prevent vendor lock-in.
							</li>
						</ul>
					</section>

					<section className="space-y-3">
						<h2 className="font-display text-2xl font-semibold text-ink">8. Contact &amp; Governance</h2>
						<p>
							For questions regarding data processing, security disclosures, or privacy compliance on your instance of AI Resume Agent,
							refer to the system administrator for your deployment or review our open-source documentation.
						</p>
					</section>
				</article>

				<footer className="mt-14 border-t border-line pt-6">
					<div className="flex flex-wrap items-center justify-between gap-4 font-ui text-sm text-ink-3">
						<Link to="/" className="text-accent-text hover:underline">&larr; Back to AI Resume Agent</Link>
						<Link to="/resume-templates" className="hover:text-ink">Templates</Link>
						<Link to="/ats-checker" className="hover:text-ink">ATS Checker</Link>
						<a href="https://opensource.org/licenses/MIT" target="_blank" rel="noopener noreferrer" className="hover:text-ink">MIT License</a>
					</div>
				</footer>
			</div>
		</main>
	);
}
