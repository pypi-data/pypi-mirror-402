"""
Sync client for VibeKit pull/push operations.

Handles bidirectional synchronization between local folders and vkcli.com SaaS.
- .vk/ - Project management data (config, sprints, tasks, roadmap)
- .claude/ - Claude Code configuration (rules, patterns, agents, tools, hooks)
"""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from vk.client import VKClient
from vk.sync.models import (
    AgentConfig,
    DocsConfig,
    HookConfig,
    LinterConfig,
    LSPConfig,
    MilestoneConfig,
    PatternConfig,
    PhaseConfig,
    ProjectConfig,
    PullPayload,
    PushPayload,
    QualityGate,
    RulesConfig,
    SprintConfig,
    SyncResult,
    TaskStatus,
    TaskStatusEnum,
    TechStack,
    ToolsConfig,
    WorkflowConfig,
)


class SyncClient:
    """
    Client for syncing project data between local and SaaS.

    Usage:
        sync = SyncClient(project_root)

        # Pull all config from SaaS
        result = sync.pull()

        # Push task updates to SaaS
        result = sync.push()
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        client: Optional[VKClient] = None,
    ):
        """
        Initialize sync client.

        Args:
            project_root: Root directory of the project (default: cwd)
            client: Optional VKClient instance (creates one if not provided)
        """
        self.project_root = project_root or Path.cwd()
        self.vk_dir = self.project_root / ".vk"  # Project data (config, sprints, tasks)
        self.claude_dir = self.project_root / ".claude"  # Claude config (rules, patterns, agents)
        self._client = client

    @property
    def client(self) -> VKClient:
        """Get or create VK client, respecting project's api_url."""
        if self._client is None:
            # Read api_url from project config if available
            config = self._get_project_config()
            api_url = config.get("api_url") if config else None

            # Create VKClient with appropriate auth config
            if api_url:
                from vk.auth.config import get_config

                auth_config = get_config(api_url=api_url)
                self._client = VKClient(config=auth_config)
            else:
                self._client = VKClient()
        return self._client

    def _get_project_config(self) -> Optional[dict]:
        """Read project configuration from .vk/config.yaml."""
        config_file = self.vk_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        return None

    def is_initialized(self) -> bool:
        """Check if project has been initialized with vk init."""
        return (self.vk_dir / "config.yaml").exists() or (self.claude_dir / "config.yaml").exists()

    def get_project_id(self) -> Optional[str]:
        """Get project ID from local config."""
        config_file = self.vk_dir / "config.yaml"
        if not config_file.exists():
            return None

        with open(config_file) as f:
            config = yaml.safe_load(f)

        return config.get("project_id")

    def get_project_slug(self) -> Optional[str]:
        """Get project slug from local config."""
        config_file = self.vk_dir / "config.yaml"
        if not config_file.exists():
            return None

        with open(config_file) as f:
            config = yaml.safe_load(f)

        return config.get("project_slug") or config.get("slug")

    # ========================================================================
    # Pull Operations (SaaS -> Local)
    # ========================================================================

    def pull(self, no_cache: bool = False) -> SyncResult:
        """
        Pull all configuration from SaaS to local folders.

        Downloads to .vk/ (project data):
        - config.yaml: Project settings
        - sprints/current.yaml: Current sprint and tasks
        - roadmap/phases.yaml: Project roadmap

        Downloads to .claude/ (Claude config):
        - rules/*.md: Coding rules and patterns
        - patterns/*.md: Code patterns
        - agents/*.yaml: Agent configurations
        - tools/*.yaml: Tool configurations
        - hooks/hooks.json: Event hooks

        Also generates CLAUDE.md for Claude Code.

        Args:
            no_cache: If True, bypass local cache and fetch fresh from API

        Returns:
            SyncResult with details of synced files
        """
        result = SyncResult(success=True, operation="pull")

        try:
            # Ensure directories exist
            self.vk_dir.mkdir(exist_ok=True)
            self.claude_dir.mkdir(exist_ok=True)

            # Get project ID
            project_id = self.get_project_id()
            if not project_id:
                result.success = False
                result.errors.append("Project not initialized. Run 'vk init' first.")
                return result

            # Fetch full payload from SaaS (always fresh when no_cache=True)
            payload = self._fetch_pull_payload(project_id, no_cache=no_cache)

            # Sync project data to .vk/
            self._sync_project_config(payload.project)
            result.files_synced.append(".vk/config.yaml")

            if payload.sprint:
                self._sync_sprint_config(payload.sprint)
                result.files_synced.append(".vk/sprints/current.yaml")

            # Sync roadmap phases to .vk/
            if payload.roadmap:
                self._sync_roadmap(payload.roadmap)
                result.files_synced.append(".vk/roadmap/phases.yaml")

            # Sync Claude config to .claude/
            self._sync_rules(payload.rules)
            result.files_synced.extend(
                [
                    ".claude/rules/coding_standards.md",
                    ".claude/rules/architecture.md",
                    ".claude/rules/security.md",
                    ".claude/rules/testing.md",
                ]
            )

            self._sync_agents(payload.agents)
            for agent in payload.agents:
                result.files_synced.append(f".claude/agents/{agent.name}.md")

            self._sync_tools(payload.tools)
            result.files_synced.extend(
                [
                    ".claude/tools/lsp.yaml",
                    ".claude/tools/linters.yaml",
                    ".claude/tools/quality_gates.yaml",
                    ".claude/tools/docs.yaml",
                ]
            )

            # Sync patterns (code patterns and conventions) to .claude/
            if payload.patterns:
                self._sync_patterns(payload.patterns)
                for pattern in payload.patterns:
                    safe_name = pattern.name.replace(" ", "-").lower()
                    result.files_synced.append(f".claude/patterns/{safe_name}.md")

            # Sync workflows (automation sequences) to .claude/
            if payload.workflows:
                self._sync_workflows(payload.workflows)
                for workflow in payload.workflows:
                    safe_name = workflow.name.replace(" ", "-").lower()
                    result.files_synced.append(f".claude/workflows/{safe_name}.yaml")

            # Sync hooks (event triggers) to .claude/
            if payload.hooks:
                self._sync_hooks(payload.hooks)
                result.files_synced.append(".claude/hooks/hooks.json")

            # Generate CLAUDE.md
            from vk.generator import ClaudeMdGenerator

            generator = ClaudeMdGenerator(self.project_root)
            generator.generate()
            result.files_synced.append("CLAUDE.md")

            # Generate pre-commit configuration
            from vk.generator import write_precommit_config

            precommit_path = write_precommit_config(self.project_root)
            result.files_synced.append(".pre-commit-config.yaml")

            # Generate context files for token optimization (Claude config)
            self._generate_context_mini(payload.project, payload.sprint)
            result.files_synced.append(".claude/context-mini.yaml")

            self._generate_context_micro(payload.project, payload.sprint)
            result.files_synced.append(".claude/context-micro.yaml")

            # Cache goes to .vk/ (not Claude config)
            self._generate_context_cache(payload.project, payload.sprint)
            result.files_synced.append(".vk/context-cache.json")

            # Always ensure state directories exist (even without sprint)
            from vk.sync.state_manager import FilenameStateManager

            state_manager = FilenameStateManager(self.project_root)
            state_manager.ensure_directories()

            # Generate filename-based state structure (token-efficient navigation)
            if payload.sprint:
                state_files = state_manager.sync_from_sprint(payload.sprint)
                for sf in state_files:
                    result.files_synced.append(str(sf.relative_to(self.project_root)))

            # Generate codebase documentation (Layer 4 context)
            from vk.generator import generate_codebase_docs

            codebase_files = generate_codebase_docs(self.project_root)
            for cf in codebase_files:
                result.files_synced.append(str(cf.relative_to(self.project_root)))

            # Save state hash for conflict detection
            self._save_state_hash(payload)

            # ========================================================================
            # Generate GSD-style artifacts for stateless intelligence
            # ========================================================================

            # Generate PROJECT.md (living requirements)
            try:
                from vk.generator.project_md import generate_project_md

                # Extract quality gates from tools config
                quality_gates = payload.tools.quality_gates if payload.tools else None

                generate_project_md(
                    project=payload.project,
                    sprint=payload.sprint,
                    output_dir=self.project_root,
                    quality_gates=quality_gates,
                )
                result.files_synced.append("PROJECT.md")
            except Exception as e:
                result.errors.append(f"Failed to generate PROJECT.md: {e}")

            # Generate PLAN.md for each pending/active task
            if payload.sprint:
                try:
                    from vk.generator.plan_md import generate_all_task_plans

                    # Reuse quality_gates extracted above for PROJECT.md
                    plan_paths = generate_all_task_plans(
                        sprint=payload.sprint,
                        project=payload.project,
                        output_dir=self.project_root,
                        quality_gates=quality_gates,
                    )
                    for plan_path in plan_paths:
                        result.files_synced.append(str(plan_path.relative_to(self.project_root)))
                except Exception as e:
                    result.errors.append(f"Failed to generate task plans: {e}")

            # Generate INDEX.yaml with full awareness (agents, tools, context paths)
            try:
                from vk.sync.state_manager import FilenameStateManager

                state_mgr = FilenameStateManager(self.project_root)
                state_mgr.generate_index(
                    agents=payload.agents,
                    tools=payload.tools,
                )
                result.files_synced.append(".vk/INDEX.yaml")

                # Also generate STATE.md for human-readable state
                state_mgr.generate_state_md()
                result.files_synced.append(".vk/STATE.md")
            except Exception as e:
                result.errors.append(f"Failed to generate state files: {e}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _fetch_pull_payload(self, project_id: str, no_cache: bool = False) -> PullPayload:
        """Fetch all project data from SaaS via sync/pull endpoint.

        Args:
            project_id: Project ID to fetch
            no_cache: If True, adds cache-busting parameter to ensure fresh data
        """
        # Use consolidated sync/pull endpoint for efficiency
        url = f"/projects/{project_id}/sync/pull"
        if no_cache:
            # Add cache-busting parameter to ensure fresh data from API
            url += "?no_cache=true"
        data = self.client.get(url)

        # Transform API response to CLI models
        project_data = data.get("project", {})
        project = ProjectConfig(
            project_id=project_data.get("project_id") or project_data.get("id"),
            name=project_data.get("name", ""),
            description=project_data.get("description"),
            tech_stack=TechStack(
                languages=project_data.get("tech_stack", {}).get("languages", []),
                frameworks=project_data.get("tech_stack", {}).get("frameworks", []),
                databases=project_data.get("tech_stack", {}).get("databases", []),
                tools=project_data.get("tech_stack", {}).get("tools", []),
            ),
            objectives=project_data.get("objectives", []),
            success_criteria=project_data.get("success_criteria", []),
        )

        # Parse sprint data
        sprint = None
        sprint_data = data.get("sprint")
        if sprint_data:
            sprint = SprintConfig(**sprint_data)

        # Parse rules - API returns arrays of strings, convert to rule objects
        rules_data = data.get("rules", {})
        rules = self._parse_rules_response(rules_data)

        # Parse agents - API returns list of agent configs
        agents_data = data.get("agents", [])
        agents = self._parse_agents_response(agents_data)

        # Parse tools - API returns tools config
        tools_data = data.get("tools", {})
        tools = self._parse_tools_response(tools_data)

        # Parse roadmap phases
        roadmap_data = data.get("roadmap", [])
        roadmap = self._parse_roadmap_response(roadmap_data)

        # Parse patterns - NEW
        patterns_data = data.get("patterns", [])
        patterns = self._parse_patterns_response(patterns_data)

        # Parse workflows - NEW
        workflows_data = data.get("workflows", [])
        workflows = self._parse_workflows_response(workflows_data)

        # Parse hooks - NEW
        hooks_data = data.get("hooks", [])
        hooks = self._parse_hooks_response(hooks_data)

        return PullPayload(
            project=project,
            sprint=sprint,
            roadmap=roadmap,
            rules=rules,
            agents=agents,
            tools=tools,
            patterns=patterns,
            workflows=workflows,
            hooks=hooks,
        )

    def _fetch_rules(self, project_id: str) -> RulesConfig:
        """Fetch rules configuration from SaaS."""
        try:
            rules_data = self.client.get(f"/projects/{project_id}/rules")
            return RulesConfig(**rules_data)
        except Exception:
            return RulesConfig()

    def _fetch_agents(self, project_id: str) -> list[AgentConfig]:
        """Fetch agent configurations from SaaS."""
        try:
            agents_data = self.client.get(f"/projects/{project_id}/agents")
            return [AgentConfig(**a) for a in agents_data]
        except Exception:
            return []

    def _fetch_tools(self, project_id: str) -> ToolsConfig:
        """Fetch tools configuration from SaaS."""
        try:
            tools_data = self.client.get(f"/projects/{project_id}/tools")
            return ToolsConfig(**tools_data)
        except Exception:
            return ToolsConfig()

    def _parse_rules_response(self, rules_data: dict) -> RulesConfig:
        """Parse rules from API response (handles string arrays)."""
        return RulesConfig(
            coding_standards=rules_data.get("coding_standards", []),
            architecture_rules=rules_data.get("architecture_rules", []),
            security_rules=rules_data.get("security_rules", []),
            testing_rules=rules_data.get("testing_rules", []),
        )

    def _parse_agents_response(self, agents_data: list) -> list[AgentConfig]:
        """Parse agents from API response."""
        agents = []
        for a in agents_data:
            try:
                agents.append(
                    AgentConfig(
                        agent_id=a.get("name", a.get("agent_id", "unknown")),
                        name=a.get("name", ""),
                        description=a.get("description", ""),
                        enabled=a.get("enabled", True),
                        priority=a.get("priority", 0),
                        rules=a.get("rules", []),
                        settings=a.get("settings", {}),
                    )
                )
            except Exception:
                pass
        return agents

    def _parse_tools_response(self, tools_data: dict) -> ToolsConfig:
        """Parse tools from API response."""
        lsp_data = tools_data.get("lsp", {})
        lsp = LSPConfig(
            enabled=lsp_data.get("enabled", True),
            languages=lsp_data.get("languages", []),
            symbol_operations=lsp_data.get("symbol_operations", True),
            auto_import=lsp_data.get("auto_import", True),
        )

        linters = []
        for linter_data in tools_data.get("linters", []):
            linters.append(
                LinterConfig(
                    name=linter_data.get("name", ""),
                    enabled=linter_data.get("enabled", True),
                    config_file=linter_data.get("config_file"),
                    settings=linter_data.get("config", linter_data.get("settings", {})),
                )
            )

        quality_gates = []
        for g in tools_data.get("quality_gates", []):
            quality_gates.append(
                QualityGate(
                    name=g.get("name", ""),
                    enabled=g.get("enabled", True),
                    required=g.get("required", False),
                    settings=g.get("config", g.get("settings", {})),
                )
            )

        docs_data = tools_data.get("docs", {})
        docs = DocsConfig(
            enabled=docs_data.get("enabled", True),
            sources=docs_data.get("sources", []),
        )

        return ToolsConfig(
            lsp=lsp,
            linters=linters,
            quality_gates=quality_gates,
            docs=docs,
        )

    def _parse_roadmap_response(self, roadmap_data: list) -> list[PhaseConfig]:
        """Parse roadmap phases from API response."""
        phases = []
        for p in roadmap_data:
            try:
                milestones = [
                    MilestoneConfig(
                        id=m.get("id", ""),
                        name=m.get("name", ""),
                        completed=m.get("completed", False),
                    )
                    for m in p.get("milestones", [])
                ]
                phases.append(
                    PhaseConfig(
                        phase_id=p.get("phase_id", p.get("id", "")),
                        phase_number=p.get("phase_number", 1),
                        name=p.get("name", ""),
                        description=p.get("description"),
                        status=p.get("status", "planned"),
                        milestones=milestones,
                        target_date=p.get("target_date"),
                        started_at=p.get("started_at"),
                        completed_at=p.get("completed_at"),
                    )
                )
            except Exception:
                pass
        return phases

    def _parse_patterns_response(self, patterns_data: list) -> list[PatternConfig]:
        """Parse patterns from API response."""
        patterns = []
        for p in patterns_data:
            try:
                patterns.append(
                    PatternConfig(
                        name=p.get("name", "unknown"),
                        description=p.get("description", ""),
                        content=p.get("content", {}),
                        category=p.get("category"),
                        enabled=p.get("enabled", True),
                        source=p.get("source", "system"),
                    )
                )
            except Exception:
                pass
        return patterns

    def _parse_workflows_response(self, workflows_data: list) -> list[WorkflowConfig]:
        """Parse workflows from API response."""
        workflows = []
        for w in workflows_data:
            try:
                workflows.append(
                    WorkflowConfig(
                        name=w.get("name", "unknown"),
                        description=w.get("description", ""),
                        content=w.get("content", {}),
                        category=w.get("category"),
                        enabled=w.get("enabled", True),
                        source=w.get("source", "system"),
                    )
                )
            except Exception:
                pass
        return workflows

    def _parse_hooks_response(self, hooks_data: list) -> list[HookConfig]:
        """Parse hooks from API response."""
        hooks = []
        for h in hooks_data:
            try:
                hooks.append(
                    HookConfig(
                        name=h.get("name", "unknown"),
                        description=h.get("description", ""),
                        content=h.get("content", {}),
                        category=h.get("category"),
                        enabled=h.get("enabled", True),
                        source=h.get("source", "system"),
                    )
                )
            except Exception:
                pass
        return hooks

    def _sync_project_config(self, config: ProjectConfig) -> None:
        """Write project config to .vk/config.yaml.

        Preserves existing fields like api_url and project_slug that are not
        part of ProjectConfig but are important for local operation.
        """
        config_file = self.vk_dir / "config.yaml"

        # Read existing config to preserve local-only fields
        existing_data = {}
        if config_file.exists():
            with open(config_file) as f:
                existing_data = yaml.safe_load(f) or {}

        # Get new config data
        data = config.model_dump(mode="json", exclude_none=True)

        # Preserve local-only fields that shouldn't be overwritten
        local_fields = ["api_url", "project_slug", "slug"]
        for field in local_fields:
            if field in existing_data and field not in data:
                data[field] = existing_data[field]

        with open(config_file, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def _sync_sprint_config(self, sprint: SprintConfig) -> None:
        """Write sprint config to .vk/sprints/current.yaml."""
        sprints_dir = self.vk_dir / "sprints"
        sprints_dir.mkdir(exist_ok=True)

        # Create archive directory for completed sprints
        archive_dir = sprints_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        sprint_file = sprints_dir / "current.yaml"
        data = sprint.model_dump(mode="json", exclude_none=True)

        with open(sprint_file, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def _sync_rules(self, rules: RulesConfig) -> None:
        """Write rules to .claude/rules/*.md files."""
        rules_dir = self.claude_dir / "rules"
        rules_dir.mkdir(exist_ok=True)

        # Coding standards
        self._write_rules_file(
            rules_dir / "coding_standards.md",
            "Coding Standards",
            rules.coding_standards,
        )

        # Architecture rules
        self._write_rules_file(
            rules_dir / "architecture.md",
            "Architecture Rules",
            rules.architecture_rules,
        )

        # Security rules
        self._write_rules_file(
            rules_dir / "security.md",
            "Security Rules",
            rules.security_rules,
        )

        # Testing rules
        self._write_rules_file(
            rules_dir / "testing.md",
            "Testing Rules",
            rules.testing_rules,
        )

    def _write_rules_file(self, path: Path, title: str, rules: list) -> None:
        """Write a rules markdown file.

        Handles both string rules (from API) and CodingRule objects.
        """
        content = f"# {title}\n\n"

        if not rules:
            content += "_No rules configured._\n"
        else:
            for _i, rule in enumerate(rules, 1):
                # Handle string rules (from sync/pull API)
                if isinstance(rule, str):
                    content += f"- {rule}\n"
                # Handle CodingRule objects
                elif hasattr(rule, "title"):
                    content += f"## {rule.title}\n\n"
                    content += f"{rule.description}\n\n"
                    if rule.examples:
                        content += "**Examples:**\n"
                        for example in rule.examples:
                            content += f"- {example}\n"
                        content += "\n"
                # Handle dict rules
                elif isinstance(rule, dict):
                    if "title" in rule:
                        content += f"## {rule['title']}\n\n"
                        content += f"{rule.get('description', '')}\n\n"
                    else:
                        content += f"- {str(rule)}\n"
                else:
                    content += f"- {str(rule)}\n"

        with open(path, "w") as f:
            f.write(content)

    def _sync_agents(self, agents: list[AgentConfig]) -> None:
        """Write agent configs to .claude/agents/*.md (Claude Code format) with cross-agent awareness."""
        agents_dir = self.claude_dir / "agents"
        agents_dir.mkdir(exist_ok=True)

        # Clean up old .yaml files (migrating to .md format)
        for old_yaml in agents_dir.glob("*.yaml"):
            old_yaml.unlink()

        # Build agent inventory for cross-awareness
        agent_inventory = []
        for agent in agents:
            agent_inventory.append(
                {
                    "name": agent.name,
                    "purpose": agent.description[:50]
                    if len(agent.description) > 50
                    else agent.description,
                }
            )

        for agent in agents:
            # Write as .md file with YAML frontmatter (Claude Code format)
            agent_file = agents_dir / f"{agent.name}.md"

            # Build YAML frontmatter
            frontmatter = {
                "name": agent.name,
                "description": agent.description,
            }
            if agent.tools:
                frontmatter["tools"] = agent.tools
            if agent.model and agent.model != "sonnet":
                frontmatter["model"] = agent.model

            # Generate content
            lines = ["---"]
            lines.append(
                yaml.safe_dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
            )
            lines.append("---")
            lines.append("")
            lines.append(f"# {agent.name}")
            lines.append("")

            # Add system prompt or generate default
            if agent.system_prompt:
                lines.append(agent.system_prompt)
            else:
                # Generate default system prompt from description
                lines.append(agent.description)

            # Add Context Awareness section
            lines.append("")
            lines.append("## Context Awareness")
            lines.append("")
            lines.append("Before executing, read `.vk/INDEX.yaml` for current state:")
            lines.append("- Current sprint progress")
            lines.append("- Active/pending tasks")
            lines.append("- Next task to execute")

            # Add Available Agents section (exclude self)
            other_agents = [a for a in agent_inventory if a["name"] != agent.name]
            if other_agents:
                lines.append("")
                lines.append("## Available Agents for Delegation")
                lines.append("")
                lines.append("| Agent | Purpose |")
                lines.append("|-------|---------|")
                for other in other_agents:
                    lines.append(f"| {other['name']} | {other['purpose']} |")

            # Add Guidelines section
            if agent.rules:
                lines.append("")
                lines.append("## Guidelines")
                lines.append("")
                for rule in agent.rules:
                    lines.append(f"- {rule}")

            with open(agent_file, "w") as f:
                f.write("\n".join(lines) + "\n")

    def _sync_tools(self, tools: ToolsConfig) -> None:
        """Write tool configs to .claude/tools/*.yaml."""
        tools_dir = self.claude_dir / "tools"
        tools_dir.mkdir(exist_ok=True)

        # LSP config
        lsp_file = tools_dir / "lsp.yaml"
        with open(lsp_file, "w") as f:
            yaml.safe_dump(
                tools.lsp.model_dump(mode="json"),
                f,
                default_flow_style=False,
            )

        # Linters config
        linters_file = tools_dir / "linters.yaml"
        linters_data = [linter.model_dump(mode="json") for linter in tools.linters]
        with open(linters_file, "w") as f:
            yaml.safe_dump(linters_data, f, default_flow_style=False)

        # Quality gates config
        gates_file = tools_dir / "quality_gates.yaml"
        gates_data = [g.model_dump(mode="json") for g in tools.quality_gates]
        with open(gates_file, "w") as f:
            yaml.safe_dump(gates_data, f, default_flow_style=False)

        # Docs config
        docs_file = tools_dir / "docs.yaml"
        with open(docs_file, "w") as f:
            yaml.safe_dump(
                tools.docs.model_dump(mode="json"),
                f,
                default_flow_style=False,
            )

    def _sync_roadmap(self, phases: list[PhaseConfig]) -> None:
        """Write roadmap phases to .vk/roadmap/phases.yaml."""
        roadmap_dir = self.vk_dir / "roadmap"
        roadmap_dir.mkdir(exist_ok=True)

        phases_file = roadmap_dir / "phases.yaml"
        data = [p.model_dump(mode="json", exclude_none=True) for p in phases]

        with open(phases_file, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def _sync_patterns(self, patterns: list[PatternConfig]) -> None:
        """Write patterns to .claude/patterns/*.md files."""
        patterns_dir = self.claude_dir / "patterns"
        patterns_dir.mkdir(exist_ok=True)

        for pattern in patterns:
            # Sanitize name for filename
            safe_name = pattern.name.replace(" ", "-").lower()
            pattern_file = patterns_dir / f"{safe_name}.md"

            # Build markdown content
            content = f"# {pattern.name}\n\n"
            if pattern.description:
                content += f"{pattern.description}\n\n"
            if pattern.category:
                content += f"**Category**: {pattern.category}\n\n"

            # Include body from content dict
            body = pattern.content.get("body", "")
            if body:
                content += body

            with open(pattern_file, "w") as f:
                f.write(content)

    def _sync_workflows(self, workflows: list[WorkflowConfig]) -> None:
        """Write workflows to .claude/workflows/*.yaml files."""
        workflows_dir = self.claude_dir / "workflows"
        workflows_dir.mkdir(exist_ok=True)

        for workflow in workflows:
            # Sanitize name for filename
            safe_name = workflow.name.replace(" ", "-").lower()
            workflow_file = workflows_dir / f"{safe_name}.yaml"

            # Build workflow data
            data = {
                "name": workflow.name,
                "description": workflow.description,
                "category": workflow.category,
                "enabled": workflow.enabled,
                "source": workflow.source,
            }

            # Include content (steps, triggers, etc.)
            if workflow.content:
                data.update(workflow.content)

            with open(workflow_file, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def _sync_hooks(self, hooks: list[HookConfig]) -> None:
        """Write hooks to .claude/hooks/hooks.json file."""
        hooks_dir = self.claude_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        hooks_file = hooks_dir / "hooks.json"

        # Build hooks array for JSON
        hooks_data = []
        for hook in hooks:
            hook_entry = {
                "name": hook.name,
                "description": hook.description,
                "category": hook.category,
                "enabled": hook.enabled,
                "source": hook.source,
            }

            # Include content (event, matcher, action, etc.)
            if hook.content:
                hook_entry.update(hook.content)

            hooks_data.append(hook_entry)

        with open(hooks_file, "w") as f:
            json.dump(hooks_data, f, indent=2)

    # ========================================================================
    # Push Operations (Local -> SaaS)
    # ========================================================================

    def push(self, force: bool = False) -> SyncResult:
        """
        Push local changes to SaaS.

        Uploads:
        - Task status updates (started, completed, blocked)
        - Metrics (time spent, etc.)
        - Git refs (commit hashes linked to tasks)

        Args:
            force: Skip conflict detection and force push

        Returns:
            SyncResult with details of pushed data
        """
        result = SyncResult(success=True, operation="push")

        try:
            project_id = self.get_project_id()
            if not project_id:
                result.success = False
                result.errors.append("Project not initialized. Run 'vk init' first.")
                return result

            # Conflict detection (unless forced)
            if not force:
                conflict = self._check_for_conflicts(project_id)
                if conflict:
                    result.success = False
                    result.errors.append(
                        "Remote state has changed since last pull. "
                        "Run 'vk pull' to sync or use 'vk push --force' to override."
                    )
                    return result

            # Build push payload
            payload = self._build_push_payload(project_id)

            # Send to SaaS
            self._send_push_payload(payload)

            result.files_synced.append("task_updates")
            if payload.git_refs:
                result.files_synced.append("git_refs")
            if payload.metrics:
                result.files_synced.append("metrics")
            # Track bidirectional sync
            if payload.rules:
                result.files_synced.append("rules")
            if payload.agents:
                result.files_synced.append("agents")
            if payload.tools:
                result.files_synced.append("tools")
            if payload.hooks:
                result.files_synced.append("hooks")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _build_push_payload(self, project_id: str) -> PushPayload:
        """Build payload for push operation."""
        task_updates = self._get_task_updates()
        git_refs = self._get_git_refs()
        metrics = self._get_metrics()

        # Bidirectional sync: collect local rules/agents/tools/hooks changes
        rules = self._get_rules_updates()
        agents = self._get_agents_updates()
        tools = self._get_tools_updates()
        hooks = self._get_hooks_updates()

        return PushPayload(
            project_id=project_id,
            task_updates=task_updates,
            metrics=metrics,
            git_refs=git_refs,
            rules=rules,
            agents=agents,
            tools=tools,
            hooks=hooks,
        )

    def _get_task_updates(self) -> list[TaskStatus]:
        """Get task status updates from local sprint file."""
        sprint_file = self.vk_dir / "sprints" / "current.yaml"
        if not sprint_file.exists():
            return []

        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        updates = []
        for req in sprint_data.get("requirements", []):
            for task in req.get("tasks", []):
                updates.append(
                    TaskStatus(
                        task_id=task["task_id"],
                        status=TaskStatusEnum(task.get("status", "pending")),
                        commit_sha=task.get("commit_sha"),
                        started_at=task.get("started_at"),
                        completed_at=task.get("completed_at"),
                    )
                )

        return updates

    def _get_git_refs(self) -> dict:
        """Get git commit references for tasks."""
        refs = {}

        # Get recent commits that reference tasks
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-50"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                import re

                task_pattern = re.compile(r"TASK-[\w-]+")

                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    commit_sha = line.split()[0]
                    tasks = task_pattern.findall(line)
                    for task_id in tasks:
                        if task_id not in refs:
                            refs[task_id] = commit_sha

        except Exception:
            pass

        return refs

    def _get_metrics(self) -> dict:
        """Get local metrics for push."""
        metrics = {
            "last_sync": datetime.now().isoformat(),
        }

        # Add git stats
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                metrics["total_commits"] = int(result.stdout.strip())
        except Exception:
            pass

        return metrics

    def _get_rules_updates(self) -> Optional[dict]:
        """Read local rules from .claude/rules/*.md files for push."""
        rules_dir = self.claude_dir / "rules"
        if not rules_dir.exists():
            return None

        rules = {}

        # Map files to rule types
        file_map = {
            "coding_standards.md": "coding_standards",
            "architecture.md": "architecture_rules",
            "security.md": "security_rules",
            "testing.md": "testing_rules",
        }

        for filename, key in file_map.items():
            rule_file = rules_dir / filename
            if rule_file.exists():
                content = rule_file.read_text()
                # Parse markdown rules (lines starting with "- ")
                parsed_rules = []
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") and not line.startswith("- _No rules"):
                        parsed_rules.append(line[2:])  # Remove "- " prefix
                rules[key] = parsed_rules

        return rules if rules else None

    def _get_agents_updates(self) -> Optional[list]:
        """Read local agent configs from .claude/agents/*.md for push."""
        agents_dir = self.claude_dir / "agents"
        if not agents_dir.exists():
            return None

        agents = []

        # Read .md files (Claude Code format with YAML frontmatter)
        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text()
                # Parse YAML frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        system_prompt = parts[2].strip()
                        if frontmatter:
                            frontmatter["system_prompt"] = system_prompt
                            frontmatter["agent_id"] = frontmatter.get("name", agent_file.stem)
                            agents.append(frontmatter)
            except Exception:
                pass

        # Also read legacy .yaml files for backwards compat
        for agent_file in agents_dir.glob("*.yaml"):
            try:
                with open(agent_file) as f:
                    agent_data = yaml.safe_load(f)
                    if agent_data:
                        agents.append(agent_data)
            except Exception:
                pass

        return agents if agents else None

    def _get_tools_updates(self) -> Optional[dict]:
        """Read local tools config from .claude/tools/*.yaml for push."""
        tools_dir = self.claude_dir / "tools"
        if not tools_dir.exists():
            return None

        tools = {}

        # Read LSP config
        lsp_file = tools_dir / "lsp.yaml"
        if lsp_file.exists():
            try:
                with open(lsp_file) as f:
                    tools["lsp"] = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Read linters config
        linters_file = tools_dir / "linters.yaml"
        if linters_file.exists():
            try:
                with open(linters_file) as f:
                    tools["linters"] = yaml.safe_load(f) or []
            except Exception:
                pass

        # Read quality gates config
        quality_file = tools_dir / "quality_gates.yaml"
        if quality_file.exists():
            try:
                with open(quality_file) as f:
                    tools["quality_gates"] = yaml.safe_load(f) or []
            except Exception:
                pass

        # Read docs config
        docs_file = tools_dir / "docs.yaml"
        if docs_file.exists():
            try:
                with open(docs_file) as f:
                    tools["docs"] = yaml.safe_load(f) or {}
            except Exception:
                pass

        return tools if tools else None

    def _get_hooks_updates(self) -> Optional[list]:
        """Read local hook configs from .claude/hooks/hooks.json for push."""
        hooks_file = self.claude_dir / "hooks" / "hooks.json"
        if not hooks_file.exists():
            return None

        try:
            with open(hooks_file) as f:
                hooks_data = json.load(f)
            return hooks_data.get("hooks", []) if hooks_data else None
        except Exception:
            return None

    def _send_push_payload(self, payload: PushPayload) -> dict:
        """Send push payload to SaaS via /sync/push endpoint."""
        # Build request body
        body = {
            "task_updates": [
                {
                    "task_id": u.task_id,
                    "status": u.status.value,
                    "commit_sha": u.commit_sha,
                }
                for u in payload.task_updates
            ],
            "metrics": payload.metrics,
            "git_refs": payload.git_refs,
        }

        # Include bidirectional sync data if present
        if payload.rules is not None:
            body["rules"] = payload.rules
        if payload.agents is not None:
            body["agents"] = payload.agents
        if payload.tools is not None:
            body["tools"] = payload.tools
        if payload.hooks is not None:
            body["hooks"] = payload.hooks

        # Send complete payload to sync/push endpoint
        response = self.client.post(
            f"/projects/{payload.project_id}/sync/push",
            json=body,
        )
        return response

    # ========================================================================
    # Status Operations
    # ========================================================================

    def status(self) -> dict:
        """
        Get sync status comparing local and remote.

        Returns:
            Dictionary with sync status information
        """
        status = {
            "initialized": self.is_initialized(),
            "project_id": self.get_project_id(),
            "local_files": [],
            "needs_pull": False,
            "needs_push": False,
        }

        if not status["initialized"]:
            return status

        # Check what local files exist
        if (self.vk_dir / "config.yaml").exists():
            status["local_files"].append("config.yaml")
        if (self.vk_dir / "sprints" / "current.yaml").exists():
            status["local_files"].append("sprints/current.yaml")
        if (self.vk_dir / "rules").exists():
            status["local_files"].extend(
                [f"rules/{f.name}" for f in (self.vk_dir / "rules").glob("*.md")]
            )
        if (self.vk_dir / "agents").exists():
            status["local_files"].extend(
                [f"agents/{f.name}" for f in (self.vk_dir / "agents").glob("*.yaml")]
            )
        if (self.vk_dir / "tools").exists():
            status["local_files"].extend(
                [f"tools/{f.name}" for f in (self.vk_dir / "tools").glob("*.yaml")]
            )

        return status

    # ========================================================================
    # Context Generation (Token Optimization)
    # ========================================================================

    def _generate_context_mini(self, config: ProjectConfig, sprint: Optional[SprintConfig]) -> None:
        """
        Generate minimal context file for sub-agents (~800 tokens).

        This file contains only essential information that most agents need,
        avoiding the overhead of loading full CLAUDE.md or sprint config.
        """
        context = {
            "project_id": config.project_id,
            "name": config.name,
            "tech_stack": ", ".join(config.tech_stack.languages + config.tech_stack.frameworks),
        }

        # Add current task if sprint exists
        if sprint and sprint.requirements:
            # Find first pending or in_progress task
            for req in sprint.requirements:
                if hasattr(req, "tasks") and req.tasks:
                    for task in req.tasks:
                        if hasattr(task, "status") and task.status in ["pending", "in_progress"]:
                            context["current_task"] = {
                                "task_id": task.task_id
                                if hasattr(task, "task_id")
                                else task.get("task_id", ""),
                                "title": task.title
                                if hasattr(task, "title")
                                else task.get("title", ""),
                                "priority": task.priority
                                if hasattr(task, "priority")
                                else task.get("priority", "medium"),
                            }
                            break
                    if "current_task" in context:
                        break

        # Add quality gates from config
        config_file = self.vk_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                local_config = yaml.safe_load(f) or {}
                context["quality_gates"] = {
                    "coverage_threshold": local_config.get("coverage_threshold", 80),
                    "tests_required": local_config.get("quality_gates", {}).get(
                        "tests_required", True
                    ),
                    "lint_required": local_config.get("quality_gates", {}).get(
                        "lint_required", True
                    ),
                }
                context["commands"] = {
                    "test": local_config.get("project", {}).get("test_command", "pytest"),
                    "lint": local_config.get("project", {}).get("lint_command", "ruff check ."),
                }

        # Write context-mini.yaml to .claude/
        context_file = self.claude_dir / "context-mini.yaml"
        with open(context_file, "w") as f:
            yaml.safe_dump(context, f, default_flow_style=False, sort_keys=False)

    def _generate_context_cache(
        self, config: ProjectConfig, sprint: Optional[SprintConfig]
    ) -> None:
        """
        Generate pre-parsed context cache for sub-agents.

        This JSON file contains structured data that agents frequently need,
        avoiding repeated YAML parsing and file reads.
        """
        cache = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_id": config.project_id,
            "project_name": config.name,
            "tech_stack_summary": ", ".join(
                config.tech_stack.languages[:2] + config.tech_stack.frameworks[:2]
            ),
        }

        # Add sprint data if exists
        if sprint:
            cache["sprint_id"] = sprint.sprint_id
            cache["sprint_name"] = sprint.name
            cache["sprint_goal"] = sprint.goal

            # Build task index
            tasks = {}
            task_ids_by_status = {
                "pending": [],
                "in_progress": [],
                "completed": [],
                "blocked": [],
            }

            for req in sprint.requirements or []:
                req_tasks = req.tasks if hasattr(req, "tasks") else req.get("tasks", [])
                for task in req_tasks:
                    task_id = task.task_id if hasattr(task, "task_id") else task.get("task_id", "")
                    status = (
                        task.status if hasattr(task, "status") else task.get("status", "pending")
                    )

                    tasks[task_id] = {
                        "title": task.title if hasattr(task, "title") else task.get("title", ""),
                        "status": status,
                        "priority": task.priority
                        if hasattr(task, "priority")
                        else task.get("priority", "medium"),
                        "acceptance_criteria": (
                            task.acceptance_criteria
                            if hasattr(task, "acceptance_criteria")
                            else task.get("acceptance_criteria", [])
                        ),
                    }

                    if status in task_ids_by_status:
                        task_ids_by_status[status].append(task_id)

            cache["tasks"] = tasks
            cache["task_ids_by_status"] = task_ids_by_status
            cache["progress"] = {
                "total": len(tasks),
                "completed": len(task_ids_by_status["completed"]),
                "in_progress": len(task_ids_by_status["in_progress"]),
                "pending": len(task_ids_by_status["pending"]),
                "blocked": len(task_ids_by_status["blocked"]),
            }

        # Add quality config
        config_file = self.vk_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                local_config = yaml.safe_load(f) or {}
                cache["test_command"] = local_config.get("project", {}).get(
                    "test_command", "pytest"
                )
                cache["lint_command"] = local_config.get("project", {}).get(
                    "lint_command", "ruff check ."
                )
                cache["coverage_threshold"] = local_config.get("coverage_threshold", 80)

        # Write context-cache.json
        cache_file = self.vk_dir / "context-cache.json"
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)

    def _generate_context_micro(
        self, config: ProjectConfig, sprint: Optional[SprintConfig]
    ) -> None:
        """
        Generate micro context file for task execution (~200 tokens).

        Layer 0 context - the absolute minimum needed for task execution.
        Contains only:
        - Current task ID
        - Test command
        - Lint command
        """
        context = {}

        # Find current task ID (first pending or in_progress task)
        if sprint and sprint.requirements:
            for req in sprint.requirements:
                req_tasks = req.tasks if hasattr(req, "tasks") else req.get("tasks", [])
                for task in req_tasks:
                    status = (
                        task.status if hasattr(task, "status") else task.get("status", "pending")
                    )
                    if status in ["pending", "in_progress"]:
                        task_id = (
                            task.task_id if hasattr(task, "task_id") else task.get("task_id", "")
                        )
                        context["task"] = task_id
                        break
                if "task" in context:
                    break

        # Get commands from config
        config_file = self.vk_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                local_config = yaml.safe_load(f) or {}
                context["test"] = local_config.get("project", {}).get("test_command", "pytest")
                context["lint"] = local_config.get("project", {}).get(
                    "lint_command", "ruff check ."
                )

        # Write context-micro.yaml to .claude/
        context_file = self.claude_dir / "context-micro.yaml"
        with open(context_file, "w") as f:
            f.write("# .claude/context-micro.yaml (auto-generated)\n")
            if "task" in context:
                f.write(f"task: {context['task']}\n")
            if "test" in context:
                f.write(f"test: {context['test']}\n")
            if "lint" in context:
                f.write(f"lint: {context['lint']}\n")

    # ========================================================================
    # AI Content Generation
    # ========================================================================

    def generate_content(self) -> dict:
        """
        Generate AI-powered content for the project.

        Calls the /generate/all endpoint to create:
        - Project-specific coding rules
        - Code patterns for the tech stack
        - Enhanced CLAUDE.md sections

        Returns:
            Dict with success status and files written
        """
        result = {"success": False, "files_written": []}

        try:
            project_id = self.get_project_id()
            if not project_id:
                result["error"] = "Project not initialized"
                return result

            # Call generate/all endpoint
            response = self.client.post(
                f"/projects/{project_id}/generate/all",
                json={
                    "rules": True,
                    "patterns": True,
                    "agents": False,  # Agents are opt-in
                    "claude_md": True,
                },
            )

            if not response.get("generated"):
                result["error"] = response.get("detail", "Generation failed")
                return result

            # Write generated rules to .claude/rules/generated/
            if "rules" in response:
                files = self._write_generated_rules(response["rules"])
                result["files_written"].extend(files)

            # Write generated patterns to .claude/patterns/generated/
            if "patterns" in response:
                files = self._write_generated_patterns(response["patterns"])
                result["files_written"].extend(files)

            # Enhance CLAUDE.md with generated sections
            if "claude_md" in response:
                files = self._enhance_claude_md(response["claude_md"])
                result["files_written"].extend(files)

            result["success"] = True

        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "not available" in error_msg.lower():
                result["error"] = "not_configured"
            else:
                result["error"] = error_msg

        return result

    def _write_generated_rules(self, rules: dict) -> list[str]:
        """Write AI-generated rules to .claude/rules/generated/ directory."""
        files_written = []

        generated_dir = self.claude_dir / "rules" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)

        # Write each rule category
        rule_files = {
            "coding_standards": "coding_ai.md",
            "architecture_rules": "architecture_ai.md",
            "security_rules": "security_ai.md",
            "testing_rules": "testing_ai.md",
        }

        for key, filename in rule_files.items():
            if key in rules and rules[key]:
                content = f"# AI-Generated {key.replace('_', ' ').title()}\n\n"
                content += "_Generated based on your tech stack._\n\n"
                for rule in rules[key]:
                    content += f"- {rule}\n"

                rule_file = generated_dir / filename
                with open(rule_file, "w") as f:
                    f.write(content)

                files_written.append(f".claude/rules/generated/{filename}")

        return files_written

    def _write_generated_patterns(self, patterns: list) -> list[str]:
        """Write AI-generated patterns to .claude/patterns/generated/ directory."""
        files_written = []

        generated_dir = self.claude_dir / "patterns" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)

        for pattern in patterns:
            name = pattern.get("name", "pattern")
            safe_name = name.lower().replace(" ", "-").replace("/", "-")
            filename = f"{safe_name}.md"

            content = f"# {name}\n\n"
            if pattern.get("description"):
                content += f"{pattern['description']}\n\n"
            if pattern.get("category"):
                content += f"**Category**: {pattern['category']}\n\n"

            # Add code body
            body = pattern.get("content", {}).get("body", "")
            if body:
                content += "## Example\n\n"
                content += f"```\n{body}\n```\n"

            pattern_file = generated_dir / filename
            with open(pattern_file, "w") as f:
                f.write(content)

            files_written.append(f".claude/patterns/generated/{filename}")

        return files_written

    def _enhance_claude_md(self, claude_md_sections: dict) -> list[str]:
        """Enhance CLAUDE.md with AI-generated sections."""
        files_written = []

        # Write generated sections to a separate file
        generated_file = self.claude_dir / "claude-md-generated.md"

        content = "# AI-Generated CLAUDE.md Enhancements\n\n"
        content += "_Include this content in your CLAUDE.md or use as reference._\n\n"

        if claude_md_sections.get("overview"):
            content += "## Project Overview\n\n"
            content += f"{claude_md_sections['overview']}\n\n"

        if claude_md_sections.get("architecture_notes"):
            content += "## Architecture Notes\n\n"
            notes = claude_md_sections["architecture_notes"]
            if isinstance(notes, list):
                for note in notes:
                    content += f"- {note}\n"
            else:
                content += f"{notes}\n"
            content += "\n"

        if claude_md_sections.get("common_tasks"):
            content += "## Common Tasks\n\n"
            tasks = claude_md_sections["common_tasks"]
            if isinstance(tasks, list):
                for task in tasks:
                    content += f"- {task}\n"
            else:
                content += f"{tasks}\n"
            content += "\n"

        with open(generated_file, "w") as f:
            f.write(content)

        files_written.append(".claude/claude-md-generated.md")

        return files_written

    # ========================================================================
    # AI Studio Generated Content Sync
    # ========================================================================

    def pull_generated(self, include_claude_md: bool = True) -> SyncResult:
        """
        Pull AI Studio generated content as Claude Code plugin files.

        This method fetches all content from AI Studio (agents, commands, skills,
        hooks, rules, patterns) and writes them as properly formatted Claude Code
        plugin files to .claude/ directory.

        Args:
            include_claude_md: Also generate CLAUDE.md from project data

        Returns:
            SyncResult with details of synced files
        """
        result = SyncResult(success=True, operation="pull_generated")

        try:
            project_id = self.get_project_id()
            if not project_id:
                result.success = False
                result.errors.append("Project not initialized. Run 'vk init' first.")
                return result

            # Fetch generated bundle from API
            response = self.client.post(
                f"/projects/{project_id}/content/bundle",
                json={
                    "include_claude_md": include_claude_md,
                    "include_sprint_context": True,
                },
            )

            files = response.get("files", {})
            file_count = response.get("file_count", 0)

            if not files:
                result.warnings.append("No content to sync. Create content in AI Studio first.")
                return result

            # Write each file to disk
            for file_path, content in files.items():
                # Ensure path is within .claude/ or project root (for CLAUDE.md)
                if file_path.startswith(".claude/") or file_path == "CLAUDE.md":
                    full_path = self.project_root / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(full_path, "w") as f:
                        f.write(content)

                    result.files_synced.append(file_path)

            result.message = f"Synced {len(result.files_synced)} generated files"

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _sync_commands(self, commands_data: list) -> list[str]:
        """Write command configs to .claude/commands/*.md files."""
        commands_dir = self.claude_dir / "commands"
        commands_dir.mkdir(exist_ok=True)

        files_written = []

        for cmd in commands_data:
            name = cmd.get("name", "unknown")
            safe_name = name.replace(" ", "-").lower()
            cmd_file = commands_dir / f"{safe_name}.md"

            # Build YAML frontmatter
            frontmatter = {"name": name}
            if cmd.get("description"):
                frontmatter["description"] = cmd["description"]

            content = cmd.get("content", {})
            if content.get("argument_hint"):
                frontmatter["argument-hint"] = content["argument_hint"]
            if content.get("allowed_tools"):
                frontmatter["allowed-tools"] = ", ".join(content["allowed_tools"])
            if content.get("context"):
                frontmatter["context"] = content["context"]
            if content.get("agent"):
                frontmatter["agent"] = content["agent"]

            # Generate file content
            lines = ["---"]
            lines.append(
                yaml.safe_dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
            )
            lines.append("---")
            lines.append("")

            # Add command body
            body = content.get("content", "")
            if body:
                lines.append(body)

            with open(cmd_file, "w") as f:
                f.write("\n".join(lines) + "\n")

            files_written.append(f".claude/commands/{safe_name}.md")

        return files_written

    def _sync_skills(self, skills_data: list) -> list[str]:
        """Write skill configs to .claude/skills/*/SKILL.md files."""
        skills_dir = self.claude_dir / "skills"
        skills_dir.mkdir(exist_ok=True)

        files_written = []

        for skill in skills_data:
            name = skill.get("name", "unknown")
            safe_name = name.replace(" ", "-").lower()
            skill_subdir = skills_dir / safe_name
            skill_subdir.mkdir(exist_ok=True)
            skill_file = skill_subdir / "SKILL.md"

            # Build YAML frontmatter
            frontmatter = {"name": name}
            if skill.get("description"):
                frontmatter["description"] = skill["description"]

            content = skill.get("content", {})
            if content.get("languages"):
                frontmatter["languages"] = content["languages"]
            if content.get("user_invocable"):
                frontmatter["user-invocable"] = content["user_invocable"]
            if content.get("default_enabled") is False:
                frontmatter["default-enabled"] = False

            # Generate file content
            lines = ["---"]
            lines.append(
                yaml.safe_dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
            )
            lines.append("---")
            lines.append("")

            # Add skill body
            if content.get("intro"):
                lines.append(content["intro"])
                lines.append("")

            body = content.get("content", "")
            if body:
                lines.append(body)

            with open(skill_file, "w") as f:
                f.write("\n".join(lines) + "\n")

            files_written.append(f".claude/skills/{safe_name}/SKILL.md")

        return files_written

    # ========================================================================
    # Conflict Detection
    # ========================================================================

    def _compute_state_hash(self, payload: PullPayload) -> str:
        """
        Compute hash of remote state for conflict detection.

        Hashes the sprint data to detect if server state changed since last pull.
        """
        if not payload.sprint:
            return ""

        # Create a stable representation of sprint state
        state_data = {
            "sprint_id": payload.sprint.sprint_id,
            "name": payload.sprint.name,
            "goal": payload.sprint.goal,
            "tasks": sorted(
                [
                    {
                        "task_id": task.task_id
                        if hasattr(task, "task_id")
                        else task.get("task_id"),
                        "status": task.status if hasattr(task, "status") else task.get("status"),
                        "title": task.title if hasattr(task, "title") else task.get("title"),
                    }
                    for req in (payload.sprint.requirements or [])
                    for task in (req.tasks if hasattr(req, "tasks") else req.get("tasks", []))
                ],
                key=lambda t: t["task_id"],
            ),
        }

        # Hash the stable representation
        state_str = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()

    def _save_state_hash(self, payload: PullPayload) -> None:
        """Save current state hash after pull for conflict detection."""
        state_hash = self._compute_state_hash(payload)
        if state_hash:
            state_file = self.vk_dir / ".state_hash"
            state_file.write_text(state_hash)

    def _get_local_state_hash(self) -> Optional[str]:
        """Get saved state hash from last pull."""
        state_file = self.vk_dir / ".state_hash"
        if state_file.exists():
            return state_file.read_text().strip()
        return None

    def _check_for_conflicts(self, project_id: str) -> bool:
        """
        Check if remote state has changed since last pull.

        Returns:
            True if conflict detected (remote changed), False otherwise
        """
        try:
            # Get local state hash from last pull
            local_hash = self._get_local_state_hash()
            if not local_hash:
                # No previous state, allow push
                return False

            # Fetch current remote state
            url = f"/projects/{project_id}/sync/pull"
            data = self.client.get(url)

            # Parse sprint data
            sprint_data = data.get("sprint")
            if not sprint_data:
                # No sprint on server, allow push
                return False

            # Create minimal payload for hash computation
            from vk.sync.models import SprintConfig

            sprint = SprintConfig(**sprint_data)
            remote_payload = PullPayload(
                project=ProjectConfig(
                    project_id=project_id,
                    name="",
                    tech_stack=TechStack(),
                ),
                sprint=sprint,
                roadmap=[],
                rules=RulesConfig(),
                agents=[],
                tools=ToolsConfig(),
                patterns=[],
                workflows=[],
                hooks=[],
            )

            # Compute remote hash
            remote_hash = self._compute_state_hash(remote_payload)

            # Compare hashes
            return local_hash != remote_hash

        except Exception:
            # On error, allow push (fail open)
            return False
