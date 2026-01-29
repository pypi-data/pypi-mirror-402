"""Lawgorithm SDK data models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# Enums


class RiskLevel(str, Enum):
    """AI Act risk levels."""

    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class Severity(str, Enum):
    """Policy severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ControlStatus(str, Enum):
    """Control result status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class IncidentSeverity(str, Enum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CLOSED = "closed"


# Models


class System(BaseModel):
    """AI System representation."""

    id: str
    name: str
    description: str | None = None
    risk_level: RiskLevel | None = None
    risk_justification: str | None = None
    purpose: str | None = None
    domain: str | None = None
    status: str | None = None
    human_supervisor_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        extra = "allow"


class Policy(BaseModel):
    """Compliance policy."""

    id: str
    policy_id: str
    title: str
    description: str | None = None
    source: str | None = None
    risk_level: RiskLevel | None = None
    severity: Severity
    enabled: bool = True
    source_url: str | None = None
    sync_enabled: bool = False


class ControlResult(BaseModel):
    """Result of a policy control evaluation."""

    id: str
    policy_id: str
    policy_title: str
    system_id: str
    status: ControlStatus
    message: str | None = None
    fix_suggestion: str | None = None
    severity: Severity
    evaluated_at: datetime


class ComplianceIssue(BaseModel):
    """A compliance issue found during check."""

    policy_id: str
    policy_title: str
    system_id: str
    system_name: str
    severity: Severity
    message: str
    fix_suggestion: str | None = None


class ComplianceCheckResult(BaseModel):
    """Result of a CI/CD compliance check."""

    repo: str
    commit: str
    branch: str
    systems_analyzed: int
    policies_evaluated: int
    passed: int
    failed: int
    compliance_rate: float = Field(ge=0, le=1)
    has_failures: bool
    blocked: bool
    issues: list[ComplianceIssue] = []
    exit_code: int = 0
    compliance_state_id: str | None = None


class Incident(BaseModel):
    """Post-market incident (AI Act Article 72)."""

    id: str
    system_id: str
    title: str
    description: str | None = None
    severity: IncidentSeverity
    status: IncidentStatus
    category: str | None = None
    root_cause: str | None = None
    impact_assessment: str | None = None
    corrective_actions: str | None = None
    authority_notified: bool = False
    authority_notified_at: datetime | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class IncidentStats(BaseModel):
    """Incident statistics for a system."""

    system_id: str
    total: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    by_category: dict[str, int]
    authority_notifications: int
    avg_resolution_hours: float | None = None


class Attestation(BaseModel):
    """Ed25519 signed attestation."""

    id: str
    system_id: str
    attestation_type: str
    attester_org: str
    attester_role: str
    statement: str
    public_key: str
    signature: str
    valid: bool = True
    created_at: datetime
    revoked_at: datetime | None = None


class DossierCompleteness(BaseModel):
    """Dossier completeness check result."""

    system_id: str
    overall_complete: bool
    completion_percentage: float
    obligations_covered: int
    obligations_total: int
    evidence_count: int
    test_count: int
    signature_count: int
    missing_obligations: list[str] = []


class DossierExport(BaseModel):
    """Exported compliance dossier."""

    system_id: str
    system_name: str
    export_format: str
    generated_at: datetime
    content: str | dict[str, Any]
    completeness: DossierCompleteness


class ComplianceState(BaseModel):
    """Immutable compliance state snapshot."""

    id: str
    system_id: str
    state_hash: str
    previous_hash: str | None = None
    merkle_root: str
    trigger: str
    compliance_score: float
    policies_passed: int
    policies_failed: int
    commit_hash: str | None = None
    branch: str | None = None
    created_at: datetime
