"""
Pre-commit Configuration Generator

Generates .pre-commit-config.yaml based on project settings and detected stack.
Called during `vk pull` to ensure pre-commit hooks are configured.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

# Pre-commit hook definitions
HOOKS = {
    # Mandatory - cannot be disabled
    "secrets": {
        "repo": "https://github.com/gitleaks/gitleaks",
        "rev": "v8.18.0",
        "hooks": [
            {
                "id": "gitleaks",
                "name": "Secret Detection",
                "description": "Detect secrets in code",
            }
        ],
        "mandatory": True,
        "description": "Blocks commits containing secrets",
    },
    # Python formatting
    "ruff-format": {
        "repo": "local",
        "hooks": [
            {
                "id": "ruff-format",
                "name": "Ruff Format",
                "entry": "ruff format",
                "language": "system",
                "types": ["python"],
                "description": "Format Python code",
            }
        ],
        "languages": ["python"],
        "category": "format",
    },
    # Python linting
    "ruff-lint": {
        "repo": "local",
        "hooks": [
            {
                "id": "ruff-lint",
                "name": "Ruff Lint",
                "entry": "ruff check --fix",
                "language": "system",
                "types": ["python"],
                "description": "Lint Python code with auto-fix",
            }
        ],
        "languages": ["python"],
        "category": "lint",
    },
    # JavaScript/TypeScript formatting
    "prettier": {
        "repo": "local",
        "hooks": [
            {
                "id": "prettier",
                "name": "Prettier",
                "entry": "prettier --write",
                "language": "system",
                "types_or": ["javascript", "typescript", "vue", "json", "css", "scss", "markdown"],
                "description": "Format JS/TS/CSS code",
            }
        ],
        "languages": ["javascript", "typescript", "vue"],
        "category": "format",
    },
    # JavaScript/TypeScript linting
    "eslint": {
        "repo": "local",
        "hooks": [
            {
                "id": "eslint",
                "name": "ESLint",
                "entry": "eslint --fix",
                "language": "system",
                "types_or": ["javascript", "typescript", "vue"],
                "description": "Lint JS/TS code with auto-fix",
            }
        ],
        "languages": ["javascript", "typescript", "vue"],
        "category": "lint",
    },
    # Type checking
    "pyright": {
        "repo": "local",
        "hooks": [
            {
                "id": "pyright",
                "name": "Pyright",
                "entry": "pyright",
                "language": "system",
                "types": ["python"],
                "pass_filenames": False,
                "description": "Type check Python code",
            }
        ],
        "languages": ["python"],
        "category": "typecheck",
    },
    "tsc": {
        "repo": "local",
        "hooks": [
            {
                "id": "tsc",
                "name": "TypeScript",
                "entry": "tsc --noEmit",
                "language": "system",
                "types": ["typescript"],
                "pass_filenames": False,
                "description": "Type check TypeScript code",
            }
        ],
        "languages": ["typescript"],
        "category": "typecheck",
    },
    # VibeKit custom linters
    "vk-security": {
        "repo": "local",
        "hooks": [
            {
                "id": "vk-security",
                "name": "Security Patterns",
                "entry": "python -m vk.linters.security",
                "language": "system",
                "pass_filenames": False,
                "description": "Check security patterns",
            }
        ],
        "category": "security",
    },
    # Conventional commits
    "commitlint": {
        "repo": "local",
        "hooks": [
            {
                "id": "commitlint",
                "name": "Commit Lint",
                "entry": "npx commitlint --edit",
                "language": "system",
                "stages": ["commit-msg"],
                "description": "Enforce conventional commits",
            }
        ],
        "languages": ["javascript", "typescript"],
        "category": "commit",
    },
}


def detect_project_languages(project_root: Path) -> set[str]:
    """Detect programming languages used in the project."""
    languages = set()

    # Python indicators
    if (project_root / "pyproject.toml").exists() or (project_root / "requirements.txt").exists():
        languages.add("python")

    # JavaScript/TypeScript indicators
    if (project_root / "package.json").exists():
        languages.add("javascript")
        if (project_root / "tsconfig.json").exists():
            languages.add("typescript")

    # Vue indicators
    if list(project_root.rglob("*.vue")):
        languages.add("vue")

    return languages


def generate_precommit_config(
    project_root: Path,
    enabled_hooks: dict[str, bool] | None = None,
    languages: set[str] | None = None,
) -> str:
    """
    Generate pre-commit configuration YAML.

    Args:
        project_root: Project root directory
        enabled_hooks: Optional dict of hook_id -> enabled
        languages: Optional set of languages (auto-detected if not provided)

    Returns:
        YAML string for .pre-commit-config.yaml
    """
    if languages is None:
        languages = detect_project_languages(project_root)

    if enabled_hooks is None:
        enabled_hooks = {}

    config: dict[str, Any] = {
        "fail_fast": True,
        "minimum_pre_commit_version": "3.0.0",
        "repos": [],
    }

    # Group hooks by repo
    local_hooks: list[dict[str, Any]] = []
    external_repos: list[dict[str, Any]] = []

    for hook_id, hook_def in HOOKS.items():
        # Check if hook should be included
        is_mandatory = hook_def.get("mandatory", False)
        is_enabled = enabled_hooks.get(hook_id, True)  # Default enabled
        hook_languages = set(hook_def.get("languages", []))

        # Mandatory hooks are always included
        if is_mandatory:
            pass
        # Non-mandatory hooks must be enabled and match languages
        elif not is_enabled:
            continue
        elif hook_languages and not hook_languages.intersection(languages):
            continue

        # Build hook configuration
        if hook_def["repo"] == "local":
            for hook in hook_def["hooks"]:
                hook_config = {
                    "id": hook["id"],
                    "name": hook["name"],
                    "entry": hook["entry"],
                    "language": hook.get("language", "system"),
                }
                if "types" in hook:
                    hook_config["types"] = hook["types"]
                if "types_or" in hook:
                    hook_config["types_or"] = hook["types_or"]
                if hook.get("pass_filenames") is False:
                    hook_config["pass_filenames"] = False
                if "stages" in hook:
                    hook_config["stages"] = hook["stages"]

                local_hooks.append(hook_config)
        else:
            repo_config = {
                "repo": hook_def["repo"],
                "rev": hook_def.get("rev", "latest"),
                "hooks": [{"id": h["id"]} for h in hook_def["hooks"]],
            }
            external_repos.append(repo_config)

    # Add external repos first (secrets detection is critical)
    config["repos"].extend(external_repos)

    # Add local hooks
    if local_hooks:
        config["repos"].append({
            "repo": "local",
            "hooks": local_hooks,
        })

    # Generate YAML with comments
    yaml_str = yaml.dump(config, sort_keys=False, default_flow_style=False)

    # Add header comment
    header = """# Pre-commit configuration
# Generated by VibeKit - https://vkcli.com
#
# Install: pre-commit install
# Run manually: pre-commit run --all-files
#
# IMPORTANT: Secret detection (gitleaks) cannot be bypassed.
# Using --no-verify is audited.

"""
    return header + yaml_str


def install_precommit_hooks(project_root: Path) -> bool:
    """Install pre-commit hooks in the project."""
    try:
        # Check if pre-commit is installed
        result = subprocess.run(
            ["pre-commit", "--version"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if result.returncode != 0:
            return False

        # Install hooks
        result = subprocess.run(
            ["pre-commit", "install", "--install-hooks"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if result.returncode != 0:
            return False

        # Also install commit-msg hook
        subprocess.run(
            ["pre-commit", "install", "--hook-type", "commit-msg"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        return True
    except FileNotFoundError:
        return False


def write_precommit_config(
    project_root: Path,
    enabled_hooks: dict[str, bool] | None = None,
    languages: set[str] | None = None,
) -> Path:
    """
    Write pre-commit configuration to project.

    Args:
        project_root: Project root directory
        enabled_hooks: Optional dict of hook_id -> enabled
        languages: Optional set of languages

    Returns:
        Path to the generated config file
    """
    config_content = generate_precommit_config(
        project_root=project_root,
        enabled_hooks=enabled_hooks,
        languages=languages,
    )

    config_path = project_root / ".pre-commit-config.yaml"
    config_path.write_text(config_content, encoding="utf-8")

    return config_path
