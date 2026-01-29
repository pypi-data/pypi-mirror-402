"""
VibeKit Generator Module - Configuration file generation.

This module generates various configuration files for projects:
- CLAUDE.md: Claude Code context from .claude/ configuration
- .pre-commit-config.yaml: Pre-commit hooks configuration
- .claude/tools/lsp.yaml: LSP server configuration
- .claude/codebase/: Token-efficient codebase documentation
- PROJECT.md: Living requirements document (GSD-style)
- PLAN.md: Executable task prompts (GSD-style)

Usage:
    from vk.generator import ClaudeMdGenerator, write_precommit_config, write_lsp_config

    generator = ClaudeMdGenerator()
    generator.generate()  # Creates/updates CLAUDE.md

    write_precommit_config(project_root)  # Creates .pre-commit-config.yaml

    write_lsp_config(project_root)  # Creates .claude/tools/lsp.yaml

    generate_codebase_docs(project_root)  # Creates .claude/codebase/*.md

    # GSD-style generators
    generate_project_md(project, sprint, output_dir)  # Creates PROJECT.md
    generate_all_task_plans(sprint, project, output_dir)  # Creates PLAN.md files
"""

from vk.generator.claude_md import ClaudeMdGenerator
from vk.generator.codebase_docs import CodebaseDocsGenerator, generate_codebase_docs
from vk.generator.lsp_config import (
    LspConfigGenerator,
    generate_lsp_config,
    write_lsp_config,
)
from vk.generator.plan_md import generate_all_task_plans, generate_task_plan
from vk.generator.precommit_config import (
    generate_precommit_config,
    install_precommit_hooks,
    write_precommit_config,
)
from vk.generator.project_md import generate_project_md

__all__ = [
    "ClaudeMdGenerator",
    "CodebaseDocsGenerator",
    "LspConfigGenerator",
    "generate_codebase_docs",
    "generate_lsp_config",
    "generate_precommit_config",
    "install_precommit_hooks",
    "write_lsp_config",
    "write_precommit_config",
    "generate_project_md",
    "generate_task_plan",
    "generate_all_task_plans",
]
