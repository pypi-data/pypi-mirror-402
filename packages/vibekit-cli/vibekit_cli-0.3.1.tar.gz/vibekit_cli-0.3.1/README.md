# VibeKit

**Vibe Coding Platform** - Configure sprints in SaaS, execute locally with Claude Code.

[![PyPI](https://img.shields.io/pypi/v/vkcli)](https://pypi.org/project/vkcli/)
[![Python](https://img.shields.io/pypi/pyversions/vkcli)](https://pypi.org/project/vkcli/)

## What is VibeKit?

VibeKit bridges your project management in the cloud with AI-powered local development:

1. **Configure** sprints, tasks, and rules in the web dashboard at [vkcli.com](https://vkcli.com)
2. **Sync** configuration to your local project with `vk pull`
3. **Execute** tasks with Claude Code using intelligent agents
4. **Track** progress automatically synced back to the dashboard

## Installation

```bash
pip install vkcli
```

## Quick Start

```bash
# 1. Login to VibeKit
vk login

# 2. Initialize a new project (creates project in SaaS)
vk init

# 3. Or link to existing project and pull in one command
vk init myuser/myproject
# or
vk pull myuser/myproject

# 4. Pull configuration (if already initialized)
vk pull

# 5. Check sprint status
vk status
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `vk login` | Authenticate with VibeKit |
| `vk logout` | Clear credentials |
| `vk init [project]` | Create new project, or link to existing if slug provided |
| `vk link [project]` | Link existing project (auto-detects from git) |
| `vk pull [project]` | Sync config from SaaS (links first if slug provided) |
| `vk push` | Push task status to SaaS |
| `vk status` | View current sprint status |
| `vk sprint` | Start/manage sprints |
| `vk done <task>` | Mark task complete |
| `vk update` | Update CLI to latest version |
| `vk open` | Open project in browser |

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     vkcli.com (SaaS)                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Projects│  │ Sprints │  │  Tasks  │  │  Rules  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API + SSE
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Local Development                         │
│                                                              │
│  $ vk pull                    $ vk push                      │
│       │                            ▲                         │
│       ▼                            │                         │
│  ┌─────────┐    ┌─────────┐   ┌─────────┐                   │
│  │  .vk/   │───►│CLAUDE.md│───►│ Claude  │                   │
│  │ config  │    │ context │    │  Code   │                   │
│  └─────────┘    └─────────┘   └─────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Generated Files

When you run `vk pull`, the CLI generates:

```
your-project/
├── CLAUDE.md              # Context for Claude Code
└── .vk/
    ├── config.yaml        # Project configuration
    ├── context.yaml       # Full context (sprints, tasks, rules)
    ├── context-mini.yaml  # Minimal context for quick loads
    ├── sprints/           # Sprint data
    ├── rules/             # Coding rules and standards
    ├── tools/             # Tool configurations (LSP, linters)
    └── codebase/          # Auto-generated code documentation
        ├── INDEX.md       # Codebase navigation
        ├── WHERE_TO_PUT.md # Feature placement guide
        ├── ENDPOINTS.md   # API routes
        └── ...
```

## Using with Claude Code

Once you've pulled your configuration, Claude Code automatically reads `CLAUDE.md` for context. The file includes:

- Project overview and tech stack
- Current sprint and tasks
- Coding rules and standards
- Quality gates

You can also install the **vk-plugin** for Claude Code to get:
- `/vk status` - View sprint in Claude Code
- `/vk run` - Execute tasks with agents
- `/vk commit` - Smart commits
- And more...

## Documentation

- [CLI Reference](./docs/cli.md) - Full command documentation
- [API Reference](./docs/api.md) - REST API for integrations
- [Plugin Guide](./docs/plugin.md) - Claude Code plugin setup
- [Architecture](./docs/architecture.md) - System design

## Links

- **Website**: [vkcli.com](https://vkcli.com)
- **Dashboard**: [vkcli.com/dashboard](https://vkcli.com/dashboard)
- **PyPI**: [pypi.org/project/vkcli](https://pypi.org/project/vkcli/)
- **Issues**: [GitHub Issues](https://github.com/AgeofIA/vibe-kit/issues)

## License

MIT
