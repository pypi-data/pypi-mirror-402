"""
Auto-detect project settings from existing files.

Provides intelligent detection of project type, languages, frameworks,
and common commands based on configuration files present in the project.
"""

import json
from pathlib import Path
from typing import Optional


class ProjectDetector:
    """
    Detects project type, languages, frameworks, and conventions.

    Scans project files to automatically determine:
    - Programming languages used
    - Frameworks in use
    - Test, lint, and build commands
    - Database technologies

    Usage:
        detector = ProjectDetector(Path("/path/to/project"))
        settings = detector.detect_all()
    """

    def __init__(self, project_root: Path):
        """
        Initialize detector.

        Args:
            project_root: Root directory of the project
        """
        self.root = project_root

    def detect_all(self) -> dict:
        """
        Detect all project settings.

        Returns:
            Dictionary with detected settings:
            - languages: List of detected programming languages
            - frameworks: List of detected frameworks
            - databases: List of detected databases
            - test_command: Detected test command
            - lint_command: Detected lint command
            - build_command: Detected build command
        """
        return {
            "languages": self.detect_languages(),
            "frameworks": self.detect_frameworks(),
            "databases": self.detect_databases(),
            "test_command": self.detect_test_command(),
            "lint_command": self.detect_lint_command(),
            "build_command": self.detect_build_command(),
        }

    def detect_languages(self) -> list[str]:
        """
        Detect programming languages from project files.

        Returns:
            List of detected language names
        """
        languages = []

        # JavaScript/TypeScript
        if (self.root / "package.json").exists():
            if (self.root / "tsconfig.json").exists():
                languages.append("TypeScript")
            else:
                languages.append("JavaScript")

        # Python
        if (
            (self.root / "pyproject.toml").exists()
            or (self.root / "setup.py").exists()
            or (self.root / "requirements.txt").exists()
        ):
            languages.append("Python")

        # Go
        if (self.root / "go.mod").exists():
            languages.append("Go")

        # Rust
        if (self.root / "Cargo.toml").exists():
            languages.append("Rust")

        # Ruby
        if (self.root / "Gemfile").exists():
            languages.append("Ruby")

        # Java/Kotlin
        if (self.root / "pom.xml").exists() or (self.root / "build.gradle").exists():
            if (self.root / "build.gradle.kts").exists():
                languages.append("Kotlin")
            else:
                languages.append("Java")

        # PHP
        if (self.root / "composer.json").exists():
            languages.append("PHP")

        # C#/.NET
        if any(self.root.glob("*.csproj")) or any(self.root.glob("*.sln")):
            languages.append("C#")

        return languages

    def detect_frameworks(self) -> list[str]:
        """
        Detect frameworks from configuration files.

        Returns:
            List of detected framework names
        """
        frameworks = []

        # Check package.json for JS/TS frameworks
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                # Frontend frameworks
                if "react" in deps:
                    frameworks.append("React")
                if "vue" in deps:
                    frameworks.append("Vue")
                if "svelte" in deps:
                    frameworks.append("Svelte")
                if "@angular/core" in deps:
                    frameworks.append("Angular")

                # Meta-frameworks
                if "next" in deps:
                    frameworks.append("Next.js")
                if "nuxt" in deps:
                    frameworks.append("Nuxt")
                if "gatsby" in deps:
                    frameworks.append("Gatsby")
                if "remix" in deps:
                    frameworks.append("Remix")

                # Backend frameworks
                if "express" in deps:
                    frameworks.append("Express")
                if "fastify" in deps:
                    frameworks.append("Fastify")
                if "nestjs" in deps or "@nestjs/core" in deps:
                    frameworks.append("NestJS")
                if "hono" in deps:
                    frameworks.append("Hono")

                # Testing frameworks
                if "jest" in deps:
                    frameworks.append("Jest")
                if "vitest" in deps:
                    frameworks.append("Vitest")
                if "playwright" in deps or "@playwright/test" in deps:
                    frameworks.append("Playwright")
            except (json.JSONDecodeError, OSError):
                pass

        # Check pyproject.toml for Python frameworks
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text()

                # Web frameworks
                if "fastapi" in content.lower():
                    frameworks.append("FastAPI")
                if "django" in content.lower():
                    frameworks.append("Django")
                if "flask" in content.lower():
                    frameworks.append("Flask")
                if "starlette" in content.lower():
                    frameworks.append("Starlette")

                # Testing
                if "pytest" in content.lower():
                    frameworks.append("pytest")

                # CLI
                if "typer" in content.lower():
                    frameworks.append("Typer")
                if "click" in content.lower():
                    frameworks.append("Click")

                # Data
                if "pydantic" in content.lower():
                    frameworks.append("Pydantic")
                if "sqlalchemy" in content.lower():
                    frameworks.append("SQLAlchemy")
            except OSError:
                pass

        # Check requirements.txt as fallback
        requirements = self.root / "requirements.txt"
        if requirements.exists() and not frameworks:
            try:
                content = requirements.read_text().lower()
                if "fastapi" in content:
                    frameworks.append("FastAPI")
                if "django" in content:
                    frameworks.append("Django")
                if "flask" in content:
                    frameworks.append("Flask")
                if "pytest" in content:
                    frameworks.append("pytest")
            except OSError:
                pass

        # Check Gemfile for Ruby frameworks
        gemfile = self.root / "Gemfile"
        if gemfile.exists():
            try:
                content = gemfile.read_text().lower()
                if "rails" in content:
                    frameworks.append("Rails")
                if "sinatra" in content:
                    frameworks.append("Sinatra")
            except OSError:
                pass

        return frameworks

    def detect_databases(self) -> list[str]:
        """
        Detect database technologies from configuration.

        Returns:
            List of detected database names
        """
        databases = []

        # Check docker-compose for database services
        compose_files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
        for compose_file in compose_files:
            compose_path = self.root / compose_file
            if compose_path.exists():
                try:
                    content = compose_path.read_text().lower()
                    if "postgres" in content:
                        databases.append("PostgreSQL")
                    if "mysql" in content:
                        databases.append("MySQL")
                    if "mongo" in content:
                        databases.append("MongoDB")
                    if "redis" in content:
                        databases.append("Redis")
                    if "elasticsearch" in content:
                        databases.append("Elasticsearch")
                except OSError:
                    pass

        # Check .env files
        env_files = [".env", ".env.example", ".env.local"]
        for env_file in env_files:
            env_path = self.root / env_file
            if env_path.exists():
                try:
                    content = env_path.read_text().lower()
                    if "postgres" in content and "PostgreSQL" not in databases:
                        databases.append("PostgreSQL")
                    if "mysql" in content and "MySQL" not in databases:
                        databases.append("MySQL")
                    if "mongo" in content and "MongoDB" not in databases:
                        databases.append("MongoDB")
                    if "redis" in content and "Redis" not in databases:
                        databases.append("Redis")
                except OSError:
                    pass

        return databases

    def detect_test_command(self) -> str:
        """
        Detect the appropriate test command.

        Returns:
            Test command string
        """
        # Check package.json scripts
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                scripts = pkg.get("scripts", {})
                if "test" in scripts:
                    return "npm test"
                if "test:unit" in scripts:
                    return "npm run test:unit"
            except (json.JSONDecodeError, OSError):
                pass
            return "npm test"

        # Check for Python test setup
        if (self.root / "pyproject.toml").exists():
            # Check if pytest is configured
            try:
                content = (self.root / "pyproject.toml").read_text()
                if "pytest" in content.lower():
                    return "pytest"
            except OSError:
                pass
            return "pytest"

        if (self.root / "pytest.ini").exists() or (self.root / "conftest.py").exists():
            return "pytest"

        if (self.root / "setup.py").exists():
            return "python -m pytest"

        # Check for Makefile
        makefile = self.root / "Makefile"
        if makefile.exists():
            try:
                content = makefile.read_text()
                if "test:" in content:
                    return "make test"
            except OSError:
                pass

        # Go
        if (self.root / "go.mod").exists():
            return "go test ./..."

        # Rust
        if (self.root / "Cargo.toml").exists():
            return "cargo test"

        # Ruby
        if (self.root / "Gemfile").exists():
            return "bundle exec rspec"

        return "echo 'No test command configured'"

    def detect_lint_command(self) -> str:
        """
        Detect the appropriate lint command.

        Returns:
            Lint command string
        """
        # Check package.json scripts
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                scripts = pkg.get("scripts", {})
                if "lint" in scripts:
                    return "npm run lint"
                if "lint:fix" in scripts:
                    return "npm run lint:fix"
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "eslint" in deps:
                    return "npx eslint ."
                if "biome" in deps or "@biomejs/biome" in deps:
                    return "npx biome check ."
            except (json.JSONDecodeError, OSError):
                pass
            return "npm run lint"

        # Python linting
        if (self.root / "pyproject.toml").exists():
            try:
                content = (self.root / "pyproject.toml").read_text()
                if "ruff" in content.lower():
                    return "ruff check . && ruff format --check ."
                if "black" in content.lower():
                    return "black --check . && flake8"
            except OSError:
                pass
            return "ruff check ."

        if (self.root / "ruff.toml").exists():
            return "ruff check ."

        if (self.root / ".flake8").exists():
            return "flake8"

        # Makefile
        makefile = self.root / "Makefile"
        if makefile.exists():
            try:
                content = makefile.read_text()
                if "lint:" in content:
                    return "make lint"
            except OSError:
                pass

        # Go
        if (self.root / "go.mod").exists():
            return "golangci-lint run"

        # Rust
        if (self.root / "Cargo.toml").exists():
            return "cargo clippy"

        return "echo 'No lint command configured'"

    def detect_build_command(self) -> Optional[str]:
        """
        Detect the appropriate build command.

        Returns:
            Build command string or None
        """
        # Check package.json scripts
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                scripts = pkg.get("scripts", {})
                if "build" in scripts:
                    return "npm run build"
            except (json.JSONDecodeError, OSError):
                pass

        # Python build
        if (self.root / "pyproject.toml").exists():
            return "python -m build"

        # Makefile
        makefile = self.root / "Makefile"
        if makefile.exists():
            try:
                content = makefile.read_text()
                if "build:" in content:
                    return "make build"
            except OSError:
                pass

        # Go
        if (self.root / "go.mod").exists():
            return "go build ./..."

        # Rust
        if (self.root / "Cargo.toml").exists():
            return "cargo build --release"

        return None

    def get_summary(self) -> str:
        """
        Get a human-readable summary of detected settings.

        Returns:
            Summary string
        """
        settings = self.detect_all()
        parts = []

        if settings["languages"]:
            parts.append(f"Languages: {', '.join(settings['languages'])}")
        if settings["frameworks"]:
            parts.append(f"Frameworks: {', '.join(settings['frameworks'])}")
        if settings["databases"]:
            parts.append(f"Databases: {', '.join(settings['databases'])}")

        return " | ".join(parts) if parts else "No project configuration detected"
