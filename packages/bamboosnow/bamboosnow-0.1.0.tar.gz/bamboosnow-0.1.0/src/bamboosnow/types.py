"""
BambooSnow SDK Types

Type definitions for the BambooSnow SDK using Pydantic models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


# Generic type for paginated responses
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    per_page: int = Field(alias="perPage")
    total_pages: int = Field(alias="totalPages")

    class Config:
        populate_by_name = True


# Enums
class AgentStatus(str, Enum):
    """Agent deployment status."""

    DRAFT = "draft"
    BUILT = "built"
    PENDING = "pending"
    DEPLOYED = "deployed"
    PAUSED = "paused"
    FAILED = "failed"
    ARCHIVED = "archived"


class RunStatus(str, Enum):
    """Agent run status."""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplexityLevel(str, Enum):
    """Complexity level classification."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ThoughtStepType(str, Enum):
    """Thought step types (Sense-Think-Act loop)."""

    SENSE = "sense"
    THINK = "think"
    ACT = "act"


class ActionResult(str, Enum):
    """Action result outcomes."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


# Agent types
class AgentTemplate(BaseModel):
    """Agent template definition."""

    slug: str
    name: str
    description: str
    category: str
    triggers: list[str]
    capabilities: list[str]
    required_stack: dict[str, list[str]] = Field(alias="requiredStack")
    complexity: ComplexityLevel
    risk_level: RiskLevel = Field(alias="riskLevel")
    estimated_setup_minutes: int = Field(alias="estimatedSetupMinutes")

    class Config:
        populate_by_name = True


class Agent(BaseModel):
    """Agent instance."""

    id: str
    name: str
    description: str | None = None
    agent_type: str = Field(alias="agentType")
    template_slug: str | None = Field(None, alias="templateSlug")
    repository_id: str | None = Field(None, alias="repositoryId")
    project_id: str | None = Field(None, alias="projectId")
    status: AgentStatus
    triggers: list[str]
    pr_url: str | None = Field(None, alias="prUrl")
    pr_number: int | None = Field(None, alias="prNumber")
    total_runs: int = Field(alias="totalRuns")
    successful_runs: int = Field(alias="successfulRuns")
    deployment_pr_url: str | None = Field(None, alias="deploymentPrUrl")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True


class AgentHealthScore(BaseModel):
    """Agent health score breakdown."""

    overall_score: float = Field(alias="overallScore")
    reliability_score: float = Field(alias="reliabilityScore")
    efficiency_score: float = Field(alias="efficiencyScore")
    cost_score: float = Field(alias="costScore")
    activity_score: float = Field(alias="activityScore")
    grade: str

    class Config:
        populate_by_name = True


# Run types
class ThoughtStep(BaseModel):
    """A step in the agent's thought trace."""

    type: ThoughtStepType
    timestamp: datetime
    content: str
    metadata: dict[str, Any] | None = None


class AgentAction(BaseModel):
    """An action taken by the agent."""

    type: str
    description: str
    timestamp: datetime
    result: ActionResult
    details: dict[str, Any] | None = None


class ApprovalRequest(BaseModel):
    """Human-in-the-loop approval request."""

    action: str
    description: str
    risk: RiskLevel
    changes: list[str]


class AgentRun(BaseModel):
    """Agent run instance."""

    id: str
    agent_id: str = Field(alias="agentId")
    status: RunStatus
    trigger_type: str = Field(alias="triggerType")
    trigger_payload: dict[str, Any] = Field(alias="triggerPayload")
    thought_trace: list[ThoughtStep] = Field(alias="thoughtTrace")
    actions_taken: list[AgentAction] = Field(alias="actionsTaken")
    result: dict[str, Any] | None = None
    error_message: str | None = Field(None, alias="errorMessage")
    tokens_used: int = Field(alias="tokensUsed")
    cost_usd: float = Field(alias="costUsd")
    requires_approval: bool = Field(alias="requiresApproval")
    approval_request: ApprovalRequest | None = Field(None, alias="approvalRequest")
    started_at: datetime | None = Field(None, alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True


class RunSummary(BaseModel):
    """Run summary for list views."""

    id: str
    agent_id: str = Field(alias="agentId")
    agent_name: str = Field(alias="agentName")
    status: RunStatus
    trigger_type: str = Field(alias="triggerType")
    tokens_used: int = Field(alias="tokensUsed")
    cost_usd: float = Field(alias="costUsd")
    requires_approval: bool = Field(alias="requiresApproval")
    started_at: datetime | None = Field(None, alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    duration_seconds: int | None = Field(None, alias="durationSeconds")

    class Config:
        populate_by_name = True


# Repository types
class Repository(BaseModel):
    """Connected repository."""

    id: str
    provider: str
    full_name: str = Field(alias="fullName")
    name: str
    owner: str
    default_branch: str = Field(alias="defaultBranch")
    description: str | None = None
    language: str | None = None
    detected_stack: dict[str, list[str]] | None = Field(None, alias="detectedStack")
    is_private: bool = Field(alias="isPrivate")
    last_synced_at: datetime | None = Field(None, alias="lastSyncedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    class Config:
        populate_by_name = True


class AnalysisStatus(str, Enum):
    """Analysis status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(BaseModel):
    """Repository analysis."""

    id: str
    repository_id: str = Field(alias="repositoryId")
    status: AnalysisStatus
    progress_percent: int = Field(alias="progressPercent")
    summary: str | None = None
    bottlenecks: list[dict[str, Any]] | None = None
    recommendations: list[dict[str, Any]] | None = None
    detected_stack: dict[str, list[str]] | None = Field(None, alias="detectedStack")
    error_message: str | None = Field(None, alias="errorMessage")
    started_at: datetime | None = Field(None, alias="startedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True


# User types
class User(BaseModel):
    """User account."""

    id: str
    email: str
    name: str | None = None
    avatar_url: str | None = Field(None, alias="avatarUrl")
    github_username: str | None = Field(None, alias="githubUsername")
    plan: str
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True


class APIKey(BaseModel):
    """API key."""

    id: str
    name: str
    prefix: str
    last_used_at: datetime | None = Field(None, alias="lastUsedAt")
    expires_at: datetime | None = Field(None, alias="expiresAt")
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True
