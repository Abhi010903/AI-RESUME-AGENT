"""Pydantic request and response schemas for Resume Ingestion."""

from datetime import datetime
import json
import re
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentBase(BaseModel):
    """Base document attributes."""

    id: str
    filename: str
    file_format: str
    file_size: int
    file_hash: str
    status: str
    page_count: int | None = None
    warnings: list[str] = []
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("warnings", mode="before")
    @classmethod
    def parse_warnings_field(cls, value: object) -> list[str]:
        """Safely parse warnings whether passed as list or JSON-encoded ORM column string."""
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []


class DocumentListItemResponse(BaseModel):
    """Concise document metadata for list endpoints."""

    id: str
    filename: str
    file_format: str
    file_size: int
    status: str
    page_count: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentBase):
    """Detailed document response including full extraction outcome."""

    extracted_text: str | None = None


class DocumentTextResponse(BaseModel):
    """Focused response for extracted text and warnings."""

    id: str
    filename: str
    file_format: str
    status: str
    extracted_text: str
    page_count: int | None = None
    warnings: list[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("warnings", mode="before")
    @classmethod
    def parse_warnings_field(cls, value: object) -> list[str]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []


class BatchUploadResponse(BaseModel):
    """Summary of batch upload and extraction."""

    total_submitted: int
    successful_count: int
    failed_count: int
    documents: list[DocumentResponse]


# ============================================================================
# Stage 3: Candidate Profile Intelligence Schemas
# ============================================================================


class ConflictItem(BaseModel):
    """Detected conflict across resumes or chronology."""

    id: str
    conflict_type: str
    severity: str  # "error", "warning", "info"
    description: str
    affected_entities: list[str] = []
    resolution_status: str = "unresolved"  # "unresolved", "resolved", "dismissed"
    resolution_notes: str | None = None


class WorkExperienceBase(BaseModel):
    company: str
    job_title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    skills_used: list[str] = []
    confidence_score: float = 1.0


class WorkExperienceResponse(WorkExperienceBase):
    id: str
    profile_id: str
    source_document_id: str
    is_approved: bool
    raw_text: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("skills_used", mode="before")
    @classmethod
    def parse_skills_used(cls, value: object) -> list[str]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []


class WorkExperienceUpdate(BaseModel):
    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    description: str | None = None
    skills_used: list[str] | None = None
    is_approved: bool | None = None


class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None


class EducationResponse(EducationBase):
    id: str
    profile_id: str
    source_document_id: str
    is_approved: bool
    raw_text: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EducationUpdate(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    is_approved: bool | None = None


class SkillBase(BaseModel):
    name: str
    category: str | None = None
    proficiency: str | None = None
    years_of_experience: float | None = None


class SkillResponse(SkillBase):
    id: str
    profile_id: str
    source_document_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    proficiency: str | None = None
    years_of_experience: float | None = None
    is_approved: bool | None = None


class CertificationBase(BaseModel):
    name: str
    issuing_organization: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class CertificationResponse(CertificationBase):
    id: str
    profile_id: str
    source_document_id: str
    is_approved: bool
    raw_text: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificationUpdate(BaseModel):
    name: str | None = None
    issuing_organization: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    is_approved: bool | None = None


class CandidateProfileResponse(BaseModel):
    """Complete consolidated candidate profile with traceability and conflicts."""

    id: str
    user_id: str | None = None
    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    source_document_ids: list[str] = []
    verification_status: str
    is_approved: bool
    approval_date: datetime | None = None
    conflicts: list[ConflictItem] = []

    experiences: list[WorkExperienceResponse] = []
    education: list[EducationResponse] = []
    skills: list[SkillResponse] = []
    certifications: list[CertificationResponse] = []
    projects: list[dict[str, Any]] = []
    achievements: list[str] = []
    completeness_percentage: float = 0.0

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("source_document_ids", "achievements", mode="before")
    @classmethod
    def parse_source_document_ids(cls, value: object) -> list[str]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @field_validator("projects", mode="before")
    @classmethod
    def parse_projects(cls, value: object) -> list[dict[str, Any]]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []

    @field_validator("conflicts", mode="before")
    @classmethod
    def parse_conflicts(cls, value: object) -> list[dict[str, object]]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []


class CandidateProfileUpdate(BaseModel):
    """Candidate manual profile edits."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None


class ConsolidationRequest(BaseModel):
    """Request to consolidate multiple uploaded resumes into a single profile."""

    document_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="IDs of 1 to 10 successfully extracted resumes.",
    )
    user_id: str | None = None


class ResolveConflictRequest(BaseModel):
    """Request to resolve or dismiss a detected conflict."""

    resolution_status: str = Field(..., pattern="^(resolved|dismissed)$")
    resolution_notes: str | None = None


class ProfileApprovalRequest(BaseModel):
    """Request to approve verified profile entities or the whole profile."""

    approve_all: bool = False
    experience_ids: list[str] = []
    education_ids: list[str] = []
    skill_ids: list[str] = []
    certification_ids: list[str] = []


# ============================================================================
# Stage 4: Job Description Intelligence Schemas
# ============================================================================


class NormalizedSkillItem(BaseModel):
    """Normalized technical or professional skill required or preferred by a job."""

    name: str
    category: str = "General"
    is_mandatory: bool = True
    raw_mention: str = ""
    importance: str = "high"


class RequirementItem(BaseModel):
    """Specific extracted requirement from a job description."""

    name: str
    category: str  # technical_skill, soft_skill, responsibility, education, certification, experience
    is_mandatory: bool = True
    raw_text: str = ""
    normalized_name: str = ""
    priority: str = "high"
    confidence: float = 1.0
    is_ambiguous: bool = False


class JobDescriptionAnalyzeRequest(BaseModel):
    """Request to ingest and analyze a job description."""

    raw_text: str = Field(..., min_length=10, max_length=100000)
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    user_id: str | None = None


class JobDescriptionCreate(BaseModel):
    """Manual or API job description creation."""

    raw_text: str = Field(..., min_length=10, max_length=100000)
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    summary: str | None = None
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    education_level: str | None = None
    user_id: str | None = None


class JobDescriptionUpdate(BaseModel):
    """Editable fields for a job description."""

    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    summary: str | None = None
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    education_level: str | None = None
    status: str | None = None


class JobDescriptionListItemResponse(BaseModel):
    """Concise job description metadata for list queries."""

    id: str
    title: str
    company: str | None = None
    location: str | None = None
    seniority_level: str | None = None
    min_years_experience: float | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionResponse(BaseModel):
    """Full structured job description response."""

    id: str
    title: str
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    summary: str | None = None
    raw_text: str
    normalized_text: str | None = None
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    education_level: str | None = None

    responsibilities: list[str] = []
    required_skills: list[dict[str, object]] = []
    preferred_skills: list[dict[str, object]] = []
    required_qualifications: list[str] = []
    preferred_qualifications: list[str] = []
    certifications: list[str] = []
    soft_skills: list[str] = []
    quality_warnings: list[str] = []

    status: str
    user_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator(
        "responsibilities",
        "required_qualifications",
        "preferred_qualifications",
        "certifications",
        "soft_skills",
        "quality_warnings",
        mode="before",
    )
    @classmethod
    def parse_string_list_field(cls, value: object) -> list[str]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def parse_dict_list_field(cls, value: object) -> list[dict[str, object]]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []


class JobRequirementsResponse(BaseModel):
    """Structured requirements breakdown for a job."""

    job_id: str
    title: str
    mandatory_requirements: list[RequirementItem] = []
    preferred_requirements: list[RequirementItem] = []
    responsibilities: list[str] = []
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    education_level: str | None = None
    certifications: list[str] = []


class JobSkillsResponse(BaseModel):
    """Normalized required and preferred skills for a job."""

    job_id: str
    title: str
    required_skills: list[NormalizedSkillItem] = []
    preferred_skills: list[NormalizedSkillItem] = []


# ============================================================================
# Stage 5: Evidence-Based Skill Matching Engine Schemas
# ============================================================================


class MatchRequest(BaseModel):
    """Request to match a candidate profile against a job description."""

    profile_id: str = Field(..., description="ID of candidate profile from Stage 3")
    job_id: str = Field(..., description="ID of job description from Stage 4")
    scoring_config: dict[str, float] | None = None


class RequirementMatchItem(BaseModel):
    """Evaluation of candidate evidence against a single job requirement."""

    requirement_name: str
    category: str
    is_mandatory: bool
    match_status: str  # STRONG_MATCH, PARTIAL_MATCH, RELATED_MATCH, NO_EVIDENCE, CONFLICTED_EVIDENCE, NOT_ASSESSED
    matched_candidate_skill: str | None = None
    matched_entity_id: str | None = None
    source_document_id: str | None = None
    evidence_excerpt: str | None = None
    relation_note: str | None = None
    confidence: float = 1.0
    score_contribution: float = 0.0


class GapItem(BaseModel):
    """Itemized gap or area for candidate evidence improvement."""

    requirement_name: str
    category: str
    is_mandatory: bool
    match_status: str
    reason: str
    recommended_evidence: str


class ScoreBreakdownResponse(BaseModel):
    """Detailed score breakdown and explainability narrative."""

    overall_score: float
    mandatory_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    certification_score: float
    domain_score: float
    evidence_coverage: float
    conflict_impact: float
    weights: dict[str, float]
    penalties_applied: list[str] = []
    disclaimer: str = (
        "This score is a platform-generated alignment indicator based strictly on "
        "evidence in the candidate profile, not a hiring guarantee or probability."
    )


class GapAnalysisResponse(BaseModel):
    """Structured gap analysis between candidate profile and job requirements."""

    match_id: str
    profile_id: str
    job_id: str
    total_gaps: int
    missing_mandatory_skills: list[GapItem] = []
    missing_preferred_skills: list[GapItem] = []
    partially_met_requirements: list[GapItem] = []
    related_transferable_skills: list[GapItem] = []
    experience_gaps: list[GapItem] = []
    education_gaps: list[GapItem] = []
    certification_gaps: list[GapItem] = []


class RequirementMatchListResponse(BaseModel):
    """List of requirement evaluations for a match."""

    match_id: str
    profile_id: str
    job_id: str
    requirements: list[RequirementMatchItem] = []


class MatchResultListItemResponse(BaseModel):
    """Summary of match result for list views."""

    id: str
    profile_id: str
    job_id: str
    overall_score: float
    mandatory_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    certification_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchResultResponse(BaseModel):
    """Complete match result with evidence breakdown, gaps, and score components."""

    id: str
    profile_id: str
    job_id: str
    overall_score: float
    mandatory_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    certification_score: float
    domain_score: float
    evidence_coverage: float
    conflict_impact: float

    score_breakdown: dict[str, object] = {}
    requirement_matches: list[RequirementMatchItem] = []
    gaps: list[GapItem] = []
    scoring_config: dict[str, object] = {}
    matching_version: str
    is_stale: bool = False
    stale_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("requirement_matches", mode="before")
    @classmethod
    def parse_requirement_matches(cls, value: object) -> list[object]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []

    @field_validator("gaps", mode="before")
    @classmethod
    def parse_gaps(cls, value: object) -> list[object]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []

    @field_validator("score_breakdown", "scoring_config", mode="before")
    @classmethod
    def parse_dict_field(cls, value: object) -> dict[str, object]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        if isinstance(value, dict):
            return value
        return {}


# ============================================================================
# Stage 6: Resume Generation & ATS Evaluation Schemas
# ============================================================================


class ClaimEvidence(BaseModel):
    """Schema tracking claim-level factual provenance back to source evidence."""

    claim_id: str
    section: str
    claim_text: str
    source_field: str
    source_document_id: str | None = None
    source_excerpt: str
    transformation_type: str = "direct"  # "direct", "synthesized", "summarized"
    validation_status: str = "verified"  # "verified", "inferred"
    confidence_score: float = 1.0


class GeneratedResumeCreate(BaseModel):
    """Payload to trigger tailored resume generation."""

    profile_id: str
    job_id: str
    match_id: str | None = None
    title: str | None = None


class GeneratedResumeListItemResponse(BaseModel):
    """Concise representation of a generated resume for list endpoints."""

    id: str
    profile_id: str
    job_id: str
    title: str
    target_role: str
    target_company: str | None = None
    version_number: int
    ats_score: float | None = None
    has_docx: bool = True
    has_pdf: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "GeneratedResumeListItemResponse":
        if hasattr(obj, "docx_path") or hasattr(obj, "pdf_path"):
            data = {
                "id": obj.id,
                "profile_id": obj.profile_id,
                "job_id": obj.job_id,
                "title": obj.title,
                "target_role": obj.target_role,
                "target_company": obj.target_company,
                "version_number": obj.version_number,
                "ats_score": getattr(obj, "ats_score", None),
                "has_docx": bool(getattr(obj, "docx_path", None)),
                "has_pdf": bool(getattr(obj, "pdf_path", None)),
                "created_at": obj.created_at,
            }
            return super().model_validate(data, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)


class GeneratedResumeResponse(BaseModel):
    """Complete generated resume representation with tailored content and file availability flags."""

    id: str
    profile_id: str
    job_id: str
    match_id: str | None = None
    title: str
    target_role: str
    target_company: str | None = None
    version_number: int
    sections: list[dict[str, Any]] = []
    claim_provenance: list[dict[str, Any]] = []
    has_docx: bool = True
    has_pdf: bool = True
    ats_score: float | None = None
    user_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "GeneratedResumeResponse":
        if hasattr(obj, "docx_path") or hasattr(obj, "pdf_path"):
            data = {
                "id": obj.id,
                "profile_id": obj.profile_id,
                "job_id": obj.job_id,
                "match_id": getattr(obj, "match_id", None),
                "title": obj.title,
                "target_role": obj.target_role,
                "target_company": obj.target_company,
                "version_number": obj.version_number,
                "sections": getattr(obj, "sections", []),
                "claim_provenance": getattr(obj, "claim_provenance", []),
                "has_docx": bool(getattr(obj, "docx_path", None)),
                "has_pdf": bool(getattr(obj, "pdf_path", None)),
                "ats_score": getattr(obj, "ats_score", None),
                "user_id": getattr(obj, "user_id", None),
                "created_at": obj.created_at,
                "updated_at": getattr(obj, "updated_at", obj.created_at),
            }
            return super().model_validate(data, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)

    @field_validator("sections", "claim_provenance", mode="before")
    @classmethod
    def parse_sections(cls, value: object) -> list[dict[str, Any]]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []


class ResumeVersionComparisonResponse(BaseModel):
    """Comparison between the latest and preceding generated resume versions."""

    profile_id: str
    job_id: str
    current_version: GeneratedResumeResponse
    previous_version: GeneratedResumeResponse | None = None
    differences: dict[str, Any] = {}


class ATSEvaluateRequest(BaseModel):
    """Payload to request ATS evaluation for a generated resume against a job."""

    resume_id: str
    job_id: str


class ATSEvaluationReportResponse(BaseModel):
    """Comprehensive ATS score breakdown, checks, and recommendations."""

    id: str
    resume_id: str
    job_id: str
    overall_score: float
    mandatory_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    keyword_score: float
    structure_score: float
    readability_score: float
    report: dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("report", mode="before")
    @classmethod
    def parse_report(cls, value: object) -> dict[str, Any]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        if isinstance(value, dict):
            return value
        return {}


# ============================================================================
# Stage 7: Authentication & Production Hardening Schemas
# ============================================================================


class UserRegisterRequest(BaseModel):
    """User registration payload."""

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128, description="Password at least 8 characters")
    full_name: str = Field(min_length=2, max_length=200, description="Full name of candidate")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, clean):
            raise ValueError("Invalid email address format")
        return clean


class UserLoginRequest(BaseModel):
    """User authentication payload."""

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, clean):
            raise ValueError("Invalid email address format")
        return clean


class UserResponse(BaseModel):
    """Public user profile information."""

    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Authentication token response with bearer JWT."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ============================================================================
# Additional Candidate Account & Profile Management Schemas
# ============================================================================


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)


class WorkExperienceCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    skills_used: list[str] = []


class EducationCreate(BaseModel):
    institution: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=200)
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str | None = None
    proficiency: str | None = None
    years_of_experience: float | None = None


class CertificationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    issuing_organization: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class ProjectItem(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subtitle: str | None = None
    technologies: list[str] = []
    bullets: list[str] = []


# ============================================================================
# Candidate Job / Application Tracker Schemas (Section 5.8)
# ============================================================================


class InterviewStageItem(BaseModel):
    id: str | None = None
    round_name: str
    scheduled_at: str | None = None
    status: str = "SCHEDULED"
    notes: str | None = None


class JobApplicationCreate(BaseModel):
    job_id: str | None = None
    resume_id: str | None = None
    company: str = Field(min_length=1, max_length=200)
    position_title: str = Field(min_length=1, max_length=200)
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    status: str = "INTERESTED"
    applied_date: str | None = None
    notes: str | None = None
    interviews: list[InterviewStageItem | dict[str, Any]] = []


class JobApplicationUpdate(BaseModel):
    job_id: str | None = None
    resume_id: str | None = None
    company: str | None = None
    position_title: str | None = None
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    status: str | None = None
    applied_date: str | None = None
    notes: str | None = None
    interviews: list[InterviewStageItem | dict[str, Any]] | None = None


class JobApplicationResponse(BaseModel):
    id: str
    user_id: str | None = None
    job_id: str | None = None
    resume_id: str | None = None
    company: str
    position_title: str
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    status: str
    applied_date: str | None = None
    notes: str | None = None
    interviews: list[dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("interviews", mode="before")
    @classmethod
    def parse_interviews(cls, value: object) -> list[dict[str, Any]]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []
        if isinstance(value, list):
            return value
        return []


class ActivityLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    title: str
    description: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowStageItem(BaseModel):
    key: str
    label: str
    status: str  # "not_started" | "in_progress" | "needs_attention" | "completed" | "blocked"
    description: str
    action_label: str
    action_url: str


class WorkflowPrimaryAction(BaseModel):
    title: str
    description: str
    reason: str
    action_label: str
    action_url: str
    priority: str


class WorkflowMetrics(BaseModel):
    resumes_count: int
    profile_status: str
    profile_completeness: float
    verified_skills_count: int
    projects_count: int
    experience_count: int
    certifications_count: int
    jobs_count: int
    matches_count: int
    generated_resumes_count: int
    ats_evaluations_count: int
    applications_count: int


class WorkflowStatusResponse(BaseModel):
    headline: str | None = None
    metrics: WorkflowMetrics
    stages: list[WorkflowStageItem]
    primary_action: WorkflowPrimaryAction
