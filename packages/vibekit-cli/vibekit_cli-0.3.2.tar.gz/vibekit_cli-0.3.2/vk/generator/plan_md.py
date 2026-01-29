"""
PLAN.md Generator - Executable task prompts.

Generates GSD-style PLAN.md files for each task.
These are executable prompts that fresh agents can pick up.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vk.sync.models import ProjectConfig, SprintConfig, Task


def _validate_patterns(patterns: list[str], output_dir: Path) -> tuple[list[str], list[str]]:
    """Validate that pattern references exist in .claude/patterns/.

    Args:
        patterns: List of pattern names to validate
        output_dir: Project root directory

    Returns:
        Tuple of (valid_patterns, missing_patterns)
    """
    patterns_dir = output_dir / ".claude" / "patterns"
    valid = []
    missing = []

    for pattern in patterns:
        # Check for pattern file (pattern-name.md or pattern_name.md)
        pattern_file = patterns_dir / f"{pattern}.md"
        pattern_file_alt = patterns_dir / f"{pattern.replace('-', '_')}.md"

        if pattern_file.exists() or pattern_file_alt.exists():
            valid.append(pattern)
        else:
            missing.append(pattern)

    return valid, missing


def _get_tech_stack_patterns(project: ProjectConfig) -> list[str]:
    """Get tech-stack specific pattern suggestions.

    Args:
        project: Project configuration

    Returns:
        List of suggested patterns based on tech stack
    """
    suggestions = []
    languages = project.tech_stack.languages if project.tech_stack else []
    frameworks = project.tech_stack.frameworks if project.tech_stack else []

    languages_lower = [lang.lower() for lang in languages]
    frameworks_lower = [fw.lower() for fw in frameworks]

    # Python patterns
    if "python" in languages_lower:
        suggestions.extend([
            "Use pytest fixtures for test setup/teardown",
            "Add type hints for all function signatures",
            "Use context managers for resource handling",
            "Prefer async/await for I/O operations",
        ])

        # FastAPI specific
        if any("fastapi" in fw for fw in frameworks_lower):
            suggestions.extend([
                "Use Depends() for dependency injection",
                "Define Pydantic models for request/response",
                "Use HTTPException for error responses",
            ])

    # JavaScript/TypeScript patterns
    if any(lang in languages_lower for lang in ["javascript", "typescript"]):
        suggestions.extend([
            "Use TypeScript interfaces for type safety",
            "Prefer const/let over var",
            "Use async/await over callbacks",
        ])

        # Vue.js specific
        if any("vue" in fw for fw in frameworks_lower):
            suggestions.extend([
                "Use Composition API with <script setup>",
                "Define props with defineProps<T>()",
                "Use Pinia stores for shared state",
                "Emit events with defineEmits<T>()",
            ])

        # React specific
        if any("react" in fw for fw in frameworks_lower):
            suggestions.extend([
                "Use functional components with hooks",
                "Prefer useState/useReducer for state",
                "Use useEffect for side effects",
            ])

    # Go patterns
    if "go" in languages_lower or "golang" in languages_lower:
        suggestions.extend([
            "Return errors, don't panic",
            "Use interfaces for abstraction",
            "Prefer composition over inheritance",
        ])

    # Rust patterns
    if "rust" in languages_lower:
        suggestions.extend([
            "Use Result<T, E> for error handling",
            "Prefer borrowing over cloning",
            "Use derive macros for common traits",
        ])

    # Java/Kotlin patterns
    if any(lang in languages_lower for lang in ["java", "kotlin"]):
        suggestions.extend([
            "Use constructor injection over field injection",
            "Prefer immutable objects and records for DTOs",
            "Use Optional for nullable returns",
            "Follow Google Java Style Guide",
        ])

        # Spring Boot specific
        if any("spring" in fw for fw in frameworks_lower):
            suggestions.extend([
                "Use @Service, @Repository, @Controller annotations",
                "Write @SpringBootTest for integration tests",
                "Use @Transactional for database operations",
            ])

        # Kotlin specific
        if "kotlin" in languages_lower:
            suggestions.extend([
                "Use data classes for DTOs",
                "Prefer val over var for immutability",
                "Use coroutines for async operations",
            ])

    # C#/.NET patterns
    if any(lang in languages_lower for lang in ["c#", "csharp", "f#", "fsharp"]):
        suggestions.extend([
            "Use dependency injection via constructor",
            "Prefer async/await for I/O operations",
            "Use records for immutable data types",
            "Follow Microsoft C# coding conventions",
        ])

        # ASP.NET specific
        if any(fw in frameworks_lower for fw in ["asp.net", "aspnet", ".net core", "dotnet"]):
            suggestions.extend([
                "Use IActionResult for controller returns",
                "Configure services in Program.cs",
                "Use Entity Framework Core for data access",
            ])

    return suggestions


def _get_verification_commands(project: ProjectConfig, quality_gates: list | None = None) -> str:
    """Get tech-stack aware verification commands.

    Args:
        project: Project configuration
        quality_gates: Optional list of quality gate configurations from tools

    Returns:
        Formatted verification commands as markdown code block
    """
    # Try to extract commands from quality gates first
    test_command = None
    lint_command = None

    if quality_gates:
        for gate in quality_gates:
            gate_dict = (
                gate
                if isinstance(gate, dict)
                else (gate.model_dump() if hasattr(gate, "model_dump") else {})
            )
            name = gate_dict.get("name", "").lower()
            command = gate_dict.get("command")
            enabled = gate_dict.get("enabled", True)

            if enabled and command:
                if "test" in name or "pytest" in name:
                    test_command = command
                elif "lint" in name or "ruff" in name or "eslint" in name:
                    lint_command = command

    # If we found commands in quality gates, use them
    if test_command or lint_command:
        commands = []
        if test_command:
            commands.append(f"# Run tests\n{test_command}")
        if lint_command:
            commands.append(f"# Run linter\n{lint_command}")

        if commands:
            return "```bash\n" + "\n\n".join(commands) + "\n```"

    # Otherwise, fall back to tech-stack detection
    languages = project.tech_stack.languages if project.tech_stack else []
    languages_lower = [lang.lower() for lang in languages]

    # Detect project type
    is_python = "python" in languages_lower
    is_js = any(
        lang in languages_lower for lang in ["javascript", "typescript", "node", "vue", "react"]
    )
    is_go = "go" in languages_lower or "golang" in languages_lower
    is_rust = "rust" in languages_lower
    is_java = any(lang in languages_lower for lang in ["java", "kotlin"])
    is_csharp = any(lang in languages_lower for lang in ["c#", "csharp", "f#", "fsharp"])

    # Check for build tools in frameworks/tools
    frameworks = project.tech_stack.frameworks if project.tech_stack else []
    tools = project.tech_stack.tools if project.tech_stack else []
    all_tools = [t.lower() for t in frameworks + tools]
    uses_gradle = any("gradle" in t for t in all_tools)
    uses_maven = any("maven" in t for t in all_tools)

    if is_java:
        if uses_gradle:
            return """```bash
# Run tests
./gradlew test

# Run linter/checkstyle
./gradlew check

# Build
./gradlew build
```"""
        else:  # Maven (default for Java)
            return """```bash
# Run tests
mvn test

# Run linter/checkstyle
mvn checkstyle:check

# Build
mvn package -DskipTests
```"""
    elif is_csharp:
        return """```bash
# Run tests
dotnet test

# Build
dotnet build

# Run (if applicable)
dotnet run
```"""
    elif is_js:
        return """```bash
# Run tests
npm test

# Run linter
npm run lint

# Type check
npm run typecheck

# Build (optional)
npm run build
```"""
    elif is_go:
        return """```bash
# Run tests
go test ./...

# Run linter
golangci-lint run

# Build
go build ./...
```"""
    elif is_rust:
        return """```bash
# Run tests
cargo test

# Run linter
cargo clippy

# Build
cargo build
```"""
    elif is_python:
        return """```bash
# Run tests
pytest

# Run linter
ruff check .

# Type check (if configured)
# mypy . / pyright
```"""
    else:
        # Default/generic
        return """```bash
# Run project-specific tests
# Check .vk/INDEX.yaml for quality_gates

# Common patterns:
# pytest / npm test / go test ./...
# ruff / eslint / golangci-lint
```"""


def generate_task_plan(
    task: Task,
    sprint: SprintConfig,
    project: ProjectConfig,
    output_dir: Path,
    quality_gates: list | None = None,
) -> Path:
    """Generate PLAN.md for a single task - executable prompt.

    Args:
        task: Task to generate plan for
        sprint: Sprint configuration
        project: Project configuration
        output_dir: Output directory for plan files
        quality_gates: Optional list of quality gate configurations
    """

    # Format context files - include STATE.md for current progress
    context_lines = ["- @PROJECT.md", "- @CLAUDE.md", "- @.vk/STATE.md"]
    if task.files_likely:
        context_lines.extend(f"- @{f}" for f in task.files_likely)
    context_section = "\n".join(context_lines)

    # Format acceptance criteria for body
    if task.acceptance_criteria:
        criteria_section = "\n".join(f"- [ ] {c}" for c in task.acceptance_criteria)
    else:
        criteria_section = (
            "- [ ] Task completed successfully\n- [ ] Tests pass\n- [ ] Linting passes"
        )

    # Format patterns with validation
    patterns_lines = []
    if task.patterns_to_use:
        valid_patterns, missing_patterns = _validate_patterns(task.patterns_to_use, output_dir)
        if valid_patterns:
            patterns_lines.append("**Configured patterns:**")
            patterns_lines.extend(f"- {p}" for p in valid_patterns)
        if missing_patterns:
            patterns_lines.append("\n**⚠️ Missing patterns** (not found in `.claude/patterns/`):")
            patterns_lines.extend(f"- ~~{p}~~" for p in missing_patterns)

    # Add tech-stack specific suggestions
    tech_patterns = _get_tech_stack_patterns(project)
    if tech_patterns:
        if patterns_lines:
            patterns_lines.append("\n**Tech-stack best practices:**")
        else:
            patterns_lines.append("**Tech-stack best practices:**")
        patterns_lines.extend(f"- {p}" for p in tech_patterns[:4])  # Limit to 4

    if patterns_lines:
        patterns_section = "\n".join(patterns_lines)
    else:
        patterns_section = (
            "_No specific patterns recommended. Check `.claude/patterns/` for applicable patterns._"
        )

    # Format dependencies
    if task.dependencies:
        deps_section = "\n".join(f"- {d}" for d in task.dependencies)
    else:
        deps_section = "_No dependencies_"

    # Get tech-stack aware verification commands
    verification_section = _get_verification_commands(project, quality_gates)

    # Build frontmatter with rich task data
    frontmatter_lines = [
        "---",
        f"phase: {sprint.name}",
        f"task: {task.task_id}",
        f"priority: {task.priority.value}",
        f"status: {task.status.value}",
    ]

    # Add acceptance_criteria to frontmatter
    if task.acceptance_criteria:
        frontmatter_lines.append("acceptance_criteria:")
        for criterion in task.acceptance_criteria:
            frontmatter_lines.append(f"  - {criterion}")

    # Add files_likely to frontmatter
    if task.files_likely:
        frontmatter_lines.append("files_likely:")
        for file_path in task.files_likely:
            frontmatter_lines.append(f"  - {file_path}")

    # Add dependencies to frontmatter
    if task.dependencies:
        frontmatter_lines.append("dependencies:")
        for dep in task.dependencies:
            frontmatter_lines.append(f"  - {dep}")

    # Add assignee to frontmatter if available
    if task.assignee:
        frontmatter_lines.append(f"assignee: {task.assignee}")

    # Add generated_by to frontmatter if available
    if task.generated_by:
        frontmatter_lines.append(f"generated_by: {task.generated_by}")

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    content = f"""{frontmatter}

# {task.title}

## Objective

{task.description or "_No description provided._"}

## Context Files

{context_section}

## Acceptance Criteria

{criteria_section}

## Suggested Patterns

{patterns_section}

## Dependencies

{deps_section}

## Verification

{verification_section}

## Done When

All acceptance criteria checked AND all quality gates pass.

After completion:
1. Run `vk done {task.task_id}` to mark complete
2. State files will auto-update
3. Next task will be available in `.vk/plans/ready/`
"""

    # Write to .vk/plans/ready/{task_id}.md
    plans_dir = output_dir / ".vk" / "plans" / "ready"
    plans_dir.mkdir(parents=True, exist_ok=True)

    plan_path = plans_dir / f"{task.task_id}.md"
    plan_path.write_text(content)
    return plan_path


def generate_all_task_plans(
    sprint: SprintConfig,
    project: ProjectConfig,
    output_dir: Path,
    quality_gates: list | None = None,
) -> list[Path]:
    """Generate PLAN.md for all pending/active tasks in sprint.

    Args:
        sprint: Sprint configuration
        project: Project configuration
        output_dir: Output directory for plan files
        quality_gates: Optional list of quality gate configurations
    """
    plans = []

    for req in sprint.requirements:
        for task in req.tasks:
            # Only generate plans for pending and in_progress tasks
            if task.status.value in ["pending", "in_progress"]:
                plan_path = generate_task_plan(task, sprint, project, output_dir, quality_gates)
                plans.append(plan_path)

    return plans
