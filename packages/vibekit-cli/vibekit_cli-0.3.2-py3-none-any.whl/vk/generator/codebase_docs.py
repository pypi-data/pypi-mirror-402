"""
Codebase Documentation Generator for VibeKit.

Auto-generates token-efficient documentation for .claude/codebase/ that enables
AI agents to find code locations without exploratory file operations.

Generated files:
- INDEX.md: Master lookup table (~1KB)
- WHERE_TO_PUT.md: Feature placement guide (~1.5KB)
- ENDPOINTS.md: All API routes (~1.5KB)
- MODELS.md: Data schemas (~1.5KB)
- CONVENTIONS.md: Naming patterns (~800 tokens)
- COMPONENTS.md: Vue component map (~1KB)
- SERVICES.md: Service layer map (~800 tokens)

Total budget: ~8KB (under Layer 4's 16KB allocation)
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


class CodebaseDocsGenerator:
    """
    Generator for .claude/codebase/ documentation.

    Analyzes codebase structure and generates token-efficient
    documentation for AI agent consumption.

    Usage:
        generator = CodebaseDocsGenerator(project_root)
        files = generator.generate()
    """

    def __init__(self, project_root: Path):
        """
        Initialize generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.codebase_dir = project_root / ".claude" / "codebase"

    def generate(self) -> list[Path]:
        """
        Generate all codebase documentation files.

        Returns:
            List of created file paths
        """
        self.codebase_dir.mkdir(parents=True, exist_ok=True)

        files = []
        files.append(self._generate_index())
        files.append(self._generate_where_to_put())
        files.append(self._generate_endpoints())
        files.append(self._generate_models())
        files.append(self._generate_conventions())
        files.append(self._generate_components())
        files.append(self._generate_services())

        # Generate checksums for staleness detection
        self._generate_checksums(files)

        return files

    # =========================================================================
    # Individual File Generators
    # =========================================================================

    def _generate_index(self) -> Path:
        """Generate INDEX.md - master lookup table."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Detect project structure dynamically
        structure = self._detect_project_structure()

        content = f"""# Codebase Index

> Auto-generated: {timestamp}

## Quick Lookup

| Need | File | Section |
|------|------|---------|
| Add feature | WHERE_TO_PUT.md | Feature Matrix |
| Code style | CONVENTIONS.md | Naming Patterns |
"""
        if structure.get("has_api"):
            content += "| Find endpoint | ENDPOINTS.md | Routes Table |\n"
            content += "| Find model | MODELS.md | Schema Table |\n"
            content += "| Service logic | SERVICES.md | Service Map |\n"
        if structure.get("has_frontend"):
            content += "| Find component | COMPONENTS.md | Component Table |\n"

        content += f"""
## Structure Summary

```
{self.project_root.name}/
"""
        # Add detected directories
        for dir_info in structure.get("directories", []):
            content += f"├── {dir_info['name']}/".ljust(20) + f"# {dir_info['desc']}\n"
        content += "```\n"

        # File counts for detected directories
        if structure.get("file_counts"):
            content += """
## File Counts

| Directory | Files | Pattern |
|-----------|-------|---------|
"""
            for dir_path, info in structure["file_counts"].items():
                content += f"| {dir_path} | {info['count']} | {info['pattern']} |\n"

        # Key paths
        content += """
## Key Paths

"""
        for path_info in structure.get("entry_points", []):
            content += f"- **{path_info['name']}**: `{path_info['path']}`\n"

        path = self.codebase_dir / "INDEX.md"
        path.write_text(content)
        return path

    def _detect_project_structure(self) -> dict:
        """Detect the actual project structure dynamically."""
        structure = {
            "has_api": False,
            "has_frontend": False,
            "directories": [],
            "file_counts": {},
            "entry_points": [],
            "tech_stack": set(),
        }

        # Detect Python project
        if (self.project_root / "pyproject.toml").exists() or (self.project_root / "setup.py").exists():
            structure["tech_stack"].add("python")

        # Detect Node.js/JS project
        if (self.project_root / "package.json").exists():
            structure["tech_stack"].add("javascript")

        # Detect common backend structures
        for api_dir in ["api", "app", "src", "backend", "server"]:
            api_path = self.project_root / api_dir
            if api_path.exists() and api_path.is_dir():
                # Check for routes/controllers
                routes_path = api_path / "routes"
                controllers_path = api_path / "controllers"
                if routes_path.exists() or controllers_path.exists():
                    structure["has_api"] = True
                    structure["directories"].append({"name": api_dir, "desc": "Backend/API"})

                    # Count files
                    route_dir = routes_path if routes_path.exists() else controllers_path
                    py_count = len(list(route_dir.glob("*.py")))
                    js_count = len(list(route_dir.glob("*.js"))) + len(list(route_dir.glob("*.ts")))
                    if py_count > 0:
                        structure["file_counts"][f"{api_dir}/routes/"] = {"count": py_count, "pattern": "*.py routes"}
                    if js_count > 0:
                        structure["file_counts"][f"{api_dir}/routes/"] = {"count": js_count, "pattern": "*.ts routes"}

                # Check for models
                models_path = api_path / "models"
                if models_path.exists():
                    model_count = len(list(models_path.glob("*.py")))
                    if model_count > 0:
                        structure["file_counts"][f"{api_dir}/models/"] = {"count": model_count, "pattern": "model classes"}

                # Check for services
                services_path = api_path / "services"
                if services_path.exists():
                    svc_count = len(list(services_path.glob("*.py")))
                    if svc_count > 0:
                        structure["file_counts"][f"{api_dir}/services/"] = {"count": svc_count, "pattern": "*_service.py"}

                # Entry points
                for entry in ["main.py", "app.py", "index.py", "__init__.py"]:
                    if (api_path / entry).exists():
                        structure["entry_points"].append({"name": "API Entry", "path": f"{api_dir}/{entry}"})
                        break

        # Detect frontend structures
        for ui_dir in ["ui", "frontend", "client", "web", "src"]:
            ui_path = self.project_root / ui_dir
            if ui_path.exists() and ui_path.is_dir():
                # Check for Vue
                if list(ui_path.rglob("*.vue")):
                    structure["has_frontend"] = True
                    structure["tech_stack"].add("vue")
                    vue_count = len(list(ui_path.rglob("*.vue")))
                    structure["directories"].append({"name": ui_dir, "desc": "Vue.js frontend"})
                    structure["file_counts"][f"{ui_dir}/"] = {"count": vue_count, "pattern": "*.vue components"}
                # Check for React
                elif list(ui_path.rglob("*.jsx")) or list(ui_path.rglob("*.tsx")):
                    structure["has_frontend"] = True
                    structure["tech_stack"].add("react")
                    react_count = len(list(ui_path.rglob("*.jsx"))) + len(list(ui_path.rglob("*.tsx")))
                    structure["directories"].append({"name": ui_dir, "desc": "React frontend"})
                    structure["file_counts"][f"{ui_dir}/"] = {"count": react_count, "pattern": "*.jsx/*.tsx components"}

        # Detect other common directories
        for other_dir, desc in [
            ("tests", "Test suite"),
            ("test", "Test suite"),
            ("docs", "Documentation"),
            ("scripts", "Utility scripts"),
            ("lib", "Library code"),
            ("pkg", "Package code"),
            ("cmd", "CLI commands"),
        ]:
            dir_path = self.project_root / other_dir
            if dir_path.exists() and dir_path.is_dir():
                structure["directories"].append({"name": other_dir, "desc": desc})

        # Detect entry points
        for entry, name in [
            ("main.py", "Main Entry"),
            ("app.py", "App Entry"),
            ("cli.py", "CLI Entry"),
            ("index.js", "JS Entry"),
            ("index.ts", "TS Entry"),
            ("main.ts", "Main Entry"),
        ]:
            if (self.project_root / entry).exists():
                structure["entry_points"].append({"name": name, "path": entry})
            # Check in src/
            if (self.project_root / "src" / entry).exists():
                structure["entry_points"].append({"name": name, "path": f"src/{entry}"})

        # Config files
        if (self.project_root / ".claude" / "config.yaml").exists():
            structure["entry_points"].append({"name": "Config", "path": ".claude/config.yaml"})

        return structure

    def _generate_where_to_put(self) -> Path:
        """Generate WHERE_TO_PUT.md - feature placement guide based on detected structure."""
        structure = self._detect_project_structure()

        content = """# Where to Put Code

## Feature Type Matrix

| Feature Type | Location | Example |
|--------------|----------|---------|
"""
        # Generate based on detected directories
        detected_patterns = []

        # Python backend patterns
        if (self.project_root / "api" / "routes").exists():
            content += "| API endpoint | `api/routes/{domain}.py` | `api/routes/users.py` |\n"
            detected_patterns.append(("Route", "api/services/", "api/routes/"))
        elif (self.project_root / "app" / "routes").exists():
            content += "| API endpoint | `app/routes/{domain}.py` | `app/routes/users.py` |\n"
            detected_patterns.append(("Route", "app/services/", "app/routes/"))
        elif (self.project_root / "src" / "routes").exists():
            content += "| API endpoint | `src/routes/{domain}.py` | `src/routes/users.py` |\n"

        if (self.project_root / "api" / "services").exists():
            content += "| Business logic | `api/services/{domain}_service.py` | `api/services/user_service.py` |\n"
            detected_patterns.append(("Service", "api/repositories/", "api/services/"))
        elif (self.project_root / "app" / "services").exists():
            content += "| Business logic | `app/services/{domain}_service.py` | `app/services/user_service.py` |\n"
        elif (self.project_root / "services").exists():
            content += "| Business logic | `services/{domain}_service.py` | `services/user_service.py` |\n"

        if (self.project_root / "api" / "models").exists():
            content += "| Data model | `api/models/{entity}.py` | `api/models/user.py` |\n"
        elif (self.project_root / "app" / "models").exists():
            content += "| Data model | `app/models/{entity}.py` | `app/models/user.py` |\n"
        elif (self.project_root / "models").exists():
            content += "| Data model | `models/{entity}.py` | `models/user.py` |\n"

        if (self.project_root / "api" / "repositories").exists():
            content += "| DB access | `api/repositories/{domain}_repository.py` | `api/repositories/user_repository.py` |\n"

        # Frontend patterns - Vue
        if list((self.project_root / "ui" / "src").rglob("*.vue")) if (self.project_root / "ui" / "src").exists() else []:
            content += "| UI page | `ui/src/views/{Name}View.vue` | `ui/src/views/DashboardView.vue` |\n"
            content += "| UI component | `ui/src/components/{Name}.vue` | `ui/src/components/Button.vue` |\n"
        elif list((self.project_root / "frontend" / "src").rglob("*.vue")) if (self.project_root / "frontend" / "src").exists() else []:
            content += "| UI page | `frontend/src/views/{Name}View.vue` | `frontend/src/views/DashboardView.vue` |\n"
            content += "| UI component | `frontend/src/components/{Name}.vue` | `frontend/src/components/Button.vue` |\n"
        elif list((self.project_root / "src").rglob("*.vue")) if (self.project_root / "src").exists() else []:
            content += "| UI page | `src/views/{Name}View.vue` | `src/views/DashboardView.vue` |\n"
            content += "| UI component | `src/components/{Name}.vue` | `src/components/Button.vue` |\n"

        # Frontend patterns - React
        if list((self.project_root / "src").rglob("*.tsx")) if (self.project_root / "src").exists() else []:
            content += "| React page | `src/pages/{Name}.tsx` | `src/pages/Dashboard.tsx` |\n"
            content += "| React component | `src/components/{Name}.tsx` | `src/components/Button.tsx` |\n"

        # Test patterns
        if (self.project_root / "tests").exists():
            content += "| Tests | `tests/{module}/test_{name}.py` | `tests/api/test_users.py` |\n"
        elif (self.project_root / "test").exists():
            content += "| Tests | `test/{module}/test_{name}.py` | `test/api/test_users.py` |\n"

        # Decision tree based on detected structure
        content += """
## Decision Tree

```
New Feature
"""
        if structure.get("has_api"):
            content += """├─ Backend only?
│   ├─ Data storage? → models/
│   ├─ Business logic? → services/
│   └─ HTTP endpoint? → routes/
│
"""
        if structure.get("has_frontend"):
            content += """├─ Frontend only?
│   ├─ Full page? → views/
│   ├─ Reusable piece? → components/
│   └─ Shared state? → stores/
│
"""
        content += """└─ Tests?
    └─ → tests/ or test/
```
"""

        # Import patterns only if we detected layers
        if detected_patterns:
            content += """
## Import Patterns

| When adding to | Import from |
|----------------|-------------|
"""
            for layer, imports_from, _ in detected_patterns:
                content += f"| {layer} | `{imports_from}` |\n"

        path = self.codebase_dir / "WHERE_TO_PUT.md"
        path.write_text(content)
        return path

    def _generate_endpoints(self) -> Path:
        """Generate ENDPOINTS.md - all API routes."""
        routes = self._analyze_api_routes()

        content = """# API Endpoints

## Route Summary

"""
        # Group routes by file
        routes_by_file: dict[str, list] = {}
        for route in routes:
            file = route["file"]
            if file not in routes_by_file:
                routes_by_file[file] = []
            routes_by_file[file].append(route)

        for file, file_routes in sorted(routes_by_file.items()):
            domain = file.replace(".py", "").title()
            content += f"### {domain}\n\n"
            content += "| Method | Path | Handler |\n"
            content += "|--------|------|--------|\n"
            for r in file_routes:
                content += f"| {r['method']} | `{r['path']}` | {file}::{r.get('handler', '')} |\n"
            content += "\n"

        # Dynamically list route files
        routes_dir = self.project_root / "api" / "routes"
        if not routes_dir.exists():
            routes_dir = self.project_root / "app" / "routes"
        if not routes_dir.exists():
            routes_dir = self.project_root / "src" / "routes"

        if routes_dir.exists():
            content += """## Route Files

| Domain | File |
|--------|------|
"""
            for route_file in sorted(routes_dir.glob("*.py")):
                if not route_file.name.startswith("_"):
                    domain = route_file.stem.replace("_", " ").title()
                    content += f"| {domain} | `{route_file.relative_to(self.project_root)}` |\n"

        path = self.codebase_dir / "ENDPOINTS.md"
        path.write_text(content)
        return path

    def _generate_models(self) -> Path:
        """Generate MODELS.md - data schemas."""
        models = self._analyze_models()

        content = """# Data Models

## Core Models

| Model | File | Collection | Key Fields |
|-------|------|------------|------------|
"""
        for m in models:
            fields = ", ".join(m.get("fields", [])[:4])
            content += f"| {m['name']} | `api/models/{m['file']}` | {m.get('collection', '')} | {fields} |\n"

        # Dynamically detect enums
        enums = self._analyze_enums()
        if enums:
            content += """
## Enums

| Enum | File | Values |
|------|------|--------|
"""
            for e in enums:
                values = ", ".join(e.get("values", [])[:5])
                if len(e.get("values", [])) > 5:
                    values += "..."
                content += f"| {e['name']} | `{e['file']}` | {values} |\n"

        path = self.codebase_dir / "MODELS.md"
        path.write_text(content)
        return path

    def _generate_conventions(self) -> Path:
        """Generate CONVENTIONS.md - naming patterns based on detected tech stack."""
        structure = self._detect_project_structure()
        tech_stack = structure.get("tech_stack", set())

        content = """# Conventions

"""
        # Python conventions
        if "python" in tech_stack or (self.project_root / "pyproject.toml").exists():
            content += """## Python

| Element | Pattern | Example |
|---------|---------|---------|
| File | `snake_case.py` | `user_service.py` |
| Class | `PascalCase` | `UserService` |
| Function | `snake_case` | `get_by_id` |
| Constant | `UPPER_SNAKE` | `MAX_RETRIES` |
| Private | `_prefix` | `_validate_input` |

"""

        # JavaScript/TypeScript conventions
        if "javascript" in tech_stack or (self.project_root / "package.json").exists():
            content += """## JavaScript/TypeScript

| Element | Pattern | Example |
|---------|---------|---------|
| File | `camelCase.ts` or `PascalCase.tsx` | `userService.ts` |
| Class | `PascalCase` | `UserService` |
| Function | `camelCase` | `getUserById` |
| Constant | `UPPER_SNAKE` | `MAX_RETRIES` |
| Type/Interface | `PascalCase` | `UserResponse` |

"""

        # Vue conventions
        if "vue" in tech_stack:
            content += """## Vue Components

| Element | Pattern | Example |
|---------|---------|---------|
| Component file | `PascalCase.vue` | `UserCard.vue` |
| View file | `*View.vue` | `DashboardView.vue` |
| Store file | `*.ts` | `users.ts` |
| Composable | `use*.ts` | `useAuth.ts` |

"""

        # React conventions
        if "react" in tech_stack:
            content += """## React Components

| Element | Pattern | Example |
|---------|---------|---------|
| Component file | `PascalCase.tsx` | `UserCard.tsx` |
| Page file | `*.tsx` | `Dashboard.tsx` |
| Hook | `use*.ts` | `useAuth.ts` |

"""

        # API patterns if backend detected
        if structure.get("has_api"):
            content += """## API Patterns

| Pattern | Format | Example |
|---------|--------|---------|
| List | `GET /resource` | `GET /users` |
| Get single | `GET /resource/{id}` | `GET /users/{id}` |
| Create | `POST /resource` | `POST /users` |
| Update | `PATCH /resource/{id}` | `PATCH /users/{id}` |
| Delete | `DELETE /resource/{id}` | `DELETE /users/{id}` |

"""

        path = self.codebase_dir / "CONVENTIONS.md"
        path.write_text(content)
        return path

    def _generate_components(self) -> Path:
        """Generate COMPONENTS.md - Vue component map."""
        components = self._analyze_vue_components()

        content = """# Vue Components

## Views (Pages)

| View | File | Route |
|------|------|-------|
"""
        views = [c for c in components if c.get("type") == "view"]
        for v in views[:15]:  # Limit to 15 for token efficiency
            content += f"| {v['name']} | `{v['path']}` | {v.get('route', '')} |\n"

        content += """
## Shared Components

| Component | File | Purpose |
|-----------|------|---------|
"""
        shared = [c for c in components if c.get("type") == "component"]
        for c in shared[:15]:
            content += f"| {c['name']} | `{c['path']}` | {c.get('purpose', '')} |\n"

        # Dynamically detect layouts
        layouts = [c for c in components if c.get("type") == "layout"]
        if layouts:
            content += """
## Layouts

| Layout | File |
|--------|------|
"""
            for lay in layouts[:10]:
                content += f"| {lay['name']} | `{lay['path']}` |\n"

        path = self.codebase_dir / "COMPONENTS.md"
        path.write_text(content)
        return path

    def _generate_services(self) -> Path:
        """Generate SERVICES.md - service layer map."""
        services = self._analyze_services()

        content = """# Services

## Service Map

| Service | File | Responsibility |
|---------|------|----------------|
"""
        for s in services:
            content += f"| {s['name']} | `api/services/{s['file']}` | {s.get('desc', '')} |\n"

        content += """
## Repository Map

| Repository | File | Model |
|------------|------|-------|
"""
        repos = self._analyze_repositories()
        for r in repos:
            content += f"| {r['name']} | `api/repositories/{r['file']}` | {r.get('model', '')} |\n"

        path = self.codebase_dir / "SERVICES.md"
        path.write_text(content)
        return path

    # =========================================================================
    # Analysis Methods
    # =========================================================================

    def _analyze_api_routes(self) -> list[dict]:
        """Analyze api/routes/*.py for endpoint definitions."""
        routes = []
        routes_dir = self.project_root / "api" / "routes"

        if not routes_dir.exists():
            return routes

        for route_file in routes_dir.glob("*.py"):
            if route_file.name.startswith("_"):
                continue

            try:
                content = route_file.read_text()
                # Parse @router.get/post/patch/delete decorators
                for match in re.finditer(
                    r'@router\.(\w+)\(["\']([^"\']+)["\']',
                    content
                ):
                    routes.append({
                        "method": match.group(1).upper(),
                        "path": match.group(2),
                        "file": route_file.name,
                    })
            except Exception:
                pass

        return routes

    def _analyze_models(self) -> list[dict]:
        """Analyze api/models/*.py for Document classes."""
        models = []
        models_dir = self.project_root / "api" / "models"

        if not models_dir.exists():
            return models

        for model_file in models_dir.glob("*.py"):
            if model_file.name.startswith("_"):
                continue

            try:
                content = model_file.read_text()
                # Parse class definitions inheriting from Document
                for match in re.finditer(r'class (\w+)\(Document\):', content):
                    model_name = match.group(1)
                    # Try to find collection name
                    collection_match = re.search(
                        rf'class {model_name}.*?class Settings:.*?name\s*=\s*["\'](\w+)["\']',
                        content,
                        re.DOTALL
                    )
                    collection = collection_match.group(1) if collection_match else model_name.lower() + "s"

                    models.append({
                        "name": model_name,
                        "file": model_file.name,
                        "collection": collection,
                        "fields": [],  # Could extract fields if needed
                    })
            except Exception:
                pass

        return models

    def _analyze_enums(self) -> list[dict]:
        """Analyze Python files for Enum classes."""
        enums = []

        # Check multiple possible locations
        for search_dir in ["api/models", "app/models", "models", "src/models", "api", "app", "src"]:
            dir_path = self.project_root / search_dir
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                try:
                    content = py_file.read_text()
                    # Find Enum classes
                    for match in re.finditer(
                        r'class\s+(\w+)\s*\(\s*(?:str\s*,\s*)?Enum\s*\):',
                        content
                    ):
                        enum_name = match.group(1)

                        # Extract enum values
                        values = []
                        # Find the class body and extract values
                        class_pattern = rf'class\s+{enum_name}\s*\([^)]*Enum[^)]*\):\s*\n((?:\s+\w+\s*=.*\n?)+)'
                        class_match = re.search(class_pattern, content)
                        if class_match:
                            body = class_match.group(1)
                            for val_match in re.finditer(r'^\s+(\w+)\s*=', body, re.MULTILINE):
                                values.append(val_match.group(1).lower())

                        rel_path = py_file.relative_to(self.project_root)
                        enums.append({
                            "name": enum_name,
                            "file": str(rel_path),
                            "values": values[:6],  # Limit to 6 values
                        })
                except Exception:
                    pass

        return enums

    def _analyze_vue_components(self) -> list[dict]:
        """Analyze ui/src/ for Vue components."""
        components = []
        ui_src = self.project_root / "ui" / "src"

        if not ui_src.exists():
            return components

        for vue_file in ui_src.rglob("*.vue"):
            try:
                rel_path = vue_file.relative_to(self.project_root)
                name = vue_file.stem

                # Determine type
                if "View" in name or "views" in str(rel_path):
                    comp_type = "view"
                elif "Layout" in name:
                    comp_type = "layout"
                else:
                    comp_type = "component"

                components.append({
                    "name": name,
                    "path": str(rel_path),
                    "type": comp_type,
                })
            except Exception:
                pass

        return components

    def _analyze_services(self) -> list[dict]:
        """Analyze api/services/*.py for service classes."""
        services = []
        services_dir = self.project_root / "api" / "services"

        if not services_dir.exists():
            return services

        for service_file in services_dir.glob("*_service.py"):
            try:
                name = service_file.stem.replace("_service", "").title() + "Service"
                services.append({
                    "name": name,
                    "file": service_file.name,
                    "desc": "",
                })
            except Exception:
                pass

        return services

    def _analyze_repositories(self) -> list[dict]:
        """Analyze api/repositories/*.py for repository classes."""
        repos = []
        repos_dir = self.project_root / "api" / "repositories"

        if not repos_dir.exists():
            return repos

        for repo_file in repos_dir.glob("*_repository.py"):
            try:
                name = repo_file.stem.replace("_repository", "").title() + "Repository"
                model = repo_file.stem.replace("_repository", "").title()
                repos.append({
                    "name": name,
                    "file": repo_file.name,
                    "model": model,
                })
            except Exception:
                pass

        return repos

    # =========================================================================
    # Staleness Detection
    # =========================================================================

    def _generate_checksums(self, generated_files: list[Path]) -> Path:
        """Generate checksums.json for staleness detection."""
        checksums = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_files": {},
            "generated_files": {},
        }

        # Hash source directories
        source_dirs = [
            self.project_root / "api" / "routes",
            self.project_root / "api" / "models",
            self.project_root / "api" / "services",
            self.project_root / "ui" / "src" / "views",
        ]

        for source_dir in source_dirs:
            if source_dir.exists():
                dir_hash = self._hash_directory(source_dir)
                checksums["source_files"][str(source_dir.relative_to(self.project_root))] = dir_hash

        # Hash generated files
        for gen_file in generated_files:
            if gen_file.exists():
                file_hash = self._hash_file(gen_file)
                checksums["generated_files"][gen_file.name] = file_hash

        checksums_path = self.codebase_dir / "checksums.json"
        with open(checksums_path, "w") as f:
            json.dump(checksums, f, indent=2)

        return checksums_path

    def _hash_file(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        try:
            content = filepath.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return "error"

    def _hash_directory(self, dirpath: Path) -> str:
        """Calculate combined hash of all files in directory."""
        try:
            hashes = []
            for f in sorted(dirpath.rglob("*")):
                if f.is_file() and not f.name.startswith("."):
                    hashes.append(self._hash_file(f))
            combined = "".join(hashes)
            return hashlib.sha256(combined.encode()).hexdigest()[:16]
        except Exception:
            return "error"

    def check_staleness(self) -> dict:
        """
        Check if codebase docs are stale.

        Returns:
            Dict with stale status and details
        """
        checksums_file = self.codebase_dir / "checksums.json"
        if not checksums_file.exists():
            return {"stale": True, "reason": "No checksums file"}

        try:
            with open(checksums_file) as f:
                old_checksums = json.load(f)

            stale_dirs = []
            for dir_path, old_hash in old_checksums.get("source_files", {}).items():
                full_path = self.project_root / dir_path
                if full_path.exists():
                    current_hash = self._hash_directory(full_path)
                    if current_hash != old_hash:
                        stale_dirs.append(dir_path)

            return {
                "stale": len(stale_dirs) > 0,
                "stale_directories": stale_dirs,
                "generated_at": old_checksums.get("generated_at"),
            }
        except Exception as e:
            return {"stale": True, "reason": str(e)}


def generate_codebase_docs(project_root: Path) -> list[Path]:
    """
    Convenience function to generate codebase docs.

    Args:
        project_root: Project root directory

    Returns:
        List of generated file paths
    """
    generator = CodebaseDocsGenerator(project_root)
    return generator.generate()
