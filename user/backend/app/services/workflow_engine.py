"""Candidate Workflow Orchestration Engine.

Computes 12-stage candidate lifecycle progress, stage readiness,
blocking dependencies, and state-based next action recommendations.
"""

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import (
    CandidateProfile,
    Document,
    JobApplication,
    JobDescription,
    MatchResult,
    GeneratedResume,
    ATSEvaluation,
    User,
)
from app.schemas import (
    WorkflowMetrics,
    WorkflowPrimaryAction,
    WorkflowStageItem,
    WorkflowStatusResponse,
)


def compute_candidate_workflow_status(
    db: Session,
    user: User | None = None,
) -> WorkflowStatusResponse:
    """Evaluate candidate data and compute 12-step lifecycle state and recommendations."""
    user_id = user.id if user else None

    # Query Documents
    doc_stmt = select(Document)
    if user_id:
        doc_stmt = doc_stmt.where((Document.user_id == user_id) | (Document.user_id.is_(None)))
    documents = list(db.scalars(doc_stmt).all())
    doc_count = len(documents)
    extracted_docs = [d for d in documents if d.status == "completed" or (d.extracted_text and len(d.extracted_text) > 20)]
    processing_docs = [d for d in documents if d.status in ("pending", "processing")]

    # Query Profiles
    prof_stmt = select(CandidateProfile)
    if user_id:
        prof_stmt = prof_stmt.where((CandidateProfile.user_id == user_id) | (CandidateProfile.user_id.is_(None)))
    profiles = list(db.scalars(prof_stmt).all())
    active_profile = profiles[0] if profiles else None

    # Query Jobs
    job_stmt = select(JobDescription)
    if user_id:
        job_stmt = job_stmt.where((JobDescription.user_id == user_id) | (JobDescription.user_id.is_(None)))
    jobs = list(db.scalars(job_stmt).all())
    jobs_count = len(jobs)

    # Query Matches
    match_stmt = select(MatchResult)
    if user_id:
        match_stmt = match_stmt.where((MatchResult.user_id == user_id) | (MatchResult.user_id.is_(None)))
    matches = list(db.scalars(match_stmt).all())
    matches_count = len(matches)
    has_fresh_match = any(not m.is_stale for m in matches)
    has_stale_match = any(m.is_stale for m in matches)

    # Query Generated Resumes
    gen_stmt = select(GeneratedResume)
    if user_id:
        gen_stmt = gen_stmt.where((GeneratedResume.user_id == user_id) | (GeneratedResume.user_id.is_(None)))
    resumes = list(db.scalars(gen_stmt).all())
    resumes_count = len(resumes)

    # Query ATS Reports
    ats_stmt = select(ATSEvaluation)
    if user_id:
        ats_stmt = ats_stmt.where((ATSEvaluation.user_id == user_id) | (ATSEvaluation.user_id.is_(None)))
    ats_reports = list(db.scalars(ats_stmt).all())
    ats_count = len(ats_reports)

    # Query Applications
    app_stmt = select(JobApplication)
    if user_id:
        app_stmt = app_stmt.where((JobApplication.user_id == user_id) | (JobApplication.user_id.is_(None)))
    applications = list(db.scalars(app_stmt).all())
    apps_count = len(applications)

    # Evaluate Profile Specifics
    completeness = active_profile.completeness_percentage if active_profile else 0.0
    verified_skills = len([s for s in active_profile.skills if s.is_approved]) if active_profile else 0
    projects_count = len(active_profile.projects) if active_profile else 0
    experience_count = len(active_profile.experiences) if active_profile else 0
    certifications_count = len(active_profile.certifications) if active_profile else 0
    unresolved_conflicts = [c for c in active_profile.conflicts if c.get("status") == "detected"] if active_profile else []
    is_profile_approved = bool(active_profile and active_profile.is_approved)

    # Build Metrics
    metrics = WorkflowMetrics(
        resumes_count=doc_count,
        profile_status=active_profile.verification_status if active_profile else "not_consolidated",
        profile_completeness=completeness,
        verified_skills_count=verified_skills,
        projects_count=projects_count,
        experience_count=experience_count,
        certifications_count=certifications_count,
        jobs_count=jobs_count,
        matches_count=matches_count,
        generated_resumes_count=resumes_count,
        ats_evaluations_count=ats_count,
        applications_count=apps_count,
    )

    # Build 12 Stages
    stages: list[WorkflowStageItem] = []

    # 1. Upload Resumes
    stages.append(
        WorkflowStageItem(
            key="upload_resumes",
            label="Upload Resumes",
            status="completed" if doc_count > 0 else "not_started",
            description=f"{doc_count} source document(s) uploaded in library." if doc_count > 0 else "Upload PDF or DOCX resumes to extract career evidence.",
            action_label="Upload Resumes",
            action_url="/resumes",
        )
    )

    # 2. Extract Information
    if doc_count == 0:
        extract_status = "blocked"
        extract_desc = "Blocked: Upload at least one resume document first."
    elif len(extracted_docs) == doc_count and doc_count > 0:
        extract_status = "completed"
        extract_desc = f"All {doc_count} resume documents parsed with provenance tags."
    elif processing_docs:
        extract_status = "in_progress"
        extract_desc = f"{len(processing_docs)} document(s) currently extracting..."
    else:
        extract_status = "needs_attention"
        extract_desc = "Some documents failed extraction. Reprocess them in Resume Library."

    stages.append(
        WorkflowStageItem(
            key="extract_information",
            label="Extract Information",
            status=extract_status,
            description=extract_desc,
            action_label="View Ingestion",
            action_url="/resumes",
        )
    )

    # 3. Consolidate Profile
    if not extracted_docs:
        cons_status = "blocked"
        cons_desc = "Blocked: Complete resume text extraction first."
    elif active_profile:
        cons_status = "completed"
        cons_desc = f"Career profile consolidated ({completeness}% completeness)."
    else:
        cons_status = "not_started"
        cons_desc = f"{len(extracted_docs)} parsed resume(s) ready to consolidate into master profile."

    stages.append(
        WorkflowStageItem(
            key="consolidate_profile",
            label="Consolidate Profile",
            status=cons_status,
            description=cons_desc,
            action_label="Build Profile",
            action_url="/resumes",
        )
    )

    # 4. Resolve Conflicts
    if not active_profile:
        conf_status = "blocked"
        conf_desc = "Blocked: Consolidate candidate profile first."
    elif unresolved_conflicts:
        conf_status = "needs_attention"
        conf_desc = f"{len(unresolved_conflicts)} conflict(s) require candidate resolution."
    else:
        conf_status = "completed"
        conf_desc = "No unresolved source-document conflicts detected."

    stages.append(
        WorkflowStageItem(
            key="resolve_conflicts",
            label="Resolve Conflicts",
            status=conf_status,
            description=conf_desc,
            action_label="Review Conflicts",
            action_url="/profile",
        )
    )

    # 5. Approve Profile
    if not active_profile:
        appr_status = "blocked"
        appr_desc = "Blocked: Build candidate profile first."
    elif unresolved_conflicts:
        appr_status = "blocked"
        appr_desc = "Blocked: Resolve all pending conflicts before approving profile."
    elif is_profile_approved:
        appr_status = "completed"
        appr_desc = "Profile approved as authoritative source of truth."
    else:
        appr_status = "needs_attention"
        appr_desc = "Review candidate claims and formally approve profile."

    stages.append(
        WorkflowStageItem(
            key="approve_profile",
            label="Approve Profile",
            status=appr_status,
            description=appr_desc,
            action_label="Review & Approve",
            action_url="/profile",
        )
    )

    # 6. Add Target Job
    if not active_profile:
        job_status = "blocked"
        job_desc = "Blocked: Consolidate profile first."
    elif jobs_count > 0:
        job_status = "completed"
        job_desc = f"{jobs_count} target job position(s) analyzed."
    else:
        job_status = "not_started"
        job_desc = "Add target role description (paste or upload PDF/DOCX/TXT/MD)."

    stages.append(
        WorkflowStageItem(
            key="add_target_job",
            label="Add Target Job",
            status=job_status,
            description=job_desc,
            action_label="Add Target Job",
            action_url="/jobs",
        )
    )

    # 7. Analyze Requirements
    if jobs_count == 0:
        ana_status = "blocked"
        ana_desc = "Blocked: Add at least one target job description first."
    else:
        ana_status = "completed"
        ana_desc = f"{jobs_count} job description(s) structured into mandatory/preferred requirements."

    stages.append(
        WorkflowStageItem(
            key="analyze_requirements",
            label="Analyze Requirements",
            status=ana_status,
            description=ana_desc,
            action_label="View Jobs",
            action_url="/jobs",
        )
    )

    # 8. Generate Skill Match
    if not active_profile or jobs_count == 0:
        mat_status = "blocked"
        mat_desc = "Blocked: Requires both an approved profile and a target job."
    elif has_stale_match:
        mat_status = "needs_attention"
        mat_desc = "Match results are stale because profile or job changed. Re-run matching."
    elif has_fresh_match:
        mat_status = "completed"
        mat_desc = f"{matches_count} evidence-based fit calculation(s) completed."
    else:
        mat_status = "not_started"
        mat_desc = "Run 6-dimension evidence-based skill matching engine."

    stages.append(
        WorkflowStageItem(
            key="generate_skill_match",
            label="Generate Skill Match",
            status=mat_status,
            description=mat_desc,
            action_label="Compute Match",
            action_url="/matching",
        )
    )

    # 9. Review Skill Gaps
    if matches_count == 0:
        gap_status = "blocked"
        gap_desc = "Blocked: Compute skill matching first."
    else:
        gap_status = "completed"
        gap_desc = "Requirement checklist and honest gap recommendations available."

    stages.append(
        WorkflowStageItem(
            key="review_skill_gaps",
            label="Review Skill Gaps",
            status=gap_status,
            description=gap_desc,
            action_label="Inspect Gaps",
            action_url="/matching",
        )
    )

    # 10. Generate Tailored Resume
    if matches_count == 0:
        gen_status = "blocked"
        gen_desc = "Blocked: Complete skill match to select proven evidence."
    elif resumes_count > 0:
        gen_status = "completed"
        gen_desc = f"{resumes_count} tailored single-page A4 resume version(s) generated."
    else:
        gen_status = "not_started"
        gen_desc = "Generate zero-hallucination, single-page tailored resume in PDF and DOCX."

    stages.append(
        WorkflowStageItem(
            key="generate_tailored_resume",
            label="Generate Tailored Resume",
            status=gen_status,
            description=gen_desc,
            action_label="Tailor Resume",
            action_url="/generation",
        )
    )

    # 11. Evaluate ATS
    if resumes_count == 0:
        ats_st = "blocked"
        ats_desc = "Blocked: Generate a tailored resume first."
    elif ats_count > 0:
        ats_st = "completed"
        ats_desc = f"{ats_count} 7-dimension ATS parsing report(s) completed."
    else:
        ats_st = "not_started"
        ats_desc = "Simulate enterprise ATS parsing with keyword density check."

    stages.append(
        WorkflowStageItem(
            key="evaluate_ats",
            label="Evaluate ATS",
            status=ats_st,
            description=ats_desc,
            action_label="Run ATS Check",
            action_url="/ats",
        )
    )

    # 12. Track Applications
    if resumes_count == 0:
        track_status = "blocked"
        track_desc = "Blocked: Tailor resume version for your application first."
    elif apps_count > 0:
        track_status = "completed"
        track_desc = f"{apps_count} application(s) tracked across 8 Kanban pipeline stages."
    else:
        track_status = "not_started"
        track_desc = "Add your target position to Kanban pipeline with interviews & follow-up dates."

    stages.append(
        WorkflowStageItem(
            key="track_applications",
            label="Track Applications",
            status=track_status,
            description=track_desc,
            action_label="Open Tracker",
            action_url="/applications",
        )
    )

    # Compute Primary Recommended Next Action
    primary_action: WorkflowPrimaryAction
    if doc_count == 0:
        primary_action = WorkflowPrimaryAction(
            title="Upload Your Source Resumes",
            description="Start by uploading your existing PDF or DOCX resumes to extract verified career facts.",
            reason="No resume documents found in your library.",
            action_label="Upload Resumes",
            action_url="/resumes",
            priority="high",
        )
    elif not active_profile:
        primary_action = WorkflowPrimaryAction(
            title="Consolidate Resumes into Master Profile",
            description="Your uploaded documents are parsed. Merge them into a single, unified career profile.",
            reason="Source documents uploaded, but candidate profile has not been built yet.",
            action_label="Build My Profile",
            action_url="/resumes",
            priority="high",
        )
    elif unresolved_conflicts:
        primary_action = WorkflowPrimaryAction(
            title="Resolve Detected Career Conflicts",
            description="Conflicting dates or facts were detected across your resumes. Review side-by-side evidence to resolve.",
            reason=f"{len(unresolved_conflicts)} conflict(s) require candidate verification.",
            action_label="Resolve Conflicts",
            action_url="/profile",
            priority="high",
        )
    elif not is_profile_approved:
        primary_action = WorkflowPrimaryAction(
            title="Review and Formally Approve Profile",
            description="Verify your skills and experience to lock your authoritative source of truth for resume tailoring.",
            reason="Profile must be approved before downstream tailoring and matching.",
            action_label="Review & Approve Profile",
            action_url="/profile",
            priority="high",
        )
    elif jobs_count == 0:
        primary_action = WorkflowPrimaryAction(
            title="Add a Target Job Description",
            description="Add the job posting you want to apply for. Paste text or upload a job description document.",
            reason="An analyzed job is needed to evaluate skill compatibility.",
            action_label="Add Target Job",
            action_url="/jobs",
            priority="medium",
        )
    elif matches_count == 0 or has_stale_match:
        primary_action = WorkflowPrimaryAction(
            title="Calculate Evidence-Based Skill Match" if matches_count == 0 else "Refresh Stale Skill Match",
            description="Run our 6-dimension matching engine to audit your skills against mandatory job requirements.",
            reason="Job description exists, but match assessment is pending or stale." if matches_count == 0 else "Profile or Job changed since last match assessment.",
            action_label="Compute Evidence Match",
            action_url="/matching",
            priority="high",
        )
    elif resumes_count == 0:
        primary_action = WorkflowPrimaryAction(
            title="Generate Job-Specific Tailored Resume",
            description="Generate a strictly single-page, ATS-optimized PDF and DOCX resume backed by verified facts.",
            reason="Skill match is ready. Proceed to generate your tailored resume.",
            action_label="Generate Tailored Resume",
            action_url="/generation",
            priority="high",
        )
    elif ats_count == 0:
        primary_action = WorkflowPrimaryAction(
            title="Evaluate ATS Compatibility",
            description="Audit your tailored resume against enterprise ATS filters and check for keyword coverage.",
            reason="Your generated resume has not yet been audited for ATS compliance.",
            action_label="Evaluate ATS Score",
            action_url="/ats",
            priority="medium",
        )
    elif apps_count == 0:
        primary_action = WorkflowPrimaryAction(
            title="Track Your Job Application",
            description="Link your tailored resume and target job to the Kanban pipeline to track interview stages.",
            reason="Your application materials are ready, but the position is not tracked yet.",
            action_label="Track Application",
            action_url="/applications",
            priority="medium",
        )
    else:
        primary_action = WorkflowPrimaryAction(
            title="Manage Interview Pipeline",
            description="Track interview rounds, follow-up dates, and offers across your active applications.",
            reason="All platform stages complete. Monitor your live applications pipeline.",
            action_label="View Applications Tracker",
            action_url="/applications",
            priority="low",
        )

    return WorkflowStatusResponse(
        headline=active_profile.headline if active_profile else None,
        metrics=metrics,
        stages=stages,
        primary_action=primary_action,
    )
