"""
LSP (Language Server Protocol) configuration generator for VibeKit.

Auto-detects project languages and generates .claude/lsp.yaml with appropriate
LSP server configurations for IDE/editor integration.
"""

import json
from pathlib import Path
from typing import Optional

import yaml


class LspConfigGenerator:
    """
    Generator for LSP configuration.

    Auto-detects project languages and generates LSP server configurations
    for Python, TypeScript, Vue, Rust, Go, and other supported languages.

    Usage:
        generator = LspConfigGenerator(project_root)
        generator.generate()  # Creates .claude/tools/lsp.yaml
    """

    # LSP server configurations by language
    LSP_SERVERS = {
        "python": {
            "name": "pyright",
            "command": "pyright-langserver",
            "args": ["--stdio"],
            "root_markers": [
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                ".git",
            ],
            "filetypes": ["python"],
        },
        "typescript": {
            "name": "typescript-language-server",
            "command": "typescript-language-server",
            "args": ["--stdio"],
            "root_markers": ["package.json", "tsconfig.json", ".git"],
            "filetypes": ["typescript", "javascript"],
        },
        "javascript": {
            "name": "typescript-language-server",
            "command": "typescript-language-server",
            "args": ["--stdio"],
            "root_markers": ["package.json", "tsconfig.json", ".git"],
            "filetypes": ["javascript", "typescript"],
        },
        "vue": {
            "name": "volar",
            "command": "vue-language-server",
            "args": ["--stdio"],
            "root_markers": ["package.json", "vite.config.ts", "vue.config.js", ".git"],
            "filetypes": ["vue"],
        },
        "rust": {
            "name": "rust-analyzer",
            "command": "rust-analyzer",
            "args": [],
            "root_markers": ["Cargo.toml", "Cargo.lock", ".git"],
            "filetypes": ["rust"],
        },
        "go": {
            "name": "gopls",
            "command": "gopls",
            "args": [],
            "root_markers": ["go.mod", "go.sum", ".git"],
            "filetypes": ["go"],
        },
    }

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize LSP config generator.

        Args:
            project_root: Root directory of the project (default: cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.vk_dir = self.project_root / ".vk"
        self.tools_dir = self.vk_dir / "tools"
        self.output_file = self.tools_dir / "lsp.yaml"

    def detect_languages(self) -> list[str]:
        """
        Auto-detect project languages from various indicators.

        Returns:
            List of detected language names
        """
        languages = set()

        # Check Python
        if (
            (self.project_root / "pyproject.toml").exists()
            or (self.project_root / "setup.py").exists()
            or (self.project_root / "requirements.txt").exists()
            or list(self.project_root.glob("**/*.py"))
        ):
            languages.add("python")

        # Check TypeScript/JavaScript
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                    # Check for TypeScript
                    if "typescript" in deps or (self.project_root / "tsconfig.json").exists():
                        languages.add("typescript")

                    # Check for Vue
                    if "vue" in deps or list(self.project_root.glob("**/*.vue")):
                        languages.add("vue")

                    # Always add JavaScript if package.json exists
                    languages.add("javascript")

            except Exception:
                # Fallback: just add JavaScript
                languages.add("javascript")

        # Check Vue files directly
        if list(self.project_root.glob("**/*.vue")):
            languages.add("vue")

        # Check Rust
        if (self.project_root / "Cargo.toml").exists() or list(self.project_root.glob("**/*.rs")):
            languages.add("rust")

        # Check Go
        if (self.project_root / "go.mod").exists() or list(self.project_root.glob("**/*.go")):
            languages.add("go")

        return sorted(languages)

    def generate(self) -> Path:
        """
        Generate LSP configuration file from detected languages.

        Returns:
            Path to generated lsp.yaml file
        """
        languages = self.detect_languages()

        # Build server configurations
        servers = []
        for lang in languages:
            if lang in self.LSP_SERVERS:
                servers.append(self.LSP_SERVERS[lang])

        config = {
            "enabled": True,
            "languages": languages,
            "servers": servers,
            "symbol_operations": True,
            "auto_import": True,
        }

        # Ensure tools directory exists
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        # Write config
        with open(self.output_file, "w") as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)

        return self.output_file

    def get_server_config(self, language: str) -> Optional[dict]:
        """
        Get LSP server configuration for a specific language.

        Args:
            language: Language name (e.g., "python", "typescript")

        Returns:
            Server configuration dict or None if not supported
        """
        return self.LSP_SERVERS.get(language)


def generate_lsp_config(project_root: Optional[Path] = None) -> str:
    """
    Generate LSP configuration and return as YAML string.

    Args:
        project_root: Root directory of the project (default: cwd)

    Returns:
        LSP configuration as YAML string
    """
    generator = LspConfigGenerator(project_root)
    languages = generator.detect_languages()

    servers = []
    for lang in languages:
        if lang in generator.LSP_SERVERS:
            servers.append(generator.LSP_SERVERS[lang])

    config = {
        "enabled": True,
        "languages": languages,
        "servers": servers,
        "symbol_operations": True,
        "auto_import": True,
    }

    return yaml.dump(config, sort_keys=False, default_flow_style=False)


def write_lsp_config(project_root: Optional[Path] = None) -> Path:
    """
    Generate and write LSP configuration file.

    Args:
        project_root: Root directory of the project (default: cwd)

    Returns:
        Path to generated lsp.yaml file
    """
    generator = LspConfigGenerator(project_root)
    return generator.generate()
