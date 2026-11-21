"""SQLAlchemy database models for AI Resume Agent."""

from datetime import datetime, timezone
import json
from typing import Any
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Document(Base):
    """Uploaded candidate resume document and extraction metadata."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Document ownership boundary (ready for Phase 7 authentication / multi-tenancy)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def warnings_list(self) -> list[str]:
        """Deserialize stored JSON warnings."""
        if not self.warnings:
            return []
        try:
            parsed = json.loads(self.warnings)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except Exception:
            return [self.warnings]

    def set_warnings(self, warnings: list[str]) -> None:
        """Serialize warnings list to JSON string."""
        self.warnings = json.dumps(warnings) if warnings else None


class CandidateProfile(Base):
    """Consolidated profile representing a candidate across multiple resumes."""

    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    source_document_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unverified", index=True
    )
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conflicts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    projects_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    achievements_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def completeness_percentage(self) -> float:
        points = 0.0
        if self.full_name:
            points += 5.0
        if self.email:
            points += 5.0
        if self.phone:
            points += 5.0
        if self.headline or self.summary:
            points += 5.0
        if self.education:
            points += 20.0
        if self.experiences:
            points += 20.0
        if len(self.skills) >= 5:
            points += 20.0
        elif self.skills:
            points += 10.0
        if self.projects:
            points += 10.0
        if self.certifications or self.achievements:
            points += 10.0
        return min(100.0, round(points, 1))

    # Relationships
    experiences: Mapped[list["WorkExperience"]] = relationship(
        "WorkExperience",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(WorkExperience.start_date)",
    )
    education: Mapped[list["Education"]] = relationship(
        "Education",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(Education.start_date)",
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="Skill.name",
    )
    certifications: Mapped[list["Certification"]] = relationship(
        "Certification",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(Certification.issue_date)",
    )

    @property
    def source_document_ids(self) -> list[str]:
        try:
            return json.loads(self.source_document_ids_json) if self.source_document_ids_json else []
        except Exception:
            return []

    def set_source_document_ids(self, doc_ids: list[str]) -> None:
        self.source_document_ids_json = json.dumps(doc_ids)

    @property
    def conflicts(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.conflicts_json) if self.conflicts_json else []
        except Exception:
            return []

    def set_conflicts(self, conflicts: list[dict[str, Any]]) -> None:
        self.conflicts_json = json.dumps(conflicts) if conflicts else None

    @property
    def projects(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.projects_json) if self.projects_json else []
        except Exception:
            return []

    def get_projects(self) -> list[dict[str, Any]]:
        return self.projects

    def set_projects(self, projects: list[dict[str, Any]]) -> None:
        self.projects_json = json.dumps(projects) if projects else "[]"

    @property
    def achievements(self) -> list[str]:
        try:
            return json.loads(self.achievements_json) if self.achievements_json else []
        except Exception:
            return []

    def get_achievements(self) -> list[str]:
        return self.achievements

    def set_achievements(self, achievements: list[str]) -> None:
        self.achievements_json = json.dumps(achievements) if achievements else "[]"


class WorkExperience(Base):
    """Extracted and consolidated employment record with source document traceability."""

    __tablename__ = "work_experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    company: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_used_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="experiences")

    @property
    def skills_used(self) -> list[str]:
        try:
            return json.loads(self.skills_used_json) if self.skills_used_json else []
        except Exception:
            return []

    def set_skills_used(self, skills: list[str]) -> None:
        self.skills_used_json = json.dumps(skills) if skills else None


class Education(Base):
    """Extracted academic qualification with source document traceability."""

    __tablename__ = "educations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    institution: Mapped[str] = mapped_column(String(250), nullable=False)
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)

    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="education")


class Skill(Base):
    """Extracted technical or professional skill with source document traceability."""

    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_of_experience: Mapped[float | None] = mapped_column(Float, nullable=True)

    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="skills")


class Certification(Base):
    """Extracted professional certification with source document traceability."""

    __tablename__ = "certifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuing_organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    issue_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    source_document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="certifications")


class JobDescription(Base):
    """Structured job description requirements and metadata (Stage 4)."""

    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    min_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(200), nullable=True)

    responsibilities_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    required_skills_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    preferred_skills_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    required_qualifications_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    preferred_qualifications_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    certifications_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    soft_skills_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    quality_warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="analyzed", index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def responsibilities(self) -> list[str]:
        try:
            return json.loads(self.responsibilities_json) if self.responsibilities_json else []
        except Exception:
            return []

    def set_responsibilities(self, items: list[str]) -> None:
        self.responsibilities_json = json.dumps(items)

    @property
    def required_skills(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.required_skills_json) if self.required_skills_json else []
        except Exception:
            return []

    def set_required_skills(self, items: list[dict[str, Any]]) -> None:
        self.required_skills_json = json.dumps(items)

    @property
    def preferred_skills(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.preferred_skills_json) if self.preferred_skills_json else []
        except Exception:
            return []

    def set_preferred_skills(self, items: list[dict[str, Any]]) -> None:
        self.preferred_skills_json = json.dumps(items)

    @property
    def required_qualifications(self) -> list[str]:
        try:
            return json.loads(self.required_qualifications_json) if self.required_qualifications_json else []
        except Exception:
            return []

    def set_required_qualifications(self, items: list[str]) -> None:
        self.required_qualifications_json = json.dumps(items)

    @property
    def preferred_qualifications(self) -> list[str]:
        try:
            return json.loads(self.preferred_qualifications_json) if self.preferred_qualifications_json else []
        except Exception:
            return []

    def set_preferred_qualifications(self, items: list[str]) -> None:
        self.preferred_qualifications_json = json.dumps(items)

    @property
    def certifications(self) -> list[str]:
        try:
            return json.loads(self.certifications_json) if self.certifications_json else []
        except Exception:
            return []

    def set_certifications(self, items: list[str]) -> None:
        self.certifications_json = json.dumps(items)

    @property
    def soft_skills(self) -> list[str]:
        try:
            return json.loads(self.soft_skills_json) if self.soft_skills_json else []
        except Exception:
            return []

    def set_soft_skills(self, items: list[str]) -> None:
        self.soft_skills_json = json.dumps(items)

    @property
    def quality_warnings(self) -> list[str]:
        try:
            return json.loads(self.quality_warnings_json) if self.quality_warnings_json else []
        except Exception:
            return []

    def set_quality_warnings(self, items: list[str]) -> None:
        self.quality_warnings_json = json.dumps(items)


class MatchResult(Base):
    """Evidence-based match assessment between candidate profile and job description (Stage 5)."""

    __tablename__ = "match_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    mandatory_skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, nullable=False)
    certification_score: Mapped[float] = mapped_column(Float, nullable=False)
    domain_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    conflict_impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    score_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_matches_json: Mapped[str] = mapped_column(Text, nullable=False)
    gaps_json: Mapped[str] = mapped_column(Text, nullable=False)
    scoring_config_json: Mapped[str] = mapped_column(Text, nullable=False)
    matching_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stale_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")
    job: Mapped["JobDescription"] = relationship("JobDescription")

    @property
    def score_breakdown(self) -> dict[str, Any]:
        try:
            return json.loads(self.score_breakdown_json) if self.score_breakdown_json else {}
        except Exception:
            return {}

    @property
    def requirement_matches(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.requirement_matches_json) if self.requirement_matches_json else []
        except Exception:
            return []

    @property
    def gaps(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.gaps_json) if self.gaps_json else []
        except Exception:
            return []

    @property
    def scoring_config(self) -> dict[str, Any]:
        try:
            return json.loads(self.scoring_config_json) if self.scoring_config_json else {}
        except Exception:
            return {}


class GeneratedResume(Base):
    """Tailored, ATS-optimized resume version generated for a target job (Stage 6)."""

    __tablename__ = "generated_resumes"
    __table_args__ = (
        UniqueConstraint("profile_id", "job_id", "version_number", name="uq_generated_resume_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    target_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)

    sections_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    claim_provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")
    docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")
    job: Mapped["JobDescription"] = relationship("JobDescription")
    match: Mapped["MatchResult | None"] = relationship("MatchResult")
    ats_evaluations: Mapped[list["ATSEvaluation"]] = relationship(
        "ATSEvaluation", back_populates="resume", cascade="all, delete-orphan"
    )

    @property
    def sections(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.sections_json) if self.sections_json else []
        except Exception:
            return []

    def set_sections(self, sections: list[dict[str, Any]]) -> None:
        self.sections_json = json.dumps(sections)

    @property
    def claim_provenance(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.claim_provenance_json) if self.claim_provenance_json else []
        except Exception:
            return []

    def set_claim_provenance(self, provenance: list[dict[str, Any]]) -> None:
        self.claim_provenance_json = json.dumps(provenance)


class ATSEvaluation(Base):
    """Detailed ATS compliance and keyword alignment evaluation (Stage 6)."""

    __tablename__ = "ats_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generated_resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    mandatory_skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, nullable=False)
    keyword_score: Mapped[float] = mapped_column(Float, nullable=False)
    structure_score: Mapped[float] = mapped_column(Float, nullable=False)
    readability_score: Mapped[float] = mapped_column(Float, nullable=False)

    report_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    resume: Mapped["GeneratedResume"] = relationship("GeneratedResume", back_populates="ats_evaluations")
    job: Mapped["JobDescription"] = relationship("JobDescription")

    @property
    def report(self) -> dict[str, Any]:
        try:
            return json.loads(self.report_json) if self.report_json else {}
        except Exception:
            return {}

    def set_report(self, report: dict[str, Any]) -> None:
        self.report_json = json.dumps(report)


class User(Base):
    """Candidate account for authentication and tenant data isolation (Stage 7)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class JobApplication(Base):
    """Personal candidate job application tracker."""

    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resume_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("generated_resumes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    company: Mapped[str] = mapped_column(String(200), nullable=False)
    position_title: Mapped[str] = mapped_column(String(200), nullable=False)
    job_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="INTERESTED", index=True)
    applied_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    interviews_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    job: Mapped["JobDescription | None"] = relationship("JobDescription")
    resume: Mapped["GeneratedResume | None"] = relationship("GeneratedResume")

    @property
    def interviews(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.interviews_json) if self.interviews_json else []
        except Exception:
            return []

    def set_interviews(self, items: list[dict[str, Any]]) -> None:
        self.interviews_json = json.dumps(items)


class ActivityLog(Base):
    """Immutable audit event for candidate platform actions and workflow changes."""

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

