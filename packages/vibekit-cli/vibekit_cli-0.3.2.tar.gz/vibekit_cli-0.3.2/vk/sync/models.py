"""
Data models for VibeKit sync operations.

These models represent the data structures synced between local and SaaS.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatusEnum(str, Enum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class RequirementType(str, Enum):
    """Requirement types aligned with conventional commits."""

    FEAT = "feat"
    FIX = "fix"
    REFACTOR = "refactor"
    PERF = "perf"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"


# ============================================================================
# Project Configuration
# ============================================================================


class TechStack(BaseModel):
    """Technology stack configuration."""

    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """
    Project configuration synced from SaaS.

    Stored locally at: .vk/config.yaml
    """

    project_id: str
    name: str
    description: str | None = None
    tech_stack: TechStack = Field(default_factory=TechStack)
    objectives: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ============================================================================
# Sprint Configuration
# ============================================================================


class Task(BaseModel):
    """Individual task within a sprint."""

    task_id: str
    title: str
    description: str | None = None
    requirement_id: str | None = None
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    estimate: int | None = None  # Story points or hours
    assignee: str | None = None
    commit_sha: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # Enriched task context for stateless intelligence (GSD-style)
    acceptance_criteria: list[str] = Field(default_factory=list)
    files_likely: list[str] = Field(default_factory=list)
    patterns_to_use: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    generated_by: str | None = None  # "sprint_goal", "requirement", "manual"


class Requirement(BaseModel):
    """Requirement within a sprint."""

    requirement_id: str
    title: str
    description: str | None = None
    type: RequirementType = RequirementType.FEAT
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    tasks: list[Task] = Field(default_factory=list)
    created_at: datetime | None = None


class SprintConfig(BaseModel):
    """
    Sprint configuration synced from SaaS.

    Stored locally at: .vk/sprints/current.yaml
    """

    sprint_id: str
    name: str
    goal: str | None = None
    status: str = "planning"  # planning, active, completed
    start_date: datetime | None = None
    end_date: datetime | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    created_at: datetime | None = None


# ============================================================================
# Rules Configuration
# ============================================================================


class CodingRule(BaseModel):
    """Individual coding rule."""

    rule_id: str
    title: str
    description: str
    category: str  # style, architecture, security, testing
    severity: str = "warning"  # error, warning, info
    examples: list[str] = Field(default_factory=list)


class RulesConfig(BaseModel):
    """
    Project rules synced from SaaS.

    Stored locally at: .claude/rules/*.md
    API returns rules as string arrays, not CodingRule objects.
    """

    coding_standards: list = Field(default_factory=list)  # Can be strings or CodingRule
    architecture_rules: list = Field(default_factory=list)
    security_rules: list = Field(default_factory=list)
    testing_rules: list = Field(default_factory=list)


# ============================================================================
# Roadmap Configuration
# ============================================================================


class MilestoneConfig(BaseModel):
    """Milestone within a roadmap phase."""

    id: str
    name: str
    completed: bool = False


class PhaseConfig(BaseModel):
    """
    Roadmap phase configuration synced from SaaS.

    Stored locally at: .vk/roadmap/phases.yaml
    """

    phase_id: str
    phase_number: int = 1
    name: str
    description: str | None = None
    status: str = "planned"  # planned, in_progress, completed
    milestones: list[MilestoneConfig] = Field(default_factory=list)
    target_date: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ============================================================================
# Agent Configuration
# ============================================================================


class AgentConfig(BaseModel):
    """
    Agent configuration synced from SaaS.

    Stored locally at: .claude/agents/*.md (Markdown with YAML frontmatter)

    Claude Code agent format:
    ---
    name: agent-name
    description: When to use this agent
    tools: Read, Grep, Glob
    model: sonnet
    ---

    System prompt content here...
    """

    agent_id: str
    name: str
    description: str
    enabled: bool = True
    priority: int = 0
    # Claude Code specific fields
    tools: str | None = None  # Comma-separated: "Read, Grep, Glob, Bash"
    model: str = "sonnet"  # sonnet, opus, haiku, inherit
    system_prompt: str | None = None  # Markdown content for the agent
    # Legacy fields (kept for backwards compat)
    triggers: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


# ============================================================================
# Tools Configuration
# ============================================================================


class LSPConfig(BaseModel):
    """LSP tool configuration."""

    enabled: bool = True
    languages: list[str] = Field(default_factory=list)
    symbol_operations: bool = True
    auto_import: bool = True
    settings: dict = Field(default_factory=dict)


class LinterConfig(BaseModel):
    """Linter tool configuration."""

    name: str
    enabled: bool = True
    config_file: str | None = None
    settings: dict = Field(default_factory=dict)


class QualityGate(BaseModel):
    """Quality gate configuration."""

    name: str
    enabled: bool = True
    required: bool = False  # Block commit if fails
    command: str | None = None
    settings: dict = Field(default_factory=dict)


class DocsConfig(BaseModel):
    """Documentation tool configuration (context7-style)."""

    enabled: bool = True
    sources: list[str] = Field(default_factory=list)  # Doc sources to include
    auto_fetch: bool = True
    cache_ttl: int = 3600  # Seconds


class ToolsConfig(BaseModel):
    """
    Tools configuration synced from SaaS.

    Stored locally at: .claude/tools/*.yaml
    """

    lsp: LSPConfig = Field(default_factory=LSPConfig)
    linters: list[LinterConfig] = Field(default_factory=list)
    quality_gates: list[QualityGate] = Field(default_factory=list)
    docs: DocsConfig = Field(default_factory=DocsConfig)


# ============================================================================
# Pattern Configuration
# ============================================================================


class PatternConfig(BaseModel):
    """
    Code pattern configuration synced from SaaS.

    Stored locally at: .claude/patterns/*.md
    """

    name: str
    description: str | None = None
    content: dict = Field(default_factory=dict)  # Includes body, severity, linter, etc.
    category: str | None = None  # security, quality, architecture, etc.
    enabled: bool = True
    source: str = "system"  # system, user, marketplace


# ============================================================================
# Workflow Configuration
# ============================================================================


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""

    name: str | None = None
    command: str
    continue_on_error: bool = False


class WorkflowConfig(BaseModel):
    """
    Automation workflow configuration synced from SaaS.

    Stored locally at: .claude/workflows/*.yaml
    """

    name: str
    description: str | None = None
    content: dict = Field(default_factory=dict)  # Includes steps, triggers
    category: str | None = None  # quality, workflow, planning
    enabled: bool = True
    source: str = "system"


# ============================================================================
# Hook Configuration
# ============================================================================


class HookConfig(BaseModel):
    """
    Event hook configuration synced from SaaS.

    Stored locally at: .claude/hooks/hooks.json
    """

    name: str
    description: str | None = None
    content: dict = Field(default_factory=dict)  # Includes event, matcher, action
    category: str | None = None  # quality, workflow, etc.
    enabled: bool = True
    source: str = "system"


# ============================================================================
# Sync Operations
# ============================================================================


class TaskStatus(BaseModel):
    """Task status update for push operations."""

    task_id: str
    status: TaskStatusEnum
    commit_sha: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SyncResult(BaseModel):
    """Result of a sync operation."""

    success: bool
    operation: str  # "pull" or "push"
    files_synced: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Full Sync Payload
# ============================================================================


class PullPayload(BaseModel):
    """Complete payload received from SaaS on pull."""

    project: ProjectConfig
    sprint: SprintConfig | None = None
    roadmap: list[PhaseConfig] = Field(default_factory=list)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    agents: list[AgentConfig] = Field(default_factory=list)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    # NEW: Additional content types
    patterns: list[PatternConfig] = Field(default_factory=list)
    workflows: list[WorkflowConfig] = Field(default_factory=list)
    hooks: list[HookConfig] = Field(default_factory=list)


class PushPayload(BaseModel):
    """Payload sent to SaaS on push."""

    project_id: str
    task_updates: list[TaskStatus] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    git_refs: dict = Field(default_factory=dict)  # commit hashes for tasks
    # Bidirectional sync: local changes pushed to SaaS
    rules: dict | None = None  # coding_standards, architecture_rules, etc.
    agents: list[dict] | None = None  # Agent configs
    tools: dict | None = None  # LSP, linters, quality_gates, docs
    hooks: list[dict] | None = None  # Hook configs
