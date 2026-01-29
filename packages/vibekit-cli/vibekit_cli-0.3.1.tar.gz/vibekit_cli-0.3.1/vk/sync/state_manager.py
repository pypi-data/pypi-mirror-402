"""
Filename-based state manager for VibeKit.

Enables AI agents to understand project state from file structure alone,
without reading file contents. Uses hybrid approach:
- Directory = status (tasks/pending/, tasks/active/, etc.)
- Filename = metadata (001.p0.iter3.md = task 001, priority 0, iteration 3)

Token savings: ~90% reduction in context loading operations.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from vk.sync.models import (
    SprintConfig,
    Task,
    TaskPriority,
    TaskStatusEnum,
)

# =============================================================================
# Constants
# =============================================================================

PRIORITY_MAP = {
    TaskPriority.HIGH: "p0",
    TaskPriority.MEDIUM: "p1",
    TaskPriority.LOW: "p2",
    "high": "p0",
    "medium": "p1",
    "low": "p2",
}

PRIORITY_REVERSE = {
    "p0": TaskPriority.HIGH,
    "p1": TaskPriority.MEDIUM,
    "p2": TaskPriority.LOW,
}

STATUS_DIRS = {
    TaskStatusEnum.PENDING: "pending",
    TaskStatusEnum.IN_PROGRESS: "active",
    TaskStatusEnum.COMPLETED: "done",
    TaskStatusEnum.BLOCKED: "blocked",
    "pending": "pending",
    "in_progress": "active",
    "completed": "done",
    "blocked": "blocked",
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ParsedFilename:
    """Parsed state information from a filename."""

    task_id: str
    priority: str  # p0, p1, p2
    status: str  # from directory
    iteration: Optional[int] = None
    max_iterations: Optional[int] = None
    dependency: Optional[str] = None
    dependencies_count: Optional[int] = None
    raw_filename: str = ""
    directory: str = ""

    @property
    def priority_enum(self) -> TaskPriority:
        """Get priority as enum."""
        return PRIORITY_REVERSE.get(self.priority, TaskPriority.MEDIUM)

    @property
    def status_enum(self) -> TaskStatusEnum:
        """Get status as enum."""
        status_map = {
            "pending": TaskStatusEnum.PENDING,
            "active": TaskStatusEnum.IN_PROGRESS,
            "done": TaskStatusEnum.COMPLETED,
            "blocked": TaskStatusEnum.BLOCKED,
        }
        return status_map.get(self.status, TaskStatusEnum.PENDING)


@dataclass
class IndexData:
    """Data structure for INDEX.yaml."""

    sprint_id: str
    sprint_progress: int
    sprint_status: str
    tasks_total: int
    tasks_pending: int
    tasks_active: int
    tasks_done: int
    tasks_blocked: int
    next_task: Optional[str]
    next_task_path: Optional[str]
    updated: datetime


# =============================================================================
# Filename State Manager
# =============================================================================


class FilenameStateManager:
    """
    Manages project state through filesystem structure.

    Enables token-efficient navigation where AI agents can understand
    project state from `ls` commands alone.

    Directory structure:
        .vk/
        ├── INDEX.yaml                    # Master navigation
        ├── STATE.md                      # Human-readable snapshot
        ├── sprints/
        │   ├── active/
        │   │   └── SPRINT-001.p65.md    # Progress in filename
        │   └── archive/
        ├── tasks/
        │   ├── pending/
        │   │   └── 001.p0.md            # Priority in filename
        │   ├── active/
        │   │   └── 002.p1.iter3.md      # Iteration tracking
        │   ├── done/
        │   └── blocked/
        │       └── 003.p1.dep002.md     # Dependency visible

    Naming convention:
        {task_id}.{priority}.{metadata}.md

    Examples:
        - 001.p0.md               (critical priority, ready)
        - 002.p1.iter3.md         (high priority, iteration 3)
        - 003.p1.dep002.md        (blocked by task 002)
        - SPRINT-001.p65.md       (65% complete)
    """

    # Regex patterns for parsing filenames
    TASK_PATTERN = re.compile(
        r"^(?P<task_id>[A-Za-z0-9_-]+)"  # Task ID
        r"\.(?P<priority>p[0-2])"  # Priority (p0, p1, p2)
        r"(?:\.iter(?P<iter>\d+)(?:of(?P<max>\d+))?)?"  # Optional iteration
        r"(?:\.dep(?P<dep>[A-Za-z0-9_-]+))?"  # Optional single dependency
        r"(?:\.deps(?P<deps_count>\d+))?"  # Optional multiple deps count
        r"\.md$"
    )

    SPRINT_PATTERN = re.compile(
        r"^(?P<sprint_id>SPRINT-[A-Za-z0-9_-]+)"  # Sprint ID
        r"\.p(?P<progress>\d+)"  # Progress percentage
        r"\.md$"
    )

    def __init__(self, project_root: Path):
        """
        Initialize state manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.vk_dir = project_root / ".vk"
        self.tasks_dir = self.vk_dir / "tasks"
        self.sprints_dir = self.vk_dir / "sprints"

    # =========================================================================
    # Directory Setup
    # =========================================================================

    def ensure_directories(self) -> None:
        """Create all required directories."""
        dirs = [
            self.tasks_dir / "pending",
            self.tasks_dir / "active",
            self.tasks_dir / "done",
            self.tasks_dir / "blocked",
            self.sprints_dir / "active",
            self.sprints_dir / "archive",
            self.vk_dir / "plans" / "ready",
            self.vk_dir / "plans" / "executing",
            self.vk_dir / "plans" / "done",
            self.vk_dir / "prompts",
            self.vk_dir / "prompts" / "agents",
            self.vk_dir / "codebase",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Filename Generation
    # =========================================================================

    def generate_task_filename(
        self,
        task_id: str,
        priority: TaskPriority | str,
        iteration: Optional[int] = None,
        max_iterations: Optional[int] = None,
        dependency: Optional[str] = None,
        dependencies_count: Optional[int] = None,
    ) -> str:
        """
        Generate a state-encoded filename for a task.

        Args:
            task_id: Task identifier (e.g., "001", "TASK-001")
            priority: Task priority (high/medium/low or p0/p1/p2)
            iteration: Current iteration number (for self-healing)
            max_iterations: Maximum iterations allowed
            dependency: Single blocking task ID
            dependencies_count: Count of multiple dependencies

        Returns:
            Filename string (e.g., "001.p0.iter3.md")
        """
        # Normalize priority
        if isinstance(priority, TaskPriority):
            p = PRIORITY_MAP[priority]
        elif isinstance(priority, str):
            p = PRIORITY_MAP.get(priority.lower(), priority)
        else:
            p = "p1"

        # Clean task ID (remove any existing extension)
        clean_id = task_id.replace(".md", "").split(".")[0]

        # Build filename parts
        parts = [clean_id, p]

        if iteration is not None:
            if max_iterations:
                parts.append(f"iter{iteration}of{max_iterations}")
            else:
                parts.append(f"iter{iteration}")

        if dependency:
            parts.append(f"dep{dependency}")
        elif dependencies_count and dependencies_count > 1:
            parts.append(f"deps{dependencies_count}")

        return ".".join(parts) + ".md"

    def generate_sprint_filename(self, sprint_id: str, progress: int) -> str:
        """
        Generate a state-encoded filename for a sprint.

        Args:
            sprint_id: Sprint identifier (e.g., "SPRINT-001")
            progress: Progress percentage (0-100)

        Returns:
            Filename string (e.g., "SPRINT-001.p65.md")
        """
        # Ensure sprint ID has prefix
        if not sprint_id.startswith("SPRINT-"):
            sprint_id = f"SPRINT-{sprint_id}"

        # Clamp progress
        progress = max(0, min(100, progress))

        return f"{sprint_id}.p{progress:02d}.md"

    # =========================================================================
    # Filename Parsing
    # =========================================================================

    def parse_task_filename(self, filepath: Path) -> Optional[ParsedFilename]:
        """
        Parse state information from a task filename.

        Args:
            filepath: Path to the task file

        Returns:
            ParsedFilename with extracted state, or None if not parseable
        """
        filename = filepath.name
        directory = filepath.parent.name

        match = self.TASK_PATTERN.match(filename)
        if not match:
            return None

        return ParsedFilename(
            task_id=match.group("task_id"),
            priority=match.group("priority"),
            status=directory,
            iteration=int(match.group("iter")) if match.group("iter") else None,
            max_iterations=int(match.group("max")) if match.group("max") else None,
            dependency=match.group("dep"),
            dependencies_count=(
                int(match.group("deps_count")) if match.group("deps_count") else None
            ),
            raw_filename=filename,
            directory=directory,
        )

    def parse_sprint_filename(self, filepath: Path) -> dict:
        """
        Parse state information from a sprint filename.

        Args:
            filepath: Path to the sprint file

        Returns:
            Dict with sprint_id and progress, or empty dict if not parseable
        """
        filename = filepath.name

        match = self.SPRINT_PATTERN.match(filename)
        if not match:
            return {}

        return {
            "sprint_id": match.group("sprint_id"),
            "progress": int(match.group("progress")),
            "status": filepath.parent.name,
        }

    # =========================================================================
    # State Transitions
    # =========================================================================

    def transition_task(
        self,
        task_id: str,
        new_status: TaskStatusEnum | str,
        priority: Optional[str] = None,
        iteration: Optional[int] = None,
        max_iterations: Optional[int] = None,
        dependency: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Transition a task to a new state (move and rename file).

        Args:
            task_id: Task identifier
            new_status: New status for the task
            priority: Priority (if changing)
            iteration: Iteration number (if applicable)
            max_iterations: Max iterations (if applicable)
            dependency: Blocking dependency (if blocked)

        Returns:
            New file path, or None if task not found
        """
        # Find current task file
        current_file = self._find_task_file(task_id)
        if not current_file:
            return None

        # Parse current state
        current_state = self.parse_task_filename(current_file)
        if not current_state:
            return None

        # Determine new directory
        if isinstance(new_status, TaskStatusEnum):
            new_dir_name = STATUS_DIRS[new_status]
        else:
            new_dir_name = STATUS_DIRS.get(new_status, new_status)

        new_dir = self.tasks_dir / new_dir_name

        # Generate new filename
        new_priority = priority or current_state.priority
        new_filename = self.generate_task_filename(
            task_id=task_id,
            priority=new_priority,
            iteration=iteration,
            max_iterations=max_iterations,
            dependency=dependency,
        )

        new_path = new_dir / new_filename

        # Move file
        new_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current_file), str(new_path))

        return new_path

    def update_sprint_progress(self, sprint_id: str, new_progress: int) -> Optional[Path]:
        """
        Update sprint progress by renaming the sprint file.

        Args:
            sprint_id: Sprint identifier
            new_progress: New progress percentage

        Returns:
            New file path, or None if sprint not found
        """
        # Find current sprint file
        current_file = self._find_sprint_file(sprint_id)
        if not current_file:
            return None

        # Generate new filename
        new_filename = self.generate_sprint_filename(sprint_id, new_progress)
        new_path = current_file.parent / new_filename

        # Rename file
        shutil.move(str(current_file), str(new_path))

        return new_path

    # =========================================================================
    # State Queries (Token-Efficient)
    # =========================================================================

    def get_tasks_by_status(self, status: str) -> list[ParsedFilename]:
        """
        Get all tasks with a given status from directory listing.

        This is the token-efficient way to query task state -
        just listing files, not reading contents.

        Args:
            status: Directory name (pending, active, done, blocked)

        Returns:
            List of parsed task filenames
        """
        status_dir = self.tasks_dir / status
        if not status_dir.exists():
            return []

        tasks = []
        for f in status_dir.glob("*.md"):
            parsed = self.parse_task_filename(f)
            if parsed:
                tasks.append(parsed)

        # Sort by priority (p0 first), then by task_id
        tasks.sort(key=lambda t: (t.priority, t.task_id))
        return tasks

    def get_ready_tasks(self) -> list[ParsedFilename]:
        """
        Get tasks ready to execute (pending without blocking dependencies).

        Returns:
            List of ready tasks, sorted by priority
        """
        pending = self.get_tasks_by_status("pending")
        # Tasks without dep suffix are ready
        return [t for t in pending if not t.dependency]

    def get_next_task(self) -> Optional[ParsedFilename]:
        """
        Get the highest priority ready task.

        Returns:
            Next task to execute, or None if no ready tasks
        """
        ready = self.get_ready_tasks()
        return ready[0] if ready else None

    def get_sprint_progress(self) -> dict:
        """
        Get current sprint progress from filename and current.yaml.

        Combines:
        1. Progress from encoded filename (SPRINT-001.p65.md) for stateless reading
        2. Name and goal from current.yaml for rich context

        Returns:
            Dict with sprint_id, progress, status, name, goal
        """
        result = {}

        # Try stateless approach first (encoded filename for progress)
        active_dir = self.sprints_dir / "active"
        if active_dir.exists():
            for f in active_dir.glob("SPRINT-*.md"):
                result = self.parse_sprint_filename(f)
                break

        # Always read name and goal from current.yaml (they're not in filename)
        current_file = self.sprints_dir / "current.yaml"
        if current_file.exists():
            try:
                sprint_data = yaml.safe_load(current_file.read_text())
                if sprint_data:
                    # If we didn't get data from filename, calculate progress
                    if not result:
                        total_tasks = 0
                        done_tasks = 0
                        for req in sprint_data.get("requirements", []):
                            for task in req.get("tasks", []):
                                total_tasks += 1
                                if task.get("status") == "completed":
                                    done_tasks += 1

                        progress = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0

                        result = {
                            "sprint_id": sprint_data.get("sprint_id", ""),
                            "status": sprint_data.get("status", "active"),
                            "progress": progress,
                        }

                    # Always add name and goal from current.yaml
                    result["name"] = sprint_data.get("name", "")
                    result["goal"] = sprint_data.get("goal", "")
            except Exception:
                pass

        return result

    # =========================================================================
    # INDEX.yaml Generation
    # =========================================================================

    def _get_tech_stack(self) -> dict:
        """
        Read tech stack from config.yaml.

        Returns:
            Dict with summary, languages, and frameworks
        """
        config_path = self.vk_dir / "config.yaml"
        if not config_path.exists():
            return {
                "summary": "",
                "languages": [],
                "frameworks": [],
            }

        try:
            config = yaml.safe_load(config_path.read_text())
            tech_stack = config.get("tech_stack", {})

            # Build summary from tech stack
            languages = tech_stack.get("languages", [])
            frameworks = tech_stack.get("frameworks", [])

            # Create comma-separated summary
            summary_parts = []
            if languages:
                summary_parts.extend(languages)
            if frameworks:
                summary_parts.extend(frameworks)

            return {
                "summary": ", ".join(summary_parts),
                "languages": languages,
                "frameworks": frameworks,
            }
        except Exception:
            return {
                "summary": "",
                "languages": [],
                "frameworks": [],
            }

    def _get_current_roadmap_phase(self) -> dict:
        """
        Read current roadmap phase from roadmap/phases.yaml.

        Returns:
            Dict with current_phase, phase_number, and phase_status
        """
        roadmap_path = self.vk_dir / "roadmap" / "phases.yaml"
        if not roadmap_path.exists():
            return {}

        try:
            roadmap = yaml.safe_load(roadmap_path.read_text())
            current_phase_num = roadmap.get("current_phase")
            if not current_phase_num:
                return {}

            # Find the current phase details
            phases = roadmap.get("phases", [])
            for phase in phases:
                if phase.get("phase_number") == current_phase_num:
                    return {
                        "current_phase": phase.get("name", f"Phase {current_phase_num}"),
                        "phase_number": current_phase_num,
                        "phase_status": phase.get("status", "unknown"),
                    }

            return {}
        except Exception:
            return {}

    def generate_index(
        self,
        agents: list | None = None,
        tools: dict | None = None,
    ) -> Path:
        """
        Generate INDEX.yaml with master navigation data.

        This is the single source of truth for agents to quickly
        understand project state (~100 tokens).

        Args:
            agents: Optional list of agent configurations
            tools: Optional dict of tool configurations (lsp, linters, quality_gates)

        Returns:
            Path to generated INDEX.yaml
        """
        # Count tasks by status
        pending = len(list((self.tasks_dir / "pending").glob("*.md")))
        active = len(list((self.tasks_dir / "active").glob("*.md")))
        done = len(list((self.tasks_dir / "done").glob("*.md")))
        blocked = len(list((self.tasks_dir / "blocked").glob("*.md")))

        # Get sprint info
        sprint_info = self.get_sprint_progress()

        # Get next task
        next_task = self.get_next_task()

        # Get tech stack
        tech_stack = self._get_tech_stack()

        # Get roadmap phase
        roadmap = self._get_current_roadmap_phase()

        # Build index data
        index = {
            "sprint": {
                "id": sprint_info.get("sprint_id", "none"),
                "name": sprint_info.get("name", ""),
                "goal": sprint_info.get("goal", ""),
                "progress": sprint_info.get("progress", 0),
                "status": sprint_info.get("status", "none"),
            },
            "tasks": {
                "total": pending + active + done + blocked,
                "pending": pending,
                "active": active,
                "done": done,
                "blocked": blocked,
            },
            "next": {
                "task": next_task.task_id if next_task else None,
                "path": f"tasks/pending/{next_task.raw_filename}" if next_task else None,
            },
            "updated": datetime.now(timezone.utc).isoformat(),
        }

        # Add tech stack if available
        if tech_stack.get("summary"):
            index["tech_stack"] = tech_stack

        # Add roadmap if available
        if roadmap:
            index["roadmap"] = roadmap

        # NEW: Agent inventory
        if agents:
            index["agents"] = {
                "count": len(agents),
                "available": [
                    {
                        "name": a.name if hasattr(a, "name") else a.get("name", ""),
                        "purpose": (
                            a.description
                            if hasattr(a, "description")
                            else a.get("description", "")
                        )[:50],
                        "delegates_to": (
                            (
                                a.settings.get("delegates_to", [])
                                if hasattr(a, "settings") and a.settings
                                else []
                            )
                            if hasattr(a, "settings")
                            else a.get("settings", {}).get("delegates_to", [])
                        ),
                    }
                    for a in agents
                ],
            }

        # NEW: Tools inventory
        if tools:
            lsp = (
                tools.get("lsp", {})
                if isinstance(tools, dict)
                else getattr(tools, "lsp", None)
            )
            linters = (
                tools.get("linters", [])
                if isinstance(tools, dict)
                else getattr(tools, "linters", [])
            )
            quality_gates = (
                tools.get("quality_gates", [])
                if isinstance(tools, dict)
                else getattr(tools, "quality_gates", [])
            )

            index["tools"] = {
                "lsp": (
                    lsp.get("languages", [])
                    if isinstance(lsp, dict)
                    else (lsp.languages if lsp else [])
                ),
                "linters": [
                    (
                        l.get("name", l)
                        if isinstance(l, dict)
                        else (l.name if hasattr(l, "name") else str(l))
                    )
                    for l in linters
                ],
                "quality_gates": [
                    (
                        g.get("name", g)
                        if isinstance(g, dict)
                        else (g.name if hasattr(g, "name") else str(g))
                    )
                    for g in quality_gates
                ],
            }

        # NEW: Context layer paths for stateless awareness
        index["context"] = {
            "micro": ".claude/context-micro.yaml",
            "mini": ".claude/context-mini.yaml",
            "full": "CLAUDE.md",
            "project": "PROJECT.md",
            "state": ".vk/STATE.md",
        }

        # Write INDEX.yaml
        index_path = self.vk_dir / "INDEX.yaml"
        with open(index_path, "w") as f:
            yaml.safe_dump(index, f, default_flow_style=False, sort_keys=False)

        return index_path

    def generate_state_md(self, sprint: Optional[SprintConfig] = None) -> Path:
        """
        Generate STATE.md with human-readable snapshot.

        Args:
            sprint: Optional sprint config for additional details

        Returns:
            Path to generated STATE.md
        """
        sprint_info = self.get_sprint_progress()
        pending = self.get_tasks_by_status("pending")
        active = self.get_tasks_by_status("active")
        blocked = self.get_tasks_by_status("blocked")
        done = self.get_tasks_by_status("done")

        lines = [
            "# Project State",
            "",
            f"> Auto-generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Sprint",
            "",
            f"- **ID**: {sprint_info.get('sprint_id', 'None')}",
            f"- **Progress**: {sprint_info.get('progress', 0)}%",
            f"- **Status**: {sprint_info.get('status', 'none')}",
            "",
            "## Tasks Summary",
            "",
            "| Status | Count |",
            "|--------|-------|",
            f"| Pending | {len(pending)} |",
            f"| Active | {len(active)} |",
            f"| Done | {len(done)} |",
            f"| Blocked | {len(blocked)} |",
            f"| **Total** | **{len(pending) + len(active) + len(done) + len(blocked)}** |",
            "",
        ]

        # Active tasks
        if active:
            lines.extend(
                [
                    "## Active Tasks",
                    "",
                ]
            )
            for t in active:
                iter_info = f" (iter {t.iteration})" if t.iteration else ""
                lines.append(f"- `{t.task_id}` [{t.priority}]{iter_info}")
            lines.append("")

        # Ready tasks
        ready = [t for t in pending if not t.dependency]
        if ready:
            lines.extend(
                [
                    "## Ready to Execute",
                    "",
                ]
            )
            for t in ready[:5]:  # Show top 5
                # Check if plan file exists
                plan_path = self.vk_dir / "plans" / "ready" / f"{t.task_id}.md"
                if plan_path.exists():
                    lines.append(f"- `{t.task_id}` [{t.priority}] → [📋 PLAN](.vk/plans/ready/{t.task_id}.md)")
                else:
                    lines.append(f"- `{t.task_id}` [{t.priority}]")
            if len(ready) > 5:
                lines.append(f"- ... and {len(ready) - 5} more")
            lines.append("")

        # Blocked tasks
        if blocked:
            lines.extend(
                [
                    "## Blocked",
                    "",
                ]
            )
            for t in blocked:
                dep_info = f" (needs {t.dependency})" if t.dependency else ""
                lines.append(f"- `{t.task_id}`{dep_info}")
            lines.append("")

        # Completed tasks (show recent ones with commit SHA)
        if done:
            lines.extend(
                [
                    "## Completed",
                    "",
                ]
            )
            # Show last 10 completed tasks
            for t in done[-10:]:
                # Try to read commit_sha from task file
                task_file = self.tasks_dir / "done" / t.raw_filename
                commit_sha = self._extract_commit_sha(task_file)

                if commit_sha:
                    lines.append(f"- `{t.task_id}` [{t.priority}] ✅ (commit: {commit_sha[:7]})")
                else:
                    lines.append(f"- `{t.task_id}` [{t.priority}] ✅")

            if len(done) > 10:
                lines.append(f"- ... and {len(done) - 10} more")
            lines.append("")

        # Write STATE.md
        state_path = self.vk_dir / "STATE.md"
        with open(state_path, "w") as f:
            f.write("\n".join(lines))

        return state_path

    # =========================================================================
    # Sync Integration
    # =========================================================================

    def sync_from_sprint(self, sprint: SprintConfig) -> list[Path]:
        """
        Create filesystem state from sprint configuration.

        Called during `vk pull` to generate the directory structure
        from API response.

        Args:
            sprint: Sprint configuration from API

        Returns:
            List of created file paths
        """
        self.ensure_directories()
        created_files = []

        # Calculate sprint progress
        all_tasks = []
        for req in sprint.requirements:
            all_tasks.extend(req.tasks)

        total = len(all_tasks)
        done_count = sum(1 for t in all_tasks if t.status == TaskStatusEnum.COMPLETED)
        progress = int((done_count / total * 100) if total > 0 else 0)

        # Create sprint file
        sprint_filename = self.generate_sprint_filename(sprint.sprint_id, progress)
        sprint_path = self.sprints_dir / "active" / sprint_filename
        self._write_task_content(sprint_path, self._sprint_to_content(sprint))
        created_files.append(sprint_path)

        # Create task files
        for req in sprint.requirements:
            for task in req.tasks:
                # Determine status directory
                status_dir = STATUS_DIRS.get(task.status, "pending")

                # Check for dependencies - extract from description
                dependency = None
                if task.status == TaskStatusEnum.BLOCKED and task.description:
                    # Parse dependency patterns from description
                    # Patterns: "Blocked by TASK-XXX", "depends on TASK-XXX", "waiting for XXX"
                    dep_pattern = r"(?:blocked by|depends on|waiting for|requires)\s+(?:TASK-)?([A-Za-z0-9_-]+)"
                    match = re.search(dep_pattern, task.description, re.IGNORECASE)
                    if match:
                        dependency = match.group(1)

                # Generate filename
                filename = self.generate_task_filename(
                    task_id=task.task_id,
                    priority=task.priority,
                    dependency=dependency,
                )

                # Write task file
                task_path = self.tasks_dir / status_dir / filename
                self._write_task_content(task_path, self._task_to_content(task, req))
                created_files.append(task_path)

        # Generate INDEX.yaml and STATE.md
        created_files.append(self.generate_index())
        created_files.append(self.generate_state_md(sprint))

        return created_files

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find a task file by ID across all status directories."""
        for status_dir in ["pending", "active", "done", "blocked"]:
            dir_path = self.tasks_dir / status_dir
            if not dir_path.exists():
                continue
            for f in dir_path.glob(f"{task_id}*.md"):
                return f
        return None

    def _find_sprint_file(self, sprint_id: str) -> Optional[Path]:
        """Find a sprint file by ID."""
        # Normalize sprint ID
        if not sprint_id.startswith("SPRINT-"):
            sprint_id = f"SPRINT-{sprint_id}"

        for status_dir in ["active", "archive"]:
            dir_path = self.sprints_dir / status_dir
            if not dir_path.exists():
                continue
            for f in dir_path.glob(f"{sprint_id}*.md"):
                return f
        return None

    def _extract_commit_sha(self, task_file: Path) -> Optional[str]:
        """Extract commit SHA from task markdown file."""
        if not task_file.exists():
            return None

        try:
            content = task_file.read_text()
            # Look for "**Commit**: <sha>" pattern
            match = re.search(r"\*\*Commit\*\*:\s*([a-f0-9]+)", content)
            if match:
                return match.group(1)
        except Exception:
            pass

        return None

    def _write_task_content(self, path: Path, content: str) -> None:
        """Write task content to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    def _task_to_content(self, task: Task, requirement=None) -> str:
        """Convert task to markdown content."""
        lines = [
            f"# {task.task_id}: {task.title}",
            "",
            f"**Priority**: {task.priority.value if hasattr(task.priority, 'value') else task.priority}",
            f"**Status**: {task.status.value if hasattr(task.status, 'value') else task.status}",
        ]

        # Add commit_sha if available
        if task.commit_sha:
            lines.append(f"**Commit**: {task.commit_sha}")

        lines.append("")

        if task.description:
            lines.extend(["## Description", "", task.description, ""])

        if requirement:
            lines.extend(
                [
                    "## Requirement",
                    "",
                    f"- **ID**: {requirement.requirement_id}",
                    f"- **Title**: {requirement.title}",
                    "",
                ]
            )

        return "\n".join(lines)

    def _sprint_to_content(self, sprint: SprintConfig) -> str:
        """Convert sprint to markdown content."""
        lines = [
            f"# {sprint.sprint_id}: {sprint.name}",
            "",
            f"**Status**: {sprint.status}",
            "",
        ]

        if sprint.goal:
            lines.extend(["## Goal", "", sprint.goal, ""])

        # Requirements summary
        lines.extend(["## Requirements", ""])
        for req in sprint.requirements:
            task_count = len(req.tasks)
            done_count = sum(1 for t in req.tasks if t.status == TaskStatusEnum.COMPLETED)
            lines.append(f"- **{req.requirement_id}**: {req.title} ({done_count}/{task_count})")

        return "\n".join(lines)
